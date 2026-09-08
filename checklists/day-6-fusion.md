# Day 6 — Fusion, and the UI

**Goal:** labelled landmarks on the map, in RViz and in the browser.

**Prerequisite:** Day 5 gate passed. `/detections` stable with track IDs.

**This is where Track A and Track B merge.**

---

## 1 · Bring the June `semantic_objects` across

Source: `semantic-object-ros/semantic_objects/` in this workspace.
Full audit: `reference/recovered-facts.md`.

- [ ] Copied into `cap_ws/src/semantic_objects/` as a proper ROS 2 package
- [ ] The four `test_*.py` files came too
- [ ] **Pushed before it is extended**
- [ ] Unit tests run green as-is:

```bash
make test
```

## 2 · Fix it, in this order

### 2.1 · The parameter bug — [ ] **do this first**

**The node cannot start without it.** Five call sites read dotted parameters
with slashes:

| Line | Change |
|---|---|
| 118 | `publish/rate_hz` → `publish.rate_hz` |
| 119 | `landmark/stale_timeout` → `landmark.stale_timeout` |
| 130 | `landmark/merge_radius` → `landmark.merge_radius` |
| 131 | `landmark/ema_alpha` → `landmark.ema_alpha` |
| 132 | `landmark/persist_path` → `landmark.persist_path` |

- [ ] Node constructs without `ParameterNotDeclaredError`

### 2.2 · P2 — TF at the detection's timestamp

`_lookup_pose()` at line ~344 uses `rclpy.time.Time()`, which means *latest
available*, not *at capture*. While rotating this is the dominant error: at
ω = 1 rad/s and Δt ≈ 100 ms, a landmark 3 m away lands 0.30 m from truth.

- [ ] Pass `det_msg.header.stamp` into `lookup_transform`
- [ ] Let the TF buffer interpolate; keep `tf.lookup_timeout` for the wait
- [ ] **Skip the frame** when the transform is unavailable — do not extrapolate

### 2.3 · P3 — motion gate

- [ ] Subscribe `/odom`
- [ ] Drop detections while `|ω| > motion.max_omega` (0.3 rad/s)
- [ ] Parameter added to `robot_params.yaml`

A dozen lines. Objects are re-observed as soon as the robot settles, so almost
nothing is lost — and the alternative is a scan-deskewing project.

### 2.4 · P4, partial — reject, do not fall back

- [ ] `detection.min_returns: 3` — reject windows with fewer valid rays
- [ ] `detection.max_spread: 0.5` — reject windows whose returns spread more
      than this (the window straddles an object edge and the background)
- [ ] Tune `min_returns` against the **measured** dropout from Day 3, not the
      design note's inherited "half"

> **The size-prior fallback is cut** (decision D-09). Objects off the scan plane
> are rejected, not ranged. Documented as a limitation.

### 2.5 · P5 — associate on track ID

- [ ] Read `Detection2D.id` through `ros_bridge` into `LandmarkStore`
- [ ] Associate on track ID first — within a continuous track it is exact and free
- [ ] Fall back to class-gated nearest neighbour only when a track is new or lost

### 2.6 · Intrinsics

- [ ] `camera.fx/fy/cx/cy` from Day 4 in `robot_params.yaml`
- [ ] **Built-in `554.0` defaults deleted**
- [ ] Extrinsics read from TF (`base_link → camera_link`), not params
- [ ] `landmark.persist_path` set to real storage — it was `""`

> **Do not attempt P6, P7 or P8 today.** They are cut. See `records/decisions.md`
> and `RECOVERY.md` §9, which already has the sentences to write about each.

## 3 · Run it

- [ ] `launch/semantic.launch.py` written
- [ ] Everything up: `make real` · `make slam` · `make yolo` · `make semantic`

```bash
ros2 topic echo /semantic_landmarks --once
ros2 topic hz /semantic_markers
```

- [ ] Markers appear in RViz at roughly the right place
- [ ] Drive past a chair → a labelled marker appears and **stays** after you
      drive away
- [ ] Watch the node's own `Fused n/m detections` log line — the ratio should be
      well above zero. Near zero means the geometry chain is broken, not the
      fusion.

  **fused ratio ______ / ______**

## 4 · Bridge and UI

These are **drop-in** — the JSON contract was verified matching on all seven
fields. If they need changes, the schema drifted and the fix belongs in the node.

- [ ] `clear_landmarks` service (`std_srvs/Empty`) provided by the node
- [ ] `ros-humble-compressed-image-transport` installed; camera namespaced
      to `/camera` so `/camera/image_raw/compressed` exists
- [ ] Bridge up:

```bash
make bridge      # uvicorn on 0.0.0.0
```

- [ ] `GET /health` shows `ros_connected: true` and a landmark count
- [ ] UI up:

```bash
make ui          # vite --host
```

- [ ] Browser on another machine shows: occupancy grid, robot pose, scan,
      labelled landmarks, camera feed
- [ ] `ROS_DOMAIN_ID` matches between bridge and robot
- [ ] CORS origin matches the UI's actual host

---

## GATE — do not start Day 7 until all of these hold

- [ ] A labelled marker appears at roughly the right place and **stays**
- [ ] The browser UI shows it
- [ ] Fused-detections ratio is well above zero
- [ ] Everything pushed

**Then update `STATE.md`.**
