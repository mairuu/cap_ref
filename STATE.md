# STATE — where the work stands

> **Update this at the end of every session and whenever a gate passes.**
> Claude reads this first. If it is stale, Claude works from stale assumptions.

**Last updated:** 25 Sep 2026 (obj 1 into the report; the 21 Sep text below stands) — **DAY 7 IN PROGRESS.** Speeds were raised
(Nav2 earlier today, teleop this session); the IMU work from 18 Sep still has
every driven measurement outstanding.

> 🧭 **25 Sep (late) — SLAM trusts odometry more (D-32), NOT YET DRIVEN.**
> `link_match_minimum_response_fine` 0.1 → **0.35** (near-chain matches were
> unpenalised and overwrote the keyframe pose — the likely route for `_0925b`'s
> lap-2 +46 cm jump), `minimum_distance_penalty` 0.5 → **0.3**,
> `angle_variance_penalty` 0.15 → **0.1**, `minimum_angle_penalty` 0.8 → **0.7**.
> Window unchanged. **Restart `make slam` to pick it up** (symlinked, no build).
> Test = a ≥ 2-lap objective 1 run; compare REPEAT to `_0925b`'s 25.7 cm.

> 🧮 **24 Sep — objective 5 (CPU ≤ 80 %) ✅ PASS at 55.8 %, IN THE REPORT.**
> Pre-fix 81.5 % (23 Sep, yolo26s ONNX) → post-fix **55.8 %** (24 Sep 19:58 window,
> 472 of 596 s: yolo restart 129–175 s and the stack-off tail from 521 s excluded,
> which *raises* the mean from the file's 48.4 %). The drop is the OpenBLAS fix
> (D-28); the model swap is < 1 point. `tab:eval` row 5, new `tab:obj5`, results
> text, abstract, conclusion and `figures/resource_usage.png` done. Regenerate
> with the command in `records/calibration.md` → Objective 5 post-fix.
> **Unconfirmed:** that yolo26l was the model (inferred from launch time) and
> that the robot drove the whole window.

> 📏 **24 SEP — REPORT MEASUREMENTS (see `MEASUREMENT-PLAN.md`, the live runbook).**
> Objective 2 ✅ **82.2 %** macro F1 (yolo26l TensorRT fp16 480×640, conf 0.4;
> baseline yolo26s 64.4 %) — tuned on the same 143 frames, no held-out set
> (D-27, D-29). Objective 3 ✅ **15.16 Hz** with SLAM + semantic. **Plain
> `make yolo` now runs yolo26l TensorRT 480×640 at conf 0.4 (D-30)** and
> rebuilds the engine if missing (~13 min, stack down). Node change: compiled models take
> imgsz from the model (cap_ws `27dec07`). Round B (obj 4) ✅ **PASS, worst 33.8 cm, mean 18.8 cm** (report from `~/maps/object_accuracy_chair_final.jsonl`) — see `records/calibration.md` → Objective 4. C ✅ (obj 5, above).
> ~~Still owed: D only~~ **D ✅ 25 Sep: obj 1 PASS, worst 6.4 cm (ALIGNED 6.5) at A/B/C,
> `_0925c`, 1 lap, NO HOME return (battery died), area 4.85 × 3.52 m. In the report
> (`tab:obj1`, `slam_error_result.png`) with those limits stated.** A full lap back to
> HOME is still worth driving if there is time; report whatever it gives. E: `nav2_costmap_path.png` in (local costmap only; user
> declined a retake with a path). `all_nodes_running.png` in (user's screenshot). `ros2_node_graph` (headless, `node_graph.py`) and
> `tf_tree` (`view_frames`) ✅ made 24 Sep 22:07 from the live demo stack.
> Report is `project_report-good3.tex` only (good5 removed).

> 🏃 **SPEED LIMITS CHANGED TWICE ON 21 SEP. Any figure quoted below from an
> earlier session is at the OLD speed.**
>
> **Nav2 (`make explore`, goal navigation) — commit `7de62ce`:**
> `max_vel_x` **0.055 → 0.10**, `max_vel_theta` **0.125 → 0.25**, in both
> `FollowPath` and `velocity_smoother`; `behavior_server.max_rotational_vel`
> 0.1 → 0.2. The Day 4 gate and the Spin recovery were evidenced at the OLD
> values — **the 16.4 s / 1.5762 rad spin will now take about half as long,
> and the `time_allowance="25.0"` override (D-21) has that much more margin.**
>
> **Teleop — D-26, this session, at the user's request.** `make teleop-nav`
> and `make teleop` were capped at 0.10 m/s with `q` deliberately inert; the
> user asked for 0.30. **Three numbers had to move together** or the lowest
> silently wins: `diff_cont` `linear.x` ±0.15 → **±0.30**
> (`my_controllers.yaml`), `teleop_speed_guard` `max_linear` 0.10 → **0.30**
> (script default *and* `navigation.launch.py`), and the Makefile's
> `TELEOP_MAX_LINEAR` **and** `SPEED` 0.10 → **0.30**. Angular untouched at
> 0.5 rad/s — it was never the binding limit. Built and verified in
> `install/`; **not yet driven.**
>
> ⚠ **THE MAPPING SPEED IS STILL 0.10 m/s AND NOTHING ENFORCES IT NOW.**
> Scan shear is `speed × 86 ms`: 0.9 cm at 0.10, **2.6 cm at 0.30**, 8.7 cm at
> 0.5 (which lost the 10 Sep map). For any run that is *building* a map, drive
> `make teleop-nav SPEED=0.10`, or start the session with
> `make nav TELEOP_MAX_LINEAR=0.10`. The guard no longer protects the map — it
> only stops a runaway.
>
> ⚠ **`make explore` was NOT raised to 0.30** and is still 0.10. That is
> deliberate (D-26): raising Nav2 is a coupled retune — `max_vel_x`,
> `max_speed_xy`, `acc_lim_x`/`decel_lim_x`, `velocity_smoother.max_velocity`
> *and* `sim_time`, because lookahead distance is `sim_time × max_vel_x` — and
> it was not worth doing to a passing gate on Day 7.
>
> **A running stack keeps the parameters it started with.** If the robot still
> crawls, it is a pre-21-Sep `make real` / `make nav` still up, not the config.

> ✅ **RESOLVED — `/dev/esp32` and `/dev/ydlidar` are both up.** `make udev`
> was re-run 20:55 with both devices plugged in; the ESP32 is back on its
> original path `1-2.1.4` → `ttyUSB1`, the lidar on `1-2.2` → `ttyUSB0`.
> **Label the sockets** — the rules match physical port path, so the names
> follow the socket and not the device.
>
> ⚠ One cosmetic wart in the regenerated rules: the ESP32's identification
> line reads `answered \`e\` as: unknown` where the 9 Sep run said `esp32`.
> The mapping is right (`imu_check.py` talked to `/dev/esp32` successfully),
> so this is the probe landing mid-boot, not a crossed pair. Do not "fix" it
> by editing the rules file.

> **BUILT — the GY-521 (MPU6050) is fused into odometry, behind two
> default-off flags (D-25).** The user added the chip and an `i` command to
> the firmware; this session hardened the firmware for being polled from the
> 30 Hz loop (`esp-motor-firmware` `6c487ef`, pushed), added a ros2_control
> `<sensor>` to `DiffDriveSerial`, `imu_broad`, `robot_localization`
> (`ros-humble-robot-localization` 3.5.4 installed) and `config/ekf.yaml`.
> **`make real` alone is byte-identical to the stack that passed gates 1–6;**
> `make real USE_IMU=true USE_EKF=true` is the fused path, in which the EKF
> owns `odom → base_link` (gyro 100:1 over wheels in yaw rate). Builds clean;
> URDF validates both ways; launch resolves the right spawners per flag.
>
> ✅ **THE CHIP IS FLASHED, CHARACTERISED AND ITS NUMBERS ARE INSTALLED**
> (18 Sep, `imu_check.py`). **Gyro bias −105.5 / +238.4 / −81.6 raw counts**
> (−0.81 / +1.82 / −0.62 °/s, all inside the ±20 °/s spec) → installed in
> `ros2_control.xacro`. **σ 0.00171 / 0.00145 / 0.00112 rad/s**; σ_z is
> 0.064 °/s, which is quiet enough to double as proof the 42 Hz DLPF took
> effect — so the rest noise is also the check that the new firmware is the
> one running. **Axis map measured by hand: identity, det +1** — the chip
> really is x-forward, y-left, z-up, and `imu.xacro`'s `rpy 0 0 0` is now a
> result rather than an assumption about a silkscreen.
>
> Gyro covariance installed at **1e−5**, which is 8× the measured rest
> variance and not the measured value: rest noise is not driving noise, and
> chassis vibration is still unmeasured. Wheel-to-gyro ratio on yaw rate is
> **1000:1**.
>
> ⚠ **Two transcription errors were made and caught when those biases were
> first pasted in** — x as −100.5, and **z with its sign dropped to +81.6**.
> The biases are *subtracted*, so a dropped sign doubles the error instead of
> removing it: +81.6 for z gives −1.25 °/s of phantom yaw, **75 °/min** of
> heading drift standing still, against 37 °/min uncorrected. z is the only
> axis the EKF fuses. **Copy `imu_check.py`'s bias line verbatim; do not
> retype it.** A second defect from the same afternoon is also fixed: `1.0e6`
> in the new covariance arrays parsed as a *string* (YAML 1.1 wants a signed
> exponent), which `diff_cont` would have rejected at load.
>
> ✅ **THE FUSED STACK RAN, STATIONARY, AND IT WORKS** (18 Sep evening,
> `use_ekf:=true`, which correctly implied the IMU). **`/joint_states`
> 29.996 Hz** — the serial budget fits, which was the real risk. Also:
> `/imu_broad/imu` **30.00 Hz with zero gaps > 50 ms**, all three
> controllers active, `enable_odom_tf` **False** so the EKF owns
> `odom → base_link`, bias subtraction confirmed end to end, |a| 0.999 g,
> and **stationary yaw drift +0.06 °/min** — 0.6° over a ten-minute demo.
>
> ⚠ **One number was wrong and has been corrected: the gyro covariance.**
> Installed at 1e−5 from the rest measurement; σ on the *running* stack is
> **11× that variance** (1.11e−04 vs 1.25e−06) because energising the drive
> is most of the noise. The filter said so plainly — `/odometry/filtered`
> vyaw σ came back 0.01023 against the gyro's 0.01053, i.e. **no smoothing
> at all** — and it put 14.8° of total yaw path into a stationary 30 s
> window. Now **1e−4**, the measured value, restoring the intended
> **100:1** ratio. **Rebuilt; the stack must be restarted to pick it up.**
>
> ✅ **`DLPF_CFG` 3 → 4 IS FLASHED AND IT WORKED** (firmware `3f188b5`).
> On the running stack the gyro variance fell **4.8×** (σ 0.01053 →
> 0.00486 rad/s, 0.603 → 0.276 °/s) and stationary yaw jitter fell **3.4×**
> (14.84° → 5.68° of path per 30 s), while **rest noise was unchanged** —
> which is the signature of aliasing, because folding only shows when there
> is vibration to fold. 42 Hz of bandwidth against a 30 Hz poll put
> everything above the 15 Hz Nyquist back into the reading.
> **Covariance re-derived and installed at 5e−5** (2× the measured
> 2.31e−05; the padding covers only the wheels-turning case, still
> unmeasured). Gyro outvotes the wheels **200:1**. Stationary net yaw drift
> is **+0.01 °/min**.
>
> ⚠ **Read this before quoting any of it in the report: at standstill the
> EKF is strictly WORSE than wheel odometry.** Stationary encoders cannot
> report rotation, so `/diff_cont/odom` yaw path over 30 s is **0.000°**
> while the EKF adds 5.7° of random walk. The standstill numbers prove the
> plumbing, the bias correction and the noise floor. **They do not prove the
> fusion is worth anything** — its entire value is in the driven and slip
> cases, and neither has been measured.
>
> **Nothing is running now.** Both stacks started this evening were stopped
> with a clean SIGINT (motors stopped on deactivate); no ROS processes and
> the port is free.
>
> ✅ **`odom_check.py --compare` PASSED (18 Sep).** Hand-pushed 1.1 m and
> turned ~90°: distance **wheels 1.127 m vs EKF 1.116 m (0.98 %)**, yaw
> **−87.9° vs −92.2° (4.3°)**, and **the yaw SIGNS AGREE** — which confirms
> the measured gyro axis map on real rotation, the one error that would make
> the EKF worse than no EKF. The 4.3° is not attributable to either sensor:
> the MPU6050's ±3 % scale tolerance covers it and the true angle was a hand
> turn. `calibrate_spin.py` under power with the gyro logged alongside would
> calibrate the gyro scale for free — worth folding into Day 3.
>
> ⚠ **Do not lift or pivot this robot mid-run.** An earlier attempt caught
> the EKF turning −86.4° while the wheels read −0.6° — an event, not drift.
> The EKF integrates the gyro through a lift and the encoders see nothing, so
> `odom` stops meaning anything until `slam_toolbox` absorbs it.
>
> **Still to do, all of it needing the robot to MOVE UNDER POWER:**
> the Day 3 loop with `check_pose_stability.py` **both ways** (the claim:
> `map → odom` correction total-path goes DOWN with the EKF) → one Nav2
> goal + Spin → **the wedged-slip yaw comparison, which is the report
> figure and the only thing that closes D-23** → the stationary bench
> check. Full table in `records/calibration.md` "IMU". **Stop at the first
> failure and drop the flags — the demo does not depend on any of it.**
>
> One deliberate choice left open: the semantic layer's motion gate still
> reads ω from `/diff_cont/odom` (`robot_params.yaml: odom_topic`), so it
> stays blind during a slip even with the EKF on. Repointing it at
> `/odometry/filtered` is one line and needs its own re-test.

**Previously, 18 Sep afternoon** — two things settled, one built, one cut.

> **BUILT — the UI has an object list and inspector** (`cap_ref` `942cf1b`).
> The side panel now lists every landmark with class, published map-frame
> position, confidence and seen count, ordered nearest-the-robot first — the
> same landmark `go_to_object.py` would pick. Clicking a row rings it on the
> canvas; `⌖` centres the view (turning FOLLOW off first, because the RAF loop
> re-centres on the robot every frame and would otherwise overwrite the view
> before it was painted). Per-class counts double as the legend, which means
> **`chair ×2` on screen is the duplicate-landmarks metric, live.**
>
> Two fixes rode along. The **MOCK badge had never once appeared** —
> `HealthResponse` had no `mock` field while `App.tsx` has always read
> `h.mock` and the README has always promised the badge; a demo display must
> not be able to show synthetic data without saying so. And **unmapped classes
> no longer all render grey**: `classColor` had seven entries and a grey
> fallback, so `table` and `door` — two of the three landmarks the bridge's own
> mock mode publishes — were the same colour as each other and as everything
> else. Unknown labels now hash to a stable hue. This deliberately changed an
> assertion in `colors.test.ts`. 75 UI tests, 39 bridge tests, `tsc --noEmit`
> and a production build all clean.

> ⛔ **CUT — the four-pass tape-measure protocol was not run. See D-24.**
> Rehearsals were given the robot time instead. **No number in this project
> comes from a driven pass.** The one filled row of the §08 results table is
> the 16 Sep **stationary** bench check (1.64 m: error 0.08 m, within-run
> spread 0.04 m, duplicates 1, fused 94.3 %). D-24 carries a drafted
> limitations sentence for the report, and names what this leaves untested:
> **re-acquisition from a new bearing**, which is the known weak point (144
> track ids in 301 s, chair holding both 329 and 230; P5 keys object identity
> on the track id). Duplicates = 1 from a stationary robot is **not** evidence
> that re-acquisition is sound.

> ⚠ **Correction to a figure quoted all week.** The **~45 % fused ratio is not
> a while-driving number.** `records/calibration.md` records that those four
> windows were captured with the robot *largely stationary*, and that the
> drive-past which satisfied the "stays" clause had its ratio uncaptured. Do
> not cite ~45 % as a driving figure in the report.

**Stack state, 18 Sep ~15:50:** everything was brought up (`real`, `slam`,
`nav`, `semantic`, RViz) and then **stopped by Ctrl-C**; the launch logs record
`user interrupted with ctrl-c (SIGINT)` on all three. Nothing is running now but
the `ros2` daemon. Two shutdown-path warts seen while tearing down, neither a
runtime fault: **`semantic_objects_node` exits 1 on SIGINT** rather than
cleanly, and **`image_transport republish` dies with -11 (SIGSEGV)**.

**Verified live before shutdown:** `/scan` 11.6 Hz · `/image/compressed`
13.3 Hz · `/detections` 14.8 Hz (person 0.96, chair 0.84, laptop 0.93) ·
`/semantic_landmarks` publishing a chair at (−1.683, 3.993) ·
`ros2 param get /diff_cont linear.x.max_velocity` → **0.15** (that reading was
correct on 18 Sep; **it is 0.30 as of 21 Sep** — D-26, see the top of this file). The RViz
`Semantic Landmarks` display was **confirmed correctly defined** in `nav.rviz`
(enabled, `/semantic_markers`, Reliable + Transient Local, depth 1 — matching
the publisher exactly) but **still never observed populating**; it remains the
one carried-forward unknown.

---

**Previously, 16 Sep 2026, evening** — ✅ **DAY 6 GATE PASSED. Track A and
Track B are merged and the committed demo is complete.** All four clauses:
a labelled marker appears in roughly the right place and **stays after driving
away** (user-confirmed), the browser UI shows it, the fused ratio is **~45 %**
(~25/57 per 5 s window, `tf miss 0`, all rejections `max_spread`), and both
repos are pushed. **Day 7 may start.**

> ⚠ **Two things carried forward, neither blocking.**
>
> **1. "Markers appear in RViz" is still not confirmed** — it is a §3 item, not
> a GATE clause, so Day 7 is not blocked. But the `Semantic Landmarks` display
> added to `nav.rviz` on 16 Sep (MarkerArray on `/semantic_markers`, **Transient
> Local**) has never been exercised, and with multi-machine ROS 2 down RViz on
> the Jetson is a likely demo display. If it is present but empty while the node
> reports landmarks, the durability match is wrong, not the fusion.
>
> **2. The fused ratio is below Day 7's target.** Day 7 scores *detections
> mapped / detections received* against **> 0.6** and this run gave ~0.45. Every
> rejection was `max_spread` — the chair sitting closer than ideal, so the scan
> window straddles it and the background. The stationary bench check at 1.64 m
> managed **94.3 %**. **Back the robot off further before the tape-measure
> protocol.**

> **Four defects were found and fixed reaching this gate. Not one was a fusion
> or geometry fault** — each presented as if the robot were wrong:
> a **fatal startup race** in `semantic_objects_node.py` (stats initialised
> after the subscribers, so starting `semantic` into a live `/detections` killed
> the executor silently — the natural bring-up order was the failing one);
> **`NO SIGNAL` rendered unconditionally** over a working 15.3 Hz feed; **the map
> fetched once and never refreshed** while `slam_toolbox` kept extending it; and
> **class labels at 1.08:1 contrast** against mapped free space. Worth citing in
> the Day 7 write-up.

**Earlier, 16 Sep — DAY 6 STATIONARY BENCH CHECK PASSED**
(error **0.08 m**, spread **0.04 m**, duplicates **1**, fused **132/140 = 94.3 %**).
The geometry chain is verified end to end: the chair was 18.4° off-axis on the
right, where a mirrored window would have missed by ~1.06 m. **The Day 6 gate
proper — the drive-past — is still open**, as is P2 under rotation and the
motion gate, neither of which a stationary robot exercises.

**And the Day 4 Spin recovery was finally run, and it FAILS — see the block
below.** Stack was brought up and taken back down cleanly in the same session;
nothing is running now.

**Earlier, 16 Sep — `make yolo` runs `yolo26s` as an fp16 `.onnx`
(D-22), and the DAY 5 GATE IS RE-PASSED on it.** 301 s, real scene: **15.13 Hz,
4553 msgs, every frame processed; id 37 (laptop) held 4459/4553 = 100.0 %; tj
max 52.0 °C.** The swap cost 1.2 ms on the bench — this board is launch-bound,
so the bigger model is nearly free, but **ONNX fp32 is a 9 ms regression against
torch and only the fp16 export pays for itself** (`ONNX_HALF=true`; do not ship
false). The venv gained onnxruntime-gpu 1.24.0 — the **Jetson** wheel, by direct
URL; PyPI's is CPU-only, imports under the same name, and would cost a silent
10× with nothing in any log.

> ⚠ **Two things that run raises, neither of which blocks Day 6.**
>
> **1. The GPU is no longer idling.** 14 Sep had it pinned at its 306 MHz floor,
> 0–50 % bursty. 16 Sep: **625 MHz ceiling, 57 % mean load, tj 52 °C** (was
> 44.6). Still far from the ~90 °C limit and still camera-limited — but
> `sudo jetson_clocks` is no longer a lever in reserve, because the clock now
> reaches its ceiling on its own. **The run changed two variables at once**
> (model+backend *and* blank wall → 4.41 dets/frame), so this cannot be pinned
> on the model. 60 s of `make yolo MODEL=~/yolo/yolo26n.pt` in the same scene
> would separate them. Not run.
>
> **2. 144 distinct track ids in 301 s**, with several classes holding more than
> one (laptop 37 and 107; chair 329 and 230). The gate only asks for one
> persistent id and got a perfect one. But **P5 uses the track id as the
> semantic layer's "same object again" key**, so a chair that picks up a second
> id becomes two landmarks. The report cannot tell two chairs from one chair
> twice. **The Day 6 bench check settles it** — one taped chair, no driving —
> and should be run before reading anything into the drive-past.

Also fixed: `detection_report.py` ended every run with `terminate called without
an active exception` / `[ros2run]: Aborted` — a spin-thread/exit race, after the
report had already printed. Clean exit now.

**Previously, 15 Sep 2026, evening** — **DAY 3 AND DAY 4 GATES PASSED. Track A
is complete through Nav2.** The re-run with Fixed Frame `map` and the D-21
behaviour tree was clean: three goals, three successes, no stale-frame timeouts
(115.5 s / 31.8 s / 6.9 s; `bt_navigator_8618_1789465529679.log`).

> ✅ **CLOSED 16 Sep — THE SPIN RECOVERY WORKS. The Day 4 gate is now fully
> evidenced.** `SUCCEEDED in 16.400653 s`, rotating **1.5762 rad (90.31°)**
> against the 1.57 target, wheels counter-rotating −5.9963 / +6.1356 rad. Inside
> the predicted 15.7–16.5 s. **D-21 is vindicated on both counts:** the
> `time_allowance="25.0"` override is loaded and used, *and* the stiction risk it
> flagged is **disproven** — the successful run used the same
> `max_rotational_vel: 0.1`, which was left unchanged.
>
> ⚠ **RETRACTION.** An earlier version of this block said the spin had failed on
> **stiction**. That was wrong. Two failed attempts the same day were caused by
> an **unseated battery**: the ESP32 is USB-powered, so serial connected and the
> encoders reported normally while the motor rail was dead — every reading looked
> like a stalled drivetrain. **Check the battery before suspecting friction.**
> The connector is keyed, this was a one-off, and no pre-flight step was added.
> The diagnostic that separates the two (`/joint_states`, not odom) is in the
> symptom index.
>
> **Free result:** the successful spin's encoder data back-computes
> `wheel_separation` to **0.25169 m** against the configured **0.25168 m** —
> the **first physical validation** of a number settled on 10 Sep by inverting a
> formula without driving. See `records/calibration.md` "Spin recovery".

> ⚠ **Goal C was not a real test** — (3.01, 0.30) → (3.08, 0.37) is 0.099 m,
> inside `xy_goal_tolerance` 0.15, so the robot was already at the goal and only
> settled its yaw. Two of the three goals were real. The doorway and
> unknown-space cases in the Day 4 checklist §3 are not distinguishable in the
> log either; if they were driven, they passed, but nothing records which goal
> was which.

**DAY 3 GATE PASSED.** The loop was driven and
`~/maps/day3-reference` is a valid artefact at last (271×488 @ 0.05 m =
13.6 × 24.4 m, origin [−6.82, −9.80], saved 17:16). **The Day 4 gate was
attempted and FAILED — four goals, four failures — and both causes are found,
proven from the logs, and one of them is already fixed in the repo.** Neither
was navigation tuning. See "Day 4 gate, attempt 1" below before re-running it.

> **Day 4 gate, attempt 1 (15 Sep) — the two causes.**
>
> **1. The goals were published in the `odom` frame, not `map`.** RViz stamps a
> goal in its **Fixed Frame**, and a goal already in `map` needs no TF lookup at
> all, so a wrong Fixed Frame is silent until it isn't. `nav.rviz` ships with
> `Fixed Frame: map` and `make rviz` loads it; it had been changed — most
> likely during the Day 3 drive, before a map existed. **Fix: set Fixed Frame
> back to `map`. No code change.**
>
> The signature to recognise: `planner_server: Could not transform the start or
> goal pose in the costmap frame`, with the requested time **pinned** at one
> value across every retry while "earliest data" marches forward. The BT keeps
> the original goal on its blackboard and replans at 1 Hz **keeping the
> original stamp**, so the first ~10 s of plans succeed — the robot starts and
> moves briefly and looks fine — and then every replan fails forever.
>
> ⚠ **Do not read the printed gap as the TF buffer depth.** "earliest is 1.34 s
> after requested" does **not** mean the buffer holds 1.3 s. It holds a healthy
> **10 s** — measured on this board 15 Sep. The printed gap is
> `request_age − 10 s`, so those requests were **~11 s stale**. `map → odom`
> itself measured clean at the same time: 46.1 Hz, zero backwards steps, stamps
> +70 ms. Chasing `transform_tolerance` or `tf_buffer_duration` is chasing the
> wrong number.
>
> **2. The Spin recovery can never succeed — arithmetic, not drift.** Upstream's
> BT hard-codes `<Spin spin_dist="1.57"/>` and leaves `time_allowance` at its
> **port default of 10.0 s**; at `max_rotational_vel: 0.1` rad/s, 1.57 rad needs
> **15.7 s**. Measured: `Turning 1.57` → `Exceeded time allowance` at exactly
> **10.000 s**, four times out of four. `time_allowance` is a **BT port, not a
> ROS parameter**, so this is unfixable from `nav2_params.yaml`.
>
> ✅ **FIXED AND BUILT** — `my_bot/behavior_trees/navigate_to_pose_w_replanning_and_recovery.xml`
> with `time_allowance="25.0"`, selected by `bt_navigator.default_nav_to_pose_bt_xml`.
> **D-21.** The `$(find-pkg-share my_bot)/...` form was *verified* to resolve
> (it works only because `nav2_bringup` wraps the params in
> `ParameterFile(allow_substs=True)`). `max_rotational_vel` deliberately left at
> 0.1, below DWB's `max_vel_theta`.
>
> **To re-run the gate: restart `make nav` ONLY.** `make real` and `make slam`
> must keep running or the Day 3 map is lost from `slam_toolbox` and Nav2 has
> nothing to plan on. Numbers in `records/calibration.md` "Day 4 gate — first
> attempt"; both symptoms in the index under **Nav2**.

> **Day 6 desk work, 14 Sep — Track B: `semantic_objects` rebuilt as a package in `cap_ws`, all nine fixes in, 139 tests green, bridge and UI running on the Jetson. Two geometry defects the checklist did not know about are fixed (mirrored scan window, wrong range origin), and the camera is on the RIGHT — `camera.xacro` corrected. Day 5 gate passed earlier today. Day 3, 4 and 6 gates all need the robot: Day 6's needs a chair and a tape first (no driving), then the drive-past.**

> **Day 6 at a glance (14 Sep).** `cap_ws/src/semantic_objects/` — node,
> `launch/semantic.launch.py`, `config/robot_params.yaml`, `clear_landmarks`
> service, 28 new tests. `make semantic` · `make bridge` · `make ui` in the
> `cap_ws` Makefile; `make test` runs the 139 unit tests. Verified on the desk
> with `robot_state_publisher` alone: intrinsics read from `c615_640x480.yaml`
> (fx 667.874), camera (+0.050, −0.030) and lidar (−0.034, 0) from TF, bridge
> `ros_connected: true`, `POST /api/clear` reaches the node, Vite answers at
> `http://192.168.160.106:3000/`. **Next, needs a person but no driving — the
> stationary bench check:**
> ```
> make real · make slam · make yolo · make semantic          # four terminals
> ros2 run my_bot landmark_tape_measure.py chair --truth X Y # chair 20-25 deg OFF-AXIS, taped
> ```
> Expect one landmark within 0.25 m; move the chair to the other side and it
> must follow. A centred chair cannot reveal a mirror or a camera-side error.
> Then the Day 6 gate proper (drive past, marker stays, browser shows it) with
> the Day 3/4 drive. Records: `records/calibration.md` "Semantic fusion",
> D-19/D-20, symptom index "Semantic layer" and "Bridge and UI".

> **Day 5 at a glance (14 Sep).** `scripts/yolo_detector.py` + `launch/yolo.launch.py`
> + `scripts/detection_report.py` (the gate tool), all in `cap_ws`. `yolo26n.pt`
> straight from torch, fp16, no TensorRT engine and none needed: 44.5 ms p50
> inference+tracking inside a 66.7 ms frame, GPU at its 306 MHz floor clock the
> whole run. Track ids proven on a still image (5 ids, 893/893 frames) and then
> **on the real camera: one cup, id 1 in 457/457 frames** (user, 30 s run).
> Day 6 can start on Track B. The gate tool for any re-check:
> ```
> make yolo                                             # terminal 1
> ros2 run my_bot detection_report.py --seconds 300     # terminal 2
> ```
> Numbers in `records/calibration.md`; symptom entries under "Day 5 detector".
> ⚠ The `lap` package was missing from the venv and ultralytics pip-installed it
> at first `track()`; `setup_yolo_venv.sh` now installs it and the launch sets
> `YOLO_OFFLINE=1` so that can never happen silently on demo day.

> ⛔ **Multi-machine ROS 2 stopped working — found 11 Sep.** Both machines left
> the hotspot and are on **different subnets** (Jetson `192.168.160.106/22`
> wired, laptop `10.0.144.205/16` wifi), while both DDS peer lists still name
> the dead `172.20.10.2` / `172.20.10.5`. The laptop sees **none** of the
> robot's topics. **RViz on the laptop is unusable until this is re-run on both
> machines** — `reference/ros2-network.md` has the two commands. Until then run
> RViz on the Jetson.

> **The reported RViz rubber band: three of four causes are eliminated, on this
> board, stationary.** One process each of `ros2_control_node`,
> `robot_state_publisher` and `slam_toolbox`; `map → odom` 50.1 Hz and
> `odom → base_link` 30.0 Hz, both exactly their configured rates; zero
> backwards stamps anywhere; `/scan` age 88.4 ms **sd 1.1 ms**; laptop clock
> 10.3 ms off. **What is left is the scan matcher fighting odom, and that can
> only be measured while driving:**
> `ros2 run my_bot check_pose_stability.py --seconds 30`.
> Baseline numbers in `records/calibration.md`; the four causes and what each
> looks like are in the symptom index.
>
> ✅ **The config review for (3) is done and applied — D-18, 11 Sep evening.**
> The matcher had a ±25 cm / ±20° search window per keyframe with an odometry
> penalty of 0.95 at the window edge — odometry had no effective vote, against
> a measured ~1 cm / ~0.01° of odom error per 0.2 m keyframe. Now ±15 cm /
> ±10° with `distance_variance_penalty` 0.1 and `angle_variance_penalty` 0.2
> (verified against the humble-branch `Mapper.cpp`: the penalty is
> `1 − 0.2·d²/p²` and the setter squares `p`). **Odometry covariance was
> confirmed a red herring** — slam_toolbox reads TF, not `/diff_cont/odom`.
> Also added a **hard velocity ceiling in `diff_cont`** (0.15 m/s, 0.5 rad/s)
> so a stray `q` can never reproduce the 10 Sep shear. Rebuilt; installed
> copies verified; committed and pushed as `cap_ws` `257d4f1`. Both are untested on a moving robot: the next driving session
> is the test.
**Current day:** **Day 7.** Gates 1–6 are all passed as of 16 Sep; the committed
demo (drive · map · Nav2 goal · live semantic markers) is complete end to end.
Day 7 is measure · rehearse · write.
~~**Multi-machine ROS 2 is up (9 Sep)**~~ **DOWN since 11 Sep** — see the banner above. Until it is re-run on both machines, **RViz runs on the Jetson's HDMI display** (`:0`, confirmed present). `reference/ros2-network.md` and D-16.
**Blocked on:** nothing technical — **the two remaining items both need the
robot driven**, which needs you: §1(c) `calibrate_spin.py`, then the closed
loop for the gate. ~~building `ydlidar_ros2_driver`~~ **resolved 9 Sep.**

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

**Next action:** two driving tasks, in this order. Both need a person: the
robot moves, and **`make teleop-nav` is the e-stop** (real again as of 10 Sep).

> **The `wheel_separation` item that used to head this list is done** — settled
> 10 Sep by inverting the formula, no driving required. See the callout below.
> Day 3's gate is now **only** the closed loop.

1. ~~**`calibrate_spin.py --turns 10`, and NOTE THE DIRECTION.**~~ ✅ **DONE
   10 Sep, without driving.** See the settled callout below. Kept for the
   reasoning, which still applies to any future spin:

   > **The old two-direction decision rule is retired — read this before
   > driving.** It expected a reverse run to separate a separation error from a
   > wheel asymmetry by sign. That reasoning is wrong: in a spin the wheels
   > counter-rotate, so a per-wheel radius error enters yaw with the *same* sign
   > on both sides and **cancels**, surfacing as the robot's centre translating
   > rather than as residual heading. A reverse run would not have
   > discriminated.
   >
   > **It no longer needs to.** The asymmetry was measured and applied on 9 Sep
   > (`1.002982` / `0.997018`) and verified the same day at ~0.1° of heading
   > change over 3 m. With that removed, **a spin residual now reads separation
   > cleanly** — one run, either direction, settles it. Record the direction
   > anyway.

   Any future change goes into **both** `my_controllers.yaml` and
   `robot_core.xacro` (`wheel_separation = 2 × wheel_offset_y`), then rebuild.

1. **Drive the closed loop** — slowly, at a **constant ~0.10 m/s**, then
   `make save-map MAP=~/maps/day3-reference`. **This is the Day 3 gate**, and
   now the only thing standing between here and Day 4's.

   > **Run `check_pose_stability.py --seconds 30` in a fifth terminal during
   > the first minute of driving (D-18).** Read the `map -> odom CORRECTION`
   > section: total path of the correction close to the net means the matcher
   > is quiet and odom is trusted. Total path far above net means it is still
   > fighting → next step is `distance_variance_penalty: 0.05`, not a wider
   > window. Pose steady but walls elongated → shear → speed, which the new
   > controller ceiling of 0.15 m/s should now make impossible from teleop.
   > First thing to confirm on bring-up: `ros2 param get /diff_cont
   > linear.x.max_velocity` → 0.15, and that `make teleop-nav` still drives.

   > ⚠ **Do not touch `q` during the run.** `teleop_twist_keyboard`'s `q`
   > raises speed **permanently** until `z` lowers it, and the current value is
   > shown only in the teleop terminal — which nobody is watching while looking
   > at RViz. The 10 Sep attempt was driven at 0.10 "except for a moment" and
   > the map smeared on straight sections; `~/maps/day3-reference` from that run
   > is kept as a file but is **not** a valid gate artefact.
   >
   > **A brief fast segment is not brief in its effects.** Sheared scans enter
   > the pose graph, and optimisation can move a scan's pose but cannot un-shear
   > the scan, so the doubled wall stays drawn. Start from a fresh `make slam`.
2. **Then Day 4 §3:** RViz `2D Goal Pose` → arrives and stops; block it with a
   chair → recovery behaviours fire. **That is the Day 4 gate.**
3. ~~**Track B — camera intrinsics.**~~ ✅ **DONE 11 Sep, and validated against
   a tape measure.** Installed at `my_bot/config/c615_640x480.yaml`:

   **fx 667.874 · fy 669.846 · cx 321.569 · cy 234.502**
   reprojection **0.3403 px**, focus **locked at 51**. 80 images captured, refit
   on the 59 at or beyond 0.30 m — `make calib-report` takes `--min-depth` for
   exactly this. **Tape-checked twice, both PASS**; pooled tape estimate 668.6,
   installed value −0.11% from it.

   > ⚠ **Do not quote the tape to better than a couple of percent.** Two runs of
   > three stations returned `fx_true` **664.87** and **672.36** — 1.1% apart,
   > because `SE(slope) = σ/√Sxx` is **±2.6%** at that span and scatter. The
   > ±2% gate the script shipped with was tighter than its own precision and has
   > been corrected: it now reports σ, span, SE and dof, widens the tolerance to
   > its own 2σ, and defaults to **six stations out to 1.5 m** (SE ±1.2%).
   >
   > **What the tape settles beyond doubt is the ~51° vs ~62° question** — a 20%
   > error is eight sigma. What it cannot do is choose between 667.87 and
   > 672.65. The refit is installed on the strength of **`cx`**, not the tape.

   > **The trim was worth it for `cx`, not for the RMS.** It moved 331.19 →
   > 321.57, and `cx` biases *every* bearing by a constant: 9.6 px at fx 668 is
   > **0.82° of systematic pointing error** taken out of every landmark. Do not
   > trim further — the 0.35 m cut scores better still and throws `cx` out to
   > 308.4. Trimming is not monotonic and the RMS will not tell you where to
   > stop.

   > **The ~62° HFOV this project assumed was wrong.** The camera is **~51°** —
   > 50.9° from the calibration and 51.4° from the tape, independently. The 62°
   > in `reference/hardware-inventory.md` was a pre-dump guess, now corrected,
   > and `camera_calib_report.py`'s reference value with it. **Anything still
   > assuming ~62°, or `fx` near the node's `554.0` default, is ~20% wrong.**

   > **Autofocus was the whole problem, and the numbers close the loop.** The
   > first attempt (AF on) passed the gate at 0.3651 px and was wrong: split by
   > capture order it gave fx **819.74** (first 29) against **676.30** (last
   > 19). That `676.30` — the frames after the lens settled — sits alongside the
   > focus-locked **672.65** and the tape's **664.85**, all inside 1.7%. The
   > outlier was the AF-hunting, depth-degenerate opening. **`make camera` now
   > locks focus; use the same `FOCUS` for the demo as for the calibration.**

   > **Still outstanding, and it is Day 6 work, not Day 4:** the semantic node's
   > built-in `554.0` intrinsics must be **deleted** when the September
   > `semantic_objects` tree is rebuilt, so a missing params file fails loudly
   > instead of quietly mapping the room 20% off. The only surviving copy is the
   > June-era `semantic-object-ros/semantic_objects/semantic_objects_node.py`
   > lines 144–145, which is reference-only and does not run.

> **The 0.2325 prediction is dead.** Day 2's eyeballed 90° implied a 7 % yaw
> error; ten machine-counted turns say **0.61–0.67 %**, and in the opposite
> direction. The eyeball was the error — which is exactly why that prediction
> was written down as a prediction and not applied.
>
> ⚠ **But "0.25 was right" — an earlier version of this line — is also wrong.**
> 0.25 is 0.67 % low, worth 2.4° of yaw per full turn. The eyeballed 7 % was
> badly wrong about the *size*; it was not wrong that there was something to
> correct. Settled value is **0.25168**.

**The network is off the critical path now.** RViz can run on the laptop
instead of on the Jetson, which frees the Orin's GPU during the driving tasks
above and means the robot no longer needs a screen on it.

```bash
# laptop, in its own terminal
rviz2 -d ~/cap_view/nav.rviz
```

> **The stale-stack warning below still applies, and the four Makefile
> terminals still run on the Jetson.** Only RViz moves.

> ⚠ **`ROS_DOMAIN_ID` is now 42, not 0.** Both machines have it exported from
> `~/.bashrc`. Anything launched from a stripped environment — a systemd unit,
> a container, `env -i` — will land on domain 0 and see nothing. This is the
> first thing to check if a node that used to work goes silent.

**✅ The speed prediction held (9 Sep, evening).** The map smeared when driven
forward at teleop's 0.5 m/s and came out **clean at 0.10 m/s** over the same
floor. It was motion shear; `reversion` is exonerated and stays `true`. Nothing
to calibrate for it — **map at Nav2 speeds or slow teleop down.** The original
reasoning, kept because it is the diagnostic: `make teleop` starts at **0.5 m/s** and nothing clamps
it — the `nav2_params.yaml` limits are the robot's only velocity limit and they
are not running during manual driving. Measured on the live stack: 86 ms sweep,
`header.stamp` already 88 ms old at receipt, so **8.7 cm of shear per scan at
teleop speed** against 1.0 cm at Nav2's 0.055 m/s. A spin smears about the
sensor origin and `slam_toolbox` absorbs it into its ±20° yaw search;
translation shears along the path and no rigid transform can absorb it.

~~**`reversion` produces the same asymmetry and is the other suspect.**~~
✅ **ELIMINATED 11 Sep.** `reversion: true` is now verified on this board with
`check_scan_bearing.py`: an object placed in front of the robot read
**+1.5 / −0.5 / +2.6°**, i.e. ~0°. A wrong `reversion` would have put it at
180°. `inverted: true` was settled in the same session — an object at the
robot's **left** read **+91.3 / +89.2°**, where a wrong `inverted` mirrors it
to −90°. **Both flags are measured now, not inherited.**

**The test settles both**, and it is the run that was wanted anyway:

```bash
ros2 run my_bot calibrate_straight.py --distance 3.0   # drives at 0.10 m/s
```

Watch RViz during it. **Clean at 0.10 m/s → speed, nothing to calibrate.**
Still smeared → `reversion` next, then real odometry curvature. Mark the floor
as well as the distance: the offset off the chalk line is the encoder-split
measurement and the run only gives it once.

> The map built at 0.5 m/s is not evidence. Discard it.

> ✅ **`wheel_separation` is SETTLED (10 Sep) — 0.25168 stays, and no driving
> was needed.** `calibrate_correct.py`'s formula is one-parameter, so the
> installed value inverts back to the reading that made it:
> `0.25 × 3600.32/(3600.32 − 24.0) = 0.25168`, against
> `0.25 × 3600.32/(3600.32 − 22.0) = 0.25154`. **Both are the same 9 Sep run** —
> same odom reading, same starting 0.25 — with the floor residual read as −24°
> when it was applied and −22° when it was written down. Nothing else fits
> either number.
>
> **Kept at 0.25168.** The gap is 0.14 mm / 0.056 %, worth 0.05° of yaw over a
> 90° turn and 0.20° over a full rotation — below the precision of reading a
> chalk mark after ten turns. Churning it would record noise as a calibration,
> the same reason `wheel_radius` stayed 0.0327.
>
> **What is resolved is that 0.25 was wrong:** both readings put the separation
> 0.61–0.67 % high, i.e. 2.2–2.4° of yaw per full turn. The correction is real;
> the fifth decimal is not. Full derivation in `records/calibration.md`.
> Committed in `cap_ws` `db32d88`, paired with `wheel_offset_y: 0.12584`.

> ✅ **`make teleop-nav` IS the e-stop again — restored 10 Sep.** The rule has
> flipped back. `navigation.launch.py` and `nav2_params.yaml` are ported, all
> seven Nav2 lifecycle nodes reach `active`, `twist_mux` runs, and
> `/cmd_vel_teleop` has subscribers where it had none. Use `make teleop-nav`,
> **never `make teleop`**, during any autonomous run.
>
> ~~`make teleop-nav` is NOT an e-stop yet — found 9 Sep.~~ Kept as history:
> nothing in `cap_ws` started `twist_mux`, and because `config/twist_mux.yaml`
> and the `package.xml` dependency were both already present, the gap was
> invisible. That is the failure mode to remember, not the fix.
>
> ⚠ **Two live-graph findings that qualify it** — both in
> `records/calibration.md` and the symptom index:
> - **Recoveries bypass the `velocity_smoother`.** `behavior_server` publishes
>   straight onto `/cmd_vel`, so the smoother's `[0.055, 0, 0.125]` does not
>   clamp them; `behavior_server.max_rotational_vel: 0.1` does, and `BackUp` /
>   `DriveOnHeading` take speed from the BT goal and are not clamped by params
>   at all. Relevant to the Day 4 gate, which deliberately provokes a recovery.
> - **`/cmd_vel_teleop` has two subscribers**, `twist_mux` and
>   `behavior_server` (it is `AssistedTeleop`'s input topic). The e-stop is
>   unaffected; the topic is simply not exclusively ours.
>
> **`make teleop-nav` now starts at 0.10 m/s, not 0.5** (`SPEED` in the
> Makefile). 0.5 is what smeared the Day 3 map. `k` still stops the robot at any
> speed.

**That run also found a real wheel asymmetry, and it is APPLIED (9 Sep).**
Odom reported 0.9 mm of lateral drift over 3 m; the robot finished **10.9 cm
right** of the line. The loop steers on odom, so that gap is pure odometry bias:
**4.07° over 3 m, a 0.60 % asymmetry.** Now in `config/my_controllers.yaml` as
`left_wheel_radius_multiplier: 1.002982` / `right_wheel_radius_multiplier:
0.997018`, built and loaded.

**✅ Verified same day.** Re-run landed at **~0.1° of heading change** against a
predicted **−0.090°** — the yaw bias is corrected. The run also finished 8 cm
*left* of the line, but that is **not curvature**: an arc reaching 8 cm over 3 m
needs 3.06° of heading change and the run shows ~0.1°. A 1.53° error in the
lateral reference produces exactly 8 cm with zero heading change, and the setup
aligned the *wheel axis* to a grout line — which fixes heading but not the
centreline reference. **Multipliers left as installed**; the residual is inside
what `slam_toolbox` absorbs. **Odometry is good enough for the gate — go drive
the loop.**

`wheel_radius` was **deliberately left at 0.0327**. The same run suggests
0.03264, but that correction is 5.2 mm over 3 m and the distance was *counted as
five 600 mm floor tiles*, not taped — grout makes tile pitch vary by more than
the correction. Re-derive over a longer taped run if map scale ever looks wrong.

> ⚠ **The Day 3 decision rule for `wheel_separation` looks wrong, and it is
> about to cost a driving session.** It expects a reverse-direction spin to
> separate a separation error from a wheel asymmetry by sign. But in a spin the
> wheels counter-rotate, so a per-wheel radius error enters yaw with the same
> sign on both sides and **cancels** — it surfaces as the robot's centre
> translating, not as residual heading. A radius asymmetry should therefore
> **not** flip sign with spin direction, and the reverse run should return
> ≈0.61 % again rather than discriminating. **Check this reasoning before
> driving it.** Clean decomposition: straight run → asymmetry (from lateral)
> and mean radius (from tape); spin → mean radius × separation.

Worth doing in the same session, both quick:
`check_scan_world_fixed.py` (turns ~90° in place, needs clear space), and
re-run `scan_dropout_report.py` **in the room the map is made in**.

> ~~⚠ **A `make real USE_LIDAR=false` stack from the Day 2 session was still
> running at 17:18** (pids 3299/3317/3319).~~ **Gone — checked 9 Sep, no ROS
> processes are running on the Jetson.** The reason it mattered stands: two
> drivers cannot share `/dev/ydlidar` and
> `use_lidar` now defaults to `true`, so check before `make real`. Clean start:
>
> ```
> make real           # base + lidar, USE_LIDAR is no longer needed
> make slam           # second terminal
> make rviz           # third -- or rviz2 on the laptop instead
> make teleop-nav     # fourth -- the e-stop
> ```

**Day 3 §2 and the SLAM config are done (9 Sep).** `ydlidar_ros2_driver` builds
and runs, `/scan` is live at **11.57 Hz**, `/map` publishes 162×249 @ 0.05 m,
`map → odom` appears, and all eight TF edges resolve. `laser_frame` lands
**0.220 m** above `base_footprint`, matching the tape.

> ✅ **Both flags in `config/ydlidar.yaml` are VERIFIED ON THIS BOARD (11 Sep)**
> and stay `true` — `reversion` and `inverted`. Method and readings are in
> `records/calibration.md`; the values are annotated at the point of use in
> `ydlidar.yaml`.
>
> The tool is **`check_scan_bearing.py`**, written 10 Sep because nothing
> existing could do it. `check_scan_world_fixed.py` rotates the robot and only
> catches `inverted`; a scan rotated by π is still world-fixed under rotation,
> so it is blind to `reversion`, whose only symptom is that driving *forward*
> smears the map. The static bearing test catches both in thirty seconds with
> the robot stationary — an object in front separates `reversion`, one at the
> robot's left separates `inverted`.

> ⚠ **The recovered dropout figure was wrong twice, and this is the kind of
> number the whole project exists to stop re-deriving badly.** It is **350 rays
> per scan, not 400** (the driver prints `Single Fixed Size: 350`;
> `angle_increment` 1.032° agrees) and **27.9 % dropout, not ~50 %**. Worse, the
> average is misleading: 5–28 % on the robot's right against 46–70 % on its
> left, because a bearing with nothing inside `range_max` 12 m returns `0.0`,
> indistinguishable from a real dropout. **27.9 % describes this corner of this
> room.** Re-measure where the map is made. If the left-side deficit follows the
> robot instead of the room, it is chassis clipping or a glazed surface — worth
> knowing before Day 6 blames the camera.

**Day 2 gate passed 9 Sep.** `make teleop` drives the robot and `i` is forward.
Both controllers active, both command interfaces claimed, `/joint_states` and
`/diff_cont/odom` each at exactly 30.0 Hz, all seven TF edges resolving.

Hand-push odometry, via `odom_check.py`:

| Move | Odom said | vs nominal |
|---|---|---|
| ~1 m straight | **0.980 m**, yaw change −0.1° | −2.0 % |
| ~90° in place | **−83.7°**, drift 0.9 cm | −7.0 % |

**The decoupling is the real result** — distance with no yaw, yaw with no
distance. That is what proves the encoder signs and the kinematics, and it is
the thing a swapped encoder would break loudly.

> ~~**A prediction for Day 3.**~~ **Settled 9 Sep: it did not hold.** The 7 %
> shortfall implied `wheel_separation` ≈ 0.2325; `calibrate_spin.py --turns 10`
> measured **0.61 %** the other way, implying **0.25154**. The eyeballed 90° was
> the unreliable part. **0.25 stands**, pending the reverse-direction run.
>
> ⚠ **The Day 2 checklist's odom test is wrong as written.** "Push 1 m → `/odom`
> x increases by 1 m" only holds if the robot starts aligned with odom's x-axis.
> Ours sat 26.7° off it, so x rose 0.875 and y rose 0.441 — **straight-line
> distance is the check**. Also: the topic is **`/diff_cont/odom`**, not
> `/odom`; echoing `/odom` shows nothing and looks exactly like a dead
> controller.

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
| 2 | `make teleop` drives the robot; `/odom` changes sanely; TF tree has no gaps | **[x] PASSED 9 Sep.** Teleop drives, `i` is forward; 1 m push → 0.980 m; 90° turn → −83.7°; 7 TF edges resolve; 30.0 Hz. Track B finished `day-5-yolo.md` §1 as well |
| 3 | A driven loop closes without a visible double wall | **[x] PASSED 15 Sep.** Loop driven at 0.10 m/s; `~/maps/day3-reference` saved 17:16, 271×488 @ 0.05 m, origin [−6.82, −9.80]. Supersedes the invalid 10 Sep file. `wheel_separation` settled 10 Sep at 0.25168 |
| 4 | RViz goal → robot arrives; recovery behaviours fire when blocked | **[x] FULLY PASSED — goal clause 15 Sep, recovery clause 16 Sep.** 3 goals, 3 successes, no stale-frame timeouts. ~~The recovery clause has no log evidence.~~ **`/spin` SUCCEEDED 16 Sep in 16.4007 s** (1.5762 rad vs 1.57), so D-21 is executed and proven; the stiction risk it flagged is disproven at the same `max_rotational_vel: 0.1`. ~~ATTEMPTED AND FAILED earlier that day, 4 goals.~~ Two causes, both proven: goals sent in the `odom` frame (RViz Fixed Frame — set it to `map`), and Spin's `time_allowance` 10 s against the 15.7 s the spin needs (**fixed, D-21**). Both fixes confirmed by the re-run |
| 5 | `/detections` stable; track IDs persist; no thermal throttle | **[x] PASSED 14 Sep.** 15.15 Hz sd 5 ms over 301 s; tj max 44.6 °C over 301 s (52 °C later in the evening); versions recorded; **one cup → id 1 in 457/457 frames** on the real camera |
| 6 | Labelled marker appears at roughly the right place and stays; UI shows it | **[x] PASSED 16 Sep.** Bench check: error **0.08 m**, spread 0.04, duplicates 1, fused 94.3 % at 1.64 m. Drive-past: marker persisted after driving away; browser shows it; fused **~45 %** (all rejections `max_spread`, chair too close — below Day 7's 0.6 target, back the robot off). ⚠ RViz markers still unconfirmed (a §3 item, not a gate clause) |
| 7 | Three clean end-to-end rehearsals; tape-measure numbers recorded | [ ] |

## Track status

| Track | Scope | Where |
|---|---|---|
| **A** — needs the robot | foundation → drive → odometry → SLAM → Nav2 | Day 1 done, **Day 2 done**. **Day 3 part done**: lidar driver built, `/scan` live, SLAM running. **Day 4 §1 done 10 Sep** — Nav2 ported, all 7 lifecycle nodes active, e-stop restored. Remaining is all driving — `wheel_separation`, the loop, then goals |
| **B** — needs only Jetson + camera | uv env → calibration → detector → fusion | **DONE through Day 6's build.** Venv (Day 2), intrinsics (11 Sep), detector + gate (14 Sep), `semantic_objects` + bridge + UI (14 Sep night). Track B is finished; what remains on Day 6 needs the robot on the floor with the lidar up |

Track B runs in the gaps of Track A. Start it Day 2, not Day 5 — it is the
highest-variance item in the week and it needs no robot.

---

## Network

> ⚠ **The Jetson's address moved again — read 15 Sep: `enP8p1s0` is
> `10.228.103.105/24`.** Not the `192.168.160.106` recorded below, and not the
> `172.20.10.2` in the tables further down. **Nothing in this file is a valid
> address; re-derive with `ip -4 addr` every session.**
>
> **Consequence for Day 6/7, not for Day 4:** `semantic-object/semantic_map_ui/.env`
> is currently uncommitted and set to `VITE_BACKEND_URL=http://172.20.10.2:8000`,
> which is two addresses out of date. Vite bakes it in at start, so it must be
> corrected and `make ui` restarted before the browser will ever show a
> landmark. Left uncommitted deliberately — committing an address is the
> mistake this box exists to prevent.


Set up 9 Sep, verified both directions. **`reference/ros2-network.md` is the
full account**; this is the quick-reference mirror. Reproduce with `make net`.

| | Jetson (robot) | Laptop (viewer) |
|---|---|---|
| user@address | `mic-711@`**`172.20.10.2`** | `ju@`**`172.20.10.5`** |
| hostname | `ubuntu` | `ju-hp-probook-laptop` |
| interface | `enP8p1s0` | `wlp0s20f3` |
| runs | `make real` / `slam` / `nav` / `teleop-nav` | `rviz2 -d ~/cap_view/nav.rviz` |
| firewall | none (ufw inactive) | **ufw active** — first suspect on one-way discovery |

`ROS_DOMAIN_ID=42` · `ROS_LOCALHOST_ONLY=0` ·
`FASTRTPS_DEFAULT_PROFILES_FILE=~/.ros2/fastdds_hotspot.xml` on both.
SSH is key-based Jetson → laptop, no password.

> ⚠ **`172.20.10.2` is the Jetson, not the laptop.** It was handed over as the
> "remote" address and is not; there is no `ju` account on the Jetson. Both
> addresses are `172.20.10.x` and neither hostname says which is the robot.

> ⚠ **These are DHCP addresses on a phone hotspot, and the DDS peer list is
> literal.** Nothing detects a change; discovery just stops. After any
> reconnection: `ip -4 addr` on both, then, if either moved, re-run on **both**
> — `make net PEERS=<jetson>,<laptop>` on the Jetson and
> `~/cap_view/setup_ros2_network.sh --peers <jetson>,<laptop>` on the laptop.
> This is the network equivalent of the `ttyUSB` swaps below — do not cite an
> address, re-derive it.

> **`make net` is Jetson-only.** The laptop has no `cap_ws` and no Makefile, by
> design — it needs nothing built. `make viewer-sync` pushes `nav.rviz`,
> `setup_ros2_network.sh` and `check_ros2_link.py` into `~/cap_view/` on it;
> those are copies, so re-run it after editing any of the three.

Measured 9 Sep with `check_ros2_link.py`, Jetson → laptop over 15.1 s:
**String 10.07 Hz of 10** and **40 kB OccupancyGrid 1.99 Hz of 2**, no loss —
so `/map` crosses without socket-buffer tuning.

---

## Devices

Fill in as soon as §5.1 is done. These die with the board every time.

**Neither adapter has a unique serial** — confirmed from the recovered rules.
Both were matched by USB port path. This carrier has different USB topology, so
**the recovered paths do not transfer. Re-run `make udev`.** (The audit blamed
"the Advantech carrier"; `jetson_release` calls this an Orin NX Engineering
Reference Developer Kit. The conclusion held, the stated reason may not.)

Confirmed still present 9 Sep: `/dev/esp32 → ttyUSB0`, `/dev/ydlidar → ttyUSB1`.
**Re-checked 17:00 the same day and they had swapped again** — `/dev/esp32 →
ttyUSB1`, `/dev/ydlidar → ttyUSB0`. Nothing was unplugged; the enumeration order
simply differed across a restart. Both stable names still resolved to the right
adapter, which is the udev rules doing exactly their job. This is the third
recorded swap.
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

**Do not read `ttyUSB` numbers as identity.** They have now swapped twice:
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
| `wheel_separation` | **0.25168** m | ✅ **settled 10 Sep.** 9 Sep spin run, residual −24°. Installed, committed, = 2 × `wheel_offset_y` 0.12584. Recovered 0.25 was 0.67 % low |
| `wheel_offset_x / _y` | **0.255 / 0.125** m | recovered |
| Lidar height above ground | **0.22** m | recovered |
| `laser_frame` in `base_link` | **(−0.034, 0, 0.186)** | recovered |
| **Lidar model** | **YDLidar X3 Pro** | ⚠ **corrected 11 Sep** — every doc said X2. No software route to the model; read the label |
| X3 Pro rays per scan | **350** | **measured 9 Sep** — recovered "400" was never counted. `m_FixedSize` is measured, not configured |
| X3 Pro `range_max` | **8.0** m | ⚠ **corrected 11 Sep** from 12.0, which was the X2's. Propagated to slam, Nav2 and the Gazebo sensor |
| X3 Pro `range_min` | **0.12** m | corrected 11 Sep from 0.1 |
| X3 Pro sample rate | **~4.07K** | **measured 11 Sep** — SDK prints 4.57K, less its +0.5 rounding term. X2/X3 are 3K; this is what flagged the model |
| X3 Pro dropout fraction | **~19%** of 350 rays | measured 11 Sep. ⚠ **Position dominates** — 27.9% (9 Sep), 25.7% (10 Sep), all different spots. Not a trend, and NOT the range fix |
| X3 Pro dropout, worst sector | **43.8%** at −15° AHEAD | measured 10 Sep — was +75° LEFT at 69.6% on 9 Sep |
| X3 Pro left-side deficit | ✅ **was the room, not the sensor** | settled 10 Sep — it did not follow the robot |
| X3 Pro measured rate | **11.57–11.60 Hz** | **confirmed 9 and 11 Sep**; config's `frequency: 10.0` is not what it does |
| Longest return seen | **6.30 m** | measured 11 Sep — the room is smaller than either range rating, so the 8 vs 12 m fix shows nothing here |
| `reversion` flag | **true** | ✅ **verified on this board 11 Sep** — front object read ~0°, not 180° |
| `inverted` flag | **true** | ✅ **verified on this board 11 Sep** — left object read ~+90°, not −90° |
| `camera.fx` | **667.874** | ✅ calibrated 11 Sep — this row was stale until 14 Sep |
| `camera.fy` | **669.846** | ✅ calibrated 11 Sep |
| `camera.cx` | **321.569** | ✅ calibrated 11 Sep |
| `camera.cy` | **234.502** | ✅ calibrated 11 Sep |
| camera `dx` (forward of axle) | **+0.050** m | **measured 9 Sep**, tape |
| camera `dy` (left of centre) | **−0.030** m — the camera is on the **RIGHT** | magnitude 9 Sep; ✅ **side confirmed by the user 14 Sep**, `camera.xacro` corrected the same day |
| camera `dz` (above floor) | **0.20** m | measured 9 Sep |
| camera pitch | **−0.0524** rad (3° **up**) | measured 9 Sep |
| torch / torchvision | **2.11.0 / 0.26.0** | JetPack cp310 aarch64 wheels, 9 Sep |
| CUDA / cuDNN / TensorRT | **12.6.68 / 9.3.0.75 / 10.3.0.30** | installed 9 Sep |
| YOLO detection rate | **15.15 Hz**, camera-limited | ✅ **measured 14 Sep on 6.1**, `yolo26n.pt` torch fp16, no engine; 44.5 ms p50 inference+tracking; tj max 44.6 °C over 301 s |

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
| `cap_ws` | [x] `mairuu/cap_ws` | [x] **pushed through `7e73c63`, 9 Sep** — Day 3 lidar + SLAM. Earlier: **`3383188`** — the whole `my_bot` port and `camera.xacro`. `~/cap_ws`, renamed from `capstone-ws` 8 Sep. Branch is **`main`**, matching the others (an earlier note said `master`; it is not) |
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
| 9 Sep | `ydlidar_ros2_driver` taken from the **`humble`** branch, not `master` | `master` is Dashing-era: `node_executable=` / `node_name=` in the launch files and one-argument `declare_parameter(name)`, which Humble deprecated and which throws with no override. `make lidar-deps` pins the branch and refuses a wrong checkout. |
| 9 Sep | `src/ydlidar_ros2_driver/` gitignored, not vendored | Pristine upstream checkout at `humble` `4ef70d3`; `make lidar-deps` reproduces it exactly. Vendoring buries a large upstream diff in our history for no gain. |
| 9 Sep | `nvidia-opencv` **not** installed | `checklists/day-5-yolo.md` §1 asks for JetPack's CUDA OpenCV; `cv_bridge` is built against Ubuntu's 4.5.4 and shadowing it six days out risks the image pipeline for no gain. **`cv2.cuda` is unavailable — reported limitation.** D-15. |
| 10 Sep | Day 4 §1 done **before** Day 3's gate, inverting the checklist order | Porting Nav2 is what starts `twist_mux`, and `twist_mux` is the e-stop. Driving Day 3's loop first would have meant driving with no software stop. Desk work, no robot needed, so it cost nothing to reorder. |
| 10 Sep | `nav2_params.yaml` ported wholesale; Day 4 §2's `robot_radius` rejected | The recovered file already *is* the derivation §2 asks for, annotated per-delta. `robot_radius` is forbidden by `CLAUDE.md` — the enclosing circle needs r≈0.30 against a 0.147 half-width and refuses doorways the robot fits. **D-17.** |
| 10 Sep | `make teleop-nav` defaults to `SPEED=0.10`, not teleop's own 0.5 | 0.5 m/s is what smeared the Day 3 map (8.7 cm of scan shear per sweep). The e-stop is unaffected — `k` sends zeros at any speed. Override with `make teleop-nav SPEED=0.3`. |
| 11 Sep | slam_toolbox matcher retuned to trust odometry; hard velocity ceiling added to `diff_cont` | Upstream matcher params let the scan matcher wander ±25 cm / ±20° per keyframe with no effective odometry penalty, against ~1 cm of measured odom error per keyframe. Nothing capped speed during manual driving. **D-18.** Untested while moving until the next driving session. |
| 10 Sep | Day 4 §4's camera commands replaced | Checklist says `usb_cam` / `/camera/image_raw` / `8x6` / `0.025`. All four are wrong post-dump: it is `cam2image` on `/image`, board is **9×6 / 20 mm**, and `--no-service-check` is required because `cam2image` offers no `set_camera_info` service. |
| 11 Sep | Day 4 §4 **rewritten in the file**, not only logged | The 10 Sep row above recorded the replacement but `checklists/day-4-nav2.md` still carried the `usb_cam` / `8x6` / `0.025` commands. Now rewritten, with `make camera` / `make calib` / `make calib-report` added to the Makefile so the corrected form is the one that runs. |
| 11 Sep | Two scripts added rather than walking the calibration by hand | `camera_calib_report.py` exists because `cameracalibrator` computes the reprojection error and discards it — the Day 4 gate is otherwise unmeasurable. `make_checkerboard.py` exists because a mis-scaled printout is invisible to that error. Working agreement: a bring-up step that needs a measurement gets a script. |
| 11 Sep | `reference/hardware-inventory.md`'s ~62° HFOV corrected to ~51° measured | Two independent measurements on this camera agree at ~51° and the spec figure was a pre-dump guess. It was not harmless: it fired a false "fx may be wrong" warning on two good calibrations, and it is the same 20% error carried by the node's `554.0` default. `camera_calib_report.py`'s reference is now the measured value, annotated as such. |
| 11 Sep | Focus lock folded into `make camera` rather than left as a checklist line | The C615 is varifocal and autofocus moves `fx`. A step that must hold identically at calibration time and at demo time is not a thing to remember — it belongs in the target that starts the camera. `FOCUS=auto` restores AF for anything that genuinely wants it. |
| 11 Sep | `make calib-scale` added; the Day 4 gate gains a second camera condition | Reprojection error cannot see a wrong `fx` — it is pixels against a self-consistent fit. The 11 Sep run passed at 0.3651 px while being 17.5% unstable internally. A tape measure is the only independent length available, so the gate now requires it. |
| 11 Sep | `/image/compressed` dropped as a Day 4 checkbox | It does not exist. `cam2image` uses a plain `rclcpp` publisher, not `image_transport`, so no transport plugin ever attaches — confirmed on the live node. Becomes a Day 6 decision: an `image_transport republish` node, or a different camera driver. |
| 14 Sep | Day 6 §1–§2 and §4 done **before** the Day 3/4/5 gates were all closed | Same Track B reasoning; desk work only. The gate itself is untouched. |
| 14 Sep | Intrinsics read from `c615_640x480.yaml`, not copied into `robot_params.yaml` | One copy of the numbers; a missing file is fatal. **D-19.** |
| 14 Sep | Projector intersects the camera ray with the lidar range circle | The June "camera + r·ray" was a 9 cm constant bias; the checklist did not list it. **D-19.** |
| 14 Sep | Extractor's scan window mirrored into lidar angles | Image-right vs lidar-left sign convention; not in P1–P8; 5 tests. |
| 14 Sep | `camera_offset_y` flipped to **−0.03** in `camera.xacro` | User confirmed the camera is on the right. Fixed in the URDF, never downstream, per the 9 Sep note. |
| 14 Sep | Bridge edited (scan QoS, map QoS, camera topic, CORS, `datetime.UTC`) | Interfaces did not match this robot; the landmark schema did and is untouched. **D-20.** |
| 14 Sep | Node 20 installed from NodeSource; UI served from the Jetson | User's choice; apt's Node 12 cannot run Vite 5. **D-20.** |
| 14 Sep | `landmark_tape_measure.py` written on Day 6, not Day 7 | The stationary bench check is a measurement; working agreement. |
| 14 Sep | Day 5 §2–§3 done **before** the Day 3 and Day 4 gates, inverting the checklist order | The detector needs only the Jetson and the camera (Track B by design, `RECOVERY.md`), while both open gates need a person driving the robot. Same reasoning as the 10 Sep Nav2 reorder: desk work that costs nothing to bring forward. The gates are still gates — Day 6's fusion is not started against them. |
| 14 Sep | D-11 closed on **B** (custom `vision_msgs` node), not A (`yolo_ros` + TensorRT) | Measured 15.15 Hz camera-limited from `.pt` alone — the same rate A was recorded at — so the lost patch, the dead engines and `yolo_msgs` would have bought nothing visible. Engine export stays a one-line escape hatch. |
| 14 Sep | Day 5's `imgsz 480` / `yolov8n` levers marked as not levers | Benchmarked: 480 is no faster than 640 (36.2 vs 34.9 ms), fp16 no faster on yolo26n. Pipeline is launch-bound at nano size. Recorded so nobody spends Day 6 pulling them. |
| 14 Sep | `detection_report.py` written instead of `ros2 topic hz` + `tegrastats` | The gate's four lines are four measurements (rate *and* jitter, id lifetimes, temperature trend, versions) and the checklist gave a tool for one of them. Working agreement: a step that needs a measurement gets a script. |
| 8 Sep | `cap_ws` created with only `Makefile` + `setup_udev.sh` | Day 1 needs no more than that. The rest of `my_bot` crosses over file by file on Day 2, re-verifying measured numbers as it goes (D-13). The recovered `99-my-bot-serial.rules` was **not** copied — its `KERNELS` paths are devkit-specific. |
