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

- [ ] Checkerboard printed and **mounted on something rigid and flat** — a
      floppy printout is the usual cause of bad intrinsics
- [ ] Camera up:

```bash
ros2 run usb_cam usb_cam_node_exe --ros-args -r __ns:=/camera \
  -p image_width:=640 -p image_height:=480
```

- [ ] Calibrate:

```bash
ros2 run camera_calibration cameracalibrator \
  --size 8x6 --square 0.025 image:=/camera/image_raw camera:=/camera
```

- [ ] Board moved through the **whole frame**, especially the corners — that is
      where distortion lives and where the bearing error matters most
- [ ] **All four coverage bars filled** before clicking Calibrate
- [ ] Reprojection error < 0.5 px

  **fx ______ · fy ______ · cx ______ · cy ______ · reproj err ______ px**

- [ ] Saved to `my_bot/config/c615_640x480.yaml`
- [ ] `usb_cam` pointed at it via `camera_info_url`
- [ ] Values copied into `robot_params.yaml`
- [ ] **The node's built-in `554.0` defaults deleted** — a missing params file
      must fail loudly, not silently map the room at the wrong focal length
- [ ] Recorded in `records/calibration.md` with the reprojection error
- [ ] Compressed transport works — the bridge needs it:

```bash
ros2 topic hz /camera/image_raw/compressed
```

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
