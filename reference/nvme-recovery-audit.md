# NVMe recovery — what came back, 8 Sep 2026

Audited against the actual files in `recoverable/mount/`. **This supersedes the
"definitively gone" list in `RECOVERY.md` §01**, which was written before the
dump existed.

Recovered tree is 4.9 MB: `Makefile`, `uv.lock`, `.bash_history` (1,800+ lines),
`efi/`, and the **complete `my_bot` package**.

---

## Recovered — high value

| What | Where | Why it matters |
|---|---|---|
| **Whole `my_bot` package** | `recoverable/mount/my_bot/` | URDF, ros2_control, 8 launch files, 7 configs, C++ hardware interface, 5 scripts, udev rules, 2 Gazebo worlds |
| **Root `Makefile`** | `recoverable/mount/Makefile` | Every target, heavily commented with the reasoning |
| **All odometry calibration** | `config/my_controllers.yaml`, `description/ros2_control.xacro` | With method **and** date **and** the story behind each |
| **Lidar orientation flags** | `config/ydlidar.yaml` | `reversion` / `inverted`, each with its failure mode written out. Days of work. |
| **X2 dropout figure** | `config/ydlidar.yaml` | "~50% of the 400 rays are 0.0" — **now sourced**, not inherited |
| **twist_mux e-stop design** | `config/twist_mux.yaml`, README | The robot's only emergency stop |
| **Nav2 footprint + speeds** | `config/nav2_params.yaml` | Real footprint polygon, and the only velocity clamp that exists |
| **`setup_udev.sh`** | `scripts/setup_udev.sh` | Interactive, handles the no-serial case properly |
| **4 calibration/diagnostic scripts** | `scripts/` | Better than the specs I wrote for them |
| **`.bash_history`** | `recoverable/mount/.bash_history` | The commands that actually worked |

## Still lost — nothing recovered these

| What | Consequence |
|---|---|
| **`robot_params.yaml` + `camera_info.yaml`** | **Camera intrinsics are still gone.** The one calibration that must be redone. |
| `semantic_objects` September tree | Only the June-era copy on the USB drive survives. P1–P8 were read from the September one. |
| **`cap_ws/patches/`** | A one-line `yolo_ros` patch needed for `.engine` models. Without it `make yolo` **hangs at `Activating...`**. |
| `semantic_objects/tools/` | `capture_checkerboard.py`, `calibrate_camera.py` |
| `/home/jetson/yolo/compile.py` | Built the TensorRT engines |
| The `.engine` files | Invalid after the JetPack downgrade anyway — see below |
| The hand-built venv | Path and *contents* known; the tree itself is gone |
| `~/firmware/calibation` | Recorded `l:2473 r:2556`; superseded, see below |

---

## What the JetPack 6.1 downgrade changes

Ubuntu 22.04 either way, so **ROS 2 Humble is still correct** — constraint 1 is
untouched. Three things do change:

1. **The `.engine` files will not load.** A TensorRT plan is tied to the
   TensorRT version it was built with. 6.2 → 6.1 changes it. They must be
   re-exported from the `.pt` weights — and `compile.py` is lost, so that gets
   rewritten (ultralytics `model.export(format="engine", imgsz=640)`).
2. **The JetPack torch/torchvision wheels must match L4T 36.4**, not whatever
   6.2 shipped. The recovered launch file records the working pair as
   **torch 2.11.0 / torchvision 0.26.0 (JetPack aarch64 wheels)** — verify that
   against the 6.1 wheel index rather than assuming.
3. **The recovered udev rules are almost certainly wrong.** Both devices matched
   by **USB port path** (`KERNELS=="1-2.1"` and `"1-2.2.4"`) because neither has
   a unique serial. An Advantech carrier board has different USB topology from
   the devkit those paths were recorded on. **Re-run `make udev`** — do not
   copy the rules file across.

---

## Facts that contradict what I wrote before the dump

| I wrote | Actually |
|---|---|
| `/dev/lidar` | **`/dev/ydlidar`** |
| `usb_cam` namespaced to `/camera` | **`cam2image`** from `image_tools`, publishing `/image`, **RELIABLE** QoS |
| Checkerboard 8×6, 25 mm | **9×6, 20 mm** (`--size 9x6 --square 20.0`) |
| Assume a CP210x VID:PID collision | Correct — and the answer was **`KERNELS`**, neither adapter has a serial |
| Controller named `diff_drive_controller` | **`diff_cont`**; broadcaster is `joint_broad` |
| `slam_toolbox` base frame `base_link` | **`base_footprint`** |
| Nav2 `robot_radius` | **`footprint` polygon** — a circle needs r=0.265 and refuses doorways it fits through |
| One hardware `ticks_per_rev` | **Two params**, `enc_counts_per_rev_left` / `_right` |
| Gazebo descoped as never-built | It **worked** — `worlds/room.world` exists and `make sim` is wired up |

---

## The encoder-split story — read this before touching odometry

`description/ros2_control.xacro` carries a long comment worth preserving:

> `~/firmware/calibation` recorded `l:2473 r:2556` "measured per wheel by hand",
> with no method written down, **and that 3.4% split was wrong, not merely
> imprecise.** Counts per rev is a property of the encoder disc and the gearbox
> ratio; both sides are the same parts, so the true figures cannot differ by 3%.
> Only tyre diameter can differ between wheels, and that belongs in the radius
> multipliers.
>
> Measured 2026-08-28 with `calibrate_straight.py`: a 3 m closed-loop run ended
> **62 cm left** of the line while odom reported 0.0000 m of lateral drift. The
> loop steers on odom, so it held the *estimated* arcs equal, which with that
> split forces the right wheel to physically turn 3.4% further. Predicted drift:
> 57 cm. Measured: 62 cm. **The split explained 93% of it.**

> ⚠ **Discrepancy to resolve.** That comment says "2514 is the mean of the two
> old figures", but the installed values are `left: 2475` / `right: 2470`. The
> numbers were evidently re-derived after the comment was written. Trust the
> **values**, not the prose, and re-confirm with `calibrate_correct.py` if a
> straight run drifts.

---

## The two lidar flags — the most expensive thing in the dump

Both are `true` and both must stay `true`. From `config/ydlidar.yaml`:

**`reversion: true`** — the puck is mounted with its 0° reference pointing at
the **back** of the robot, so raw bearings are 180° out. This makes the SDK
apply `angle = angle + pi`, which runs **before** the `inverted` mirror, so the
two flags are independent: this one rotates, that one changes handedness.

> With it false the scan is rotated by π. Unlike a mirrored scan this stays
> world-fixed while the robot turns in place, so `check_scan_world_fixed.py`
> **cannot catch it** — it only tests rotation. It breaks on **translation**
> instead: the error is a reflection through the lidar centre, which moves with
> the robot, so driving forward smears the map and `slam_toolbox` loses the match.

**`inverted: true`** — the X2 reports ray angles increasing **clockwise**;
REP-103 requires counter-clockwise-positive. The SDK applies `angle = 2π − angle`.

> With it false the scan is mirrored, and it does not look mirrored: once TF
> places it in odom it **counter-rotates at twice the robot's yaw rate**,
> because a feature belonging at bearing `b` is emitted at `−(b − yaw)` and
> lands at `2·yaw − b`. Driving straight looks nearly fine; the moment you
> rotate, the world spins, `slam_toolbox` can never match consecutive scans, the
> map stays almost empty and `map → odom` sits at exactly identity.

**Neither shows up in simulation.** Gazebo's `gpu_lidar` is mounted at
`laser_frame` with identity rotation and is counter-clockwise natively. These
are real-robot-only failures. Verify with `check_scan_world_fixed.py` after any
change: turn 90° and the scan must still overlap itself in the odom frame.

**Do not "fix" either by yawing `laser_joint` in `description/lidar.xacro`** —
that file is shared with sim and would break the sim scan instead.

---

## The YOLO architecture that worked

Not what I assumed. From the Makefile, `launch/yolo.launch.py` and the README:

- **`yolo_ros` nodes** (`yolo_node`, `tracking_node`, `debug_node`) from
  `mgonzs13/yolo_ros`, publishing **`yolo_msgs/DetectionArray`** on
  `/yolo/detections` and `/yolo/tracking`, plus `/yolo/dbg_image`
- **TensorRT `.engine` models**, fixed 640×640, at `/home/jetson/yolo/`
  (`yolo26n.engine`, `yolo26s.engine`)
- **Camera is `cam2image`** from `ros-humble-image-tools` on `/image`, 640×480
  @ 15 Hz, **RELIABLE** QoS — the YOLO subscribers must match
- Venv at `dev_ws/install/yolo_ros/share/yolo_ros/.venv`, interpreter
  `/usr/bin/python3.10` — the same one the ROS nodes use, so only
  `PYTHONPATH` needs setting. **No `activate`.**
- **Measured 15 Hz end to end, camera-limited.** `yolo26n` infers 640×640 in
  ~18 ms; `yolo26s` ~27 ms.

> ⚠ **`uv sync` is the trap.** The checked-in `uv.lock` (recovered) pins generic
> PyPI **torch 2.13.0 / torchvision 0.28.0** and does not list `tensorrt` at
> all. Syncing it downgrades the JetPack aarch64 wheels (**torch 2.11.0 /
> torchvision 0.26.0**) and prunes TensorRT, leaving a venv with no CUDA and no
> `.engine` support. Upstream's `yolo_bringup/launch/yolo.launch.py` runs
> exactly that sync on every start, which is why this workspace has its own
> launch file. **The recovered `uv.lock` is a hazard, not an asset.**

---

## Safety facts recovered

**Nothing between Nav2 and the motors clamps speed.** `diff_cont` sets no
limits and `hardware/diffdrive_serial.cpp` passes commands straight to the
ESP32. The limits in `nav2_params.yaml` are the **only** speed limit the robot
has — and they are deliberately timid starting values, not measured ones:

```
max_vel_x      0.055 m/s   (DWB)      min_vel_x  -0.025
max_vel_theta  0.125 rad/s (DWB)
velocity_smoother  max [0.055, 0.0, 0.125]
```

**`twist_mux` is the e-stop.** `/cmd_vel` (Nav2, priority 10) and
`/cmd_vel_teleop` (human, priority **100**) → `/diff_cont/cmd_vel_unstamped`.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/cmd_vel_teleop
```

> `make teleop` publishes to `/diff_cont/cmd_vel_unstamped` **downstream of the
> mux**, so during an autonomous run it does **not** override Nav2 — the two
> fight over the same topic and the robot jerks between them. `make teleop-nav`
> is the one that stops the robot. Getting this wrong is the difference between
> stopping the robot and making it worse.
