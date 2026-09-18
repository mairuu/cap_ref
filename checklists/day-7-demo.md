# Day 7 — Measure, rehearse, write

**Goal:** a demo you have run end-to-end three times, and honest numbers.

**Prerequisite:** Day 6 gate passed. Landmarks appear and persist.

---

## 1 · Morning — the tape-measure protocol

> ⛔ **CUT on 18 Sep — this section was not run. See D-24.** Rehearsals were
> given the robot time instead. The script is written, installed and ready
> (`--pass-label` / `--summary`), and `~/maps/tape_session.jsonl` is clean, so
> two passes would still recover the across-pass spread if robot time frees up.
> **The unticked boxes below are a record of what was cut, not a to-do list.**
> D-24 carries the drafted limitations sentence for the report.


The design note's §08 validation. Run it **once, properly**. Even mediocre
numbers are worth far more in a report than no numbers, because they show you
knew what to measure.

- [x] ~~Write `landmark_tape_measure.py`~~ — **written 14 Sep (Day 6)** and used
      for the bench check that passed
- [x] **Extend it for four passes** — ✅ 16 Sep. The design note wants spread
      **across** four passes; the script only measured spread *within* one run,
      and keyed it on the nearest landmark id, so a mid-loop association split
      silently dropped history and **understated** the number. Both fixed:

```bash
ros2 run my_bot landmark_tape_measure.py chair --truth X Y --pass-label front
#   ... right, back, left ...
ros2 run my_bot landmark_tape_measure.py chair --truth X Y --summary
```
> ⚠ **Back the robot off to ~1.6 m before starting.** Day 6 measured the
> detections-mapped metric at **~0.45** against this day's **> 0.6** target.
> Every rejection was `max_spread` — the chair close enough that the scan window
> straddles it and the background. The bench check at **1.64 m got 94.3 %**.
> Set up at that range or the metric scores against you for a reason that has
> nothing to do with the fusion.

- [ ] Place a chair at a position measured against **two walls** with a tape

  ground truth: x ______ m · y ______ m

- [ ] Drive a closed loop around the room, passing the chair from **four
      directions**
- [ ] Log the landmark's published position on every pass

| Pass | Published x | Published y | Error vs. tape |
|---|---|---|---|
| 1 (front) | | | |
| 2 (right) | | | |
| 3 (back) | | | |
| 4 (left) | | | |

- [ ] Fill the design note's results table:

| Metric | Target | Measured |
|---|---|---|
| Absolute position error, floor-standing class | < 0.25 m | |
| Spread across four passes | < 0.15 m | |
| Duplicate landmarks per true object | 1.0 | |
| Ghosts surviving a second pass | 0 | *(expect > 0 — P7 is cut)* |
| Detections mapped / detections received | > 0.6 | |

> **Absolute error tests the geometry chain; spread tests the fusion. They fail
> for different reasons — report both.**

- [ ] All of it in `records/calibration.md`

## 2 · Afternoon — rehearse

**Three full runs from cold boot.** Time each one.

```bash
make ports      # devices first, always
make bag        # optional; start it whenever, /tf_static is latched
make real
make slam
# drive the loop
make nav        # REQUIRED: twist_mux and the speed guard live here, so
                # `make teleop-nav` (the e-stop) does nothing without it
make yolo
make semantic
make bridge     # + make ui
```

> **`make nav` was missing from this block.** It is not optional: the e-stop
> depends on it, and the §3 stretch goal needs `NavigateToPose`. Rehearsing
> without it rehearses a startup you will not use.

| Run | Time | Failed at | Note |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

- [ ] Run 1 clean
- [ ] Run 2 clean
- [ ] Run 3 clean
- [ ] **One run on a half-charged battery** — find the step that fails when the
      pack sags
- [ ] `make bag` recorded on the best run — insurance if live hardware fails on
      the day. ✅ **Target written 16 Sep** (it did not exist). Replay with
      `make bag-play BAG=...`. Note the `RECOVERY.md` draft of this target
      records `/odom`, which is **not a topic on this robot** — use the Makefile's
      version. Latched topics need no special handling: rosbag2 stores each
      publisher's offered QoS and reproduces it (verified 16 Sep)
- [ ] Startup order written down as a one-page demo script

## 3 · Stretch — navigate to a named object

> **Only if all three rehearsals were clean.** This stacks an action server on
> top of the fusion pipeline; if that pipeline is shaky, it will fail in the
> most visible way possible.

- [ ] Small action server: look up landmarks by class → nearest → standoff pose
      0.8 m in front, facing the object → `NavigateToPose`
- [ ] "Go to the nearest chair" works three times running
- [ ] If it does not work by early evening, **stop and cut it.** Say in the
      report that the pieces exist and the integration was not reached.

## 4 · Evening — write the limitations section

Write it while it is fresh. `RECOVERY.md` §9 has drafted sentences for
**Gazebo, P6, P7, P8 and P4's size-prior fallback**.

> ⚠ **Two of the items named here have no drafted sentence**, contrary to what
> this line used to claim: **AMCL** (§9 has rationale, not a limitation
> sentence — raw material in D-05 and `navigation.launch.py`) and
> **multi-session persistence** (no decision record of its own; it rides on
> D-05, and the reasoning is in `semantic_objects_node.py`'s header). P4 *does*
> have one, so it was a false alarm in the other direction.

- [ ] Each cut item has a sentence saying what is missing and what would fix it
- [ ] Deviations from `STATE.md` folded into a methodology note
- [ ] The before/after framing: what the tape-measure numbers show

> A demo that does five things well and names six limitations precisely reads as
> stronger engineering than one that does eleven things unreliably. **The
> limitations section is not an apology** — it is evidence you knew where the
> edges were.

---

## GATE — done

- [ ] Three clean end-to-end rehearsals
- [x] ~~Tape-measure numbers recorded~~ — **cut, D-24.** Stationary bench
      numbers stand in; the limitation is drafted and must reach the report
- [ ] Demo script written
- [ ] Bag recorded as fallback
- [ ] Limitations section drafted
- [ ] **Everything pushed**

**Then update `STATE.md` one last time.**
