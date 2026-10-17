"""Ablation and proportionality sweep for the 4T-A constitution.

Computes each screened payment's components once (score, Shapley values, typology flags, counterfactual
availability), then re-applies different rule sets, so every policy is compared on identical payments.
"""
import itertools
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

import experiment_4ta as E

C = E.CONSTITUTION
d = E.generate(E.DATA_ASSUMPTIONS["n_payments"])          # same seed -> same data as the main run
tr, te = train_test_split(d, test_size=0.25, random_state=E.SEED, stratify=d["illicit"])
tr, va = train_test_split(tr, test_size=0.2, random_state=E.SEED, stratify=tr["illicit"])
model = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08, random_state=E.SEED)
model.fit(tr[E.FEATS].to_numpy(float), tr["illicit"].to_numpy())
C["tau_alert"] = float(np.quantile(model.predict_proba(va[E.FEATS].to_numpy(float))[:, 1], 1 - C["alert_rate"]))
shap = E.ExactShap(model, tr[E.FEATS].sample(40, random_state=E.SEED).to_numpy(float))
te = te.copy()
te["p"] = model.predict_proba(te[E.FEATS].to_numpy(float))[:, 1]
te["amount"] = np.exp(te["log_amount"])
te["cyber"] = (te.device_risk >= C["R4_cyber_device"]) & (te.velocity_24h >= C["R4_cyber_velocity"])
te["layer"] = (te.fan_out >= C["R4_layer_fanout"]) & (te.account_age_days < C["R4_layer_age"]) & (te.p >= C["R4_layer_score"])
te["name_hit"] = te.name_match >= C["name_screen"]
te["alert"] = (te.p >= C["tau_alert"]) | te.name_hit

# components for alerted payments
name_share = pd.Series(0.0, index=te.index)
for i, row in te[te.alert].iterrows():
    phi = np.clip(shap.explain(row[E.FEATS].to_numpy(float)), 0, None)
    name_share[i] = phi[E.FEATS.index("name_match")] / phi.sum() if phi.sum() > 0 else 0
te["name_share"] = name_share


def policy(df, R1=True, R2=True, R4=True, r2_amount=C["R2_small_value_inr"]):
    out = np.where(df.alert, "HOLD", "RELEASE").astype(object)
    if R4:
        out[(df.cyber | df.layer).to_numpy()] = "HOLD+FIU_ALERT"
    rest = (out == "HOLD")
    if R1:
        m = rest & (df.second_id_match == 0).to_numpy() & (df.name_hit | ((df.name_share >= C["R1_name_share"]) & (df.p < C["R2_max_score"]))).to_numpy()
        out[m] = "VERIFY"; rest &= ~m
    if R2:
        m = rest & ~(df.name_hit & (df.second_id_match == 1)).to_numpy()
        m = m & (df.amount < r2_amount).to_numpy() & (df.p < C["R2_max_score"]).to_numpy()
        out[m] = "RELEASE+MONITOR"
    return out


def score(df, dec):
    frozen = pd.Series(dec, index=df.index).isin(["HOLD", "HOLD+FIU_ALERT"])
    verify = pd.Series(dec, index=df.index) == "VERIFY"
    monitor = pd.Series(dec, index=df.index) == "RELEASE+MONITOR"
    L, I = df.illicit == 0, df.illicit == 1
    stopped = frozen | (verify & (df.kind == "sanctioned"))
    return {
        "wrongful_freezes_per_10k": round(1e4 * frozen[L].mean(), 1),
        "wrongful_freezes_translit_per_10k": round(1e4 * frozen[L & (df.translit == 1)].mean(), 1),
        "wrongful_freezes_other_per_10k": round(1e4 * frozen[L & (df.translit == 0)].mean(), 1),
        "illicit_stopped_pct": round(100 * stopped[I].mean(), 1),
        "illicit_stopped_or_monitored_pct": round(100 * (stopped | monitor)[I].mean(), 1),
        "legit_monitored_per_10k": round(1e4 * monitor[L].mean(), 1),
    }


rows = []
for name, kw in [("Black box (freeze on score)", dict(R1=False, R2=False, R4=False)),
                 ("+ R4 security override", dict(R1=False, R2=False, R4=True)),
                 ("+ R1 no hold on name alone", dict(R1=True, R2=False, R4=True)),
                 ("+ R2 proportionality (full constitution)", dict(R1=True, R2=True, R4=True))]:
    rows.append({"policy": name, **score(te, policy(te, **kw))})
ablation = pd.DataFrame(rows)

sweep = []
for amt in [0, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000]:
    sweep.append({"r2_threshold_inr": amt, **score(te, policy(te, r2_amount=amt))})
sweep = pd.DataFrame(sweep)

ablation.to_csv(E.RES / "ablation.csv", index=False)
sweep.to_csv(E.RES / "proportionality_sweep.csv", index=False)
print(ablation.to_string(index=False)); print(); print(sweep.to_string(index=False))
