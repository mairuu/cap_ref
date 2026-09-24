#!/usr/bin/env python3
"""fig:infer-bench (chapter 2) from the model-cost table in records/objective-tests.md.

That table (cap_ws/yolo/model_footprint.py, 24 Sep 2026, nvpmodel 15 W, nothing
else on the GPU, real frames) is the only run that measured every candidate the
same way, the deployed yolo26l engine included. Inference time only: the
script's track() wall runs high (its sampling thread shares the GIL).

    python scripts/plot_inference_cost.py   # -> figures/inference_time_comparison.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE, ORANGE = "#2a78d6", "#eb6834"
GREY, INK, INK2, GRID = "#8a8984", "#0b0b0b", "#52514e", "#e4e3df"

# label, inference ms, GPU load %, colour
ROWS = [
    ("YOLO26s\nONNX FP16\n(เดิม)", 36.7, 50.7, ORANGE),
    ("YOLO26s\nPyTorch", 36.0, 53.6, GREY),
    ("YOLO26m\nPyTorch", 59.1, 62.2, GREY),
    ("YOLO26l\nPyTorch", 74.4, 68.9, GREY),
    ("YOLO26l\nTensorRT FP16\n(ใช้งานจริง)", 36.4, 44.8, BLUE),
]

plt.rcParams.update({
    "font.family": ["TH Sarabun New", "DejaVu Sans"], "font.size": 19,
    "axes.unicode_minus": False, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "xtick.color": INK2, "ytick.color": INK2,
    "savefig.dpi": 300, "savefig.bbox": "tight", "figure.facecolor": "white",
})

fig, ax = plt.subplots(figsize=(8.6, 5.4))
x = range(len(ROWS))
bars = ax.bar(x, [r[1] for r in ROWS], width=0.6, ec="white", lw=2,
              color=[r[3] for r in ROWS])
for bar, (_, ms, gpu, _) in zip(bars, ROWS):
    cx = bar.get_x() + bar.get_width() / 2
    ax.annotate(f"{ms:.1f}", (cx, ms), xytext=(0, 4), textcoords="offset points",
                ha="center", va="bottom", fontsize=22, color=INK)
    ax.text(cx, 2.5, f"GPU {gpu:.0f}%", ha="center", va="bottom",
            fontsize=16, color="white")

# the step the chapter is about: same model, PyTorch -> TensorRT
ax.annotate("", xy=(3.68, 39), xytext=(3.32, 71),
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.6,
                            connectionstyle="arc3,rad=-0.3"))
ax.text(3.72, 64, "TensorRT\nลดลง 51%", ha="left", va="center",
        fontsize=17, color=BLUE)

ax.set_xticks(list(x), [r[0] for r in ROWS], fontsize=17)
ax.set_ylabel("เวลาอนุมานต่อเฟรม (มิลลิวินาที)")
ax.set_ylim(0, 95)
ax.grid(axis="x", visible=False)
ax.text(0.02, 1.0, "Jetson Orin NX 8 GB โหมดพลังงาน 15 วัตต์ ภาพจริงจากกล้อง\n"
        "ไม่มีงานอื่นใช้หน่วยประมวลผลกราฟิก (ไม่รวม ByteTrack)",
        transform=ax.transAxes, ha="left", va="top", fontsize=16, color=INK2)
fig.tight_layout()

out = os.path.join(os.path.dirname(__file__), "..", "figures",
                   "inference_time_comparison.png")
fig.savefig(out)
print(os.path.normpath(out))
