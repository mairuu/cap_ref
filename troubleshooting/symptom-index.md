# Symptom index

**The 2am file.** Find the symptom, get the first thing to check.
Add to it every time something costs you more than twenty minutes.

> **Before anything else:** `make ports` · is the right thing plugged in and
> named correctly? Half of all robot bugs are a device symlink.

> **Many entries below were recovered from the old board's own notes** (8 Sep).
> They are failures that actually happened, not predictions.

---

## Hardware and serial

### A wheel accelerates to full speed and stays there
**Almost certainly the encoder sign.** The PID reads the error as growing while
it pushes. **Cut power now.** Flip that wheel's `LEFT_ENC_INVERT` /
`RIGHT_ENC_INVERT` in `config.h`, reflash, retest on blocks.
→ `checklists/day-1-foundation.md` §5.7

### `/dev/ydlidar` is the ESP32 — after copying a rules file from somewhere
You installed the **recovered** `udev/99-my-bot-serial.rules` instead of the one
`make udev` generated. `KERNELS=="1-2.2.4"` was the **lidar** on the old board
and is the **ESP32** on this one, so the old file cross-wires them *silently* —
both symlinks appear, both point at a real adapter, and the wrong one answers.
Regenerate with `make udev`. The file under `recoverable/` is never installable.
→ `records/calibration.md` "Devices"

### Reading `/dev/esp32` hangs, or floods unreadable binary
**It is the lidar on the ESP32's name.** Happened for real on 8 Sep: `make udev`
was answered with the two adapters swapped, and a port-path rule cannot tell you
it is on the wrong port. The firmware is **silent until spoken to**, so anything
arriving unprompted is not it.

Identify them without guessing — one at a time, sending nothing:

```bash
timeout 2 cat /dev/ttyUSB0 | wc -c      # thousands of bytes -> the lidar
./src/my_bot/scripts/serial_probe.py --port /dev/ttyUSB1 -v e   # "0 0" -> the ESP32
```

`encoder_report.py` and `serial_probe.py` both refuse a streaming port and say
so. Then swap the two `KERNELS` values in `src/my_bot/udev/99-my-bot-serial.rules`
(or re-run `make udev`, which now checks your answers against the wire).
→ `records/issues.md` "`/dev/esp32` and `/dev/ydlidar` were crossed"

### No boot banner when I open the port — is the board dead?
**Not necessarily, and a missing banner proves nothing.** Whether opening the
tty reboots the ESP32 depends on the DTR/RTS state the previous close left
behind (`hupcl`); clearing them in pyserial before `open()` only stops pyserial
driving the lines, not the kernel. Measured both ways in one sitting on 8 Sep:
three pyserial opens each produced a ~506-byte burst and the banner, while a
`bash` redirect after `stty -hupcl` produced nothing at all.

Ask instead of waiting: `serial_probe.py e` must answer two integers. And do not
assume encoder counts carry across two invocations of anything — hold one
connection open (`encoder_report.py`) for that.

### A wheel accelerates to full speed under `m` and stays there
**Cut power now.** That wheel's encoder sign disagrees with its motor sign, so
the PID reads the error as *growing* while it pushes and winds to full PWM. On
blocks it is noise; on the ground it is a wall.

Flip that side's `LEFT_ENC_INVERT` / `RIGHT_ENC_INVERT` in the firmware's
`config.h`, reflash, and retest from `o` before `m`. Do not "try it on the
ground to see".

**This is not hypothetical here — `RIGHT_ENC_INVERT` shipped wrong.** It was
`true` in `config.h` (commit `8b745d3`) and `true` in
`reference/firmware-protocol.md`; the robot needed `false`. Caught 8 Sep under
`o`, before the first `m`.

Check it *before* ever sending `m`, by driving rather than hand-spinning:

```bash
./src/my_bot/scripts/motor_check.py        # robot on blocks
```

`o` bypasses the PID, so this cannot run away while it measures. The script
refuses to reach `m` until both sides agree, and cuts PWM itself at 3x the
commanded rate. It cannot tell forward from backward, though — two backwards
wheels still "agree", and that fix is swapping the motor's FORWARD/BACKWARD
pins, not touching the inverts. Watch the wheels.
→ `records/issues.md` "`RIGHT_ENC_INVERT` was documented wrong"

### `/dev/esp32` sometimes points at the lidar (or vice versa)
**Neither adapter has a unique serial** — confirmed. The rules match by USB
**port path**, so a device moved to another socket loses its name.
Re-run `make udev`. → `make ports` shows what each name resolves to

### A udev symlink does not appear after `make udev`
`udevadm trigger` does not re-fire for every adapter. **Unplug and replug** that
device. If it still does not show:
```bash
udevadm test $(udevadm info -q path -n /dev/ttyUSB0)   # which rules matched
udevadm info -a -n /dev/ttyUSB0 | head -40             # matchable attributes
```

### Permission denied opening `/dev/esp32`
Rules install as `GROUP="dialout", MODE="0660"`.
`id -nG | grep dialout` — if missing, `sudo usermod -aG dialout $USER`, then log
out and back in.
> **Confirmed missing on the rebuilt board, 8 Sep** — `mic-711` is in `sudo`,
> `video`, `plugdev` and others but **not `dialout`**. Do this before `make
> udev`, not after: the symlinks appear either way, so the failure looks like a
> dead adapter rather than a permission problem. A re-login is required —
> `newgrp` does not reach processes ROS launches.

### ESP32 will not flash — pyserial disconnect error
Something holds the port. Looks like permissions; is not.
```bash
sudo fuser -v /dev/esp32
```
A `micro_ros_agent` running as root did this on the old board.

### Board boots intermittently
GPIO12 is the MTDI strapping pin and is wired to `RIGHT_MOTOR_BACKWARD`. Test
with five power cycles. If it glitches, move the signal to a free
non-strapping GPIO and reflash.

### `# boot … encoders=FAIL`
The PCNT units would not configure — a pin problem. Check the right-encoder pin
conflict: `config.h` says 23/22, `ARCHITECTURE.md` says 32/33.
→ `reference/firmware-protocol.md`

### `e` returns counts that never change
Encoder not wired to the pins the flashed firmware uses, or the encoder is not
actively driving GPIO 34/35 (input-only, no pull-ups). Spin the wheel by hand
with `encoder_report.py` running.

### Motors stop on their own after ~2 seconds
**That is correct behaviour.** `AUTO_STOP_INTERVAL_MS = 2000`. The host must
send `m` every cycle, including zeros.

### Garbage on the serial line before the boot banner
The ROM bootloader logs at 115200 regardless of our 57600. Expected. Discard
until the `# boot` line.

---

## Lidar

### `ydlidar_ros2_driver` will not build, or dies on the first parameter
**You are on the `master` branch.** Upstream's default branch is Dashing-era:
its launch files pass `node_executable=` / `node_name=` (removed in Foxy) and
its node calls the one-argument `declare_parameter(name)`, which Humble
deprecated and which throws when no override is supplied. The repo has a
**`humble` branch** — use it:

```bash
git -C ~/cap_ws/src/ydlidar_ros2_driver checkout humble
```

Built 9 Sep from `humble` at `4ef70d3`, against YDLidar-SDK `01cdda4` installed
to `/usr/local`. The SDK is a separate CMake project and is **not** an apt
package; build it first or `find_package(ydlidar_sdk)` fails.
→ `checklists/day-3-odometry-slam.md` §2

### `Fail to get baseplate device information!` and checksum errors on startup
**Normal for the X2, ignore both.** The X2 is single-channel and has no
baseplate info to report, and a checksum error or two while the motor spins up
is routine. The line that means it worked is `Lidar has started!`, followed by
`Single Fixed Size: 350`.

### `ros2 topic hz /scan` prints nothing at all
Not a dead lidar — **`ros2 topic hz` subscribes RELIABLE and `/scan` is
BEST_EFFORT**, so it never receives a message and never says why. Humble's `hz`
has no QoS flag to fix this (`--qos-*` exists on `ros2 topic echo`, not on
`hz`). Confirm the publisher is alive with `ros2 topic info /scan --verbose`,
and get the real rate from `ros2 run my_bot scan_dropout_report.py`, which
subscribes with sensor-data QoS.

### Driver connects but `/scan` never publishes
**`isSingleChannel: true`** — the X2 is single-channel. And `baudrate: 115200`.

### A node subscribes to `/scan` and receives nothing, with no error
`/scan` is **BEST_EFFORT** (sensor-data QoS). A default **RELIABLE**
subscription is QoS-incompatible and gets nothing — **silently, with no warning
on either side.** This is the single easiest ROS 2 bug to lose an afternoon to.

### The map stays almost empty and `map → odom` sits at exactly identity
**The scan is mirrored — `inverted` in `ydlidar.yaml` got flipped to false.**
It does not look mirrored: once TF places it in odom it counter-rotates at
**twice** the robot's yaw rate, so driving straight looks nearly fine and the
world spins the moment you turn. `slam_toolbox` can then never match consecutive
scans.
Confirm with `check_scan_world_fixed.py`: `~-2×` the turn means mirrored.
**Gazebo never shows this** — `gpu_lidar` is counter-clockwise natively.

### The map smears when driving forward, but turning in place looks fine
**Two causes make this exact shape, and they need opposite fixes. Check the
speed first — it is free and it is the more likely one.**

**1 · You are driving far too fast to map.** ✅ **CONFIRMED 9 Sep** — the same
floor that smeared at teleop speed mapped clean at 0.10 m/s. Check this first;
in the one case on record it was the whole answer. `make teleop` runs
`teleop_twist_keyboard`, whose `speed` parameter defaults to **0.5 m/s**
(`teleop_twist_keyboard.py:145`), and **nothing clamps it** — teleop publishes
straight at the controller, and the only velocity limits in this stack live in
`nav2_params.yaml`, which is not running when you drive by hand. Measured on the
live stack: the sweep takes **86 ms** and `header.stamp` is already **88 ms**
old on arrival, so every scan is a smear attributed to a single pose:

| speed | shear per scan |
|---|---|
| teleop default **0.5 m/s** | **8.7 cm** |
| `calibrate_straight.py` 0.10 m/s | 1.7 cm |
| Nav2 `max_vel_x` 0.055 m/s | 1.0 cm |

Rotation survives it because a pure spin smears the cloud *about the sensor
origin*, and `slam_toolbox` searches ±20° of yaw
(`coarse_search_angle_offset` 0.349) — it absorbs that into the pose and the map
stays self-consistent. Translation smears it into a **shear along the direction
of travel**, which no rigid transform can absorb, so walls double.

**2 · `reversion` got flipped to false.** ⚠ Still a real failure mode, but it
was **exonerated for the 9 Sep case** — the map came clean at 0.10 m/s with the
flag untouched, so speed alone explained it. The puck's 0° points at the robot's
back, so the whole scan is rotated by π. That error is a reflection through the
lidar centre, and the centre moves with the robot, so it breaks on
**translation**. `check_scan_world_fixed.py` **cannot catch this** — it only
tests rotation.

> The flag being `true` is not the same as the flag being *right*. It reads
> `true` in `config/ydlidar.yaml` and on the live node (confirmed 9 Sep), but
> `true` was **recovered from the old board's physical mounting** and has never
> been verified against this one.

**Separating them.** Drive the same path at 0.10 m/s and watch RViz:

```bash
ros2 run my_bot calibrate_straight.py --distance 3.0
```

- **Clean at 0.10 m/s** → it was speed. Nothing to calibrate; map at Nav2 speeds
  or slow teleop down (`x` lowers linear speed only).
- **Still smeared at 0.10 m/s** → not speed. `reversion` next, then genuine
  odometry curvature — which the same run has already measured, if you marked
  the floor as well as the distance.

**Ruling out `reversion` needs five seconds and no driving**, with the stack up:
note where the open floor in the room actually is, then compare it against the
scan. If the scan puts the open space behind the robot while the room has it in
front, the flag is inverted.

> A map built at 0.5 m/s is not evidence of anything. Discard it rather than
> reasoning from it.

### Tempted to fix a scan orientation by yawing `laser_joint`
**Don't.** `description/lidar.xacro` is shared with simulation; yawing it fixes
the real robot and breaks the sim scan. The flags in `ydlidar.yaml` are the
real-robot-only correction.

### The map comes out mirrored
`invert`, `reversion` or `angle_min` in `ydlidar.yaml`. Verify against the
driver's own X2 example.

### Half the scan is missing / lots of zero ranges
**Expected.** `invalid_range_is_inf` is `false`, so dropouts come back as `0.0`,
which is **below `range_min`**: anything that only checks for inf/nan treats
them as obstacles 0 m away. Filter against **the scan message's own
`range_min`**.

Measured 9 Sep on this board: **27.9 % of 350 rays**, not the ~50 % of 400 that
was recorded. The scan is **350 rays** — the driver says so on startup
(`Single Fixed Size: 350`) and `angle_increment` 1.032° agrees; 400 was
inherited and never counted. Re-measure with
`ros2 run my_bot scan_dropout_report.py` before treating any figure as the
sensor's.

### One side of the scan drops far more rays than the other
**Probably the room, not the lidar.** A bearing with no surface inside
`range_max` (12 m) returns `0.0` — byte-identical to a true dropout, and nothing
in the message distinguishes them. On 9 Sep the left half read 46–70 % against
the right half's 5–28 %, purely because the open floor was on that side.

Move the robot to open floor and re-run `scan_dropout_report.py`. If the
asymmetry follows the robot rather than the room, *then* suspect the hardware —
chassis clipping the beam on that side, or a dark or glazed surface.

> ✅ **Settled 10 Sep: it was the room.** Re-run from a different spot put
> +75° LEFT at 24.2 % (was 69.6 %) and +105° LEFT at 5.5 % (was 47.0 %), while
> the worst sector moved to −15° AHEAD. The deficit did not follow the robot,
> so the sensor and its mounting are cleared. The **overall** fraction held at
> 25.7 % against 27.9 % — that is the figure to quote, not any one sector.

---

## URDF and TF

### `xacro` dies with "XML parsing error: not well-formed (invalid token)"
Check the comment on the reported line for a **double hyphen**. `--` is illegal
inside an XML comment, and a prose dash is the usual culprit. None of the
recovered xacro files contain one, which is not an accident. Use a comma.

### Landmarks land 90° from where the object is
The wrong camera frame was looked up. **`camera_link`** is the mount (x-forward,
REP-103 body convention); **`camera_optical_link`** is z-forward / x-right /
y-down and is the frame image geometry is expressed in. The projection must use
the **optical** one.

Both frames exist and both resolve, so TF reports no gap and `view_frames` looks
perfect — the only symptom is a clean right-angle rotation of every bearing.
Check this before re-measuring anything. → `description/camera.xacro`, D-10

### Every landmark is offset a few cm to one side, consistently
Suspect the **sign** of `camera_offset_y` in `description/camera.xacro` before
suspecting the calibration. The magnitude was measured 9 Sep; the side was
assumed **left**. A flipped sign puts everything 6 cm out — small, constant, and
easy to mistake for slop.

### The whole launch dies and the base never comes up
If the error names `ydlidar_ros2_driver_node`, that driver is not installed —
it builds from source against the YDLidar SDK and is **not** an apt package. A
missing executable takes down every node in the launch, not just itself:

```bash
make real USE_LIDAR=false     # drive and odometry, no /scan
```

SLAM and Nav2 need it back on.

## Odometry and SLAM

### Map shows double walls when the loop closes
**Odometry, not SLAM.** Usually `wheel_separation` — a yaw error is what draws
an already-mapped wall a second time, rotated off the first. Do not tune SLAM to
hide it. → `calibrate_spin.py`

### Robot curves while odom reports a perfectly straight line
**The encoder split is wrong.** `calibrate_straight.py` steers a closed loop on
odom, so it holds the *estimated* arcs equal — if `enc_counts_per_rev_left/right`
are mis-split, that forces the wheels to physically differ and the robot arcs.
Yaw bias ≈ `2 × floor_lateral / distance` radians.
This exact failure cost 62 cm over 3 m on the old board. → `calibrate_correct.py`

### Odom distance is uniformly too long or too short, headings fine
`wheel_radius` — and note it lives in **two** files that must agree:
`config/my_controllers.yaml` (the copy `diff_cont` actually reads) and
`description/robot_core.xacro`. → `calibrate_straight.py`

### `ros2 topic echo /odom` prints nothing
Wrong topic. `diff_cont` publishes on **`/diff_cont/odom`**. `/odom` does not
exist, and its silence looks exactly like a controller that never spawned —
check `ros2 control list_controllers` before believing that.

### A 1 m hand push raises odom x by much less than 1 m
Probably not an error. The odom frame is fixed where the controller started, so
unless the robot was aligned with odom's x-axis the motion lands on **both**
axes. Check the **straight-line** distance (`odom_check.py` reports it) and
confirm yaw stayed flat through the push.

### A hand push generates yaw, or a turn walks the robot sideways
**Stop.** That is an encoder sign fault, not a calibration error, and it is the
PID runaway condition once the motors are driving.
→ `checklists/day-1-foundation.md` §5.7

### Robot drives backward overall
Flip `motors_reversed` on the ROS side. **Do not rewire.**

### Robot turns the wrong way / turns too far
`wheel_separation` is wrong. → §5.4(c), `spin_in_place.py`

### Distance travelled is consistently short or long
`wheel_radius` / `ticks_per_rev`. → §5.4(a),(b), `walk_straight.py`

### A `scripts/` tool dies with `FileNotFoundError: .../install/my_bot/lib/config/...`
**Fixed 9 Sep in `calibrate_correct.py`; check any other script that reads a
config file.** The recovered scripts resolved `config/` and `description/` from
`dirname(dirname(abspath(__file__)))`, which is right in the source tree
(`src/my_bot/scripts/`) and wrong under `ros2 run`, where the script lives at
`install/my_bot/lib/my_bot/`. They had only ever been run as
`./src/my_bot/scripts/...`. Use `realpath(__file__)` — with `--symlink-install`
the installed script is a symlink back into `src/`, which is also the copy you
must edit, since a `make build` would erase an edit to `install/`.

### TF says `map → odom` is missing
`slam_toolbox` is not running or not publishing. Run `tf_check.py` before
blaming anything downstream.

### slam_toolbox warns `minimum laser range setting (0.1 m) exceeds the capabilities of the used Lidar (0.1 m)`
**Expected, ignore it.** It compares `min_laser_range` (a double, 0.1) against
the scan message's `range_min` (a float32, which widens to 0.10000000149), so
0.1 always looks smaller than itself. It clamps to `range_min` either way and
the effective value is the one we want. Do **not** nudge the parameter to 0.12
to silence it — that throws away 2 cm of range for a cosmetic fix. Seen on the
first scan, 9 Sep, exactly as the recovered config predicted.

### `Message Filter dropping message: ... 'discarding message because the queue is full'` on startup
**Normal on the first scan or two**, while slam_toolbox is still registering the
sensor and the TF buffer has not filled. It matters only if it keeps repeating
once you are driving, which means the Jetson is not keeping up — raise
`map_update_interval` back toward upstream's 5.0.

### Nav2 plans a perfect path and the robot never moves
**`twist_mux` is not running.** `diff_cont` has `use_stamped_vel: false` so it
listens on `/diff_cont/cmd_vel_unstamped` — **not** `/cmd_vel`, which is where
Nav2 publishes. `twist_mux` is the only thing that bridges them.
```bash
ros2 topic echo /diff_cont/cmd_vel_unstamped
```

### Teleop does not override an autonomous run — the robot jerks
You used `make teleop`, which publishes **downstream** of the mux and fights
Nav2 for the same topic. **`make teleop-nav` is the e-stop** — it publishes to
`/cmd_vel_teleop`, priority 100 against Nav2's 10.

### Everything looks fine but nothing moves
```bash
ros2 control list_hardware_interfaces   # all claimed?
ros2 control list_controllers           # active?
ros2 topic echo /diff_drive_controller/cmd_vel_unstamped
```
Check `cmd_vel` is going to the topic the controller actually subscribes to.

---

## Nav2

### A recovery behaviour moves faster than the velocity_smoother should allow
It is not a bug and the smoother is not broken — **recoveries bypass it.**
`behavior_server` publishes straight onto `/cmd_vel` (five publishers, one per
behaviour plugin); only `controller_server` routes through `/cmd_vel_nav` →
`velocity_smoother` → `/cmd_vel`. So `velocity_smoother.max_velocity` never sees
a recovery.

What clamps a recovery spin is **`behavior_server.max_rotational_vel`** (0.1
rad/s here). `BackUp` and `DriveOnHeading` take their speed from the BT action
goal and are not clamped by any params file in this repo. Verified from the live
graph 10 Sep. → `config/nav2_params.yaml`

### `/cmd_vel_teleop` has two subscribers, not one
Expected. `twist_mux` is one; the other is **`behavior_server`** — it is the
input topic of the `AssistedTeleop` behaviour plugin. The e-stop still works
(twist_mux holds priority 100), but the topic is shared. Nothing in our BT
invokes `AssistedTeleop`, so it is dormant. Do not "fix" this by renaming the
teleop topic — that would break the mux config and the Makefile target together.

### Nav2 plans a perfect path and the robot does not move
`diff_cont` has `use_stamped_vel: false`, so it listens on
`/diff_cont/cmd_vel_unstamped` and **nothing in Nav2 publishes there.**
`twist_mux` is what bridges the gap, via the `cmd_vel_out` remap in
`navigation.launch.py`. If `twist_mux` is not running, Nav2 looks completely
healthy — lifecycle nodes active, a plan drawn in RViz — and the wheels never
turn. Check `ros2 topic info /diff_cont/cmd_vel_unstamped` for a publisher.

This is exactly what was wrong from the rebuild until 10 Sep: `navigation.launch.py`
had not been ported, so nothing started the mux, and because `config/twist_mux.yaml`
and the `package.xml` dependency were both already present the gap was invisible.

### `make teleop-nav` does nothing — no keypress moves the robot
**`twist_mux` is not running, and as of 9 Sep nothing in `cap_ws` can start
it.** `navigation.launch.py` is the launch file that brings it up and it has
**not been ported yet** — Day 2 brought across `controller.launch.py`,
`real_robot.launch.py`, `rsp.launch.py` and `slam.launch.py` only. The config
(`config/twist_mux.yaml`) and the `package.xml` dependency are both there, which
makes the gap easy to miss.

So `/cmd_vel_teleop` currently has **no subscriber**. `make teleop-nav`
publishes into nothing.

> ⚠ **This inverts the standing safety rule until Day 4.** `make teleop-nav` is
> the e-stop *once `make nav` is running*. With only `make real` up it is a
> no-op, and the things that actually stop the robot are:
>
> - **Ctrl-C in the terminal driving it** — `calibrate_straight.py`,
>   `calibrate_spin.py` and `motor_check.py` all publish a zero `Twist` on the
>   way out and have a `finally` that runs it.
> - **`make teleop`**, which publishes to `/diff_cont/cmd_vel_unstamped`, the
>   same topic the calibration scripts use. It fights rather than overrides, so
>   the robot stutters toward a stop rather than stopping cleanly.
> - Cutting power.
>
> Re-read this the moment `navigation.launch.py` lands: from then on
> `make teleop-nav` **is** the e-stop and `make teleop` is the dangerous one.


### Robot refuses doorways it physically fits through
Someone replaced `footprint` with `robot_radius`. A circle enclosing this robot
needs **r = 0.265** because `base_link` sits on the axle, not the centre. Use
the polygon. **If both keys are set, `footprint` wins and `robot_radius` is
silently ignored.**

### Every goal rejected as unplannable
`allow_unknown` got set back to `false`. Frontier goals sit on the boundary of
unknown space and need it `true`.

### The robot's pose jumps around
Something other than `slam_toolbox` is publishing `map → odom` — usually an
accidentally launched `amcl` or `map_server`.

### The robot jerks forward and snaps back, and the map smears behind it
**Rubber-banding. Four causes make this shape and they need different fixes.**
Do not guess between them — the measurement is one command, run *while driving*:

```bash
ros2 run my_bot check_pose_stability.py --seconds 30 --check-peer ju@172.20.10.5
```

1. **Two TF broadcasters on one edge.** The only true rubber band: the pose
   alternates between two answers frame by frame. Almost always **a second
   `make real` left running in a forgotten terminal** — nothing in `cap_ws`
   double-publishes (audited 11 Sep: no `amcl`, no `map_server`, no
   `static_transform_publisher`, no `robot_localization`; `navigation.launch.py`
   starts only `twist_mux` and `teleop_speed_guard`). Fix: kill every terminal
   and bring up exactly one stack.
2. **A scan arriving older than `transform_timeout` (0.2 s).** slam_toolbox
   discards it outright, matches on a gappy history, and corrects hard when it
   finally does match.
3. **The scan matcher fighting odometry.** The correction *oscillates* rather
   than drifts — it travels far more than it nets. That is the snap-back.
4. **Clock skew to the RViz laptop.** Since 9 Sep RViz runs on the laptop, and
   RViz resolves every transform against **its own** clock. Two clocks more than
   ~50 ms apart draw the robot and the map at different instants. **This one is
   purely a display artefact — the map on disk is fine.**

> **✅ (1), (2) and (4) were all ELIMINATED on this board, 11 Sep**, on a
> stationary robot with the full stack up. Do not re-derive them — see the
> idle-stack timing baseline in `records/calibration.md`:
> - **One** `ros2_control_node`, **one** `robot_state_publisher`, **one**
>   `slam_toolbox` process. `map → odom` at 50.1 Hz = exactly
>   `1/transform_publish_period`, `odom → base_link` at 30.0 Hz = exactly the
>   `update_rate` cap. Zero backwards stamps, zero same-stamp-different-pose.
> - `/scan` stamp age **88.4 ms median, sd 1.1 ms** — structural (it is the
>   89 ms sweep), nowhere near the 200 ms `transform_timeout`.
> - Laptop clock **10.3 ms** behind the Jetson.
>
> That leaves **(3)**, and (3) can only be measured while driving.

> ⚠ **`slam_toolbox` holds TWO `/tf` publisher endpoints, and this is normal.**
> `ros2 topic info /tf --verbose` shows two writers with different GIDs under
> the one node name, which reads exactly like a duplicate broadcaster and is
> not one: `libtoolbox_common.so` contains a single `sendTransform` reference,
> and the measured `map → odom` rate is 50 Hz, not 100. One writer is idle.
> **Endpoint count never settles this question — the per-edge rate does.**
> Likewise `diff_cont` publishes `/tf` under its **own** node name, not
> `controller_manager`'s, despite running inside `ros2_control_node`.

> **`base_link → laser_frame` has no update rate**, and looking for one is a
> false alarm. It is a fixed joint, so `robot_state_publisher` puts it on
> `/tf_static` once, latched. Only `odom → base_link`, `map → odom` and the two
> wheel joints appear on `/tf` at all.

> ⚠ **`ros2 run tf2_ros tf_monitor` cannot settle (1), and does not exist.**
> The executable is **`tf2_monitor`**. More importantly its authority column is
> useless in ROS 2: ROS 1 read the publisher from the message's connection
> header and DDS has no equivalent, so Humble hardcodes it —
> `libtf2_ros.so` contains the literal string **`Authority undetectable`**, and
> `tf2_monitor` prints `<no authority available>`. Every edge reports the same
> invented authority however many nodes publish it. Use
> `ros2 topic info /tf --verbose` (a real DDS endpoint census) or the script
> above, which also catches the doubled edge rate and the backwards stamps.

**If all four come back clean and the map still smears while the pose holds
steady, it is not a rubber band at all** — it is motion shear, see "The map
smears when driving forward" above.

### RViz on the laptop shows nothing, and `ros2 topic list` is empty there
**The DHCP addresses moved and the DDS peer list did not.** Checked 11 Sep: both
machines had left the hotspot, the Jetson was on `192.168.160.106/22` wired and
the laptop on `10.0.144.205/16` wifi, while `~/.ros2/fastdds_hotspot.xml` on
both still listed the dead `172.20.10.2` / `172.20.10.5`. **Different subnets
now**, so the multicast locator cannot cover for the stale unicast peers the way
it does on one LAN. Fix on **both** machines — see `reference/ros2-network.md`:

```bash
make net PEERS=<jetson>,<laptop>                              # Jetson
~/cap_view/setup_ros2_network.sh --peers <jetson>,<laptop>    # laptop
```

`ssh` to the laptop will also fail with `Host key verification failed` until the
new address is added; the host key itself does not change with the address, so
compare fingerprints before accepting rather than blindly `-o StrictHostKeyChecking=no`.

### Nothing happens in simulation, and no error
`SIM_TIME` was not passed to **every** layer. `use_sim_time` must match across
slam, nav and explore or TF lookups fail silently.

### Robot refuses to start moving toward a goal
Costmap footprint vs. `robot_radius` — it thinks it is already in collision.

### Clips corners / scrapes doorways
`inflation_radius`, `cost_scaling_factor`.

### Oscillates near the goal
`yaw_goal_tolerance`, `min_speed_theta`.

### Drives into a wall the lidar sees badly
Cross-check the dropout sector from Day 3. Widen inflation on that bearing or
accept it as a documented limitation.

---

## YOLO / Jetson

### `import torch` fails on `libcudss.so.0`
```
ImportError: libcudss.so.0: cannot open shared object file
```
JetPack torch links **cuDSS**, which is **not in the NVIDIA Jetson apt repo** —
`apt-cache search cudss` returns nothing, so this looks unfixable at first. It
ships in the PyPI wheel `nvidia-cudss-cu12`.

⚠ **Do not just leave that wheel installed.** It pulls `cuda-toolkit` **12.9**
and `nvidia-cublas-cu12` **12.9** onto a CUDA **12.6** system — the same trap as
the `uv.lock` hazard, one layer down. Take the `.so` files, drop the wheel:
`records/calibration.md` → "The two traps" has the exact commands.

### `numpy.core.multiarray failed to import`, and nobody installed numpy
**torch's own dependency resolution** installed **numpy 2.x** into the venv,
which shadows the system numpy 1.x that the system `cv2` is built against.
Pin **after** torch, never before:

```bash
uv pip install --python ~/yolo/venv/bin/python "numpy<2"
```

The checklist's `numpy<2` warning is usually attributed to `ultralytics`. On
this board it was torch. → `cap_ws/yolo/setup_yolo_venv.sh` step 3

### `import tensorrt` fails on `libnvdla_compiler.so`
```
ImportError: libnvdla_compiler.so: cannot open shared object file
```
TensorRT's **Python binding links the DLA compiler** even though nothing here
uses the DLA. Two steps, and the first alone is not enough:

```bash
sudo apt install nvidia-l4t-dla-compiler=36.4.0-20240912212859
sudo ldconfig          # <- the file lands in /usr/lib/aarch64-linux-gnu/nvidia/
```

Without `ldconfig` the library is on disk and still not found, which looks
exactly like the install having failed. **Pin 36.4.0** to match
`nvidia-l4t-core`; the repo default is 36.4.7, a newer BSP than the running
kernel. → D-15

### `torch.cuda.is_available()` is False and there was never a `uv sync`
Before blaming the lock file, check whether **CUDA is installed at all**:

```bash
jetson_release            # Libraries: CUDA / cuDNN / TensorRT
find /usr -name 'libnvinfer*' -o -name 'libcudnn*'
```

On this board, 9 Sep, all three read **Not installed** and both `find`s came
back empty. The cause is upstream of Python entirely: every line of
`/etc/apt/sources.list.d/nvidia-l4t-apt-source.list` is **commented out**, so
`nvidia-jetpack` is not a package apt has ever heard of and the 6.2 → 6.1
rollback never restored the userspace. Uncomment the `r36.4` lines, `apt
update`, then install the JetPack components.

This masquerades as a Python problem — every torch wheel you try "does not see
the GPU" — and no amount of reinstalling wheels fixes it. → `records/calibration.md`,
Day 2 progress

### `torch.cuda.is_available()` is False, and TensorRT vanished
**Something ran `uv sync`.** The checked-in `uv.lock` pins generic PyPI
**torch 2.13.0 / torchvision 0.28.0** and does not list `tensorrt` at all, so a
sync downgrades the JetPack aarch64 wheels (**2.11.0 / 0.26.0**) and prunes
TensorRT — leaving no CUDA and no `.engine` support.
Upstream `yolo_bringup/launch/yolo.launch.py` runs that sync **on every launch**,
which is why the workspace has its own launch file. **Never sync this venv.**

### `make yolo` hangs at `Activating...`
`yolo_ros` needs a **one-line patch** before `.engine` models load at all. That
patch lived in `cap_ws/patches/` and was **not recovered** — it will have to be
rediscovered. → decision D-11

### A `.engine` model fails to load after the JetPack change
TensorRT plans are tied to the TensorRT version they were built with. JetPack
6.2 → 6.1 invalidates them. **Re-export from the `.pt` weights.**

### `cam2image` aborts with `Could not open video stream`
Something else still holds the camera, usually a node left from a previous run.
```bash
fuser -v /dev/video0
```
The launch takes everything down when this happens, rather than leaving the YOLO
nodes up silently receiving nothing.

### YOLO nodes run but receive no images
`cam2image` publishes **RELIABLE**. The YOLO subscribers must match
(`image_reliability: 1`). A best-effort camera driver needs that flipped to 2.

### `import cv2` fails or segfaults after installing ultralytics
Something reinstalled `opencv-python`, or numpy 2 landed. JetPack's system `cv2`
is built against numpy 1.x → pin `numpy<2`, use `--system-site-packages`.

### `import rclpy` fails inside the venv
The venv was created sealed. It must be
`uv venv --system-site-packages` — `rclpy` is a system apt package.

### Detection rate falls over several minutes
Thermal throttling. `tegrastats`. Check cooling, `nvpmodel -m 0`,
`jetson_clocks`. Drop `imgsz` to 480 and use `yolov8n`.

---

## Camera and calibration

### `cameracalibrator` starts and then sits there — no window, no corners
It is waiting on a `set_camera_info` service that **`cam2image` does not
offer**. There is no error and no timeout; it looks exactly like a hung node.

```bash
ros2 run camera_calibration cameracalibrator \
  --size 9x6 --square 0.020 --no-service-check -c c615 image:=/image
```

`--no-service-check` is **required on this robot**, not cosmetic. Use
`make calib`, which passes it.

### Pressed COMMIT and nothing was saved
Same cause. COMMIT calls `set_camera_info`, which `cam2image` does not provide.
**SAVE** is the button — it writes `/tmp/calibrationdata.tar.gz`. Then
`make calib-report`.

### Calibration finished but the reprojection error is nowhere
It is computed and thrown away. `calibrator.py:797` binds `reproj_err` from
`cv2.calibrateCamera` and never stores it. **The number next to CALIBRATE is
the *linear* error**, a different measurement — not the < 0.5 px gate.

`make calib-report` recovers the real one from the saved tarball, overall and
**per image**. A run at 0.8 px is usually two bad frames, not a bad set: drop
the worst ones it lists and re-run rather than recapturing blind.

### Intrinsics look plausible, bearings in the semantic layer are all off by a few percent
Two candidates, and reprojection error catches **neither**.

- **The printed board is not 20 mm.** Verified 11 Sep: re-scoring the same
  images with `--square 0.030` instead of `0.020` changed the RMS by **zero** —
  a uniform scale error is absorbed by the board-to-camera distance. Measure ten
  squares; the span must be 200 mm. The one automatic guard is the implied HFOV
  against the C615's ~62°, which `calib-report` prints.
- **It was calibrated at 320×240.** `cam2image` **defaults** to that, and `fx`,
  `fy`, `cx`, `cy` all scale with resolution. `make camera` sets 640×480
  explicitly and `calib-report` refuses a tarball that says anything else.

### `ros2 topic hz /image/compressed` shows nothing
**The topic does not exist.** `cam2image` publishes with a plain `rclcpp`
publisher, not an `image_transport::CameraPublisher`, so the transport plugins
never attach — a live `cam2image` offers only `/image` (confirmed 11 Sep).
`compressed_image_transport` being installed changes nothing.

Republish it if the bridge needs it:

```bash
ros2 run image_transport republish raw compressed \
  --ros-args -r in:=/image -r out/compressed:=/image/compressed
```

The pre-dump advice — namespace `usb_cam` to `/camera` and read
`/camera/image_raw/compressed` — belonged to a driver this robot does not use.

### `cam2image` aborts with `Could not open video stream`
Something else still holds `/dev/video0` — usually a previous run. See the
recovered `my_bot/README.md`. `fuser -v /dev/video0` names it.

## Multi-machine / network

### Both machines ping fine, but `ros2 topic list` on one shows none of the other's topics
**The hotspot is dropping multicast.** A phone hotspot is an access point; it
forwards unicast between clients and drops client-to-client multicast. Fast DDS
discovers over `239.255.0.1` by default, so a link with 0.08 ms ping carries
**zero** discovery. Firewall, domain and `ROS_LOCALHOST_ONLY` all look guilty
and are all innocent. Fix: run the setup on **both** machines — it adds each
address as a unicast initial peer. `make net` in `~/cap_ws` on the Jetson;
`~/cap_view/setup_ros2_network.sh` on the laptop, which has no Makefile.
→ `reference/ros2-network.md`, D-16

### It worked yesterday and today neither machine sees the other
**Check the addresses first, before anything else.** The peer list in
`~/.ros2/fastdds_hotspot.xml` is literal, and the hotspot hands out DHCP. A
reconnection can move either machine. `ip -4 addr` on both, then, if either
changed, re-run on **both** with the new pair:

```bash
make net PEERS=<jetson>,<laptop>                              # Jetson
~/cap_view/setup_ros2_network.sh --peers <jetson>,<laptop>    # laptop
```

### Strange nodes in `ros2 topic list`, or `/tf` looks corrupted with the robot idle
**Someone else is on `ROS_DOMAIN_ID` 0.** We are on **42** for exactly this
reason — domain 0 is everyone's default, and a stranger's `/tf` competing with
ours reads as a broken TF tree rather than as a second robot. Confirm with
`echo $ROS_DOMAIN_ID` in the shell that actually launched the node; a systemd
unit or container will not have inherited the `.bashrc` block.

### RViz on the laptop shows the laser but the map never appears
**Not discovery — UDP fragmentation.** `/scan` is small; `/map` and Nav2's
costmaps exceed the ~64 kB datagram limit and are fragmented, and fragments are
dropped silently when the socket buffers are smaller than the burst. A
talker/listener test passes straight through this. Diagnose with the two-stream
check — small arriving while large does not is the signature:

```bash
make net-check                            # on the Jetson
~/cap_view/check_ros2_link.py --sub       # on the laptop
```

It measured **clean at 40 kB** on 9 Sep, so no tuning is installed. If Nav2's
larger costmaps do stall on Day 4, the script prints the `sysctl` and the two
`<...SocketBufferSize>` lines to add.

### Discovery works one way only
**First suspect is the laptop's `ufw`, which is active.** Traffic crosses today
only because the laptop's own outbound announcements open conntrack state.
Make it explicit, on the laptop:

```bash
sudo ufw allow from 172.20.10.0/28 comment "ROS2 hotspot subnet"
```

The Jetson has no firewall, so nothing is needed there.

### `ros2 topic echo /yolo/detections` fails on the laptop with an unknown type
Expected. `yolo_msgs` is not installed there and the laptop has no `cap_ws` —
by design, it only needs standard types. Echo it on the Jetson. The Day 6
semantic markers are `visualization_msgs/MarkerArray` and do display in the
laptop's RViz.

---

## Semantic layer

### Node dies immediately on startup
**The parameter bug.** Five call sites read dotted parameters with slashes →
`ParameterNotDeclaredError` in `__init__`. Lines 118, 119, 130, 131, 132.
→ `reference/recovered-facts.md`

### `Fused 0/n detections` — nothing ever maps
Work down the chain: is TF resolving at the detection timestamp? Are the
intrinsics real or still `554.0`? Is `min_returns` rejecting everything because
the dropout rate is worse than assumed? Is the detection topic name right?

### Landmarks appear roughly 2 m too far away
**P4** — the object is off the lidar's scan plane (a cup on a table, a bottle on
a shelf) and `range_method: "min"` returned the background wall. Expected and
documented; `min_returns` / `max_spread` should reject most of these.

### Duplicate landmarks for one object
**P2** if it happens while rotating — TF looked up at "latest" instead of the
image timestamp puts the landmark 0.30 m off at ω = 1 rad/s. Otherwise
`merge_radius` too small, or track IDs not being carried through.

### One landmark where there are two real objects
`merge_radius: 0.5` is merging them. Known limitation — the Mahalanobis gate
that would fix it is cut (D-06).

### A false positive that never goes away
Expected. **P7 is cut** — landmarks age but are never disproved. Documented
limitation.

### Landmarks and the grid disagree after a big loop
Expected. **P8 is cut** — landmarks are stored as absolute map-frame coordinates
and do not follow a loop closure. Documented limitation.

---

## Bridge and UI

### UI shows nothing / `ros_connected: false`
`ROS_DOMAIN_ID` mismatch between the bridge and the robot.

### Camera panel is blank
The compressed topic does not exist — and installing
`ros-humble-compressed-image-transport` will not create it. `cam2image` does not
use `image_transport` at all, so it has no `/compressed` companion. Run an
`image_transport republish` node; see **Camera and calibration** above. The old
advice here (namespace `usb_cam` to `/camera`) was written pre-dump for a driver
this robot does not use.

### Landmarks reach the bridge but not the browser
CORS. `cors_origins` in `semantic_bridge/config.py` defaults to
`localhost:5173` and `:3000` — add the actual host you are browsing from.

### Bridge parses no landmarks, logs a warning
The JSON schema drifted. The contract is exactly:
`id · class_label · x · y · confidence · seen_count · stale`.
**Fix belongs in the node, not the bridge.**

### `clear_landmarks` does nothing
The service (`std_srvs/Empty`) must be provided by `semantic_objects`. It is
called by the bridge, not implemented there.
