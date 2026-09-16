# Day 6 — Fusion, and the UI

**Goal:** labelled landmarks on the map, in RViz and in the browser.

**Prerequisite:** Day 5 gate passed. `/detections` stable with track IDs.

**This is where Track A and Track B merge.**

---

## 1 · Bring the June `semantic_objects` across

Source: `semantic-object-ros/semantic_objects/` in this workspace.
Full audit: `reference/recovered-facts.md`.

- [x] Copied into `cap_ws/src/semantic_objects/` as a proper ROS 2 package — ✅ 14 Sep, `b136955`. The June tree had **no** package skeleton; authored
- [x] The four `test_*.py` files came too (`test/`)
- [x] **Pushed before it is extended** — ✅ pushed unchanged first
- [x] Unit tests run green as-is: ✅ 111 passed as copied; **139** after Day 6

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

- [x] Node constructs without `ParameterNotDeclaredError` — ✅ 14 Sep (five sites + the docstring that taught slashes)

### 2.2 · P2 — TF at the detection's timestamp

`_lookup_pose()` at line ~344 uses `rclpy.time.Time()`, which means *latest
available*, not *at capture*. While rotating this is the dominant error: at
ω = 1 rad/s and Δt ≈ 100 ms, a landmark 3 m away lands 0.30 m from truth.

- [x] Pass `det_msg.header.stamp` into `lookup_transform`
- [x] Let the TF buffer interpolate; keep `tf.lookup_timeout` for the wait — and `TransformListener(spin_thread=True)`, without which the wait can never be satisfied
- [x] **Skip the frame** when the transform is unavailable — do not extrapolate

### 2.3 · P3 — motion gate

- [x] Subscribe ~~`/odom`~~ **`/diff_cont/odom`** — there is no `/odom` on this robot
- [x] Drop detections while `|ω| > motion.max_omega` (0.3 rad/s) — fail-closed when odom is absent, with a warning that says so
- [x] Parameter added to `robot_params.yaml`

A dozen lines. Objects are re-observed as soon as the robot settles, so almost
nothing is lost — and the alternative is a scan-deskewing project.

### 2.4 · P4, partial — reject, do not fall back

- [x] `detection.min_returns: 3` — reject windows with fewer valid rays (the June parameter existed and was never read)
- [x] `detection.max_spread: 0.5` — reject windows whose returns spread more
      than this (the window straddles an object edge and the background)
- [x] Tune `min_returns` against the **measured** dropout from Day 3, not the
      design note's inherited "half"

> **The size-prior fallback is cut** (decision D-09). Objects off the scan plane
> are rejected, not ranged. Documented as a limitation.

### 2.5 · P5 — associate on track ID

- [x] Read `Detection2D.id` through `ros_bridge` into `LandmarkStore`
- [x] Associate on track ID first — within a continuous track it is exact and free (binding expires after 2 s; refused beyond a 1 m jump, for a restarted detector)
- [x] Fall back to class-gated nearest neighbour only when a track is new or lost

### 2.6 · Intrinsics

- [x] `camera.fx/fy/cx/cy` from Day 4 ~~in `robot_params.yaml`~~ **read from `my_bot/config/c615_640x480.yaml`** — one copy (D-19)
- [x] **Built-in `554.0` defaults deleted** — no intrinsics parameters exist at all now
- [x] Extrinsics read from TF (`base_link → camera_link` for yaw and camera origin, `base_link → laser_frame` for the range origin), not params. ⚠ Two defects found here the checklist did not list: the scan window was mirrored, and the range was applied from the camera not the lidar. Both fixed and tested (D-19)
- [x] `landmark.persist_path` set to real storage — `~/maps/landmarks.json`, written on the publish timer, **not reloaded** on start (D-05)

> **Do not attempt P6, P7 or P8 today.** They are cut. See `records/decisions.md`
> and `RECOVERY.md` §9, which already has the sentences to write about each.

## 3 · Run it

- [x] `launch/semantic.launch.py` written — node + `image_transport republish` for `/image/compressed`
- [x] Everything up: `make real` · `make slam` · `make yolo` · `make semantic` — ✅ 16 Sep (plus `make nav` for teleop, since `twist_mux` and the speed guard live in `navigation.launch.py`)

```bash
ros2 topic echo /semantic_landmarks --once
ros2 topic hz /semantic_markers
```

- [ ] Markers appear in RViz at roughly the right place — ⚠ **STILL NOT
      CONFIRMED.** Not a GATE clause, so it does not block Day 7, but the
      `Semantic Landmarks` display added to `nav.rviz` on 16 Sep (MarkerArray on
      `/semantic_markers`, **Transient Local**) has never been exercised. With
      multi-machine ROS 2 down, RViz on the Jetson is a likely demo display.
      If the display is present but empty while the node reports landmarks, the
      durability match is wrong, not the fusion.
- [x] Drive past a chair → a labelled marker appears and **stays** after you
      drive away — ✅ **16 Sep, user-confirmed. The marker persisted correctly
      after driving away.** This is the clause the whole semantic layer exists
      for.
- [x] Watch the node's own `Fused n/m detections` log line — the ratio should be
      well above zero. Near zero means the geometry chain is broken, not the
      fusion.

  **fused ratio ~25 / 57 per 5 s window (~45 %)**, steady, `tf miss 0`,
  `gate: no-odom 0 turning 0`. Every rejection was `max_spread` — the scan
  window straddling the chair and the background, i.e. the chair sitting
  closer than ideal, **not** a geometry fault. For contrast the stationary
  bench check at 1.64 m managed 94.3 %.

  ⚠ **Below Day 7's target.** Day 7 scores *detections mapped / detections
  received* against **> 0.6**. Backing the robot off further should recover
  most of the gap; do that before the tape-measure protocol.

## 4 · Bridge and UI

These are **drop-in** — the JSON contract was verified matching on all seven
fields. If they need changes, the schema drifted and the fix belongs in the node.

- [x] `clear_landmarks` service (`std_srvs/Empty`) provided by the node — the June tree had none; ✅ `POST /api/clear` reaches it (desk, 14 Sep)
- [x] ~~`ros-humble-compressed-image-transport` installed; camera namespaced~~ **stale**: `cam2image` has no transport plugins. `semantic.launch.py` runs `republish` → `/image/compressed`; the bridge's `camera_topic` setting points there
      to `/camera` so `/camera/image_raw/compressed` exists
- [x] Bridge up: ✅ desk 14 Sep (`make bridge-venv` once, then `make bridge`)

```bash
make bridge      # uvicorn on 0.0.0.0
```

- [x] `GET /api/health` shows `ros_connected: true` and a landmark count — ✅ desk 14 Sep
- [x] UI up: ✅ desk 14 Sep, on the Jetson (Node 20, `make ui-deps` once, then `make ui`), answers at `http://192.168.160.106:3000/`

```bash
make ui          # vite --host
```

- [ ] Browser on another machine shows: occupancy grid, robot pose, scan,
      labelled landmarks, camera feed
- [x] `ROS_DOMAIN_ID` matches between bridge and robot — both from the shell's 42
- [x] CORS origin matches the UI's actual host — `["*"]`, no credentials in use

---

## GATE — ✅ **PASSED 16 Sep 2026.** Day 7 may start

- [x] A labelled marker appears at roughly the right place and **stays** — ✅ confirmed after driving away
- [x] The browser UI shows it — ✅ after three UI defects were fixed the same day (see below); the ROS side and the bridge were correct throughout
- [x] Fused-detections ratio is well above zero — ✅ **~45 %** (~25/57 per window)
- [x] Everything pushed — ✅ both repos

> **Three UI defects were found and fixed reaching this gate, and none of them
> were fusion or geometry faults** — worth remembering for the Day 7 write-up,
> because each one presented as if the robot were wrong:
>
> 1. **`NO SIGNAL` was rendered unconditionally.** Nothing tracked whether a
>    frame had arrived, so the placeholder sat over a working feed forever.
>    `/image/compressed` was publishing at 15.3 Hz the whole time.
> 2. **The map was fetched once at page load and never refreshed.** `slam_toolbox`
>    keeps extending the grid, so the browser froze while RViz showed it live.
>    The bridge's grid was verified byte-identical to `/map`.
> 3. **Landmark class labels were invisible** — `#e8e8e8` on mapped free space
>    `#f0f0f0` is **1.08:1** contrast. They read fine over unknown grey (4.83:1),
>    so labels vanished exactly where the robot had already mapped.
>
> Also fixed on the way: a **fatal startup race in `semantic_objects_node.py`**
> — stats were initialised after the subscribers, so starting `semantic` while
> `/detections` was already flowing killed the executor silently, leaving the
> process alive and the node registered while nothing was ever processed. The
> natural bring-up order was the failing one.

**Then update `STATE.md`.** ✅ done 16 Sep.
