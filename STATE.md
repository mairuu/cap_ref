# STATE — where the work stands

> **Update this at the end of every session and whenever a gate passes.**
> Claude reads this first. If it is stale, Claude works from stale assumptions.

**Last updated:** 8 Sep 2026 — Day 1 §4 and §5 passed on the hardware
**Current day:** Day 1 — **§2, §4, §5 done except 5.8.** §3 still deferred
**Blocked on:** one hardware step and one credential problem.

1. **§5.8 — power-cycle the board five times**, confirming it boots every
   time. Watching for GPIO12, the MTDI strapping pin, which selects flash
   voltage at reset *and* is wired to `RIGHT_MOTOR_BACKWARD`. It presents as
   an intermittently dead board, not a motor fault. `serial_probe.py -v e`
   after each cycle is the whole test. **This is the last item on the Day 1
   gate.**
2. **No git credentials on this board**, unchanged. Three repos now hold
   unpushed work. See "Repos pushed" below.

~~Hardware is not plugged in~~ and ~~log out and back in~~ are both resolved:
`id -nG` lists `dialout`, both adapters enumerate, and every port opens.

**Deferred by the user, not blocked:** §3 repos / git credentials. This board
cannot `git push` (*"could not read Username for https://github.com"* — no
credential helper, no SSH key, no `gh`) and `cap_ws` has no remote at all.
Hard constraint 4 is not being met; commits are landing locally only. Revisit
before Day 2 puts real code in `cap_ws`.

---

## Right now

**Next action:** `checklists/day-1-foundation.md` **§5.8** — five power
cycles, `serial_probe.py -v e` after each. Then the Day 1 gate closes and
Day 2 starts.

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
| 1 | `e` returns changing counts by hand; `m 20 20` spins both wheels forward and auto-stops after 2 s | **[~]** §4 and §5.1–5.7 passed 8 Sep; **§5.8 (5 power cycles) is the only item left** |
| 2 | `make teleop` drives the robot; `/odom` changes sanely; TF tree has no gaps | [ ] |
| 3 | A driven loop closes without a visible double wall | [ ] |
| 4 | RViz goal → robot arrives; recovery behaviours fire when blocked | [ ] |
| 5 | `/detections` stable; track IDs persist; no thermal throttle | [ ] |
| 6 | Labelled marker appears at roughly the right place and stays; UI shows it | [ ] |
| 7 | Three clean end-to-end rehearsals; tape-measure numbers recorded | [ ] |

## Track status

| Track | Scope | Where |
|---|---|---|
| **A** — needs the robot | foundation → drive → odometry → SLAM → Nav2 | **Day 1 all but §5.8** |
| **B** — needs only Jetson + camera | uv env → calibration → detector | not started |

Track B runs in the gaps of Track A. Start it Day 2, not Day 5 — it is the
highest-variance item in the week and it needs no robot.

---

## Devices

Fill in as soon as §5.1 is done. These die with the board every time.

**Neither adapter has a unique serial** — confirmed from the recovered rules.
Both were matched by USB port path. The Advantech carrier has different USB
topology, so **the recovered paths will not transfer. Re-run `make udev`.**

> ⚠ **This table listed the two paths the wrong way round until 8 Sep** — the
> same crossing that `make udev` installed. Corrected below **from the wire**:
> the ESP32 is the adapter that answers `e`, the lidar is the one that streams.

| Symlink | Old `KERNELS` | New `KERNELS` | Confirmed |
|---|---|---|---|
| `/dev/esp32` | `1-2.1` | **`1-2.2.1`** | [x] answers `e`; survives a replug |
| `/dev/ydlidar` | `1-2.2.4` | **`1-2.2.4`** | [x] streams `0xAA55`; survives a replug |

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
| `esp-motor-firmware` | [x] | [x] — `b0b762b`. ⚠ `52cf077` ahead, **unpushed** |

> ~~The recovered tree is not backed up.~~ **Resolved** — `recoverable/` is
> tracked in `cap_ref` and pushed at `18d29d8`.
>
> ⚠ **`cap_ws` has local commits and no remote** (`c7da2b1`, `6e91aec`,
> `d056229`). That breaks hard constraint 4. `gh` is not installed on this
> board. Create the remote before any more code goes in.
>
> ⚠ **Three repos now hold unpushed work**, not one: `cap_ref` (`70e38c4`
> onward), `cap_ws` (all of it), `esp-motor-firmware` (`52cf077`). The Day 1
> checklist asks for `config.h` to be *pushed the same day* and that cannot be
> met. **Sort credentials before Day 2** — the risk compounds with every commit.

---

## Deviations from the plan

Log anything done differently from `RECOVERY.md`, and why. This becomes the
report's methodology section.

| Date | Deviation | Why |
|---|---|---|
| 8 Sep | Day-1 §2 apt block replaced by `scripts/bootstrap-ros-humble.sh` | The block predates the NVMe dump: it installed `usb_cam` (wrong — the camera is `cam2image`) and installed Nav2 fatally inline. `.bash_history` shows Nav2 apt-failing ~12× on the old board; the script isolates it so we learn on Day 1, not Day 4. See `records/issues.md`. |
| 8 Sep | Workspace named `cap_ws`, not `capstone-ws` | User's call, and it restores the old board's own name — `.bash_history` is full of `cd cap_ws/` and the recovered `Makefile` comment reads *"cap_ws is sourced after it and wins"*. All docs updated; `recoverable/` untouched. |
| 8 Sep | `cap_ws` created with only `Makefile` + `setup_udev.sh` | Day 1 needs no more than that. The rest of `my_bot` crosses over file by file on Day 2, re-verifying measured numbers as it goes (D-13). The recovered `99-my-bot-serial.rules` was **not** copied — its `KERNELS` paths are devkit-specific. |
