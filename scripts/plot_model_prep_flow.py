#!/usr/bin/env python3
"""fig:onnx-export (chapter 4) -- what `make yolo` does before the node starts.

Mirrors cap_ws/Makefile (yolo: yolo-onnx yolo-engine) and cap_ws/yolo/export_engine.py:
MODEL defaults to ~/yolo/yolo26l_480x640.engine (D-30); the .onnx path is the
first-release fallback (export_onnx.py, unchanged).

    python scripts/plot_model_prep_flow.py   # -> figures/model_prep_flow.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon  # noqa: E402

BLUE, BLUE_BG = "#2a78d6", "#e8f1fb"
GREEN, GREEN_BG = "#1baf7a", "#e8f7f0"
RED, RED_BG = "#eb6834", "#fdf0ea"
GREY, GREY_BG = "#8a8984", "#f3f2ef"
INK, INK2 = "#0b0b0b", "#52514e"

plt.rcParams.update({"font.family": ["TH Sarabun New", "DejaVu Sans"],
                     "font.size": 17, "savefig.dpi": 300, "savefig.bbox": "tight",
                     "figure.facecolor": "white"})
fig, ax = plt.subplots(figsize=(17, 6.6))
ax.set_xlim(0, 170); ax.set_ylim(1, 70); ax.axis("off")


def box(x, y, w, h, text, ec=INK2, fc=GREY_BG, lw=1.3, round_=False, bold=None):
    style = "round,pad=0,rounding_size=3.2" if round_ else "square,pad=0"
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=style,
                                ec=ec, fc=fc, lw=lw))
    ax.text(x, y, text, ha="center", va="center", color=INK, linespacing=1.25,
            fontsize=16, fontweight=bold)
    return (x, y, w, h)


def diamond(x, y, w, h, text):
    ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2),
                          (x - w / 2, y)], closed=True, ec=INK2, fc=GREY_BG, lw=1.3))
    ax.text(x, y, text, ha="center", va="center", color=INK, fontsize=16,
            linespacing=1.2)


def arrow(p, q, label=None, color=INK2, lpos=0.5, loff=(0, 1.6)):
    ax.annotate("", q, p, arrowprops=dict(arrowstyle="-|>", color=color, lw=1.4,
                                          shrinkA=0, shrinkB=0))
    if label:
        lx = p[0] + (q[0] - p[0]) * lpos + loff[0]
        ly = p[1] + (q[1] - p[1]) * lpos + loff[1]
        ax.text(lx, ly, label, ha="center", va="bottom", fontsize=15, color=color)


# row 1: the deployed TensorRT path
Y = 44
box(7, Y, 11, 7, "make yolo", round_=True)
diamond(25, Y, 18, 15, "ไฟล์แบบจำลอง\nเป็นชนิดใด")
diamond(49, Y, 20, 15, "มีเครื่องยนต์\nyolo26l_480x640\n.engine แล้ว?")
diamond(73, Y, 18, 15, "มี yolo26l.pt?")
diamond(96, Y, 20, 15, "หน่วยความจำว่าง\n≥ 4.5 GB?")
box(122, Y, 24, 15, "สร้างเครื่องยนต์ TensorRT\nFP16 · 480×640 · batch 1\nในโฟลเดอร์ชั่วคราว\n~13–14 นาที · ~3.1 GB",
    ec=BLUE, fc=BLUE_BG, lw=2)
box(154, Y + 16, 28, 15, "โหนดตรวจจับ\nYOLO26l TensorRT FP16\nค่าความเชื่อมั่น 0.4\n(ใช้งานจริง)",
    ec=GREEN, fc=GREEN_BG, lw=2, round_=True)

arrow((12.5, Y), (16, Y))
arrow((34, Y), (39, Y), ".engine\n(ค่าเริ่มต้น)", color=BLUE, loff=(0, 1.2))
arrow((59, Y), (64, Y), "ไม่มี", loff=(0, 1.0))
arrow((82, Y), (86, Y), "มี", loff=(0, 1.0))
arrow((106, Y), (110, Y), "พอ", loff=(0, 1.0))
# built -> move into place -> node
arrow((134, Y + 3), (140, Y + 12), "ย้ายไป\nตำแหน่งจริง", lpos=0.5, loff=(7, -4))
# engine exists -> node (skip the build)
ax.plot([49, 49, 140], [Y + 7.5, Y + 16, Y + 16], color=INK2, lw=1.4)
arrow((139, Y + 16), (140, Y + 16))
ax.text(95, Y + 16.8, "มีแล้ว: ข้ามการสร้าง (เสียเวลาเฉพาะครั้งแรก)",
        ha="center", va="bottom", fontsize=15, color=INK2)

# refusals
box(73, 20, 20, 8, "หยุด · แจ้งให้\nดาวน์โหลดน้ำหนักก่อน", ec=RED, fc=RED_BG)
box(96, 20, 20, 8, "หยุด · ให้ปิดส่วนอื่น\nของระบบก่อน", ec=RED, fc=RED_BG)
arrow((73, Y - 7.5), (73, 24), "ไม่มี", lpos=0.45, loff=(3.5, -1))
arrow((96, Y - 7.5), (96, 24), "ไม่พอ", lpos=0.45, loff=(4, -1))

# row 2: the first-release ONNX fallback
Y2 = 8
box(49, Y2, 34, 10, "ตรวจ / ส่งออก yolo26s.onnx\nFP16 · 640×640 (ขั้นตอนของรุ่นแรก)",
    ec=GREY, fc="white", lw=1.3)
box(154, Y2, 28, 10, "โหนดตรวจจับ YOLO26s\nONNX Runtime (CUDA)", ec=GREY, fc="white",
    round_=True)
ax.plot([25, 25], [Y - 7.5, Y2], color=GREY, lw=1.4)
arrow((25, Y2), (32, Y2))
ax.text(23.5, 22, ".onnx\n(สำรอง)", ha="right", va="center", fontsize=15, color=GREY)
arrow((66, Y2), (140, Y2), "ผ่าน", color=GREY, loff=(0, 0.8))

fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "..", "figures", "model_prep_flow.png")
fig.savefig(out)
print(os.path.normpath(out))
