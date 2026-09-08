"""WebSocket endpoint tests. Uses Starlette TestClient; no ROS2 required."""

from __future__ import annotations

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from semantic_bridge.main import app
from semantic_bridge.state import AppState, get_state
from tests.conftest import make_landmark


def override(state: AppState):
    app.dependency_overrides[get_state] = lambda: state


def clear_overrides():
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /ws/state — message schema
# ---------------------------------------------------------------------------


class TestStateWebSocket:
    def test_first_message_schema(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                msg = ws.receive_json()
        clear_overrides()

        assert "timestamp" in msg
        assert "robot_pose" in msg
        assert "landmarks" in msg
        assert "scan" in msg

    def test_landmarks_in_message(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                msg = ws.receive_json()
        clear_overrides()

        assert len(msg["landmarks"]) == 1
        lm = msg["landmarks"][0]
        assert lm["class_label"] == "chair"
        assert set(lm.keys()) == {
            "id", "class_label", "x", "y", "confidence", "seen_count", "stale"
        }

    def test_robot_pose_in_message(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                msg = ws.receive_json()
        clear_overrides()

        pose = msg["robot_pose"]
        assert pose["x"] == pytest.approx(1.5)
        assert "yaw" in pose

    def test_pose_is_null_when_unavailable(self, blank_state: AppState) -> None:
        override(blank_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                msg = ws.receive_json()
        clear_overrides()

        assert msg["robot_pose"] is None

    def test_scan_in_message(self, populated_state: AppState) -> None:
        override(populated_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                msg = ws.receive_json()
        clear_overrides()

        scan = msg["scan"]
        assert "angle_min" in scan
        assert "angle_increment" in scan
        assert isinstance(scan["ranges"], list)
        assert len(scan["ranges"]) == 180

    def test_scan_null_when_unavailable(self, blank_state: AppState) -> None:
        override(blank_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                msg = ws.receive_json()
        clear_overrides()

        assert msg["scan"] is None

    def test_timestamp_is_recent(self, blank_state: AppState) -> None:
        override(blank_state)
        before = time.time()
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                msg = ws.receive_json()
        after = time.time()
        clear_overrides()

        assert before <= msg["timestamp"] <= after

    def test_multiple_messages_arrive(self, blank_state: AppState) -> None:
        """Ticker keeps sending; timestamps must be monotonically increasing."""
        override(blank_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                t1 = ws.receive_json()["timestamp"]
                t2 = ws.receive_json()["timestamp"]
                t3 = ws.receive_json()["timestamp"]
        clear_overrides()

        assert t1 <= t2 <= t3

    def test_state_updates_reflected(self, blank_state: AppState) -> None:
        """A landmark added after connect must appear in a subsequent message."""
        override(blank_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/state") as ws:
                first = ws.receive_json()
                assert first["landmarks"] == []

                blank_state.update_landmarks([make_landmark(99)])
                # Burn messages until we see the update (ticker fires every 200ms)
                for _ in range(10):
                    msg = ws.receive_json()
                    if msg["landmarks"]:
                        break
                else:
                    pytest.fail("Landmark update never appeared in WS stream")

                assert msg["landmarks"][0]["id"] == "id-99"
        clear_overrides()


# ---------------------------------------------------------------------------
# /ws/camera — binary frame passthrough
# ---------------------------------------------------------------------------


class TestCameraWebSocket:
    def test_receives_binary_frame(self, blank_state: AppState) -> None:
        """
        Inject a frame directly into the camera queue after connect.
        The queue is registered synchronously before the first await inside
        ws_camera, so it is visible immediately after websocket_connect returns.
        """
        fake_frame = b"\xff\xd8\xff\xe0" + b"\xab\xcd" * 50  # fake JPEG bytes

        override(blank_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/camera") as ws:
                # Push directly into the registered queue(s)
                with blank_state._lock:
                    queues = set(blank_state._camera_queues)
                assert queues, "Camera queue was not registered on connect"
                for q in queues:
                    q.put_nowait(fake_frame)

                received = ws.receive_bytes()

        clear_overrides()
        assert received == fake_frame

    def test_queue_removed_on_disconnect(self, blank_state: AppState) -> None:
        override(blank_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/camera"):
                with blank_state._lock:
                    count_connected = len(blank_state._camera_queues)
        # After exiting the context manager the connection is closed
        with blank_state._lock:
            count_after = len(blank_state._camera_queues)
        clear_overrides()

        assert count_connected == 1
        assert count_after == 0

    def test_slow_client_drops_oldest_frame(self, blank_state: AppState) -> None:
        """
        With maxsize=2, injecting 3 frames must result in the oldest being dropped.
        """
        frame_a = b"\xaa" * 10
        frame_b = b"\xbb" * 10
        frame_c = b"\xcc" * 10

        override(blank_state)
        with TestClient(app) as client:
            with client.websocket_connect("/ws/camera") as ws:
                with blank_state._lock:
                    queues = list(blank_state._camera_queues)
                q = queues[0]

                q.put_nowait(frame_a)
                q.put_nowait(frame_b)
                # Queue is now full (maxsize=2). Use the state helper to drop oldest.
                from semantic_bridge.state import _enqueue_dropping_oldest
                _enqueue_dropping_oldest(q, frame_c)

                r1 = ws.receive_bytes()
                r2 = ws.receive_bytes()

        clear_overrides()
        # frame_a was dropped; b and c remain
        assert r1 == frame_b
        assert r2 == frame_c
