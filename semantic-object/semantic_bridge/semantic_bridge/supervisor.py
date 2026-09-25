"""Operator console back end: drive the stack THROUGH tmux, never own it.

WHY TMUX AND NOT SUBPROCESSES. The obvious design holds a process group per
component in this process's memory. Then uvicorn restarts -- a reload, an
exception escaping lifespan, a stopped terminal -- and every component it
started is orphaned, still running, and unstoppable, because the only handle
to them died with the supervisor. On the next boot it finds a "foreign stack"
that it started itself. That is precisely the failure this console exists to
prevent (STATE.md: "the robot still crawls because a pre-21-Sep `make real` is
still up"), reintroduced by the tool meant to prevent it.

tmux removes the failure mode and most of the code with it:

    stop          tmux send-keys C-c   -- SIGINT to the pane's foreground
                                          process group, byte for byte what
                                          Ctrl-C in a terminal does, which is
                                          the shutdown path this stack has
                                          been exercised on every day
    logs          tmux capture-pane    -- the ring buffer, for free
    exit codes    #{pane_dead_status}  -- with remain-on-exit, a crashed pane
                                          KEEPS its output instead of vanishing
    ownership     the tmux server      -- survives anything happening to us
    escape hatch  tmux attach          -- the operator can always take over

It also means `make up` and this console are the same mechanism, so a stack
started from the terminal is fully visible and controllable here, and vice
versa. Nothing has to know which one started it.

WHAT THIS DOES NOT DO, on purpose:

  * It does not restart `real` or `slam`. Stopping `real` resets the ESP32 over
    DTR, and a restart that races that reset gives "device busy" and never
    comes back -- mid-demo, recoverable only from a terminal. Restarting `slam`
    silently throws the map away. Both are start/stop, and stop asks first.
  * It does not auto-restart anything that crashes. `on_exit=Shutdown` in
    navigation.launch.py is a deliberate design whose intended failure mode is
    a STOPPED robot; an auto-restarter fights that, and can bring Nav2 back up
    against stale costmaps. Crashes are reported loudly and left alone.
  * It does not manage `bridge` or `ui`. The bridge is this process. The UI is
    what you are reading this in.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
import signal
import tempfile
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Component states. `stopped` means "no window"; `crashed` means "a dead window
# is still there, and its output with it".
STOPPED, STARTING, READY, CRASHED, STOPPING = (
    "stopped", "starting", "ready", "crashed", "stopping")

# The window that holds the session open while remain-on-exit is being set.
# Without it, a first component that dies in under a second takes the whole
# session down before the option can land. See the Makefile's `up`.
BOOT_WINDOW = "__boot"

# Per-component POLICY, which is a different thing from the readiness SPECS in
# stack_wait.py: those say what "up" means, these say what the console is
# allowed to do about it.
POLICY: dict[str, dict] = {
    "real": {
        "restartable": False,
        "devices": ["/dev/esp32", "/dev/ydlidar"],
        "warn": "Stopping this resets the ESP32 over DTR and drops odometry, "
                "TF and /scan. Everything above it will fail.",
    },
    "slam": {
        "restartable": False,
        "warn": "Stopping this DISCARDS THE MAP. There is no undo; save it "
                "first with `make save-map`.",
    },
    "nav": {
        "restartable": True,
        "warn": "twist_mux and teleop_speed_guard live here, so stopping it "
                "takes the e-stop chain down with it. `make teleop-nav` will "
                "do nothing until it is back.",
    },
    "yolo": {"restartable": True, "devices": ["/dev/video0"]},
    "semantic": {"restartable": True},
    "explore": {"restartable": True},
    "bag": {
        "restartable": False,
        "warn": "Stopping this closes the recording.",
    },
    # Not ours to manage: one is this process, the other is serving the page.
    "bridge": {"managed": False},
    "ui": {"managed": False},
}


@dataclass
class Component:
    name: str
    state: str = STOPPED
    dead_status: Optional[int] = None
    pid: Optional[int] = None
    ready: bool = False
    checks: list = field(default_factory=list)
    since: Optional[float] = None

    @property
    def managed(self) -> bool:
        return POLICY.get(self.name, {}).get("managed", True)

    @property
    def restartable(self) -> bool:
        return POLICY.get(self.name, {}).get("restartable", True)

    def as_dict(self) -> dict:
        pol = POLICY.get(self.name, {})
        return {
            "name": self.name,
            "state": self.state,
            "ready": self.ready,
            "dead_status": self.dead_status,
            "pid": self.pid,
            "uptime_s": round(time.time() - self.since, 1) if self.since else None,
            "managed": self.managed,
            "restartable": self.restartable,
            "warn": pol.get("warn"),
            "devices": pol.get("devices", []),
            "checks": self.checks,
        }


class SupervisorError(RuntimeError):
    pass


class Supervisor:
    def __init__(self, settings) -> None:
        self._s = settings
        self._session = settings.tmux_session
        self._components: dict[str, Component] = {}
        self._intentional: set[str] = set()
        self._busy: dict[str, asyncio.Lock] = {}
        self._events: list[dict] = []
        self._profile_cache: dict[str, list[str]] = {}
        self._last_readiness = 0.0
        self._poller: Optional[asyncio.Task] = None
        self._listeners: set[asyncio.Queue] = set()

    # -- process plumbing --------------------------------------------------

    async def _run(self, *argv: str, timeout: float = 15.0) -> tuple[int, str]:
        """Run a command and collect its output VIA A FILE, not a pipe.

        This looks like the long way round and is not. `tmux new-session`
        starts a tmux SERVER, which daemonizes holding the file descriptors it
        was given -- so with a pipe, communicate() waits for a stdout that will
        not close until the tmux server exits, i.e. never. The command has
        succeeded and we hang for the full timeout and then report failure.
        Cost 20 minutes on 23 Sep; the symptom was `new-session` timing out
        while the session it created was demonstrably there.

        Waiting on proc.wait() waits for the PROCESS. A daemon that inherited
        the fd is then free to hold it as long as it likes.
        """
        with tempfile.TemporaryFile() as fh:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=fh,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=str(self._s.cap_ws),
            )
            try:
                rc = await asyncio.wait_for(proc.wait(), timeout)
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except ProcessLookupError:
                    pass                     # already gone; nothing to kill
                return 124, f"timed out after {timeout}s: {' '.join(argv)}"
            fh.seek(0)
            return rc or 0, fh.read().decode("utf-8", "replace")

    async def _tmux(self, *args: str, timeout: float = 15.0) -> tuple[int, str]:
        return await self._run("tmux", *args, timeout=timeout)

    def _child_env_args(self) -> list[str]:
        """`tmux new-window -e` arguments carrying the ROS environment.

        NOT AN OPTIONAL BELT-AND-BRACES. A tmux window inherits the environment
        of the tmux SERVER, which belongs to whoever started it first -- and
        that may be a session with no ROS variables at all. STATE.md: "anything
        launched from a stripped environment will land on domain 0 and see
        nothing", which presents as a stack that starts perfectly and is
        invisible to everything else. Naming the variables explicitly on every
        window makes that impossible regardless of who owns the server.
        """
        args: list[str] = []
        for key in ("ROS_DOMAIN_ID", "ROS_LOCALHOST_ONLY",
                    "FASTRTPS_DEFAULT_PROFILES_FILE", "RMW_IMPLEMENTATION"):
            val = os.environ.get(key)
            if val:
                args += ["-e", f"{key}={val}"]
        return args

    def assert_environment(self) -> None:
        """Refuse to start an invisible stack."""
        if not os.environ.get("ROS_DOMAIN_ID"):
            raise SupervisorError(
                "ROS_DOMAIN_ID is unset in the bridge's environment, so "
                "anything started from here would land on domain 0 and be "
                "invisible to RViz, to teleop and to the rest of the stack. "
                "Start the bridge from a normal login shell (`make bridge`), "
                "not from a unit or a container with a stripped environment.")

    # -- reading tmux ------------------------------------------------------

    async def session_exists(self) -> bool:
        rc, _ = await self._tmux("has-session", "-t", self._session, timeout=5)
        return rc == 0

    async def _windows(self) -> dict[str, dict]:
        rc, out = await self._tmux(
            "list-windows", "-t", self._session,
            "-F", "#{window_name}\t#{pane_dead}\t#{pane_dead_status}\t#{pane_pid}",
            timeout=5)
        if rc != 0:
            return {}
        found = {}
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 4 or parts[0] == BOOT_WINDOW:
                continue
            name, dead, status, pid = parts
            found[name] = {
                "dead": dead == "1",
                "status": int(status) if status.strip().isdigit() else None,
                "pid": int(pid) if pid.strip().isdigit() else None,
            }
        return found

    async def profile(self, name: str) -> list[str]:
        """Ask the Makefile, which is where a profile is actually defined."""
        if name in self._profile_cache:
            return self._profile_cache[name]
        rc, out = await self._run("make", "-s", "print-stack", f"PROFILE={name}")
        names = out.split() if rc == 0 else []
        if not names:
            raise SupervisorError(f"unknown profile {name!r}")
        self._profile_cache[name] = names
        return names

    # -- readiness ---------------------------------------------------------

    async def readiness(self, names: list[str], timeout: float = 90.0) -> dict:
        """Run the SAME gate `make up` uses. One process, all components.

        stack_wait.py needs /opt/ros sourced but NOT install/setup.bash (it
        resolves message types from the graph rather than importing them), and
        this process already has that -- verified 22 Sep. So it is exec'd
        directly rather than through `ros2 run`, which would need the overlay.
        """
        if not names:
            return {}
        argv = ["python3", str(self._s.stack_wait), "--once", "--json", *names]
        rc, out = await self._run(*argv, timeout=timeout)
        # stdout carries the JSON; the human table goes to stderr, which is
        # merged into the same stream, so take the last JSON array.
        start = out.find("[")
        if start < 0:
            logger.warning("stack_wait produced no JSON (rc=%s): %s", rc, out[-400:])
            return {}
        import json
        try:
            report = json.loads(out[start:])
        except ValueError as exc:
            logger.warning("stack_wait JSON unparseable: %s", exc)
            return {}
        return {r["component"]: r for r in report}

    # -- state -------------------------------------------------------------

    async def refresh(self, with_readiness: bool = False) -> dict:
        names = await self.profile("demo")
        # Anything running that is not in the demo profile still belongs on the
        # panel -- `explore` and `bag` are started deliberately, not by profile.
        windows = await self._windows()
        for extra in windows:
            if extra not in names:
                names = names + [extra]

        for name in names:
            comp = self._components.setdefault(name, Component(name=name))
            win = windows.get(name)
            if win is None:
                comp.state = STOPPED
                comp.ready = False
                comp.pid = None
                comp.since = None
                comp.dead_status = None
                comp.checks = []
            elif win["dead"]:
                comp.state = CRASHED
                comp.ready = False
                comp.dead_status = win["status"]
                comp.pid = None
            else:
                comp.pid = win["pid"]
                if comp.since is None:
                    comp.since = time.time()
                if comp.state in (STOPPED, CRASHED):
                    comp.state = STARTING
                comp.dead_status = None

        if with_readiness:
            live = [n for n, c in self._components.items()
                    if c.state in (STARTING, READY)]
            report = await self.readiness(live)
            for name, res in report.items():
                comp = self._components.get(name)
                if comp is None:
                    continue
                comp.ready = bool(res.get("ready"))
                comp.checks = res.get("checks", [])
                if comp.state in (STARTING, READY):
                    comp.state = READY if comp.ready else STARTING
            self._last_readiness = time.time()

        return self.snapshot()

    def snapshot(self) -> dict:
        return {
            "session": self._session,
            "components": [c.as_dict() for c in self._components.values()],
            "events": self._events[-40:],
            "readiness_age_s": (round(time.time() - self._last_readiness, 1)
                                if self._last_readiness else None),
        }

    def _event(self, level: str, text: str) -> None:
        self._events.append({"t": time.time(), "level": level, "text": text})
        del self._events[:-200]
        logger.info("stack: %s", text)

    # -- control -----------------------------------------------------------

    def _lock(self, name: str) -> asyncio.Lock:
        return self._busy.setdefault(name, asyncio.Lock())

    def _check_managed(self, name: str) -> None:
        if not self._s.stack_enabled:
            raise SupervisorError("stack control is disabled (CAP_STACK_ENABLED=0)")
        if name not in POLICY:
            raise SupervisorError(f"unknown component {name!r}")
        if not POLICY[name].get("managed", True):
            raise SupervisorError(
                f"{name} is not managed from here -- "
                + ("it is this process." if name == "bridge"
                   else "it is serving the page you are reading."))

    async def _ensure_session(self) -> None:
        if await self.session_exists():
            return
        await self._tmux("new-session", "-d", "-s", self._session,
                         "-n", BOOT_WINDOW, "-c", str(self._s.cap_ws),
                         "sleep infinity")
        # Server-global, and set while a window that cannot die is holding the
        # session open. Same reasoning as the Makefile's `up`.
        await self._tmux("set-option", "-g", "remain-on-exit", "on")

    async def start(self, name: str) -> dict:
        self._check_managed(name)
        self.assert_environment()
        async with self._lock(name):
            windows = await self._windows()
            if name in windows and not windows[name]["dead"]:
                raise SupervisorError(f"{name} is already running")
            if name in windows:                      # dead window in the way
                await self._tmux("kill-window", "-t", f"{self._session}:{name}")

            await self._ensure_session()
            # -o build: every target has `build` as a prerequisite, so without
            # it each start runs colcon again -- and two starts at once run two
            # colcon builds in one workspace, which has no lock.
            rc, out = await self._tmux(
                "new-window", "-d", "-t", self._session, "-n", name,
                "-c", str(self._s.cap_ws), *self._child_env_args(),
                f"make -o build {shlex.quote(name)}")
            if rc != 0:
                raise SupervisorError(f"tmux refused to start {name}: {out.strip()}")
            await self._tmux("kill-window", "-t", f"{self._session}:{BOOT_WINDOW}")

            comp = self._components.setdefault(name, Component(name=name))
            comp.state = STARTING
            comp.since = time.time()
            comp.ready = False
            self._event("info", f"{name}: starting")
            return comp.as_dict()

    async def stop(self, name: str) -> dict:
        self._check_managed(name)
        async with self._lock(name):
            windows = await self._windows()
            if name not in windows:
                raise SupervisorError(f"{name} is not running")

            comp = self._components.setdefault(name, Component(name=name))
            comp.state = STOPPING
            self._intentional.add(name)
            target = f"{self._session}:{name}"
            pane_pid = windows[name]["pid"]

            if not windows[name]["dead"]:
                # SIGINT to the pane's foreground process group. Exactly one:
                # a second one makes ros2 launch escalate to SIGTERM and lose
                # graceful node shutdown.
                await self._tmux("send-keys", "-t", target, "C-c")
                await self._await_group_gone(pane_pid, timeout=20.0)

            await self._await_devices_released(name, timeout=15.0)
            await self._tmux("kill-window", "-t", target)

            comp.state = STOPPED
            comp.ready = False
            comp.pid = None
            comp.since = None
            comp.checks = []
            self._intentional.discard(name)
            self._event("info", f"{name}: stopped")
            return comp.as_dict()

    async def restart(self, name: str) -> dict:
        if not POLICY.get(name, {}).get("restartable", True):
            raise SupervisorError(
                f"{name} is deliberately not restartable from here. "
                + (POLICY[name].get("warn") or "") +
                " Stop it and start it again if you really mean to.")
        try:
            await self.stop(name)
        except SupervisorError as exc:
            if "not running" not in str(exc):
                raise
        return await self.start(name)

    async def _await_group_gone(self, pane_pid: Optional[int],
                                timeout: float) -> bool:
        """Wait for the pane's whole PROCESS GROUP, escalating if it will not go.

        Not the pane, and not `make`. bash exec-optimises the recipe away, so
        the pane's process IS `make`, and GNU make re-raises a fatal signal and
        exits in milliseconds while ros2 launch is still stopping nodes -- and
        `#{pane_dead}` follows `make`, so it goes true while the stack is still
        up. Measured on the bridge 23 Sep: the window was gone and reported
        stopped while uvicorn was still running, and one such process was still
        alive two hours later.

        tmux gives each pane its own process group, so killpg(pgid, 0) is true
        until every process in that window is gone. That is the only thing
        "stopped" can honestly mean.
        """
        if pane_pid is None:
            return True

        def alive() -> bool:
            try:
                os.killpg(pane_pid, 0)
                return True
            except ProcessLookupError:
                return False
            except PermissionError:
                return True

        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if not alive():
                return True
            await asyncio.sleep(0.25)

        for sig in (signal.SIGTERM, signal.SIGKILL):
            if not alive():
                return True
            self._event("warn", f"pane group {pane_pid} ignored SIGINT; "
                                f"sending {sig.name}")
            try:
                os.killpg(pane_pid, sig)
            except ProcessLookupError:
                return True
            await asyncio.sleep(2.0 if sig is signal.SIGTERM else 1.0)
        return not alive()

    async def _await_devices_released(self, name: str, timeout: float) -> None:
        """And then wait for the kernel, which is the only witness that cannot lie.

        An orphaned ros2_control_node still holding /dev/esp32 is what makes
        the NEXT start fail with something that reads like a hardware fault.
        """
        devices = POLICY.get(name, {}).get("devices", [])
        if not devices:
            return
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            held = []
            for dev in devices:
                rc, _ = await self._run("fuser", "-s", dev, timeout=5)
                if rc == 0:
                    held.append(dev)
            if not held:
                return
            await asyncio.sleep(0.5)
        self._event("warn", f"{name}: stopped, but {', '.join(devices)} "
                            f"still held -- something did not shut down")

    async def logs(self, name: str, lines: Optional[int] = None) -> str:
        n = lines or self._s.stack_log_lines
        rc, out = await self._tmux("capture-pane", "-p", "-t",
                                   f"{self._session}:{name}", "-S", f"-{n}",
                                   timeout=10)
        if rc != 0:
            return ""
        return "\n".join(l.rstrip() for l in out.splitlines()).strip("\n")

    # -- bulk --------------------------------------------------------------

    async def start_profile(self, profile: str) -> None:
        """Ordered, gated, serial. Exactly what `make up` does."""
        names = await self.profile(profile)
        self.assert_environment()
        self._event("info", f"starting profile '{profile}': {' '.join(names)}")
        for name in names:
            if not POLICY.get(name, {}).get("managed", True):
                self._event("info", f"{name}: skipped (not managed from here)")
                continue
            windows = await self._windows()
            if name in windows and not windows[name]["dead"]:
                self._event("info", f"{name}: already up")
                continue
            await self.start(name)
            report = await self.readiness([name], timeout=180.0)
            res = report.get(name, {})
            comp = self._components[name]
            comp.checks = res.get("checks", [])
            comp.ready = bool(res.get("ready"))
            if not comp.ready:
                comp.state = STARTING
                bad = [c["detail"] for c in comp.checks if not c.get("ok")]
                self._event("error",
                            f"{name}: gate failed -- {'; '.join(bad) or 'no detail'}. "
                            f"Everything already up is left running.")
                return
            comp.state = READY
            self._event("info", f"{name}: ready")
        self._event("info", f"profile '{profile}' up")

    async def stop_profile(self, profile: str) -> None:
        names = await self.profile(profile)
        for name in reversed(names):
            if not POLICY.get(name, {}).get("managed", True):
                continue
            try:
                await self.stop(name)
            except SupervisorError as exc:
                if "not running" not in str(exc):
                    self._event("warn", f"{name}: {exc}")

    # -- background poller -------------------------------------------------

    def start_poller(self) -> None:
        if self._poller is None:
            self._poller = asyncio.create_task(self._poll_loop())

    async def stop_poller(self) -> None:
        if self._poller is not None:
            self._poller.cancel()
            try:
                await self._poller
            except asyncio.CancelledError:
                pass
            self._poller = None

    async def _poll_loop(self) -> None:
        while True:
            try:
                due = (time.time() - self._last_readiness) >= self._s.stack_readiness_s
                await self.refresh(with_readiness=due)
                self._publish()
            except asyncio.CancelledError:
                raise
            except Exception as exc:                   # never kill the poller
                logger.warning("stack poll failed: %s", exc)
            await asyncio.sleep(self._s.stack_poll_s)

    def register(self, q: asyncio.Queue) -> None:
        self._listeners.add(q)

    def unregister(self, q: asyncio.Queue) -> None:
        self._listeners.discard(q)

    def _publish(self) -> None:
        if not self._listeners:
            return
        snap = self.snapshot()
        for q in list(self._listeners):
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(snap)
            except asyncio.QueueFull:
                pass
