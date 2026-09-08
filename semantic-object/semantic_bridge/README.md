# semantic_bridge

FastAPI service that bridges ROS2 topics to browser-consumable WebSocket streams.

```
ROS2 topics                 semantic_bridge               Browser
──────────────              ───────────────               ───────
/semantic_landmarks  ───┐
/map                 ───┤
/tf (robot pose)     ───┼──► single rclpy node  ──────►  /ws/state   (JSON, 5 Hz)
/scan                ───┘                                 /ws/camera  (JPEG binary)
                                                          /api/landmarks
/image_raw/compressed ──────────────────────────────────► /api/map
                                                          /api/health
                                                          /api/clear
```

---

## Requirements

- Python 3.10+
- ROS2 (Humble or later) with rclpy, tf2_ros, nav_msgs, sensor_msgs, std_srvs
- For mock / dev mode: no ROS2 needed

---

## Install

```bash
cd semantic_bridge
pip install -e ".[dev]"
```

rclpy is provided by the ROS2 system install, not pip:
```bash
source /opt/ros/humble/setup.bash
```

---

## Run

### With a live robot
```bash
source /opt/ros/humble/setup.bash
semantic-bridge
# or:
uvicorn semantic_bridge.main:app --host 0.0.0.0 --port 8000
```

### Mock mode (no robot / no ROS2)
```bash
SEMANTIC_BRIDGE_MOCK=1 semantic-bridge
```

Serves synthetic data: a robot tracing a 2 m circle, three fixed landmarks, a
rolling lidar halo, and (if Pillow is installed) color-cycling JPEG camera frames.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SEMANTIC_BRIDGE_MOCK` | `0` | Set to `1` for mock mode |
| `ROS_DOMAIN_ID` | `0` | ROS2 domain ID |
| `STATE_WS_INTERVAL_MS` | `200` | `/ws/state` tick interval in ms |
| `CAMERA_FPS` | `10` | Target camera FPS (informational; actual rate depends on topic) |
| `ROS_RETRY_INTERVAL_S` | `5` | Seconds between ROS2 reconnect attempts |
| `SCAN_DOWNSAMPLE_RAYS` | `180` | Number of lidar rays forwarded to the browser |

---

## API

### `GET /api/health`
```json
{
  "ros_connected": true,
  "last_landmark_msg": "2024-01-15T10:30:00.123456",
  "landmark_count": 3,
  "robot_pose": { "x": 1.2, "y": 0.5, "yaw": 1.57 }
}
```

### `GET /api/landmarks`
Snapshot of the latest `/semantic_landmarks` message.

### `GET /api/map`
Occupancy grid as base64-encoded int8 array (−1 unknown, 0 free, 100 occupied).
Returns 503 until the first `/map` message is received.

### `POST /api/clear`
Calls the `clear_landmarks` ROS2 service. Returns 503 if ROS is disconnected
or the service is unavailable.

### `WS /ws/state`
JSON message every 200 ms:
```json
{
  "timestamp": 1234567890.123,
  "robot_pose": { "x": 1.2, "y": 0.5, "yaw": 1.57 },
  "landmarks": [ ... ],
  "scan": { "angle_min": -3.14, "angle_increment": 0.035, "ranges": [ ... ] }
}
```

### `WS /ws/camera`
Binary JPEG frames from `/image_raw/compressed`. Connect and render directly
into an `<img>` tag via `URL.createObjectURL`.

---

## Tests

```bash
pytest
```

Tests run without ROS2 installed. The rclpy layer is never imported during the
test suite — `state.py` is injected via FastAPI dependency overrides.

```bash
pytest -v                 # verbose
pytest tests/test_state.py  # single module
```

---

## Project layout

```
semantic_bridge/
├── pyproject.toml
├── README.md
└── semantic_bridge/
    ├── main.py           # FastAPI app + lifespan
    ├── ros_node.py       # rclpy node + RosManager
    ├── state.py          # shared state + FastAPI dependency
    ├── models.py         # Pydantic models
    ├── config.py         # env-var settings
    ├── mock_publisher.py # synthetic data for MOCK=1 mode
    └── routes/
        ├── rest.py       # /api/* endpoints
        └── websocket.py  # /ws/* endpoints
```
