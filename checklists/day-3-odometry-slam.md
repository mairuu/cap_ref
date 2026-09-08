# Day 3 — Odometry that tells the truth, then the lidar

**Goal:** a `slam_toolbox` map of one room that closes.

**Prerequisite:** Day 2 gate passed. Teleop drives, TF tree is complete.

> **SLAM quality is bounded by odometry quality.** Every downstream number
> inherits this error. The morning is worth the hours — do not shortcut it.

---

## 1 · Morning — calibrate odometry

Three numbers, **in this order**. Each depends on the one before.
Full rationale: `RECOVERY.md` §5.4.

### (a) Ticks per wheel revolution — safe, no motor power

- [ ] Write `walk_straight.py` and `spin_in_place.py` first
      (`reference/scripts-to-rebuild.md`)

```
r                    # zero
(rotate one wheel exactly 10 full turns by hand, marking the tyre)
e                    # read counts
ticks_per_rev = counts / 10
```

Ten turns, not one — your marking error divides by ten. 4× quadrature, so
expect `4 × CPR × gear_ratio`.

  **`ticks_per_rev` = ____________**

### (b) Effective wheel radius

Calipers first, then correct empirically — loaded rubber rolls smaller than it
measures.

```
ticks_per_metre = ticks_per_rev / (2π × r)
```

- [ ] `walk_straight.py 3.0`, measure actual with a tape

```
r_corrected = r_measured × (commanded / actual)
```

- [ ] Repeat once. Two iterations is plenty; a third chases floor variation.

  pass 1: commanded 3.0 m, actual ______ m → r = ______
  pass 2: commanded 3.0 m, actual ______ m → **r = ______**

### (c) Wheel separation

- [ ] Mark the start heading on the floor
- [ ] `spin_in_place.py 10` — ten full rotations

```
sep_corrected = sep_measured × (commanded / actual)
```

  pass 1: actual ______ ° over/under → sep = ______
  pass 2: actual ______ ° over/under → **sep = ______**

- [ ] All three written into `controllers.yaml`
- [ ] All three written into `records/calibration.md` **with the date**
- [ ] Re-run the Day 2 sanity checks — 1 m push and 90° rotate now agree closely
- [ ] Pushed

## 2 · Afternoon — lidar

The X2 is **not in apt**. Build the SDK, then the driver.

- [ ] SDK:

```bash
git clone https://github.com/YDLIDAR/YDLidar-SDK.git && cd YDLidar-SDK
mkdir build && cd build && cmake .. && make -j$(nproc) && sudo make install
```

- [ ] `ydlidar_ros2_driver` into `cap_ws/src`, `colcon build`
- [ ] `config/ydlidar.yaml` per `RECOVERY.md` §6.5

> **`isSingleChannel: true` and `baudrate: 115200`.** Get either wrong and the
> driver connects and publishes nothing. This is the setting people miss.

- [ ] `/scan` publishes:

```bash
ros2 topic hz /scan          # expect ~10 Hz
ros2 topic echo /scan --once
```

- [ ] In RViz, the scan matches the room's actual shape. **If it is mirrored,
      that is `invert` / `reversion` / `angle_min` in `ydlidar.yaml`** — verify
      against the driver's own X2 example.

### Measure the dropout rate

The design note's "roughly half the rays" came from the lost `ydlidar.yaml` and
is **currently unverified**.

- [ ] Write and run `scan_dropout_report.py` — robot still, normal room, 100 scans

  **dropout fraction = ______ %** · worst sector: ____________

- [ ] Recorded in `records/calibration.md`

This sets `detection.min_returns` on Day 6. If it really is ~50%, a narrow bbox
at 3 m may be backed by two returns and `min_returns: 3` will reject it — the
right trade, but choose it knowingly.

- [ ] Write and run `tf_check.py` — `base_link → laser_frame` resolves with a
      sane age

## 3 · SLAM

- [ ] `config/slam.yaml` written
- [ ] Launch:

```bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$(ros2 pkg prefix my_bot)/share/my_bot/config/slam.yaml
```

- [ ] `/map` publishes; `map → odom` appears in TF
- [ ] Drive a closed loop around one room, **slowly** — the X2 sweeps 360° over
      a full 100 ms, so fast rotation smears the scan

---

## GATE — do not start Day 4 until this holds

- [ ] A driven loop closes **without a visible double wall**

> **If it does not close, the fault is almost always odometry.** Go back to §1
> and re-calibrate. Do **not** tune SLAM parameters to hide an odometry error —
> you will pay for it on Day 4 and again on Day 7.

- [ ] Map saved as a reference artefact for comparison later
- [ ] All three calibration numbers recorded and pushed

**Then update `STATE.md`.**
