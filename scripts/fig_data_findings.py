"""Figures for Section 3.3 (data) and Sections 4.4-4.5 (findings), added in round 8.

Fig04_Data_Sources_Flow.png      data sources -> analysis -> evidence (Figure 4)
Fig05_Synthetic_Data_Profile.png feature distributions by payment type (Figure 5)
Fig08_Decision_Flow.png          where the black box's freezes go under the constitution (Figure 8)
Fig09_Ablation_Robustness.png    ablation path (a) and 20-seed robustness intervals (b) (Figure 9)
Fig12_Scenario_Paths.png         each scenario's path through the rules (a) and its Shapley reasons (b) (Figure 12)
No bar charts: box plots, flows, dot-and-interval and lollipop plots only. All numbers are read from 10_Experiment_Results.
"""
import pathlib
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path

import experiment_4ta as E

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES, FIG = ROOT / "10_Experiment_Results", ROOT / "06_Figures"
NAVY, TEAL, RUST, GREY, INK, SAND, LIGHT = "#1F3A5F", "#2A7F62", "#B5523B", "#9AA5B1", "#222222", "#F3EFE6", "#E6EBF0"
GOLD = "#C08A2E"
plt.rcParams.update({"font.size": 8.8, "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "axes.spines.top": False, "axes.spines.right": False, "mathtext.fontset": "stix"})


def save(fig, name):
    fig.savefig(FIG / name, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def box(ax, x, y, w, h, text, fc, tc="white", fs=7.6, ec=None, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.06", fc=fc, ec=ec or fc, lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, linespacing=1.25,
            weight="bold" if bold else "normal")


def arrow(ax, x0, y0, x1, y1, c="#555555"):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=c, lw=0.9, shrinkA=0, shrinkB=0))


# ---------------------------------------------------------------- Figure 4: data sources and analysis flow
def fig_sources():
    fig = plt.figure(figsize=(7.4, 5.7))
    ax = fig.add_axes([0.005, 0.0, 0.99, 1.0])
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.7); ax.axis("off")
    FSB = 9.5
    for x, t in [(1.5, "Data source"), (4.85, "Analysis (Section 3.5)"), (8.15, "Evidence produced")]:
        ax.text(x, 5.5, t, ha="center", fontsize=9.6, weight="bold", color=INK)
    rows = [
        ("Documentary corpus\n11 instruments: India, EU,\ninternational (Suppl. Table S1)",
         "Step 1: code 5 axes × 4 codes;\nblind second coder,\nCohen's κ",
         "Friction matrix and\nfour themes\n(Sections 4.1–4.2)", "RQ1"),
        ("Synthetic payments\n60,000 payments, 9 features,\nseed 42 (Experiment 1)",
         "Steps 2–3: boosted trees, exact\nShapley values, rules (Eqs. 1–7);\nEq. 8, ablation, 20 seeds",
         "Wrongful freezes, group gap,\nrecourse, latency (Section 4.4)\nScenarios S1–S5 (Section 4.5)", "RQ2"),
        ("OFAC SDN list (real)\n7,509 listed individuals;\n6 × 64 constructed names",
         "Step 4: string similarity\n≥ 0.80 (Ratcliff–Obershelp); Fisher's\nexact test; Wilson intervals",
         "Name-collision burden by\nnaming convention\n(Section 4.6)", "RQ2"),
        ("Fictional name pairs\n180 pairs of 4 kinds",
         "Step 4: local Qwen3-8B, plain\ninstruction vs. written\nconstitution",
         "Constitution pilot with a\nlanguage model\n(Section 4.6)", "RQ2"),
        ("Synthetic welfare\n40,000 beneficiaries,\nregimes A, A2, B, C",
         "Step 5: rules W1–W8;\nhybrid payee rule (Eq. 9);\nmisuse control M (Eq. 11)",
         "Payee choice vs misuse\ncontrol (Section 4.7)", "RQ2"),
    ]
    cols = [NAVY, TEAL, GOLD, RUST, "#5B4B8A"]
    for i, (a, b, c, tag) in enumerate(rows):
        y = 4.45 - i * 1.0
        h = 0.86
        box(ax, 0.05, y, 2.9, h, a, LIGHT, tc=INK, ec=cols[i], fs=FSB)
        box(ax, 3.35, y, 3.0, h, b, cols[i], fs=FSB)
        box(ax, 6.75, y, 2.65, h, c, "white", tc=INK, ec=cols[i], fs=FSB)
        arrow(ax, 2.95, y + h / 2, 3.35, y + h / 2); arrow(ax, 6.35, y + h / 2, 6.75, y + h / 2)
        ax.text(9.7, y + h / 2, tag, ha="center", va="center", fontsize=9.5, weight="bold", color=cols[i])
    ax.text(5.0, 0.14, "RQ3 (adoption) maps the artefact onto ISO 20022 messages and institutional roles (Section 5.3).",
            ha="center", fontsize=9.5, style="italic", color="#444")
    save(fig, "Fig04_Data_Sources_Flow.png")


# ---------------------------------------------------------------- Figure 5: synthetic data profile
GROUPS = [("ordinary", "Legitimate: ordinary"), ("trader", "Legitimate: small trader"),
          ("traveller", "Legitimate: traveller"), ("new_account", "Legitimate: new account"),
          ("sanctioned", "Sanctions-linked"), ("layering", "Shell-company layering"), ("cyber", "Compromised wallet")]


def fig_profile():
    E.rng = np.random.default_rng(E.SEED)           # identical draw to the experiment (seed 42)
    E.DATA_ASSUMPTIONS["bias_scale"] = 0.6
    d = E.generate(E.DATA_ASSUMPTIONS["n_payments"])
    d["grp"] = np.where(d.kind == "legit", d.segment, d.kind)
    d["account_age_days"] = d.account_age_days.clip(lower=1)
    fig, axs = plt.subplots(2, 3, figsize=(7.1, 5.9), sharey=False)
    labels = ["Ordinary", "Small trader", "Traveller", "New account", "Sanctions-linked", "Layering", "Compromised wallet"]
    colours = [GREY, GREY, GREY, GREY, RUST, RUST, RUST]

    def panel(ax, col, title, log=False):
        data = [d.loc[d.grp == g, col].to_numpy() for g, _ in GROUPS]
        bp = ax.boxplot(data, vert=False, widths=0.6, showfliers=False, patch_artist=True,
                        medianprops=dict(color=INK, lw=1.1), whiskerprops=dict(lw=0.8), capprops=dict(lw=0.8))
        for patch, c in zip(bp["boxes"], colours):
            patch.set(facecolor=c, alpha=0.55, edgecolor=c)
        ax.set_yticks(range(1, 8)); ax.set_yticklabels(labels if ax in (axs[0, 1], axs[1, 0]) else [""] * 7, fontsize=8.6)
        ax.tick_params(axis="x", labelsize=8.6)
        ax.invert_yaxis(); ax.set_title(title, fontsize=8.8)
        if log:
            ax.set_xscale("log")

    # (a) name-match score: the stated bias assumption, legitimate payers split by name origin
    ax = axs[0, 0]
    L = d.kind == "legit"
    data = [d.loc[L & (d.translit == 0), "name_match"], d.loc[L & (d.translit == 1), "name_match"],
            d.loc[d.kind == "sanctioned", "name_match"]]
    bp = ax.boxplot(data, vert=False, widths=0.6, showfliers=False, patch_artist=True,
                    medianprops=dict(color=INK, lw=1.1))
    for patch, c in zip(bp["boxes"], [GREY, GOLD, RUST]):
        patch.set(facecolor=c, alpha=0.6, edgecolor=c)
    ax.axvline(E.CONSTITUTION["name_screen"], color=RUST, ls=":", lw=0.9)
    ax.text(E.CONSTITUTION["name_screen"] + 0.02, 3.4, "μ = 0.70", fontsize=8.6, color=RUST)
    ax.set_yticks([1, 2, 3]); ax.set_yticklabels(["Legitimate:\nother names", "Legitimate:\ntransliterated", "Sanctions-\nlinked"], fontsize=8.6)
    ax.tick_params(axis="x", labelsize=8.6)
    ax.invert_yaxis(); ax.set_title("(a) Name-match score  m", fontsize=8.8); ax.set_xlim(0, 1)
    panel(axs[0, 1], "velocity_24h", "(b) Payments in last 24 h")
    panel(axs[0, 2], "fan_out", "(c) New counterparties")
    axs[0, 2].axvline(E.CONSTITUTION["R4_layer_fanout"], color=RUST, ls=":", lw=0.9)
    panel(axs[1, 0], "account_age_days", "(d) Account age (days, log)", log=True)
    panel(axs[1, 1], "device_risk", "(e) Device / session risk")
    panel(axs[1, 2], "r16_complete", "(f) R.16 completeness")
    axs[1, 1].axvline(E.CONSTITUTION["R4_cyber_device"], color=RUST, ls=":", lw=0.9)
    fig.tight_layout(h_pad=1.6, w_pad=0.6)
    save(fig, "Fig05_Synthetic_Data_Profile.png")


# ---------------------------------------------------------------- Figure 8: decision flow (alluvial)
def ribbon(ax, x0, y0a, y0b, x1, y1a, y1b, c, alpha=0.45):
    xm = (x0 + x1) / 2
    verts = [(x0, y0a), (xm, y0a), (xm, y1a), (x1, y1a), (x1, y1b), (xm, y1b), (xm, y0b), (x0, y0b), (x0, y0a)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
             Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), fc=c, ec="none", alpha=alpha))


def fig_flow():
    t = pd.read_csv(RES / "test_decisions.csv", index_col=0)
    t = t[t.bb_decision == "HOLD"].copy()
    # in the audit log every sanctions-linked HOLD is "sanctions match confirmed by second identifier" (no remedy)
    t.loc[(t.kind == "sanctioned") & (t.ca_decision == "HOLD"), "ca_decision"] = "CONFIRMED"
    left = [("legit", "Legitimate", GREY), ("sanctioned", "Sanctions-linked", RUST),
            ("layering", "Shell-company layering", RUST), ("cyber", "Compromised wallet", RUST)]
    right = [("RELEASE+MONITOR", "Released under monitoring (R2)", TEAL), ("VERIFY", "Verify: second identifier (R1)", GOLD),
             ("CONFIRMED", "Hold: sanctions match confirmed (R1)", RUST),
             ("HOLD", "Hold with reasons and remedy (R3)", NAVY), ("HOLD+HUMAN_REVIEW", "Hold, human review (R3)", NAVY),
             ("HOLD+FIU_ALERT", "Hold + FIU-IND/ED alert (R4)", INK)]
    N, gap = len(t), 12
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    ax.set_xlim(-0.05, 1.05); ax.axis("off")
    H = N + gap * (len(right) - 1)
    ax.set_ylim(-14, H + 18)

    def stack(items, col):
        pos, y = {}, H
        sizes = {k: (t[col] == k).sum() for k, _, _ in items}
        g = (H - N) / (len(items) - 1)
        for k, _, _ in items:
            pos[k] = [y, y - sizes[k]]; y -= sizes[k] + g
        return pos, sizes

    lp, ls_ = stack(left, "kind"); rp, rs = stack(right, "ca_decision")
    lcur = {k: v[0] for k, v in lp.items()}; rcur = {k: v[0] for k, v in rp.items()}
    x0, x1, w = 0.30, 0.70, 0.025
    for kl, _, cl in left:
        for kr, _, cr in right:
            n = ((t.kind == kl) & (t.ca_decision == kr)).sum()
            if n == 0:
                continue
            ribbon(ax, x0 + w, lcur[kl], lcur[kl] - n, x1, rcur[kr], rcur[kr] - n, cl if kl == "legit" else RUST,
                   alpha=0.35 if kl == "legit" else 0.30)
            lcur[kl] -= n; rcur[kr] -= n
    for k, lab, c in left:
        a, b = lp[k]; ax.add_patch(plt.Rectangle((x0, b), w, a - b, fc=c, ec="none"))
        ax.text(x0 - 0.012, (a + b) / 2, f"{lab}\nn = {ls_[k]}", ha="right", va="center", fontsize=7.4)
    for k, lab, c in right:
        a, b = rp[k]; ax.add_patch(plt.Rectangle((x1, b), w, a - b, fc=c, ec="none"))
        nl = ((t.kind == "legit") & (t.ca_decision == k)).sum()
        ax.text(x1 + w + 0.012, (a + b) / 2, f"{lab}\nn = {rs[k]}  (legitimate {nl})", ha="left", va="center", fontsize=7.4)
    ax.text(x0 + w / 2, H + 10, "Black box: all frozen,\nno reasons (n = %d)" % N, ha="center", fontsize=7.8, weight="bold")
    ax.text(x1 + w / 2, H + 10, "Constitutional layer:\nreasons recorded for all", ha="center", fontsize=7.8, weight="bold")
    save(fig, "Fig08_Decision_Flow.png")


# ---------------------------------------------------------------- Figure 9: ablation path and robustness
def fig_ablation():
    ab = pd.read_csv(RES / "ablation.csv")
    rob = RES / "robustness_summary.csv"
    have_rob = rob.exists()
    fig, axs = plt.subplots(2 if have_rob else 1, 1, figsize=(6.9, 6.6 if have_rob else 3.4), gridspec_kw={"height_ratios": [1.1, 1]} if have_rob else None)
    a = axs[0] if have_rob else axs
    steps = ["Black box", "+ R4", "+ R1", "+ R2\n(full)"]
    for col, lab, c, m in [("wrongful_freezes_translit_per_10k", "Transliterated names", GOLD, "o"),
                           ("wrongful_freezes_per_10k", "All legitimate", NAVY, "s"),
                           ("wrongful_freezes_other_per_10k", "Other names", GREY, "^")]:
        a.plot(range(4), ab[col], color=c, marker=m, ms=4.5, lw=1.3, label=lab)
        for i, v in enumerate(ab[col]):
            if i in (0, 3):
                dy = {GOLD: 9, NAVY: 0, GREY: -9}[c] if i == 3 else 0
                a.text(i + (0.12 if i == 3 else -0.12), v + dy, f"{v:.1f}", fontsize=8.8, color=c, va="center",
                       ha="left" if i == 3 else "right")
    a.set_xticks(range(4)); a.set_xticklabels(steps, fontsize=8.8); a.set_xlim(-0.6, 3.6)
    a.set_ylabel("Wrongful freezes per 10,000 legitimate"); a.set_ylim(0, 165)
    a.legend(frameon=False, fontsize=8.8, loc="lower left"); a.set_title("(a) Adding the rules one at a time (seed 42)", fontsize=9.6, loc="left")
    if have_rob:
        s = pd.read_csv(rob)
        b = axs[1]
        pols = [("BB", "Black box"), ("BB-match", "Black box, threshold\nmatched to constitution"),
                ("BB+ID", "Black box + second-\nidentifier check (R1)"), ("CONST", "Full constitution")]
        for j, (bias, mk, off) in enumerate([(0.6, "o", -0.12), (0.0, "D", 0.12)]):
            for i, (p, _) in enumerate(pols):
                r = s[(s.bias == bias) & (s.policy == p)].iloc[0]
                c = TEAL if p == "CONST" else (GOLD if p == "BB+ID" else RUST)
                b.plot([r.wf_all_lo, r.wf_all_hi], [i + off] * 2, color=c, lw=1.4)
                b.scatter(r.wf_all_mean, i + off, color=c if bias == 0.6 else "white", edgecolor=c, marker=mk, s=34, zorder=3)
        b.set_yticks(range(4)); b.set_yticklabels([p[1] for p in pols], fontsize=8.8); b.invert_yaxis()
        b.set_xlabel("Wrongful freezes per 10,000 legitimate\n(mean, 2.5th–97.5th percentile across 20 seeds)")
        b.scatter([], [], color=GREY, marker="o", s=20, label="name bias assumed")
        b.scatter([], [], color="white", edgecolor=GREY, marker="D", s=20, label="no name bias")
        b.legend(frameon=False, fontsize=8.8, loc="lower right"); b.set_xlim(left=0)
        b.set_title("(b) Robustness across random seeds", fontsize=9.6, loc="left")
    fig.tight_layout(h_pad=1.8)
    save(fig, "Fig09_Ablation_Robustness.png")


# ---------------------------------------------------------------- Figure 12: scenario paths and reasons
def fig_scenarios():
    sc = pd.read_csv(RES / "scenarios_1_4.csv")
    fig = plt.figure(figsize=(7.2, 5.6))
    ax = fig.add_axes([0.0, 0.0, 0.52, 1.0]); ax.set_xlim(0, 6); ax.set_ylim(0, 7.4); ax.axis("off")
    box(ax, 0.2, 6.55, 3.1, 0.6, "Examined payment: score s(x),\nname screen m(x)", LIGHT, tc=INK, ec=NAVY, fs=9.2)
    q = [(5.35, "R4  Security typology?\n(cyber burst or layering)"), (3.95, "R1  Name-driven alert and\nno second identifier?"),
         (2.55, "R2  Amount < ₹50,000 and\nscore < 0.80?")]
    outs = [("HOLD + FIU alert\nevidence pack", INK, "S3, S4"), ("VERIFY\nask for identifier", GOLD, "S2"),
            ("RELEASE +\nMONITOR", TEAL, "S1")]
    arrow(ax, 1.75, 6.55, 1.75, 6.05)
    for (y, txt), (o, c, tag) in zip(q, outs):
        box(ax, 0.2, y, 3.1, 0.7, txt, NAVY, fs=9.0)
        box(ax, 4.0, y + 0.02, 1.75, 0.66, o, c, fs=9.0)
        arrow(ax, 3.3, y + 0.35, 4.0, y + 0.35); ax.text(3.65, y + 0.42, "yes", fontsize=9.2, ha="center", color="#444")
        ax.text(4.875, y - 0.16, tag, ha="center", fontsize=9.2, weight="bold", color=RUST)
        arrow(ax, 1.75, y, 1.75, y - 0.7); ax.text(1.85, y - 0.4, "no", fontsize=9.2, color="#444")
    box(ax, 0.2, 1.15, 3.1, 0.7, "R3  HOLD with top-3 reasons\nand minimal remedy c*", NAVY, fs=9.0)
    box(ax, 4.0, 1.17, 1.75, 0.66, "Human review\nif no remedy", GREY, fs=9.0)
    arrow(ax, 3.3, 1.5, 4.0, 1.5)
    ax.text(1.75, 0.55, "Every non-release decision is written to the\nhash-chained audit log (Eq. 7)",
            ha="center", fontsize=9.2, style="italic", color="#444")
    ax.text(0.2, 7.3, "(a) Path of each scenario through the constitution", fontsize=9.4, weight="bold")

    b = fig.add_axes([0.73, 0.1, 0.26, 0.8])
    y, ticks, labs = 0, [], []
    for _, r in sc.iterrows():
        sid = r["Scenario"].split()[0]
        reasons = re.findall(r"([^;]+?) \(([+-]\d+\.\d+)\)", r["Top reasons (Shapley)"])
        b.text(0.06, y - 0.1, f"{sid}  (score {r['Model score']:.2f})", fontsize=9.2, weight="bold", ha="left",
               transform=b.get_yaxis_transform())
        y += 0.75
        for name, v in reasons:
            v = float(v)
            b.plot([0, v], [y, y], color=NAVY, lw=1.2); b.scatter(v, y, color=NAVY, s=18, zorder=3)
            ticks.append(y); labs.append(name.strip().replace("Sanctions name-match score", "Name-match score").replace("FATF R.16", "R.16"))
            y += 0.7
        y += 0.55
    b.set_yticks(ticks); b.set_yticklabels(labs, fontsize=9.2); b.set_ylim(y - 0.4, -0.7); b.tick_params(labelsize=9.2)
    b.axvline(0, color=GREY, lw=0.7); b.set_xlabel("Shapley contribution\nto risk score")
    b.set_title("(b) Top reasons recorded", fontsize=9.4, weight="bold", loc="left")
    b.yaxis.tick_left()
    save(fig, "Fig12_Scenario_Paths.png")


if __name__ == "__main__":
    fig_sources(); fig_profile(); fig_flow(); fig_ablation(); fig_scenarios()
