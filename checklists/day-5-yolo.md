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
- [x] **Exact working versions written into `records/calibration.md` the moment
      they pass.** ✅ 9 Sep, re-confirmed live 14 Sep This is the knowledge that was lost last time and the most
      expensive thing here to rediscover.

  torch **2.11.0** · torchvision **0.26.0** · numpy **1.26.4** · ultralytics **8.4.144**
  cv2 **4.5.4** · JetPack **6.1 (L4T 36.4.0)** · TensorRT 10.3.0 · **lap 0.5.13** (tracker; added 14 Sep)

- [x] ~~`uv.lock`~~ `yolo/setup_yolo_venv.sh` + `requirements-frozen.txt` committed and pushed (a lock file cannot express order or exclusions — see the script header)

## 2 · The detection node

- [x] Custom node inside that venv, publishing `vision_msgs/Detection2DArray`
      on `/detections` — ✅ **14 Sep, `scripts/yolo_detector.py`.** D-11 closed on B

> **Message type decision (D-01):** `vision_msgs`, **not** `yolo_msgs`. It is
> apt-installable (`ros-humble-vision-msgs`) and the surviving `semantic_objects`
> already parses it. Do not build `yolo_msgs`.

- [x] Uses ultralytics' own tracker — no separate tracking node:

```python
results = model.track(frame, persist=True, verbose=False)
```

- [x] **Track ID written into `Detection2D.id`** — this is what satisfies P5. ✅ Proven 14 Sep: 5 ids, each 893/893 frames on a still image
- [x] `header.stamp` carries the **image capture time**, not publish time. The
      semantic node's TF lookup depends on it (P2). ✅ Header copied from the image; age at publish p50 48 ms confirms it
- [x] Subscribes to the same ~~`/camera` namespace~~ **`/image` topic** the calibration used (`cam2image`, RELIABLE — the node's subscriber matches it)
- [x] `launch/yolo.launch.py` written — starts `cam2image` with focus **locked at 51**, same as the calibration; `make yolo`

## 3 · Rate and thermals

Two levers if the Jetson cannot hold 15 Hz:

- [x] ~~`imgsz` down to 480~~ **measured 14 Sep: buys nothing** (36.2 vs 34.9 ms; launch-bound)
- [x] ~~`yolov8n`, not `yolov8m`~~ ~~**`yolo26n`**~~ **`yolo26s`, as an fp16 `.onnx`** since 16 Sep (**D-22**). The swap costs 1.2 ms — this board is launch-bound, so the bigger model is nearly free. `yolov8n` and `yolo26n` are both still on disk: `make yolo MODEL=~/yolo/yolo26n.pt` runs the Day 5 torch path unchanged
- [x] **fp16 matters for ONNX and only for ONNX.** fp32 `.onnx` is a 9 ms *regression* against torch; fp16 lands level with it. Do not ship `ONNX_HALF=false`

```bash
ros2 topic hz /detections
tegrastats                    # watch for throttling over several minutes
```

  **rate 15.15 Hz · model yolo26n.pt (torch fp16) · imgsz 640 · tj after 5 min 44.1 °C (max 44.6)**

> ⚠ **That line is the 14 Sep run, and it no longer describes what `make yolo`
> does.** The model is `yolo26s.onnx` (fp16) as of 16 Sep. Bench says ~46 ms p50
> in a 66.7 ms budget, so it should still be camera-limited — but a synthetic
> frame proves neither the rate nor the track ids. **Re-run the gate.**

- [x] Recorded — `records/calibration.md`, 14 Sep. Replace `ros2 topic hz` + `tegrastats` above with **`ros2 run my_bot detection_report.py --seconds 300`**, which measures all four gate lines at once

> **Fallback if CUDA never comes up:** run detection at 5 Hz on CPU. Ugly, but
> demoable. Log it in `STATE.md` deviations and keep going — do not spend Day 6
> on it.

---

## GATE — do not start Day 6 until all of these hold

> ⚠ **PASSED 14 Sep on `yolo26n.pt`/torch, and the model and backend BOTH
> changed on 16 Sep (D-22).** The first three clauses were evidence about a
> configuration that is no longer what `make yolo` launches, so they are
> re-opened. The fourth still holds. Nothing about the node, the topic or the
> track-id contract changed, so this is expected to be a re-confirmation rather
> than a re-investigation — but it has to actually be run.

- [ ] `ros2 topic hz /detections` is **stable** — ~~✅ 15.15 Hz over 301 s~~ **re-run on `yolo26s.onnx`**
- [ ] Track IDs **persist across frames** for a stationary object — ~~✅ one cup, id 1 in 457/457 frames~~ **re-run on `yolo26s.onnx`**; needs a COCO object held still in frame
- [ ] The Jetson is **not thermally throttling** after five minutes — ~~✅ tj 42.8 → 44.1 °C~~ **re-run**; fp16 ONNX benches level with the old nano `.pt`, so no change is expected
- [x] Working dependency versions recorded and pushed — ✅ re-frozen 16 Sep with onnxruntime-gpu 1.24.0 (Jetson wheel), onnx 1.22.0, onnxslim 0.1.96

**Then update `STATE.md`.**
