#!/usr/bin/env python3
"""fig:fps-gpu (chapter 4) -- detection rate per model/run, and topic rates of one run.

Numbers from records/calibration.md:
  YOLO26n torch standalone 14 Sep, YOLO26s ONNX standalone 16 Sep (301 s),
  YOLO26s ONNX full stack from the 22 Sep demo bag (215.3 s),
  YOLO26l engine standalone 24 Sep 18:58 (15.1-15.2 Hz in 5 s windows),
  YOLO26l engine + SLAM + semantic 24 Sep ~19:05 (detection_report 120 s).
Panel (b) is the 22 Sep bag's topic rates.

    python scripts/plot_fps_gpu_ch4.py   # -> figures/inference_fps_gpu.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GREY, INK, INK2, GRID = "#8a8984", "#0b0b0b", "#52514e", "#e4e3df"

# label, rate, text shown, colour
RUNS = [
    ("YOLO26n PyTorch\nทำงานลำพัง (14 ก.ย.)", 15.15, "15.15", GREY),
    ("YOLO26s ONNX FP16\nทำงานลำพัง (16 ก.ย.)", 15.13, "15.13", ORANGE),
    ("YOLO26s ONNX FP16\nร่วมกับ SLAM และชั้นผสานข้อมูล\n(22 ก.ย.)", 13.05, "13.05", ORANGE),
    ("YOLO26l TensorRT FP16\nทำงานลำพัง (24 ก.ย.)", 15.15, "15.1–15.2", BLUE),
    ("YOLO26l TensorRT FP16\nร่วมกับ SLAM และชั้นผสานข้อมูล\n(24 ก.ย.)", 15.16, "15.16", BLUE),
]
TOPICS = [  # 22 Sep demo bag, 215.3 s
    ("/diff_cont/odom", 29.06, GREY), ("/detections", 13.05, ORANGE),
    ("/image/compressed", 13.04, GREY), ("/scan", 11.60, AQUA),
    ("/semantic_landmarks", 1.87, GREY), ("/map", 0.49, AQUA),
]

plt.rcParams.update({
    "font.family": ["TH Sarabun New", "DejaVu Sans"], "font.size": 17,
    "axes.unicode_minus": False, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
    "axes.titlesize": 20, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "xtick.color": INK2, "ytick.color": INK2,
    "savefig.dpi": 300, "savefig.bbox": "tight", "figure.facecolor": "white",
})

fig, (a, b) = plt.subplots(1, 2, figsize=(13, 6.2),
                           gridspec_kw={"width_ratios": [1.15, 1]})

y = list(range(len(RUNS)))[::-1]
a.barh(y, [r[1] for r in RUNS], height=0.6, color=[r[3] for r in RUNS])
for yi, (_, v, txt, _) in zip(y, RUNS):
    a.annotate(txt, (v, yi), xytext=(6, 0), textcoords="offset points",
               va="center", fontsize=19, color=INK)
a.axvline(5, color=INK2, lw=1.4, ls=(0, (5, 3)))
a.text(5.2, len(RUNS) - 0.4, "เกณฑ์ 5 FPS", color=INK2, fontsize=16, va="bottom")
a.set_yticks(y, [r[0] for r in RUNS], fontsize=15)
a.set_xlim(0, 19.5)
a.set_ylim(-0.6, len(RUNS) + 0.5)
a.set_xlabel("อัตราการเผยแพร่ผลการตรวจจับ (เฟรมต่อวินาที)")
a.set_title("(ก) อัตราเฟรมของการตรวจจับ", loc="left")
a.grid(axis="y", visible=False)
a.text(0.99, 0.99, "GPU เฉลี่ย / อุณหภูมิชิปสูงสุด\n"
       "16 ก.ย. YOLO26s: 57% / 52.0 °C\n24 ก.ย. YOLO26l: 51% / 54.6 °C",
       transform=a.transAxes, ha="right", va="top", fontsize=14, color=INK2,
       bbox=dict(fc="white", ec="none", pad=2))

yt = list(range(len(TOPICS)))[::-1]
b.barh(yt, [t[1] for t in TOPICS], height=0.6, color=[t[2] for t in TOPICS])
for yi, (_, v, _) in zip(yt, TOPICS):
    b.annotate(f"{v:.2f}", (v, yi), xytext=(6, 0), textcoords="offset points",
               va="center", fontsize=17, color=INK)
b.set_yticks(yt, [t[0] for t in TOPICS], fontsize=15)
b.set_xlim(0, 35)
b.set_xlabel("อัตราข้อความ (เฮิรตซ์)")
b.set_title("(ข) หัวข้อที่ทำงานพร้อมกันในรอบเดียว (22 ก.ย.)", loc="left")
b.grid(axis="y", visible=False)
b.text(0.99, 0.02, "สีเขียว = SLAM (/scan, /map)\nข้อมูลจาก rosbag 215.3 วินาที",
       transform=b.transAxes, ha="right", va="bottom", fontsize=14, color=INK2)
fig.tight_layout()

out = os.path.join(os.path.dirname(__file__), "..", "figures", "inference_fps_gpu.png")
fig.savefig(out)
print(os.path.normpath(out))
