"""Figure 2: Conceptual framework - 4T-A accountability loop inside data-governance and model-risk layers.
Drawn in inch coordinates at 7.2 in wide so that, at the 6.5 in text width, the smallest text prints at about 7.8 pt."""
import pathlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

OUT = pathlib.Path(__file__).resolve().parent.parent / "06_Figures"
NAVY, TEAL, SAND, GREY, INK, RED = "#1F3A5F", "#2A7F62", "#F3EFE6", "#E6EBF0", "#222222", "#8C2D19"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"]})
W, H = 7.2, 5.9
fig, ax = plt.subplots(figsize=(W, H), dpi=300)
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off"); fig.subplots_adjust(0, 0, 1, 1)


def box(x, y, w, h, fc, ec, lw=1.2, r=0.18):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))


# outer obligations
box(0.05, 0.05, W - 0.1, H - 0.1, "white", INK, 1.4)
ax.text(1.85, 5.5, "LEGAL CONSTITUTION", ha="center", fontsize=10.5, weight="bold", color=NAVY)
ax.text(1.85, 5.3, "Puttaswamy proportionality ·\nDPDP Act 2023 · GDPR Art. 22 ·\nEU AI Act Art. 86",
        ha="center", va="top", fontsize=9.2, color=NAVY, linespacing=1.15)
ax.text(5.35, 5.5, "SECURITY MANDATE", ha="center", fontsize=10.5, weight="bold", color=RED)
ax.text(5.35, 5.3, "PMLA 2002 · FIU-IND / ED\nFATF Recommendation 16", ha="center", va="top", fontsize=9.2, color=RED, linespacing=1.15)
ax.annotate("", xy=(4.05, 5.25), xytext=(3.15, 5.25), arrowprops=dict(arrowstyle="<->", color="#8A8A8A", lw=1.2))
ax.text(3.6, 5.35, "tension", ha="center", fontsize=9.2, style="italic", color="#555")

# governance layers
box(0.3, 0.5, W - 0.6, 4.05, GREY, "#7A8899", 1.0, r=0.2)
ax.text(W / 2, 4.3, "MODEL-RISK MANAGEMENT  ·  validation · effective challenge · monitoring",
        ha="center", fontsize=9.2, weight="bold", color="#3F4D5C")
box(0.6, 0.68, W - 1.2, 3.5, SAND, "#B8A98A", 1.0, r=0.2)
ax.text(W / 2, 3.93, "DATA GOVERNANCE  ·  principles · quality · metadata / lineage · access · life cycle",
        ha="center", fontsize=9.2, weight="bold", color="#6A5A38")

# accountability loop
cx, cy = W / 2, 2.25
ax.add_patch(Circle((cx, cy), 0.66, fc="white", ec=INK, lw=1.2))
ax.text(cx, cy, "Automated\nhold or freeze\non a cross-\nborder e₹\npayment", ha="center", va="center",
        fontsize=9.2, color=INK, weight="bold", linespacing=1.1)
BW, BH = 1.5, 0.62
nodes = [((cx, 3.33), "TRACE", "Traceability"),
         ((cx + 1.85, cy), "EXPLAIN", "Transparency"),
         ((cx, 1.13), "CONTEST", "Trust (human in the loop)"),
         ((cx - 1.85, cy), "CORRECT", "Accountability")]
for (x, y), verb, pr in nodes:
    box(x - BW / 2, y - BH / 2, BW, BH, TEAL if verb == "CONTEST" else NAVY, "white", 0.8, r=0.12)
    ax.text(x, y + 0.1, verb, ha="center", va="center", fontsize=10, color="white", weight="bold")
    ax.text(x, y - 0.15, pr, ha="center", va="center", fontsize=9.2, color="white")
(tx, ty), (ex, ey), (kx, ky), (rx, ry) = [n[0] for n in nodes]
links = [((tx + BW / 2, ty), (ex, ey + BH / 2)), ((ex, ey - BH / 2), (kx + BW / 2, ky)),
         ((kx - BW / 2, ky), (rx, ry - BH / 2)), ((rx, ry + BH / 2), (tx - BW / 2, ty))]
for p, q in links:
    ax.add_patch(FancyArrowPatch(p, q, connectionstyle="arc3,rad=-0.3", arrowstyle="-|>", mutation_scale=13, lw=1.4, color=INK))

ax.text(W / 2, 0.22, "4T-A principle: every automated intervention must be traced, explained, contestable and correctable",
        ha="center", fontsize=9.2, style="italic", color="#333")
for ext in ("png", "svg"):
    fig.savefig(OUT / f"Fig02_Conceptual_Framework.{ext}", bbox_inches="tight", pad_inches=0.03, facecolor="white")
print("saved")
