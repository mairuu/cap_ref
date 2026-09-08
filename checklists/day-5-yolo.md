# Day 5 — YOLO on the Jetson

**Goal:** `/detections` publishing `vision_msgs/Detection2DArray` with track IDs,
at a usable rate.

**Prerequisite:** Day 4 gate passed. Camera calibrated.

> ⚠ **§1 should already be done** — it was Track B work starting Day 2. If the
> `uv` environment is still not built, that is today's whole job and the rest
> slips. This is the highest-variance item in the week.

> **Not a container.** Do **not** propose a Docker or L4T container build. What
> worked was a `uv` virtualenv taken from `mgonzs13/yolo_ros`, with Jetson
> dependency fixes, running a custom node.

---

## 1 · The `uv` environment (start this on Day 2)

Four fights, in the order they bite. `RECOVERY.md` §5.6.

- [ ] **`--system-site-packages` is mandatory** — the node needs `rclpy`, which
      is a system apt package and will not install into a sealed venv:

```bash
uv venv --system-site-packages
```

- [ ] **PyPI torch is wrong for aarch64.** Installing `ultralytics` normally
      pulls a CPU-only or x86 wheel. Install NVIDIA's JetPack 6
      torch/torchvision wheels **first**, then:

```bash
uv pip install ultralytics --no-deps
```

      then add the remaining deps by hand.

- [ ] **numpy 2 breaks JetPack's OpenCV.** The system `cv2` is built against
      numpy 1.x → pin `numpy<2`.
- [ ] **Nothing reinstalls `opencv-python`.** Use JetPack's CUDA-enabled system
      OpenCV via system-site-packages.

**Verify before writing any node — all three must pass inside the venv:**

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"
python -c "import rclpy; print('rclpy ok')"
```

- [ ] `torch.cuda.is_available()` is **True**
- [ ] **Exact working versions written into `records/calibration.md` the moment
      they pass.** This is the knowledge that was lost last time and the most
      expensive thing here to rediscover.

  torch ________ · torchvision ________ · numpy ________ · ultralytics ________
  cv2 ________ · JetPack ________

- [ ] `uv.lock` / requirements committed and pushed

## 2 · The detection node

- [ ] Custom node inside that venv, publishing `vision_msgs/Detection2DArray`
      on `/detections`

> **Message type decision (D-01):** `vision_msgs`, **not** `yolo_msgs`. It is
> apt-installable (`ros-humble-vision-msgs`) and the surviving `semantic_objects`
> already parses it. Do not build `yolo_msgs`.

- [ ] Uses ultralytics' own tracker — no separate tracking node:

```python
results = model.track(frame, persist=True, verbose=False)
```

- [ ] **Track ID written into `Detection2D.id`** — this is what satisfies P5
- [ ] `header.stamp` carries the **image capture time**, not publish time. The
      semantic node's TF lookup depends on it (P2).
- [ ] Subscribes to the same `/camera` namespace the calibration used
- [ ] `launch/yolo.launch.py` written

## 3 · Rate and thermals

Two levers if the Jetson cannot hold 15 Hz:

- [ ] `imgsz` down to 480
- [ ] `yolov8n`, not `yolov8m` — a demo does not need the bigger model

```bash
ros2 topic hz /detections
tegrastats                    # watch for throttling over several minutes
```

  **rate ______ Hz · model ________ · imgsz ______ · temp after 5 min ______ °C**

- [ ] Recorded

> **Fallback if CUDA never comes up:** run detection at 5 Hz on CPU. Ugly, but
> demoable. Log it in `STATE.md` deviations and keep going — do not spend Day 6
> on it.

---

## GATE — do not start Day 6 until all of these hold

- [ ] `ros2 topic hz /detections` is **stable**
- [ ] Track IDs **persist across frames** for a stationary object
- [ ] The Jetson is **not thermally throttling** after five minutes
- [ ] Working dependency versions recorded and pushed

**Then update `STATE.md`.**
