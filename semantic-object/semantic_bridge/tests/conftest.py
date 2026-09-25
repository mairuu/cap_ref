"""Shared fixtures for the test suite. No rclpy import anywhere in here."""

from __future__ import annotations

import pytest

from semantic_bridge.config import settings
from semantic_bridge.models import Landmark, RobotPose, ScanSnapshot
from semantic_bridge.state import AppState


@pytest.fixture(autouse=True, scope="session")
def _no_stack_console():
    """Never start the process supervisor in tests.

    Two reasons, and the second is the one that bites. It is a facility for
    starting and stopping a robot; unit tests of REST handlers have no
    business with it. And it spawns subprocesses, while TestClient builds a
    NEW EVENT LOOP PER TEST -- asyncio's child watcher is process-global and
    stays bound to the first loop, so from the second test onwards every
    subprocess call waits out its full timeout instead of reaping. One test
    took 5.5 s; five took over two minutes and never finished.

    Production has exactly one event loop for the life of the process, so this
    is a test-harness problem rather than a bug in the supervisor -- but a
    suite that cannot finish is not a suite.
    """
    previous = settings.stack_enabled
    settings.stack_enabled = False
    yield
    settings.stack_enabled = previous


def make_landmark(i: int = 0, stale: bool = False) -> Landmark:
    return Landmark(
        id=f"id-{i}",
        class_label="chair",
        x=float(i),
        y=0.0,
        confidence=0.9,
        seen_count=i + 1,
        stale=stale,
    )


@pytest.fixture
def blank_state() -> AppState:
    return AppState()


@pytest.fixture
def populated_state() -> AppState:
    state = AppState()
    state.ros_connected = True
    state.latest_landmarks = [make_landmark(1)]
    state.latest_pose = RobotPose(x=1.5, y=0.5, yaw=0.0)
    state.latest_scan = ScanSnapshot(
        angle_min=-3.14159,
        angle_increment=0.03491,
        ranges=[2.0] * 180,
    )
    return state
