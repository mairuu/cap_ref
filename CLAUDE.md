# CLAUDE.md — read this first, every session

You are helping rebuild a capstone robot on a Jetson Orin after the previous
processing board died and took the entire ROS 2 workspace with it. There is
roughly one week. This file is the standing brief; it does not change.

---

## Session start protocol

Do these four things before answering anything:

0. **Read `reference/nvme-recovery-audit.md`.** An NVMe dump recovered the whole
   `my_bot` package on 8 Sep. It supersedes the "definitively gone" list, and
   several earlier facts are now **wrong** (`/dev/lidar` → `/dev/ydlidar`,
   `usb_cam` → `cam2image`, checkerboard 8×6/25 mm → 9×6/20 mm).
1. **Read `STATE.md`.** It says what day it is, what has passed its gate, what
   is blocked, and every number derived so far. It is the handoff between
   sessions. Trust it over your assumptions.
2. **Read the checklist for the current day** in `checklists/`.
3. **Check the hardware is where STATE.md says it is:**
   ```bash
   ls -l /dev/esp32 /dev/ydlidar     # or: make ports
   ```
4. **Say where we are in one or two lines**, then get to work. Do not re-derive
   what `records/` already records — **and most of it now is recorded.**

## Session end protocol

Before the session closes, or whenever a gate is passed:

1. Update `STATE.md` — day, gates, blockers, next action, any new numbers.
2. Append any new symptom→cause pair to `troubleshooting/symptom-index.md`.
3. Put every measured number in `records/calibration.md` with its date and method.
4. Log any decision that closes off an option in `records/decisions.md`.
5. Commit and push. **Every package gets pushed before it gets extended.**

---

## Hard constraints — never renegotiate these

1. **ROS 2 Humble / JetPack 6.1 Advantech / Ubuntu 22.04.** Every apt package,
   container base and Gazebo choice follows from this. **Never suggest Jazzy.**
   JetPack was rolled back from 6.2 (suspected unstable); Ubuntu is 22.04 either
   way so Humble is unaffected. See decision D-12 for what it *does* change.
2. **Build the robot package from the ground up.** The lost one was based on
   `joshnewans/articubot_one`, but that lineage is Jazzy-era. **Do not propose
   forking it.** Write our own URDF, ros2_control config and launch files.
   **This still holds after the recovery** (decision D-13) — but the recovered
   tree in `recoverable/` is *our own Humble-era code*, so copy from it freely
   and knowingly, file by file, re-verifying anything measured.
3. **One week.** Scope to a working demo, not to correctness. Anything that can
   be documented as a limitation instead of built — document it. See
   `RECOVERY.md` §9 for the cut list that has already been agreed.
4. **Git remote from commit one.** Losing the board is why these documents
   exist.
5. **Assume nothing survives that is not listed in `reference/recovered-facts.md`
   or `reference/nvme-recovery-audit.md`.** The camera intrinsics are the one
   calibration still genuinely lost.

## Things not to suggest

| Don't | Why |
|---|---|
| ROS 2 Jazzy, or any Jazzy-era package | Platform is Humble. Non-negotiable. |
| Forking `articubot_one` | Jazzy-era; porting costs more than writing fresh. |
| A Docker / L4T container build for YOLO | What worked was a `uv` virtualenv from `mgonzs13/yolo_ros` with Jetson dependency fixes, running a custom node. See `checklists/day-5-yolo.md`. |
| A depth camera (RealSense / OAK-D) | Not in the build. The mono-camera + lidar fusion **is** the project. |
| Monocular depth estimation | GPU budget is committed to detection. |
| Running `uv sync` against the YOLO venv | It downgrades the JetPack torch wheels and prunes TensorRT. The recovered `uv.lock` is a hazard, not an asset. |
| `make teleop` as an e-stop | It publishes *downstream* of `twist_mux` and fights Nav2. **`make teleop-nav` is the e-stop.** |
| Replacing Nav2's `footprint` with `robot_radius` | A circle needs r=0.265 and refuses doorways the robot fits through. |
| Yawing `laser_joint` to fix scan orientation | That file is shared with sim. Use `reversion`/`inverted` in `ydlidar.yaml`. |
| `amcl` | One-session SLAM provides `map → odom`. Decision D-05. |

**Open decision — D-11:** whether YOLO goes back to `yolo_ros` + TensorRT
engines (what actually ran, at 15 Hz) or the simpler `vision_msgs` custom node.
Two of the first option's prerequisites are lost or invalidated. Read D-11
before Day 5; do not assume D-01 still stands unexamined.

---

## Working agreements

- **If a bring-up step needs a measurement, it gets a script.** Do not walk the
  user through doing it by hand — offer to write the small script instead, and
  put it in `my_bot/scripts/`. Specs are in `reference/scripts-to-rebuild.md`.
- **When a step depends on a detail that died with the board, say so** and give
  a way to re-derive it from the hardware. Never guess a vendor ID, a pin, or a
  calibration constant.
- **Numbers go in `records/calibration.md` the moment they are measured.** Not
  at the end of the day. This is the file whose loss cost the most.
- **Gates are gates.** If the previous day's gate has not passed, say so and
  fix that before starting the next day's work.
- **Safety:** anything involving the motors happens with the robot **on blocks**
  until §5.2 step 7 has passed. An encoder-sign error drives the PID to full PWM.

---

## Workspace map

```
CLAUDE.md            this file — standing brief
README.md            human entry point
STATE.md             LIVE status. Read first, update last.
RECOVERY.md          the strategic seven-day plan, with full rationale
camera-lidar_semantic_mapping.md   design note for the semantic layer (4 Sep)

checklists/          one per day; commands, expected output, gates
reference/           facts that must not be re-derived
records/             what we measured, decided, and hit
troubleshooting/     symptom → cause → fix

recoverable/mount/   NVMe recovery: the whole my_bot package, Makefile,
                     uv.lock (a hazard), .bash_history. READ-ONLY reference.
semantic-object/     semantic_bridge + semantic_map_ui (from the USB drive)
semantic-object-ros/ June-era semantic_objects (reference only; does not run)
```

**Never edit anything under `recoverable/`.** It is the only copy of the old
board's state. Copy out of it into `capstone-ws`.

**`RECOVERY.md` is the why. The checklists are the what. `STATE.md` is the where.**

---

## The demo we are building toward

**Committed:** drive · `slam_toolbox` map · Nav2 goal navigation · live semantic
markers.
**Stretch, only if all three rehearsals are clean:** navigate to a named object.
