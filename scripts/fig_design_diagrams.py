"""Figures 3, 6, 7 and 15: research design, friction heatmap, three-tier architecture, adoption pathway.
Diagrams are drawn in inch coordinates (1 data unit = 1 inch) at about 7.5 in wide, so that when Word scales them to the
6.5 in text width every label prints at 7.5 pt or larger (checked with figcheck.py)."""
import pathlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import ListedColormap
import numpy as np

FIG = pathlib.Path(__file__).resolve().parent.parent / "06_Figures"
NAVY, TEAL, RUST, SAND, GREY, INK, LIGHT = "#1F3A5F", "#2A7F62", "#B5523B", "#F3EFE6", "#7C8794", "#222222", "#E6EBF0"
plt.rcParams.update({"font.size": 8.8, "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"]})
FS = 9.4                                                        # body text in boxes (prints at about 8.1 pt)


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=300)
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    return fig, ax


def box(ax, x, y, w, h, text, fc=NAVY, tc="white", fs=FS, bold=False, ec="white", r=0.06, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=0.9, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            weight="bold" if bold else "normal", linespacing=1.15)


def arrow(ax, p, q, color=INK, rad=0.0, ls="-", lw=1.1):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=10, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls))


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", pad_inches=0.04, facecolor="white"); plt.close(fig)


# ---------------------------------------------------------------- Figure 3: research design (DSR)
fig, ax = canvas(7.5, 2.85)
steps = [("1. Problem\nidentification", "Section 1:\nNexus\nscreening gap"),
         ("2. Objectives\nand RQs", "RQ1–RQ3\n(Table 1)"),
         ("3. Comparative\npolicy\nanalysis", "11 instruments\ncoded into a\nfriction matrix\n(RQ1)"),
         ("4. Artefact\ndesign", "4T-A principle;\nthree-tier\narchitecture\n(RQ2)"),
         ("5. Demon-\nstration", "AML experiment,\nfive scenarios,\nwelfare experiment"),
         ("6. Evaluation", "Ablation,\n20 seeds,\nlatency,\nname test"),
         ("7. Communi-\ncation and\nadoption", "Legacy\npathway (RQ3);\nfuture research")]
w, gap, x0, yb, hb = 0.95, 0.12, 0.06, 1.2, 0.9
for i, (t, sub) in enumerate(steps):
    x = x0 + i * (w + gap)
    box(ax, x, yb, w, hb, t, fc=TEAL if i in (2, 4, 5) else NAVY, bold=True)
    ax.text(x + w / 2, yb - 0.08, sub, ha="center", va="top", fontsize=9.3, color="#333", linespacing=1.15)
    if i < len(steps) - 1:
        arrow(ax, (x + w, yb + hb / 2), (x + w + gap, yb + hb / 2))
x5 = x0 + 5 * (w + gap) + w / 2; x3 = x0 + 3 * (w + gap) + w / 2
arrow(ax, (x5, yb + hb + 0.03), (x3, yb + hb + 0.03), color=RUST, rad=0.3, ls="--")
ax.text((x3 + x5) / 2, 2.62, "iterate: evaluation results revise the rulebook", ha="center", fontsize=9.3, color=RUST, style="italic")
ax.text(x0, 0.3, "Teal = evidence-producing stages. Data: secondary documents and synthetic payments; no personal data used.",
        fontsize=9.3, color="#444")
save(fig, "Fig03_Research_Design.png")

# ---------------------------------------------------------------- Figure 6: friction heatmap (coded documents, revised after legal review)
inst = ["RBI CBDC Concept Note (2022)", "RBI payment-data storage (2018)", "Project Nexus / NGP rules",
        "FATF Recommendation 16", "PMLA 2002", "EU AML Regulation 2024/1624", "EU Transfer of Funds Reg. 2023/1113",
        "Puttaswamy (2017) / Aadhaar (2018)", "DPDP Act 2023", "GDPR (Art. 22)", "EU AI Act (Art. 86)"]
axes = ["A1\nSpeed and\nfinality", "A2\nScreening\nand tracing", "A3\nExplanation\nand contest", "A4\nMinimisation\nand\nlocalisation", "A5\nHuman\noversight"]
M = np.array([[2, 1, 0, 1, 0],
              [0, 0, 0, 2, 0],
              [2, 2, 0, 0, 0],
              [0, 2, 0, 0, 0],
              [0, 2, -1, 0, 0],
              [0, 2, -1, 1, 0],
              [0, 2, 0, 1, 0],
              [0, 1, 1, 2, 0],
              [0, 1, 1, 2, 0],
              [0, 0, 1, 2, 1],
              [0, 0, 1, 0, 1]])
side = ["IN", "IN", "Multi", "Intl", "IN", "EU", "EU", "IN", "IN", "EU", "EU"]
fig, ax = plt.subplots(figsize=(6.6, 5.8), dpi=300)
ax.imshow(M, cmap=ListedColormap(["#E8B4A6", "#F4F4F4", "#9FC5B8", NAVY]), vmin=-1, vmax=2, aspect="auto")
lab = {-1: "restricts", 0: "–", 1: "partial", 2: "requires"}
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, lab[M[i, j]], ha="center", va="center", fontsize=9.3, color="white" if M[i, j] == 2 else "#222")
ax.set_xticks(range(5)); ax.set_xticklabels(axes, fontsize=9.3)
ax.set_yticks(range(len(inst))); ax.set_yticklabels([f"{n}  [{s}]" for n, s in zip(inst, side)], fontsize=9.3)
ax.xaxis.tick_top()
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_xticks(np.arange(-.5, 5), minor=True); ax.set_yticks(np.arange(-.5, len(inst)), minor=True)
ax.grid(which="minor", color="white", lw=2); ax.tick_params(which="both", length=0)
ax.add_patch(plt.Rectangle((-0.46, -0.46), 1.92, 6.92, fill=False, ec=RUST, lw=1.8, ls="--", zorder=5, clip_on=False))
ax.add_patch(plt.Rectangle((1.54, -0.46), 0.92, 10.92, fill=False, ec=TEAL, lw=1.8, ls="--", zorder=5, clip_on=False))
ax.text(4.62, 2.6, "Payment and AML\ninstruments\ndemand speed\nand tracing\n(red box)", fontsize=9.3, color=RUST, va="center")
ax.text(4.62, 7.8, "No instrument\nrequires reasons\nfor automated\nAML holds; AML\nlaw restricts\nthem (green\ncolumn)", fontsize=9.3, color=TEAL, va="center")
ax.set_xlim(-0.5, 6.0)
save(fig, "Fig04_Friction_Matrix.png")

# ---------------------------------------------------------------- Figure 7: three-tier architecture
fig, ax = canvas(7.5, 4.9)
tiers = [(3.4, "TIER 1 · DOMESTIC EDGE (bank / token service provider)", LIGHT),
         (1.72, "TIER 2 · CONSTITUTIONAL XAI ENGINE (neuro-symbolic core)", SAND),
         (0.04, "TIER 3 · CROSS-BORDER SETTLEMENT (Nexus gateway / receiving PSP)", LIGHT)]
TH = 1.48
for y, t, c in tiers:
    ax.add_patch(FancyBboxPatch((0.04, y), 6.1, TH, boxstyle="round,pad=0,rounding_size=0.08", fc=c, ec="#8A8A8A", lw=0.9))
    ax.text(0.15, y + TH - 0.2, t, fontsize=9.6, weight="bold", color=INK)
BH = 0.98
# tier 1
y1 = 3.4 + 0.1
box(ax, 0.15, y1, 1.3, BH, "Payer initiates\ne₹ / UPI\npayment", fc="white", tc=INK, ec=INK)
box(ax, 1.65, y1, 1.45, BH, "Wallet classifier:\nstandard,\npurpose-bound\nor offline")
box(ax, 3.3, y1, 1.45, BH, "Welfare rules\nW1–W8: hybrid\npayee rule, offline\ncap ₹5,000")
box(ax, 4.95, y1, 1.1, BH, "FATF R.16\ndata\ncompleteness")
for a, b in [(1.45, 1.65), (3.1, 3.3), (4.75, 4.95)]:
    arrow(ax, (a, y1 + BH / 2), (b, y1 + BH / 2))
# tier 2
y2 = 1.72 + 0.1
box(ax, 0.15, y2, 1.3, BH, "Learned risk\nmodel + sanctions\nname screen", fc=TEAL)
box(ax, 1.65, y2, 1.2, BH, "Exact Shapley\nattribution\n(top reasons)", fc=TEAL)
box(ax, 3.05, y2, 1.55, BH, "Machine-readable\nconstitution\n(rules R1–R4,\nSuppl. Table S4)")
box(ax, 4.8, y2, 1.25, BH, "Decision +\nreasons +\ncounterfactual →\nhash-chained log")
for a, b in [(1.45, 1.65), (2.85, 3.05), (4.6, 4.8)]:
    arrow(ax, (a, y2 + BH / 2), (b, y2 + BH / 2))
arrow(ax, (5.5, y1), (5.5, y2 + BH))
# tier 3
y3 = 0.04 + 0.1
# flow runs right to left here so the hand-off from Tier 2 drops straight down without crossing the tier title
box(ax, 4.3, y3, 1.75, BH, "ISO 20022 message +\ncompliance\nattestation (reasons,\nnot raw data)")
box(ax, 2.8, y3, 1.3, BH, "Nexus gateway:\nFX, addressing,\nsettlement")
box(ax, 0.15, y3, 2.45, BH, "Receiving PSP screens\nits own lists; reason\ncodes returned on\nany stop")
arrow(ax, (4.3, y3 + BH / 2), (4.1, y3 + BH / 2)); arrow(ax, (2.8, y3 + BH / 2), (2.6, y3 + BH / 2))
arrow(ax, (5.3, y2), (5.3, y3 + BH))
# side channels
box(ax, 6.3, 3.5, 1.16, 1.28, "CONTEST\nhuman review\ndesk /\nombudsman\n(Trust)", fc=TEAL)
box(ax, 6.3, 1.82, 1.16, 1.28, "SECURITY\nFIU-IND / ED\nalert with\nevidence pack\n(R4)", fc=RUST)
box(ax, 6.3, 0.14, 1.16, 1.28, "SHARED\nNETWORK\npseudonymous\ntypology\nmonitoring\n(Scenario 5)", fc=NAVY)
arrow(ax, (6.05, y2 + 0.8), (6.3, 3.9), color=TEAL); arrow(ax, (6.05, y2 + 0.45), (6.3, 2.4), color=RUST)
arrow(ax, (6.05, y3 + 0.45), (6.3, 0.75), color=NAVY)
save(fig, "Fig05_Three_Tier_Architecture.png")

# ---------------------------------------------------------------- Figure 15: adoption pathway + future research
fig, ax = canvas(7.5, 3.25)
phases = [("Phase 0\nToday", "Correspondent\nbanking, ISO 20022,\nopaque screening\nscores", GREY),
          ("Phase 1\nSidecar", "Explanation and\naudit layer beside\nexisting screening;\nno rail change", NAVY),
          ("Phase 2\nSandbox", "RBI regulatory\nsandbox; shared\npseudonymous\nmonitoring", NAVY),
          ("Phase 3\nScheme rule", "Nexus scheme\nrulebook: reason\ncodes required\non every stop", NAVY),
          ("Phase 4\nRecognition", "India–EU mutual\nrecognition; public\ncompliance\nbenchmark", TEAL)]
w, gap = 1.3, 0.235
for i, (t, s, c) in enumerate(phases):
    x = 0.05 + i * (w + gap)
    ax.add_patch(FancyBboxPatch((x, 1.62), w, 1.58, boxstyle="round,pad=0,rounding_size=0.06", fc=c, ec="white", lw=0.9))
    ax.text(x + w / 2, 3.12, t, ha="center", va="top", fontsize=FS, color="white", weight="bold", linespacing=1.1)
    ax.text(x + w / 2, 2.6, s, ha="center", va="top", fontsize=FS, color="white", linespacing=1.15)
    if i < 4:
        arrow(ax, (x + w, 2.45), (x + w + gap, 2.45))
frq = ["FRQ1: latency at\npeak load (RBI\nsandbox, real\nvolumes)",
       "FRQ2: does a\nwritten constitution\nreduce unjustified\nfreezes? (LLM test)",
       "FRQ3: robustness\nto AI-enabled\nfraud and\ncyber attack"]
for k, t in enumerate(frq):
    cx = 0.05 + (k + 1) * (w + gap) + w / 2
    box(ax, cx - 0.72, 0.05, 1.44, 1.0, t, fc="white", tc=RUST, ec=RUST, ls="--")
    arrow(ax, (cx, 1.05), (cx, 1.62), color=RUST, ls=":")
cx = 0.05 + 4 * (w + gap) + w / 2
box(ax, cx - w / 2, 0.05, w, 1.0, "Welfare pilot with\na real scheme", fc="white", tc=RUST, ec=RUST, ls="--")
arrow(ax, (cx, 1.05), (cx, 1.62), color=RUST, ls=":")
ax.text(0.05, 0.55, "Future research\nquestions\n(Section 5.5)", fontsize=FS, color=RUST, weight="bold", va="center")
save(fig, "Fig10_Adoption_Pathway.png")
print("saved Figures 3, 6, 7, 15")
