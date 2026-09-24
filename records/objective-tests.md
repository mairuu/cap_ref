# Objective tests — how each row of the report's evaluation table gets its number

The report (`report-prototype.md` §วัตถุประสงค์, and the evaluation table
`tab:eval` in §การประเมินคุณภาพของระบบงาน) states five numeric criteria and
leaves the **ผล** column empty. This file is the method for filling it: what to
run, what to write down, and what each number does and does not prove.

**One lap fills four of the five.** Objectives 1, 3, 4 and 5 are all measured
from the same drive, by starting three listeners before the lap and stopping
them after. Only objective 2 needs work off the robot. Budget ~45 minutes for
the lap, plus an evening for objective 2.

| # | Criterion (report) | Tool | Status |
|---|---|---|---|
| 1 | SLAM position error ≤ **10 cm**, area ≥ 5×5 m | `slam_accuracy_check.py` **(new)** | needs the lap |
| 2 | Detection accuracy ≥ **80 %** | hand-labelled frames from a bag | **needs a decision — see below** |
| 3 | Detection rate ≥ **5 FPS**, SLAM running | `detection_report.py` | ✅ **13.05 Hz already measured** |
| 4 | Object position error ≤ **50 cm** | `landmark_tape_measure.py` | partial: 0.08 m stationary |
| 5 | Mean CPU ≤ **80 %** | `resource_report.py` **(new)** | needs the lap |

---

## Copy-paste sheet — the whole measurement lap

**Before any command.** Tape a cross on the floor for `HOME` and park the robot
on it, aimed straight down a wall. Tape three more crosses around the room and
measure each from `HOME` with the tape: **x along the robot's heading, y to its
left** (right is negative). Put the test chair about **1.6 m** from a spot the
robot can stop at, and measure its x/y the same way. Write the four pairs on
paper before you start — the map origin is fixed the moment `make slam` runs,
and re-deriving it afterwards is not possible.

`~/.bashrc` sets `ROS_DOMAIN_ID=42` but does **not** source ROS. The `make`
targets source it themselves; every `ros2 run` terminal below needs this line
first:

```bash
source /opt/ros/humble/setup.bash && source ~/cap_ws/install/setup.bash
```

### The stack — seven terminals, in this order

```bash
cd ~/cap_ws && make ports    # check: /dev/esp32 and /dev/ydlidar both present
make real                    # T1
make slam                    # T2  <- THE ORIGIN IS SET HERE. Robot on HOME, facing the wall.
make nav                     # T3  required: twist_mux, the speed guard, NavigateToPose
make yolo                    # T4  starts its own camera; do not also run `make camera`
make semantic                # T5
make bridge                  # T6
make ui                      # T7
```

### The measurement terminals — start these BEFORE driving

```bash
make bag                                                             # T8

# T9 -- objective 5. Cover the whole lap; Ctrl-C ends it early and still reports.
ros2 run my_bot resource_report.py --seconds 900 \
  --label "real+slam+nav+yolo+semantic, driving"

# T10 -- objective 3, a live figure to sit beside the bag's 13.05 Hz.
ros2 run my_bot detection_report.py --seconds 300
```

### Drive, and stop on each mark

```bash
# T11 -- 0.10 m/s. Nothing enforces this since D-26. Do not press `q`.
cd ~/cap_ws && make teleop-nav SPEED=0.10
```

At each cross, stop the robot and run one line in T12 — objective 1:

```bash
ros2 run my_bot slam_accuracy_check.py mark HOME     --truth 0 0
ros2 run my_bot slam_accuracy_check.py mark MARK_B   --truth 4.20 -2.65
ros2 run my_bot slam_accuracy_check.py mark MARK_C   --truth 6.80  1.10
ros2 run my_bot slam_accuracy_check.py mark MARK_D   --truth 2.05  3.40
```

Then drive the lap again and repeat all four. **Three laps minimum** — one visit
per mark gives an error, three give repeatability, and repeatability is the
number with no tape in it.

Park by the chair for objective 4, one run per side (back the robot off to
~1.6 m each time):

```bash
ros2 run my_bot landmark_tape_measure.py chair --truth 5.10 -1.35 --pass-label front
ros2 run my_bot landmark_tape_measure.py chair --truth 5.10 -1.35 --pass-label right
ros2 run my_bot landmark_tape_measure.py chair --truth 5.10 -1.35 --pass-label back
ros2 run my_bot landmark_tape_measure.py chair --truth 5.10 -1.35 --pass-label left
```

### Before shutting anything down

```bash
make save-map MAP=~/maps/objective-lap-$(date +%m%d)   # while slam_toolbox is still up
```

### Read the results back

```bash
ros2 run my_bot slam_accuracy_check.py --summary        # objective 1
ros2 run my_bot landmark_tape_measure.py chair --truth 5.10 -1.35 --summary   # objective 4
ros2 run my_bot resource_report.py --summary            # objective 5
```

`detection_report.py` prints its verdict when its window ends (objective 3).
Copy every number into `records/calibration.md` the same day.

---

## The lap: one run, four numbers

Start the stack as usual (`make real`, `make slam`, `make nav`, `make yolo`,
`make semantic`), then **before driving** open three more terminals:

```bash
# 1. resources, for objective 5 -- runs for the whole lap
ros2 run my_bot resource_report.py --seconds 600 --label "slam+yolo+nav, driving"

# 2. detector rate, for objective 3 -- concurrent by construction
ros2 run my_bot detection_report.py --seconds 300

# 3. the bag, so the lap can be re-measured later without the robot
make bag
```

Drive the lap at **0.10 m/s** (`make teleop-nav SPEED=0.10`) — nothing enforces
that any more since D-26, and 0.30 m/s shears the scans by 2.6 cm. Stop on each
tape mark for objective 1, and park by the test object for objective 4.

---

## Objective 1 — SLAM position error ≤ 10 cm

**Criterion:** `ความคลาดเคลื่อนเชิงตำแหน่งไม่เกิน 10 เซนติเมตร` in a controlled
area of at least 5×5 m.
**Stated method:** mark reference points of known true coordinates, drive the
robot back to them, compare the reported pose with the truth.

```bash
# on each mark, robot stationary:
ros2 run my_bot slam_accuracy_check.py mark HOME     --truth 0 0
ros2 run my_bot slam_accuracy_check.py mark CORNER_A --truth 4.20 -2.65
#   ... one line per mark, per lap. Three laps minimum.
ros2 run my_bot slam_accuracy_check.py --summary
```

**Where the truths come from.** `slam_toolbox` puts the map origin at the
robot's pose when `make slam` started, +x along its heading, +y to its **left**.
Every `--truth` is measured from that spot, in that direction — the script's
docstring carries the full recipe. Park the robot facing down a wall and the
tape work becomes two perpendicular measurements per mark.

**Record three things, not one:**

- **absolute error** — the objective's number. Worst case across all visits.
- **repeatability** — spread across repeat visits to one mark. Contains no tape
  error and no parking error, so it is the honest measure of SLAM itself.
- **the area** — the criterion names 5×5 m, so state the mapped extent. The
  22 Sep map is 666×361 px at 0.05 m/px = **33.3 × 18.1 m of bounding box**,
  comfortably past the criterion; give the floor area actually driven.

> **The reported error is an upper bound, and say so.** Parking on a floor cross
> by hand is worth ~2 cm and the tape ~1 cm; both are inside the number. Being
> wrong in that direction is the right way round for a pass/fail criterion.

**Supporting figure, free:** measure one long wall with the tape, count its
pixels in `~/maps/day7-run-22sep.pgm`, multiply by 0.05. A consistent
over/under-reading across two walls is a **scale** error (wheel radius, ticks
per rev), not a mapping error — `--summary`'s pair table says the same thing
from the pose side.

## Objective 2 — detection accuracy ≥ 80 % ⚠ read this before writing anything

**Criterion:** `ค่าความแม่นยำไม่น้อยกว่าร้อยละ 80`, evaluated on a held-out
test set, averaged over the target classes.

**The honest position:** the detector is **`yolo26s` pretrained on COCO**,
exported to ONNX at 640×640 and run at `conf 0.5`. No model was trained here, so
there is no held-out split of ours to evaluate on. Two ways to produce a real
number, and they answer different questions:

- **(a) In-situ test set — recommended.** Pull ~120 frames spread across a bag
  (`/image/compressed` and `/detections` are both recorded, at 13 Hz), label by
  hand what is actually in each frame for the target classes, and score
  precision / recall / F1 per class at `conf 0.5`. This measures **the deployed
  detector in the room it is deployed in**, which is the claim the project
  actually needs, and it takes one evening.
- **(b) Public benchmark.** Quote the published COCO mAP for the model and cite
  it. Costs nothing, proves nothing about this robot, and an examiner may
  reasonably ask why the number is not yours.

Do (a); mention (b) in one sentence for context.

### What to claim, given that the model is not ours

Objective 2 is worded `เพื่อพัฒนาและปรับปรุงโมเดลการเรียนรู้เชิงลึก` — to
**develop and improve** the model. Pretrained COCO weights were used as they
came, so that wording overstates what was done, and an examiner who asks "which
dataset, how many epochs" must not get a vague answer. Two ways to make the
claim match the work, and the measurement is identical either way:

- **Keep the objective, change what the number is about.** Report the
  **accuracy of the deployed detector in the target environment** — your own
  labelled frames, your room, your camera, at `conf 0.5`. That is a genuine
  experimental result about the system, and it is a more relevant one than a
  COCO score, because it is measured where the robot works.
- **Reword the objective** to selection and deployment on an edge device rather
  than training. Worth one question to the advisor; it costs nothing if the
  answer is yes and it removes the only soft claim in the chapter.

**And name what was actually engineered**, because it is not nothing:

- export `yolo26s.pt` → ONNX at a fixed 640×640 and run it through ONNX Runtime
  on the Orin's GPU — a deployment decision with a measurable cost;
- the confidence threshold and the target-class filter;
- the detection→lidar fusion gate (motion gate, `max_spread` rejection) — a
  system-level accuracy improvement that *is* ours, and objective 3's 0.08 m
  is the evidence for it.

> The `.pt` versus `.onnx` comparison on the same labelled frames is what turns
> "we used a pretrained model" into a measured engineering decision. Equal
> accuracy at a higher frame rate is a result; skipping the comparison leaves
> the export as an unjustified assertion.

**Worth the extra hour, and it is a good figure:** score the same labelled
frames through `yolo26s.pt` (torch) and `yolo26s.onnx` (ONNX Runtime). Equal
accuracy at a higher frame rate is the evidence for the export decision, and it
turns "we used a pretrained model" into "we quantified what deployment cost".

> **Blocked on one input:** which classes count as `วัตถุเป้าหมาย`. The
> landmark set from 22 Sep contains `chair`, `bench`, `person`, `laptop`. Pick
> the list, and the labelling and the scorer follow from it.

### Run log

#### 24 Sep — attempt 1: bag recorded, extracted, pre-labelled — **NOT USABLE, robot stationary**

**Method as run** (round A of `MEASUREMENT-PLAN.md`):

| Step | What | Result |
|---|---|---|
| Stack | `make real` · `make yolo` (yolo26s ONNX fp16, 640, conf 0.5) · `make teleop` — no SLAM, no semantic | |
| Frames | `image_transport republish raw compressed` of **`/image`** (raw camera, no drawn boxes) → `/image/compressed`, 15.13 Hz | a first bag at 16:37 had only `/detections/image` (annotated) and was discarded |
| Record | `make bag TOPICS="/image/compressed /detections"`, zstd file mode | `~/bags/2026-09-24-165025`: 3962 images, 3549 detection msgs, 290 s (4.8 min) |
| Extract | `extract --every 23 --matched-only` | 3283/3962 images processed by the detector (≈13 FPS vs 15 Hz camera) → **143 frames, 143/143 matched at stamp** |
| Pre-label | `prelabel --model ~/yolo/yolo26x.pt` (conf 0.25), classes `person chair backpack laptop` | drafts: person 296 · chair 448 · backpack 143 · laptop 114 |

`--matched-only` is used because the detector copies the image header: a frame
it processed has a detection message at exactly its stamp, even an empty one,
so an unmatched frame is one it dropped — scoring it as all-misses penalises a
frame the model never saw, and `--slop 0.1` would pin a neighbour's boxes on it.

**Why it is not usable.** Every one of the 143 frames is the same viewpoint:
one laptop and one backpack on the floor at the left, the same blue chair at the
right, only the people move. So `laptop` and `backpack` are **one object each at
one pose, 143 times** — the ≥ 50-instance rule counts instances, and these are
one sample repeated. This is exactly the "อย่าจอดนิ่ง" failure the plan warns
about. Not labelled; not scored as a result.

**Provisional, NOT the objective 2 result** — yolo26s at conf 0.5 scored against
the *uncorrected* yolo26x drafts (i.e. agreement between two models, on the
unusable set): macro prec 98.5 %, recall 53.2 %, F1 65.3 %; per class F1 person
63.8 · chair 27.6 · backpack 77.8 · laptop 92.0. Kept only for what it predicts
about the real run: **chair recall is where macro F1 will be lost.** The room
has many small, distant, partly hidden chairs under the desks; the labelling
rule is "every visible instance", so they count, and yolo26s at 0.5 misses most
of them. Do not change the rule or the class list because of this
(`MEASUREMENT-PLAN.md` §7.1).

**Next:** re-record round A **driving the whole time** — several distances and
angles, 2–3 backpacks, 1–2 laptops — then extract into a fresh directory. The
attempt-1 data is kept as `~/eval/insitu2_stationary` for reference.

## Objective 3 — detection rate ≥ 5 FPS with SLAM running ✅

**Already satisfied, with evidence, and the concurrency is not an assumption.**
From `~/bags/2026-09-22-163401/metadata.yaml`, one 215.3 s window:

| topic | messages | rate |
|---|---|---|
| `/detections` | 2 809 | **13.05 Hz** |
| `/image/compressed` | 2 808 | 13.04 Hz |
| `/scan` | 2 497 | 11.60 Hz |
| `/map` | 105 | 0.49 Hz |
| `/diff_cont/odom` | 6 257 | 29.06 Hz |

`/scan` flowing and `/map` updating in the same window **is** SLAM running, so
this is the criterion's condition, measured, at **2.6× the requirement**.

Day 5's standalone gate measured **15.15 Hz, sd 5 ms over 301 s** with tj max
44.6 °C. The difference between 15.15 and 13.05 is what SLAM and the recorder
cost — quote both; the pair is more informative than either.

> These are *recorded* rates. Run `detection_report.py --seconds 300` once
> during the lap for a live figure with jitter and latency, so the table does
> not rest on a bag alone.

## Objective 4 — object position error ≤ 50 cm

**Criterion:** `ความคลาดเคลื่อน ... ไม่เกิน 50 เซนติเมตร`, object detected from
several viewpoints, published position compared with the true one.

```bash
# robot ~1.6 m from the object, one run per viewing direction:
ros2 run my_bot landmark_tape_measure.py chair --truth 1.80 0.75 --pass-label front
#   ... right, back, left ...
ros2 run my_bot landmark_tape_measure.py chair --truth 1.80 0.75 --summary
```

**In hand already (16 Sep, stationary bench):** error **0.08 m**, within-run
spread 0.04 m, duplicates 1, fused 94.3 % at 1.64 m. That is **6× inside** the
report's 50 cm criterion and inside the design note's stricter internal target
of 25 cm.

**What is missing is the viewpoint clause.** The four-pass protocol was cut on
18 Sep (D-24) and re-acquisition from a new bearing is the known weak point.
One stationary pass is not evidence for a criterion that says *several
viewpoints* — two passes from different sides is the minimum that honours the
wording, and the script's `--pass-label` / `--summary` already produce the
across-pass spread.

> **Back off to ~1.6 m before measuring.** Closer than that and the scan window
> straddles object and background; every Day 6 rejection was `max_spread` for
> exactly this reason.

## Objective 5 — mean CPU ≤ 80 %

**Criterion:** `อัตราการใช้งานหน่วยประมวลผลหลักเฉลี่ยไม่เกินร้อยละ 80`
throughout the working period, with SLAM and detection running together.

```bash
ros2 run my_bot resource_report.py --seconds 600 --label "slam+yolo+nav, driving"
ros2 run my_bot resource_report.py --summary     # every window side by side
```

Take **three windows**, because the comparison is the interesting part and each
costs only the time it runs:

1. idle board, nothing up — the baseline;
2. `make real` + `make slam` only — mapping alone;
3. the full stack while driving — **this is the table's number**.

The script reports the 6-core mean (the criterion), each core separately, GPU,
RAM peak and tj. If one core sits near 100 % while the mean passes, report the
mean and say the sentence about single-threaded executors — naming the real
ceiling reads as engineering, not as a failure.

---

## Where the numbers go

Every figure lands in `records/calibration.md` with its date and method **the
moment it is measured**, then into the report's `ผล` column. The evaluation
table wants one line each; the methodology note behind it wants the caveats
above — the upper-bound framing for objective 1, the pretrained-model position
for objective 2, the concurrency evidence for objective 3, the viewpoint gap
for objective 4, and the busy-core reading for objective 5.
