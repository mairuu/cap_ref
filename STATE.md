# STATE — where the work stands

> **Update this at the end of every session and whenever a gate passes.**
> Claude reads this first. If it is stale, Claude works from stale assumptions.

**Last updated:** 9 Sep 2026 — Day 2 in progress
**Current day:** **Day 2.** Package ported and building; gate not yet passed
**Blocked on:** nothing. The Day 2 gate needs the robot **on blocks** and a
human at the keyboard — that is the only thing left in the day.

- ~~**`cap_ws` has no remote yet**~~ **Resolved 9 Sep.** `mairuu/cap_ws` exists,
  branch is **`main`** (not `master` as recorded earlier), and everything is
  pushed. `gh` is authenticated as `mairuu`. **Hard constraint 4 is fully met
  across all four repos for the first time.**

~~Hardware is not plugged in~~, ~~log out and back in~~, and ~~this board
cannot git push~~ are all resolved.

**§5.8's real power cycles were cut** (**D-14**) — unreliable to perform on this
robot. Closed on 50/50 clean EN resets instead, which re-latch GPIO12 exactly as
a power-on does. **The supply-ramp gap is accepted, not closed**, and it is a
reported limitation rather than a passed test — see the warning below.

---

## Right now

**Next action:** **finish the Day 2 gate.** Everything that does not need the
robot is done. Put the robot **on blocks**, then:

```bash
cd ~/cap_ws && make real USE_LIDAR=false     # terminal 1
make teleop                                   # terminal 2
```

then `ros2 control list_hardware_interfaces`, `ros2 topic echo /odom`,
`ros2 run tf2_tools view_frames`. Wheels the right way on `i` before the robot
goes on the ground.

> **Day 3's first task is not Day 3 work.** `ydlidar_ros2_driver` is **not
> installed and not an apt package** — it builds from source against the YDLidar
> SDK. Nothing on Day 2 needs it (hence `USE_LIDAR=false`), but SLAM cannot start
> without it. Budget for it before the Day 3 checklist, not during.

> ⚠ **First suspect for any later flakiness: the power path.** The user reports
> power-cycling this robot is not reliable, which is why D-14 cut §5.8's manual
> cycles — but that is itself a finding, and it points at the same rail GPIO12
> shares a pin with. An unreliable supply does not stay confined to a bring-up
> checkbox: under load it looks like a robot that randomly stops, resets, or
> drops its encoder counts mid-run, and from Day 3 that presents as bad odometry
> or a SLAM failure rather than as an electrical fault. A reset mid-run is
> visible for free — the banner starts with `#`, and both `encoder_report.py`
> and `motor_check.py` warn when one goes past. **Believe the warning.**

**§5 passed 8 Sep, robot on blocks.** The firmware drives wheels under closed
loop: `o 50 50` turns both forward, auto-stop fires at 2.0 s, and `m 20 20`
settles both sides near the commanded 600 ticks/s with no wind-up. Measured
with `cap_ws/src/my_bot/scripts/motor_check.py` (`d056229`).

> ⚠ **`RIGHT_ENC_INVERT` was `true` and `true` was wrong** — the right encoder
> counted backwards against its own motor, which is the PID runaway condition.
> `false` now, reflashed and verified. `reference/firmware-protocol.md` and
> firmware commit `8b745d3` both argued for `true`; the robot disagreed.
> Also settled: the right encoder is on **23/22**, so `ARCHITECTURE.md`'s 32/33
> was stale and has been corrected (`esp-motor-firmware` `52cf077`).

**§4 fully passed**, including the replug test that had been outstanding. The
adapters were returned in the opposite order, re-enumerated the other way round
(`ttyUSB0` ↔ `ttyUSB1` swapped their port paths), and the stable names did not
follow the numbers. The corrected rules are installed in `/etc/udev/rules.d/`.

Machine confirmed 8 Sep: Ubuntu 22.04.5, L4T R36.4.0 (= JetPack 6.1, matches),
7.4 GB RAM, 101 GB free on nvme0n1p1.

**§2 verified 8 Sep**, not just assumed. `/opt/ros/humble` present; `colcon` and
`rosdep` 0.26.0 on PATH, rosdep cache populated. All fifteen packages the
recovered launch files reference resolve: `nav2_bringup`, `nav2_map_server`,
`slam_toolbox`, `twist_mux`, `image_tools`, `camera_calibration`,
`vision_msgs`, `teleop_twist_keyboard`, `xacro`, `robot_state_publisher`,
`controller_manager`, `diff_drive_controller`, `joint_state_broadcaster`,
`rviz2`, `tf2_tools`.

> **The Nav2 apt failure did not recur.** 30 `ros-humble-nav2-*` debs installed
> cleanly from `packages.ros.org`, first try, no snapshot repo and no local
> debs. See `records/issues.md` — the entry stays as history, but the risk it
> described is retired for this build.

## Day 2, done so far (9 Sep)

**The package is across and it builds.** `my_bot` ported out of
`recoverable/mount/` per D-13: six xacro files, the 660-line ESP32 hardware
interface, configs, three launch files, both worlds. `description/` and
`hardware/` are **byte-identical** to the recovered tree (`diff -rq` clean).
`colcon build` clean first try; `xacro` processes; the plugin XML exports.

**The four duplicated numbers agree**, which is the check D-13 asks for:
`wheel_radius` 0.0327 in `robot_core.xacro` *and* `my_controllers.yaml`;
`wheel_separation` 0.25 = 2 × `wheel_offset_y` 0.125; `controller_manager`
`update_rate` 30 = `loop_rate` 30 = the firmware's `PID_RATE_HZ`.

**`camera.xacro` is new and measured** — the dump had no camera frame at all.
See Live numbers, and `records/calibration.md` for method. **The TF tree is
structurally complete**: 9 links, 8 joints, single root at `base_link`, no
orphans, `camera_link → camera_optical_link` present. Runtime confirmation
(`odom → base_link` from `diff_cont`) still needs the robot.

**Track B got much further than planned, because it found a real hole.** The
board had **no CUDA, cuDNN or TensorRT at all** — the L4T apt sources were
commented out and the re-flash never restored the userspace. Now installed and
verified: **CUDA 12.6.68 · cuDNN 9.3.0.75 · TensorRT 10.3.0.30**, `import
tensorrt` working in both system python and the venv. **D-15** records why we
took a targeted install over the `nvidia-jetpack` metapackage.

> **D-12's premise was corrected by the user (9 Sep).** What was suspected
> unstable was the **SDK Manager's flashing process**, not JetPack 6.2 as a
> release; this board was re-flashed with NVIDIA's recommended tooling. So
> nothing obliges us to avoid 6.2-era userspace, and the rollback is history
> rather than a live constraint. See the amendment on D-12.

**The recovered torch pair is confirmed, not assumed.** The audit said to check
it against the 6.1 wheel index rather than trust it:
`https://pypi.jetson-ai-lab.io/jp6/cu126/` (note **`.io`** — the `.dev` host
does not resolve) publishes exactly **torch 2.11.0** and **torchvision 0.26.0**
for cp310 aarch64 — the recovered figures are **right**.

**Track B's gate is passed.** `torch.cuda.is_available()` → **True**, device
**Orin**, verified with a real matmul on device: torch 2.11.0 · torchvision
0.26.0 · TensorRT 10.3.0 · cuDNN 9.3.0 · cv2 4.5.4 with numpy 1.26.4 · rclpy ·
ultralytics 8.4.144.

> **Two traps sat between the wheels landing and torch working**, neither in any
> prior note: `libcudss.so.0` is not an apt package at all (and its PyPI wheel
> smuggles in CUDA 12.9), and **torch's own resolver** — not ultralytics — is
> what installed numpy 2 and broke the system `cv2`. Both are written up in
> `records/calibration.md` and the symptom index.
>
> **The rebuild is `cap_ws/yolo/setup_yolo_venv.sh`, not a lock file.** Order
> and exclusions are what matter here and a freeze records neither. It refuses
> to start if cuDNN, TensorRT or libcudss are missing system-side.

**Still true and still important:**

An NVMe dump recovered **the whole `my_bot` package**, the root `Makefile`,
`uv.lock` and `.bash_history` into `recoverable/mount/`. **Read
`reference/nvme-recovery-audit.md` before doing anything** — it supersedes the
"definitively gone" list, and several things written before the dump are now
wrong (`/dev/lidar` is really `/dev/ydlidar`, the camera is `cam2image` not
`usb_cam`, the checkerboard is 9×6/20 mm, Nav2 uses a `footprint` polygon).

**All odometry calibration is recovered** — see `records/calibration.md`.
Camera **extrinsics are now measured**; the **intrinsics** are the one
calibration still genuinely lost.

Decision still open: **D-11**, whether YOLO goes back to `yolo_ros` + engines or
to the simpler custom node. See `records/decisions.md`. **TensorRT now exists,
so Option A is no longer blocked on the platform** — only on the lost one-line
patch and the re-exported engines.

---

## Platform

| | |
|---|---|
| JetPack | **6.1** (L4T 36.4.0). Re-flashed with NVIDIA's own tooling; the SDK Manager was the suspect, not 6.2 — D-12 amended |
| Board | `jetson_release` says **Orin NX Engineering Reference Developer Kit**, *not* Advantech. Stop citing "Advantech" as confirmed |
| Ubuntu | 22.04 → **ROS 2 Humble unaffected** |
| CUDA / cuDNN / TensorRT | **12.6.68 / 9.3.0.75 / 10.3.0.30** — installed 9 Sep, were absent entirely (D-15) |
| torch / torchvision | **2.11.0 / 0.26.0** cp310 aarch64, from `pypi.jetson-ai-lab.io/jp6/cu126` |
| OpenCV | 4.5.4, **no CUDA** — `nvidia-opencv` deliberately skipped (D-15). Documented limitation |
| Consequence | TensorRT `.engine` files still invalid (re-export from `.pt`); udev port paths still invalid |

## Gates

A day is not done until its gate passes. Do not start the next day's work on a
failed gate.

| Day | Gate | Passed |
|---|---|---|
| 1 | `e` returns changing counts by hand; `m 20 20` spins both wheels forward and auto-stops after 2 s | **[x] PASSED 8 Sep.** §5.8 closed on 50/50 EN resets; manual cycles cut, D-14 |
| 2 | `make teleop` drives the robot; `/odom` changes sanely; TF tree has no gaps | **[~] partial.** Package ported, built and pushed; TF tree structurally complete (9 links, no orphans); Track B well past its checkbox. **Awaiting the on-blocks teleop + `/odom` run** |
| 3 | A driven loop closes without a visible double wall | [ ] |
| 4 | RViz goal → robot arrives; recovery behaviours fire when blocked | [ ] |
| 5 | `/detections` stable; track IDs persist; no thermal throttle | [ ] |
| 6 | Labelled marker appears at roughly the right place and stays; UI shows it | [ ] |
| 7 | Three clean end-to-end rehearsals; tape-measure numbers recorded | [ ] |

## Track status

| Track | Scope | Where |
|---|---|---|
| **A** — needs the robot | foundation → drive → odometry → SLAM → Nav2 | Day 1 done. **Day 2 built and pushed; gate awaits the robot on blocks** |
| **B** — needs only Jetson + camera | uv env → calibration → detector | **`day-5-yolo.md` §1 is DONE, on Day 2.** Venv built and verified end to end; CUDA/cuDNN/TensorRT installed after finding them absent entirely. Next: camera **intrinsics** (Day 4 work, needs no robot) and **D-11** |

Track B runs in the gaps of Track A. Start it Day 2, not Day 5 — it is the
highest-variance item in the week and it needs no robot.

---

## Devices

Fill in as soon as §5.1 is done. These die with the board every time.

**Neither adapter has a unique serial** — confirmed from the recovered rules.
Both were matched by USB port path. This carrier has different USB topology, so
**the recovered paths do not transfer. Re-run `make udev`.** (The audit blamed
"the Advantech carrier"; `jetson_release` calls this an Orin NX Engineering
Reference Developer Kit. The conclusion held, the stated reason may not.)

Confirmed still present 9 Sep: `/dev/esp32 → ttyUSB0`, `/dev/ydlidar → ttyUSB1`.
Camera enumerates on `usb-3610000.usb-2.2.2` as `/dev/video0`, 640×480 MJPG and
YUYV at 30 fps.

> ⚠ **This table listed the two paths the wrong way round until 8 Sep** — the
> same crossing that `make udev` installed. Corrected below **from the wire**:
> the ESP32 is the adapter that answers `e`, the lidar is the one that streams.

| Symlink | Old `KERNELS` | **Current `KERNELS`** | Confirmed |
|---|---|---|---|
| `/dev/esp32` | `1-2.1` | **`1-2.2.3`** | [x] answers `e` → `0 0`, 8 Sep 19:12 |
| `/dev/ydlidar` | `1-2.2.4` | **`1-2.2.4`** | [x] streams `0xAA55`, 8 Sep 19:12 |

> ⚠ **The ESP32 was on `1-2.2.1` earlier the same day.** It moved socket, so
> `make udev` was re-run at 19:12 and the rules regenerated. This is the
> load-bearing-socket hazard arriving in practice, hours after being written
> down as a risk. **Treat any `KERNELS` value in this table as true only until
> a cable moves** — re-derive it, do not cite it.

**Do not read `ttyUSB` numbers as identity.** They have already swapped once:
first boot gave esp32 → `ttyUSB1`, after the replug esp32 → `ttyUSB0`. That the
names held across the swap is the proof the rules work.

Both are `10c4:ea60` CP210x with **no serial** — the predicted collision, and
the fallback to port path, both confirmed. **Sockets are now load-bearing:
label them.**

> ~~**`1-2.2.4` means different hardware on the two boards** — lidar then,
> ESP32 now.~~ **Wrong, and it was wrong because this table was crossed.**
> `1-2.2.4` is the **lidar on both boards**; only the ESP32 moved, `1-2.1` →
> `1-2.2.1`.
>
> So installing the recovered rules file would have failed *loudly*, not
> silently: `1-2.1` does not exist on this carrier, so `/dev/esp32` would simply
> never appear while `/dev/ydlidar` came up correct. The silent cross-wiring
> risk was real, but it came from **answering `make udev` with the adapters
> swapped**, which is what actually happened — not from the recovered file.
> Still install only the `make udev`-generated copy in
> `cap_ws/src/my_bot/udev/`.

Camera: **Logitech HD Webcam C615** (`046d:082c`) on `/dev/video0`, no rule
needed. Driven by `cam2image`, not `usb_cam`.

`scripts/setup_udev.sh` is recovered and does this interactively.

---

## Live numbers

Authoritative copies live in `records/calibration.md` with method and date.
This is the quick-reference mirror.

| Value | Current | Status |
|---|---|---|
| `enc_counts_per_rev_left` | **2475** | recovered |
| `enc_counts_per_rev_right` | **2470** | recovered — near-equal on purpose |
| `wheel_radius` | **0.0327** m | recovered, tape-calibrated |
| `wheel_separation` | **0.25** m | recovered, contact-patch |
| `wheel_offset_x / _y` | **0.255 / 0.125** m | recovered |
| Lidar height above ground | **0.22** m | recovered |
| `laser_frame` in `base_link` | **(−0.034, 0, 0.186)** | recovered |
| X2 dropout fraction | **~50%** of 400 rays | recovered, bench-measured |
| X2 measured rate | **~11.6 Hz** | recovered |
| `camera.fx` | — | ⚠ **still lost** |
| `camera.fy` | — | ⚠ **still lost** |
| `camera.cx` | — | ⚠ **still lost** |
| `camera.cy` | — | ⚠ **still lost** |
| camera `dx` (forward of axle) | **+0.050** m | **measured 9 Sep**, tape |
| camera `dy` (left of centre) | **+0.030** m | measured 9 Sep — ⚠ **sign assumed**, see below |
| camera `dz` (above floor) | **0.20** m | measured 9 Sep |
| camera pitch | **−0.0524** rad (3° **up**) | measured 9 Sep |
| torch / torchvision | **2.11.0 / 0.26.0** | JetPack cp310 aarch64 wheels, 9 Sep |
| CUDA / cuDNN / TensorRT | **12.6.68 / 9.3.0.75 / 10.3.0.30** | installed 9 Sep |
| YOLO detection rate | 15 Hz on JP 6.2 | re-measure on 6.1 |

> ⚠ **The camera's `dy` magnitude is measured; its side is not.** 3 cm off the
> centreline was measured, but not which side; `+0.03` in `camera.xacro` means
> **left** (REP-103). If it is actually right, every landmark lands 6 cm to one
> side — constant, small, and indistinguishable from calibration slop, which is
> precisely why it will not be caught on Day 6. **Confirm by eye, fix in
> `camera.xacro`, never downstream.**
>
> Also note the camera sits **8.4 cm in front of** and **2 cm below**
> `laser_frame`. The semantic layer takes bearing from the camera and range
> from the lidar's 0.22 m scan plane, so an object high in frame can be above
> the plane that measures it.

**Re-verify on the new board rather than trusting blind:** every recovered
number was measured on the old board with the same physical robot, so the
mechanical ones should hold. Confirm `wheel_radius` and `wheel_separation` with
one `calibrate_straight.py` / `calibrate_spin.py` run each — that is an hour,
against a day if odometry is quietly wrong.

---

## Repos pushed

| Repo | Remote created | Initial commit pushed |
|---|---|---|
| `capstone-docs` (this workspace) | [x] `mairuu/cap_ref` | [x] **`eb4e9b3`, pushed 8 Sep** — includes `recoverable/` |
| `semantic-bridge` | [x] tracked inside `cap_ref` | [x] — split out only if it starts changing |
| `cap_ws` | [x] `mairuu/cap_ws` | [x] **pushed through `3383188`, 9 Sep** — the whole `my_bot` port and `camera.xacro`. `~/cap_ws`, renamed from `capstone-ws` 8 Sep. Branch is **`main`**, matching the others (an earlier note said `master`; it is not) |
| `esp-motor-firmware` | [x] | [x] **`52cf077`, pushed 8 Sep** — the encoder fixes |

> ~~The recovered tree is not backed up.~~ **Resolved** — `recoverable/` is
> tracked in `cap_ref` and pushed at `18d29d8`.
>
> ✅ **The credentials problem is over.** `gh` is authenticated as `mairuu`,
> and the whole backlog went out on 8 Sep: `cap_ref` `18d29d8..eb4e9b3`,
> `esp-motor-firmware` `b0b762b..52cf077`. Hard constraint 4 is met again.
>
> ✅ **`cap_ws` is no longer the exception.** The remote exists and the whole
> backlog plus the Day 2 port is pushed. **All four repos are now on a remote —
> hard constraint 4 is fully met for the first time since the board died.**

---

## Deviations from the plan

Log anything done differently from `RECOVERY.md`, and why. This becomes the
report's methodology section.

| Date | Deviation | Why |
|---|---|---|
| 8 Sep | Day-1 §2 apt block replaced by `scripts/bootstrap-ros-humble.sh` | The block predates the NVMe dump: it installed `usb_cam` (wrong — the camera is `cam2image`) and installed Nav2 fatally inline. `.bash_history` shows Nav2 apt-failing ~12× on the old board; the script isolates it so we learn on Day 1, not Day 4. See `records/issues.md`. |
| 8 Sep | Workspace named `cap_ws`, not `capstone-ws` | User's call, and it restores the old board's own name — `.bash_history` is full of `cd cap_ws/` and the recovered `Makefile` comment reads *"cap_ws is sourced after it and wins"*. All docs updated; `recoverable/` untouched. |
| 9 Sep | `real_robot.launch.py` gains `use_lidar`; Makefile gains `USE_LIDAR` | `ydlidar_ros2_driver` is built from source, not apt, and is not on this board. A missing executable takes the whole launch down, base included, so Day 2 could not have brought up drive at all. Default stays `true`. |
| 9 Sep | `camera.xacro` written from tape-measure numbers, not recovered | The dump contained no camera frame; the old extrinsics lived in the lost `robot_params.yaml`. D-10 makes the URDF joint origin the single source. |
| 9 Sep | JetPack userspace installed piecemeal, not via `nvidia-jetpack` | CUDA/cuDNN/TensorRT were **absent**. The metapackage is 112 packages and forces a 36.4.7 BSP component onto a 36.4.0 kernel. **D-15.** |
| 9 Sep | `nvidia-opencv` **not** installed | `checklists/day-5-yolo.md` §1 asks for JetPack's CUDA OpenCV; `cv_bridge` is built against Ubuntu's 4.5.4 and shadowing it six days out risks the image pipeline for no gain. **`cv2.cuda` is unavailable — reported limitation.** D-15. |
| 8 Sep | `cap_ws` created with only `Makefile` + `setup_udev.sh` | Day 1 needs no more than that. The rest of `my_bot` crosses over file by file on Day 2, re-verifying measured numbers as it goes (D-13). The recovered `99-my-bot-serial.rules` was **not** copied — its `KERNELS` paths are devkit-specific. |
