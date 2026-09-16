# STATE — where the work stands

> **Update this at the end of every session and whenever a gate passes.**
> Claude reads this first. If it is stale, Claude works from stale assumptions.

**Last updated:** 16 Sep 2026 — **`make yolo` now runs `yolo26s` as an fp16
`.onnx` (D-22), built on this board by `cap_ws/yolo/export_onnx.py`.** Desk work
done and benched; the venv gained onnxruntime-gpu 1.24.0 (the **Jetson** wheel).
**This re-opens three of the four Day 5 gate clauses** — they were evidence
about `yolo26n.pt` on torch, and both the weights and the backend changed. The
re-run is two terminals and a cup, no robot, no driving:
```
make yolo                                          # terminal 1
ros2 run my_bot detection_report.py --seconds 300  # terminal 2
```
Expect ~46 ms p50 in a 66.7 ms budget, i.e. still camera-limited. Numbers and
the caveat on them are in `records/calibration.md` "YOLO model swap"; the new
failure modes are in the symptom index under "ONNX model path".

**Previously, 15 Sep 2026, evening** — **DAY 3 AND DAY 4 GATES PASSED. Track A
is complete through Nav2.** The re-run with Fixed Frame `map` and the D-21
behaviour tree was clean: three goals, three successes, no stale-frame timeouts
(115.5 s / 31.8 s / 6.9 s; `bt_navigator_8618_1789465529679.log`).

> ⚠ **One clause of the Day 4 gate is ticked but not evidenced, and it is the
> half that matters on demo day.** "Recovery behaviours fire when you block it"
> has **zero `Running spin` lines** in the successful session's
> `behavior_server_8584_1789465529644.log` — against twelve in the failed
> attempt. No recovery ran, so **the D-21 Spin fix has never executed on this
> robot.** If the chair was replanned around without a recovery firing, that is
> good navigation and a weak test of the recovery path.
>
> **Close it in about a minute, no chair needed, with the stack up and clear
> space around the robot** — hand on `make teleop-nav`:
> ```
> ros2 action send_goal /spin nav2_msgs/action/Spin "{target_yaw: 1.57, time_allowance: {sec: 25}}"
> ```
> **`time_allowance` must be passed explicitly** — the CLI default is 0 s and
> Spin would fail instantly for the wrong reason. Expect completion in
> **15.7–16.5 s** at `max_rotational_vel: 0.1`. Two ways it can still fail, and
> they look alike: over 25 s means the fix is too tight; a robot that does not
> visibly turn at all means **stiction** — 0.1 rad/s is only ~151 encoder
> ticks/s per wheel, four times slower than the `BackUp` that succeeded every
> time at 0.05 m/s. That is the open question flagged in D-21.

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
**Current day:** Day 4 on Track A; **Day 5 PASSED and Day 6 built on Track B** — Day 6's gate needs the bench check, then the drive-past. §1 (Nav2 port) **done and verified**; Day 3's gate is
still the blocker and both remaining Track A items need the robot driven.
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
| 4 | RViz goal → robot arrives; recovery behaviours fire when blocked | **[x] PASSED 15 Sep on the goal clause** — 3 goals, 3 successes, no stale-frame timeouts. ⚠ **The recovery clause has no log evidence: zero `Running spin` lines in the session.** D-21 is therefore still untested on the robot. ~~ATTEMPTED AND FAILED earlier that day, 4 goals.~~ Two causes, both proven: goals sent in the `odom` frame (RViz Fixed Frame — set it to `map`), and Spin's `time_allowance` 10 s against the 15.7 s the spin needs (**fixed, D-21**). Both fixes confirmed by the re-run |
| 5 | `/detections` stable; track IDs persist; no thermal throttle | **[x] PASSED 14 Sep.** 15.15 Hz sd 5 ms over 301 s; tj max 44.6 °C over 301 s (52 °C later in the evening); versions recorded; **one cup → id 1 in 457/457 frames** on the real camera |
| 6 | Labelled marker appears at roughly the right place and stays; UI shows it | [ ] **Built and desk-verified 14 Sep**; bench check (chair, tape, no driving) and the drive-past are open. Everything pushed |
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
