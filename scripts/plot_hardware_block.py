#!/usr/bin/env python3
"""fig:hwblock (chapter 3) -- hardware connections. Redrawn from the earlier
diagram with the detector updated to the deployed YOLO26l TensorRT (D-30).

    python scripts/plot_hardware_block.py   # -> figures/hardware_block_diagram.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

BLUE, BLUE_BG = "#2a78d6", "#e8f1fb"
GREEN, GREEN_BG = "#1baf7a", "#e8f7f0"
RED, RED_BG = "#eb6834", "#fdf0ea"
GREY, GREY_BG, PANEL = "#8a8984", "#f3f2ef", "#fafaf8"
INK, INK2 = "#0b0b0b", "#52514e"

plt.rcParams.update({"font.family": ["TH Sarabun New", "DejaVu Sans"],
                     "font.size": 17, "savefig.dpi": 300, "savefig.bbox": "tight",
                     "figure.facecolor": "white"})
fig, ax = plt.subplots(figsize=(17, 7))
ax.set_xlim(0, 200); ax.set_ylim(0, 80); ax.axis("off")


def panel(x0, y0, x1, y1, title):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="square,pad=0",
                                ec="#c9c8c2", fc=PANEL, lw=1))
    ax.text((x0 + x1) / 2, y1 - 1.2, title, ha="center", va="top", fontsize=16,
            color=INK)


def box(x, y, w, h, title, lines, ec, fc, lw=1.3):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="square,pad=0",
                                ec=ec, fc=fc, lw=lw))
    ax.text(x, y + h / 2 - 3.2 if lines else y, title, ha="center", va="center",
            fontsize=17, fontweight="bold", color=INK)
    if lines:
        ax.text(x, y + h / 2 - 5.6, "\n".join(lines), ha="center", va="top",
                fontsize=16, color=INK, linespacing=1.55)


def link(p, q, label=None, lpos=0.5, loff=(0, 0), both=False, dashed=False):
    ax.annotate("", q, p, arrowprops=dict(
        arrowstyle="<|-|>" if both else "-|>", color=INK2, lw=1.3,
        ls=(0, (2, 2)) if dashed else "-", shrinkA=0, shrinkB=0,
        connectionstyle="arc3,rad=0"))
    if label:
        lx = p[0] + (q[0] - p[0]) * lpos + loff[0]
        ly = p[1] + (q[1] - p[1]) * lpos + loff[1]
        ax.text(lx, ly, label, ha="center", va="center", fontsize=15, color=INK2,
                bbox=dict(fc="white", ec="none", pad=1.5), linespacing=1.4)


# drivetrain panel
panel(50, 46, 198, 79, "ชุดขับเคลื่อน")
box(65, 69, 15, 11, "MPU6050", ["ไจโรสโคป"], RED, RED_BG)
box(110, 67, 21, 11, "ESP32 DevKit", ["PID · PWM · PCNT"], RED, RED_BG)
box(149, 57, 18, 11, "L298N", ["โมดูลขับมอเตอร์"], RED, RED_BG)
box(185, 62, 19, 11, "มอเตอร์ DC × 2", ["พร้อมเอนโคเดอร์"], RED, RED_BG)

# sensors panel
panel(1, 3, 30, 38, "เซนเซอร์")
box(15.5, 27, 23, 11, "YDLIDAR X3 Pro", ["ไลดาร์ 2 มิติ · 11.6 Hz"], GREEN, GREEN_BG)
box(15.5, 11, 23, 11, "Logitech C615", ["กล้องยูเอสบี 640×480"], GREEN, GREEN_BG)

# compute, battery, browser
box(65, 21, 25, 30, "MIC-711-ON",
    ["(Jetson Orin NX)", "ROS 2 Humble", "slam_toolbox · Nav2", "YOLO26l TensorRT (GPU)",
     "FastAPI"], BLUE, BLUE_BG, lw=2)
box(110, 36, 14, 11, "แบตเตอรี่", ["7.4–12 V"], GREY, GREY_BG)
box(110, 11, 26, 11, "เบราว์เซอร์", ["Web Dashboard (React)"], GREY, GREY_BG)

link((72.5, 69), (99.5, 67), "I²C", both=True, loff=(0, 1.5))
link((177, 66.5), (120.5, 70), "สัญญาณ A/B", lpos=0.45, loff=(0, 2.2))
link((120.5, 64), (140, 58), "PWM · IN1–IN4", lpos=0.5, loff=(0, 2.3))
link((158, 57.5), (175.5, 61), "ไฟเลี้ยงมอเตอร์", lpos=0.5, loff=(0, -2.5))
link((110, 41.5), (141, 54), "12 V", lpos=0.55, loff=(-2, 1.5))
link((103, 61.5), (70, 37), "USB · 57600 Bd\n/dev/esp32", lpos=0.45, loff=(4, 0), both=True)
link((27, 27), (52.5, 27), "USB · 115200 Bd\n/dev/ydlidar", lpos=0.5, loff=(0, 3.8))
link((27, 11), (52.5, 11), "USB (UVC)", lpos=0.5, loff=(0, 2))
link((77.5, 11), (97, 11), "WiFi · WebSocket", lpos=0.5, loff=(0, 2), both=True,
     dashed=True)

fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "..", "figures", "hardware_block_diagram.png")
fig.savefig(out)
print(os.path.normpath(out))
