"""Figure 1: Evolution from correspondent banking to programmable CBDC corridors (timeline, no bars)."""
import pathlib
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).resolve().parent.parent / "06_Figures"
INDIA, INTL, INK, MUTED = "#1F3A5F", "#2A7F62", "#222222", "#8A8A8A"

# (decimal year, label, lane, height, alignment); lane +1 = international (above), -1 = India (below)
EVENTS = [
    (2016.6, "UPI launched", -1, -0.55, "center"),
    (2017.65, "Puttaswamy: privacy\na fundamental right", -1, -1.05, "center"),
    (2018.4, "GDPR applies\n(Art. 22 automated\ndecisions)", 1, 0.55, "center"),
    (2020.8, "G20 roadmap for\ncross-border payments", 1, 0.95, "center"),
    (2021.6, "BIS Project Nexus\nblueprint", 1, 1.45, "center"),
    (2022.2, "Finance Act 2022:\ndigital rupee enabled", -1, -0.55, "right"),
    (2022.85, "Oct-Dec 2022: RBI CBDC Concept Note;\ne₹-W (Nov) and e₹-R (Dec) pilots", -1, -1.45, "center"),
    (2023.6, "DPDP Act 2023", -1, -0.55, "left"),
    (2024.5, "Jun 2024: Nexus agreement,\nIndia + 4 ASEAN central banks", 1, 1.45, "right"),
    (2024.58, "Aug 2024: EU AI Act\nin force (Art. 86)", 1, 0.6, "left"),
]

fig, ax = plt.subplots(figsize=(11, 4.6), dpi=300)
ax.axhline(0, color=INK, lw=1.2, zorder=1)
for yr in range(2016, 2026):
    ax.plot([yr, yr], [-0.06, 0.06], color=INK, lw=0.8)
    ax.text(yr, -0.16, str(yr), ha="center", va="top", fontsize=8, color=MUTED)

for x, label, lane, h, ha in EVENTS:
    col = INTL if lane == 1 else INDIA
    ax.plot([x, x], [0, h], color=col, lw=0.8, zorder=1)
    ax.scatter([x], [0], s=28, color=col, zorder=3, edgecolor="white", linewidth=0.6)
    ax.text(x, h + (0.04 if lane == 1 else -0.04), label, ha=ha,
            va="bottom" if lane == 1 else "top", fontsize=7.2, color=col, linespacing=1.15)

ax.text(2015.45, 0.32, "Legacy baseline:\ncorrespondent banking\nover SWIFT (since 1973)",
        fontsize=7.2, color=MUTED, ha="left", va="bottom", style="italic")
ax.text(2025.35, 1.9, "International / EU", color=INTL, fontsize=8.5, ha="right", weight="bold")
ax.text(2025.35, -2.15, "India", color=INDIA, fontsize=8.5, ha="right", weight="bold")
ax.set_xlim(2015.4, 2025.4)
ax.set_ylim(-2.3, 2.05)
ax.axis("off")
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"Fig01_Payments_Evolution_Timeline.{ext}", bbox_inches="tight", facecolor="white")
print("saved")
