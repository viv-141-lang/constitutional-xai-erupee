"""Robustness of Experiment 1 (referee M1-M3): 20 seeds x 2 name-bias settings, stronger baselines,
matched-recall comparison and four-way outcomes including wrongful verifications.

Policies (all on identical payments within a seed):
  BB        black box: freeze every alert (score >= tau or name screen)
  BB-match  black box with tau raised until illicit-frozen share matches the full constitution's
  BB+ID     black box + 'second identifier before freeze' (rule R1 only)
  CONST     full constitution (R4, R1, R2; R3 explanations)
Thresholds tau, mu, kappa and R4 parameters are fixed in advance or on the validation split; nothing uses the test set
except BB-match, which is deliberately an operating point chosen on the test set to favour the baseline.
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

import experiment_4ta as E

C = E.CONSTITUTION
SEEDS = list(range(1, 21))
BIAS = [0.6, 0.0]


def run(seed, bias):
    E.rng = np.random.default_rng(seed)
    E.DATA_ASSUMPTIONS["bias_scale"] = bias
    d = E.generate(E.DATA_ASSUMPTIONS["n_payments"])
    tr, te = train_test_split(d, test_size=0.25, random_state=seed, stratify=d["illicit"])
    tr, va = train_test_split(tr, test_size=0.2, random_state=seed, stratify=tr["illicit"])
    m = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08, random_state=seed)
    m.fit(tr[E.FEATS].to_numpy(float), tr["illicit"].to_numpy())
    tau = float(np.quantile(m.predict_proba(va[E.FEATS].to_numpy(float))[:, 1], 1 - C["alert_rate"]))
    te = te.copy()
    te["p"] = m.predict_proba(te[E.FEATS].to_numpy(float))[:, 1]
    shap = E.ExactShap(m, tr[E.FEATS].sample(40, random_state=seed).to_numpy(float))
    name_hit = (te.name_match >= C["name_screen"]).to_numpy()
    alert = (te.p >= tau).to_numpy() | name_hit
    eta = np.zeros(len(te))
    for k in np.where(alert)[0]:
        phi = np.clip(shap.explain(te.iloc[k][E.FEATS].to_numpy(float)), 0, None)
        eta[k] = phi[E.FEATS.index("name_match")] / phi.sum() if phi.sum() > 0 else 0
    amount = np.exp(te.log_amount.to_numpy()); p = te.p.to_numpy(); sid = te.second_id_match.to_numpy()
    cyber = (te.device_risk >= C["R4_cyber_device"]).to_numpy() & (te.velocity_24h >= C["R4_cyber_velocity"]).to_numpy()
    layer = (te.fan_out >= C["R4_layer_fanout"]).to_numpy() & (te.account_age_days < C["R4_layer_age"]).to_numpy() & (p >= C["R4_layer_score"])

    def policy(r1, r2, r4, a=alert):
        out = np.where(a, "FREEZE", "RELEASE").astype(object)
        if r4:
            out[cyber | layer] = "FREEZE"
        rest = (out == "FREEZE") & ~(cyber | layer if r4 else np.zeros(len(out), bool))
        if r1:
            mm = rest & (sid == 0) & (name_hit | ((eta >= C["R1_name_share"]) & (p < C["R2_max_score"])))
            out[mm] = "VERIFY"; rest &= ~mm
        if r2:
            mm = rest & ~(name_hit & (sid == 1)) & (amount < C["R2_small_value_inr"]) & (p < C["R2_max_score"])
            out[mm] = "MONITOR"
        return out

    L = (te.illicit == 0).to_numpy(); I = ~L; T = (te.translit == 1).to_numpy(); sanc = (te.kind == "sanctioned").to_numpy()

    def metrics(o):
        fr = o == "FREEZE"; ve = o == "VERIFY"; mo = o == "MONITOR"
        stopped = fr | (ve & sanc)
        return {"wf_all": 1e4 * fr[L].mean(), "wf_translit": 1e4 * fr[L & T].mean(), "wf_other": 1e4 * fr[L & ~T].mean(),
                "gap": 1e4 * (fr[L & T].mean() - fr[L & ~T].mean()),
                "wverify_translit": 1e4 * ve[L & T].mean(), "wverify_other": 1e4 * ve[L & ~T].mean(),
                "illicit_frozen": 100 * stopped[I].mean(), "illicit_frozen_verified_or_monitored": 100 * (stopped | ve | mo)[I].mean(),
                "illicit_released_unmonitored": 100 * (o == "RELEASE")[I].mean(),
                "illicit_released_monitored": 100 * (mo & ~stopped)[I].mean()}

    res = {"CONST": metrics(policy(True, True, True)), "BB": metrics(policy(False, False, False)),
           "BB+ID": metrics(policy(True, False, False))}
    target = res["CONST"]["illicit_frozen"]
    best = None
    for t in np.quantile(p, np.linspace(0.9, 0.9995, 300)):                 # raise tau until recall matches
        o = policy(False, False, False, a=(p >= t) | name_hit)
        mt = metrics(o)
        if best is None or abs(mt["illicit_frozen"] - target) < abs(best["illicit_frozen"] - target):
            best = mt
    res["BB-match"] = best
    res["n_illicit"] = int(I.sum()); res["n_legit_translit"] = int((L & T).sum()); res["n_legit_other"] = int((L & ~T).sum())
    return res


rows = []
for bias in BIAS:
    for s in SEEDS:
        r = run(s, bias)
        for pol in ["BB", "BB-match", "BB+ID", "CONST"]:
            rows.append({"bias": bias, "seed": s, "policy": pol, **r[pol], "n_illicit": r["n_illicit"],
                         "n_legit_translit": r["n_legit_translit"], "n_legit_other": r["n_legit_other"]})
        print(f"bias={bias} seed={s} done", flush=True)
df = pd.DataFrame(rows)
df.to_csv(E.RES / "robustness_runs.csv", index=False)
cols = ["wf_all", "wf_translit", "wf_other", "gap", "wverify_translit", "wverify_other", "illicit_frozen",
        "illicit_frozen_verified_or_monitored", "illicit_released_unmonitored", "illicit_released_monitored"]
summ = df.groupby(["bias", "policy"])[cols].agg(["mean", lambda x: np.percentile(x, 2.5), lambda x: np.percentile(x, 97.5)])
summ.columns = [f"{c}_{s}" for c, s in [(a, {"mean": "mean", "<lambda_0>": "lo", "<lambda_1>": "hi"}[b]) for a, b in summ.columns]]
summ.round(1).to_csv(E.RES / "robustness_summary.csv")
print(summ.round(1)[[f"{c}_mean" for c in ["wf_all", "gap", "illicit_frozen", "illicit_frozen_verified_or_monitored"]]].to_string())
