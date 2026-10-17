"""Figures 3, 4, 5, 9: research design, friction heatmap, three-tier architecture, adoption pathway."""
import pathlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

FIG = pathlib.Path(__file__).resolve().parent.parent / "06_Figures"
NAVY, TEAL, RUST, SAND, GREY, INK, LIGHT = "#1F3A5F", "#2A7F62", "#B5523B", "#F3EFE6", "#9AA5B1", "#222222", "#E6EBF0"
plt.rcParams.update({"font.size": 8})


def box(ax, x, y, w, h, text, fc=NAVY, tc="white", fs=7.6, bold=False, ec="white", r=0.06):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            weight="bold" if bold else "normal", linespacing=1.2)


def arrow(ax, p, q, color=INK, rad=0.0, ls="-", lw=1.1):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=10, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls))


# ---------------------------------------------------------------- Figure 3: research design (DSR)
fig, ax = plt.subplots(figsize=(10, 3.6), dpi=300); ax.set_xlim(0, 10); ax.set_ylim(0, 3.6); ax.axis("off")
steps = [("1. Problem\nidentification", "Ch 1 · Nexus\nscreening gap"),
         ("2. Objectives\n& RQs", "RQ1–RQ3\nTable 1"),
         ("3. Comparative\npolicy analysis", "9 instruments coded\n→ friction matrix (RQ1)"),
         ("4. Artefact\ndesign", "4T-A principle\n3-tier architecture (RQ2)"),
         ("5. Demonstration", "Synthetic experiment\n+ 5 scenarios"),
         ("6. Evaluation", "Ablation · sensitivity ·\nlatency · 4T-A criteria"),
         ("7. Communication\n& adoption", "Legacy pathway (RQ3)\nfuture research")]
w, gap = 1.22, 0.19
for i, (t, sub) in enumerate(steps):
    x = 0.12 + i * (w + gap)
    box(ax, x, 1.75, w, 0.95, t, fc=TEAL if i in (2, 4, 5) else NAVY, bold=True, fs=7.6)
    ax.text(x + w / 2, 1.55, sub, ha="center", va="top", fontsize=6.8, color="#333", linespacing=1.2)
    if i < len(steps) - 1:
        arrow(ax, (x + w, 2.22), (x + w + gap, 2.22))
x5 = 0.12 + 5 * (w + gap) + w / 2; x3 = 0.12 + 3 * (w + gap) + w / 2
arrow(ax, (x5, 2.72), (x3, 2.72), color=RUST, rad=0.35, ls="--")
ax.text((x3 + x5) / 2, 3.32, "iterate: evaluation results revise the rulebook", ha="center", fontsize=7, color=RUST, style="italic")
ax.text(0.12, 0.25, "Teal = evidence-producing stages. Secondary documentary data + synthetic data; no personal data used.",
        fontsize=6.8, color="#555")
fig.savefig(FIG / "Fig03_Research_Design.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---------------------------------------------------------------- Figure 4: friction heatmap (coded documents)
inst = ["RBI CBDC Concept Note (2022)", "RBI payment-data storage (2018)", "Project Nexus / NGP rules",
        "FATF Recommendation 16", "PMLA 2002", "Puttaswamy (2017)", "DPDP Act 2023", "GDPR (Art. 22)", "EU AI Act (Art. 86)"]
axes = ["A1 Speed &\nfinality", "A2 Screening &\ntraceability", "A3 Explanation &\ncontestability", "A4 Data minimisation\n& localisation", "A5 Human\noversight"]
M = np.array([[2, 1, 0, 1, 0],
              [0, 0, 0, 2, 0],
              [2, 2, 0, 0, 0],
              [0, 2, 0, 0, 0],
              [0, 2, 0, 0, 0],
              [0, 1, 1, 2, 0],
              [0, 1, 1, 2, 0],
              [0, 0, 2, 2, 2],
              [0, 0, 2, 0, 1]])
side = ["IN", "IN", "Multi", "Intl", "IN", "IN", "IN", "EU", "EU"]
from matplotlib.colors import ListedColormap
fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=300)
ax.imshow(M, cmap=ListedColormap(["#F4F4F4", "#9FC5B8", NAVY]), vmin=0, vmax=2, aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, {0: "–", 1: "partial", 2: "requires"}[M[i, j]], ha="center", va="center", fontsize=7,
                color="white" if M[i, j] == 2 else "#333")
ax.set_xticks(range(5)); ax.set_xticklabels(axes, fontsize=7.4)
ax.set_yticks(range(len(inst))); ax.set_yticklabels([f"{n}  [{s}]" for n, s in zip(inst, side)], fontsize=7.4)
ax.xaxis.tick_top()
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xticks(np.arange(-.5, 5), minor=True); ax.set_yticks(np.arange(-.5, len(inst)), minor=True)
ax.grid(which="minor", color="white", lw=2); ax.tick_params(which="both", length=0)
ax.add_patch(plt.Rectangle((-0.46, -0.46), 1.92, 4.92, fill=False, ec=RUST, lw=1.8, ls="--", zorder=5, clip_on=False))
ax.add_patch(plt.Rectangle((1.54, 6.54), 2.92, 1.92, fill=False, ec=TEAL, lw=1.8, ls="--", zorder=5, clip_on=False))
ax.text(4.65, 2.2, "Payment & security\ninstruments demand\nspeed + tracing\n(red box)…", fontsize=6.8, color=RUST, va="center")
ax.text(4.65, 7.6, "…only EU instruments\ndemand reasons +\nhuman review\n(green box)", fontsize=6.8, color=TEAL, va="center")
ax.set_xlim(-0.5, 6.3)
fig.savefig(FIG / "Fig04_Friction_Matrix.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---------------------------------------------------------------- Figure 5: three-tier architecture
fig, ax = plt.subplots(figsize=(10, 6.2), dpi=300); ax.set_xlim(0, 10); ax.set_ylim(0, 6.2); ax.axis("off")
tiers = [(4.45, "TIER 1 · DOMESTIC EDGE (bank / token service provider)", LIGHT),
         (2.35, "TIER 2 · CONSTITUTIONAL XAI ENGINE (neuro-symbolic core)", SAND),
         (0.25, "TIER 3 · CROSS-BORDER SETTLEMENT (Nexus gateway / receiving PSP)", LIGHT)]
for y, t, c in tiers:
    ax.add_patch(FancyBboxPatch((0.1, y), 8.0, 1.75, boxstyle="round,pad=0,rounding_size=0.08", fc=c, ec="#8A8A8A", lw=0.9))
    ax.text(0.25, y + 1.55, t, fontsize=8, weight="bold", color=INK)
# tier 1
box(ax, 0.3, 4.6, 1.75, 0.75, "Payer initiates\ne₹ / UPI payment", fc="white", tc=INK, ec=INK)
box(ax, 2.35, 4.6, 1.75, 0.75, "Wallet classifier\nstandard · purpose-bound\n· offline-synced", fs=7)
box(ax, 4.4, 4.6, 1.75, 0.75, "Purpose-bound gate\n(domestic conditions\nstay domestic)", fs=7)
box(ax, 6.45, 4.6, 1.5, 0.75, "FATF R.16\ndata completeness", fs=7)
for a, b in [(2.05, 2.35), (4.1, 4.4), (6.15, 6.45)]:
    arrow(ax, (a, 4.97), (b, 4.97))
# tier 2
box(ax, 0.3, 2.5, 1.5, 0.75, "Learned risk model\n+ sanctions\nname screen", fs=7, fc=TEAL)
box(ax, 2.05, 2.5, 1.5, 0.75, "Exact Shapley\nattribution\n(top reasons)", fs=7, fc=TEAL)
box(ax, 3.8, 2.5, 2.2, 0.75, "Machine-readable constitution\nR1 no hold on name alone\nR2 proportionality · R3 explain\nR4 security override", fs=6.4)
box(ax, 6.25, 2.5, 1.7, 0.75, "Decision + reasons\n+ counterfactual\n→ hash-chained log", fs=7)
for a, b in [(1.8, 2.05), (3.55, 3.8), (6.0, 6.25)]:
    arrow(ax, (a, 2.87), (b, 2.87))
arrow(ax, (7.2, 4.6), (7.2, 3.25))
# tier 3
box(ax, 0.3, 0.4, 2.2, 0.75, "ISO 20022 message +\ncompliance attestation\n(reasons, not raw data)", fs=7)
box(ax, 2.8, 0.4, 2.0, 0.75, "Nexus gateway:\nFX · addressing ·\nsettlement", fs=7)
box(ax, 5.1, 0.4, 2.85, 0.75, "Receiving PSP screens own lists;\nreason codes returned on any stop", fs=7)
arrow(ax, (2.5, 0.77), (2.8, 0.77)); arrow(ax, (4.8, 0.77), (5.1, 0.77))
arrow(ax, (7.1, 2.5), (1.4, 1.15), rad=0.15)
# side channels
box(ax, 8.35, 4.45, 1.55, 1.25, "CONTEST\nHuman review desk /\nombudsman\n(Trust)", fc=TEAL, fs=7, bold=False)
box(ax, 8.35, 2.35, 1.55, 1.25, "SECURITY\nFIU-IND / ED alert\nwith evidence pack\n(R4)", fc=RUST, fs=7)
box(ax, 8.35, 0.25, 1.55, 1.25, "SHARED NETWORK\npseudonymous\ntypology monitoring\n(scenario 5)", fc=NAVY, fs=7)
arrow(ax, (7.95, 2.95), (8.35, 4.9), color=TEAL); arrow(ax, (7.95, 2.8), (8.35, 2.95), color=RUST)
arrow(ax, (7.95, 0.75), (8.35, 0.85), color=NAVY)
fig.savefig(FIG / "Fig05_Three_Tier_Architecture.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---------------------------------------------------------------- Figure 9: adoption pathway + future research
fig, ax = plt.subplots(figsize=(10, 3.9), dpi=300); ax.set_xlim(0, 10); ax.set_ylim(0, 3.9); ax.axis("off")
phases = [("Phase 0 · Today", "Correspondent banking,\nISO 20022, opaque\nscreening scores", GREY),
          ("Phase 1 · Sidecar", "Explanation + audit\nlayer added beside\nexisting screening;\nno rail change", NAVY),
          ("Phase 2 · Sandbox", "RBI regulatory sandbox;\nshared pseudonymous\nmonitoring among banks", NAVY),
          ("Phase 3 · Scheme rule", "Nexus scheme rulebook:\nreason codes required\non every stop", NAVY),
          ("Phase 4 · Recognition", "India–EU mutual\nrecognition; public\ncompliance benchmark", TEAL)]
for i, (t, s, c) in enumerate(phases):
    x = 0.15 + i * 1.98
    box(ax, x, 2.15, 1.7, 1.45, f"{t}\n\n{s}", fc=c, fs=7)
    if i < 4:
        arrow(ax, (x + 1.7, 2.87), (x + 1.98, 2.87))
frq = [(2.13, "FRQ1: latency at peak load\n(RBI sandbox, real volumes)"),
       (4.11, "FRQ2: does a written constitution\nreduce unjustified freezes? (LLM test)"),
       (6.09, "FRQ3: robustness to AI-enabled\nfraud and cyber attack")]
for x, t in frq:
    ax.add_patch(FancyBboxPatch((x, 0.35), 1.7, 1.1, boxstyle="round,pad=0,rounding_size=0.06", fc="white", ec=RUST, lw=1, ls="--"))
    ax.text(x + 0.85, 0.9, t, ha="center", va="center", fontsize=6.5, color=RUST)
    arrow(ax, (x + 0.85, 1.45), (x + 0.85, 2.15), color=RUST, ls=":")
ax.text(0.15, 0.6, "Future research\nquestions (Sec. 5.5)", fontsize=7.4, color=RUST, weight="bold", va="center")
fig.savefig(FIG / "Fig09_Adoption_Pathway.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
print("saved 3,4,5,9")
