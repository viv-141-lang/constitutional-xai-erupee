"""Figure 16: choice-misuse frontier of Experiment 3 (welfare_frontier.csv, seed 42). No bars."""
import pathlib

import matplotlib.pyplot as plt
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
F = pd.read_csv(ROOT / "10_Experiment_Results" / "welfare_frontier.csv")
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "font.size": 9.5,
                     "mathtext.fontset": "stix"})
OFF = {0.5: (6, 6), 1.0: (-4, -15)}
RUST, GREEN, GREY = "#b5532d", "#2e7d5b", "#6b6b6b"

fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.5))
for ax, col, title in zip(axes, ["choice_tuition", "choice_relief"],
                          ["(a) Student tuition grant", "(b) Farmer debt relief"]):
    a2 = F[F.regime == "A2"].sort_values("empanel_share")
    ax.plot(a2[col], a2.M_pct, "-o", color=RUST, ms=5, label="A2 approved list")
    for _, r in a2.iterrows():
        ax.annotate(f"{r.empanel_share:.0%}", (r[col], r.M_pct), textcoords="offset points",
                    xytext=OFF.get(r.empanel_share, (4, -14)), ha=("right" if r.empanel_share == 1 else "left"), fontsize=9.5, color=RUST)
    for reg, c, mk, lab in [("B", GREY, "s", "B silent hybrid"), ("C", GREEN, "D", "C this design")]:
        r = F[F.regime == reg].iloc[0]
        ax.plot(r[col], r.M_pct, mk, color=c, ms=7, label=lab)
    ax.set_title(title, fontsize=9.5)
    ax.set_xlabel("Payee choice (median admissible payees)")
    ax.set_ylim(40, 100)
    ax.margins(x=0.12)
    ax.grid(alpha=0.3)
axes[0].set_ylabel("Misuse control M (%)")
axes[0].legend(loc="lower left", fontsize=9.5, frameon=False)
fig.tight_layout()
fig.savefig(ROOT / "06_Figures" / "Fig16_Welfare_Choice_Misuse.png", dpi=300)
