"""Five scenario walkthroughs + result figures (no bar charts) for Chapter 4."""
import hashlib
import json

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

import experiment_4ta as E

FIG = E.ROOT / "06_Figures"
NAVY, TEAL, RUST, GREY, INK = "#1F3A5F", "#2A7F62", "#B5523B", "#9AA5B1", "#222222"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "font.family": "serif",
                     "font.serif": ["Times New Roman", "DejaVu Serif"], "mathtext.fontset": "stix"})
# figures are drawn about 7 in wide so that, at the 6.5 in text width, the smallest label prints at 7.5 pt or more

# rebuild the identical model (same seed, same split)
C = E.CONSTITUTION
d = E.generate(E.DATA_ASSUMPTIONS["n_payments"])
tr, te = train_test_split(d, test_size=0.25, random_state=E.SEED, stratify=d["illicit"])
tr, va = train_test_split(tr, test_size=0.2, random_state=E.SEED, stratify=tr["illicit"])
model = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08, random_state=E.SEED)
model.fit(tr[E.FEATS].to_numpy(float), tr["illicit"].to_numpy())
C["tau_alert"] = float(np.quantile(model.predict_proba(va[E.FEATS].to_numpy(float))[:, 1], 1 - C["alert_rate"]))
shap = E.ExactShap(model, tr[E.FEATS].sample(40, random_state=E.SEED).to_numpy(float))

# ------------------------------------------------------------------ scenarios 1-4 (single payments)
SCEN = {
    "S1 Farmer co-operative pays EU seed supplier (purpose-bound e₹)":
        dict(log_amount=np.log(40_000), name_match=0.35, second_id_match=0, velocity_24h=6, fan_out=4,
             account_age_days=30, device_risk=0.20, r16_complete=0.60, corridor_us=0, kind="legit"),
    "S2 Remittance to EU recipient with a common Indian name":
        dict(log_amount=np.log(150_000), name_match=0.78, second_id_match=0, velocity_24h=1, fan_out=1,
             account_age_days=1500, device_risk=0.10, r16_complete=0.85, corridor_us=0, kind="legit"),
    "S3 Shell-company layering through new accounts":
        dict(log_amount=np.log(400_000), name_match=0.05, second_id_match=0, velocity_24h=7, fan_out=9,
             account_age_days=12, device_risk=0.25, r16_complete=0.40, corridor_us=0, kind="layering"),
    "S4 Burst from compromised wallets during a cyber attack (India–US)":
        dict(log_amount=np.log(60_000), name_match=0.08, second_id_match=0, velocity_24h=16, fan_out=2,
             account_age_days=700, device_risk=0.85, r16_complete=0.55, corridor_us=1, kind="cyber"),
}
srows = []
for name, f in SCEN.items():
    row = pd.Series(f)
    rec = E.constitutional_decision(row, model, shap)
    bb = "FREEZE (no reason given)" if (rec["score"] >= C["tau_alert"] or row["name_match"] >= C["name_screen"]) else "RELEASE"
    srows.append({"Scenario": name, "Model score": rec["score"], "Black box": bb, "Constitutional decision": rec["decision"],
                  "Rule applied": rec["rule"],
                  "Top reasons (Shapley)": "; ".join(f"{E.LABELS[k]} (+{v:.2f})" if v >= 0 else f"{E.LABELS[k]} ({v:.2f})" for k, v in rec.get("top3", [])),
                  "Counterfactual / remedy": ", ".join(rec.get("counterfactual") or []) or ("FIU-IND/ED alert with evidence pack" if "FIU" in rec["decision"] else "-")})
scen = pd.DataFrame(srows)
scen.to_csv(E.RES / "scenarios_1_4.csv", index=False)
print(scen.to_string(index=False))

# ------------------------------------------------------------------ scenario 5: shared monitoring network
rng = np.random.default_rng(7)
psps = ["Bank A (India)", "Bank B (India)", "PSP C (EU)"]
ring = {"source": "S", "mules": [f"M{i}" for i in range(1, 13)], "sink": "X"}
edges = []
for i, m in enumerate(ring["mules"]):
    edges.append(("S", m, psps[i % 3]))       # 4 mules per institution
    edges.append((m, "X", psps[i % 3]))
salt = "shared-network-salt"                  # pseudonymous IDs: institutions share hashes, not identities
pseud = {n: hashlib.sha256((salt + n).encode()).hexdigest()[:8] for n in ["S", "X"] + ring["mules"]}
local_fanout = {p: sum(1 for a, b, q in edges if a == "S" and q == p) for p in psps}
pooled_fanout = sum(1 for a, b, q in edges if a == "S")
s5 = {"local_fan_out_seen_by_each_institution": local_fanout, "pooled_fan_out_on_shared_network": pooled_fanout,
      "R4_layer_fanout_threshold": C["R4_layer_fanout"],
      "detected_locally": any(v >= C["R4_layer_fanout"] for v in local_fanout.values()),
      "detected_on_shared_network": pooled_fanout >= C["R4_layer_fanout"],
      "shared_fields": "salted SHA-256 pseudonym of counterparty, timestamp bucket, amount band; no names or account numbers",
      "source_pseudonym": pseud["S"]}
(E.RES / "scenario5_network.json").write_text(json.dumps(s5, indent=1), encoding="utf-8")
print(json.dumps(s5, indent=1))

fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.9), dpi=300)
colors = {psps[0]: NAVY, psps[1]: TEAL, psps[2]: RUST}
for ax, pooled in zip(axs, [False, True]):
    G = nx.DiGraph()
    shown = edges if pooled else [e for e in edges if e[2] == psps[0]]
    for a, b, q in shown:
        G.add_edge(a, b, psp=q)
    pos = {"S": (0, 0), "X": (2, 0)}
    ms = [m for m in ring["mules"] if m in G]
    for k, m in enumerate(ms):
        pos[m] = (1, (k - (len(ms) - 1) / 2) * 0.32)
    ec = [colors[G[a][b]["psp"]] for a, b in G.edges]
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=ec, arrows=True, arrowsize=7, width=1.0, node_size=160)
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=ms, node_color="white", edgecolors=INK, node_size=110, linewidths=0.8)
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=["S", "X"], node_color=[RUST, INK], node_size=330)
    nx.draw_networkx_labels(G, pos, ax=ax, labels={"S": "S", "X": "X"}, font_color="white", font_size=9, font_weight="bold")
    fo = pooled_fanout if pooled else local_fanout[psps[0]]
    ttl = ("(b) Shared network view (pseudonymous)" if pooled else "(a) What one institution sees") + f"\nfan-out = {fo}  (rule threshold = {C['R4_layer_fanout']})"
    ax.set_title(ttl, fontsize=9.5, color=RUST if pooled else INK)
    ax.axis("off")
handles = [plt.Line2D([0], [0], color=c, lw=2, label=p) for p, c in colors.items()]
fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=9.5)
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(FIG / "Fig08_Shared_Monitoring_Network.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------------ Figure 6: policy frontier + group gap (no bars)
sweep = pd.read_csv(E.RES / "proportionality_sweep.csv")
abl = pd.read_csv(E.RES / "ablation.csv")
fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.9, 6.6), dpi=300, gridspec_kw={"height_ratios": [1.45, 1]})
a1.plot(sweep.r2_threshold_inr / 1000, sweep.wrongful_freezes_per_10k, "-o", color=RUST, ms=4, label="Wrongful freezes of legitimate payments (per 10,000)")
a1b = a1.twinx()
a1b.plot(sweep.r2_threshold_inr / 1000, sweep.illicit_stopped_pct, "-s", color=NAVY, ms=4, label="Illicit payments frozen (%)")
a1b.plot(sweep.r2_threshold_inr / 1000, sweep.illicit_stopped_or_monitored_pct, "--", color=TEAL, lw=1.6, label="Illicit payments frozen or monitored (%)")
a1.set_xscale("symlog", linthresh=5); a1.set_xticks([0, 5, 10, 25, 50, 100, 250]); a1.set_xticklabels(["0", "5", "10", "25", "50", "100", "250"])
a1.set_xlabel("Proportionality threshold R2 (₹ thousand)"); a1.set_ylabel("Wrongful freezes per 10,000", color=RUST)
a1b.set_ylabel("Illicit payments (%)", color=NAVY); a1b.set_ylim(40, 90); a1b.spines["right"].set_visible(True)
a1.axvline(50, color=GREY, lw=0.8, ls=":"); a1.text(54, 62, "design value\n(₹50,000)", fontsize=9, color="#444")
h1, l1 = a1.get_legend_handles_labels(); h2, l2 = a1b.get_legend_handles_labels()
a1.legend(h1 + h2, l1 + l2, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1, frameon=False)
a1.set_title("(a) The proportionality frontier", fontsize=10, loc="left")
grp = [("All legitimate", "wrongful_freezes_per_10k"), ("Transliterated names", "wrongful_freezes_translit_per_10k"), ("Other names", "wrongful_freezes_other_per_10k")]
bb, full = abl.iloc[0], abl.iloc[-1]
for y, (lab, col) in enumerate(grp):
    a2.plot([full[col], bb[col]], [y, y], color=GREY, lw=2, zorder=1)
    a2.scatter(bb[col], y, color=RUST, s=40, zorder=2, label="Black box" if y == 0 else None)
    a2.scatter(full[col], y, color=TEAL, s=40, zorder=2, label="Constitutional" if y == 0 else None)
    a2.text(bb[col] + 3, y, f"{bb[col]:.0f}", fontsize=9, color=RUST, va="center"); a2.text(full[col] - 3, y, f"{full[col]:.0f}", fontsize=9, color=TEAL, ha="right", va="center")
a2.set_yticks(range(3)); a2.set_yticklabels([g[0] for g in grp]); a2.set_xlabel("Wrongful freezes per 10,000 legitimate payments")
a2.set_xlim(0, 160); a2.set_ylim(-0.6, 2.9); a2.invert_yaxis(); a2.legend(fontsize=9, frameon=False, loc="lower right", ncol=2); a2.set_title("(b) Who bears wrongful freezes", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig(FIG / "Fig06_Policy_Frontier_and_Bias.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# ------------------------------------------------------------------ Figure 7: Shapley beeswarm + latency ECDF
sr = pd.read_csv(E.RES / "shap_examined.csv")
lat = pd.read_csv(E.RES / "latency_ms.csv").iloc[:, 0].to_numpy()
fig, (b1, b2) = plt.subplots(2, 1, figsize=(6.9, 7.0), dpi=300, gridspec_kw={"height_ratios": [1.7, 1]})
order = sr[["phi_" + f for f in E.FEATS]].abs().mean().sort_values().index
for y, col in enumerate(order):
    f = col[4:]
    v = sr[f].to_numpy(float); c = (v - v.min()) / (np.ptp(v) + 1e-9)
    jitter = np.random.default_rng(y).uniform(-0.28, 0.28, len(sr))
    b1.scatter(sr[col], y + jitter, c=c, cmap="coolwarm", s=5, alpha=0.75, linewidths=0)
b1.axvline(0, color=GREY, lw=0.8)
b1.set_yticks(range(len(order))); b1.set_yticklabels([E.LABELS[c[4:]] for c in order], fontsize=9)
b1.set_xlabel("Shapley contribution to risk score"); b1.set_title("(a) What drives each examined decision", fontsize=10, loc="left")
b1.text(1.0, 1.02, "dot colour: blue = low, red = high feature value", transform=b1.transAxes, ha="right", fontsize=9, color="#444")
xs = np.sort(lat); b2.plot(xs, np.arange(1, len(xs) + 1) / len(xs), color=NAVY, lw=1.6)
for q, ls in [(50, "--"), (95, ":")]:
    v = np.percentile(lat, q); b2.axvline(v, color=RUST, ls=ls, lw=1); b2.text(v + 1, 0.05 + (q == 95) * 0.1, f"p{q} = {v:.0f} ms", fontsize=9, color=RUST)
b2.set_xlabel("Decision time per examined payment (ms)\nmodel + exact Shapley + rules + counterfactual"); b2.set_ylabel("Share of payments")
b2.set_title("(b) Decision latency (laptop CPU)", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig(FIG / "Fig07_Shapley_and_Latency.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
print("figures saved")
