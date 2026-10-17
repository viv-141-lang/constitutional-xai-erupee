"""Experiment 3 (Tier 1): purpose-bound welfare payments with citizen choice and accountability.

Two schemes (student tuition grant, farmer debt relief) are paid through four regimes on IDENTICAL beneficiaries,
payees and misuse draws within each seed:
  A   today's DBT bank transfer: money is unrestricted
  A2  approved-vendor list (e-RUPI / current e-rupee pilot style); generic decline code, ordinary grievance
  B   hybrid payee rule (W1) on programmable e-rupee, but silent failures, unsigned lists, no ladder, no payee scoring
  C   the full design: W1-W8 + governance (reasoned failures, recovery ladder, signed eligibility lists,
      payee risk scores, purpose-bound refunds, idle reclaim, emergency release, identity fallback)
Headline (Design Note s.6): payee choice chi (Eq. 13) at matched misuse control M (Eq. 14).
Every number that is an assumption sits in ASSUME and is varied in the robustness runs. All data are SYNTHETIC.
Tamper detection for B and C is not assumed: records are actually edited in a SHA-256 chain and the chain re-verified.
"""
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "10_Experiment_Results"
REGIMES = ["A", "A2", "B", "C"]

ASSUME = {
    # population and payees
    "n_students": 20_000, "n_farmers": 20_000, "n_districts": 4, "blocks_per_district": 10, "villages_per_block": 10,
    "colleges": (30, 60), "banks": (15, 30), "coops": (20, 40), "informal": (30, 60),   # per district, uniform range
    "empanel_share": 0.25,         # A2: share of registered colleges/co-ops on the approved list (banks all approved)
    "vetting_catch": 0.5,          # A2: chance that empanelment vetting excludes a colluding payee
    "p_student_enrolled": 0.70,    # tuition payee known at disbursement (designated college)
    "p_switch": 0.05,              # enrolled student changes college mid-year
    "p_bank": 0.60, "p_coop": 0.35, "p_informal": 0.25,                               # farmer has debt with ...
    # misuse
    "p_misuse": 0.08, "misuse_share": 0.30,        # genuine beneficiary tries to spend part outside the purpose
    "p_colluding_payee": 0.03, "p_kickback": 0.70, "kickback_share": 0.50, "p_refund_on_ledger": 0.50,
    "p_ghost": 0.02, "corrupt_officers": 2, "officers_per_district": 5,
    "skim_rate": 0.03,             # one district layer skims this share of every transfer passing through it
    "n_tamper": 20,                # edits to past payment records and to the eligibility list (each)
    # genuine edge cases
    "p_id_fail": 0.03, "p_emergency": 0.01, "p_idle": 0.04, "p_idle_late_genuine": 0.25,
    # conventional controls (regimes A, A2, B)
    "p_audit_conventional": 0.20,  # sample audit finds a given ghost / kickback
    "p_reconcile_conventional": 0.30,   # manual reconciliation finds a skim or an edited record
    "p_recover_conventional": 0.30,     # detected misuse money actually recovered by ordinary legal process
    # design controls (regime C)
    "payee_flag_top": 0.05, "p_audit_confirms_flag": 0.80,
    "p_fraud_appeal": 0.50, "p_appeal_overturn_fraud": 0.10,
    # resolution of genuine blocks: P(knows reason) x P(fix exists) x P(channel answers in time)
    "know": {"A2": 0.5, "B": 0.2, "C": 1.0},
    "channel30": {"A2": 0.25, "B": 0.25, "C": 0.80}, "channel60": {"A2": 0.40, "B": 0.40, "C": 1.0},
    "fix_unapproved_payee_A2": 0.20,   # the payee gets empanelled in time
    "fix_informal_lender": 0.30,       # an informal lender registers in time (all regimes)
    "fix_id": {"A2": 0.60, "B": 0.60, "C": 0.95},   # single office vs any branch / officer (decision 15)
    "fix_emergency_C": 0.90,           # logged release within 48 h (W5)
    "k_min": 10, "idle_days": 90,
}


# --------------------------------------------------------------------------------------------- W1, Eq. (12)
def admissible(regime, is_designated, in_registry, in_approved):
    """Return a boolean array: may this purpose-bound payment go to this payee under `regime`?

    is_designated : payee is the institution fixed at disbursement (enrolled college, known loan account)
    in_registry   : payee is in the scheme's certified category registry (recognised colleges; banks and co-ops)
    in_approved   : payee is on the approved-vendor list used by today's pilots
    Regime A pays unrestricted money, so every payee is admissible there.
    """
    if regime == "A":
        return np.ones_like(is_designated, bool)
    if regime == "A2":                              # today's pilots: approved vendors only
        return np.asarray(in_approved, bool)
    # B and C share the hybrid rule (they differ only in accountability): the designated payee
    # always passes, even if it later leaves the registry; otherwise any registered payee.
    return np.asarray(is_designated, bool) | np.asarray(in_registry, bool)


# --------------------------------------------------------------------------------------------- hash chain (Eq. 7)
class Chain:
    def __init__(self):
        self.recs, self.hashes = [], []

    def add(self, rec):
        prev = self.hashes[-1] if self.hashes else "0" * 64
        self.recs.append(dict(rec))
        self.hashes.append(hashlib.sha256((prev + json.dumps(rec, sort_keys=True, default=str)).encode()).hexdigest())

    def first_break(self):
        prev = "0" * 64
        for i, (r, h) in enumerate(zip(self.recs, self.hashes)):
            if hashlib.sha256((prev + json.dumps(r, sort_keys=True, default=str)).encode()).hexdigest() != h:
                return i
            prev = h
        return None


def tamper_test(rng, n_records=2000, n_edits=20):
    """Write a chain of hand-off records, edit n_edits past records one at a time, and check each is detected."""
    detected = 0
    for _ in range(n_edits):
        ch = Chain()
        for i in range(n_records):
            ch.add({"i": i, "from": "district", "to": f"w{i}", "amt": int(rng.integers(20_000, 100_000))})
        j = int(rng.integers(0, n_records))
        ch.recs[j]["amt"] += 1000                       # an official quietly changes a past amount
        detected += ch.first_break() == j
    return detected / n_edits


# --------------------------------------------------------------------------------------------- world
def build_world(rng, A):
    payees = []
    for d in range(A["n_districts"]):
        for kind in ["colleges", "banks", "coops", "informal"]:
            for _ in range(int(rng.integers(*A[kind]))):
                payees.append({"district": d, "kind": kind})
    P = pd.DataFrame(payees)
    P["pid"] = np.arange(len(P))
    P["in_registry"] = P.kind != "informal"
    P["colluding"] = rng.random(len(P)) < A["p_colluding_payee"]
    # approved-vendor list: all banks, a share of colleges and co-ops; vetting removes some colluders
    cand = P.kind.isin(["colleges", "coops"])
    pick = rng.random(len(P)) < A["empanel_share"]
    vetted_out = P.colluding & (rng.random(len(P)) < A["vetting_catch"])
    P["in_approved"] = ((P.kind == "banks") | (cand & pick)) & ~vetted_out & P.in_registry
    # payee risk features (W8): colluders inflate fees and grow enrolments; exact Shapley of a linear score
    P["fee_ratio"] = np.exp(rng.normal(0.25 * P.colluding, 0.15))
    P["growth"] = rng.normal(1.0 * P.colluding, 1.0)
    z = lambda s: (s - s.mean()) / s.std()
    P["phi_fee"], P["phi_growth"] = z(np.log(P.fee_ratio)), z(P.growth)
    P["risk"] = P.phi_fee + P.phi_growth
    P["flagged"] = P.groupby("kind").risk.rank(pct=True) > 1 - A["payee_flag_top"]
    return P


def build_beneficiaries(rng, A, P):
    rows = []
    nd, nb, nv = A["n_districts"], A["blocks_per_district"], A["villages_per_block"]
    for scheme, n in [("tuition", A["n_students"]), ("relief", A["n_farmers"])]:
        d = rng.integers(0, nd, n)
        b = rng.integers(0, nb, n)
        v = rng.integers(0, nv, n)
        if scheme == "tuition":
            age = rng.integers(17, 26, n)
            occ = np.where(rng.random(n) < 0.8, "student (UG)", "student (PG)")
            amt = np.round(np.exp(rng.normal(np.log(55_000), 0.35, n)), -2)
        else:
            age = rng.integers(20, 76, n)
            occ = rng.choice(["marginal farmer", "small farmer", "tenant farmer"], n, p=[0.5, 0.35, 0.15])
            amt = np.round(np.exp(rng.normal(np.log(35_000), 0.30, n)), -2)
        rows.append(pd.DataFrame({"scheme": scheme, "district": d, "block": d * nb + b, "village": (d * nb + b) * nv + v,
                                  "age": age, "occupation": occ, "amount": amt}))
    B = pd.concat(rows, ignore_index=True)
    B["bid"] = np.arange(len(B))
    B["officer"] = B.district * A["officers_per_district"] + rng.integers(0, A["officers_per_district"], len(B))
    # intended payee
    pid, desig, edge = np.empty(len(B), int), np.zeros(len(B), bool), np.array([""] * len(B), dtype=object)
    by = {(d, k): P.loc[(P.district == d) & (P.kind == k), "pid"].to_numpy() for d in range(nd)
          for k in ["colleges", "banks", "coops", "informal"]}
    for i, r in enumerate(B.itertuples()):
        if r.scheme == "tuition":
            pid[i] = rng.choice(by[(r.district, "colleges")])
            if rng.random() < A["p_student_enrolled"]:
                desig[i] = True
                if rng.random() < A["p_switch"]:                      # S6: switches college mid-year
                    pid[i], desig[i], edge[i] = rng.choice(by[(r.district, "colleges")]), False, "switch"
        else:
            has = {"banks": rng.random() < A["p_bank"], "coops": rng.random() < A["p_coop"],
                   "informal": rng.random() < A["p_informal"]}
            if not any(has.values()):
                has["banks"] = True
            kinds = [k for k, h in has.items() if h]
            k = kinds[int(rng.integers(len(kinds)))]
            pid[i] = rng.choice(by[(r.district, k)])
            desig[i] = kinds == ["banks"]                               # single known loan account
            if k == "coops":
                edge[i] = "coop"
            elif k == "informal":
                edge[i] = "informal"
    B["pid"], B["is_designated"], B["edge"] = pid, desig, edge
    B = B.merge(P[["pid", "kind", "in_registry", "in_approved", "colluding", "flagged"]], on="pid", how="left")
    n = len(B)
    B["id_fail"] = rng.random(n) < A["p_id_fail"]
    B["emergency"] = rng.random(n) < A["p_emergency"]
    B["idle"] = rng.random(n) < A["p_idle"]
    B["idle_late_genuine"] = B.idle & (rng.random(n) < A["p_idle_late_genuine"])
    B["misuse"] = rng.random(n) < A["p_misuse"]
    B["kickback"] = B.colluding & (rng.random(n) < A["p_kickback"])
    B["refund_on_ledger"] = rng.random(n) < A["p_refund_on_ledger"]
    return B


def add_ghosts(rng, A, B, P):
    """Corrupt officers add ghost entries; ghost money can only be extracted through a colluding payee (or as cash in A)."""
    n = int(A["p_ghost"] * len(B))
    officers = rng.choice(B.officer.unique(), A["corrupt_officers"], replace=False)
    G = B.sample(n, random_state=int(rng.integers(1 << 30))).copy()
    G["officer"] = rng.choice(officers, n)
    G["district"] = G.officer // A["officers_per_district"]
    col = P[P.colluding & P.in_registry]
    G["pid"] = [rng.choice(col.loc[col.district == d, "pid"].to_numpy()) if (col.district == d).any()
                else rng.choice(col.pid.to_numpy()) for d in G.district]
    G = G.drop(columns=["kind", "in_registry", "in_approved", "colluding", "flagged"]).merge(
        P[["pid", "kind", "in_registry", "in_approved", "colluding", "flagged"]], on="pid", how="left")
    G["is_designated"], G["edge"] = False, "ghost"
    G[["id_fail", "emergency", "idle", "idle_late_genuine", "misuse", "kickback"]] = False
    G["bid"] = np.arange(len(B), len(B) + n)
    return G


# --------------------------------------------------------------------------------------------- one regime
def run_regime(reg, rng, A, B, G, P, skim_district):
    u = rng.random                                       # independent draws per regime are fine: rates, not identities
    out = {}
    ok = admissible(reg, B.is_designated.to_numpy(), B.in_registry.to_numpy(), B.in_approved.to_numpy())
    ok = np.asarray(ok, bool)

    # ---- genuine blocks (wrongful): intended payee not admissible, identity failure, emergency need
    blocked_payee = ~ok & B.edge.isin(["switch", "coop", "informal"]).to_numpy()
    blocked_id = B.id_fail.to_numpy() & (reg != "A")
    blocked_emerg = B.emergency.to_numpy() & (reg != "A")
    if reg == "A":
        res30 = res60 = np.ones(len(B), bool)
    else:
        know, c30, c60 = A["know"][reg], A["channel30"][reg], A["channel60"][reg]
        fix = np.ones(len(B))
        fix[B.edge.eq("informal").to_numpy()] = A["fix_informal_lender"]
        if reg == "A2":
            fix[B.edge.isin(["switch", "coop"]).to_numpy()] = A["fix_unapproved_payee_A2"]
        fix_id = A["fix_id"][reg]
        p30 = np.where(blocked_payee, know * fix * c30, 1.0)
        p60 = np.where(blocked_payee, know * fix * c60, 1.0)
        p30 = np.where(blocked_id, p30 * know * fix_id * c30, p30)
        p60 = np.where(blocked_id, p60 * know * fix_id * c60, p60)
        fe = A["fix_emergency_C"] if reg == "C" else 0.0
        p30 = np.where(blocked_emerg, p30 * fe, p30)
        p60 = np.where(blocked_emerg, p60 * fe, p60)
        r = u(len(B))
        res30, res60 = r < p30, r < p60
    blk = blocked_payee | blocked_id | blocked_emerg
    n_gen = len(B)
    out["wrongful_blocks_per_10k"] = 1e4 * blk.sum() / n_gen
    out["blocks_resolved_30d_pct"] = 100 * (blk & res30).sum() / max(blk.sum(), 1)
    out["blocks_resolved_60d_pct"] = 100 * (blk & res60).sum() / max(blk.sum(), 1)

    # ---- misuse money: attempted, stopped at payment, recovered after audit (by type)
    att, stop, rec = {}, {}, {}
    amt = B.amount.to_numpy()
    # (1) spending outside the purpose by a genuine beneficiary
    m = B.misuse.to_numpy() & ~blk
    att["outside_purpose"] = (amt * A["misuse_share"])[m].sum()
    stop["outside_purpose"] = 0.0 if reg == "A" else att["outside_purpose"]
    rec["outside_purpose"] = 0.0
    # (2) kickbacks via colluding payees (only where the payment to the colluder goes through)
    kb = B.kickback.to_numpy() & ok & ~blk & (reg != "A")
    kamt = amt * A["kickback_share"]
    att["kickback"] = kamt[kb].sum()
    if reg == "C":
        on = kb & B.refund_on_ledger.to_numpy()
        stop["kickback"] = kamt[on].sum()                               # W8: refund lands in the purpose wallet
        cash = kb & ~B.refund_on_ledger.to_numpy()
        found = cash & B.flagged.to_numpy() & (u(len(B)) < A["p_audit_confirms_flag"])
        kept = u(len(B)) < 1 - A["p_fraud_appeal"] * A["p_appeal_overturn_fraud"]
        rec["kickback"] = kamt[found & kept].sum()
    else:
        stop["kickback"] = 0.0
        found = kb & (u(len(B)) < A["p_audit_conventional"])
        rec["kickback"] = kamt[found & (u(len(B)) < A["p_recover_conventional"])].sum()
    # (3) ghost beneficiaries added by corrupt officers
    gamt = G.amount.to_numpy()
    att["ghost"] = gamt.sum()
    g_ok = np.ones(len(G), bool) if reg == "A" else np.asarray(
        admissible(reg, G.is_designated.to_numpy(), G.in_registry.to_numpy(), G.in_approved.to_numpy()), bool)
    extracted = g_ok          # ghost money leaves only through an admissible colluding payee (assumed cash kickback)
    base_find = u(len(G)) < A["p_audit_conventional"]
    if reg == "C":                                                       # W7: one find exposes every entry the officer signed
        bad = set(G.officer[base_find])
        found = G.officer.isin(bad).to_numpy()
        kept = u(len(G)) < 1 - A["p_fraud_appeal"] * A["p_appeal_overturn_fraud"]
        stop["ghost"] = gamt[~extracted].sum()                           # unspendable; reclaimed early by W3
        rec["ghost"] = gamt[found & extracted & kept].sum()
        out["ghosts_traced_to_officer_pct"] = 100 * found.mean()
    else:
        stop["ghost"] = gamt[~extracted].sum()                           # unspendable; returns only at expiry
        rec["ghost"] = gamt[base_find & extracted & (u(len(G)) < A["p_recover_conventional"])].sum()
        out["ghosts_traced_to_officer_pct"] = 0.0
    out["ghosts_found_pct"] = 100 * (found.mean() if reg == "C" else base_find.mean())
    # (4) skimming by one district layer
    sk = (B.district == skim_district).to_numpy()
    att["skim"] = (amt[sk] * A["skim_rate"]).sum()
    stop["skim"] = 0.0
    if reg in ("B", "C"):                                                # hash-chained hand-offs reconcile automatically
        det = 1.0
        recov = 1 - A["p_fraud_appeal"] * A["p_appeal_overturn_fraud"] if reg == "C" else A["p_recover_conventional"]
    else:
        det, recov = A["p_reconcile_conventional"], A["p_recover_conventional"]
    rec["skim"] = att["skim"] * det * recov
    out["skim_detected"] = det
    for k in att:
        out[f"M_{k}_pct"] = 100 * (stop[k] + rec[k]) / att[k] if att[k] else np.nan
    out["M_pct"] = 100 * (sum(stop.values()) + sum(rec.values())) / sum(att.values())
    out["misuse_attempted_cr"] = sum(att.values()) / 1e7
    out["misuse_lost_cr"] = (sum(att.values()) - sum(stop.values()) - sum(rec.values())) / 1e7

    # ---- choice (Eq. 13): admissible payees available to a beneficiary, by district and scheme
    for scheme, kinds in [("tuition", ["colleges"]), ("relief", ["banks", "coops", "informal"])]:
        cnt = []
        for d in range(A["n_districts"]):
            Q = P[(P.district == d) & P.kind.isin(kinds)]
            if reg == "A":
                cnt.append(len(Q))
            else:
                cnt.append(int(np.asarray(admissible(reg, np.zeros(len(Q), bool), Q.in_registry.to_numpy(),
                                                     Q.in_approved.to_numpy()), bool).sum()))
        out[f"choice_{scheme}"] = float(np.median(cnt))
    out["coverage_relief_pct"] = 100 * ok[(B.scheme == "relief").to_numpy()].mean()

    # ---- idle money (W3 / W4)
    idle = B.idle.to_numpy() & ~blk
    out["idle_reallocated_cr"] = amt[idle].sum() / 1e7 if reg == "C" else 0.0
    out["idle_reinstated_pct"] = 100 * (u(int(B.idle_late_genuine.sum())) < A["know"]["C"] * A["channel60"]["C"] * 0.95).mean() \
        if reg == "C" and B.idle_late_genuine.any() else np.nan

    # ---- tamper evidence: payment records (all chained in B, C) and eligibility list (chained only in C)
    det_pay = tamper_test(rng, n_edits=A["n_tamper"]) if reg in ("B", "C") else (u(A["n_tamper"]) < A["p_reconcile_conventional"]).mean()
    det_list = tamper_test(rng, n_edits=A["n_tamper"]) if reg == "C" else (u(A["n_tamper"]) < A["p_audit_conventional"]).mean()
    out["tamper_payment_detected_pct"], out["tamper_list_detected_pct"] = 100 * det_pay, 100 * det_list
    return out


def disclosure(B, k_min):
    """Eq. (16): share of non-empty cells (area x age band x occupation x scheme) suppressed at each level."""
    D = B.assign(age_band=pd.cut(B.age, [16, 20, 25, 35, 50, 65, 80], labels=["17-20", "21-25", "26-35", "36-50", "51-65", "66+"]))
    rows = []
    for level in ["village", "block", "district"]:
        c = D.groupby([level, "age_band", "occupation", "scheme"], observed=True).size()
        rows.append({"level": level, "cells": len(c), "suppressed_pct": 100 * (c < k_min).mean(),
                     "people_in_suppressed_pct": 100 * c[c < k_min].sum() / c.sum()})
    return pd.DataFrame(rows)


def run(seed, A):
    rng = np.random.default_rng(seed)
    P = build_world(rng, A)
    B = build_beneficiaries(rng, A, P)
    G = add_ghosts(rng, A, B, P)
    skim_district = int(rng.integers(A["n_districts"]))
    rows = []
    for reg in REGIMES:
        r = run_regime(reg, np.random.default_rng([seed, REGIMES.index(reg)]), A, B, G, P, skim_district)
        rows.append({"seed": seed, "regime": reg, **r})
    return pd.DataFrame(rows), B, P


def frontier(A, seed=42):
    """Choice against misuse control as the approved list widens (A2), with B and C for comparison."""
    rows = []
    for share in [0.10, 0.25, 0.50, 0.75, 1.00]:
        A2 = dict(A, empanel_share=share)
        df, _, _ = run(seed, A2)
        for _, r in df[df.regime.isin(["A2"])].iterrows():
            rows.append({"empanel_share": share, "regime": "A2", "choice_tuition": r.choice_tuition,
                         "choice_relief": r.choice_relief, "M_pct": r.M_pct})
    df, _, _ = run(seed, A)
    for _, r in df[df.regime.isin(["B", "C"])].iterrows():
        rows.append({"empanel_share": np.nan, "regime": r.regime, "choice_tuition": r.choice_tuition,
                     "choice_relief": r.choice_relief, "M_pct": r.M_pct})
    return pd.DataFrame(rows)


def main():
    base, B, P = run(42, ASSUME)
    base.to_csv(RES / "welfare_seed42.csv", index=False)
    disclosure(B, ASSUME["k_min"]).to_csv(RES / "welfare_disclosure.csv", index=False)
    frontier(ASSUME).to_csv(RES / "welfare_frontier.csv", index=False)
    high = dict(ASSUME, p_misuse=0.16, p_colluding_payee=0.06, p_ghost=0.04, skim_rate=0.06)
    runs = pd.concat([run(s, A)[0].assign(setting=name) for name, A in [("base", ASSUME), ("high_misuse", high)]
                      for s in range(1, 21)], ignore_index=True)
    runs.to_csv(RES / "welfare_runs.csv", index=False)
    num = [c for c in runs.columns if c not in ("seed", "regime", "setting")]
    summ = runs.groupby(["setting", "regime"])[num].agg(["mean", lambda s: s.quantile(.025), lambda s: s.quantile(.975)])
    summ.columns = [f"{a}_{ {'mean': 'mean', '<lambda_0>': 'lo', '<lambda_1>': 'hi'}[b]}" for a, b in summ.columns]
    summ.reset_index().to_csv(RES / "welfare_summary.csv", index=False)
    (RES / "welfare_assumptions.json").write_text(json.dumps(ASSUME, indent=1), encoding="utf-8")
    pd.set_option("display.width", 200)
    print(base.set_index("regime").T.round(2))


if __name__ == "__main__":
    main()
