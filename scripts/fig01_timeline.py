"""Figure 1: Evolution from correspondent banking to programmable CBDC corridors (timeline, no bars).
Drawn at 7.4 in wide so that, printed at the 6.5 in text width, the smallest text is about 7.6 pt."""
import pathlib
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).resolve().parent.parent / "06_Figures"
INDIA, INTL, INK, MUTED = "#1F3A5F", "#2A7F62", "#222222", "#6F6F6F"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"]})

# (decimal year, label, lane, height, alignment); lane +1 = international (above), -1 = India (below)
EVENTS = [
    (2016.6, "UPI launched", -1, -0.45, "center"),
    (2017.65, "Puttaswamy:\nprivacy a\nfundamental right", -1, -1.05, "center"),
    (2018.4, "GDPR applies\n(Art. 22\nautomated\ndecisions)", 1, 0.45, "center"),
    (2020.3, "G20 roadmap\nfor cross-border\npayments", 1, 0.45, "center"),
    (2021.6, "BIS Project\nNexus blueprint", 1, 1.5, "center"),
    (2022.3, "Finance Act 2022:\ndigital rupee\nenabled", -1, -0.45, "right"),
    (2022.62, "Oct–Dec 2022: RBI CBDC\nConcept Note; e₹-W (Nov)\nand e₹-R (Dec) pilots", -1, -1.45, "center"),
    (2023.6, "DPDP Act\n2023", -1, -0.45, "left"),
    (2024.45, "Jun 2024: Nexus agreement,\nIndia + 4 ASEAN\ncentral banks", 1, 1.5, "right"),
    (2024.6, "Aug 2024:\nEU AI Act\nin force\n(Art. 86)", 1, 0.45, "left"),
]

fig, ax = plt.subplots(figsize=(7.4, 4.5), dpi=300)
ax.axhline(0, color=INK, lw=1.2, zorder=1)
for yr in range(2016, 2026):
    ax.plot([yr, yr], [-0.06, 0.06], color=INK, lw=0.8)
    ax.text(yr, -0.12, str(yr), ha="center", va="top", fontsize=9.4, color=MUTED)

for x, label, lane, h, ha in EVENTS:
    col = INTL if lane == 1 else INDIA
    ax.plot([x, x], [0, h], color=col, lw=0.8, zorder=1)
    ax.scatter([x], [0], s=28, color=col, zorder=3, edgecolor="white", linewidth=0.6)
    ax.text(x, h + (0.04 if lane == 1 else -0.04), label, ha=ha,
            va="bottom" if lane == 1 else "top", fontsize=9.4, color=col, linespacing=1.12)

ax.text(2015.45, 1.0, "Legacy baseline:\ncorrespondent\nbanking over SWIFT\n(since 1973)",
        fontsize=9.4, color=MUTED, ha="left", va="bottom", style="italic")
ax.text(2025.4, 2.3, "International / EU", color=INTL, fontsize=9.6, ha="right", weight="bold")
ax.text(2025.4, -2.45, "India", color=INDIA, fontsize=9.6, ha="right", weight="bold")
ax.set_xlim(2015.4, 2025.45)
ax.set_ylim(-2.55, 2.4)
ax.axis("off")
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"Fig01_Payments_Evolution_Timeline.{ext}", bbox_inches="tight", facecolor="white")
print("saved")
