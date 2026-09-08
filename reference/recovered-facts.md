# Recovered facts — do not re-derive these

> ⚠ **Superseded in large part by `reference/nvme-recovery-audit.md` (8 Sep).**
> An NVMe dump recovered the whole `my_bot` package. The "definitively gone"
> section below is now wrong — read the audit first. What remains accurate here
> is the analysis of the **June-era `semantic_objects`**, which the dump did not
> reach.

Read from the actual surviving trees on 7 Sep 2026. Everything here was
verified against bytes, not recalled. **If you are about to go and work out one
of these things again, read this file instead.**

---

## What survived, and how far to trust it

| Asset | Where it is now | Trust |
|---|---|---|
| `esp-motor-firmware` | GitHub, `b0b762b` | **High for protocol, low for tuning** — never turned a motor |
| Design note `camera-lidar_semantic_mapping.md` | workspace root | High, one caveat — P1 does not exist in what we have |
| `semantic_bridge` + `semantic_map_ui` | `semantic-object/` | **High** — JSON contract verified matching, drop-in |
| `semantic_objects` (June-era) | `semantic-object-ros/` | Reference only, **and it does not run as-is** |

## Definitively gone — ⚠ MOSTLY RECOVERED 8 Sep, see the audit

Searched both prior-art trees for any `.yaml`, `.xml`, `.urdf`, `.xacro`,
`.sdf`, `launch`, or `Makefile`. **Zero hits.** Neither directory is a git repo,
so there is no history to mine.

- The whole `ws/` and `my_bot` — URDF, ros2_control, launch, config
- The root `Makefile` (reconstructed in `RECOVERY.md` §7)
- The udev rules (`/dev/esp32`, `/dev/lidar`) — re-derive per `RECOVERY.md` §5.1
- `my_bot/scripts/` including `walk_straight.py` — specs in `scripts-to-rebuild.md`
- `robot_params.yaml` — but **the schema is recoverable**, see below
- `ydlidar.yaml` — and with it, the measured X2 dropout figure

> The design note's "roughly half the X2's rays read 0.0 indoors" was read from
> the lost `ydlidar.yaml`. **That number is now an unverified inheritance.**
> Re-measure it with `scan_dropout_report.py` before letting it set
> `detection.min_returns`.

---

## Blocking defect in the June `semantic_objects`

**The node cannot start.** Verified present in the local copy at
`semantic-object-ros/semantic_objects/semantic_objects_node.py`.

`_declare_parameters()` declares **dotted** names. Five call sites read them
with **slashes**:

| Line | Reads | Should read |
|---|---|---|
| 118 | `get_parameter("publish/rate_hz")` | `publish.rate_hz` |
| 119 | `get_parameter("landmark/stale_timeout")` | `landmark.stale_timeout` |
| 130 | `get_parameter('landmark/merge_radius')` | `landmark.merge_radius` |
| 131 | `get_parameter('landmark/ema_alpha')` | `landmark.ema_alpha` |
| 132 | `get_parameter('landmark/persist_path')` | `landmark.persist_path` |

Zero slash-style declarations exist. In rclpy this raises
`ParameterNotDeclaredError` inside `__init__`. **Fix this first — it is not one
of P1–P8 and you will hit it in the first thirty seconds.**

## The design note's findings, mapped onto what we actually have

| Finding | Present? | Note |
|---|---|---|
| **P1** hard-coded `±0.1 rad` azimuth gate | **NO** | Introduced after June. Simply never write it. |
| **P2** TF looked up at "latest" | **Yes** | `rclpy.time.Time()` at line 344. Pass `header.stamp` instead. |
| **P3** no rotation gate | Yes | Nothing subscribes to `/odom`. |
| **P4** off-plane objects get background range | Yes | `range_method: "min"`, no plane policy. |
| **P5** track IDs discarded | **Different** | See below — better than the note says. |
| **P6** fixed EMA | Yes | `ema_alpha: 0.3`. **Cut** — decision D-06. |
| **P7** landmarks never disproved | Yes | **Cut** — decision D-07. |
| **P8** loop closure invalidates positions | Yes | **Cut** — decision D-08. |

### P5 is not the problem the note describes

The note assumes `yolo_msgs/DetectionArray` on `/yolo/detections`. **The June
tree is already on `vision_msgs/Detection2DArray` at `/detections`** —
apt-installable as `ros-humble-vision-msgs`.

Since we write a custom detection node anyway, use ultralytics'
`model.track(persist=True)` and put the track ID in `Detection2D.id`. That gets
P5's benefit with **no `yolo_msgs` build, no separate tracking node, and no
message-type change** to code that already parses it. See decision D-01.

---

## `robot_params.yaml` — recovered schema

Reconstructed from `_declare_parameters()`. These are the names the surviving
code actually reads. Additions for Day 6 marked `NEW`.

```yaml
semantic_objects:
  ros__parameters:
    camera:
      fx: 0.0            # ← calibrate. NO default. Fail loudly if unset.
      fy: 0.0
      cx: 0.0
      cy: 0.0
      width:  640
      height: 480
      dx:  0.0           # metres forward from base_link
      dy:  0.0           # metres left from base_link
      yaw: 0.0           # radians CCW from robot forward
    detection:
      min_confidence: 0.5
      range_method: "min"
      angular_padding: 0.0
      max_range: 5.0
      min_range: 0.15
      min_returns: 3     # NEW — P4
      max_spread: 0.5    # NEW — P4
    motion:
      max_omega: 0.3     # NEW — P3
    landmark:
      merge_radius: 0.5
      ema_alpha: 0.3
      min_seen_to_publish: 2
      stale_timeout: 300.0
      persist_path: ""   # was off — set it
    publish:
      rate_hz: 2.0
    tf:
      map_frame: map
      base_frame: base_link
      camera_frame: camera_link
      lookup_timeout: 0.1
    sync:
      slop: 0.1
```

**The node's built-in default of `fx: 554.0` must be deleted.** A missing params
file should fail loudly, not silently map the room at the wrong focal length.

---

## The landmark JSON contract — verified matching

Producer `ros_bridge.landmarks_to_json_str()` and consumer `semantic_bridge`'s
pydantic `Landmark` model agree on **all seven fields**:

```json
{ "landmarks": [
  { "id": "...", "class_label": "chair", "x": 1.23, "y": 4.56,
    "confidence": 0.87, "seen_count": 5, "stale": false } ] }
```

**The bridge and UI are drop-in** provided the new node keeps this schema.
Adding fields is safe (pydantic v2 ignores extras) but the UI will not see them.

### What the bridge requires from the rest of the system

| Requirement | Note |
|---|---|
| `/semantic_landmarks` (`std_msgs/String`, JSON above) | TRANSIENT_LOCAL |
| `/map` (`nav_msgs/OccupancyGrid`) | from `slam_toolbox` |
| `/scan` (`sensor_msgs/LaserScan`) | downsampled to 180 rays by the bridge |
| `/camera/image_raw/compressed` | **namespace the camera to `/camera`**; needs `ros-humble-compressed-image-transport` |
| `clear_landmarks` service, `std_srvs/Empty` | **must be provided by the node** |

Bridge settings live in `semantic_bridge/config.py`: `ROS_DOMAIN_ID`,
`SEMANTIC_BRIDGE_MOCK`, `scan_downsample_rays: 180`, `camera_fps: 10`,
CORS for `localhost:5173` and `:3000`.

---

## Module inventory — the June tree

| File | Lines | State per the design note |
|---|---|---|
| `lidar_range_extractor.py` | 287 | Built. Correctly drops `0.0` via the scan's own `range_min`. |
| `world_point_projector.py` | 227 | Built. Applies camera extrinsics. |
| `landmark_store.py` | 341 | Needs rework (P6, P7 — both cut). |
| `ros_bridge.py` | 291 | Built. JSON + MarkerArray rendering. |
| `semantic_objects_node.py` | 408 | Has defects — the param bug, P2, P3, P4, P5. |
| `test_*.py` × 4 | 1,737 | Pure-Python, no ROS imports. **Run them** — `make test`. |

The core modules have no ROS imports, which is the right split and makes the
unit tests cheap to keep. Cases worth pinning: a bbox spanning the
`angle_min`/`angle_max` wrap, a window of only `0.0` dropouts, a window
straddling an object edge, and a projection at non-zero yaw (where a sign error
in the extrinsics rotation is otherwise invisible).

---

## Sensor geometry — why the fusion works

At the calibrated `fx ≈ 528` and 640 px width, one pixel subtends **0.109°**.
The X2, at 10 Hz with ~400 rays over 360°, resolves **0.9°**. The camera
measures bearing about ten times more finely than the lidar can; the lidar
measures a range the camera cannot measure at all. Each sensor supplies exactly
what the other lacks.

Position uncertainty grows with range: 0.9° is 1.6 cm at 1 m and 7.9 cm at 5 m.

## Old-board environment notes

Carried from the firmware repo — may or may not still apply to the new Jetson.

- `arduino-cli` was at `/home/jetson/bin/arduino-cli`, ESP32 core 3.3.11
- The ESP32 enumerated via a **Silicon Labs CP210x** USB-UART bridge — this is
  the reason to assume a VID:PID collision with the lidar
- A `micro_ros_agent` running as root held `/dev/ttyUSB0` and blocked uploads
