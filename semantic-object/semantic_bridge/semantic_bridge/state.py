from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .models import Landmark, MapData, RobotPose, ScanSnapshot


class AppState:
    def __init__(self) -> None:
        self._lock = threading.Lock()

        # connection bookkeeping
        self.ros_connected: bool = False
        self.last_landmark_msg: Optional[datetime] = None

        # latest data per topic (None until first message)
        self.latest_landmarks: list[Landmark] = []
        self.latest_pose: Optional[RobotPose] = None
        self.latest_scan: Optional[ScanSnapshot] = None
        self.latest_map: Optional[MapData] = None

        # camera fan-out: one asyncio.Queue per connected /ws/camera client
        self._camera_queues: set[asyncio.Queue] = set()

        # set in main.py lifespan so ROS callbacks can cross the thread boundary
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        # set by the ROS node after it creates the service client
        self._clear_service_fn: Optional[Callable[[], bool]] = None

    # ------------------------------------------------------------------
    # Thread-safe reads
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        """Return a shallow copy of all mutable fields under the lock."""
        with self._lock:
            return {
                "ros_connected": self.ros_connected,
                "last_landmark_msg": self.last_landmark_msg,
                "landmark_count": len(self.latest_landmarks),
                "landmarks": list(self.latest_landmarks),
                "pose": self.latest_pose,
                "scan": self.latest_scan,
            }

    def snapshot_map(self) -> Optional[MapData]:
        with self._lock:
            return self.latest_map

    # ------------------------------------------------------------------
    # Thread-safe writes (called from rclpy callbacks in the ROS thread)
    # ------------------------------------------------------------------

    def set_ros_connected(self, value: bool) -> None:
        with self._lock:
            self.ros_connected = value

    def update_landmarks(self, landmarks: list[Landmark]) -> None:
        with self._lock:
            self.latest_landmarks = landmarks
            self.last_landmark_msg = datetime.now(UTC)
            self.ros_connected = True

    def update_pose(self, pose: RobotPose) -> None:
        with self._lock:
            self.latest_pose = pose

    def update_scan(self, scan: ScanSnapshot) -> None:
        with self._lock:
            self.latest_scan = scan

    def update_map(self, map_data: MapData) -> None:
        with self._lock:
            self.latest_map = map_data

    # ------------------------------------------------------------------
    # Camera WebSocket fan-out
    # ------------------------------------------------------------------

    def register_camera_queue(self, q: asyncio.Queue) -> None:
        with self._lock:
            self._camera_queues.add(q)

    def unregister_camera_queue(self, q: asyncio.Queue) -> None:
        with self._lock:
            self._camera_queues.discard(q)

    def broadcast_camera(self, frame: bytes) -> None:
        """Called from the ROS thread; schedules delivery onto the event loop."""
        loop = self._event_loop
        if loop is None or not loop.is_running():
            return
        with self._lock:
            queues = set(self._camera_queues)

        def _push() -> None:
            for q in queues:
                _enqueue_dropping_oldest(q, frame)

        loop.call_soon_threadsafe(_push)

    async def broadcast_camera_async(self, frame: bytes) -> None:
        """Called from an asyncio coroutine (mock publisher)."""
        with self._lock:
            queues = set(self._camera_queues)
        for q in queues:
            _enqueue_dropping_oldest(q, frame)

    # ------------------------------------------------------------------
    # ROS service call (async wrapper)
    # ------------------------------------------------------------------

    async def call_clear_service(self) -> bool:
        fn = self._clear_service_fn
        if fn is None:
            return False
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, fn)


def _enqueue_dropping_oldest(q: asyncio.Queue, item: object) -> None:
    """Put item in queue; if full, drop the oldest entry first."""
    try:
        q.put_nowait(item)
    except asyncio.QueueFull:
        try:
            q.get_nowait()
        except asyncio.QueueEmpty:
            pass
        try:
            q.put_nowait(item)
        except asyncio.QueueFull:
            pass


# ---------------------------------------------------------------------------
# Module-level singleton + FastAPI dependency
# ---------------------------------------------------------------------------

_app_state = AppState()


def get_state() -> AppState:
    """FastAPI dependency returning the shared application state."""
    return _app_state
