# Day 7 — Measure, rehearse, write

**Goal:** a demo you have run end-to-end three times, and honest numbers.

**Prerequisite:** Day 6 gate passed. Landmarks appear and persist.

---

## 1 · Morning — the tape-measure protocol

The design note's §08 validation. Run it **once, properly**. Even mediocre
numbers are worth far more in a report than no numbers, because they show you
knew what to measure.

- [ ] Write `landmark_tape_measure.py` (`reference/scripts-to-rebuild.md`)
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
make real
make slam
# drive the loop
make yolo
make semantic
make bridge     # + make ui
```

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
      the day
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

Write it while it is fresh. `RECOVERY.md` §9 already has the sentences drafted
for each cut item — Gazebo, P6, P7, P8, P4's size-prior fallback, AMCL,
multi-session persistence.

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
- [ ] Tape-measure numbers recorded
- [ ] Demo script written
- [ ] Bag recorded as fallback
- [ ] Limitations section drafted
- [ ] **Everything pushed**

**Then update `STATE.md` one last time.**
