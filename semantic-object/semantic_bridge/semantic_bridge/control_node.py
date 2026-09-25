"""Driving and goal-sending from the browser, on their own ROS node.

TOPIC CHOICE IS THE WHOLE SAFETY ARGUMENT. This publishes Twist on
`/cmd_vel_teleop_raw` -- the same topic `make teleop-nav` uses -- so the
browser enters the identical chain and gets the identical protections:

    browser -> /ws/teleop -> HERE -> /cmd_vel_teleop_raw
                          -> teleop_speed_guard  (clamps 0.30 / 0.50;
                                                  exact zero passes unclamped)
                          -> /cmd_vel_teleop
                          -> twist_mux priority 100 (Nav2 is 10)
                          -> /diff_cont/cmd_vel_unstamped

Publishing to `/cmd_vel_teleop` instead would bypass the clamp. Publishing to
`/diff_cont/cmd_vel_unstamped` would bypass the mux as well, which is what
`make teleop` does and why the Makefile says it FIGHTS Nav2 rather than
overriding it. Neither is acceptable from a browser.

QoS is default RELIABLE/VOLATILE depth 10, because that is what the guard
subscribes with. Using sensor-data QoS here would be the mirror image of the
/scan hazard: best-effort publisher, reliable subscriber, no connection, and
the robot simply never moves with nothing logged anywhere.

THE WATCHDOG RELEASES; IT DOES NOT HOLD ZERO. This is the part that is easy to
get catastrophically wrong. twist_mux gives `cmd_vel_teleop` priority 100 with
`timeout: 0.5`. A watchdog that publishes zero FOREVER when the client goes
quiet therefore holds priority 100 at zero permanently -- close a browser tab
at the wrong moment and Nav2 is locked out for the rest of the session, with
no error on any topic, in any log, anywhere. So:

    IDLE     publish nothing at all. The channel is released and Nav2 owns it.
    ACTIVE   republish the latest command at 20 Hz.
             no client message for 300 ms -> ZEROING
    ZEROING  publish exact zero at 20 Hz for 0.7 s, then -> IDLE.
             0.7 s is deliberately longer than twist_mux's 0.5 s timeout, so
             the stop is guaranteed to be the winning command for a full
             timeout window before the channel is let go.

There are three further layers under that, none of which this replaces:
twist_mux's own 0.5 s input timeout, diff_drive_controller's cmd_vel_timeout
(0.5 s, not overridden in my_controllers.yaml), and `make teleop-nav`, which
remains the e-stop. A joystick on a phone over a hotspot is not an e-stop and
nothing here pretends otherwise.

ITS OWN NODE, ON ITS OWN EXECUTOR. RosManager spins a plain single-threaded
rclpy.spin alongside _on_map, which base64-encodes an entire OccupancyGrid. A
20 Hz timer on the safety path must never queue behind that.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

IDLE, ACTIVE, ZEROING = "idle", "active", "zeroing"

TOPIC = "/cmd_vel_teleop_raw"
TICK_HZ = 20.0
STALE_S = 0.3        # no client message for this long -> start stopping
ZERO_S = 0.7         # > twist_mux's 0.5 s timeout, then release

# The pad's own ceiling, BELOW the guard's 0.30. The mapping speed is still
# 0.10 m/s and since D-26 nothing enforces it: scan shear is speed x 86 ms, so
# 0.9 cm per scan at 0.10 and 2.6 cm at 0.30, and sheared scans cannot be
# un-sheared once they are in the pose graph. A browser pad that defaulted to
# the ceiling would quietly ruin a map the first time somebody used it.
DEFAULT_MAX_LINEAR = 0.10
DEFAULT_MAX_ANGULAR = 0.50
HARD_MAX_LINEAR = 0.30       # teleop_speed_guard clamps here anyway
HARD_MAX_ANGULAR = 0.50


def _clamp(v: float, lim: float) -> float:
    if not math.isfinite(v):
        return 0.0
    return max(-lim, min(lim, v))


class ControlNode:
    """Owns the teleop publisher, its watchdog, and the NavigateToPose client."""

    def __init__(self) -> None:
        import rclpy
        import rclpy.node
        from geometry_msgs.msg import Twist
        from rclpy.action import ActionClient
        from nav2_msgs.action import NavigateToPose

        self._Twist = Twist
        self._NavigateToPose = NavigateToPose

        self._node = rclpy.node.Node("semantic_bridge_control")
        self._pub = self._node.create_publisher(Twist, TOPIC, 10)
        self._nav = ActionClient(self._node, NavigateToPose, "navigate_to_pose")

        self._lock = threading.Lock()
        self._state = IDLE
        self._vx = 0.0
        self._wz = 0.0
        self._last_cmd_at = 0.0
        self._zero_until = 0.0
        self._max_linear = DEFAULT_MAX_LINEAR
        self._max_angular = DEFAULT_MAX_ANGULAR

        self._goal_handle = None
        self._goal_lock = threading.Lock()

        self._node.create_timer(1.0 / TICK_HZ, self._tick)
        self._node.get_logger().info(
            f"browser teleop ready on {TOPIC} "
            f"(pad ceiling {DEFAULT_MAX_LINEAR} m/s; the guard clamps at "
            f"{HARD_MAX_LINEAR}). `make teleop-nav` is still the e-stop.")

    # -- the safety timer --------------------------------------------------

    def _tick(self) -> None:
        now = time.monotonic()
        with self._lock:
            state, vx, wz = self._state, self._vx, self._wz
            if state == ACTIVE and (now - self._last_cmd_at) > STALE_S:
                self._state = state = ZEROING
                self._zero_until = now + ZERO_S
                self._vx = self._wz = vx = wz = 0.0
                logger.info("teleop: client went quiet, stopping and releasing")
            elif state == ZEROING:
                vx = wz = 0.0
                if now >= self._zero_until:
                    self._state = IDLE
                    return           # release: publish NOTHING from now on

        if state == IDLE:
            return                   # Nav2 owns the mux again

        msg = self._Twist()
        msg.linear.x = vx
        msg.angular.z = wz
        self._pub.publish(msg)

    # -- called from the event loop ---------------------------------------

    def set_command(self, vx: float, wz: float) -> dict:
        with self._lock:
            self._vx = _clamp(float(vx), min(self._max_linear, HARD_MAX_LINEAR))
            self._wz = _clamp(float(wz), min(self._max_angular, HARD_MAX_ANGULAR))
            self._last_cmd_at = time.monotonic()
            self._state = ACTIVE
            return {"state": self._state, "vx": self._vx, "wz": self._wz}

    def release(self) -> None:
        """Client let go, or disconnected. Stop now, then hand the mux back."""
        with self._lock:
            if self._state == IDLE:
                return
            self._state = ZEROING
            self._vx = self._wz = 0.0
            self._zero_until = time.monotonic() + ZERO_S

    def set_limits(self, max_linear: float, max_angular: float) -> dict:
        with self._lock:
            self._max_linear = _clamp(abs(float(max_linear)), HARD_MAX_LINEAR)
            self._max_angular = _clamp(abs(float(max_angular)), HARD_MAX_ANGULAR)
            return {"max_linear": self._max_linear,
                    "max_angular": self._max_angular}

    def status(self) -> dict:
        with self._lock:
            return {
                "state": self._state,
                "vx": self._vx,
                "wz": self._wz,
                "max_linear": self._max_linear,
                "max_angular": self._max_angular,
                "hard_max_linear": HARD_MAX_LINEAR,
                "goal_active": self._goal_handle is not None,
            }

    # -- goals -------------------------------------------------------------

    def nav_ready(self) -> bool:
        return self._nav.server_is_ready()

    def send_goal(self, x: float, y: float, yaw: float) -> dict:
        """Send a NavigateToPose goal in the map frame.

        Same shape as scripts/go_to_object.py, including its complaint when
        the server is missing -- that message has already earned its keep.
        """
        if not self._nav.server_is_ready():
            raise RuntimeError(
                "NavigateToPose action server not available -- is `nav` up?")

        from geometry_msgs.msg import PoseStamped

        goal = self._NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = self._node.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation.z = math.sin(float(yaw) / 2.0)
        pose.pose.orientation.w = math.cos(float(yaw) / 2.0)
        goal.pose = pose

        future = self._nav.send_goal_async(goal)
        future.add_done_callback(self._on_goal_response)
        return {"status": "sent", "x": x, "y": y, "yaw": yaw}

    def _on_goal_response(self, future) -> None:
        try:
            handle = future.result()
        except Exception as exc:                        # noqa: BLE001
            logger.warning("goal send failed: %s", exc)
            return
        if not handle.accepted:
            logger.info("goal rejected by the BT navigator")
            return
        with self._goal_lock:
            self._goal_handle = handle
        handle.get_result_async().add_done_callback(self._on_goal_done)

    def _on_goal_done(self, _future) -> None:
        with self._goal_lock:
            self._goal_handle = None

    def cancel_goal(self) -> bool:
        with self._goal_lock:
            handle = self._goal_handle
        if handle is None:
            return False
        handle.cancel_goal_async()
        return True

    # -- lifecycle ---------------------------------------------------------

    @property
    def node(self):
        return self._node

    def destroy(self) -> None:
        try:
            self._node.destroy_node()
        except Exception:                               # noqa: BLE001
            pass


class ControlManager:
    """Runs ControlNode on its own executor thread."""

    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._executor = None
        self._control: Optional[ControlNode] = None
        self._ready = threading.Event()

    def start(self, timeout: float = 10.0) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="bridge-control")
        self._thread.start()
        if not self._ready.wait(timeout=timeout):
            logger.warning("control node did not report ready in %.0fs; "
                           "driving and goals will be unavailable", timeout)

    def _run(self) -> None:
        """Everything here is inside the try, and _ready is ALWAYS set.

        It was not, once: `import rclpy` sat above the try, so with no ROS on
        the path the thread died before setting the event and every caller
        waited out the full 10 s timeout. In the test suite, which builds a
        TestClient per test and so runs the lifespan per test, that turned a
        one-second run into a two-and-a-half-minute one that looked like a
        hang. A startup path that cannot reach its own "I failed" signal is a
        bug however unlikely the failure is.
        """
        try:
            import rclpy
            from rclpy.executors import SingleThreadedExecutor

            try:
                if not rclpy.ok():
                    rclpy.init()
            except Exception:                           # already initialised
                pass

            self._control = ControlNode()
            self._executor = SingleThreadedExecutor()
            self._executor.add_node(self._control.node)
        except Exception as exc:                        # noqa: BLE001
            logger.warning("control node unavailable (%s: %s) -- driving and "
                           "goals are disabled, the rest of the bridge is "
                           "unaffected", type(exc).__name__, exc)
            return
        finally:
            self._ready.set()

        try:
            self._executor.spin()
        except Exception as exc:                        # noqa: BLE001
            logger.info("control executor stopped: %s", exc)

    @property
    def control(self) -> Optional[ControlNode]:
        return self._control

    def stop(self) -> None:
        if self._control is not None:
            # Only pay the zero-burst wait if the channel is actually held.
            # Shutting down from IDLE has nothing to flush.
            if self._control.status()["state"] != IDLE:
                self._control.release()
                time.sleep(ZERO_S + 0.1)  # let the stop actually go out
        if self._executor is not None:
            self._executor.shutdown()
        if self._control is not None:
            self._control.destroy()
