# Recovery Plan — Capstone Robot on Jetson Orin

**Seven days from bare board to demo.** Written 7 September 2026, after an
audit of every surviving asset.

**Committed demo target:** drive + `slam_toolbox` map + Nav2 goal navigation
+ live semantic markers.
**Stretch:** navigate-to-named-object.

---

## Contents

1. [Asset audit — what I verified](#01--asset-audit)
2. [Ground rules](#02--ground-rules)
3. [The two-track plan](#03--the-two-track-plan)
4. [Day by day](#04--day-by-day)
5. [Re-derivation procedures](#05--re-derivation-procedures)
6. [Config as text](#06--config-as-text)
7. [The Makefile](#07--the-makefile)
8. [The scripts family](#08--the-scripts-family)
9. [Cut list](#09--cut-list)
10. [Risk register](#10--risk-register)

---

## 01 · Asset audit

*Everything below was checked against the actual bytes, not from your
description of them. Where my finding contradicts a document you trust,
the discrepancy is called out.*

### `esp-motor-firmware` — trust **High for protocol, Low for tuning**

The repo is reachable and current (`b0b762b`, main). The serial protocol is
fully specified and the code implementing it is clean. But:

> **The firmware has never turned a motor.** `ROADMAP.md` step 5 is checked
> only as far as `e` and `r`. Unchecked: `o 50 50`, `m 20 20`, auto-stop, and
> *every* item in step 6 — wheel direction, encoder counts increasing,
> and encoder-sign-agrees-with-motor-sign. The last of those is called out in
> the firmware's own notes as the failure mode that runs the PID away to full
> PWM.

Also unresolved in that repo, and now on your critical path:

- **The encoder pins contradict themselves.** `ARCHITECTURE.md` says the right
  encoder is on GPIO 32/33; `config.h` — the file that actually compiles — says
  23/22. The robot survived, so the wiring is ground truth. Resolve it on
  hardware ([§5.3](#53--encoder-pins-and-sign)), then fix whichever file is wrong.
- **GPIO12 is a strapping pin** (MTDI, selects flash voltage) and is wired to
  `RIGHT_MOTOR_BACKWARD`. The repo flags this as unverified. It is a boot-
  reliability risk, not a runtime one — test it by power-cycling, not by driving.
- **The historical runaway-output bug was never exercised under motor load.**
  The rewrite removed its most likely cause (no GPIO ISRs any more), and a
  3-second quiet window was clean — but only for `e`/`r`, with the PID idle.

### Design note `camera-lidar_semantic_mapping.md` — trust **High, with one caveat**

Accurate and detailed. The caveat is the one you already flagged: findings
P1–P8 were read from the September tree, and **P1 does not exist in what you
actually have.**

### `semantic_objects` (June-era) — trust **Reference only, and it does not run**

3,271 lines across five modules and four test files. Better than "reference
only" suggests — but it has a defect that stops it at construction:

> **The node cannot start.** `_declare_parameters()` declares dotted names
> (`publish.rate_hz`, `landmark.stale_timeout`, `landmark.merge_radius`,
> `landmark.ema_alpha`, `landmark.persist_path`), but five call sites read them
> with **slashes** — `get_parameter("publish/rate_hz")` at line 118,
> `landmark/stale_timeout` at 119, and three more in the startup log line at
> 130–132. In rclpy that raises `ParameterNotDeclaredError` inside `__init__`.
> Zero slash-style declarations exist. This is a mechanical five-line fix, but
> you will hit it in the first thirty seconds and it is not in P1–P8.

Mapping the design note's findings onto what you actually have:

| Finding | In the June tree? | Note |
|---|---|---|
| **P1** azimuth gate | **No** | Introduced after June. Simply never write it. |
| **P2** TF at "latest" | **Yes** | `rclpy.time.Time()` at line 344. Real, fix it. |
| **P3** no rotation gate | Yes | Nothing subscribes to `/odom`. |
| **P4** off-plane range | Yes | `range_method: "min"`, no plane policy. |
| **P5** track IDs discarded | **Different** | See below — you are better off than the note says. |
| **P6** fixed EMA | Yes | `ema_alpha: 0.3`. |
| **P7** no negative evidence | Yes | Stale only, never deleted. |
| **P8** loop closure | Yes | Absolute `map`-frame storage. |

**P5 is not the problem the note describes.** The note assumes you are on
`yolo_msgs/DetectionArray` at `/yolo/detections` and should switch to
`/yolo/tracking`. The June tree is on **`vision_msgs/Detection2DArray` at
`/detections`** — a message type that is `apt`-installable on Humble
(`ros-humble-vision-msgs`). Since you are writing a custom YOLO node anyway,
use ultralytics' own `model.track(persist=True)` and put the track ID in
`Detection2D.id`. That satisfies P5 without building `yolo_msgs`, without
running a separate tracking node, and without changing the message type the
surviving code already parses. **This is the single biggest scope saving in
the week — take it.**

### `semantic_bridge` + `semantic_map_ui` — trust **High, higher than you rated them**

I diffed the producer against the consumer. The landmark JSON contract matches
exactly on all seven fields:

```
id · class_label · x · y · confidence · seen_count · stale
```

`ros_bridge.landmarks_to_json_str()` emits precisely what
`semantic_bridge`'s pydantic `Landmark` model consumes. **These are drop-in**,
provided the new node keeps that schema. Two obligations they impose on the
rest of the system:

- The bridge subscribes to `/camera/image_raw/compressed`, so namespace the
  camera driver to `/camera` and install `ros-humble-compressed-image-transport`.
- It calls a `clear_landmarks` service of type `std_srvs/Empty`. Provide it.

Adding fields later is safe — pydantic v2 ignores extras by default — but the
UI will silently not see them.

### Confirmed gone — nothing recoverable

I searched both prior-art trees for any `.yaml`, `.xml`, `.urdf`, `.xacro`,
`.sdf`, `launch`, or `Makefile`. **Zero hits.** No `robot_params.yaml`, no
`ydlidar.yaml`, no Makefile, no URDF. Neither prior-art directory is a git
repo, so there is no history to mine either.

One consequence worth naming: the design note's "**roughly half the X2's rays
read 0.0 indoors**" was measured from `ydlidar.yaml`, which is gone. That
number is now an unverified inheritance — [§5.5](#55--x2-dropout-rate)
re-derives it.

What *is* recoverable: `robot_params.yaml`'s complete schema, reconstructable
from `_declare_parameters()`. It is written out in [§6.4](#64--robot_paramsyaml).

---

## 02 · Ground rules

**Git before anything else.** Losing the board is why this document exists.
Four repos, each pushed empty before a line goes in:

| Repo | Contents |
|---|---|
| `cap_ws` | The `ws/` overlay: `my_bot`, `my_bot_hardware`, `semantic_objects`, `yolo_node` |
| `esp-motor-firmware` | Exists. Push the pin fix from §5.3 the day you make it. |
| `semantic-bridge` | `semantic_bridge` + `semantic_map_ui`, currently ungoverned on a USB drive |
| `capstone-docs` | This file, the design note, calibration results, demo script |

Do the third one **today**, before the Jetson work starts. That source is
currently one drive failure from being as gone as `my_bot` is.

**Copy the prior art off the drive now**, into the new repos, before you
start editing it. Read from the copy, never from the mount.

**Two things also die with the board that a git remote does not cover:**
`/etc/udev/rules.d/` and your calibration numbers. Both belong in
`cap_ws` as files that get *installed*, never edited in place. §5.1
and §5.4 produce them.

---

## 03 · The two-track plan

The highest-variance item in the week — the YOLO `uv` environment — needs
**no robot hardware**, only the Jetson. So it does not belong on the critical
path behind SLAM. Split the week:

**Track A — needs the robot.** Foundation → drive → odometry → SLAM → Nav2.
Strictly sequential; each step is meaningless until the one before it works.

**Track B — needs only the Jetson and the camera.** YOLO `uv` environment →
camera calibration → detection node. Independent of Track A until they merge
on Day 6.

Run Track B in the gaps: while apt installs, while batteries charge, while
you're waiting on anything. Its failure mode is a long dependency fight, and
you want to discover that on Day 2, not Day 5.

```
Day 1   2   3   4   5   6   7
A   ███ ███ ███ ███ ─── ─── ▓▓▓   foundation→drive→odom→SLAM→Nav2
B   ─── ▓▓▓ ▓▓▓ ▓▓▓ ███ ███ ▓▓▓   uv env→calibration→detector→fusion
                        ↑
                     merge here
```

---

## 04 · Day by day

### Day 1 — Foundation, and the truth about the firmware

*Goal at end of day: Jetson runs Humble, both USB devices have stable names,
and the ESP32 has been proven to drive wheels under closed-loop control.*

**1. Flash and verify.** JetPack 6 gives you Ubuntu 22.04, which is Humble's
native tier-1 platform — no container needed for the ROS side.

```bash
lsb_release -a          # expect 22.04
uname -r                # expect a tegra kernel
sudo nvpmodel -q        # note the power mode
sudo nvpmodel -m 0 && sudo jetson_clocks   # max clocks; you need them
```

**2. ROS 2 Humble.**

```bash
sudo apt update && sudo apt install -y software-properties-common curl
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list
sudo apt update && sudo apt install -y ros-humble-desktop ros-dev-tools
```

Then the package set for the whole week:

```bash
sudo apt install -y \
  ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-usb-cam ros-humble-camera-calibration \
  ros-humble-compressed-image-transport ros-humble-image-transport-plugins \
  ros-humble-vision-msgs ros-humble-teleop-twist-keyboard \
  ros-humble-twist-mux ros-humble-xacro ros-humble-joint-state-publisher-gui \
  ros-humble-tf2-tools ros-humble-rqt-tf-tree
```

**3. Create and push the four repos.** Empty commits first. Ten minutes.

**4. Derive the udev rules** — [§5.1](#51--udev-rules). Do this before the
firmware step; you want `/dev/esp32` to exist before you start talking to it.

**5. Finish the firmware validation.** This is the day's real work, and it is
the step most likely to surprise you. Follow [§5.2](#52--firmware-validation)
exactly — **robot on blocks**, encoder sign checked before the first `m`.

> If the encoder sign is wrong and you send `m`, the PID drives to full PWM
> and stays there. On blocks that is noise. On the ground it is a wall.

**End-of-day gate:** `screen /dev/esp32 57600` → `e` returns changing counts
when you spin a wheel by hand, and `m 20 20` spins both wheels forward,
steadily, and stops on its own after two seconds.

---

### Day 2 — `my_bot`, and driving on teleop

*Goal: keyboard teleop moves the real robot, through `ros2_control`.*

Build the package fresh, per your constraint. Layout:

```
ws/src/
  my_bot/
    urdf/          robot.urdf.xacro, wheels.xacro, sensors.xacro, ros2_control.xacro
    config/        controllers.yaml, robot_params.yaml, ydlidar.yaml,
                   slam.yaml, nav2.yaml, twist_mux.yaml, c615_640x480.yaml
    launch/        real.launch.py, teleop.launch.py, slam.launch.py,
                   nav.launch.py, yolo.launch.py, semantic.launch.py
    scripts/       (see §8)
  my_bot_hardware/ the C++ SystemInterface for the ESP32 serial protocol
```

**The one C++ decision.** `diff_drive_controller` gives you odometry
integration, TF publishing, `cmd_vel` timeouts and velocity limits for free —
all the parts that are tedious to get right. The only thing you must write is
a `hardware_interface::SystemInterface` that speaks the five-letter protocol.
That is roughly 250 lines and it is the cheaper path, not the more expensive
one. Spec in [§6.2](#62--the-hardware-interface).

Start the URDF from `base_link` and measure everything with calipers — the
lost URDF's numbers are gone and guessing them poisons odometry, SLAM and the
semantic layer at once. Get `wheel_radius` and `wheel_separation` roughly right
now; §5.4 tunes them properly tomorrow.

**Track B, in the gaps:** start the `uv` environment ([§5.6](#56--the-yolo-uv-environment)).
Expect this to be unpleasant. Discovering that today is the whole point.

**Gate:** `make teleop` drives the robot. `ros2 topic echo /odom` shows
position changing in a sane direction. `ros2 run tf2_tools view_frames` shows
`odom → base_link → …` with no gaps.

---

### Day 3 — Odometry that tells the truth, then the lidar

*Goal: a `slam_toolbox` map of one room that closes.*

**Morning — calibrate odometry.** This is where `walk_straight.py` lives, and
it is worth the hours. SLAM quality is bounded by odometry quality, and every
downstream number inherits the error. Full procedure in
[§5.4](#54--odometry-calibration). Rebuild the script rather than eyeballing it.

**Afternoon — lidar.** The X2 is not in apt; build the SDK then the driver:

```bash
git clone https://github.com/YDLIDAR/YDLidar-SDK.git && cd YDLidar-SDK
mkdir build && cd build && cmake .. && make -j$(nproc) && sudo make install
# then ydlidar_ros2_driver into ws/src, colcon build
```

The X2 is **single-channel at 115200 baud** — `isSingleChannel: true` is the
setting people miss, and getting it wrong produces a driver that connects and
publishes nothing. Config in [§6.5](#65--ydlidaryaml).

Before trusting `/scan`, run `scan_dropout_report.py` ([§8](#08--the-scripts-family))
and write the real dropout figure into your notes. The "half the rays" number
in the design note came from a file that no longer exists.

**Then SLAM:**

```bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$(ros2 pkg prefix my_bot)/share/my_bot/config/slam.yaml
```

**Gate:** drive a closed loop around a room; the map closes without a visible
double wall. If it doesn't, the fault is almost always odometry — go back to
§5.4 rather than tuning SLAM.

---

### Day 4 — Nav2

*Goal: click a goal in RViz, robot drives there and stops.*

Nav2 on a differential base with a single-plane lidar and no depth is a
well-trodden path. Use `nav2_bringup` with your own params file rather than
writing a stack. Key settings for this robot in [§6.6](#66--nav2yaml).

The thing that will cost you time is not Nav2 — it is footprint and inflation
against a lidar that drops half its returns. Start with a generous
`inflation_radius` and a `robot_radius` slightly larger than the truth.

**Track B:** camera calibration ([§5.7](#57--camera-calibration)). Do not
rush it. Every bearing in the semantic layer is downstream of `fx`.

**Gate:** `make nav` → RViz goal → robot arrives. Recovery behaviours fire
when you block it, and it does not drive into the one wall the lidar sees
worst.

---

### Day 5 — YOLO on the Jetson

*Goal: `/detections` publishing `Detection2DArray` with track IDs, at a
usable rate.*

By now the `uv` environment should be settled from the Track B work. Today is
the custom node: load an ultralytics model, run `model.track(persist=True)`,
publish `vision_msgs/Detection2DArray` on `/detections`, put the track ID in
`Detection2D.id`.

Two rate levers if the Jetson can't hold 15 Hz: drop `imgsz` to 480, and use
`yolov8n` rather than anything larger. A demo does not need `yolov8m`.

**Gate:** `ros2 topic hz /detections` is stable, IDs persist across frames for
a stationary object, and the Jetson isn't thermally throttling
(`tegrastats`).

---

### Day 6 — Fusion, and the UI

*Goal: labelled landmarks on the map, in RViz and in the browser.*

Bring the June `semantic_objects` across and fix it in this order:

1. **The slash/dot parameter bug.** Five sites. Otherwise nothing starts.
2. **P2** — pass `det_msg.header.stamp` into `lookup_transform` instead of
   `rclpy.time.Time()`. Skip the frame on failure; don't extrapolate.
3. **P3** — subscribe `/odom`, drop detections while `|ω| > 0.3 rad/s`. A dozen lines.
4. **P4, partial** — add `detection.min_returns: 3` and `detection.max_spread: 0.5`.
   Reject rather than fall back. The size-prior fallback is a Day-8 item.
5. **P5** — associate on `Detection2D.id` first, geometry only for new tracks.

Then stand up `semantic_bridge` and `semantic_map_ui`. They should need no
changes; if they do, the schema drifted and the fix belongs in the node.

**Do not attempt P6, P7 or P8 today.** They are in the cut list for good
reasons ([§9](#09--cut-list)).

**Gate:** drive past a chair; a labelled marker appears at roughly the right
place and stays there. The browser UI shows it.

---

### Day 7 — Measure, rehearse, write

*Goal: a demo you have run end-to-end three times, and honest numbers.*

**Morning — the tape-measure protocol** from the design note §08. Run it once,
properly. One chair, four passes, absolute error and spread. Even mediocre
numbers are worth far more in a report than no numbers, because they show you
knew what to measure.

**Afternoon — rehearse the demo.** Three full runs from cold boot: `make real`,
`make slam`, drive the loop, `make yolo`, `make semantic`, show the UI. Time it.
Find the step that fails when the battery is low.

**If and only if all three runs are clean:** attempt navigate-to-named-object.
It is a small action server — look up landmarks by class, take the nearest,
compute a standoff pose 0.8 m in front facing the object, send `NavigateToPose`.
Half a day if the pieces beneath it are solid, and a trap if they aren't.

**Evening — write the limitations section** while it is fresh. [§9](#09--cut-list)
is the draft.

---

## 05 · Re-derivation procedures

*Every item here died with the board and cannot be guessed. Each one is a
procedure against the real hardware.*

### 5.1 · udev rules

**The trap:** the ESP32 is on a Silicon Labs CP210x bridge (the firmware repo
records this), and the YDLidar X2 very commonly ships with a CP2102 as well.
If so, **both devices present `10c4:ea60`** and a vendor/product rule matches
whichever enumerated first — which is exactly the non-determinism the symlinks
existed to remove. Assume the collision until you have proved otherwise.

**Procedure — one device at a time.**

```bash
# Unplug both. Plug in ONLY the ESP32.
ls /dev/ttyUSB*
udevadm info -a -n /dev/ttyUSB0 | grep -E 'idVendor|idProduct|serial' | head -6
```

Record `idVendor`, `idProduct`, and `serial`. Unplug, plug in **only** the
lidar, repeat. You now have both identities and know whether they collide.

**If the serials differ** (the good case):

```udev
# /etc/udev/rules.d/99-capstone.rules
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", ATTRS{serial}=="<ESP32_SERIAL>", SYMLINK+="esp32", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", ATTRS{serial}=="<LIDAR_SERIAL>", SYMLINK+="lidar", MODE="0666"
```

**If the serials are identical or absent** (common on cheap CP2102 clones),
fall back to physical USB port paths. The device is then identified by *which
socket it is plugged into* — so label the sockets physically, because the rule
is now a promise about cabling:

```bash
udevadm info -a -n /dev/ttyUSB0 | grep -m1 KERNELS   # e.g. KERNELS=="1-2.3"
```

```udev
SUBSYSTEM=="tty", KERNELS=="1-2.3", SYMLINK+="esp32", MODE="0666"
SUBSYSTEM=="tty", KERNELS=="1-2.4", SYMLINK+="lidar", MODE="0666"
```

Install and verify:

```bash
sudo cp my_bot/udev/99-capstone.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -l /dev/esp32 /dev/lidar     # this is `make ports`
```

Keep the rules file **in the repo** and install it with `make udev`. It is the
single artefact whose loss cost you the most for its size.

### 5.2 · Firmware validation

Finish `ROADMAP.md` steps 5 and 6. **Robot on blocks throughout.**

```bash
sudo fuser -v /dev/esp32          # must be empty before uploading
screen /dev/esp32 57600           # CR line ending
```

In order, and do not skip ahead:

| # | Send | Expect | If wrong |
|---|---|---|---|
| 1 | *(power on)* | `# boot reset=1 encoders=ok` | `encoders=FAIL` → PCNT/pin problem, go to §5.3 |
| 2 | `r` | `OK` | — |
| 3 | *(spin left wheel forward by hand)* then `e` | left count **increases** | `LEFT_ENC_INVERT` in `config.h` |
| 4 | *(spin right wheel forward by hand)* then `e` | right count **increases** | `RIGHT_ENC_INVERT` |
| 5 | `o 50 50` | `OK`, both wheels turn **forward** | swap that motor's FORWARD/BACKWARD pins |
| 6 | *(wait 2 s)* | motors stop by themselves | auto-stop broken — do not proceed |
| 7 | `m 20 20` | `OK`, wheels settle at a steady speed | **see below** |
| 8 | *(power-cycle 5×)* | boots every time | GPIO12 strapping issue |

> **Step 7 is the dangerous one.** If a wheel accelerates to full speed and
> stays there, the encoder sign disagrees with the motor sign — the PID is
> reading the error as growing while it pushes. Cut power, flip that wheel's
> `*_ENC_INVERT`, reflash. Do not "try it on the ground to see."

Push the resulting `config.h` the same day.

### 5.3 · Encoder pins and sign

`ARCHITECTURE.md` says right encoder = GPIO 32/33; `config.h` says 23/22.
Only the robot knows.

`config.h` is what is flashed, so start there: if step 4 above produces
changing counts, `config.h` is right and `ARCHITECTURE.md` is stale — fix the
doc. If the right encoder reads zero while the left works, reflash with 32/33
and retest. Whichever wins, **make the two files agree and push**, so the next
person (you, in March) isn't re-deriving this.

### 5.4 · Odometry calibration

Three numbers, in this order. Each depends on the one before.

**(a) Ticks per wheel revolution.** Safe, no power to motors.

```
r                      # zero
(rotate one wheel exactly 10 full turns by hand, marking the tyre)
e                      # read counts
ticks_per_rev = counts / 10
```

Ten turns rather than one, so your marking error divides by ten. The firmware
does 4× quadrature, so expect `4 × CPR × gear_ratio`.

**(b) Effective wheel radius.** Measure the tyre with calipers, then correct
it empirically — loaded rubber rolls smaller than it measures.

```
ticks_per_metre = ticks_per_rev / (2π × r)
```

Run `walk_straight.py 3.0`, measure the actual distance with a tape, and scale:

```
r_corrected = r_measured × (distance_commanded / distance_actual)
```

Repeat once. Two iterations is plenty; a third is chasing floor variation.

**(c) Wheel separation.** Run `spin_in_place.py 10` — ten full rotations in
place, marking the start heading on the floor. If it overshoots, the true
separation is larger than configured:

```
sep_corrected = sep_measured × (angle_commanded / angle_actual)
```

Ten rotations for the same reason as ten wheel turns. Write all three into
`controllers.yaml` **and** into `capstone-docs/calibration.md` with the date,
so the next board loss costs an hour rather than a day.

### 5.5 · X2 dropout rate

The design note's "roughly half the rays" came from the lost `ydlidar.yaml`
and is currently unverified. `scan_dropout_report.py` re-derives it: subscribe
to `/scan`, count returns that are `0.0` or below `msg.range_min`, report the
fraction over 100 scans, in a normal room with the robot still.

This number sets `detection.min_returns` in the semantic layer. If dropout is
genuinely ~50%, a narrow bounding box at 3 m may be backed by two returns and
`min_returns: 3` will reject it — that is the correct trade, but you should
choose it knowingly rather than inherit it.

### 5.6 · The YOLO `uv` environment

Not a container. Take the `uv` venv definition from `mgonzs13/yolo_ros` and
fix it for the Jetson. Four fights to expect, in the order they bite:

1. **`--system-site-packages` is mandatory.** Your node needs `rclpy`, which
   is a system apt package and will not install into a sealed venv.
   `uv venv --system-site-packages`.
2. **PyPI torch is wrong for aarch64.** Installing `ultralytics` normally pulls
   a CPU-only or x86 wheel. Install NVIDIA's JetPack 6 torch/torchvision wheels
   first, then `uv pip install ultralytics --no-deps`, then add the remaining
   deps by hand.
3. **numpy 2 breaks JetPack's OpenCV.** The system `cv2` is built against
   numpy 1.x. Pin `numpy<2`.
4. **Do not let anything reinstall `opencv-python`.** Use JetPack's CUDA-enabled
   system OpenCV via system-site-packages.

Verify before writing any node:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"
python -c "import rclpy; print('rclpy ok')"
```

All three must pass in the venv. **Write down the exact working versions in
`capstone-docs/` the moment they pass** — this is the knowledge you lost last
time and the most expensive thing here to rediscover.

### 5.7 · Camera calibration

A prerequisite, not a nicety. Print a checkerboard, mount it on something
rigid and flat — a floppy printout is the usual cause of bad intrinsics.

```bash
ros2 run usb_cam usb_cam_node_exe --ros-args -r __ns:=/camera -p image_width:=640 -p image_height:=480
ros2 run camera_calibration cameracalibrator \
  --size 8x6 --square 0.025 image:=/camera/image_raw camera:=/camera
```

Move the board through the **whole frame** — especially the corners, where
distortion lives and where the bearing error you care about is largest.
Fill all four bars before clicking Calibrate.

Save the result into `my_bot/config/c615_640x480.yaml`, point `usb_cam` at it
with `camera_info_url`, and copy `fx/fy/cx/cy` into `robot_params.yaml`.

> **Delete the node's built-in defaults** (`554.0`). The design note is right
> about this: a missing params file should fail loudly, not silently map your
> room with the wrong focal length.

### 5.8 · Camera extrinsics

Measure from `base_link` to the camera's optical centre: forward `dx`, left
`dy`, height `dz`, and yaw if it is not pointing straight ahead. Put them in
the URDF as the `camera_link` joint origin.

Then have the semantic node look up `base_link → camera_link` from TF at
startup rather than reading `camera.dx/dy/yaw` from the params file. Ten lines,
and it means the URDF is the single source the design note asks for — no
chance of the two drifting.

---

## 06 · Config as text

### 6.1 · `controllers.yaml`

```yaml
controller_manager:
  ros__parameters:
    update_rate: 30                     # match the firmware's PID_RATE_HZ
    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController
    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster

diff_drive_controller:
  ros__parameters:
    left_wheel_names:  ["left_wheel_joint"]
    right_wheel_names: ["right_wheel_joint"]
    wheel_separation: 0.000             # ← §5.4(c)
    wheel_radius:     0.000             # ← §5.4(b)
    publish_rate: 30.0
    odom_frame_id: odom
    base_frame_id: base_link
    enable_odom_tf: true
    open_loop: false
    cmd_vel_timeout: 0.5                # must stay under the firmware's 2 s auto-stop
    use_stamped_vel: false
    linear.x.max_velocity:   0.4
    angular.z.max_velocity:  1.5
```

`update_rate: 30` is deliberate — the firmware's `m` command is *ticks per PID
frame* at 30 Hz, so matching the rates keeps the unit conversion honest and
keeps serial traffic well inside 57600 baud.

### 6.2 · The hardware interface

`my_bot_hardware` implements `hardware_interface::SystemInterface`. The whole
job is three methods:

**`on_init`** — read `device` (`/dev/esp32`), `baud_rate` (57600),
`ticks_per_rev`, `timeout_ms` from the URDF's `<hardware>` block. Open the port.

**`read()`** — send `e\r`, parse `<left> <right>`, convert to joint position
and velocity:

```
position_rad = ticks × 2π / ticks_per_rev
velocity_rad_s = (position - prev_position) / dt
```

**`write()`** — convert each wheel's commanded rad/s into ticks per PID frame
and send `m <l> <r>\r`:

```
ticks_per_frame = ω_rad_s × ticks_per_rev / (2π × 30.0)
```

Send it **every cycle, including zeros** — the firmware stops the motors if
2 s pass without an `o` or `m`, and `diff_drive_controller` will command zero
on `cmd_vel` timeout, which is the behaviour you want to reach the motors.

Two practical notes: give the serial read a short timeout (~50 ms) and return
`ERROR` rather than blocking the controller thread, and discard the boot
banner line (`# boot …`) on first connect.

**Fallback if this eats more than a day:** a plain rclpy node subscribing
`/cmd_vel`, publishing `/odom` + TF, doing the serial itself. You lose
`diff_drive_controller`'s odometry and limits and must write them yourself,
but it is easier to debug. Note it as a deviation and move on.

### 6.3 · `ros2_control.xacro`

```xml
<ros2_control name="RealRobot" type="system">
  <hardware>
    <plugin>my_bot_hardware/DiffDriveEsp32</plugin>
    <param name="device">/dev/esp32</param>
    <param name="baud_rate">57600</param>
    <param name="ticks_per_rev">0</param>      <!-- ← §5.4(a) -->
    <param name="timeout_ms">50</param>
    <param name="pid_rate_hz">30</param>
  </hardware>
  <joint name="left_wheel_joint">
    <command_interface name="velocity"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
  <joint name="right_wheel_joint">
    <command_interface name="velocity"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
</ros2_control>
```

### 6.4 · `robot_params.yaml`

Reconstructed from the June tree's `_declare_parameters()` — this is the
schema the surviving code actually reads. Day-6 additions marked.

```yaml
semantic_objects:
  ros__parameters:
    camera:
      fx: 0.0            # ← §5.7. No default. Fail loudly if unset.
      fy: 0.0
      cx: 0.0
      cy: 0.0
      width:  640
      height: 480
      dx:  0.0           # ← §5.8, or better: read from TF
      dy:  0.0
      yaw: 0.0
    detection:
      min_confidence: 0.5
      range_method: "min"
      angular_padding: 0.0
      max_range: 5.0
      min_range: 0.15
      min_returns: 3     # NEW — P4
      max_spread: 0.5    # NEW — P4
    motion:
      max_omega: 0.3     # NEW — P3
    landmark:
      merge_radius: 0.5
      ema_alpha: 0.3
      min_seen_to_publish: 2
      stale_timeout: 300.0
      persist_path: "/home/jetson/capstone/landmarks.json"   # was "" — set it
    publish:
      rate_hz: 2.0
    tf:
      map_frame: map
      base_frame: base_link
      camera_frame: camera_link
      lookup_timeout: 0.1
    sync:
      slop: 0.1
```

> Dots throughout. The bug you are fixing is five call sites that read these
> same names with slashes.

### 6.5 · `ydlidar.yaml`

X2-specific settings. **`isSingleChannel: true` and `baudrate: 115200` are the
two that matter** — get either wrong and the driver connects but never
publishes.

```yaml
ydlidar_ros2_driver_node:
  ros__parameters:
    port: /dev/lidar
    frame_id: laser_frame
    baudrate: 115200
    lidar_type: 1              # TYPE_TRIANGLE
    device_type: 0
    sample_rate: 3
    isSingleChannel: true      # X2 is single-channel
    intensity: false
    support_motor_dtr: true
    angle_min: -180.0
    angle_max:  180.0
    range_min: 0.12
    range_max: 8.0
    frequency: 10.0
    invert: true
    reversion: false
    auto_reconnect: true
```

Verify `angle_min`/`invert`/`reversion` against the driver's own X2 example
before trusting them — if the map comes out mirrored, this is why.

`range_min: 0.12` matters twice: it bounds the driver, and the semantic layer
filters dropouts against **the scan message's own `range_min`**, not a
hard-coded constant.

### 6.6 · `nav2.yaml`

Start from `nav2_bringup`'s default and change only these:

```yaml
# Differential base, single-plane lidar, no depth
controller_server:
  FollowPath:
    plugin: "dwb_core::DWBLocalPlanner"
    max_vel_x: 0.26
    max_vel_theta: 1.0
    min_speed_theta: -1.0
    acc_lim_x: 2.5

local_costmap:
  robot_radius: 0.00          # ← measure, then add ~20%
  inflation_layer:
    inflation_radius: 0.35
    cost_scaling_factor: 3.0
  obstacle_layer:
    scan:
      topic: /scan
      obstacle_max_range: 4.0
      raytrace_max_range: 5.0
```

Do **not** use `amcl` for the demo — you are mapping and navigating in one
session with `slam_toolbox` providing `map → odom`. Set
`slam: True` in the bringup and skip localisation entirely. One less thing.

---

## 07 · The Makefile

Reconstructed from your recollection, plus the targets the week actually needs.
Keep it at the workspace root.

```makefile
WS  := $(HOME)/cap_ws
PKG := my_bot
SRC := source /opt/ros/humble/setup.bash && source $(WS)/install/setup.bash

.PHONY: build real teleop slam nav yolo semantic bridge ui ports udev calib bag test clean

build:                      ## colcon build the workspace
	cd $(WS) && colcon build --symlink-install && echo "run: source install/setup.bash"

real:                       ## hardware bringup: control + lidar + camera
	$(SRC) && ros2 launch $(PKG) real.launch.py

teleop:                     ## keyboard teleop
	$(SRC) && ros2 run teleop_twist_keyboard teleop_twist_keyboard \
	  --ros-args -r cmd_vel:=/diff_drive_controller/cmd_vel_unstamped

slam:                       ## slam_toolbox online async
	$(SRC) && ros2 launch $(PKG) slam.launch.py

nav:                        ## Nav2 stack
	$(SRC) && ros2 launch $(PKG) nav.launch.py

yolo:                       ## detection node inside the uv venv
	$(SRC) && ros2 launch $(PKG) yolo.launch.py

semantic:                   ## camera-lidar fusion node
	$(SRC) && ros2 launch $(PKG) semantic.launch.py

bridge:                     ## FastAPI ROS<->WebSocket bridge
	cd $(HOME)/semantic-bridge/semantic_bridge && uv run uvicorn semantic_bridge.main:app --host 0.0.0.0

ui:                         ## React map UI
	cd $(HOME)/semantic-bridge/semantic_map_ui && npm run dev -- --host

ports:                      ## show the udev symlinks and what they resolve to
	@ls -l /dev/esp32 /dev/lidar 2>/dev/null || echo "symlinks missing - run 'make udev'"
	@for d in /dev/ttyUSB*; do \
	  echo "$$d -> $$(udevadm info -q property -n $$d | grep -E '^ID_SERIAL=' )"; done

udev:                       ## install the udev rules and reload
	sudo cp $(WS)/src/$(PKG)/udev/99-capstone.rules /etc/udev/rules.d/
	sudo udevadm control --reload-rules && sudo udevadm trigger
	@$(MAKE) ports

calib:                      ## camera intrinsics
	$(SRC) && ros2 run camera_calibration cameracalibrator \
	  --size 8x6 --square 0.025 image:=/camera/image_raw camera:=/camera

bag:                        ## record a demo run
	$(SRC) && ros2 bag record -o $(WS)/bags/$$(date +%F-%H%M) \
	  /scan /odom /tf /tf_static /map /detections /semantic_landmarks

test:                       ## pure-python unit tests
	cd $(WS)/src/semantic_objects && python -m pytest -q

clean:
	cd $(WS) && rm -rf build install log
```

`ports` is worth the extra lines — it prints not just whether the symlinks
exist but what serial each `ttyUSB` actually has, which is the exact
information you need when the CP210x collision from §5.1 bites.

---

## 08 · The scripts family

*Your instinct is right: every bring-up step that needs a measurement should
have a script behind it. Rebuild them as you reach the step that needs one —
they are ten to forty lines each, and the point is repeatability, not elegance.*

| Script | Purpose | Needed |
|---|---|---|
| `walk_straight.py <m>` | Drive N m straight on `/cmd_vel`, print commanded vs. encoder-integrated distance. Tune `ticks_per_metre` against a tape. | §5.4(b) — Day 3 |
| `spin_in_place.py <n>` | N full rotations in place; overshoot gives `wheel_separation`. | §5.4(c) — Day 3 |
| `encoder_report.py` | Raw `e` polling at 10 Hz, both wheels, ticks and derived rad/s. First thing to reach for when a wheel misbehaves. | §5.2 — Day 1 |
| `scan_dropout_report.py` | Fraction of `/scan` returns at 0.0 or below `range_min`, over 100 scans. Re-derives the number lost with `ydlidar.yaml`. | §5.5 — Day 3 |
| `serial_probe.py` | Send one raw command to `/dev/esp32`, print the reply. Bypasses all of ROS when you need to know whether the board or the stack is at fault. | Day 1, and every bad day after |
| `tf_check.py` | Assert `map → odom → base_link → laser_frame/camera_link` all resolve, print ages. Catches the silent TF gap that makes SLAM look broken. | Day 3 |
| `landmark_tape_measure.py` | Log a named landmark's published position on every pass; report absolute error and spread. This *is* the design note's validation protocol. | Day 7 |

`serial_probe.py` and `tf_check.py` are the two that pay for themselves fastest
— both answer "is it my code or my hardware?", which is most of the debugging
in a week like this.

---

## 09 · Cut list

*Constraint 3 says anything documentable is preferable to anything built. Here
is what to cut, and the sentence to write about each. Drafting these now means
Day 7 is rehearsal, not writing.*

**Gazebo simulation.** The lost Makefile had a `sim` target; do not rebuild it.
Gazebo Classic plus `gazebo_ros2_control` on Humble is a full day, and it buys
a fallback you will not have time to use when the real robot is on the bench.
Keep the URDF sim-clean — real inertials, no zero masses — so it stays possible
later.
> *"Simulation was descoped. The URDF carries correct inertial properties and
> a `ros2_control` tag, so a Gazebo target is additive rather than a rewrite."*

**P6 — Kalman fusion.** The EMA at `α = 0.3` is wrong in the way the design
note describes, but it produces plausible landmarks. A day and a half for
better convergence and a covariance ellipse.
> *"Position fusion uses a fixed-α EMA. Because uncertainty grows with range,
> distant observations are over-weighted; a range-seeded Kalman update with
> Mahalanobis gating is specified in the design note as the next step."*

**P7 — negative evidence.** Two days, and it needs the occupancy ray-cast.
This is the one that stings, because it is what makes a second pass clean up
the first — but a false positive that lingers is a much smaller demo problem
than a fusion pipeline that doesn't run.
> *"Landmarks age but are never disproved: a false positive persists for the
> session. Ghost removal by ray-cast against the occupancy grid is designed
> but unimplemented."*

**P8 — loop-closure re-projection.** The design note already licenses this:
*"or documented as a limitation."* Take it.
> *"Landmarks are stored as absolute map-frame coordinates. A `slam_toolbox`
> loop closure moves the grid without moving the landmarks. Storing
> observations as (pose, range, bearing) and re-projecting at publish time
> would correct this for free; it was not reached."*

**P4's size-prior fallback.** Implement rejection (`min_returns`, `max_spread`)
but not the fallback. Rejecting is a few lines; the per-class plane policy plus
size priors is most of a day.
> *"Objects off the lidar's scan plane are rejected rather than ranged by size
> prior. This reduces recall for tabletop classes — cups, laptops — in exchange
> for not placing them at the range of whatever is behind them."*

**Nav2 + AMCL relocalisation.** One session, SLAM provides `map → odom`. No
map save/load cycle in the demo.

**Multi-session persistence.** Set `persist_path` so it *works*, but do not
build the reload-and-verify path.

> A demo that does five things well and names six limitations precisely reads
> as stronger engineering than one that does eleven things unreliably. The
> limitations section is not an apology — write it as evidence you knew where
> the edges were.

---

## 10 · Risk register

*Ordered by expected cost — probability × days lost.*

| # | Risk | Signal | Mitigation |
|---|---|---|---|
| 1 | **Encoder sign wrong → PID runaway** | A wheel goes to full speed on the first `m` and stays | Robot on blocks for all of §5.2. Flip `*_ENC_INVERT`. Cheap **if** caught on blocks; a broken robot if not. |
| 2 | **YOLO `uv` env fights back** | torch imports but `cuda.is_available()` is False | Start Day 2, not Day 5 — that is the whole reason for the two-track split. Fallback: run detection at 5 Hz on CPU. Ugly, demoable. |
| 3 | **udev CP210x collision** | `/dev/esp32` sometimes points at the lidar | Assume the collision. Serial-based rules, `KERNELS` fallback, `make ports` to check. |
| 4 | **Odometry too poor for SLAM** | Map shows double walls on loop closure | Do not tune SLAM — go back to §5.4. Budget half of Day 3 for a second calibration pass. |
| 5 | **Camera calibration rushed** | Reprojection error > 0.5 px; landmarks skew to one side | Rigid board, fill all four coverage bars. Redoing it costs an hour; a bad `fx` poisons every result on Day 7. |
| 6 | **Jetson thermal throttling** | Detection rate falls over minutes | `tegrastats` during rehearsal. Active cooling. Discover it on Day 7 rehearsal, not during the demo. |
| 7 | **GPIO12 boot glitch** | Board fails to boot intermittently | Five power cycles in §5.2 step 8. If it glitches, move `RIGHT_MOTOR_BACKWARD` to a free non-strapping GPIO and reflash. |
| 8 | **Hardware interface eats Day 2** | Still fighting C++/serial at end of Day 2 | Hard stop at end of Day 2. Fall back to the rclpy node in §6.2 and document the deviation. |
| 9 | **Battery dies mid-demo** | — | Charge overnight every night from Day 1. Rehearse on a half-charged pack. |

**The single highest-leverage hour in the week** is §5.2 step 7 done carefully,
on blocks, with the encoder signs verified first. Everything downstream —
odometry, SLAM, Nav2, every semantic landmark — is built on the assumption that
the wheels do what they are told.

---

*Recovery plan · Autonomous Robot with Edge AI · 7 September 2026.
Audited against `esp-motor-firmware@b0b762b`, the June-era `semantic_objects`,
`semantic_bridge`, `semantic_map_ui`, and the 4 September design note.
Findings about the firmware's unfinished validation, the encoder pin conflict,
the parameter-name defect, and the `vision_msgs` message type were read from
those trees directly and are not in the design note.*
