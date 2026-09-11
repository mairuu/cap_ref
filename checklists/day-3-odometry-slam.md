# Day 3 — Odometry that tells the truth, then the lidar

**Goal:** a `slam_toolbox` map of one room that closes.

**Prerequisite:** Day 2 gate passed. Teleop drives, TF tree is complete.

> **SLAM quality is bounded by odometry quality.** Every downstream number
> inherits this error. The morning is worth the hours — do not shortcut it.

---

## 1 · Morning — confirm odometry

> ⚠ **Rewritten 9 Sep. This section was written before the NVMe dump.** All
> three numbers are **recovered**, with method and date, in
> `records/calibration.md`. This is now a **confirmation**, not a derivation —
> do not re-derive what is already recorded, and do not edit
> `my_controllers.yaml` unless a measurement below disagrees with it.
>
> The scripts it asked you to write also already exist, under better names:
> `walk_straight.py` → **`calibrate_straight.py`**, `spin_in_place.py` →
> **`calibrate_spin.py`**, plus **`calibrate_correct.py`** for the encoder
> split. All three are recovered and installed.

Current values, from `config/my_controllers.yaml`:

| | Value | Origin |
|---|---|---|
| `enc_counts_per_rev_left` | 2475 | recovered |
| `enc_counts_per_rev_right` | 2470 | recovered — near-equal **on purpose** |
| `wheel_radius` | 0.0327 m | recovered, tape-calibrated |
| `wheel_separation` | 0.25 m | recovered, contact-patch |

### (a) Ticks per wheel revolution — **do not re-measure by hand**

The hand method this checklist described is what produced the old
`l:2473 r:2556` figures, and **that 3.4 % split was wrong, not merely
imprecise** — counts per rev is a property of the encoder disc and the gearbox,
and both sides are the same parts. It cost 62 cm of drift over 3 m. The story is
in `reference/nvme-recovery-audit.md`; read it before touching these.

If a straight run drifts, the tool is **`calibrate_correct.py`**, not a tyre
mark and ten turns by hand.

### (b) Effective wheel radius — confirm

- [ ] `ros2 run my_bot calibrate_straight.py 3.0`, measure the actual with a tape

```
r_corrected = 0.0327 × (commanded / actual)
```

  pass 1: commanded 3.0 m, actual ______ m → r = ______
  Agrees with 0.0327 within a few percent? Leave it alone.

### (c) Wheel separation — **the one open question**

Day 2's hand-turn came out **7 % short** (90° eyeballed → −83.7° reported),
which implies `wheel_separation` ≈ **0.2325** rather than 0.25. That 90° was
eyeballed, so it is a *prediction*, not a number. This settles it:

- [ ] Mark the start heading on the floor
- [ ] `ros2 run my_bot calibrate_spin.py --turns 10` — both directions

```
sep_corrected = 0.25 × (commanded / actual)
```

  CW:  actual ______ ° → sep = ______
  CCW: actual ______ ° → sep = ______

**If it lands near 0.2325, the two independent estimates agree and the number
changes.** If it lands near 0.25, Day 2's eyeball was the error and nothing
changes. Either way, write down which.

- [ ] Any change written into `config/my_controllers.yaml`
- [ ] Result written into `records/calibration.md` **with the date**, agree or not
- [ ] Re-run `odom_check.py` — 1 m push and 90° rotate now agree closely
- [ ] Pushed

## 2 · Afternoon — lidar — **DONE 9 Sep**

The X3 Pro is **not in apt**. Build the SDK, then the driver.

> ⚠ **The sensor is an X3 Pro, not an X2** (corrected 11 Sep). Upstream's
> `X2.yaml` and `X3.yaml` are identical, so the transport settings are
> unaffected — but `range_max` is **8.0**, not 12.0. See
> `records/calibration.md`.

- [x] SDK — built at `01cdda4`, installed to `/usr/local`
      (`libydlidar_sdk.a`, static):

```bash
git clone https://github.com/YDLIDAR/YDLidar-SDK.git ~/YDLidar-SDK
cd ~/YDLidar-SDK && mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release .. && make -j$(nproc) && sudo make install
```

- [x] `ydlidar_ros2_driver` into `cap_ws/src`, `colcon build`

> ⚠ **Check out the `humble` branch. `master` does not work on Humble.**
> Upstream's default branch is Dashing-era: its launch files use
> `node_executable=` / `node_name=` (removed in Foxy) and its node calls the
> one-argument `declare_parameter(name)`, deprecated in Humble and throwing
> when no override is given. Built here from `humble` at `4ef70d3`.
>
> ```bash
> git -C ~/cap_ws/src/ydlidar_ros2_driver checkout humble
> ```

- [x] `config/ydlidar.yaml` — **recovered, not written.** Both orientation
      flags are already correct and must stay `true`. Read their comments
      before touching either.

> **`isSingleChannel: true` and `baudrate: 115200`.** Get either wrong and the
> driver connects and publishes nothing. This is the setting people miss.
> Both are already right in the recovered file.

- [x] `/scan` publishes — **11.57 Hz**, 350 rays, `laser_frame`

> ⚠ **`ros2 topic hz /scan` prints nothing, and that is not a dead lidar.**
> `hz` subscribes RELIABLE; `/scan` is BEST_EFFORT, so it never receives a
> message and never says why. Humble's `hz` has no QoS flag (`--qos-*` is on
> `echo`, not `hz`). Use instead:
>
> ```bash
> ros2 topic info /scan --verbose      # publisher alive? QoS?
> ros2 run my_bot scan_dropout_report.py   # subscribes sensor-data QoS
> ```

- [ ] In RViz, the scan matches the room's actual shape (`make rviz`). **If it
      is mirrored, that is `invert` / `reversion` / `angle_min` in
      `ydlidar.yaml`** — verify against the driver's own X3 example.
      *Settled 11 Sep: both flags verified with `check_scan_bearing.py`.*
      *An ASCII top-down of 20 scans on 9 Sep showed a wall ~4 m left and ~1 m
      behind with open floor ahead, which matched the room. Confirm by eye.*
- [ ] `check_scan_world_fixed.py` — **drives the robot ~90°, needs clear space**

### Measure the dropout rate — **DONE 9 Sep, and the recovered figure was wrong**

- [x] `scan_dropout_report.py` written and run — 100 scans, robot still

  **dropout fraction = 27.9 %** · worst sector: **+75° (LEFT), 69.6 %**

  Not ~50 %, and the scan is **350 rays, not 400** — the driver prints
  `Single Fixed Size: 350` on startup and `angle_increment` 1.032° agrees. 400
  was inherited and never counted.

- [x] Recorded in `records/calibration.md`

> ⚠ **That 27.9 % is a fact about this corner of this room.** Dropout was 5–28 %
> on the robot's right and 46–70 % on its left, because bearings with nothing
> inside `range_max` 12 m return `0.0` — identical to a true dropout, and
> indistinguishable in the message. **Re-run it in the room the map is made in**
> before using it for anything. If the asymmetry follows the *robot* rather than
> the room, suspect chassis clipping or a glazed surface, and know that before
> Day 6 blames the camera.

This sets `detection.min_returns` on Day 6. At 27.9 %, a 0.3 m object subtends
~6 rays at 3 m of which ~4 come back, so `min_returns: 3` clears 3 m. At the
recovered 50 % it would not have — that is the trade, now made knowingly.

- [x] `tf_check.py` — all eight edges resolve; `base_link → laser_frame`
      `(−0.034, 0, +0.187)`, which is **0.220 m above `base_footprint`** and
      matches the 0.22 m tape measure

## 3 · SLAM — config in place 9 Sep, the drive is still to do

- [x] `config/mapper_params_online_async.yaml` — **recovered, not written.**
      (This checklist called it `slam.yaml`; the real name is the upstream one.)
      Ported with `slam.launch.py`, which defaults `use_sim_time:=false`.
- [x] Launch — **not the upstream launch this checklist quotes.** Ours owns the
      params file, so a `slam_toolbox` package upgrade cannot retune the robot:

```bash
make slam                 # ros2 launch my_bot slam.launch.py
```

- [x] `/map` publishes (162×249 @ 0.05 m); `map → odom` appears in TF

> **Two startup messages that are expected — do not chase either.**
> `minimum laser range setting (0.1 m) exceeds the capabilities of the used
> Lidar (0.1 m)` is a float32/double comparison against itself; it clamps
> correctly. `Message Filter dropping message ... queue is full` on the first
> scan is the sensor registering. Both are in the symptom index.
>
> `map → odom` at **exactly identity** is normal *before you move* and a red
> flag *after*. `tf_check.py` warns either way — read it in context.

- [ ] Drive a closed loop around one room, **slowly** — the X3 Pro sweeps 360° over
      a full 100 ms, so fast rotation smears the scan

---

## GATE — do not start Day 4 until this holds

- [ ] A driven loop closes **without a visible double wall**

> **If it does not close, the fault is almost always odometry.** Go back to §1
> and re-calibrate. Do **not** tune SLAM parameters to hide an odometry error —
> you will pay for it on Day 4 and again on Day 7.

- [ ] Map saved as a reference artefact for comparison later
      (`make save-map MAP=~/maps/day3-reference`)
- [ ] The `wheel_separation` question from §1(c) settled and recorded, whichever
      way it goes

**Then update `STATE.md`.**
