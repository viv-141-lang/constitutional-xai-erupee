"""Figure 2: Conceptual framework - 4T-A accountability loop inside data-governance and model-risk layers."""
import pathlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

OUT = pathlib.Path(__file__).resolve().parent.parent / "06_Figures"
NAVY, TEAL, SAND, GREY, INK = "#1F3A5F", "#2A7F62", "#F3EFE6", "#E6EBF0", "#222222"

fig, ax = plt.subplots(figsize=(10, 7.4), dpi=300)
ax.set_xlim(0, 10); ax.set_ylim(0, 7.4); ax.axis("off")

def box(x, y, w, h, fc, ec, lw=1.2, ls="-", r=0.25):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls))

# outer obligations
box(0.15, 0.15, 9.7, 7.1, "white", INK, 1.4)
ax.text(2.6, 6.95, "LEGAL CONSTITUTION", ha="center", fontsize=10, weight="bold", color=NAVY)
ax.text(2.6, 6.62, "Puttaswamy proportionality · DPDP Act 2023\nGDPR Art. 22 · EU AI Act Art. 86", ha="center", va="top", fontsize=7.6, color=NAVY)
ax.text(7.4, 6.95, "SECURITY MANDATE", ha="center", fontsize=10, weight="bold", color="#8C2D19")
ax.text(7.4, 6.62, "PMLA 2002 · FIU-IND / ED\nFATF Recommendation 16", ha="center", va="top", fontsize=7.6, color="#8C2D19")
ax.annotate("", xy=(5.55, 6.78), xytext=(4.45, 6.78), arrowprops=dict(arrowstyle="<->", color="#9A9A9A", lw=1.2))
ax.text(5.0, 6.88, "tension", ha="center", fontsize=7, style="italic", color="#666")

# governance layers
box(0.75, 0.55, 8.5, 5.55, GREY, "#7A8899", 1.0)
ax.text(5.0, 5.8, "MODEL-RISK MANAGEMENT  ·  validation · effective challenge · monitoring", ha="center", fontsize=8.4, weight="bold", color="#4A5868")
box(1.4, 0.95, 7.2, 4.6, SAND, "#B8A98A", 1.0)
ax.text(5.0, 5.22, "DATA GOVERNANCE  ·  principles · quality · metadata/lineage · access · life cycle", ha="center", fontsize=8.4, weight="bold", color="#7A6A48")

# accountability loop
cx, cy, R = 5.0, 3.05, 1.45
ax.add_patch(Circle((cx, cy), 0.86, fc="white", ec=INK, lw=1.2))
ax.text(cx, cy, "Automated\nhold / freeze on a\ncross-border\ne₹ payment", ha="center", va="center", fontsize=8.2, color=INK, weight="bold")
nodes = [  # (angle-position, verb, principle)
    ((cx, cy + R + 0.32), "TRACE", "Traceability"),
    ((cx + R + 1.05, cy), "EXPLAIN", "Transparency"),
    ((cx, cy - R - 0.32), "CONTEST", "Trust (human in the loop)"),
    ((cx - R - 1.05, cy), "CORRECT", "Accountability"),
]
for (x, y), verb, pr in nodes:
    box(x - 0.95, y - 0.33, 1.9, 0.66, NAVY if verb != "CONTEST" else TEAL, "white", 0.8, r=0.18)
    ax.text(x, y + 0.08, verb, ha="center", va="center", fontsize=9.5, color="white", weight="bold")
    ax.text(x, y - 0.17, pr, ha="center", va="center", fontsize=7, color="white")
pts = [(n[0][0], n[0][1]) for n in nodes]
offs = [((0.95, -0.15), (-0.2, 0.33)), ((-0.2, -0.33), (0.95, 0.15)), ((-0.95, 0.15), (0.2, -0.33)), ((0.2, 0.33), (-0.95, -0.15))]
for i in range(4):
    (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 4]
    (a, b), (c, d) = offs[i]
    ax.add_patch(FancyArrowPatch((x1 + a, y1 + b), (x2 + c, y2 + d), connectionstyle="arc3,rad=-0.32",
                                 arrowstyle="-|>", mutation_scale=13, lw=1.4, color=INK))

ax.text(5.0, 0.32, "4T-A principle: every automated intervention must be traced, explained, contestable and correctable",
        ha="center", fontsize=8, style="italic", color="#333")
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"Fig02_Conceptual_Framework.{ext}", bbox_inches="tight", facecolor="white")
print("saved")
