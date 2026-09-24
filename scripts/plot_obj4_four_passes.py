#!/usr/bin/env python3
"""fig:object-error (objective 4) from the four-pass table in records/calibration.md.

The raw session (~/maps/object_accuracy_chair_final.jsonl) lives on the Jetson;
this draws the same numbers the report's tab:obj4 quotes, so figure and table
agree. Errors are the recorded per-pass values; the offsets in panel (a) are
system minus tape of the recorded mean positions.

    python scripts/plot_obj4_four_passes.py   # -> figures/object_position_error.png
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

# label, tape (fwd, left), system (fwd, left), recorded error (m)
PASSES = [
    ("หน้า", (1.60, 0.00), (1.667, -0.023), 0.074, BLUE, (-34, 2)),
    ("ขวา", (1.60, 0.00), (1.503, -0.221), 0.248, ORANGE, (-14, -10)),
    ("หลัง", (1.458, 0.00), (1.347, -0.319), 0.338, AQUA, (8, 4)),
    ("ซ้าย", (1.70, 0.12), (1.783, 0.084), 0.090, YELLOW, (8, 14)),
]
LIMIT = 0.50

plt.rcParams.update({
    "font.family": ["TH Sarabun New", "DejaVu Sans"], "font.size": 17,
    "axes.unicode_minus": False, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "axes.titlesize": 19, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "xtick.color": INK2, "ytick.color": INK2,
    "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight",
    "figure.facecolor": "white",
})

fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.8),
                           gridspec_kw={"width_ratios": [1, 1.1]})

# (a) offset of each pass from its tape position, robot frame, cm.
# x = lateral (right positive, as seen from behind the robot), y = forward.
a.add_patch(plt.Circle((0, 0), LIMIT * 100, fill=False, ec=INK2, lw=1.2,
                       ls=(0, (5, 3))))
a.annotate("วงเส้นประ = เกณฑ์ 50 ซม.", (0, LIMIT * 100), xytext=(0, 4),
           textcoords="offset points", ha="center", va="bottom", color=INK2,
           fontsize=15)
a.scatter([0], [0], marker="*", s=220, color=INK, zorder=5)
a.annotate("ตำแหน่งจริง (ตลับเมตร)", (0, 0), xytext=(-6, -10),
           textcoords="offset points", ha="right", va="top", fontsize=15,
           color=INK)
for name, (tf, tl), (sf, sl), err, c, off in PASSES:
    dx, dy = -(sl - tl) * 100, (sf - tf) * 100
    a.annotate("", (dx, dy), (0, 0),
               arrowprops=dict(arrowstyle="-|>", color=c, lw=1.6,
                               shrinkA=6, shrinkB=4))
    a.scatter([dx], [dy], s=70, color=c, ec="white", lw=1.5, zorder=4)
    a.annotate(name, (dx, dy), xytext=off, textcoords="offset points",
               fontsize=16, color=c, va="center")
a.set_xlim(-58, 58); a.set_ylim(-58, 62); a.set_aspect("equal")
a.set_xlabel("ความคลาดเคลื่อนด้านข้าง (ซม.)   ซ้าย << >> ขวา")
a.set_ylabel("ความคลาดเคลื่อนตามแนวหน้า (ซม.)")
a.set_title("(ก) ตำแหน่งที่ระบบรายงานเทียบตำแหน่งจริง", loc="left")

# (b) error per viewpoint against the criterion.
names = [p[0] for p in PASSES]
errs = [p[3] * 100 for p in PASSES]
bars = b.bar(range(4), errs, width=0.6, ec="white", lw=2,
             color=[p[4] for p in PASSES])
for bar, e in zip(bars, errs):
    b.annotate(f"{e:.1f} ซม.", (bar.get_x() + bar.get_width() / 2, e),
               xytext=(0, 3), textcoords="offset points", ha="center",
               fontsize=15, color=INK)
b.axhline(LIMIT * 100, color=INK2, lw=1.2, ls=(0, (5, 3)))
b.annotate("เกณฑ์ 50 ซม.", (1.0, LIMIT * 100), xycoords=("axes fraction", "data"),
           xytext=(-2, 3), textcoords="offset points", ha="right", va="bottom",
           color=INK2, fontsize=15)
mean = sum(errs) / len(errs)
b.axhline(mean, color=INK2, lw=1, ls=":")
b.annotate(f"เฉลี่ย {mean:.1f} ซม.", (1.0, mean), xycoords=("axes fraction", "data"),
           xytext=(-2, 3), textcoords="offset points", ha="right", va="bottom",
           color=INK2, fontsize=15)
b.set_xticks(range(4), names)
b.set_ylim(0, 60)
b.set_xlabel("ทิศทางที่หุ่นยนต์มองวัตถุ")
b.set_ylabel("ความคลาดเคลื่อน (ซม.)")
b.set_title("(ข) ความคลาดเคลื่อนแต่ละทิศทาง", loc="left")
b.grid(axis="x", visible=False)
fig.tight_layout()

out = os.path.join(os.path.dirname(__file__), "..", "figures",
                   "object_position_error.png")
fig.savefig(out)
print(f"mean {mean:.1f} cm, worst {max(errs):.1f} cm -> {os.path.normpath(out)}")
for name, (tf, tl), (sf, sl), err, *_ in PASSES:
    print(f"  {name}: fwd {sf-tf:+.3f}  left {sl-tl:+.3f}  "
          f"|mean offset| {math.hypot(sf-tf, sl-tl)*100:.1f}  recorded {err*100:.1f} cm")
