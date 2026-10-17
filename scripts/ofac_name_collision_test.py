"""Experiment 3 (real data): how often do ordinary names collide with the OFAC SDN list under fuzzy name screening?

Real watch list: US Treasury OFAC SDN list (public CSV). Test names are constructed from common given names and
surnames; they refer to no real person. We measure the share of names that trigger a fuzzy 'hit' and how much the
hit rate moves across transliteration variants of the same name. Name groups are defined by naming convention
(South Asian-transliterated vs Anglo), not by religion or ethnicity of any individual.
"""
import csv
import difflib
import itertools
import json
import pathlib
import re
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SDN = ROOT / "02_Sources_PDF" / "ofac" / "SDN.CSV"
RES = ROOT / "10_Experiment_Results"
THRESHOLDS = [0.80, 0.85, 0.90]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s.lower())).strip()


# --- watch list: individuals only; SDN names are "SURNAME, Given names"
listed = []
with open(SDN, encoding="latin-1") as f:
    for row in csv.reader(f):
        if len(row) > 2 and row[2].strip().lower() == "individual":
            n = row[1]
            if "," in n:
                last, first = n.split(",", 1)
                n = f"{first} {last}"
            listed.append(norm(n))
listed = sorted(set(listed))
by_len = {}
for n in listed:
    by_len.setdefault(len(n) // 4, []).append(n)

# --- test names (constructed; 10 x 8 per group)
IN_FIRST = ["mohammed", "abdul", "rahul", "amit", "priya", "sunita", "ravi", "suresh", "imran", "fatima"]
IN_LAST = ["khan", "singh", "kumar", "sharma", "shaikh", "ahmed", "hussain", "reddy"]
EN_FIRST = ["john", "david", "michael", "james", "mary", "sarah", "robert", "linda", "peter", "susan"]
EN_LAST = ["smith", "johnson", "brown", "williams", "jones", "miller", "davis", "wilson"]
VARIANTS = {"mohammed": ["muhammad", "mohd", "mohamed", "mohammad"], "abdul": ["abdool", "abdel"],
            "hussain": ["husain", "hussein", "husein"], "shaikh": ["sheikh", "shaik", "sheik"], "ahmed": ["ahmad", "ahamed"],
            "fatima": ["fathima", "fatma"], "imran": ["imraan"], "khan": ["kahn"], "singh": ["sing"], "sharma": ["sarma"],
            "suresh": ["sooresh"], "reddy": ["reddi"], "kumar": ["kumaar"], "priya": ["preeya"], "sunita": ["suneeta"],
            "rahul": ["raahul"], "amit": ["ameet"], "ravi": ["ravee"]}


def best_sim(name: str) -> float:
    b = len(name) // 4
    cands = by_len.get(b - 1, []) + by_len.get(b, []) + by_len.get(b + 1, [])
    sm = difflib.SequenceMatcher(None, name)
    best = 0.0
    for c in cands:
        sm.set_seq1(c) if False else None
        s = difflib.SequenceMatcher(None, name, c)
        if s.real_quick_ratio() < best or s.quick_ratio() < best:
            continue
        best = max(best, s.ratio())
    return best


t0 = time.time()
rows = []
for grp, F, L in [("South Asian-transliterated", IN_FIRST, IN_LAST), ("Anglo", EN_FIRST, EN_LAST)]:
    for f, l in itertools.product(F, L):
        base = f"{f} {l}"
        sims = {base: best_sim(base)}
        if grp.startswith("South"):
            for vf in [f] + VARIANTS.get(f, []):
                for vl in [l] + VARIANTS.get(l, []):
                    v = f"{vf} {vl}"
                    if v not in sims:
                        sims[v] = best_sim(v)
        rows.append({"group": grp, "base": base, "base_sim": sims[base], "n_variants": len(sims),
                     "min_sim": min(sims.values()), "max_sim": max(sims.values())})

res = {"sdn_individuals": len(listed), "runtime_s": round(time.time() - t0, 1), "by_threshold": {}}
for th in THRESHOLDS:
    out = {}
    for grp in ["South Asian-transliterated", "Anglo"]:
        g = [r for r in rows if r["group"] == grp]
        out[grp] = {"names": len(g), "hit_rate_base_pct": round(100 * sum(r["base_sim"] >= th for r in g) / len(g), 1)}
        if grp.startswith("South"):
            out[grp]["hit_rate_any_variant_pct"] = round(100 * sum(r["max_sim"] >= th for r in g) / len(g), 1)
            out[grp]["outcome_depends_on_spelling_pct"] = round(100 * sum((r["max_sim"] >= th) != (r["min_sim"] >= th) for r in g) / len(g), 1)
    res["by_threshold"][str(th)] = out
(RES / "ofac_name_collision.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
with open(RES / "ofac_name_collision_rows.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(json.dumps(res, indent=1))
