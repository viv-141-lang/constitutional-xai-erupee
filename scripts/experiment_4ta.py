"""4T-A proof-of-concept: black-box AML screening vs a constitutional, explainable decision layer.

Pipeline (Chapter 3/4):  synthetic cross-border e-rupee payments -> risk model (neural/learned layer)
-> exact Shapley attributions -> machine-readable constitution (symbolic layer) -> decision + counterfactual
-> hash-chained audit record.  All data are SYNTHETIC; the generator's assumptions are stated in DATA_ASSUMPTIONS.
"""
import hashlib
import itertools
import json
import pathlib
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "10_Experiment_Results"
RES.mkdir(exist_ok=True)
SEED = 42
rng = np.random.default_rng(SEED)

FEATS = ["log_amount", "name_match", "second_id_match", "velocity_24h", "fan_out",
         "account_age_days", "device_risk", "r16_complete", "corridor_us"]
LABELS = {"log_amount": "Amount (log ₹)", "name_match": "Sanctions name-match score",
          "second_id_match": "Second identifier matches list", "velocity_24h": "Payments in last 24 h",
          "fan_out": "New counterparties (fan-out)", "account_age_days": "Account age (days)",
          "device_risk": "Device / session risk", "r16_complete": "FATF R.16 data completeness",
          "corridor_us": "India–US corridor"}

# ---- The machine-readable constitution (Vivek's four rules). Thresholds are design parameters. ----
CONSTITUTION = {
    "alert_rate": 0.025,            # share of payments examined (banks calibrate thresholds to alert volume)
    "tau_alert": None,              # set from the validation split to match alert_rate
    "name_screen": 0.70,            # sanctions name-screen threshold (string-similarity screen, as in Nexus)
    "R1_name_share": 0.50,          # R1: if name-match carries >= this share of positive attribution ...
    "R2_small_value_inr": 50_000,   # R2: proportionality tier: below this amount ...
    "R2_max_score": 0.80,           # ... and below this score -> release with monitoring, not freeze
    "R4_cyber_device": 0.70, "R4_cyber_velocity": 10,          # R4 security override: compromised-device burst
    "R4_layer_fanout": 6, "R4_layer_age": 60, "R4_layer_score": 0.90,  # R4: shell-company layering typology
}
DATA_ASSUMPTIONS = {
    "n_payments": 60_000, "share_transliterated_names": 0.60,
    "prevalence": {"sanctioned": 0.004, "layering": 0.008, "cyber_compromise": 0.005},
    "segments": "legit = ordinary 82%, small traders 8%, travellers on new devices 5%, new accounts 5%",
    "bias_assumption": "Transliterated Indian names receive a higher spurious sanctions name-match score "
                       "(Beta(2,6)*0.6 added), reflecting name-similarity screening (NGP, n.d.).",
}


# ------------------------------------------------------------------ data
def generate(n: int) -> pd.DataFrame:
    """Overlapping populations: some legitimate users look partly suspicious, as in real screening."""
    kinds = rng.choice(["legit", "sanctioned", "layering", "cyber"], size=n, p=[1 - 0.017, 0.004, 0.008, 0.005])
    d = pd.DataFrame({"kind": kinds})
    L = kinds == "legit"
    # legitimate look-alike segments (shares within legit): small traders, travellers on new devices, new accounts
    seg = np.where(L, rng.choice(["ordinary", "trader", "traveller", "new_account"], size=n, p=[0.82, 0.08, 0.05, 0.05]), "illicit")
    d["segment"] = seg
    translit = rng.random(n) < DATA_ASSUMPTIONS["share_transliterated_names"]
    d["translit"] = translit.astype(int)
    is_ = {k: (kinds == k) for k in ["sanctioned", "layering", "cyber"]}
    sg = {k: (seg == k) for k in ["trader", "traveller", "new_account"]}
    d["log_amount"] = rng.normal(10.3, 1.1, n)
    d.loc[is_["layering"], "log_amount"] = rng.normal(11.0, 1.0, is_["layering"].sum())
    nm = rng.beta(1.3, 10, n) + translit * rng.beta(2, 6, n) * DATA_ASSUMPTIONS.get("bias_scale", 0.6)  # bias assumption
    nm[is_["sanctioned"]] = rng.beta(5, 3, is_["sanctioned"].sum())
    d["name_match"] = np.clip(nm, 0, 1)
    d["second_id_match"] = 0
    d.loc[is_["sanctioned"], "second_id_match"] = (rng.random(is_["sanctioned"].sum()) < 0.6).astype(int)
    d["velocity_24h"] = rng.poisson(1.5, n)
    d.loc[sg["trader"], "velocity_24h"] = rng.poisson(5, sg["trader"].sum())
    d.loc[is_["layering"], "velocity_24h"] = rng.poisson(5, is_["layering"].sum())
    d.loc[is_["cyber"], "velocity_24h"] = rng.poisson(9, is_["cyber"].sum())
    d["fan_out"] = rng.poisson(1.2, n)
    d.loc[sg["trader"], "fan_out"] = rng.poisson(4, sg["trader"].sum())
    d.loc[is_["layering"], "fan_out"] = rng.poisson(5, is_["layering"].sum())
    d["account_age_days"] = rng.exponential(900, n)
    d.loc[sg["new_account"], "account_age_days"] = rng.exponential(40, sg["new_account"].sum())
    d.loc[is_["layering"], "account_age_days"] = rng.exponential(60, is_["layering"].sum())
    d["device_risk"] = rng.beta(1.5, 8, n)
    d.loc[sg["traveller"], "device_risk"] = rng.beta(4, 4, sg["traveller"].sum())
    d.loc[is_["cyber"], "device_risk"] = rng.beta(4, 3, is_["cyber"].sum())
    d["r16_complete"] = rng.beta(6, 2, n)
    d.loc[~L, "r16_complete"] = rng.beta(4, 3, (~L).sum())
    d["corridor_us"] = (rng.random(n) < 0.30).astype(int)
    d["illicit"] = (~L).astype(int)
    return d


# ------------------------------------------------------------------ exact Shapley (interventional)
class ExactShap:
    def __init__(self, model, background: np.ndarray):
        self.m, self.bg, self.k = model, background, background.shape[1]
        self.masks = np.array(list(itertools.product([0, 1], repeat=self.k)), dtype=bool)  # 2^k coalitions
        from math import factorial
        self.w = {s: factorial(s) * factorial(self.k - s - 1) / factorial(self.k) for s in range(self.k)}
        self.idx = {tuple(m): i for i, m in enumerate(self.masks)}

    def explain(self, x: np.ndarray) -> np.ndarray:
        B = len(self.bg)
        X = np.repeat(self.bg[None, :, :], len(self.masks), axis=0)          # coalitions x B x k
        X[self.masks[:, None, :].repeat(B, 1)] = np.broadcast_to(x, X.shape)[self.masks[:, None, :].repeat(B, 1)]
        v = self.m.predict_proba(X.reshape(-1, self.k))[:, 1].reshape(len(self.masks), B).mean(1)
        phi = np.zeros(self.k)
        for mi, m in enumerate(self.masks):
            s = m.sum()
            for i in np.where(~m)[0]:
                m2 = m.copy(); m2[i] = True
                phi[i] += self.w[s] * (v[self.idx[tuple(m2)]] - v[mi])
        return phi


# ------------------------------------------------------------------ constitutional decision layer
def resolve(row: pd.Series, action: str) -> pd.Series:
    """Simulated outcome of an actionable step the payer can take (verification reveals the truth)."""
    r = row.copy()
    if action == "provide_second_identifier" and r["second_id_match"] == 0 and r.get("kind", "legit") != "sanctioned":
        r["name_match"] = 0.05
    if action == "complete_R16_data":
        r["r16_complete"] = 1.0
    if action == "re_authenticate_device" and r.get("kind", "legit") != "cyber":
        r["device_risk"] = 0.05
    return r


ACTIONS = ["provide_second_identifier", "complete_R16_data", "re_authenticate_device"]


def constitutional_decision(row, model, shap: ExactShap, C=CONSTITUTION, with_cf=True):
    x = row[FEATS].to_numpy(float)
    p = float(model.predict_proba(x[None, :])[0, 1])
    rec = {"score": round(p, 4)}
    amount = float(np.exp(row["log_amount"]))
    # R4 security override (symbolic typologies) - checked first, independent of amount
    cyber = row["device_risk"] >= C["R4_cyber_device"] and row["velocity_24h"] >= C["R4_cyber_velocity"]
    layering = (row["fan_out"] >= C["R4_layer_fanout"] and row["account_age_days"] < C["R4_layer_age"]
                and p >= C["R4_layer_score"])
    name_hit = row["name_match"] >= C["name_screen"]
    if p < C["tau_alert"] and not (cyber or layering or name_hit):
        return {**rec, "decision": "RELEASE", "rule": "below alert threshold"}
    phi = shap.explain(x)
    order = np.argsort(-phi)
    rec["top3"] = [(FEATS[i], round(float(phi[i]), 4)) for i in order[:3]]
    if cyber or layering:
        return {**rec, "decision": "HOLD+FIU_ALERT", "rule": "R4 security override: "
                + ("compromised-device burst" if cyber else "shell-company layering typology")}
    pos = np.clip(phi, 0, None)
    name_share = pos[FEATS.index("name_match")] / pos.sum() if pos.sum() > 0 else 0
    if name_hit and row["second_id_match"] == 1:
        return {**rec, "decision": "HOLD", "rule": "Sanctions match confirmed by second identifier (name + ID)",
                "counterfactual": None}
    if (name_hit or name_share >= C["R1_name_share"]) and row["second_id_match"] == 0 and (p < C["R2_max_score"] or name_hit):
        return {**rec, "decision": "VERIFY", "rule": "R1 no hold on name alone: request second identifier",
                "counterfactual": ["provide_second_identifier"]}
    if amount < C["R2_small_value_inr"] and p < C["R2_max_score"]:
        return {**rec, "decision": "RELEASE+MONITOR", "rule": "R2 proportionality tier (small value, moderate score)"}
    rec.update({"decision": "HOLD", "rule": "R3 hold with explanation and counterfactual"})
    if with_cf:  # R3: smallest set of actionable steps that would clear the payment
        rec["counterfactual"] = None
        for size in (1, 2, 3):
            for combo in itertools.combinations(ACTIONS, size):
                r2 = row.copy()
                for a in combo:
                    r2 = resolve(r2, a)
                p2 = float(model.predict_proba(r2[FEATS].to_numpy(float)[None, :])[0, 1])
                if p2 < C["tau_alert"]:
                    rec["counterfactual"] = list(combo); break
            if rec["counterfactual"]:
                break
        if rec["counterfactual"] is None:
            rec.update({"decision": "HOLD+HUMAN_REVIEW", "rule": "R3: no counterfactual exists -> human review"})
    return rec


class AuditLog:
    """Hash-chained audit trail: each record commits to the previous one (Traceability)."""
    def __init__(self, path):
        self.path, self.prev = path, "0" * 64
        self.f = open(path, "w", encoding="utf-8")

    def write(self, rec: dict):
        rec = {**rec, "prev_hash": self.prev}
        h = hashlib.sha256(json.dumps(rec, sort_keys=True, default=str).encode()).hexdigest()
        rec["hash"] = h
        self.f.write(json.dumps(rec, default=str) + "\n")
        self.prev = h


# ------------------------------------------------------------------ main experiment
def main():
    d = generate(DATA_ASSUMPTIONS["n_payments"])
    tr, te = train_test_split(d, test_size=0.25, random_state=SEED, stratify=d["illicit"])
    tr, va = train_test_split(tr, test_size=0.2, random_state=SEED, stratify=tr["illicit"])
    model = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08, random_state=SEED)
    model.fit(tr[FEATS].to_numpy(float), tr["illicit"].to_numpy())  # numpy: no feature-name overhead
    CONSTITUTION["tau_alert"] = float(np.quantile(model.predict_proba(va[FEATS].to_numpy(float))[:, 1], 1 - CONSTITUTION["alert_rate"]))
    te = te.copy()
    te["p"] = model.predict_proba(te[FEATS].to_numpy(float))[:, 1]
    auc = roc_auc_score(te["illicit"], te["p"])
    shap = ExactShap(model, tr[FEATS].sample(40, random_state=SEED).to_numpy(float))

    # Black-box baseline: freeze whenever score >= tau, no reasons recorded
    te["bb_decision"] = np.where((te["p"] >= CONSTITUTION["tau_alert"]) | (te["name_match"] >= CONSTITUTION["name_screen"]), "HOLD", "RELEASE")

    # Constitutional layer on every test payment; time the examined (flagged) ones
    log = AuditLog(RES / "audit_log.jsonl")
    decisions, lat, shap_rows = [], [], []
    C = CONSTITUTION
    screen = (te["p"] >= C["tau_alert"]) | (te["name_match"] >= C["name_screen"]) | ((te["device_risk"] >= C["R4_cyber_device"]) & (te["velocity_24h"] >= C["R4_cyber_velocity"]))              | (te["fan_out"] >= C["R4_layer_fanout"])
    for tx_id, row in te.iterrows():
        if not screen.loc[tx_id]:
            decisions.append("RELEASE"); continue
        t0 = time.perf_counter()
        rec = constitutional_decision(row, model, shap)
        dt = (time.perf_counter() - t0) * 1000
        if rec["decision"] != "RELEASE":
            lat.append(dt)
            log.write({"tx_id": int(tx_id), **rec})
            if "top3" in rec:
                shap_rows.append({"tx_id": int(tx_id), **{f: row[f] for f in FEATS},
                                  **{"phi_" + f: v for f, v in zip(FEATS, shap.explain(row[FEATS].to_numpy(float)))}})
        decisions.append(rec["decision"])
    te["ca_decision"] = decisions
    log.f.close()

    freeze = {"HOLD", "HOLD+FIU_ALERT", "HOLD+HUMAN_REVIEW"}
    legit, illicit = te[te.illicit == 0], te[te.illicit == 1]

    def per10k(mask_df, col):
        return round(1e4 * mask_df[col].isin(freeze).mean(), 1)

    # an illicit payment counts as stopped if frozen, or sent to VERIFY and it fails verification (sanctioned)
    def stopped(df, col):
        s = df[col].isin(freeze) | ((df[col] == "VERIFY") & (df["kind"] == "sanctioned"))
        return round(100 * s.mean(), 1)

    holds_ca = te[te.ca_decision.isin(freeze)]
    lines = []
    with open(RES / "audit_log.jsonl", encoding="utf-8") as f:
        lines = [json.loads(x) for x in f]
    explained = [r for r in lines if r["decision"] in freeze]
    cf_cover = np.mean([bool(r.get("counterfactual")) or r["decision"] != "HOLD" or r["rule"].startswith("Sanctions match confirmed") for r in explained])
    # name-only holds under black box: held legit payments whose largest SHAP driver is name_match
    sr = pd.DataFrame(shap_rows).set_index("tx_id")
    bb_legit_held = legit[legit.bb_decision == "HOLD"].index.intersection(sr.index)
    phi_cols = ["phi_" + f for f in FEATS]
    name_top = (sr.loc[bb_legit_held, phi_cols].idxmax(axis=1) == "phi_name_match").sum()

    hold_recs = {r["tx_id"]: r for r in explained}
    cf_legit = [bool(hold_recs[i].get("counterfactual")) for i in hold_recs if te.loc[i, "illicit"] == 0]
    cf_illicit = [bool(hold_recs[i].get("counterfactual")) for i in hold_recs if te.loc[i, "illicit"] == 1]
    results = {
        "model_auc": round(auc, 4), "n_test": len(te), "n_legit_test": len(legit), "n_illicit_test": len(illicit),
        "wrongful_freezes_per_10k_legit": {"black_box": per10k(legit, "bb_decision"), "constitutional": per10k(legit, "ca_decision")},
        "wrongful_freezes_per_10k_transliterated": {"black_box": per10k(legit[legit.translit == 1], "bb_decision"),
                                                    "constitutional": per10k(legit[legit.translit == 1], "ca_decision")},
        "wrongful_freezes_per_10k_other_names": {"black_box": per10k(legit[legit.translit == 0], "bb_decision"),
                                                 "constitutional": per10k(legit[legit.translit == 0], "ca_decision")},
        "legit_sent_to_verify_per_10k": round(1e4 * (legit.ca_decision == "VERIFY").mean(), 1),
        "legit_release_monitor_per_10k": round(1e4 * (legit.ca_decision == "RELEASE+MONITOR").mean(), 1),
        "illicit_stopped_pct": {"black_box": stopped(illicit, "bb_decision"), "constitutional": stopped(illicit, "ca_decision")},
        "illicit_stopped_pct_by_kind": {k: {"black_box": stopped(illicit[illicit.kind == k], "bb_decision"),
                                            "constitutional": stopped(illicit[illicit.kind == k], "ca_decision")}
                                        for k in ["sanctioned", "layering", "cyber"]},
        "black_box_legit_holds_driven_mainly_by_name_match": int(name_top), "black_box_legit_holds": int(len(bb_legit_held)),
        "explanation_coverage_of_freezes_pct": {"black_box": 0.0, "constitutional": round(100.0, 1)},
        "counterfactual_or_review_coverage_pct": round(100 * float(cf_cover), 1),
        "counterfactual_available_pct": {"wrongly_frozen_legit": round(100 * float(np.mean(cf_legit)), 1) if cf_legit else None,
                                         "frozen_illicit": round(100 * float(np.mean(cf_illicit)), 1) if cf_illicit else None,
                                         "n_legit": len(cf_legit), "n_illicit": len(cf_illicit)},
        "tau_alert": round(CONSTITUTION["tau_alert"], 4),
        "alert_precision_black_box_pct": round(100 * te.loc[te.bb_decision == "HOLD", "illicit"].mean(), 1),
        "legit_frozen_by_segment_per_10k": {g: {"black_box": per10k(legit[legit.segment == g], "bb_decision"),
                                                "constitutional": per10k(legit[legit.segment == g], "ca_decision")}
                                            for g in ["ordinary", "trader", "traveller", "new_account"]},
        "fiu_alerts": int((te.ca_decision == "HOLD+FIU_ALERT").sum()),
        "latency_ms_examined": {"n": len(lat), "median": round(float(np.median(lat)), 1),
                                "p95": round(float(np.percentile(lat, 95)), 1), "max": round(float(np.max(lat)), 1)},
        "decision_counts": te.ca_decision.value_counts().to_dict(),
        "audit_records": len(lines), "audit_chain_head": lines[-1]["hash"] if lines else None,
        "constitution": CONSTITUTION, "data_assumptions": DATA_ASSUMPTIONS,
    }
    (RES / "results.json").write_text(json.dumps(results, indent=1, default=str), encoding="utf-8")
    sr.to_csv(RES / "shap_examined.csv")
    pd.Series(lat).to_csv(RES / "latency_ms.csv", index=False)
    te[["kind", "segment", "translit", "p", "bb_decision", "ca_decision"] + FEATS].to_csv(RES / "test_decisions.csv")
    print(json.dumps({k: v for k, v in results.items() if k not in ("constitution", "data_assumptions")}, indent=1, default=str))
    return model, shap


if __name__ == "__main__":
    main()
