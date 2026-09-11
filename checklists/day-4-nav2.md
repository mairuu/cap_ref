# Day 4 — Nav2

**Goal:** click a goal in RViz, robot drives there and stops.

**Prerequisite:** Day 3 gate passed. A loop closes cleanly.

> **Track B today: camera calibration.** It needs only the Jetson and the
> camera — see §4 below. Do not rush it. Every bearing in the semantic layer is
> downstream of `fx`.

---

## 1 · Bring up the stack

Use `nav2_bringup` with our own params file. Do not write a stack.

- [ ] `config/nav2.yaml` from the bringup default, changing only what
      `RECOVERY.md` §6.6 lists
- [ ] `launch/nav.launch.py` written

> **No `amcl`.** One session, `slam_toolbox` provides `map → odom`. Set
> `slam: True` in the bringup and skip localisation entirely. Decision D-05.

```bash
make slam     # must already be running
make nav
```

- [ ] Lifecycle nodes all reach `active`:

```bash
ros2 lifecycle get /controller_server
ros2 lifecycle get /planner_server
ros2 lifecycle get /bt_navigator
```

## 2 · Footprint and inflation

This is what will actually cost you time — not Nav2 itself. The lidar drops a
large fraction of its returns, so be generous.

- [ ] `robot_radius` = measured radius **+ ~20%**
- [ ] `inflation_radius` starts generous (0.35) and comes down only if the robot
      cannot get through a real doorway
- [ ] Costmaps look right in RViz — walls inflated, no phantom obstacles at the
      robot's own footprint

  measured radius ______ m → `robot_radius` ______ m

## 3 · Drive to goals

- [ ] Simple goal in open space → arrives and stops
- [ ] Goal requiring a turn → arrives
- [ ] Goal through a doorway → arrives, or tells you the inflation is too big
- [ ] Block it with a chair mid-path → **recovery behaviours fire**, it replans
- [ ] Goal in unknown space → behaves sensibly (refuses or explores toward it)

- [ ] It does **not** drive into the one wall the lidar sees worst — check the
      dropout sector from Day 3 §2

Tune only if needed:

| Symptom | Knob |
|---|---|
| Overshoots the goal | `xy_goal_tolerance`, `max_vel_x` |
| Oscillates near the goal | `yaw_goal_tolerance`, `min_speed_theta` |
| Refuses to start | costmap footprint vs. `robot_radius` |
| Clips corners | `inflation_radius`, `cost_scaling_factor` |

## 4 · Track B — camera calibration

**A prerequisite, not a nicety.** A 5% error in `fx` is a 5% bearing error at
the frame edge, and no amount of fusion work recovers it.

**Needs no robot.** Camera only — no lidar, no Nav2, nothing on blocks. This is
the task for any gap while waiting to drive.

> **Rewritten 11 Sep. The commands this section used to carry were wrong on all
> four counts** — `usb_cam`, `/camera/image_raw`, `8x6`, `0.025`. The camera is
> **`cam2image`** on **`/image`**, the board is **9×6 / 20 mm**, and
> `--no-service-check` is **required**. See `reference/nvme-recovery-audit.md`.
> The 10 Sep deviation log recorded the replacement; the file itself had not
> caught up until now.

### 4.1 · The board

- [ ] 9×6 **interior corners** (= 10×7 printed squares, 200 × 140 mm)
- [ ] **Measure it.** Lay a steel rule across ten squares: that span must be
      **200 mm**. Printers default to "Fit to page" and take 3–6% off, and a
      uniform square-size error is **invisible to the reprojection error** —
      it is absorbed by the board-to-camera distance, so the residuals stay
      clean while every `fx` is wrong by the same percentage. Verified 11 Sep:
      re-scoring the same images with `--square 0.030` instead of `0.020`
      changed the RMS by **zero**.
- [ ] If the print is not 20 mm: either reprint at 100% / Actual size, or
      **measure what you got and pass that** as `--square`. Do not scale.
      `ros2 run my_bot make_checkerboard.py` writes a correct one with a
      100 mm ruler printed alongside it.
- [ ] **Mounted on something rigid and flat** — a floppy printout is the usual
      cause of bad intrinsics. Tape all four edges to glass, a clipboard or a
      hardback. A millimetre of bow is 5% of a square.

### 4.2 · The run — two terminals

```bash
make camera     # terminal 1: cam2image, 640x480, RELIABLE, 15 Hz
make calib      # terminal 2: cameracalibrator, 9x6 / 20 mm
```

> **`640x480` is not decoration.** `cam2image` **defaults to 320×240**, and
> intrinsics do not transfer across resolutions — `fx`, `fy`, `cx`, `cy` all
> scale with it. Calibrate at the size `yolo.launch.py` actually runs.

> **`--no-service-check` is required, not optional.** Without it
> `cameracalibrator` waits for a `set_camera_info` service that `cam2image`
> does not offer, and just sits there looking hung. Same reason **COMMIT does
> nothing** — press **SAVE**.

- [ ] Board moved through the **whole frame**, especially the corners — that is
      where distortion lives and where the bearing error matters most
- [ ] Tilted as well as moved: X, Y, **Size** and **Skew** are four separate
      bars and skew only fills when the board is angled to the lens
- [ ] **All four coverage bars filled** before clicking CALIBRATE
- [ ] **SAVE** pressed → `/tmp/calibrationdata.tar.gz` written

### 4.3 · Score it and install it

```bash
make calib-report      # scores the tarball, writes config/ when it passes
```

> **The number beside CALIBRATE is not the gate.** That is the *linear* error.
> `cameracalibrator` computes the reprojection error and then discards it —
> `calibrator.py:797` binds `reproj_err` and never uses it. `calib-report`
> recovers it from the saved images, overall **and per image**.

- [ ] Reprojection error **< 0.5 px**

  **fx ______ · fy ______ · cx ______ · cy ______ · reproj err ______ px**

- [ ] Implied HFOV within a few degrees of the C615's **~62°**
- [ ] Over 0.5 px? `calib-report` lists the per-image error worst-first. **Drop
      the two or three bad frames and re-run** — a failed run is usually one
      tilted-past-60° or motion-blurred frame, not the whole set. Do not
      recapture blind.
- [ ] Written to `my_bot/config/c615_640x480.yaml` (`calib-report` does this,
      and **refuses** over the gate unless you pass `--force`)
- [ ] Values copied into `robot_params.yaml`
- [ ] **The node's built-in `554.0` defaults deleted** — a missing params file
      must fail loudly, not silently map the room at the wrong focal length
- [ ] **Recorded in `records/calibration.md`** with the date, the method and the
      reprojection error. `calib-report` prints the table ready to paste.
- [ ] Compressed transport, which the bridge needs:

```bash
ros2 run image_transport republish raw compressed \
  --ros-args -r in:=/image -r out/compressed:=/image/compressed
ros2 topic hz /image/compressed
```

> ⚠ **There is no `/image/compressed` until something republishes it.**
> `cam2image` publishes with a plain `rclcpp` publisher, not an
> `image_transport::CameraPublisher`, so the transport plugins never attach and
> no `/compressed` companion topic appears. The old checklist line
> (`ros2 topic hz /camera/image_raw/compressed`) was written for `usb_cam`,
> which does use `image_transport`. Decide on Day 6 whether the bridge gets a
> `republish` node or the camera driver changes.

## 5 · Camera extrinsics

- [ ] Measured from `base_link` to the camera's optical centre:

  **dx ______ m forward · dy ______ m left · dz ______ m up · yaw ______ rad**

- [ ] Put in the **URDF** as the `camera_link` joint origin — single source
- [ ] Semantic node will read `base_link → camera_link` from TF at startup, not
      from `camera.dx/dy/yaw` params (ten lines, removes a whole class of drift)
- [ ] Recorded

---

## GATE — do not start Day 5 until all of these hold

- [ ] `make nav` → RViz goal → robot arrives and stops
- [ ] Recovery behaviours fire when you block it
- [ ] Camera calibrated, reprojection error < 0.5 px, values in
      `robot_params.yaml` and `records/calibration.md`
- [ ] Extrinsics measured and in the URDF
- [ ] Everything pushed

**Then update `STATE.md`.**
