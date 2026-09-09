# Decisions

Decisions that close off an option. **Do not re-litigate these** — if one turns
out wrong, supersede it with a new entry rather than quietly reversing it.

Format: what was decided, why, and what it costs.

---

## D-01 · `vision_msgs/Detection2DArray`, not `yolo_msgs`
**Date:** 7 Sep 2026 (planning) · **Status:** adopted

The design note assumes `yolo_msgs/DetectionArray` on `/yolo/tracking`. The
surviving June `semantic_objects` is already on `vision_msgs/Detection2DArray`
at `/detections`, which is apt-installable as `ros-humble-vision-msgs`.

Since we write a custom detection node anyway, use ultralytics'
`model.track(persist=True)` and put the track ID in `Detection2D.id`.

**Why:** satisfies P5 with no `yolo_msgs` build, no separate tracking node, and
no message-type change to code that already parses it. Biggest scope saving in
the week.
**Cost:** `Detection2D.id` is a string; track IDs must be stringified.

## D-02 · `ros2_control` with a custom C++ hardware interface
**Date:** 7 Sep 2026 · **Status:** adopted

Write `my_bot_hardware` implementing `hardware_interface::SystemInterface` over
the ESP32's five-letter serial protocol. ~250 lines.

**Why:** `diff_drive_controller` then supplies odometry integration, TF
publishing, `cmd_vel` timeouts and velocity limits — all the tedious-to-get-right
parts. Writing those by hand in a plain node is *more* work, not less.
**Cost:** C++ and serial debugging can eat a day.
**Fallback (pre-authorised):** if it is still fighting at end of Day 2, drop to a
plain rclpy node doing `/cmd_vel` → serial → `/odom` + TF, and log the deviation.

## D-03 · Two-track schedule
**Date:** 7 Sep 2026 · **Status:** adopted

Track A (robot): foundation → drive → odometry → SLAM → Nav2.
Track B (Jetson + camera only): `uv` env → calibration → detector.
Track B runs in the gaps from Day 2; they merge on Day 6.

**Why:** the YOLO `uv` environment is the highest-variance item and needs no
robot. Behind SLAM on the critical path, its failure surfaces on Day 5 with no
recovery room.

## D-04 · No Gazebo simulation
**Date:** 7 Sep 2026 · **Status:** adopted

The lost Makefile had a `sim` target. Not rebuilding it.

**Why:** Gazebo Classic + `gazebo_ros2_control` on Humble is a full day, buying
a fallback there is no time to use with the real robot on the bench.
**Mitigation:** keep the URDF sim-clean — real inertials, no zero masses — so a
Gazebo target stays additive rather than a rewrite.

## D-05 · No AMCL; one-session SLAM
**Date:** 7 Sep 2026 · **Status:** adopted

`slam_toolbox` provides `map → odom` throughout. `slam: True` in the Nav2
bringup; no localisation stack, no map save/load cycle in the demo.

**Why:** one less subsystem, and the demo maps and navigates in a single session
anyway.

## D-06 · P6 (Kalman fusion) cut
**Date:** 7 Sep 2026 · **Status:** cut, documented

Keep the fixed-α EMA at 0.3.

**Why:** a day and a half for better convergence and a covariance ellipse. The
EMA produces plausible landmarks.
**Limitation to report:** distant observations are over-weighted because
uncertainty grows with range; a range-seeded Kalman update with Mahalanobis
gating is the specified next step.

## D-07 · P7 (negative evidence / ghost removal) cut
**Date:** 7 Sep 2026 · **Status:** cut, documented

**Why:** two days, and it needs the occupancy ray-cast. A lingering false
positive is a much smaller demo problem than a fusion pipeline that does not run.
**Limitation to report:** landmarks age but are never disproved; a false positive
persists for the session.

## D-08 · P8 (loop-closure re-projection) cut
**Date:** 7 Sep 2026 · **Status:** cut, documented

The design note itself licenses this: *"or documented as a limitation."*

**Limitation to report:** landmarks are stored as absolute map-frame
coordinates; a loop closure moves the grid without moving the landmarks. Storing
observations as (pose, range, bearing) and re-projecting at publish time would
fix it for free.

## D-09 · P4 partial — reject, no size-prior fallback
**Date:** 7 Sep 2026 · **Status:** adopted

Implement `min_returns` and `max_spread` rejection. Do **not** implement the
per-class plane policy or size-prior fallback.

**Why:** rejection is a few lines; the fallback is most of a day.
**Limitation to report:** objects off the lidar's scan plane are rejected rather
than ranged. Reduces recall for tabletop classes in exchange for not placing
them at the range of whatever is behind them.

## D-10 · Camera extrinsics from TF, not params
**Date:** 7 Sep 2026 · **Status:** adopted

The URDF's `camera_link` joint origin is the single source. The semantic node
looks up `base_link → camera_link` at startup rather than reading
`camera.dx/dy/yaw`.

**Why:** ten lines, and it removes a whole class of drift between the URDF and
the params file. This is what the design note's WP1 asks for.

## D-11 · YOLO stack — **OPEN, decide before Day 5**
**Date raised:** 8 Sep 2026 · **Status:** open

The NVMe recovery changed the inputs to D-01. What actually ran was **`yolo_ros`
nodes publishing `yolo_msgs/DetectionArray`** on `/yolo/detections` and
`/yolo/tracking`, off **TensorRT `.engine`** models, measured at **15 Hz end to
end, camera-limited**. Not the `vision_msgs` custom node D-01 assumed.

**Option A — restore what worked.** `yolo_ros` + `yolo_msgs` + TensorRT.
*For:* measured at 15 Hz; the hard part (the venv `PYTHONPATH` trick, and why
not to use `yolo_bringup`) is fully documented in the recovered launch file.
*Against:* needs `yolo_msgs` built; needs the **lost one-line `yolo_ros` patch**
rediscovered (without it `make yolo` hangs at `Activating...`); needs the
engines re-exported because JetPack 6.1 changes the TensorRT version; needs the
venv rebuilt against 6.1 wheels.

**Option B — D-01 as written.** Custom node, `vision_msgs/Detection2DArray`,
ultralytics `model.track(persist=True)`, track ID in `Detection2D.id`.
*For:* no `yolo_msgs`, no lost patch, no separate tracking node, and the June
`semantic_objects` already parses `vision_msgs`. Can run `.pt` directly and add
TensorRT later.
*Against:* throws away a measured-working integration; `.pt` inference is slower
than the engine.

**Recommendation: B**, and it is a stronger call now than before the dump — two
of Option A's four prerequisites (the patch, the engines) are *lost or invalid*,
so "restore what worked" is not actually a restore. Keep the recovered
`yolo.launch.py` as the reference for the venv handling either way.

## D-12 · JetPack 6.1 Advantech
**Date:** 8 Sep 2026 · **Status:** adopted (user decision)

Downgraded from 6.2; the 6.2 nvidia_sdk was suspected unstable on this device.

**Why:** stability of the platform beats currency of the SDK with one week left.
**Cost, in three places:**
1. TensorRT `.engine` files are version-locked → invalid → re-export from `.pt`
   (and `compile.py` is lost, so that gets rewritten).
2. JetPack torch/torchvision wheels must match **L4T 36.4**, not 6.2's.
3. The recovered udev rules match by **USB port path**, and the Advantech
   carrier has different topology → **re-run `make udev`**, do not copy the file.

**Unaffected:** Ubuntu 22.04 either way, so **ROS 2 Humble stands**. Constraint 1
is untouched.

### Amended 9 Sep 2026 — the suspicion was narrower than this recorded

> The user corrected the premise: **the instability suspected was the NVIDIA SDK
> Manager's flashing process itself, not JetPack 6.2 as a release.** This board
> was re-flashed with NVIDIA's own recommended custom tooling instead, which is
> what actually resolved it.
>
> So "6.2 is unstable on this device" was never the finding, and **nothing here
> requires avoiding 6.2-era userspace.** The rollback stands as history, not as
> a constraint on what may be installed.

**What this changed, in practice (Day 2, Track B).** The board turned out to
have **no CUDA, cuDNN or TensorRT at all** — the L4T apt sources were commented
out, so the userspace was never reinstalled after the re-flash. Enabling
`r36.4` and choosing what to install was therefore a live decision, and the
amended premise is what freed it: see **D-15**.

Point 3 above is also now doubtful — `jetson_release` reports an **Orin NX
Engineering Reference Developer Kit**, not an Advantech carrier. The conclusion
("re-run `make udev`") was right regardless and Day 1 did re-derive the paths
from the wire, but the *reason* given for it may not be.

## D-13 · Rebuild from the ground up, using the recovered tree as reference
**Date:** 8 Sep 2026 · **Status:** adopted (user decision, reaffirmed after recovery)

The recovery does **not** change the plan to write the package fresh.

**Why it still holds:** the recovered tree is a reference with known-good
*numbers* and known-good *reasoning*, but it was built incrementally against a
board that died, on a JetPack that has since been rolled back. Typing it back in
deliberately is how the numbers get verified rather than inherited.

**What changes:** this is now cribbing from **our own Humble-era code**, not
porting Jazzy-era `articubot_one`. Constraint 2's objection does not apply to
the recovered tree — copy freely from it, but copy *knowingly*, file by file,
and re-verify anything measured.

## D-14 · §5.8's real power cycles are cut; the EN-reset evidence stands in
**Date:** 8 Sep 2026 · **Status:** adopted (user decision)

Day 1 §5.8 asks for five power cycles of the actual supply. **Cut** — the user
reports power-cycling this robot is not reliable to perform. The step is closed
on the automated evidence instead: `boot_check.py`, **50/50 clean EN resets**.

**Why it is defensible.** GPIO12 (MTDI) is latched on *chip reset*, and the
strapping pins are re-sampled on an EN reset exactly as on power-on — the ESP32
cannot tell the two apart, which is why the banner reads `reset=1` either way.
The thing §5.8 exists to catch is therefore tested, ten times over.

**Limitation to report:** an EN reset does not re-run the supply ramp. Nothing
here rules out a brown-out as the motor rail comes up, or a regulator that only
misbehaves from cold. That gap is **not closed and will not be**.

**Cost, and it is not zero.** "Power-cycling is unreliable" is itself a finding,
and it points at the same rail GPIO12 shares a pin with. An unreliable power
path does not stay confined to a bring-up checkbox — under load it looks like a
robot that randomly stops, resets or drops its encoder counts mid-run, and on
Day 3+ that presents as bad odometry or a SLAM failure rather than as an
electrical fault.

**So: first suspect.** If the board misbehaves intermittently on any later day,
check the supply before debugging software. A reset mid-run is visible for free
— the boot banner starts with `#`, and both `encoder_report.py` and
`motor_check.py` already print a warning when one goes past. Believe it.

## D-15 · JetPack userspace: targeted install, not the metapackage
**Date:** 9 Sep 2026 · **Status:** adopted

`jetson_release` reported CUDA, cuDNN and TensorRT all **Not installed**; every
line of `/etc/apt/sources.list.d/nvidia-l4t-apt-source.list` was commented out.
Re-enabled the three `r36.4` lines (backup kept alongside).

**Installed, explicitly:** `cuda-toolkit-12-6` · `libcudnn9-cuda-12` +
`libcudnn9-dev-cuda-12` · `tensorrt`. Seventy packages.

**Rejected: the `nvidia-jetpack` metapackage.** 112 packages, and it pulls
`nvidia-l4t-dla-compiler 36.4.7` — a BSP component from a newer L4T than the
36.4.0 kernel actually running — plus nsight-systems, nsight-graphics, VPI,
CUPVA and nvidia-container, none of which this project uses. The version
question it appeared to raise (candidate 6.2.1+b38, with 6.1+b123 also on
offer) turned out to be nearly moot: **the libraries we need have exactly one
version each in this repo** — CUDA 12.6.11, cuDNN 9.3.0.75, TensorRT
10.3.0.30 — so the metapackage version changes the label, not the bytes.
Pinning to 6.1+b123 also fails without hand-pinning eight sub-metapackages.

**Rejected: `nvidia-opencv`.** It co-installs cleanly (apt removes nothing),
and `checklists/day-5-yolo.md` §1 does ask for JetPack's CUDA-enabled OpenCV.
But ROS's `cv_bridge` is built against Ubuntu's **4.5.4**, and shadowing that
six days before the demo buys nothing: YOLO inference runs through torch and
TensorRT, not through OpenCV. **Documented limitation** — `cv2.cuda` stays
unavailable, and the day-5 checklist item is deliberately not met.

**Reversal cost:** low. Both rejected pieces are one `apt install` away, and
the repo lines can be re-commented.

---

## Template

```
## D-NN · <decision>
**Date:** · **Status:** adopted / cut / superseded by D-NN

<what was decided>

**Why:**
**Cost:**
**Limitation to report:**
```
