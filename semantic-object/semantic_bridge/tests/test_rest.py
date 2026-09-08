"""REST endpoint tests. Uses FastAPI TestClient; no ROS2 required."""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from semantic_bridge.main import app
from semantic_bridge.models import MapData, MapOrigin
from semantic_bridge.state import AppState, get_state
from tests.conftest import make_landmark


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def override(state: AppState):
    app.dependency_overrides[get_state] = lambda: state


def clear_overrides():
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_connected(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            resp = client.get("/api/health")
        clear_overrides()

        assert resp.status_code == 200
        body = resp.json()
        assert body["ros_connected"] is True
        assert body["landmark_count"] == 1
        assert body["robot_pose"] is not None
        assert body["robot_pose"]["x"] == pytest.approx(1.5)

    def test_disconnected(self, blank_state: AppState) -> None:
        override(blank_state)
        with TestClient(app) as client:
            resp = client.get("/api/health")
        clear_overrides()

        assert resp.status_code == 200
        body = resp.json()
        assert body["ros_connected"] is False
        assert body["landmark_count"] == 0
        assert body["robot_pose"] is None
        assert body["last_landmark_msg"] is None

    def test_response_schema(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            resp = client.get("/api/health")
        clear_overrides()

        body = resp.json()
        assert set(body.keys()) == {
            "ros_connected",
            "last_landmark_msg",
            "landmark_count",
            "robot_pose",
        }


# ---------------------------------------------------------------------------
# /api/landmarks
# ---------------------------------------------------------------------------


class TestLandmarks:
    def test_returns_landmark_list(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            resp = client.get("/api/landmarks")
        clear_overrides()

        assert resp.status_code == 200
        body = resp.json()
        assert "landmarks" in body
        assert len(body["landmarks"]) == 1
        lm = body["landmarks"][0]
        assert lm["class_label"] == "chair"
        assert lm["id"] == "id-1"

    def test_empty_when_no_ros(self, blank_state: AppState) -> None:
        override(blank_state)
        with TestClient(app) as client:
            resp = client.get("/api/landmarks")
        clear_overrides()

        assert resp.status_code == 200
        assert resp.json()["landmarks"] == []

    def test_landmark_schema_fields(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            resp = client.get("/api/landmarks")
        clear_overrides()

        lm = resp.json()["landmarks"][0]
        assert set(lm.keys()) == {
            "id",
            "class_label",
            "x",
            "y",
            "confidence",
            "seen_count",
            "stale",
        }


# ---------------------------------------------------------------------------
# /api/map
# ---------------------------------------------------------------------------


def _make_map_state() -> AppState:
    state = AppState()
    state.ros_connected = True
    raw = bytes([0, 100, 255, 0])  # 4 cells: free, occupied, unknown(-1→0xFF), free
    state.latest_map = MapData(
        width=2,
        height=2,
        resolution=0.05,
        origin=MapOrigin(x=-0.1, y=-0.1, yaw=0.0),
        data=base64.b64encode(raw).decode(),
    )
    return state


class TestMap:
    def test_503_when_no_map(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            resp = client.get("/api/map")
        clear_overrides()

        assert resp.status_code == 503

    def test_returns_map_when_available(self) -> None:
        state = _make_map_state()
        override(state)
        with TestClient(app) as client:
            resp = client.get("/api/map")
        clear_overrides()

        assert resp.status_code == 200
        body = resp.json()
        assert body["width"] == 2
        assert body["height"] == 2
        assert body["resolution"] == pytest.approx(0.05)
        assert "data" in body
        # Verify base64 round-trips correctly
        decoded = base64.b64decode(body["data"])
        assert decoded == bytes([0, 100, 255, 0])

    def test_map_schema_fields(self) -> None:
        state = _make_map_state()
        override(state)
        with TestClient(app) as client:
            resp = client.get("/api/map")
        clear_overrides()

        body = resp.json()
        assert set(body.keys()) == {"width", "height", "resolution", "origin", "data"}
        assert set(body["origin"].keys()) == {"x", "y", "yaw"}


# ---------------------------------------------------------------------------
# /api/clear
# ---------------------------------------------------------------------------


class TestClear:
    def test_503_when_disconnected(self, blank_state: AppState) -> None:
        override(blank_state)
        with TestClient(app) as client:
            resp = client.post("/api/clear")
        clear_overrides()

        assert resp.status_code == 503

    def test_503_when_service_unavailable(self, populated_state: AppState) -> None:
        # ROS connected but service call fails (fn returns False)
        populated_state._clear_service_fn = lambda: False
        override(populated_state)
        with TestClient(app) as client:
            resp = client.post("/api/clear")
        clear_overrides()

        assert resp.status_code == 503

    def test_200_when_service_succeeds(self, populated_state: AppState) -> None:
        populated_state._clear_service_fn = lambda: True
        override(populated_state)
        with TestClient(app) as client:
            resp = client.post("/api/clear")
        clear_overrides()

        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
