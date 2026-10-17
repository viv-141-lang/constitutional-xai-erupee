"""Experiment 3 v2 (referee M8): symmetric spelling expansion for every naming convention, six groups, Wilson CIs.

Groups are naming conventions, not religions or ethnicities of individuals; all test names are constructed and refer to
no real person. Arabic-origin names are included as a separate convention because they are common in India and
elsewhere and because the SDN list's composition may drive collisions independently of Indian transliteration.
"""
import csv
import difflib
import itertools
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SDN = ROOT / "02_Sources_PDF" / "ofac" / "SDN.CSV"
RES = ROOT / "10_Experiment_Results"
THS = [0.80, 0.85]

GROUPS = {
    "Indic-origin (South Asian)": (
        {"rahul": ["raahul"], "amit": ["ameet"], "priya": ["preeya"], "sunita": ["suneeta"], "ravi": ["ravee"],
         "suresh": ["sooresh"], "lakshmi": ["laxmi"], "venkatesh": ["venkatesha"]},
        {"sharma": ["sarma"], "singh": ["sing"], "kumar": ["kumaar"], "reddy": ["reddi"], "iyer": ["aiyer"],
         "choudhary": ["chaudhary", "chowdhury"], "gupta": ["guptha"], "patel": ["pattel"]}),
    "Arabic-origin (common in South Asia and elsewhere)": (
        {"mohammed": ["muhammad", "mohd", "mohamed"], "abdul": ["abdool", "abdel"], "imran": ["imraan"],
         "fatima": ["fathima", "fatma"], "ahmed": ["ahmad"], "ali": ["aly"], "hussain": ["husain", "hussein"], "ayesha": ["aisha"]},
        {"khan": ["kahn"], "shaikh": ["sheikh", "shaik"], "ahmed": ["ahmad"], "hussain": ["husain", "hussein"],
         "ali": ["aly"], "qureshi": ["quraishi"], "siddiqui": ["siddiqi"], "ansari": ["ansary"]}),
    "Anglo": (
        {"john": ["jon"], "michael": ["micheal"], "catherine": ["katherine"], "sarah": ["sara"], "steven": ["stephen"],
         "linda": ["lynda"], "peter": ["pete"], "susan": ["suzan"]},
        {"smith": ["smyth"], "johnson": ["jonson"], "brown": ["browne"], "williams": ["william"], "jones": ["jone"],
         "miller": ["millar"], "davis": ["davies"], "wilson": ["willson"]}),
    "Hispanic": (
        {"jose": ["jose"], "juan": ["joan"], "maria": ["mariah"], "carlos": ["karlos"], "luis": ["louis"], "ana": ["anna"],
         "jorge": ["jorje"], "miguel": ["migel"]},
        {"garcia": ["garsia"], "rodriguez": ["rodrigues"], "martinez": ["martines"], "hernandez": ["hernandes"],
         "lopez": ["lopes"], "gonzalez": ["gonzales"], "perez": ["peres"], "sanchez": ["sanches"]}),
    "Russian (transliterated)": (
        {"sergei": ["sergey"], "alexander": ["aleksandr"], "dmitry": ["dmitri"], "olga": ["olgha"], "natalia": ["natalya"],
         "andrei": ["andrey"], "vladimir": ["wladimir"], "elena": ["yelena"]},
        {"ivanov": ["ivanoff"], "smirnov": ["smirnoff"], "kuznetsov": ["kuznetsoff"], "popov": ["popoff"],
         "petrov": ["petroff"], "sokolov": ["sokoloff"], "volkov": ["volkoff"], "morozov": ["morozoff"]}),
    "Chinese (pinyin)": (
        {"wei": ["way"], "fang": ["fong"], "jing": ["ching"], "lei": ["lui"], "ming": ["meng"], "xiaoming": ["hsiaoming"],
         "hui": ["hwei"], "jun": ["chun"]},
        {"wang": ["wong"], "li": ["lee"], "zhang": ["chang"], "liu": ["lau"], "chen": ["chan"], "yang": ["yeung"],
         "zhao": ["chao"], "huang": ["hwang"]}),
}


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s.lower())).strip()


listed = set()
with open(SDN, encoding="latin-1") as f:
    for row in csv.reader(f):
        if len(row) > 2 and row[2].strip().lower() == "individual":
            n = row[1]
            if "," in n:
                last, first = n.split(",", 1); n = f"{first} {last}"
            listed.add(norm(n))
by_len = {}
for n in listed:
    by_len.setdefault(len(n) // 4, []).append(n)
cache = {}


def best(name):
    if name in cache:
        return cache[name]
    b = len(name) // 4; top = 0.0
    for c in by_len.get(b - 1, []) + by_len.get(b, []) + by_len.get(b + 1, []):
        s = difflib.SequenceMatcher(None, name, c)
        if s.real_quick_ratio() <= top or s.quick_ratio() <= top:
            continue
        top = max(top, s.ratio())
    cache[name] = top
    return top


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round(100 * (c - h) / d, 1), round(100 * (c + h) / d, 1))


out, rows = {"sdn_individuals": len(listed), "names_per_group": 64, "groups": {}}, []
for g, (F, L) in GROUPS.items():
    for f, l in itertools.product(F, L):
        spellings = {f"{a} {b}" for a in [f] + F[f] for b in [l] + L[l]}
        sims = [best(s) for s in spellings]
        rows.append({"group": g, "base": f"{f} {l}", "n_spellings": len(spellings), "base_sim": best(f"{f} {l}"),
                     "min_sim": min(sims), "max_sim": max(sims)})
    gr = [r for r in rows if r["group"] == g]
    out["groups"][g] = {}
    for th in THS:
        kb = sum(r["base_sim"] >= th for r in gr); ka = sum(r["max_sim"] >= th for r in gr)
        kall = sum(r["min_sim"] >= th for r in gr); n = len(gr)
        out["groups"][g][str(th)] = {"base_pct": round(100 * kb / n, 1), "base_ci": wilson(kb, n),
                                     "any_spelling_pct": round(100 * ka / n, 1), "any_ci": wilson(ka, n),
                                     "all_spellings_pct": round(100 * kall / n, 1),
                                     "spelling_dependent_pct": round(100 * (ka - kall) / n, 1),
                                     "mean_spellings": round(sum(r["n_spellings"] for r in gr) / n, 2)}
    print(g, out["groups"][g]["0.8"], flush=True)
(RES / "ofac_name_collision_v2.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
with open(RES / "ofac_name_collision_v2_rows.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

# ---- Fisher tests against the Anglo group and Figure 9 (dot-and-interval plot; no bars)
from scipy.stats import fisher_exact
import matplotlib.pyplot as plt

def count(gname, key, th=0.80):
    return sum(r[key] >= th for r in rows if r["group"] == gname)

A = "Anglo"
out["fisher_vs_anglo_at_0.8"] = {
    gname: {"base_p": fisher_exact([[count(gname, "base_sim"), 64 - count(gname, "base_sim")], [count(A, "base_sim"), 64 - count(A, "base_sim")]])[1],
            "any_p": fisher_exact([[count(gname, "max_sim"), 64 - count(gname, "max_sim")], [count(A, "max_sim"), 64 - count(A, "max_sim")]])[1]}
    for gname in GROUPS if gname != A}
(RES / "ofac_name_collision_v2.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

order = ["Anglo", "Hispanic", "Indic-origin (South Asian)", "Russian (transliterated)",
         "Arabic-origin (common in South Asia and elsewhere)", "Chinese (pinyin)"]
plt.rcParams.update({"font.size": 9, "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"]})
fig, ax = plt.subplots(figsize=(6.9, 4.0), dpi=300)
for y, gname in enumerate(order):
    d = out["groups"][gname]["0.8"]
    for key, ci, col, dy, lab in [("base_pct", "base_ci", "#1F3A5F", 0.12, "Standard spelling"),
                                  ("any_spelling_pct", "any_ci", "#B5523B", -0.12, "Any common spelling")]:
        ax.plot(d[ci], [y + dy] * 2, color=col, lw=1.4)
        ax.scatter(d[key], y + dy, color=col, s=34, zorder=3, label=lab if y == 0 else None)
ax.set_yticks(range(len(order)))
ax.set_yticklabels([gname.replace(" (common in South Asia and elsewhere)", "\n(common in South Asia & elsewhere)") for gname in order], fontsize=9)
ax.set_xlabel("Constructed names flagged against the OFAC SDN list\nat similarity 0.80 (%, with 95% Wilson interval)")
ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, fontsize=9, loc="lower right"); ax.set_xlim(0, 100)
fig.tight_layout(); fig.savefig(ROOT / "06_Figures" / "Fig09_OFAC_Name_Collisions.png", bbox_inches="tight", facecolor="white")
print("Figure 9 saved")
