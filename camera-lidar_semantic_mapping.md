# Camera–Lidar Semantic Mapping

**Design note · `semantic_objects`**

Placing labelled objects on the SLAM map by taking bearing from the camera, range from the lidar, and pose from `slam_toolbox` — and what has to change in the current pipeline before the positions are trustworthy.

| Platform | Sensors | Package | Status |
|---|---|---|---|
| Jetson · ROS 2 Humble | C615 mono · YDLidar **X3 Pro** | `semantic_objects` | Scaffolded, untuned |

---

## Contents

1. [The problem](#01--the-problem)
2. [Approach](#02--approach-bearing-from-the-camera-range-from-the-lidar)
3. [Current state](#03--current-state)
4. [Findings](#04--findings)
5. [Design changes](#05--design-changes)
6. [Interfaces](#06--interfaces)
7. [Demo hooks](#07--demo-hooks)
8. [Validation](#08--validation)
9. [Risks and non-goals](#09--risks-and-non-goals)
10. [Sequencing](#10--sequencing)

---

## 01 · The problem

*SLAM and object detection both work. Neither knows about the other.*

`slam_toolbox` produces an occupancy grid: free space, walls, unknown. It has no idea that one of those wall-shaped blobs is a couch. `yolo_ros` produces bounding boxes at 15 Hz: it knows a chair when it sees one, but a bounding box is a rectangle in an image with no position in the world. The goal is a third artefact — a **semantic layer** registered to the same `map` frame — that says *there is a chair at (2.4, −1.1)* and keeps saying it after the robot has driven away.

The hardware constrains the solution sharply. The C615 is a monocular webcam: it gives no depth. The YDLidar X3 Pro gives good range — rated to 8 m — but only along a single horizontal plane, and it has no idea what it is ranging. Neither sensor can do this alone, which is the whole reason the fusion is interesting.

> **What makes the pairing work:** at the calibrated `fx ≈ 528` and 640 px width, one pixel of the image subtends **0.109°**. The lidar, at **11.6 Hz with 350 rays** over 360°, resolves **1.032°**. The camera measures bearing about ten times more finely than the lidar can — and the lidar measures a range the camera cannot measure at all. Each sensor supplies exactly what the other lacks.
>
> ⚠ **Corrected 11 Sep**, twice over: the sensor is a **YDLidar X3 Pro**, not an X2, and the ray count is **350 at 1.032°**, not "roughly 400 … 0.9°" — 400 was inherited and never counted, and the driver prints 350 on startup. The conclusion is unchanged and slightly strengthened: the camera/lidar bearing ratio is **9.5×**, not 8×. Note `fx ≈ 528` is itself from the LOST calibration and must be re-derived before any of this arithmetic is trusted.

---

## 02 · Approach: bearing from the camera, range from the lidar

*Four stages, three of which are already written as pure-Python modules with no ROS imports.*

A detection enters as a pixel rectangle. Its horizontal extent converts to an angular window in the camera frame through the intrinsics. That window selects a slice of the laser scan; the returns inside it aggregate to a single range. Range plus bearing plus the robot's pose at that instant gives a point in the `map` frame. That point is then associated with an existing landmark or becomes a new one.

**Fig. 1 — Pipeline.** Data flow: YOLO detections (`/yolo/tracking`, bbox · class · id · 15 Hz) and laser scans (`/scan`, ~400 rays · 10 Hz) are time-synchronised. The bounding box selects a lidar angular window to produce a range (`LidarRangeExtractor`). The range plus the TF pose (`map→base_link` from `slam_toolbox`, taken at the image timestamp) project to a map-frame `(x, y)` point (`WorldPointProjector`). The `LandmarkStore` associates and smooths the position before publishing markers and JSON. The camera channel contributes bearing only; the lidar channel contributes range only. They meet at the range-extraction stage, and the TF pose enters one stage later, at projection. Everything downstream of projection is frame-independent bookkeeping.

### Alternatives considered and rejected

- **Depth camera (RealSense / OAK-D).** Would solve range directly and handle off-plane objects. Rejected: not in the build, and swapping the sensor this late invalidates the calibration and mounting work already done.
- **Monocular depth estimation.** A learned depth model on the Jetson alongside the YOLO TensorRT engine. Rejected: metric scale is unreliable, and the GPU budget is already committed to detection at 15 Hz.
- **Size priors alone** (`Z ≈ H_real · fy / h_px`). Kept, but only as a *fallback* for classes the lidar plane cannot see — see P4. On its own it is roughly ±20% and depends on the object being a standard size.

---

## 03 · Current state

*The package exists and is structurally sound. The core logic is ROS-free and testable, which is the right split. What is missing is correctness in the geometry and honesty in the map lifecycle.*

| Module | Responsibility | State |
|---|---|---|
| `lidar_range_extractor.py` | Bounding box → angular window → aggregated range. Correctly drops the X2's `0.0` dropout returns via the scan's own `range_min`. | Built |
| `world_point_projector.py` | Range + bearing + 2D pose → point in `map`. Applies camera extrinsics. | Built |
| `landmark_store.py` | Class-gated nearest-neighbour association, EMA position fusion, staleness, JSON persistence. | Needs rework |
| `ros_bridge.py` | Message conversion and `MarkerArray` / JSON rendering. | Built |
| `semantic_objects_node.py` | Time sync, TF lookup, per-detection loop, publishing. | Has defects |
| `config/robot_params.yaml` | Intrinsics, extrinsics, gates, store tuning. | Placeholders |
| Negative evidence / ghost removal | Deleting landmarks that should have been re-observed and weren't. | Not started |
| Loop-closure handling | Correcting stored positions when `map→odom` jumps. | Not started |
| Nav2 / map_saver integration | Navigating to a named object; saving the semantic layer with the grid. | Not started |

> ✅ **Done 11 Sep 2026.** The C615 is calibrated at 640×480 and validated against a tape measure: **fx 667.874 · fy 669.846 · cx 321.569 · cy 234.502**, reprojection 0.3403 px, `fx` within +0.45% of the tape. Installed at `my_bot/config/c615_640x480.yaml`; method and derivation in `records/calibration.md`.
>
> ⚠ **Both figures this note quoted are ~20% wrong and must not be reinstated.** `robot_params.yaml`'s `fx: 528.1` was a `← YOUR VALUE` template placeholder, never a measurement; the node's `554.0` default implies a ~60° HFOV. **The camera is ~51°.** Every bearing in the system derives from these numbers, so when the September `semantic_objects` tree is rebuilt the defaults get **deleted**, not updated — a missing params file must fail loudly.
>
> **Autofocus must stay locked** (`focus_absolute=51`), and to the same value the calibration was taken at. The C615 is varifocal: with AF on, `fx` drifts at run time and the calibration stops describing the camera. `make camera` handles it.

---

## 04 · Findings

*Numbered in fix order — P1 first, because each earlier item changes what the later ones are measured against.*

### P1 — A hard-coded azimuth gate discards most of the frame  *(critical)*

`semantic_objects_node.py · _on_synced`

The per-detection loop contains `if abs(world_pt.azimuth_rad) > 0.1: continue` with no parameter behind it and no comment. `azimuth_rad` is the bounding box's centre bearing in the camera frame, so this accepts only detections within ±0.1 rad (±5.7°) of the optical axis.

At `fx ≈ 528` that is `±528·tan(0.1) ≈ ±53 px` — the central **106 px of 640**, about a sixth of the frame width, against a horizontal field of view of roughly 62°. An object has to be nearly dead-centre to be mapped at all. This reads like a debugging narrowing that was never removed, and it will dominate any accuracy measurement taken before it is dealt with.

**Fix:** Remove it, or promote it to `detection.max_azimuth` defaulted to the half-FOV derived from the intrinsics. If some edge-of-frame rejection is genuinely wanted — lens distortion is worst there — express it as a fraction of the half-FOV, not a bare radian literal.

### P2 — The pose is read at "latest", not at the detection's timestamp  *(critical)*

`semantic_objects_node.py · _lookup_pose`

`_lookup_pose()` calls `lookup_transform(map, base_link, rclpy.time.Time())`. A zero time means *the most recent transform available*, not the transform at the instant the image was captured. The node goes to the trouble of running an `ApproximateTimeSynchronizer` to pair a scan with a detection within 0.1 s, then projects the matched pair using a pose from an unrelated later moment.

While the robot is translating this is a small error. While it is rotating it is the dominant one — see Fig. 3.

**Fix:** Pass the detection message's `header.stamp` into the lookup, and let the TF buffer interpolate. Keep `tf.lookup_timeout` for the wait, and skip the frame rather than extrapolating when the transform is unavailable.

### P3 — Nothing suppresses observations taken mid-rotation  *(high)*

`semantic_objects_node.py · _on_synced`

Even with P2 fixed, rotation is the worst case: the lidar sweeps 360° over a full ~86 ms (measured 9 Sep; this note said 100 ms), so rays within one scan are up to 100 ms apart in time and were taken from different headings. The scan is treated as instantaneous everywhere in the pipeline.

**Fix:** Subscribe to `/odom` and drop detections while `|ω| > 0.3 rad/s`. Objects are re-observed as soon as the robot settles, so almost nothing is lost — and this is a dozen lines against what is otherwise a scan-deskewing project.

### P4 — Objects off the scan plane get the background's range  *(high)*

`lidar_range_extractor.py · _aggregate · range_method: "min"`

The lidar sees one horizontal slice at its mount height. Anything that does not intersect that slice — a cup on a table, a bottle on a shelf, a monitor on a stand — produces returns that belong to whatever is behind it. With `range_method: "min"` the aggregate is confidently wrong rather than obviously wrong, and there is nothing in the output to indicate it.

This compounds with the X2's dropout behaviour: the workspace's own `ydlidar.yaml` records that roughly half of the ~400 rays read `0.0` in an ordinary indoor room. Those are filtered correctly, but it means a narrow bounding box may be backed by only two or three real returns.

**Fix:** Three parts. (a) Classify each COCO class as floor-intersecting or off-plane, and only trust the lidar for the first group. (b) For off-plane classes, fall back to the size-prior range and flag the landmark as low-confidence. (c) Add `detection.min_returns` and reject windows with fewer valid rays than that, and reject windows whose returns have a spread above roughly 0.5 m — a wide spread means the window straddles an object edge and the background.

### P5 — The tracker is running and its IDs are being thrown away  *(high)*

`semantic_objects_node.py · _setup_subscribers · yolo.launch.py`

`yolo.launch.py` starts `tracking_node` with ByteTrack by default and publishes `/yolo/tracking`, but the node subscribes to `/yolo/detections` and associates purely by class-gated nearest neighbour within `merge_radius: 0.5` m.

A fixed radius fails in both directions: two chairs 40 cm apart merge into one landmark, and one chair observed from two sides — where the visible surface differs by more than 0.5 m — splits into two.

**Fix:** Subscribe to `/yolo/tracking` instead. Within a continuous track, association is exact and free. Fall back to the geometric test only when a track ID is new or has been lost. This is close to a one-line topic change for a large robustness gain.

### P6 — EMA treats a 0.5 m observation and a 4.5 m observation as equals  *(medium)*

`landmark_store.py · ema_alpha: 0.3`

Position uncertainty grows with range — 0.9° of lidar angular resolution is 1.6 cm at 1 m and 7.9 cm at 5 m, and the range error itself grows too. A fixed `α` gives a distant, noisy observation the same authority as a close, precise one, and provides no uncertainty estimate to gate association with.

**Fix:** Replace the EMA with a small per-landmark 2D Kalman update carrying a covariance seeded from the range and the angular window width. This buys three things at once: range-weighted updates, Mahalanobis gating that adapts instead of a fixed `merge_radius`, and a covariance ellipse to render in RViz — which also makes the fusion legible in a demo.

### P7 — Landmarks are never disproved, only aged  *(medium)*

`landmark_store.py · mark_stale · stale_timeout: 300.0`

Landmarks are created and marked stale after five minutes, but nothing ever removes one. A single YOLO false positive that survives `min_seen_to_publish: 2` stays on the map for the rest of the run, and an object that has been moved away leaves a ghost at its old position.

**Fix:** Add negative evidence. On each frame, for every landmark that is inside the current field of view, within `max_range`, and unoccluded — ray-cast against the `/map` occupancy grid — but was not detected, decrement a confidence score. Delete below a threshold. This is what makes the second pass through a room *clean up* the first.

### P8 — Loop closure silently invalidates stored positions  *(medium)*

`landmark_store.py · persisted x, y in the map frame`

Landmarks are stored as absolute `map`-frame coordinates. When `slam_toolbox` closes a loop it revises the pose graph and jumps `map→odom`; the grid moves underneath the landmarks and they do not follow. After a large loop the semantic layer and the occupancy grid disagree, and nothing reports it.

**Fix:** Full semantic SLAM — landmarks as pose-graph nodes — is out of scope. The pragmatic version: store each observation as *(robot pose at observation, range, bearing)* rather than a world point, and recompute world positions from the current TF when publishing. Corrections then propagate for free. If even that is too much, keep the current scheme and state the limitation explicitly in the report.

---

## 05 · Design changes

*The findings group into three work packages. The first is geometry and timing, and it has to land before the other two can be evaluated at all.*

### WP1 — Geometry and timing correctness

P1, P2, P3, P4 — everything that decides whether a point lands in the right place.

- ~~Calibrate the C615~~ ✅ **done 11 Sep** — `my_bot/config/c615_640x480.yaml`, tape-validated. Still to do when the node is rebuilt: point it at that file and **delete the `554.0` defaults** so a missing params file fails loudly rather than quietly running ~20% off.
- Remove the `±0.1 rad` gate; derive any azimuth limit from the intrinsics.
- Look TF up at the detection's `header.stamp`.
- Gate on `|ω|` from `/odom`.
- Add the per-class plane policy, the size-prior fallback, and `min_returns` / spread rejection.
- Measure the camera-to-lidar offset properly and publish it through the URDF rather than the launch file's `static_transform_publisher`, so simulation and the real robot share one source.

**Fig. 2 — Why P4 is not a tuning problem.** Side elevation: the lidar scan plane (one height, no vertical extent) crosses a chair's legs and returns the correct range (≈1.4 m). But it passes beneath a tabletop and between the table legs, so the cup on the table has nothing at its bearing to range; the ray flies on and `min()` returns the far wall — the cup is placed ≈2 m too far. No choice of `range_method` recovers the cup's true range — the measurement simply is not in the scan. The only options are to detect the condition and reject it, or to get the range from somewhere else.

**Fig. 3 — The cost of P2, in metres.** Top-down view: a bearing measured at the image timestamp `t_img` is applied to the robot pose read later at `t_now`, so the projected landmark is rotated away from the object's true position by the angle the robot turned through in that interval (Δθ). At ω = 1 rad/s and Δt ≈ 100 ms the robot turns 5.7°, and a landmark 3 m away is projected 0.30 m from where it actually is — comparable to the whole `merge_radius`, which is why the error shows up as duplicate landmarks rather than as blur. The fix is to look TF up at `t_img` instead of `t_now`.

### WP2 — Association and fusion quality

P5, P6 — whether repeated sightings of one object converge on one landmark.

- Switch the detection subscription to `/yolo/tracking` and carry `track_id` through `ros_bridge` into `LandmarkStore`.
- Associate on track ID first; fall back to geometry for new or re-acquired tracks.
- Replace the EMA with a 2D Kalman update; seed covariance from range and window width.
- Gate association on Mahalanobis distance and retire `merge_radius` as a hard threshold.
- Publish the covariance ellipse as a second `Marker` per landmark.

### WP3 — Map lifecycle

P7, P8 — whether the semantic layer is still true an hour later.

- Subscribe to `/map`; implement the visibility test (in FOV, in range, unoccluded by ray-cast).
- Add per-landmark confidence, incremented on detection and decremented on a missed expected observation; delete below threshold.
- Store observations as pose-plus-measurement and recompute world positions at publish time, so loop closures propagate.
- Set `landmark.persist_path` to stable storage — it is currently `""`, so nothing survives a restart.

---

## 06 · Interfaces

*What the node consumes and produces after the changes. Additions and changes are marked; everything else is as built.*

| Topic | Type | Direction | Note |
|---|---|---|---|
| `/yolo/tracking` | `yolo_msgs/DetectionArray` | in | **Changed** — was `/yolo/detections`; carries `track_id` |
| `/scan` | `sensor_msgs/LaserScan` | in | BEST_EFFORT, matching the X3 Pro driver |
| `/odom` | `nav_msgs/Odometry` | in | **New** — angular-velocity gate (P3) |
| `/map` | `nav_msgs/OccupancyGrid` | in | **New** — occlusion ray-cast (P7) |
| `/semantic_markers` | `visualization_msgs/MarkerArray` | out | TRANSIENT_LOCAL; adds covariance ellipses |
| `/semantic_landmarks` | `std_msgs/String` (JSON) | out | TRANSIENT_LOCAL; adds confidence and `range_source` |

| Parameter | Now | Proposed | Why |
|---|---|---|---|
| `camera.fx / fy / cx / cy` | placeholder | calibrated | Every bearing depends on these |
| `detection.max_azimuth` | 0.1 (hard-coded) | half-FOV | P1 |
| `detection.min_returns` | — | 3 | P4 — reject thin windows |
| `detection.max_spread` | — | 0.5 m | P4 — reject edge/background straddle |
| `motion.max_omega` | — | 0.3 rad/s | P3 |
| `landmark.merge_radius` | 0.5 m | fallback only | P5, P6 — Mahalanobis gate takes over |
| `landmark.ema_alpha` | 0.3 | removed | P6 — replaced by Kalman update |
| `landmark.confidence_decay` | — | 0.1 / miss | P7 |
| `landmark.persist_path` | `""` (off) | set | Survive restarts |

---

## 07 · Demo hooks

*Three integrations that turn a marker overlay into something an examiner can ask the robot to do.*

### Navigate to a named object

A small action server: look up landmarks by class, pick the nearest, compute a standoff pose 0.8 m in front of it facing the object, and send a `NavigateToPose` goal. "Go to the nearest chair" is the single most persuasive thing this project can demonstrate, and it exercises SLAM, detection, fusion, and Nav2 in one command.

### Save the semantic layer with the grid

When `map_saver` writes the `.pgm` and `.yaml`, write `landmarks.json` beside them. The semantic map is only useful if it can be reloaded against the same occupancy grid it was built on.

### Stop exploring when the objects are found

`explore_lite` currently stops when frontiers run out. Given a target class list, it can stop when every target has a confirmed landmark instead — turning frontier exploration into object search, which is a more interesting claim than coverage.

---

## 08 · Validation

*The pure-Python split already in place makes most of this cheap. The part that matters for the report is the one real-world number.*

### Unit level

`lidar_range_extractor`, `world_point_projector`, and `landmark_store` have no ROS imports, so they can be tested with synthetic `LaserScanData` and known poses. The cases worth pinning: a bounding box spanning the `angle_min` / `angle_max` wrap, a window containing only `0.0` dropouts, a window straddling an object edge, and a projection at a pose with non-zero yaw (where a sign error in the extrinsics rotation is otherwise invisible).

### System level — the tape-measure protocol

1. Place a chair at a position measured against two walls with a tape.
2. Drive a closed loop around the room, passing the chair from four directions.
3. Log the landmark's published position on every pass.
4. Report absolute error against the tape measurement, and the spread across passes.

Absolute error tests the geometry chain; spread tests the fusion. They fail for different reasons, so report both. Run it once before WP1 and once after — the delta is the evidence that the work was worth doing.

| Metric | Target | Before WP1 | After WP1 |
|---|---|---|---|
| Absolute position error, floor-standing class | < 0.25 m | — | — |
| Spread across four passes | < 0.15 m | — | — |
| Duplicate landmarks per true object | 1.0 | — | — |
| Ghosts surviving a second pass | 0 | — | — |
| Detections mapped / detections received | > 0.6 | — | — |

The last row is worth watching from the start: the node already logs `Fused n/m detections`, so the ratio is free. Before P1 is fixed it should sit near zero, which is a useful confirmation that the diagnosis is right.

---

## 09 · Risks and non-goals

### Risks

- **Calibration quality caps everything.** A 5% error in `fx` is a 5% bearing error at the frame edge. If the checkerboard run is rushed, no amount of fusion work recovers it.
- **The X2's dropout rate.** Half the rays reading `0.0` indoors is the workspace's own measured figure. Narrow bounding boxes at range may routinely fail `min_returns`, which trades false positions for missing landmarks — the right trade, but it will look like reduced recall.
- **Jetson budget.** The occlusion ray-cast in P7 runs per landmark per frame. Keep it to confirmed landmarks and cap the rate; it is a candidate for its own timer at 2 Hz rather than running inside the detection callback.
- **Loop closure remains partially unhandled** unless WP3's re-projection lands. Say so in the report rather than hoping the demo room is small enough to hide it.

### Non-goals

- Full semantic SLAM with landmarks in the pose graph.
- 3D object extent — landmarks are 2D points with a class, not oriented boxes.
- Multi-session map merging.
- Re-identifying a specific instance ("*this* chair") across sessions.

---

## 10 · Sequencing

*Ordered so that each step's effect is measurable before the next one starts. The first two rows change the numbers more than everything below them combined.*

| Step | Work | Cost |
|---|---|---|
| 1 | **Calibrate the camera** and record the baseline metrics with the pipeline exactly as it stands. | half a day |
| 2 | **P1 + P2** — remove the azimuth gate, look TF up at the image timestamp. Re-run the protocol. | an afternoon |
| 3 | **P5** — move to `/yolo/tracking` and associate on track ID. | an afternoon |
| 4 | **P3 + P4** — motion gate, per-class plane policy, return-count and spread rejection. | 1–2 days |
| 5 | **P6** — Kalman fusion with covariance, Mahalanobis gating, ellipse markers. | 1–2 days |
| 6 | **P7** — negative evidence and ghost removal against the occupancy grid. | 2 days |
| 7 | **Navigate-to-object action server** — the demo. | 1 day |
| 8 | **P8 + persistence** — re-projection on loop closure, save alongside `map_saver`. | 2 days, or documented as a limitation |

---

*Design note for `semantic_objects` · Autonomous Robot with Edge AI · 4 September 2026. Findings P1–P8 were read from the working tree at `src/semantic_objects/`; file and function references point at that revision.*

*Tracked in the repository at `src/semantic_objects/DESIGN.md`, which carries the checkboxes and the progress log. Keep the two in sync when either changes.*
