# DEMO — what to show, how to record it, and what to do when it breaks

Two audiences, one stack: a **recorded clip** that cannot fail during the
presentation, and a **live demo** in front of the professor. Build the clip
first — it is the insurance, and making it rehearses the live run.

---

## 1 · The six beats

In this order. Each one is a separate claim, and each is visible without
narration — that is the test for whether a beat earns its place.

| # | Beat | What the audience sees | Proves |
|---|---|---|---|
| 1 | **The robot** | 20 s pan: Orin, lidar, camera, ESP32, wheels | it is real hardware, built not bought |
| 2 | **Drive + map grows** | teleop; RViz map filling in live next to the moving robot | SLAM, odometry, the whole sensing chain |
| 3 | **Detection** | `/detections/image` — boxes, classes, track ids on a live frame | the edge detector runs on-board |
| 4 | **Objects land on the map** | labelled markers appearing in RViz at the objects' real places | **the fusion — this is the project** |
| 5 | **The web UI** | browser: map, robot, object list with per-class counts | an operator with no ROS can use it |
| 6 | **Nav2 goal** | click a goal → global plan draws → robot drives and stops | autonomy, not just teleop |

**Beat 4 is the thesis.** Anyone can show a lidar map or a YOLO box; the
camera-to-map placement of a *labelled* object is what the project is for. Give
it the most screen time and say the sentence out loud: mono camera plus 2D
lidar, no depth sensor.

Optional beat 7, only if it has worked three times that day:
`go_to_object.py` — "go to the nearest chair" → it plans a standoff pose and
drives there. High payoff, highest risk; cut it without apology.

## 2 · Recording the clip

**The clip is screen-record + phone video, cut together.** Nothing about it
needs to be one continuous take.

Record RViz and the browser **on the laptop** (`rviz2 -d ~/cap_view/nav.rviz`
already runs there, and the Jetson has no screen recorder installed). Record the
robot itself on a phone, at the same time, so the two can be cut side by side —
a map growing next to the robot that is growing it is worth more than either
shot alone.

**The safe way to film beats 2–5 is to replay the bag.** The bridge subscribes
to `/semantic_landmarks`, `/map`, `/scan` and `/image/compressed`, and all four
are in every bag `make bag` writes, so the **entire UI runs off a recording**
with no robot, no battery and no failure mode:

```bash
make bag-play BAG=~/bags/2026-09-22-163401     # terminal 1
make bridge                                     # terminal 2
make ui                                         # terminal 3
rviz2 -d ~/cap_view/nav.rviz                    # laptop
```

Two things to know before you rely on it:

- **The robot model will not draw.** `/robot_description` is latched by
  `robot_state_publisher`, which is not in the bag. Run
  `ros2 launch my_bot rsp.launch.py` alongside the replay and it appears; skip
  it and you get TF axes, which is fine but looks unfinished on camera.
- **Beat 6 is not in the 22 Sep bag.** `/plan` and `/local_plan` are not in
  `BAG_TOPICS`, so a replay cannot show the Nav2 path. Either film beat 6 live,
  or record the next bag with them:

  ```bash
  make bag TOPICS="/tf_static /tf /scan /diff_cont/odom /map /detections \
    /detections/image /image/compressed /semantic_landmarks /semantic_markers \
    /plan /local_plan /global_costmap/costmap"
  ```

  Do that on the next lap and the clip becomes fully reproducible from disk.

## 3 · The live demo

**Start the stack before the audience arrives.** Bring-up is ~60 s of terminals
and nobody needs to watch it; have it up, warm, and the map already showing the
room you are standing in. Say what is running in one sentence.

Startup order — `make nav` is **not** optional, because `make teleop-nav` is the
e-stop and it does nothing without `twist_mux`:

```bash
make ports        # devices first, always
make bag          # record the live demo too; it costs nothing
make real
make slam
make nav          # twist_mux + speed guard + NavigateToPose
make yolo
make semantic
make bridge       # + make ui
```

**Drive at 0.10 m/s while anything is being mapped.** `make teleop-nav
SPEED=0.10`. Since D-26 the ceiling is 0.30 and nothing stops you shearing the
map at 2.6 cm per scan; the guard only stops a runaway now.

**Keep one hand on the e-stop.** `make teleop-nav`, spacebar. `make teleop`
publishes downstream of the mux and *fights* Nav2 instead of overriding it —
during beat 6 it is the wrong terminal to reach for.

**What to have open but not showing:** the bag replay from §2, already loaded.
If the hardware dies mid-demo, switch to it and keep talking. That is the whole
reason the bag exists.

## 4 · Failure lines, ready to say

Rehearse these; they turn a failure into evidence of understanding.

| If | Say |
|---|---|
| a marker lands in the wrong place | "That is the association limit — one track id becomes one landmark, and from a new bearing the tracker can re-acquire as a new id. It is in the limitations section." |
| the map smears | "Scan shear — 86 ms per scan times drive speed. That is why the mapping runs are capped at 0.10 m/s." |
| Nav2 refuses a goal | "The goal was sent in the odom frame; Nav2 wants it in map." (RViz Fixed Frame) |
| a goal times out | "Recovery behaviours — it is spinning to re-localise before it re-plans." |
| nothing at all works | switch to the bag replay, and say that recording the run was the contingency |

## 5 · The numbers slide

A demo without numbers is a video. Put these on one slide, with the criterion
next to each — `records/objective-tests.md` says how each is measured and which
are still open.

| Objective | Criterion | Measured |
|---|---|---|
| SLAM position error | ≤ 10 cm | *the lap — `slam_accuracy_check.py`* |
| Detection accuracy | ≥ 80 % | *in-situ labelled set — see the decision in `objective-tests.md`* |
| Detection rate, SLAM concurrent | ≥ 5 FPS | **13.05 Hz** over 215 s (22 Sep bag) |
| Object position error | ≤ 50 cm | **0.08 m** stationary bench (16 Sep); viewpoint passes open |
| Mean CPU | ≤ 80 % | *the lap — `resource_report.py`* |

And one figure: `figures/map-22sep.png`, the 32 × 17.6 m map from the 22 Sep
run, walls single-stroke.
