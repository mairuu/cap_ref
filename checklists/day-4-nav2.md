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
- [ ] **Mounted on something rigid and flat.** This is the one that matters.

> ⚠ **Correction, 11 Sep — an earlier version of this section had this
> backwards.** It said a mis-scaled printout corrupts `fx` and told you to
> measure the squares before capturing. **It does not.** `fx`, `fy`, `cx` and
> `cy` are *exactly invariant* to square size: scale the squares by any factor
> and the solver scales every board distance by the same factor and returns the
> identical camera matrix. Measured on this board — seven significant figures
> of agreement across a 2.5× change in `--square`, with the reported board
> distance moving 0.42 m → 1.05 m.
>
> **So a badly printed board cannot corrupt a bearing.** `atan((u − cx)/fx)`
> has no length in it. Square size sets only the scale of the board's *pose*,
> which we never use — range comes from the lidar.
>
> Getting `--square` right is still worth thirty seconds, because `calib-scale`
> below compares model distances against a tape and wants the same units. But
> it is not the hazard it was written up as. **The real hazards are 4.2.**

- [ ] Need a board? `ros2 run my_bot make_checkerboard.py` writes one at exact
      PDF scale with a 100 mm ruler printed beside it. Print at 100%, not
      fit-to-page.
- [ ] **Mounted on something rigid and flat** — a floppy printout is the usual
      cause of bad intrinsics. Tape all four edges to glass, a clipboard or a
      hardback. A millimetre of bow is 5% of a square.

### 4.2 · The two things that actually corrupt `fx`

**Autofocus.** The C615 is varifocal — refocusing physically moves the lens, so
the focal length being calibrated is not a constant while
`focus_automatic_continuous` is 1. Confirmed on this board 11 Sep: left alone
with AF on, the driver moved `focus_absolute` from 51 to 85 unprompted. A
capture taken across that is one pinhole model fitted to several cameras, and at
run time the lens keeps drifting away from whatever was calibrated.

- [ ] **Focus locked, to the same value for calibration and for the demo.**
      `make camera` now does this (`FOCUS`, default 51). `make camera FOCUS=auto`
      puts it back, and should never be used for a calibration run.

> **Expect the RMS to get slightly WORSE when you lock it, and accept that.**
> `FOCUS=51` focuses far, so boards closer than ~0.3 m are soft and carry almost
> all the residual — measured 11 Sep: 0.628 px under 0.30 m against 0.271 px
> beyond 0.65 m, `corr(rms, depth) = −0.735`. The 0.3651 → 0.4464 px rise
> between the two runs is **blur, not a worse camera model**, and 51 is the
> right choice for a robot that looks across a room. Want a tighter number? Keep
> the board beyond ~0.35 m. Do **not** unlock the focus to chase it.

**A depth-degenerate capture.** If every view is at roughly the same distance,
`fx` and board distance trade off against each other almost freely — the solver
can be 15–20% wrong about `fx` and still fit its own images beautifully.
**Reprojection error cannot see this.** The 11 Sep run split by capture order
into `fx` 819.74 (29 frames, all 0.70–1.23 m, `cx` adrift at 391.7) against
676.30 (19 frames, 0.18–1.01 m, `cx` a healthy 322.1) — 17.5% apart, while the
*narrow* group scored the *better* RMS, 0.15 px against 0.53.

- [ ] Board swept through a **wide range of depths** — filling the frame at one
      end, a small patch at the other. `calib-report` prints the ratio and wants
      **2.5× or more**.
- [ ] `cx`, `cy` land near the frame centre (320, 240). A principal point that
      has wandered is the fingerprint of the degenerate fit above.

### 4.3 · The run — two terminals

```bash
make camera     # terminal 1: cam2image 640x480 RELIABLE 15 Hz, focus locked
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

### 4.4 · Score it and install it

```bash
make calib-report      # scores the tarball, writes config/ when it passes
```

> **The number beside CALIBRATE is not the gate.** That is the *linear* error.
> `cameracalibrator` computes the reprojection error and then discards it —
> `calibrator.py:797` binds `reproj_err` and never uses it. `calib-report`
> recovers it from the saved images, overall **and per image**.

- [ ] Reprojection error **< 0.5 px**

  **fx ______ · fy ______ · cx ______ · cy ______ · reproj err ______ px**

- [ ] Board **depth ratio ≥ 2.5×**, and `cx`/`cy` near (320, 240)
- [ ] Implied HFOV near the **~51° measured on this camera** — a smell test, not
      a gate. It cannot detect a mis-scaled board (see 4.1); a large gap points
      at `fx` itself being wrong.

> ⚠ **~51°, not the ~62° this project carried until 11 Sep.** That figure was a
> pre-dump guess and it was wrong — the calibration says 50.9° and the tape says
> 51.4°, independently. Anything still assuming ~62°, or `fx` near the semantic
> node's `554.0` default, is about 20% out.
- [ ] Over 0.5 px, or `cx`/`cy` off centre? `calib-report` lists the per-image
      error worst-first, and `--min-depth 0.30` refits without the soft near
      frames. A failed run is usually a handful of bad frames, not a bad set —
      do not recapture blind.

> **Trim by depth, not by score, and stop early.** On 11 Sep dropping boards
> under 0.30 m took RMS 0.4464 → 0.3403 and `cx` 331.19 → 321.57. Going on to
> 0.35 m scored better again (0.3156) and was **worse**: `cx` swung out to
> 308.4, because the near views are what constrain the wide end of the
> distortion model. **RMS will not tell you where to stop — `cx` will.**
- [ ] Written to `my_bot/config/c615_640x480.yaml` (`calib-report` does this,
      and **refuses** over the gate unless you pass `--force`)
- [ ] Values copied into `robot_params.yaml`
- [ ] **The node's built-in `554.0` defaults deleted** — a missing params file
      must fail loudly, not silently map the room at the wrong focal length

### 4.5 · Pin `fx` to a tape measure

**Nothing inside the calibration can tell you `fx` is wrong.** Reprojection
error is computed in pixels against the same self-consistent fit; a chessboard
carries no absolute length. The only way to test `fx` is to introduce a length
the calibration does not control.

```bash
make calib-scale                        # with `make camera` running
make calib-scale DISTANCES=0.5,0.8,1.2  # pick your own
```

Hold the board flat-on at each tape-measured distance. It regresses what the
model thinks the distance is against what the tape says: **slope 1.000 means
`fx` is right**, and the intercept absorbs the entrance-pupil offset — which is
why it asks for more than one distance rather than trusting any single one.

- [ ] Slope within **2%** of 1.000
- [ ] Slope recorded in `records/calibration.md` alongside `fx`

> ✅ **Passed 11 Sep: slope 1.0117 over three distances**, residuals ±9 mm,
> intercept 19.3 mm — giving the tape's own `fx = 664.87`. That is what makes
> the installed **fx 667.874 · fy 669.846 · cx 321.569 · cy 234.502**
> trustworthy, at **+0.45%**. The reprojection error alone was not, and the
> first attempt proves it: it scored *better* (0.3651 px) while being 17.5%
> unstable in `fx`.
- [ ] Off by more than that? **Recalibrate — do not scale `fx` by the ratio.**
      Fix the cause (focus lock, depth spread), then recapture.

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
- [ ] Camera calibrated with **focus locked**, reprojection error < 0.5 px,
      board depth ratio ≥ 2.5×, values in `robot_params.yaml` and
      `records/calibration.md`
- [ ] **`make calib-scale` slope within 2% of 1.000.** The reprojection error is
      not sufficient on its own — it cannot see a wrong `fx`.
- [ ] Extrinsics measured and in the URDF
- [ ] Everything pushed

**Then update `STATE.md`.**
