# STATE — where the work stands

> **Update this at the end of every session and whenever a gate passes.**
> Claude reads this first. If it is stale, Claude works from stale assumptions.

**Last updated:** 8 Sep 2026 — new board confirmed, Day 1 begun
**Current day:** Day 1 — new Jetson confirmed (Ubuntu 22.04, L4T R36.4), ROS install in progress
**Blocked on:** three things needing the user's hands, none of them hard.

1. **Hardware is not plugged in.** No `/dev/ttyUSB*`, no `/dev/video*`. §4
   (udev) and §5 (firmware) cannot start until the ESP32, the lidar and the
   camera are connected.
2. **This board cannot push.** `git push` → *"could not read Username for
   https://github.com"*. No credential helper, no SSH key, `gh` not installed.
   Commits are landing locally only. **This is hard constraint 4 failing
   silently** — fix it before more code accumulates.
3. **sudo needs a password interactively**, so the ROS install has to be
   launched by hand: `sudo ./scripts/bootstrap-ros-humble.sh`.

---

## Right now

**Next action:** run `sudo ./scripts/bootstrap-ros-humble.sh`, then verify
`ros2 pkg list | grep nav2_bringup`. After that, plug in the ESP32 + lidar and
run `make udev` from `~/capstone-ws`.

Machine confirmed 8 Sep: Ubuntu 22.04.5, L4T R36.4.0 (= JetPack 6.1, matches),
7.4 GB RAM, 101 GB free on nvme0n1p1. **No `/opt/ros` yet.**

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
| 1 | `e` returns changing counts by hand; `m 20 20` spins both wheels forward and auto-stops after 2 s | [ ] |
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
| `/dev/esp32` | `1-2.1` | | [ ] |
| `/dev/ydlidar` | `1-2.2.4` | | [ ] |

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
| `capstone-ws` | [ ] ⚠ **no remote** | local only — `40f8d6a` at `~/capstone-ws` |
| `esp-motor-firmware` | [x] | [x] — `b0b762b` |

> ~~The recovered tree is not backed up.~~ **Resolved** — `recoverable/` is
> tracked in `cap_ref` and pushed at `18d29d8`.
>
> ⚠ **`capstone-ws` has a local commit and no remote.** That breaks hard
> constraint 4. `gh` is not installed on this board. Create the remote before
> any more code goes in.

---

## Deviations from the plan

Log anything done differently from `RECOVERY.md`, and why. This becomes the
report's methodology section.

| Date | Deviation | Why |
|---|---|---|
| 8 Sep | Day-1 §2 apt block replaced by `scripts/bootstrap-ros-humble.sh` | The block predates the NVMe dump: it installed `usb_cam` (wrong — the camera is `cam2image`) and installed Nav2 fatally inline. `.bash_history` shows Nav2 apt-failing ~12× on the old board; the script isolates it so we learn on Day 1, not Day 4. See `records/issues.md`. |
| 8 Sep | `capstone-ws` created with only `Makefile` + `setup_udev.sh` | Day 1 needs no more than that. The rest of `my_bot` crosses over file by file on Day 2, re-verifying measured numbers as it goes (D-13). The recovered `99-my-bot-serial.rules` was **not** copied — its `KERNELS` paths are devkit-specific. |
