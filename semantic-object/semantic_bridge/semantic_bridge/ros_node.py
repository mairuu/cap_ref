"""
ROS2 node and lifecycle manager.

All rclpy imports are deferred inside functions so this module is importable
even when ROS2 is not installed (needed for tests and mock mode).
"""

from __future__ import annotations

import array
import base64
import json
import logging
import math
import threading
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .config import Settings
    from .state import AppState

logger = logging.getLogger(__name__)


def _quat_to_yaw(x: float, y: float, z: float, w: float) -> float:
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


class SemanticBridgeNode:
    """
    Thin wrapper around an rclpy.node.Node.

    Constructed only when rclpy is available and initialized.
    """

    def __init__(self, state: AppState, config: Settings) -> None:
        import rclpy.node
        import tf2_ros
        from nav_msgs.msg import OccupancyGrid
        from sensor_msgs.msg import CompressedImage, LaserScan
        from std_msgs.msg import String
        from std_srvs.srv import Empty

        from .models import Landmark, MapData, MapOrigin, RobotPose, ScanSnapshot

        self._state = state
        self._config = config

        class _Node(rclpy.node.Node):  # type: ignore[misc]
            pass

        self._node = _Node("semantic_bridge")
        node = self._node

        # temp !!IMPORTANT
        state.set_ros_connected(True)

        # TF
        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, node)
        node.create_timer(0.1, self._update_pose)

        # Subscriptions
        node.create_subscription(String, "/semantic_landmarks", self._on_landmarks, 10)
        node.create_subscription(OccupancyGrid, "/map", self._on_map, 1)
        node.create_subscription(LaserScan, "/scan", self._on_scan, 10)
        node.create_subscription(
            CompressedImage, "/camera/image_raw/compressed", self._on_camera, 10
        )

        # Service client
        self._clear_client = node.create_client(Empty, "clear_landmarks")
        state._clear_service_fn = self.call_clear_sync

        # keep imports in local scope available to callbacks
        self._Landmark = Landmark
        self._RobotPose = RobotPose
        self._ScanSnapshot = ScanSnapshot
        self._MapData = MapData
        self._MapOrigin = MapOrigin

    # ------------------------------------------------------------------
    # Expose the underlying rclpy node so RosManager can call spin/destroy
    # ------------------------------------------------------------------

    @property
    def node(self):  # type: ignore[return]
        return self._node

    def destroy(self) -> None:
        self._node.destroy_node()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_landmarks(self, msg) -> None:
        try:
            data = json.loads(msg.data)
            landmarks = [self._Landmark(**lm) for lm in data.get("landmarks", [])]
            self._state.update_landmarks(landmarks)
        except Exception as exc:
            logger.warning("Failed to parse /semantic_landmarks: %s", exc)

    def _on_map(self, msg) -> None:
        try:
            raw = array.array("b", msg.data)
            b64 = base64.b64encode(raw.tobytes()).decode()
            q = msg.info.origin.orientation
            yaw = _quat_to_yaw(q.x, q.y, q.z, q.w)
            map_data = self._MapData(
                width=msg.info.width,
                height=msg.info.height,
                resolution=msg.info.resolution,
                origin=self._MapOrigin(
                    x=msg.info.origin.position.x,
                    y=msg.info.origin.position.y,
                    yaw=yaw,
                ),
                data=b64,
            )
            self._state.update_map(map_data)
        except Exception as exc:
            logger.warning("Failed to process /map: %s", exc)

    def _on_scan(self, msg) -> None:
        try:
            ranges = list(msg.ranges)
            target = self._config.scan_downsample_rays
            n = len(ranges)
            if n > target:
                step = max(1, n // target)
                ranges = ranges[::step][:target]
                angle_increment = msg.angle_increment * step
            else:
                angle_increment = msg.angle_increment
            scan = self._ScanSnapshot(
                angle_min=msg.angle_min,
                angle_increment=angle_increment,
                ranges=ranges,
            )
            self._state.update_scan(scan)
        except Exception as exc:
            logger.warning("Failed to process /scan: %s", exc)

    def _on_camera(self, msg) -> None:
        self._state.broadcast_camera(bytes(msg.data))

    def _update_pose(self) -> None:
        try:
            import rclpy.time

            t = self._tf_buffer.lookup_transform(
                "map", "base_link", rclpy.time.Time()
            )
            tr = t.transform.translation
            rot = t.transform.rotation
            yaw = _quat_to_yaw(rot.x, rot.y, rot.z, rot.w)
            self._state.update_pose(
                self._RobotPose(x=tr.x, y=tr.y, yaw=yaw)
            )
        except Exception:
            pass  # TF not yet available; pose stays None

    # ------------------------------------------------------------------
    # Service call (blocking, runs in executor from the REST route)
    # ------------------------------------------------------------------

    def call_clear_sync(self, timeout: float = 5.0) -> bool:
        if not self._clear_client.wait_for_service(timeout_sec=1.0):
            logger.warning("clear_landmarks service not available")
            return False
        from std_srvs.srv import Empty

        req = Empty.Request()
        future = self._clear_client.call_async(req)
        event = threading.Event()
        future.add_done_callback(lambda _: event.set())
        if not event.wait(timeout=timeout):
            logger.warning("clear_landmarks service call timed out")
            return False
        return future.result() is not None


class RosManager:
    """
    Manages the rclpy node lifecycle in a dedicated daemon thread.

    On failure (ROS2 not installed / DDS not reachable) it logs a warning
    and retries every `config.ros_retry_interval_s` seconds.
    """

    def __init__(self, state: AppState, config: Settings) -> None:
        self._state = state
        self._config = config
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._bridge_node: Optional[SemanticBridgeNode] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._spin_loop, daemon=True, name="ros-spin"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._state.set_ros_connected(False)
        try:
            import rclpy

            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _spin_loop(self) -> None:
        while self._running:
            try:
                self._init_and_spin()
            except Exception as exc:
                logger.warning(
                    "ROS2 unavailable (%s). Retrying in %ds.",
                    exc,
                    self._config.ros_retry_interval_s,
                )
                self._state.set_ros_connected(False)
                self._cleanup_rclpy()
                time.sleep(self._config.ros_retry_interval_s)

    def _init_and_spin(self) -> None:
        import rclpy

        if not rclpy.ok():
            rclpy.init()

        self._bridge_node = SemanticBridgeNode(self._state, self._config)
        logger.info("ROS2 node started")

        try:
            rclpy.spin(self._bridge_node.node)
        finally:
            self._bridge_node.destroy()
            self._bridge_node = None
            self._state._clear_service_fn = None

    def _cleanup_rclpy(self) -> None:
        try:
            import rclpy

            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass
