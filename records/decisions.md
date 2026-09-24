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

## D-11 · YOLO stack — **CLOSED 14 Sep: Option B, the custom `vision_msgs` node**
**Date raised:** 8 Sep 2026 · **Status:** adopted (B), 14 Sep 2026

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

### Closed 14 Sep 2026 — B, and it cost nothing that A would have bought

Built and measured on this board the same afternoon: `my_bot/scripts/yolo_detector.py`
+ `launch/yolo.launch.py`, `yolo26n.pt` straight from torch (no engine), fp16,
imgsz 640. **15.2 Hz on `/detections`, camera-limited** — the same figure the
recovered `yolo_ros` + TensorRT stack was measured at — with inference+tracking
at **45 ms p50** inside the 66 ms frame period and the GPU clock sitting at its
**306 MHz floor** the whole time. So the engine, the lost patch and `yolo_msgs`
would have bought back nothing visible: the camera is the ceiling either way.

**What survives from A:** the venv `PYTHONPATH` trick and the "never `uv sync`"
rule, both carried into the new launch file verbatim in spirit. The recovered
`yolo.launch.py` stays in `recoverable/` as the reference for them.

**Cost:** `.pt` inference is ~2× the recovered engine's 18 ms, which matters
only if something else needs the GPU at the same time on Day 6. The escape
hatch is one line — `YOLO("yolo26n.pt").export(format="engine", imgsz=640)` on
this board — and the node already loads `.engine` files. Not done, not needed.

**Limitation to report:** the `vision_msgs` node has been measured at rate and
for latency, but the track-id persistence line of the gate needs a real object
held still in front of the camera, and the camera was facing a blank wall when
this was measured. See `records/calibration.md` for what is and is not proven.

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

## D-16 · Multi-machine ROS 2: domain 42, unicast peers, keep Fast DDS
**Date:** 9 Sep 2026 · **Status:** adopted

RViz and teleop run on the laptop (`ju@172.20.10.5`); the Jetson
(`172.20.10.2`) runs the stack. Discovery is `ROS_DOMAIN_ID=42` plus a Fast DDS
profile listing both machines as **unicast initial peers**, with the multicast
locator kept first. `make net` installs it. Full detail in
`reference/ros2-network.md`.

**Why:**
The hotspot is an access point and drops client-to-client multicast, which is
Fast DDS's default discovery mechanism — two machines that ping in 0.08 ms see
none of each other's topics, and every obvious culprit (firewall, domain,
`ROS_LOCALHOST_ONLY`) is a red herring. Unicast initial peers remove the
dependency on multicast crossing the AP. Domain **42 rather than 0** because 0
is what every other ROS 2 machine on a shared hotspot also defaults to, and the
collision presents as a corrupted `/tf`, not as a second robot.

**Rejected: switching to `rmw_cyclonedds_cpp`.** It is the commonly recommended
RMW for Nav2 on Humble, and its peer configuration is simpler. But the stack
that works today — Day 2's drive, Day 3's SLAM — runs on default
`rmw_fastrtps_cpp`, and the profile above already fixes the only thing that was
actually broken. Changing the RMW four days from the demo trades a solved
problem for an unknown set of new ones. Constraint 3.

**Rejected: a Fast DDS `interfaceWhiteList`.** Both machines advertise locators
the other cannot route to — `docker0` 172.17.0.1 on the laptop, `l4tbr0`
192.168.55.1 on the Jetson. Whitelisting the hotspot NIC would suppress that,
but it requires `useBuiltinTransports=false`, which drops shared memory and
risks the ~15-participant on-robot stack for a problem that measured as zero
loss on both streams. Additive config only.

**Cost:** the peer list is literal. Hotspot DHCP moves addresses, and nothing
detects it — `make net PEERS=...` on both machines after any reconnection.

**Limitation to report:** discovery is statically configured, so a third
machine (a second viewer, a demo-day laptop) does not just work — it must be
added to the peer list on every machine.


## D-17 · Nav2 params ported wholesale, and `footprint` keeps beating `robot_radius`

**Date:** 2026-09-10 · **Status:** adopted

`config/nav2_params.yaml` and `launch/navigation.launch.py` come across from
`recoverable/` as-is (D-13), rather than being re-derived from `nav2_bringup`'s
default and re-tuned. Only comments were edited; no value changed.

The Day 4 checklist §1 says "from the bringup default, changing only what
`RECOVERY.md` §6.6 lists", and §2 says to set `robot_radius` = measured radius
+ 20 % with `inflation_radius` 0.35. **Both are superseded.** They were written
before the NVMe dump, when we believed the Nav2 config was lost.

**Why:** the recovered file *is* the derivation the checklist asks for, already
done against this robot and annotated with the reasoning for each delta —
including several we would not have rediscovered in a week. `inflation_radius`
0.25 carries a note that upstream's 0.55 would inflate an 0.8 m doorway shut.
`sim_time` 5.0 carries the arithmetic showing that 1.5 s at our cut speed gives
an 8 cm planning horizon, shorter than the robot. `max_vel_theta` 0.125 carries
the deskew calculation tying yaw rate to map smear. Re-deriving these from the
upstream default means rediscovering them by driving into things.

On `robot_radius` specifically: `base_link` sits on the wheel axle and the
chassis hangs behind it, so the shape is strongly asymmetric (x −0.265…+0.09).
The enclosing circle needs r ≈ 0.30 against a true half-width of 0.147, and the
robot would refuse doorways it physically fits through. This is already a hard
constraint in `CLAUDE.md`; D-17 records that the Day 4 checklist contradicts it
and that the checklist loses.

**Cost:** we inherit tuning done on the old board, and its provenance is prose
in the file rather than a measurement in `records/`. The SPEEDS header was
already found stale on arrival — it quoted upstream's 0.22/1.0 as if they were
ours — which is a fair warning about the rest of the prose. Values were checked
against the live system where that was possible (topic names, frame names, all
seven lifecycle blocks present); the footprint polygon has **not** been checked
with a tape and `chassis_length` 0.295 remains unverified.

**Limitation to report:** the footprint's front edge (+0.09) is a deliberate
over-reservation beyond the derived +0.040, not a measurement. It is the safe
direction to be wrong, but it means the robot reserves ~5 cm more space in front
than it occupies, and a doorway refusal should be checked against that before
`inflation_radius` is touched.

---

## D-18 · Trust odometry: tighten the scan matcher, cap velocity in the controller

**Date:** 2026-09-11 · **Status:** adopted — **untested on a moving robot** ·
**velocity cap amended by D-26 (0.15 → 0.30 m/s); the scan-matcher half stands**

Five `slam_toolbox` scan-matcher parameters and six new `diff_cont` velocity
limits, both in `cap_ws/src/my_bot/config/`:

| Parameter | Was (upstream) | Now |
|---|---|---|
| `correlation_search_space_dimension` | 0.5 (±25 cm) | **0.3** (±15 cm) |
| `coarse_search_angle_offset` | 0.349 (±20°) | **0.175** (±10°) |
| `distance_variance_penalty` | 0.5 | **0.1** |
| `angle_variance_penalty` | 1.0 | **0.2** |
| `minimum_angle_penalty` | 0.9 | **0.8** |
| `diff_cont` `linear.x` velocity limit | none | **±0.15 m/s** |
| `diff_cont` `angular.z` velocity limit | none | **±0.5 rad/s** |

**Why:** the sequential scan matcher is the one rubber-band cause not yet
eliminated on this board (symptom index, cause 3). Reading the humble-branch
`karto_sdk/Mapper.cpp` settled how the "trust odometry" mechanism actually
works: each candidate pose's correlation score is multiplied by
`1 − 0.2·d²/p²` (floored at `minimum_distance_penalty`), `d` being the offset
from the odometry-predicted pose and `p` the configured value **squared by the
setter**; the best candidate is then applied with no response gate. At upstream
values the penalty is 0.95 at the very edge of the ±25 cm window and 0.976 at
±20° — odometry had no effective vote. Measured odometry error per 0.2 m
keyframe after the 9–10 Sep corrections is ~1 cm and ~0.01°, so the window was
25× the error budget in translation and ~100× in yaw. Along a plain wall the
correlation ridge is flat and the matcher lands anywhere on it, differently at
each keyframe — exactly the oscillation `check_pose_stability.py` looks for.
With the new values, 5 cm off odom costs 5 % of score, 10 cm costs 20 %; 5.7°
costs 5 %. The window stays 10× the error budget so wheel slip is still
recoverable. Loop closure uses a separate matcher with `doPenalize=false` and is
untouched; the gate is a loop closure and must stay one.

**Odometry covariance is a red herring and was deliberately not set.**
`slam_toolbox` never subscribes to `/diff_cont/odom`; it takes odometry from
the `odom → base_footprint` TF edge. Nav2 ignores the covariance too. It only
matters to an EKF, and there is no EKF because there is no IMU.

The velocity ceiling is about **shear**, the other smear mechanism. Nothing
capped speed during manual driving: `teleop_twist_keyboard`'s `q` raises speed
10 % per press without limit, and the 10 Sep attempt smeared on straight
sections after one such moment (4.4 cm of shear per 89 ms sweep at 0.5 m/s
against 0.9 cm at 0.10). `diff_cont` sits below `twist_mux`, both teleops and
Nav2's recoveries, so it is the one place a cap covers every path to the
wheels. Odometry is unaffected — limits apply to wheel commands; odom is
integrated from encoder positions. Nav2 never reaches the cap
(`velocity_smoother` 0.055 m/s / 0.125 rad/s, `behavior_server` 0.1 rad/s).

**Cost:** if the matcher was *not* the problem, tighter penalties can hide a
real odometry fault by making the map follow odom more faithfully — the map
would drift with odom instead of oscillating. The 9–10 Sep calibration runs
make that unlikely, and `check_pose_stability.py` still reports the net
correction, which is where such drift would show. A robot that slips more than
15 cm in one keyframe (a shove, a cable) is now beyond the search window and
will need a fresh `make slam`. The velocity cap also meant `make teleop-nav
SPEED=0.3` silently drove at 0.15 — **which is exactly the complaint that
produced D-26 on 21 Sep.** The cap is now 0.30 and `SPEED=0.3` does what it
says.

**Limitation to report:** tuned from the penalty maths and the calibration
numbers, not from a driven A/B. The next driving session is the test; if
`check_pose_stability.py` still shows the correction travelling far more than
it nets, the next step is `distance_variance_penalty: 0.05`, not a wider
window.

## D-19 · Fusion geometry: one copy of the intrinsics, and the range is the lidar's
**Date:** 14 Sep 2026 · **Status:** adopted

Three things the Day 6 checklist did not specify, decided while rebuilding
`semantic_objects`:

1. **Intrinsics are read from `my_bot/config/c615_640x480.yaml`** (a
   `camera.calibration_file` parameter set by the launch file), not copied into
   `robot_params.yaml`. The node has **no** fx/fy/cx/cy parameters and no
   defaults; a missing file is fatal.
2. **The camera's ray is intersected with the lidar's range circle.** The
   June projector placed the point at range r from the *camera*; the range is
   the *lidar's*. With the camera at (0.05, −0.03) and the lidar at (−0.034, 0)
   that was a constant ~9 cm, and the 3 cm lateral offset is 1.7° of bearing at
   1 m — more than a lidar ray. The intersection is exact for both and costs
   one square root.
3. **The camera mount frame (`camera_link`), not `camera_optical_link`, is
   what the node reads from TF**, because its 2D projector wants the mount's
   yaw; the optical frame's yaw is −90°. The node refuses a frame with |roll|
   or |pitch| over 20°. `camera.xacro`'s D-10 comment said "optical" and has
   been corrected.

**Why:** one copy of every number, and the two systematic errors were larger
than the design note's whole 0.25 m budget allows for slop.
**Cost:** a `.pt`-style single source means the launch must resolve `my_bot`'s
share directory; `ament_index` does that. The 2D model still drops z, the −3°
pitch and lens distortion (≤ 2 cm and ≤ 1.3 cm at 3 m).
**Limitation to report:** the scan window is computed at the camera's
position, not the lidar's; `angular_padding` 0.035 rad covers the difference
beyond ~1 m.

## D-20 · Bridge interface edits, Node 20 on the Jetson, UI served from the robot
**Date:** 14 Sep 2026 · **Status:** adopted (UI hosting: user decision)

The bridge's landmark **schema** matched on all seven fields and is untouched;
its **interfaces** did not match this robot: `/scan` subscribed RELIABLE
(driver is best-effort — never connects), `/map` volatile, camera topic
hard-coded to `usb_cam`'s `/camera/image_raw/compressed`, CORS localhost-only,
and `datetime.UTC` needs Python 3.11 where rclpy needs 3.10. All five fixed in
the bridge, logged as deviations.

The UI runs on the **Jetson** (`make ui`, Vite on port 3000, browsed from the
laptop) — the user's choice over running Vite on the laptop or serving a
static build. Ubuntu 22.04's `nodejs` is 12.22; **Node 20 from NodeSource** was
installed. `semantic_map_ui/.env` points the browser at the bridge on the
Jetson's address, not `localhost`. Only HTTP crosses the subnet, so the broken
DDS discovery (11 Sep) does not affect the UI.

**Cost:** a NodeSource apt source on the robot; a rebuild-free dev server that
must be running on demo day. **Reversal:** `make ui` on the laptop with the
same `.env`, or `npm run build` and serve `dist/` from the bridge.

---

## D-21 · `my_bot` owns the Nav2 behaviour tree XML
**Date:** 2026-09-15 · **Status:** adopted

`bt_navigator.default_nav_to_pose_bt_xml` now points at
`my_bot/behavior_trees/navigate_to_pose_w_replanning_and_recovery.xml`, a copy
of `nav2_bt_navigator`'s tree of the same name, byte-identical except that
`Spin` carries `time_allowance="25.0"`.

**Why:** upstream's tree hard-codes `<Spin spin_dist="1.57"/>` and leaves
`time_allowance` at its BT **port default of 10.0 s**. This robot's
`behavior_server.max_rotational_vel` is 0.1 rad/s, so 1.57 rad needs 15.7 s.
The spin recovery was mathematically incapable of succeeding — measured
15 Sep, four failures out of four, each at exactly 10.000 s. `time_allowance`
is a BT port and has **no ROS parameter**, so there was no way to fix it
without owning the file. Same reasoning that already applies to
`nav2_params.yaml` and `mapper_params_online_async.yaml`: a package upgrade
must not be able to retune the robot.

Considered and rejected: raising `max_rotational_vel` to fit 1.57 rad into
10 s (needs ≥0.157 rad/s, above DWB's `max_vel_theta` of 0.125 — a recovery
spin would become the fastest the robot ever moves, at exactly the moment the
map is most confused, and the lidar does not deskew); and shortening
`spin_dist` (hides the contradiction rather than fixing it, and the number
that is wrong is the allowance).

**Cost:** one more upstream file we now track by hand. If nav2 changes the
default tree, ours does not follow. The file carries the full arithmetic in a
comment so the next person can re-derive whether the copy is still needed.

**Depends on a launch-file detail:** the `$(find-pkg-share my_bot)/...` form in
`nav2_params.yaml` resolves only because `nav2_bringup`'s
`navigation_launch.py` wraps the params in `ParameterFile(..., allow_substs=True)`.
`bt_navigator` reads the parameter as a plain string. Verified 15 Sep by
evaluating the real `RewrittenYaml` → `ParameterFile` chain. A future launch
path without `allow_substs=True` breaks configuration outright.

**Limitation to report:** ~~none. The recovery behaves as upstream intends; only
the timeout was wrong for this robot's speed.~~

✅ **CONFIRMED 16 Sep — executed at last, and it passes on both counts.**
`SUCCEEDED in 16.400653 s`, rotating 1.5762 rad against the 1.57 target.

1. **The `time_allowance="25.0"` override works.** Aborts land at 25 s, never
   upstream's 10 s port default, so this file is demonstrably loaded and used.
2. **The stiction risk this decision flagged is DISPROVEN.** The successful run
   used the *same* `max_rotational_vel: 0.1` that the earlier failures used.
   0.1 rad/s does break this robot away from standstill, so the parameter was
   left alone and D-21 needs no follow-up.

⚠ **An intermediate amendment here claimed stiction was confirmed. It was
wrong and has been withdrawn.** Two failed attempts earlier the same day were
caused by an **unseated battery**, not friction: the ESP32 is USB-powered, so
serial connected and encoders reported while the motor rail was dead. Evidence
and the retraction are in `records/calibration.md` "Spin recovery"; the
diagnostic that distinguishes the two is in the symptom index.

**Bonus, from the successful run's encoder data:** `wheel_separation`
back-computes to **0.25169 m** against the configured **0.25168 m** — the first
*physical* validation of a number that was settled on 10 Sep by inverting a
formula without driving.

---

## D-22 · `make yolo` runs an fp16 `.onnx`, and the model is `yolo26s`
**Date:** 2026-09-16 · **Status:** adopted · **amends D-11**

`make yolo` now exports `~/yolo/yolo26s.pt` → `~/yolo/yolo26s.onnx` via
`cap_ws/yolo/export_onnx.py` and runs the `.onnx` under onnxruntime-gpu's
CUDAExecutionProvider. The export is a prerequisite of the `yolo` target and is
skipped when the file is already current, so a bring-up pays nothing for it.

**This does not reopen D-11.** D-11 chose our own `vision_msgs` node over
`yolo_ros`, and that still stands — same node, same topic, same track ids, same
`Detection2D.id`. What changed is the weights and the backend inside it. Requested
by the user; the measurements below are what decided *how*.

**Measured on this board, 16 Sep** — 640×640, `model.track()` wall time including
ByteTrack, 30 frames after 5 warm-up, synthetic frame:

| | mean | p50 |
|---|---|---|
| `yolo26n.pt` torch | 35.4 ms | 35.4 ms |
| `yolo26s.pt` torch | 36.6 ms | 35.5 ms |
| `yolo26s.onnx` **fp32** | **45.8 ms** | 44.2 ms |
| `yolo26s.onnx` **fp16** | 35.4 ms | 34.1 ms |

**Why:** two things that table settles.

1. **`yolo26s` is nearly free** — 1.2 ms over nano, not the 1.5× the recovered
   engine figures implied (27 ms vs 18 ms). This pipeline is launch-bound, not
   compute-bound, which is the same conclusion 14 Sep reached from `imgsz` 480
   buying nothing. The GPU sits at its 306 MHz floor either way.
2. **ONNX fp32 is a 9 ms regression against plain torch.** Only the fp16 export
   pays for itself. `ONNX_HALF` therefore defaults to **true**, and shipping
   `ONNX_HALF=false` would be strictly worse than the Day 5 configuration.

**Cost, and it is the sharp edge here:** `onnxruntime-gpu` must be the **Jetson
wheel**, installed by direct URL. PyPI has no aarch64+CUDA build; plain
`onnxruntime` is CPU-only, imports under the same module name, and would drop
inference to a few Hz with **nothing in any log** saying why. Worse, ultralytics
tries to `AutoUpdate` it at export time — observed 16 Sep, blocked only because
the launch sets `YOLO_OFFLINE=1`. That env var is now load-bearing for
correctness, not just for demo-day determinism.

**Second cost:** a static ONNX graph has its input resolution baked in, so
`model` and `imgsz` must agree. `export_onnx.py` reads the `imgsz` ultralytics
writes into the ONNX metadata and re-exports on a mismatch, so `make yolo
IMGSZ=480` stays honest; a hand-launched `ros2 launch` with a mismatched `imgsz`
does not, and will either raise a shape error or silently ignore the argument.

Considered and rejected: **TensorRT `.engine`** — `TensorrtExecutionProvider` is
available and would likely be faster still, but D-11 rejected engines because
they are tied to the TensorRT version that built them, which is exactly what
killed the recovered ones at the JetPack 6.2 → 6.1 rollback. An `.onnx` is
portable and survives that. **fp32 ONNX** — measured, and worse than doing
nothing.

**Reversal:** `make yolo MODEL=$HOME/yolo/yolo26s.pt` skips the export and runs
the Day 5 torch path unchanged. `yolo26n.pt` is still on disk.

**Limitation to report:** ~~the Day 5 gate was passed on 14 Sep with
`yolo26n.pt` on torch, and changing both the weights and the backend invalidates
that evidence.~~ ✅ **Re-passed 16 Sep** — 301 s on a real scene: 15.13 Hz,
4553/4553 frames carried detections, id 37 (laptop) held 100.0 %, tj max
52.0 °C. Full numbers in `records/calibration.md`.

What remains open is **not** a limitation of this decision but of the evidence
for it: that run changed the scene as well as the model (blank wall → 4.41
detections/frame), so the GPU going from its 306 MHz floor to its 625 MHz
ceiling at 57 % load **cannot be attributed to `yolo26s.onnx`**. A 60 s
`make yolo MODEL=~/yolo/yolo26n.pt` in the same scene would separate them. Not
run, and not blocking.

---

## D-23 · Wheel slip during a stuck spin: documented, not corrected
**Date:** 2026-09-16 · **Status:** ~~adopted — limitation, untested~~ **superseded by D-25 (18 Sep)** — an IMU is now fitted and fused, behind default-off flags; this limitation text stands until D-25's measurements are made

Reported by the user after the Day 6 gate: when the robot wedges on an obstacle
and spins, the wheels slip. Wheel odometry reports rotation that did not happen.
**Decision: document this as a limitation and change nothing.**

**Why nothing needs building.** `slam_toolbox`'s scan matcher already *is* LiDAR
heading correction. When odometry claims rotation the scans do not support, the
difference is absorbed into `map → odom`, so the robot's pose in the **`map`**
frame stays right. `/diff_cont/odom` keeps the error forever — that edge is raw
wheel odometry by construction — but nothing downstream uses it for global pose;
Nav2 reads TF.

**Why it may nonetheless fail, and this is the part worth reporting.** The
matcher's angular search window is `coarse_search_angle_offset: 0.175 rad`
= **±10°**, narrowed by **D-18** on the explicit premise that odometry is
trustworthy (measured ~1 cm / 0.01° per 0.2 m keyframe). **Wheel slip is exactly
the case that violates that premise.** At `diff_cont`'s 0.5 rad/s ceiling,
**0.35 s of full-speed slip exhausts the window**; beyond it the matcher cannot
search far enough to find the truth and will fail the match
(`link_match_minimum_response_fine: 0.1`) or lock onto a wrong one.

⚠ **Second-order, and worse for the demo than the heading error.** The semantic
layer's motion gate reads ω from `/diff_cont/odom`
(`semantic_objects_node.py:421`). During a slip it sees phantom rotation and
drops every detection at `motion.max_omega: 0.3` — **the fusion goes blind
exactly when the robot is physically still and would give its cleanest
observations.**

**Cost:** none paid; the risk is accepted rather than closed.

**Considered and rejected for this week:** widening
`coarse_search_angle_offset` or raising `angle_variance_penalty` — both reverse
part of D-18 and give back the precision it bought, and neither should be done
without measuring first. An **IMU** is the textbook answer and is not in this
build. Gating the semantic layer on scan-matched motion instead of odom ω would
fix the blindness but is a real change to the fusion path.

**Limitation to report:** *"Heading is corrected by scan matching rather than by
an IMU, and the matcher searches ±10° about the odometry prior. A wheel slip
larger than that — roughly 0.35 s of stall at full rotational speed — is outside
the search window and would not be recovered. The semantic layer additionally
gates on wheel-odometry angular velocity, so it discards detections during a
slip. Neither behaviour was measured on the robot."*

⚠ **UNTESTED.** The mechanism above is derived from the configuration and from
D-18's reasoning, **not** from an experiment on this robot. The measurement that
would settle it is cheap — induce a slip and log `map → base_footprint` yaw
against `odom → base_link` yaw — and was deliberately not run, per constraint 3.

---

## D-24 · The tape-measure protocol is cut; validation stays stationary
**Date:** 18 Sep 2026 · **Status:** adopted (user decision, Day 7)

Day 7's four-pass tape-measure protocol was **not run**. Rehearsals were given
the robot time instead.

**Why:** one robot, one room, and the two compete directly. A demo that fails
on the day is unrecoverable; a report with thin validation numbers is a smaller
and recoverable loss. Constraint 3 — scope to a working demo, not to
correctness — resolves that tie the same way. The protocol buys report evidence,
not demo capability: gates 1-6 had already passed without it.

**Cost:** four of the five metrics in the design note's §08 results table stay
empty, and the one that is filled comes from a **single stationary bench check**
(16 Sep, one chair, 1.64 m, 20-25 deg off-axis): error 0.08 m, within-run spread
0.04 m, duplicates 1, fused 132/140 = 94.3 %. No number in this project comes
from a driven pass.

**What this specifically leaves untested** — worth naming, because it is the
known weak point rather than an arbitrary gap. 144 distinct track ids appeared
in 301 s on 16 Sep, with chair holding two of them (329 and 230). P5 keys "same
object again" on the track id, so a chair that picks up a second id becomes two
landmarks. The bench check returned duplicates 1, but a stationary robot never
re-acquires an object from a new bearing. **A four-pass drive is precisely the
test that would have exposed this, and it was not run.** The duplicates figure
of 1 should not be read as evidence that re-acquisition is sound.

**Limitation to report** (drafted, for the report's limitations section):

> *"The semantic layer's position accuracy was validated at a single
> stationary station rather than by the four-direction driven protocol the
> design note specifies. With the robot held at 1.64 m from a tape-measured
> chair, absolute position error was 0.08 m against a 0.25 m target and 94.3 %
> of detections were fused. Two quantities therefore remain unmeasured: spread
> across viewing directions, and whether a single object re-acquired from a new
> bearing is recorded as one landmark or several. The second is a known risk
> rather than an open question -- object identity is keyed on the detector's
> track id, and track ids were observed to split on a stationary scene. The
> measurement that would close both is the four-pass protocol in the design
> note's section 08; it costs roughly half an hour of robot time and was cut
> for rehearsal time on the final day."*

**Reversal:** `landmark_tape_measure.py` is written, installed and takes
`--pass-label` / `--summary`; `~/maps/tape_session.jsonl` is clean. If robot
time frees up, two passes (front and one side) recover the across-pass spread
and the re-acquisition test in half the time of four.

---

## D-25 · GY-521 IMU added and fused into odometry, behind two default-off flags
**Date:** 18 Sep 2026 · **Status:** adopted (user decision, Day 7) — **built, UNMEASURED, UNTESTED on the robot**

The user fitted a GY-521 (MPU6050) to the ESP32 and added an `i` command to
`esp-motor-firmware` (`98d603f`). **Decision: fuse its yaw rate with wheel
odometry in a `robot_localization` EKF that takes over `odom → base_link`.**
This is the change D-23 named as the textbook answer and declared out of the
build; **D-23 is superseded** by this record, though its limitation text stays
true until the measurements below are made.

Raised and accepted with the user before building: it is Day 7, the committed
demo is complete, and moving `odom → base_link` to a new publisher means gates
3, 4 and 6 have to be driven again to remain evidenced.

**What was decided about the shape, and why it protects the demo:**

- **Every change is off by default.** `make real` alone starts exactly the
  stack that passed the gates: no `i` traffic on the serial line, the same two
  controllers, `diff_cont` publishing TF. `make real USE_IMU=true USE_EKF=true`
  is the fused path. A bad rehearsal drops two flags, not code.
- **The IMU goes through `DiffDriveSerial`.** `ros2_control_node` holds
  `/dev/esp32` exclusively, so no separate node can exist. The interface polls
  `i` after each encoder read and exports a ros2_control `<sensor>` in the
  chip's **raw** axes; `imu_sensor_broadcaster` publishes `/imu_broad/imu` in
  `imu_link`, and the EKF rotates it into `base_link` from TF. Mounting
  orientation lives once, in `description/imu.xacro` — D-10's principle.
- **IMU trouble can never fail `read()`.** Failed polls hold, then zero the
  angular velocity after 3, and log once after 30. The wheels are the demo;
  the IMU is an improvement on them.
- **Fusion split:** wheels give `vx`, `vy` (=0, a real constraint) and `vyaw`
  at variance **1e-2**; gyro gives `vyaw` at **1e-4**. During a slip the gyro
  outvotes the wheels 100:1; if the IMU drops out the estimate keeps turning
  on the wheels. Pose from the wheels is **not** fused, so a slip does not
  enter as a position jump. Accelerometer not fused. No orientation exists
  (`orientation_covariance[0] = −1`).
- **TF topology is unchanged.** `base_link` stays root; only the publisher of
  `odom → base_link` changes, via a spawner `--param-file` that sets
  `enable_odom_tf: false` only when `use_ekf` is true.
- `diff_cont`'s covariances are now **set**. The comment that said nothing
  reads them was true until today.

**Firmware hardening that came with it** (`6c487ef`): 10 ms I²C timeout
(core default 50 ms × two transactions = a ~100 ms stall in `loop()` per
poll on a dead bus — three PID frames, presenting on the host as an encoder
timeout); off-latch after 10 failures; ranges and DLPF (44/42 Hz; the
power-on default is **off**, which aliases motor vibration into yaw rate at
30 Hz) written explicitly on every boot, because the host's EN-pulse reset
does not power-cycle an MPU on the 3V3 rail; WHO_AM_I printed on failure.

**Why:** wheel slip during a stuck spin exceeds the ±10° matcher window D-18
narrowed (D-23); a gyro is the sensor that does not slip. And it turns D-23's
untested limitation into a measurable before/after for the report.

**Cost:** `ros-humble-robot-localization` installed (3.5.4). Re-run of gates
2–4 and the Day 6 bench check on the fused path — **not yet done**. ~8 ms
more serial per 33 ms frame with the IMU on (`imu_poll_divisor` is the lever).

**✅ MEASURED AND INSTALLED THE SAME DAY.** The chip was flashed and
characterised with `imu_check.py`, and all three blockers above are closed:
gyro bias **−105.5 / +238.4 / −81.6** raw counts (−0.81 / +1.82 / −0.62 °/s,
inside the ±20 °/s spec), σ **0.00171 / 0.00145 / 0.00112** rad/s, axis map
**identity with det +1** (the chip is genuinely x-forward, y-left, z-up), and
`/dev/esp32` restored by re-running `make udev`. Covariance installed at
**1e−5**, 8× the measured rest variance rather than the measurement itself,
because rest noise is not driving noise and chassis vibration is unmeasured.

> ⚠ **The signs are the fragile part, and one was lost on first transcription.**
> `+81.6` was pasted for z where the run said `−81.6`. Because the biases are
> *subtracted*, that doubles the error rather than removing it: −1.25 °/s of
> phantom yaw, **75 °/min** of heading drift standing still, against 37 °/min
> uncorrected — and z is the only axis the EKF fuses. Caught the same day by
> re-deriving from the script's output. **Copy the line verbatim.**

**✅ THE FUSED STACK HAS NOW RUN, STATIONARY, AND IT WORKS.** 18 Sep evening,
`use_ekf:=true`: `/joint_states` **29.996 Hz** (the serial budget fits — this
was the real risk), `/imu_broad/imu` **30.00 Hz with zero gaps > 50 ms**,
all three controllers active, `diff_cont enable_odom_tf` **False** so the EKF
owns the edge, bias subtraction confirmed end to end, and **stationary yaw
drift of +0.06 °/min** on `/odometry/filtered`. Numbers in
`records/calibration.md` "IMU — Live verification".

> ⚠ **The covariance was wrong and the filter caught it.** Installed at
> **1e−5** from the rest-noise measurement; gyro σ on the *running* stack is
> **11× that variance** (1.11e−04 against 1.25e−06), because energising the
> drive is most of the noise and that is the condition the number is used in.
> The symptom was exact: `/odometry/filtered`'s vyaw σ matched the raw gyro's
> to three decimals, i.e. **the filter was doing no smoothing at all**.
> Corrected to **1e−4**, which is the measured value and restores this
> decision's intended **100:1** ratio. Slip rejection is unaffected.
>
> ✅ **DONE AND CONFIRMED, same evening.** `DLPF_CFG` 3 → 4 (20 Hz, 8.3 ms
> delay) flashed, and on the running stack the gyro variance fell **4.8×**
> (σ 0.01053 → 0.00486 rad/s) while rest noise was unchanged — the exact
> signature of undersampling, since aliasing only shows when there is
> vibration to fold. Yaw jitter fell 3.4×. Covariance re-derived from the
> new measurement and installed at **5e−5** (2× the measured 2.31e−05,
> padded only for the wheels-turning case, which is still unmeasured).
> Gyro outvotes the wheels **200:1**.

> ⚠ **The honest caveat for the report: at standstill the EKF is strictly
> worse than wheel odometry.** Stationary encoders cannot report rotation,
> so `/diff_cont/odom` yaw path over 30 s is 0.000° while the EKF adds
> 5.7° of random walk. **Every benefit of this decision lives in the driven
> and slip cases, and neither has been measured.** The standstill numbers
> prove the plumbing, the bias correction and the noise floor — not the
> value of the fusion.

**What is still unmeasured — all of it needs the robot to MOVE:**
1. ~~`odom_check.py`~~ ✅ **DONE 18 Sep.** Hand-pushed 1.1 m and turned ~90°
   with `--compare` (added for this; the default watches only
   `/diff_cont/odom`, which the EKF does not touch). Distance agrees to
   **0.98 %**, yaw to **4.3°**, and critically **the yaw signs agree** — the
   measured axis map is confirmed on real rotation, not just on a
   stationary bench. The 4.3° is not attributable: the gyro's ±3 % scale
   tolerance covers it, and the true angle was a hand turn. See
   `records/calibration.md`.
2. The Day 3 loop with `check_pose_stability.py`, **run both ways**. The
   claim to test is that `map → odom` correction total-path goes DOWN with
   the EKF on. Note the stationary run already put 14.8° of yaw *path* into
   30 s at 1e−5; at 1e−4 that should fall, and this is the run that says so.
3. One Nav2 goal plus a deliberate Spin recovery.
4. **The wedged-slip yaw comparison** — `map → base_footprint` yaw against
   `odom → base_link` yaw, with and without `USE_EKF`. This is the report
   figure and the only thing that actually closes D-23.
5. The stationary semantic bench check.
6. Gyro σ with the wheels actually **turning** (on blocks, under `o`), which
   is a stricter case than motors merely energised, and the only reason the
   installed covariance carries 2× padding rather than sitting on the
   measurement.

**Limitation to report** (drafted, replaces D-23's if the fused path is
demonstrated; otherwise D-23's stands):

> *"Heading is estimated by an extended Kalman filter fusing wheel odometry
> with a MEMS gyroscope, weighted 100:1 toward the gyroscope in yaw rate, so
> that wheel slip during a stalled rotation does not enter the heading
> estimate. The gyroscope's bias and mounting orientation were measured at
> rest; the filter's benefit under slip was [measured as … / not measured]."*

**Reversal:** `make real` with no flags. Nothing else needs undoing.

---

## D-26 · Raise the teleop ceiling to 0.30 m/s. Nav2's own speed is unchanged
**Date:** 21 Sep 2026 · **Status:** adopted · **amends the velocity half of D-18**

Requested by the user after `make teleop-nav` and `make explore` both felt
unusably slow and `q` appeared to do nothing. **Three numbers moved together,
because any one of them left behind silently wins:**

| Where | Was | Now |
|---|---|---|
| `diff_cont` `linear.x.max_velocity` / `min_velocity` (`config/my_controllers.yaml`) | ±0.15 | **±0.30** |
| `teleop_speed_guard` `max_linear` (default in the script **and** in `navigation.launch.py`) | 0.10 | **0.30** |
| `Makefile` `TELEOP_MAX_LINEAR`, and `SPEED` (the teleop starting speed) | 0.10 | **0.30** |

`angular.z` is untouched at ±0.5 rad/s; the guard and `TURN` were already at
0.50, so yaw was never the thing being clamped.

**Nav2 was deliberately NOT raised.** `max_vel_x` stays 0.10, so `make explore`
and goal navigation drive at exactly the speed they did when the Day 4 gate
passed. Raising Nav2 is a coupled edit — `FollowPath.max_vel_x`,
`max_speed_xy`, `acc_lim_x`/`decel_lim_x` and `velocity_smoother.max_velocity`
must all move, *and* `sim_time` has to be revisited because the lookahead
distance is `sim_time × max_vel_x` (3.0 s × 0.30 = 0.9 m, against the ~30 cm
"about the robot's own length" the current value was chosen for). That is a
retune, not a number, and it was not worth doing to a passing gate on Day 7.

**Why:** `q` was inert by design and the design had stopped matching what the
robot is used for. D-18's cap was written for *map-building* runs, where shear
is the binding constraint; most driving now is repositioning between rehearsals,
where it is not. The user asked for 0.30 explicitly; this is their call.

**Cost — paid in scan shear, and it is real.** The X3 Pro sweeps 360° in ~86 ms
and `slam_toolbox` does not deskew, so each scan shears by `speed × sweep`:

| Speed | Shear per scan |
|---|---|
| 0.10 m/s (mapping) | 0.9 cm |
| **0.30 m/s (new ceiling)** | **2.6 cm** |
| 0.5 m/s (teleop stock — lost the 10 Sep map) | 8.7 cm |

So it is ~3× the shear budget the Day 3 map was built on, and about a third of
what destroyed the 10 Sep run. Sheared scans enter the pose graph permanently.
**Mitigation, and it is a habit not a mechanism:** drive map-building runs with
`make teleop-nav SPEED=0.10`, or cap the whole session with
`make nav TELEOP_MAX_LINEAR=0.10`. Nothing enforces this any more.

Second cost: **`make teleop` has no guard in front of it** (it publishes
downstream of `twist_mux`), so `q` there now climbs to 0.30 rather than 0.15.

Third, smaller: D-18's scan matcher searches ±15 cm about the odometry prior.
At 0.30 m/s the robot covers 15 cm in 0.5 s, so a dropped keyframe or a stall
eats that window about twice as fast as before. Same window, less time in it.

**Limitation to report:** *"Manual driving is limited to 0.30 m/s in the
controller. Map-building runs were driven at 0.10 m/s, where lidar shear is
0.9 cm per scan; the higher limit exists for repositioning and is not a speed
at which the mapping results were obtained."*

**Reversal:** set the three numbers back to 0.15 / 0.10 / 0.10, `colcon build`,
restart `make real` **and** `make nav`. Nothing structural changed.

---

## D-27 · Objective 2 is scored on the 24 Sep stationary-camera set, as a fixed-viewpoint test
**Date:** 24 Sep 2026 · **Status:** adopted

The 143-frame set from bag `2026-09-24-165025` (`~/eval/insitu2_stationary`)
is the objective 2 test set. It is **not** re-recorded, and it is described in
the report as what it is: **a fixed viewpoint with people moving through the
scene**, not a driven survey.

**Why:** the user's call, on time. The robot was nudged by hand during the
recording but the camera did not measurably move: the laptop's box centre is at
x = 123–124 px and 230 px wide from the first frame to the last, the
backpack's 216 px / 114 px likewise. What varies is the people — walking past
close to the camera (≈ frames 000000–000035), standing and walking at distance
(≈ 000036–000083), one seated on the blue chair (≈ 000084–000142).

**Cost:** `laptop` and `backpack` are each **one physical object at one pose**,
so their per-class scores describe one instance repeated, not the class. The
report must not describe the set as driven, multi-view or multi-distance.

**Limitation to report (Thai, for chapter 5):** *"ชุดภาพทดสอบ 143 ภาพ
สุ่มจากการบันทึก 290 วินาที ขณะหุ่นยนต์จอดนิ่งในมุมมองเดียว โดยมีบุคคลเคลื่อนที่ในฉาก
(เดินผ่านระยะใกล้ ยืน และนั่งบนเก้าอี้) ตลอดการบันทึก คลาส laptop และ backpack
มีวัตถุอย่างละหนึ่งชิ้นในตำแหน่งคงที่ ผลของสองคลาสนี้จึงสะท้อนวัตถุชิ้นเดียว
และไม่ได้ทดสอบความหลากหลายของระยะและมุมมอง"*

**Reversal:** re-record round A while moving the robot between 6–8 spots
(`MEASUREMENT-PLAN.md` §2), extract into `~/eval/insitu2`, label, score.

---

## D-28 · Objective 2 re-test: yolo26m as a TensorRT fp16 engine, conf 0.5
**Date:** 24 Sep 2026 · **Status:** adopted — **fixed before the new test set is recorded**

The detector under test becomes `~/yolo/yolo26m_480x640.engine` (ultralytics
export, fp16, **imgsz (480, 640)** to match the camera, batch 1, TensorRT 10.3),
run by the existing node (`make yolo MODEL=~/yolo/yolo26m_480x640.engine`,
`CONF` left at **0.5**). *Amended the same afternoon, before any test-set
recording:* the first engine was exported at 640×640, which measured ~2 F1
points worse on the validation set; the cause is the padding, not TensorRT
(`records/calibration.md`, "The accuracy loss is the square input"). Objective 2
is re-scored **once**, on a NEW bag recorded with the robot moving, at the
script defaults (IoU 0.5, conf 0.5, `--min-instances 50`, classes
`person chair backpack laptop`).

**Why:** the user's call. yolo26m was chosen from the exploratory sweep in
`records/objective-tests.md`, so the D-27 set is now the *validation* set and
cannot also be the test set. On it, yolo26m at conf 0.5 scored 67.4 % (vs
66.3 % for yolo26s on the same untracked path) — **expect roughly that, not a
pass**; the sweep's gain came from conf 0.25, which was offered and not taken.

**Pre-registered:** the conf-0.5 score on the new set is the objective 2
result. If the same new set is later scored at another conf, that is a
post-hoc analysis, reported beside it, never instead of it.

**Cost:** objective 3's 13.05 FPS and D-22 were measured with yolo26s ONNX;
both must be re-measured with this engine. The engine is tied to TensorRT 10.3
(D-11's objection) — the `.pt` and `.onnx` stay on disk as the rebuildable source,
and `make yolo` with no MODEL is still the yolo26s ONNX path.

**Reversal:** `make yolo` (defaults) — nothing else changed.

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

## D-28 · Objective 5: stop OpenBLAS busy-waiting, do not throttle detection
**Date:** 24 Sep 2026 · **Status:** adopted — post-fix window not yet measured

`OPENBLAS_NUM_THREADS=1` in `yolo.launch.py`'s node env. The detection rate,
model and camera rate are unchanged.

**Why:** The 596 s full-stack window was 81.5 % (fail by 1.5 points). About 200 % of
`yolo_detector.py`'s 371 % was five OpenBLAS threads busy-waiting after
ByteTrack's small matrix ops (`records/calibration.md`, Objective 5). One
thread cut the node from 263 % to 38 % offline at the same rate.
Throttling (`make yolo CAM_FPS=8`, the §4.3 table's first idea) only scales
the waste down with the frame rate, and it would put objectives 3 (13.05 FPS)
and 5 on different configurations, which the report would have to explain.
The ORT-pool hypothesis was tested first and ruled out.

**Cost:** none measured. A single BLAS thread can only matter for large matrices,
and ByteTrack's are a few boxes by a few tracks.

**Limitation to report:** the pre-fix 81.5 % window is real and must be
mentioned alongside the post-fix figure, as a finding and its fix.

**Reversal:** delete the one env line.
