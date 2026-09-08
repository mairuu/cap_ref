# Calibration record

> **This is the file whose loss cost the most.** Every number goes in here the
> moment it is measured — not at the end of the day. With the date and the
> method, so it can be re-derived or challenged later.
>
> Mirror the headline values into `STATE.md`'s "Live numbers" table.

---

## Devices — `make udev`

**MEASURED on the rebuilt board 2026-09-08.** Supersedes the recovered values
below. Both adapters are `10c4:ea60` Silicon Labs CP210x — **the predicted
VID:PID collision is confirmed** — and **neither reports a serial**, so
`setup_udev.sh` fell back to USB port path on both, exactly as it did before.

| | ESP32 | Lidar |
|---|---|---|
| Symlink | `/dev/esp32` | `/dev/ydlidar` |
| Baud | 57600 | 115200 |
| VID:PID | `10c4:ea60` | `10c4:ea60` — **collides** |
| Unique serial? | **no** | **no** |
| Old `KERNELS` (2026-09-04) | `1-2.1` | `1-2.2.4` |
| **New `KERNELS` (2026-09-08)** | **`1-2.2.4`** | **`1-2.2.1`** |
| Resolved to, first boot | `/dev/ttyUSB0` | `/dev/ttyUSB1` |
| Confirmed on new board | [x] symlink | [x] symlink |
| Confirmed as the right *device* | [ ] — §5.1 boot banner | [ ] — §5 lidar spin-up |

> ⚠ **`1-2.2.4` changed meaning between boards.** It was the **lidar** on the
> old board and it is the **ESP32** on this one. Copying the recovered
> `udev/99-my-bot-serial.rules` across would therefore not fail loudly — it
> would silently name the ESP32 `/dev/ydlidar`. The rules file in
> `cap_ws/src/my_bot/udev/` is the newly generated one; the recovered copy under
> `recoverable/` must never be installed.

> The symlinks prove the *rules* are right. They do not prove the ESP32 is on
> the port the script thinks — the script probes one adapter at a time, so it
> should be, but the first real confirmation is §5.1's `# boot reset=1
> encoders=ok` banner arriving on `/dev/esp32`. Tick the second row then.

**Method:** `cd ~/cap_ws && make udev` → `scripts/setup_udev.sh` (recovered,
interactive, both devices plugged in). Installs
`/etc/udev/rules.d/99-my-bot-serial.rules`, keeps a copy at
`src/my_bot/udev/99-my-bot-serial.rules`. Access is `GROUP="dialout",
MODE="0660"`.

**Physical sockets are now load-bearing.** Both rules match on port path, so
moving either adapter to another USB socket silently breaks its name. Label the
two sockets.

### Camera — 2026-09-08

| | |
|---|---|
| Model | **Logitech HD Webcam C615** (`046d:082c`) |
| Node | `/dev/video0` (`/dev/video1` is the same device's metadata node) |
| Group/mode | `video`, `0660` — `mic-711` **is** in `video` |
| Driver | `cam2image` (`ros-humble-image-tools`), publishes `/image`, **RELIABLE** QoS |

No udev rule needed — it is the only video device. Intrinsics are still lost;
see "Camera intrinsics" below.

## Firmware — `RECOVERY.md` §5.2, §5.3

| | Value | Date |
|---|---|---|
| `LEFT_ENC_INVERT` | | |
| `RIGHT_ENC_INVERT` | | |
| Correct right-encoder pins | 23/22 or 32/33 | |
| GPIO12 boot reliability (5 cycles) | | |
| Firmware commit after fixes | | |

## Odometry — `RECOVERY.md` §5.4

### (a) Encoder counts per revolution — **RECOVERED**

Two parameters, not one. In `description/ros2_control.xacro`.

| Param | Value | Note |
|---|---|---|
| `enc_counts_per_rev_left` | **2475** | |
| `enc_counts_per_rev_right` | **2470** | near-equal **on purpose** |

**Why near-equal:** `~/firmware/calibation` recorded `l:2473 r:2556`. That 3.4%
split was **wrong, not imprecise** — counts/rev is a property of the disc and
gearbox, and both sides are the same parts. Only tyre diameter differs, and that
belongs in the radius multipliers.

**Evidence (2026-08-28, `calibrate_straight.py`):** a 3 m closed-loop run ended
**62 cm left** of the line while odom reported 0.0000 m lateral drift. Predicted
drift from the split alone: 57 cm. The split explained **93%** of it.

> ⚠ The xacro comment says "2514 is the mean", but the installed values are
> 2475/2470 — re-derived after the comment was written. **Trust the values.**
> Re-confirm with `calibrate_correct.py` if a straight run drifts.

### (b) Effective wheel radius — **RECOVERED**

**`wheel_radius` = 0.0327 m**

Free diameter is 68 mm (→ 0.034 m), but the loaded rolling radius is ~4%
smaller, and any error in `enc_counts_per_rev_*` lands here too. Calibrated
against a tape with `calibrate_straight.py`, not measured with calipers.

`corrected_radius = wheel_radius × (tape distance / odom distance)`

> **Duplicated in two files and they must agree:** `config/my_controllers.yaml`
> (the copy `diff_drive_controller` actually reads — this one scales odometry)
> and `description/robot_core.xacro` (drives the URDF ground plane and lidar
> height). Change one, change the other, or sim and real diverge.

| Re-verify on new board | Tape | Odom | New `r` | Date |
|---|---|---|---|---|
| | | | | |

### (c) Wheel separation — **RECOVERED**

**`wheel_separation` = 0.25 m** — measured contact-patch to contact-patch,
confirmed. Must equal `2 × wheel_offset_y` (0.125) in `robot_core.xacro`.

Method: `calibrate_spin.py --turns 10`, both directions. A separation error is
symmetric — CW and CCW must give the same size of error, opposite in sign. If
they differ, something asymmetric is dragging and fitting a separation number
would just paper over it.

| Re-verify | Turns | Residual angle | New `sep` | Date |
|---|---|---|---|---|
| CCW | 10 | | | |
| CW | 10 | | | |

### (d) Chassis geometry — **RECOVERED**

| Property | Value | Confidence |
|---|---|---|
| `wheel_offset_x` (axle → chassis rear) | 0.255 | measured |
| `wheel_offset_y` | 0.125 | measured (= sep/2) |
| `wheel_thickness` | 0.028 | |
| `chassis_length` | 0.295 | **unverified** — so chassis front edge is derived |
| `chassis_width` | 0.21 | |
| `chassis_height` | 0.138 | |
| `caster_wheel_radius` | 0.038 | measured — **larger than the 34 mm drive wheels** |

> ⚠ The caster is 4 mm taller than the drive wheels. The URDF formula drops its
> contact point onto the drive wheels' ground plane so the *model* stays level.
> **Verify the real robot is level too** — if the caster bolts flat to the same
> deck as the motors, the rear sits 4 mm high and the robot pitches nose-down by
> ~1.3°, tilting the lidar with it.

**Nav2 footprint** (do **not** replace with `robot_radius` — a circle needs
r=0.265 and refuses doorways it fits through):

```
[[0.09, 0.147], [0.09, -0.147], [-0.265, -0.147], [-0.265, 0.147]]
```

## Lidar — **RECOVERED**

| | Value | Source |
|---|---|---|
| `lidar_height_above_ground` | **0.22 m** | measured |
| `lidar_offset_behind_axle` | **0.034 m** | measured |
| `laser_frame` in `base_link` | **(−0.034, 0, 0.186)** | derived |
| **Dropout fraction** | **~50% of 400 rays** are `0.0` indoors | bench-measured |
| Measured scan rate | **~11.6 Hz** (config says 10.0) | measured |
| `reversion` | **true** — puck 0° points at robot BACK | |
| `inverted` | **true** — X2 is CW, ROS needs CCW | |
| `range_min` / `range_max` | 0.1 / 12.0 | |
| `invalid_range_is_inf` | **false** → dropouts are `0.0`, **below** `range_min` | |
| `/scan` QoS | **BEST_EFFORT** — a RELIABLE subscriber gets nothing, silently | |

> `laser_frame` is the **scan plane**, not the centre of the puck. The visual
> cylinder is drawn centred on it, so the rendered puck is a couple of cm off.

**Both orientation flags must stay `true`, and neither shows up in simulation.**
Failure modes are written out in `reference/nvme-recovery-audit.md`. Verify with
`check_scan_world_fixed.py` after any change.

| Re-verify on new board | Result | Date |
|---|---|---|
| Dropout fraction | | |
| `check_scan_world_fixed.py` | | |

## Camera intrinsics — ⚠ **STILL LOST, must redo**

`robot_params.yaml` and `camera_info.yaml` were in `semantic_objects/config/`,
which the dump did not reach. **This is the one calibration that must be redone.**

The tools that produced them (`capture_checkerboard.py`, `calibrate_camera.py`
in `semantic_objects/tools/`) are also lost — rebuild or use
`ros-humble-camera-calibration`.

**Recovered method** (from `.bash_history`): checkerboard **9×6, 20 mm squares**.

```
python3 capture_checkerboard.py --out /tmp/calib
python3 calibrate_camera.py --dir /tmp/calib --size 9x6 --square 20.0 \
    --write-params ../config/robot_params.yaml --write-info ../config/camera_info.yaml
```

The history shows this was run **many** times — budget for it. One run was kept
as `/tmp/calib-0.4`, suggesting 0.4 px was the error being chased.

| | Value |
|---|---|
| Resolution | 640 × 480 |
| `fx` | |
| `fy` | |
| `cx` | |
| `cy` | |
| Distortion coefficients | |
| **Reprojection error** | ______ px (target < 0.5) |
| Checkerboard | **9×6, 20 mm** |
| Date | |

**Saved to:** `my_bot/config/c615_640x480.yaml`

## Camera extrinsics — `RECOVERY.md` §5.8

Measured from `base_link` to the camera's optical centre.

| | Value | Date |
|---|---|---|
| `dx` (forward) | | |
| `dy` (left) | | |
| `dz` (up) | | |
| `yaw` | | |

**Single source:** the URDF `camera_link` joint origin. The node reads TF.

## YOLO environment — `RECOVERY.md` §5.6

> **The most expensive thing here to rediscover.** Write these down the moment
> the three import checks pass.

**Target versions, recovered from `launch/yolo.launch.py`:**

| Package | Was working | On JetPack 6.1 |
|---|---|---|
| JetPack | 6.2 | **6.1 Advantech** — re-verify all of these |
| `torch` | **2.11.0** JetPack aarch64+CUDA wheel | |
| `torchvision` | **0.26.0** JetPack aarch64 wheel | |
| `tensorrt` | present, **not in `uv.lock`** | |
| `ultralytics` | | |
| Python | **3.10.12** off `/usr/bin` | |

> ⚠ **Never run `uv sync`** against this venv. The recovered `uv.lock` pins
> generic PyPI torch **2.13.0** / torchvision **0.28.0** and omits `tensorrt`
> entirely — a sync leaves you with no CUDA and no `.engine` support.

`torch.cuda.is_available()` → ______   **Date:** ______

**Recovered performance (JetPack 6.2, must be re-measured on 6.1):**

| | Value |
|---|---|
| Pipeline rate | **15 Hz end to end, camera-limited** |
| `yolo26n` inference @ 640×640 | ~18 ms |
| `yolo26s` inference @ 640×640 | ~27 ms |
| `imgsz` | 640×640 fixed in the engine |
| Camera | `cam2image`, 640×480 @ 15 Hz, **RELIABLE** QoS |

| Re-measured on 6.1 | Value |
|---|---|
| Model | |
| Detection rate | ______ Hz |
| Temp after 5 min | ______ °C |

## Nav2 — **RECOVERED**

| | Value | Note |
|---|---|---|
| `footprint` | `[[0.09,0.147],[0.09,-0.147],[-0.265,-0.147],[-0.265,0.147]]` | **not** `robot_radius` |
| `inflation_radius` | 0.25 | both costmaps |
| `cost_scaling_factor` | 3.0 | |
| `allow_unknown` | **true** | frontier goals sit on the unknown boundary |
| DWB `max_vel_x` | 0.055 | **timid starting value, not measured** |
| DWB `min_vel_x` | −0.025 | |
| DWB `max_vel_theta` | 0.125 | |
| `velocity_smoother` max | `[0.055, 0.0, 0.125]` | |
| slam_toolbox `base_frame` | **`base_footprint`** | not `base_link` |
| slam resolution | 0.05 | |

> ⚠ **These are the only speed limits the robot has.** `diff_cont` sets none and
> the hardware interface passes commands straight through. Watch it drive before
> raising them.

## Final results — the tape-measure protocol (Day 7)

Ground truth chair position, measured against two walls: x ______ y ______

| Pass | Direction | Published x | Published y | Error |
|---|---|---|---|---|
| 1 | front | | | |
| 2 | right | | | |
| 3 | back | | | |
| 4 | left | | | |

| Metric | Target | Measured |
|---|---|---|
| Absolute position error | < 0.25 m | |
| Spread across four passes | < 0.15 m | |
| Duplicate landmarks per object | 1.0 | |
| Ghosts surviving a second pass | 0 | |
| Detections mapped / received | > 0.6 | |
