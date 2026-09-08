# STATE — where the work stands

> **Update this at the end of every session and whenever a gate passes.**
> Claude reads this first. If it is stale, Claude works from stale assumptions.

**Last updated:** 8 Sep 2026 — new board confirmed, Day 1 begun
**Current day:** Day 1 — **§2 and §4 done.** §3 deferred. §5 (firmware) next, on a re-login
**Blocked on:** two things needing the user's hands.

1. **Hardware is not plugged in.** No `/dev/ttyUSB*`, no `/dev/video*`. §4
   (udev) and §5 (firmware) cannot start until the ESP32, the lidar and the
   camera are connected.
2. **Log out and back in.** `usermod -aG dialout` has been run — `/etc/group`
   lists `dialout:x:20:mic-711` — but **the running session predates it**, so
   `id -nG` still omits `dialout` and opening either port returns
   `PermissionError: Permission denied` (verified 8 Sep). Nothing else is
   wrong; the symlinks and rules are correct. A re-login is the whole fix.

**Deferred by the user, not blocked:** §3 repos / git credentials. This board
cannot `git push` (*"could not read Username for https://github.com"* — no
credential helper, no SSH key, no `gh`) and `cap_ws` has no remote at all.
Hard constraint 4 is not being met; commits are landing locally only. Revisit
before Day 2 puts real code in `cap_ws`.

---

## Right now

**Next action:** **log out and back in**, confirm with
`id -nG | grep dialout`, then `checklists/day-1-foundation.md` §5 — firmware
validation, **robot on blocks**. §4 is done: both adapters plugged in, `make
udev` run, both symlinks correct.

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

**Notes for the next session:**

An NVMe dump recovered **the whole `my_bot` package**, the root `Makefile`,
`uv.lock` and `.bash_history` into `recoverable/mount/`. **Read
`reference/nvme-recovery-audit.md` before doing anything** — it supersedes the
"definitively gone" list, and several things written before the dump are now
wrong (`/dev/lidar` is really `/dev/ydlidar`, the camera is `cam2image` not
`usb_cam`, the checkerboard is 9×6/20 mm, Nav2 uses a `footprint` polygon).

**All odometry calibration is recovered** — see `records/calibration.md`. The
only calibration still lost is the **camera intrinsics**.

JetPack was downgraded 6.2 → **6.1 Advantech** (6.2 nvidia_sdk suspected
unstable on this device). Ubuntu 22.04 either way so Humble is unaffected, but
it invalidates the TensorRT engines and the udev port paths.

Decision still open: **D-11**, whether YOLO goes back to `yolo_ros` + engines or
to the simpler custom node. See `records/decisions.md`.

---

## Platform

| | |
|---|---|
| JetPack | **6.1, Advantech build** (downgraded from 6.2 — suspected unstable) |
| Ubuntu | 22.04 → **ROS 2 Humble unaffected** |
| Consequence | TensorRT `.engine` files invalid; udev port paths invalid; JetPack torch wheels must match L4T 36.4 |

## Gates

A day is not done until its gate passes. Do not start the next day's work on a
failed gate.

| Day | Gate | Passed |
|---|---|---|
| 1 | `e` returns changing counts by hand; `m 20 20` spins both wheels forward and auto-stops after 2 s | [ ] §2 done, §4–§5 pending hardware |
| 2 | `make teleop` drives the robot; `/odom` changes sanely; TF tree has no gaps | [ ] |
| 3 | A driven loop closes without a visible double wall | [ ] |
| 4 | RViz goal → robot arrives; recovery behaviours fire when blocked | [ ] |
| 5 | `/detections` stable; track IDs persist; no thermal throttle | [ ] |
| 6 | Labelled marker appears at roughly the right place and stays; UI shows it | [ ] |
| 7 | Three clean end-to-end rehearsals; tape-measure numbers recorded | [ ] |

## Track status

| Track | Scope | Where |
|---|---|---|
| **A** — needs the robot | foundation → drive → odometry → SLAM → Nav2 | not started |
| **B** — needs only Jetson + camera | uv env → calibration → detector | not started |

Track B runs in the gaps of Track A. Start it Day 2, not Day 5 — it is the
highest-variance item in the week and it needs no robot.

---

## Devices

Fill in as soon as §5.1 is done. These die with the board every time.

**Neither adapter has a unique serial** — confirmed from the recovered rules.
Both were matched by USB port path. The Advantech carrier has different USB
topology, so **the recovered paths will not transfer. Re-run `make udev`.**

| Symlink | Old `KERNELS` | New `KERNELS` | Confirmed |
|---|---|---|---|
| `/dev/esp32` | `1-2.1` | **`1-2.2.4`** | [x] symlink, 8 Sep → `ttyUSB0` |
| `/dev/ydlidar` | `1-2.2.4` | **`1-2.2.1`** | [x] symlink, 8 Sep → `ttyUSB1` |

Both are `10c4:ea60` CP210x with **no serial** — the predicted collision, and
the fallback to port path, both confirmed. **Sockets are now load-bearing:
label them.**

> ⚠ **`1-2.2.4` means different hardware on the two boards** — lidar then,
> ESP32 now. The recovered rules file would cross-wire them *silently*. Only
> the `make udev`-generated copy in `cap_ws/src/my_bot/udev/` is installable.

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
| camera `dx / dy / yaw` | — | ⚠ still lost |
| YOLO detection rate | 15 Hz on JP 6.2 | re-measure on 6.1 |

**Re-verify on the new board rather than trusting blind:** every recovered
number was measured on the old board with the same physical robot, so the
mechanical ones should hold. Confirm `wheel_radius` and `wheel_separation` with
one `calibrate_straight.py` / `calibrate_spin.py` run each — that is an hour,
against a day if odometry is quietly wrong.

---

## Repos pushed

| Repo | Remote created | Initial commit pushed |
|---|---|---|
| `capstone-docs` (this workspace) | [x] `mairuu/cap_ref` | [x] `18d29d8` — **includes `recoverable/`**. ⚠ `70e38c4` is ahead, unpushed: no git creds on this board |
| `semantic-bridge` | [x] tracked inside `cap_ref` | [x] — split out only if it starts changing |
| `cap_ws` | [ ] ⚠ **no remote** | local only — `~/cap_ws`, renamed from `capstone-ws` 8 Sep |
| `esp-motor-firmware` | [x] | [x] — `b0b762b` |

> ~~The recovered tree is not backed up.~~ **Resolved** — `recoverable/` is
> tracked in `cap_ref` and pushed at `18d29d8`.
>
> ⚠ **`cap_ws` has a local commit and no remote.** That breaks hard
> constraint 4. `gh` is not installed on this board. Create the remote before
> any more code goes in.

---

## Deviations from the plan

Log anything done differently from `RECOVERY.md`, and why. This becomes the
report's methodology section.

| Date | Deviation | Why |
|---|---|---|
| 8 Sep | Day-1 §2 apt block replaced by `scripts/bootstrap-ros-humble.sh` | The block predates the NVMe dump: it installed `usb_cam` (wrong — the camera is `cam2image`) and installed Nav2 fatally inline. `.bash_history` shows Nav2 apt-failing ~12× on the old board; the script isolates it so we learn on Day 1, not Day 4. See `records/issues.md`. |
| 8 Sep | Workspace named `cap_ws`, not `capstone-ws` | User's call, and it restores the old board's own name — `.bash_history` is full of `cd cap_ws/` and the recovered `Makefile` comment reads *"cap_ws is sourced after it and wins"*. All docs updated; `recoverable/` untouched. |
| 8 Sep | `cap_ws` created with only `Makefile` + `setup_udev.sh` | Day 1 needs no more than that. The rest of `my_bot` crosses over file by file on Day 2, re-verifying measured numbers as it goes (D-13). The recovered `99-my-bot-serial.rules` was **not** copied — its `KERNELS` paths are devkit-specific. |
