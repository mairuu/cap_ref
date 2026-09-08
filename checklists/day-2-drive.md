# Day 2 — `my_bot`, and driving on teleop

**Goal:** keyboard teleop moves the real robot, through `ros2_control`.

**Prerequisite:** Day 1 gate passed. `m 20 20` works and auto-stops.

> **Track B starts today.** The YOLO `uv` environment needs no robot — run it in
> the gaps (see `checklists/day-5-yolo.md` §1). Its failure mode is a long
> dependency fight and you want to find that today, not on Day 5.

---

## 1 · Package skeleton

Build fresh. **Do not fork `articubot_one`** — it is Jazzy-era.

- [ ] Layout created in `capstone-ws/src/`:

```
my_bot/
  urdf/      robot.urdf.xacro, wheels.xacro, sensors.xacro, ros2_control.xacro
  config/    controllers.yaml, robot_params.yaml, ydlidar.yaml,
             slam.yaml, nav2.yaml, twist_mux.yaml, c615_640x480.yaml
  launch/    real.launch.py, teleop.launch.py, slam.launch.py,
             nav.launch.py, yolo.launch.py, semantic.launch.py
  scripts/   see reference/scripts-to-rebuild.md
  udev/      99-capstone.rules   ← from Day 1
my_bot_hardware/   C++ SystemInterface for the ESP32 serial protocol
```

- [ ] `Makefile` at the workspace root — `RECOVERY.md` §7 has it in full
- [ ] **Pushed before anything is extended**

## 2 · URDF

Every number here was lost. **Measure with calipers — do not guess.** Guessing
poisons odometry, SLAM and the semantic layer at once.

- [ ] `base_link` at the drive-wheel axis centre, on the floor plane
- [ ] Wheel joints (`left_wheel_joint`, `right_wheel_joint`) — continuous
- [ ] `laser_frame` at the measured lidar mount position **and height**
      (height decides what P4 can and cannot see)
- [ ] `camera_link` at the measured camera position — this is the **single
      source** for the extrinsics; the semantic node reads TF, not params
- [ ] Real inertials, no zero masses (keeps a Gazebo target additive later)
- [ ] `ros2_control.xacro` per `RECOVERY.md` §6.3

Measured → wheel radius ______ m · separation ______ m · lidar height ______ m

## 3 · The hardware interface

`my_bot_hardware` implements `hardware_interface::SystemInterface`. Roughly 250
lines. `diff_drive_controller` then gives you odometry, TF, `cmd_vel` timeouts
and velocity limits for free — this is the **cheaper** path, not the dearer one.

Protocol reference: `reference/firmware-protocol.md`. Spec: `RECOVERY.md` §6.2.

- [ ] `on_init` — read `device`, `baud_rate`, `ticks_per_rev`, `timeout_ms`
      from the URDF `<hardware>` block; open the port
- [ ] **Discard the boot banner line** (`# boot …`) on first connect
- [ ] `read()` — send `e\r`, parse `<left> <right>`:

```
position_rad   = ticks × 2π / ticks_per_rev
velocity_rad_s = (position - prev_position) / dt
```

- [ ] `write()` — send `m <l> <r>\r`:

```
ticks_per_frame = ω_rad_s × ticks_per_rev / (2π × 30.0)
```

- [ ] **Sends every cycle, including zeros** — the firmware auto-stops after 2 s
- [ ] Serial read timeout ~50 ms; return `ERROR` rather than blocking the
      controller thread
- [ ] Plugin exported and found by `controller_manager`

- [ ] `controllers.yaml` per `RECOVERY.md` §6.1, with `update_rate: 30` to match
      the firmware's PID frame

> **Hard stop at end of day.** If this is still fighting you, fall back to a
> plain rclpy node doing `/cmd_vel` → serial → `/odom` + TF. You lose
> `diff_drive_controller`'s odometry and limits and must write them yourself,
> but it is easier to debug. **Log it in `STATE.md` deviations and move on.**

## 4 · Drive it

- [ ] **On blocks first.** Wheels spin in the right direction under teleop.
- [ ] `twist_mux` wired if you want teleop and Nav2 to coexist later
- [ ] On the ground, in open space:

```bash
make teleop
```

- [ ] Forward is forward. If the robot drives backward overall, flip
      `motors_reversed` on the ROS side — **do not rewire**.

---

## Checks before the gate

```bash
ros2 topic echo /odom                    # position changes, sane direction
ros2 run tf2_tools view_frames           # no gaps in the tree
ros2 control list_hardware_interfaces    # all claimed
ros2 topic hz /joint_states
```

- [ ] Push forward 1 m by hand → `/odom` x increases by roughly 1 m
- [ ] Rotate 90° by hand → `/odom` yaw changes by roughly π/2

  *(Rough is fine today. Day 3 makes it true.)*

---

## GATE — do not start Day 3 until all of these hold

- [ ] `make teleop` drives the real robot in the correct direction
- [ ] `/odom` changes sanely under motion
- [ ] `odom → base_link → {wheels, laser_frame, camera_link}` with **no gaps**
- [ ] Package and hardware interface committed and pushed
- [ ] Track B started — `uv` venv at least created

**Then update `STATE.md`.**
