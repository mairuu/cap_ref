# Scripts

> **Mostly recovered.** The NVMe dump returned `my_bot/scripts/` — and the real
> scripts are better than the specs written from memory. They are at
> `recoverable/mount/my_bot/scripts/`. The names differ from what was recalled:
> `walk_straight.py` was really **`calibrate_straight.py`**.

A family of small scripts lived under `my_bot/scripts/`, in the spirit of
**calibration and single-purpose diagnostics.**

> **Working agreement:** any bring-up step that needs a measurement gets a
> script. Do not walk through it by hand — the point is repeatability, not
> elegance. Ten to forty lines each.

Rebuild each one when you reach the step that needs it. Tick them off here.

---

## `calibrate_straight.py` — ✅ **RECOVERED** (322 lines)

Was recalled as `walk_straight.py`. Calibrates `wheel_radius`, and does more
than the spec below imagined — it runs a **cross-track closed loop** that steers
on odom, which turns it into the sharpest test of the *encoder split*:

```
odom lateral ~0, floor lateral ~0     -> encoder split is right
odom lateral ~0, floor lateral large  -> split is wrong, by about
                                         (2 x floor_lateral / distance) rad of yaw bias
```

So **measure the floor offset at the end as well as the distance.**
`--open-loop` steers nothing — better for judging raw asymmetry, worse for
measuring distance.

Sight down through the lidar puck's centre (base_link x = −0.034) to mark the
floor. **Drives the robot several metres — clear the space.**

<details><summary>Original spec, written from memory</summary>

## `walk_straight.py <metres>` — superseded

Drive N metres in a straight line, then report.

- Publish a constant `Twist` on `/cmd_vel` (via the controller's topic), ramping
  gently in and out so wheelspin does not corrupt the measurement.
- Integrate distance from `/odom`; stop at the target.
- Print **commanded** vs **odometry-integrated** distance.
- Operator measures the **actual** distance with a tape.

Feeds §5.4(b): `r_corrected = r_measured × (commanded / actual)`.
Default 3.0 m — the original used 3 m against a tape measure.

</details>

## `calibrate_spin.py --turns 10 [--cw]` — ✅ **RECOVERED** (227 lines)

Calibrates `wheel_separation`. Stops when **odom** says N full turns; the
residual physical angle is the whole measurement.

**Run it both ways.** A separation error is symmetric — CW and CCW must give the
same size of error, opposite in sign. If they differ, something asymmetric is in
play (dragging wheel, stiff caster) and fitting a separation number would only
paper over it.

## `calibrate_correct.py` — ✅ **RECOVERED** (270 lines)

No equivalent was imagined. Pure arithmetic, no ROS: reads the *current* values
out of `my_controllers.yaml` and `ros2_control.xacro` and turns floor
measurements into config changes. Separates the two independent errors:

- **scale** — both wheels wrong by the same factor → `wheel_radius`
- **asymmetry** — the two disagree → per-side radius multipliers

```
ros2 run my_bot calibrate_correct.py --distance 3.0 \
    --tape-distance 2.94 --odom-distance 3.00 --floor-lateral 0.08
```

`--floor-lateral` is signed; positive means the robot ended up **left** of the line.

## `check_scan_world_fixed.py` — ✅ **RECOVERED** (177 lines)

No equivalent was imagined, and it guards the most expensive failure in the
build. Turns ~90° and measures the best-aligning rotation of the scan in odom:

```
~0 deg          -> correct, scan is world-fixed
~ -1x the turn  -> scan rigidly follows the robot (a TF problem)
~ -2x the turn  -> scan is MIRRORED (flip `inverted` in ydlidar.yaml)
```

> It only tests **rotation**, so it cannot catch a wrong `reversion` — that one
> is a reflection through the lidar centre and shows up on **translation**, as a
> smeared map. Different test, different symptom.

## `setup_udev.sh` — ✅ **RECOVERED**

Interactive. Lists every serial device with VID:PID, serial and USB port, asks
which is which, picks `ATTRS{serial}` when available and falls back to `KERNELS`
when not, then installs and keeps a copy in the repo. **Run with both plugged
in.** This is what `make udev` calls.

---

## Still to write

<details><summary>Original spec for spin_in_place.py — superseded by calibrate_spin.py</summary>

## `spin_in_place.py <rotations>` — superseded

N full rotations in place, zero linear velocity.

- Mark the start heading on the floor before running.
- Integrate yaw from `/odom`; stop at `n × 2π`.
- Print commanded vs integrated yaw; operator reports actual overshoot.

Feeds §5.4(c): `sep_corrected = sep_measured × (commanded / actual)`.
Use 10 rotations so the marking error divides by ten.

</details>

## `encoder_report.py` — [ ] Day 1, still to write

Poll `e` at 10 Hz over `/dev/esp32` and print both wheels: raw ticks, delta,
and derived rad/s using the current `ticks_per_rev`.

The first thing to reach for when a wheel misbehaves. Works with **no ROS
running at all** — that is the point.

## `serial_probe.py <command>` — [ ] Day 1, still to write

Send one raw command to `/dev/esp32` at 57600 with a `\r` terminator, print the
reply, exit. Discard the boot banner if present.

```
./serial_probe.py e
./serial_probe.py "m 20 20"
```

Bypasses all of ROS. Answers "is it my code or my hardware?", which is most of
the debugging in a week like this. **Write this on Day 1 and you will use it
every day after.**

## `scan_dropout_report.py` — [ ] Day 3, still to write

> The figure it measures is already **recovered**: ~50% of the 400 rays read
> `0.0` indoors. Re-run it to confirm on the new board, not to discover it.

Subscribe to `/scan`, count returns that are `0.0` or below `msg.range_min`,
report the fraction over 100 scans with the robot still in a normal room.

Re-derives the number lost with `ydlidar.yaml`. Sets `detection.min_returns`.
Also print the per-sector breakdown — dropout is rarely uniform, and knowing
which bearings are blind is worth having before you blame the fusion.

## `tf_check.py` — [ ] Day 3, still to write

Assert that `map → odom → base_link → laser_frame` and
`base_link → camera_link` all resolve, and print each transform's age.

Catches the silent TF gap that makes SLAM look broken when the real fault is a
node that did not start. Run it before blaming anything else.

## `landmark_tape_measure.py <class>` — [ ] Day 7, still to write

Subscribe to `/semantic_landmarks`. On each pass, log the named class's
published position with a timestamp. At exit, report:

- **absolute error** against a tape-measured ground truth (passed as an arg)
- **spread** across passes
- duplicate landmark count for the one true object

This *is* the design note's §08 validation protocol. Absolute error tests the
geometry chain; spread tests the fusion. **They fail for different reasons —
report both.**

---

## Notes for whoever writes these

- **Read the recovered ones first.** They set the standard: each carries a long
  docstring explaining what the measurement *cannot* settle, which is the part
  that saves you.
- They are diagnostics, not products. No argparse ceremony, no config files.
- The serial ones must work with the ROS stack **stopped** — that is their value.
- Everything they measure goes into `records/calibration.md` with the date.
- Anything that commands motion takes a distance or count argument and stops
  itself. Nothing runs open-ended.
