# Hardware inventory

**All robot hardware survived. Only compute died.**

> **Updated 8 Sep 2026 after the NVMe recovery.** Most numbers below were
> *recovered*, not re-measured. Full audit: `reference/nvme-recovery-audit.md`.
> Anything still marked *unknown* must be measured on the real robot.

---

## Compute

| | |
|---|---|
| Board | Jetson Orin (new) |
| OS | **JetPack 6.1, Advantech build** → Ubuntu 22.04 (downgraded from 6.2) |
| ROS | ROS 2 Humble, apt binaries, no container |
| Previous board | died; user was `jetson`, `arduino-cli` at `/home/jetson/bin/` |

## Base

| | |
|---|---|
| Drive | Differential, two DC motors with quadrature encoders |
| Motor driver | L298N — PWM on direction inputs, enables held high, 20 kHz LEDC |
| Controller | ESP32 DOIT DevKit V1, `esp32:esp32:esp32doit-devkit-v1` |
| Link | USB serial, 57600 8N1, via CP210x bridge → `/dev/esp32` |
| Encoder decode | ESP32 PCNT hardware, 4× quadrature, 1 µs glitch filter |
| `enc_counts_per_rev_left` | **2475** — recovered |
| `enc_counts_per_rev_right` | **2470** — recovered, near-equal on purpose |
| Wheel radius | **0.0327 m** — recovered, tape-calibrated |
| Wheel separation | **0.25 m** — recovered, contact-patch to contact-patch |
| `wheel_offset_x` / `_y` | **0.255 / 0.125 m** — recovered |
| Caster radius | **0.038 m** — larger than the drive wheels; check the robot sits level |
| Controller / broadcaster | `diff_cont` / `joint_broad` |
| Hardware plugin | `my_bot/DiffDriveSerial` |

Full pin table and the encoder-pin conflict: `reference/firmware-protocol.md`.

## Lidar — YDLidar X2

| | |
|---|---|
| Plane | Single horizontal plane at mount height |
| Rate | ~10 Hz, roughly 400 rays over 360° → **0.9° resolution** |
| Link | USB serial, **115200** baud → **`/dev/ydlidar`** |
| Driver | YDLidar-SDK + `ydlidar_ros2_driver`, **built from source** — not in apt |
| Critical settings | `isSingleChannel: true` · **`reversion: true`** · **`inverted: true`** |
| Range | 0.1 – 12.0 m as configured |
| Mount height | **0.22 m** above the floor — recovered |
| `laser_frame` in `base_link` | **(−0.034, 0, 0.186)** — the **scan plane**, not the puck centre |
| Measured rate | **~11.6 Hz** (config says 10.0) |
| `/scan` QoS | **BEST_EFFORT** — a RELIABLE subscriber receives nothing, silently |

> **The X2 drops ~50% of its 400 rays indoors** (returns `0.0`) — bench-measured,
> and the figure is now **recovered from `ydlidar.yaml`**, not inherited.
> `invalid_range_is_inf: false`, so dropouts come back as `0.0`, which is
> **below** `range_min`: consumers that only check for inf/nan treat them as
> obstacles 0 m away. Filter against **the scan message's own `range_min`**.

> **`reversion` and `inverted` must both stay `true`, and neither failure shows
> up in simulation.** Their failure modes are written out in
> `reference/nvme-recovery-audit.md`. Verify with `check_scan_world_fixed.py`.

## Camera — Logitech C615

| | |
|---|---|
| Type | Mono webcam. **No depth.** |
| Resolution in use | 640 × 480 |
| Driver | **`cam2image`** (`ros-humble-image-tools`) on `/image`, **RELIABLE** QoS |
| Native mode | 480 × 640, 15 Hz |
| Horizontal FOV | **~51° MEASURED** at 640×480 (50.9° from calibration, 51.4° from a tape). ⚠ The "roughly 62°" carried here before 11 Sep was a **pre-dump guess and is wrong** — a vendor diagonal quoted for 16:9 does not survive the crop to 4:3. |
| Autofocus | ⚠ **Varifocal, AF on by default — AF moves `fx`.** Lock it: `make camera` sets `focus_automatic_continuous=0` and `focus_absolute=51`. **Same value for calibration and for the demo.** Sharp from ~0.4 m to far. |
| `fx / fy / cx / cy` | **667.874 / 669.846 / 321.569 / 234.502** at 640×480, 11 Sep. Reprojection **0.3403 px** over 59 images (80 captured, boards under 0.30 m excluded); **+0.45% against a tape measure.** `records/calibration.md`. |
| Checkerboard used | **9×6, 20 mm squares** — recovered from `.bash_history` |
| Extrinsics from `base_link` | **Measured 9 Sep and in the URDF** — `camera_link` at (0.05, 0.03, 0.167), pitch −3°. `description/camera.xacro` is the single source (D-10); the semantic node reads TF, not params. ⚠ the +y (left) **side** was assumed, not measured — magnitude 3 cm is real. |

Calibration is a **prerequisite, not a nicety**: every bearing in the semantic
layer derives from `fx/fy/cx/cy`. A 5% error in `fx` is a 5% bearing error at
the frame edge.

> **Square size is not the risk.** `fx` is exactly invariant to the checkerboard
> square size, so a mis-scaled printout cannot corrupt a bearing. The risks are
> **autofocus** and a **depth-degenerate capture**, and reprojection error sees
> neither. `make calib-scale` is the only check with an absolute length in it —
> and it is what settled these numbers.
>
> **Anything still assuming ~62°, or `fx` near 554, is 20% wrong.** The node
> default `554.0` implies ~60°; the real camera is ~51°.

---

## Device naming

Devices are addressed as stable symlinks, **never `/dev/ttyUSB*`**:

| Symlink | Device | Baud | Configured in |
|---|---|---|---|
| `/dev/esp32` | ESP32 base controller | 57600 | `description/ros2_control.xacro` |
| **`/dev/ydlidar`** | YDLidar X2 | 115200 | `real_robot.launch.py`, `config/ydlidar.yaml` |

**The rules were recovered — and they do not transfer.** Neither adapter has a
unique serial, so both were matched by **USB port path** (`KERNELS=="1-2.1"`
and `"1-2.2.4"`). The Advantech carrier board has different USB topology.

**Run `make udev`** (which calls the recovered `scripts/setup_udev.sh`) with
both devices plugged in. It picks `ATTRS{serial}` when available and falls back
to `KERNELS` when not, then installs and keeps a repo copy.

Access is `GROUP="dialout", MODE="0660"` — your user must be in `dialout`.

> The "assume a CP210x collision" guess was right, and the answer is `KERNELS`:
> **keep each device in its own physical port**, and re-run `make udev` if
> either moves.

## Power

| | |
|---|---|
| Battery | on-robot pack |
| Charge discipline | overnight, every night, from Day 1 |
| Rehearsal | on a **half-charged** pack — find the step that fails when it sags |

## Frames

```
map → odom → base_link → base_footprint
                       → chassis → { caster_wheel, laser_frame }
                       → { left_wheel, right_wheel }
```

`map → odom` comes from `slam_toolbox` — whose `base_frame` is **`base_footprint`**,
not `base_link`. `odom → base_link` comes from `diff_cont`.

> `base_link` sits on the **wheel axle**, so `base_footprint` (the ground
> projection) drops by one wheel radius. It was identity once, which put "the
> floor" 34 mm in the air — harmless for 2D scan matching, wrong for every
> costmap height filter.

Everything below `base_link` comes from the URDF, so sim and real share one
source and the numbers cannot drift.
