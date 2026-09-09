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
**`reversion` got flipped to false** — the puck's 0° points at the robot's back,
so the whole scan is rotated by π. That error is a reflection through the lidar
centre, and the centre moves with the robot, so it breaks on **translation**.
`check_scan_world_fixed.py` **cannot catch this** — it only tests rotation.

### Tempted to fix a scan orientation by yawing `laser_joint`
**Don't.** `description/lidar.xacro` is shared with simulation; yawing it fixes
the real robot and breaks the sim scan. The flags in `ydlidar.yaml` are the
real-robot-only correction.

### The map comes out mirrored
`invert`, `reversion` or `angle_min` in `ydlidar.yaml`. Verify against the
driver's own X2 example.

### Half the scan is missing / lots of zero ranges
**Expected — ~50% of the 400 rays, bench-measured.** `invalid_range_is_inf` is
`false`, so dropouts come back as `0.0`, which is **below `range_min`**:
anything that only checks for inf/nan treats them as obstacles 0 m away. Filter
against **the scan message's own `range_min`**.

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

### TF says `map → odom` is missing
`slam_toolbox` is not running or not publishing. Run `tf_check.py` before
blaming anything downstream.

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
`/camera/image_raw/compressed` does not exist. Namespace `usb_cam` to `/camera`
and install `ros-humble-compressed-image-transport`.

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
