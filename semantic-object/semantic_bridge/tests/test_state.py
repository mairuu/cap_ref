"""Thread-safety and container correctness tests. No ROS2 needed."""

from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime

import pytest

from semantic_bridge.models import Landmark, RobotPose, ScanSnapshot
from semantic_bridge.state import AppState, _enqueue_dropping_oldest
from tests.conftest import make_landmark


# ---------------------------------------------------------------------------
# Basic defaults
# ---------------------------------------------------------------------------


def test_default_ros_connected_false(blank_state: AppState) -> None:
    assert blank_state.ros_connected is False


def test_default_landmark_list_empty(blank_state: AppState) -> None:
    assert blank_state.latest_landmarks == []


def test_default_pose_is_none(blank_state: AppState) -> None:
    assert blank_state.latest_pose is None


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


def test_update_landmarks_sets_timestamp(blank_state: AppState) -> None:
    before = datetime.now(UTC)
    blank_state.update_landmarks([make_landmark(0)])
    after = datetime.now(UTC)
    assert blank_state.last_landmark_msg is not None
    assert before <= blank_state.last_landmark_msg <= after


def test_update_landmarks_marks_connected(blank_state: AppState) -> None:
    blank_state.update_landmarks([make_landmark()])
    assert blank_state.ros_connected is True


def test_set_ros_connected(blank_state: AppState) -> None:
    blank_state.set_ros_connected(True)
    assert blank_state.ros_connected is True
    blank_state.set_ros_connected(False)
    assert blank_state.ros_connected is False


# ---------------------------------------------------------------------------
# snapshot()
# ---------------------------------------------------------------------------


def test_snapshot_reflects_updates(populated_state: AppState) -> None:
    snap = populated_state.snapshot()
    assert snap["ros_connected"] is True
    assert snap["landmark_count"] == 1
    assert len(snap["landmarks"]) == 1
    assert snap["pose"] is not None
    assert snap["scan"] is not None


def test_snapshot_returns_copy_of_list(populated_state: AppState) -> None:
    snap = populated_state.snapshot()
    # Mutating the returned list must not affect internal state
    snap["landmarks"].clear()
    assert len(populated_state.latest_landmarks) == 1


# ---------------------------------------------------------------------------
# Camera queue management
# ---------------------------------------------------------------------------


def test_register_and_unregister_camera_queue(blank_state: AppState) -> None:
    q: asyncio.Queue = asyncio.Queue(maxsize=2)
    blank_state.register_camera_queue(q)
    assert q in blank_state._camera_queues
    blank_state.unregister_camera_queue(q)
    assert q not in blank_state._camera_queues


def test_unregister_nonexistent_is_noop(blank_state: AppState) -> None:
    q: asyncio.Queue = asyncio.Queue(maxsize=2)
    blank_state.unregister_camera_queue(q)  # should not raise


# ---------------------------------------------------------------------------
# _enqueue_dropping_oldest helper
# ---------------------------------------------------------------------------


def test_enqueue_drops_oldest_when_full() -> None:
    q: asyncio.Queue = asyncio.Queue(maxsize=2)
    q.put_nowait(b"frame-1")
    q.put_nowait(b"frame-2")
    # Queue full; adding frame-3 should drop frame-1
    _enqueue_dropping_oldest(q, b"frame-3")
    assert q.qsize() == 2
    assert q.get_nowait() == b"frame-2"
    assert q.get_nowait() == b"frame-3"


# ---------------------------------------------------------------------------
# Thread-safety: concurrent reads and writes
# ---------------------------------------------------------------------------


def test_concurrent_reads_and_writes() -> None:
    """N writer threads and M reader threads must not corrupt state."""
    state = AppState()
    errors: list[Exception] = []
    iters = 200

    def writer(i: int) -> None:
        try:
            for j in range(iters):
                state.update_landmarks([make_landmark(j)])
                state.update_pose(RobotPose(x=float(j), y=0.0, yaw=0.0))
        except Exception as exc:
            errors.append(exc)

    def reader() -> None:
        try:
            for _ in range(iters):
                snap = state.snapshot()
                assert isinstance(snap["landmarks"], list)
                assert isinstance(snap["landmark_count"], int)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
    threads += [threading.Thread(target=reader) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Thread errors: {errors}"


def test_concurrent_queue_register_unregister() -> None:
    """Concurrent queue registration/deregistration must not raise."""
    state = AppState()
    errors: list[Exception] = []

    def register_loop() -> None:
        try:
            for _ in range(100):
                q: asyncio.Queue = asyncio.Queue(maxsize=2)
                state.register_camera_queue(q)
                state.unregister_camera_queue(q)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=register_loop) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
