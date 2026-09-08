"""Shared fixtures for the test suite. No rclpy import anywhere in here."""

from __future__ import annotations

import pytest

from semantic_bridge.models import Landmark, RobotPose, ScanSnapshot
from semantic_bridge.state import AppState


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
