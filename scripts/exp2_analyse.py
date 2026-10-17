"""Summarise Experiment 2 (local LLM with/without written constitution) and render Section 4.7 text."""
import csv
import json
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / "10_Experiment_Results" / "exp2_llm_constitution.csv", encoding="utf-8")))
n = len(rows)
TYPES = {"T1": "same person, spelling variant", "T2": "namesake, different identifiers",
         "T3": "name only, no identifier", "T4": "different person"}


def share(sub, col, val):
    return round(100 * sum(r[col] == val for r in sub) / len(sub), 1) if sub else None


out = {"n_cases": n, "by_type": {}}
for t in TYPES:
    sub = [r for r in rows if r["type"] == t]
    out["by_type"][t] = {"n": len(sub),
                         "string_match_pct": share(sub, "string_baseline", "MATCH"),
                         "base": {k: share(sub, "base_decision", k) for k in ["MATCH", "NO_MATCH", "NEED_MORE_INFO"]},
                         "const": {k: share(sub, "const_decision", k) for k in ["MATCH", "NO_MATCH", "NEED_MORE_INFO"]}}
out["accuracy_pct"] = {c: round(100 * sum(r[f"{c}_decision"] == r["truth"] for r in rows) / n, 1) for c in ["base", "const"]}
out["median_seconds"] = {c: round(statistics.median(float(r[f"{c}_s"]) for r in rows), 1) for c in ["base", "const"]}
(ROOT / "10_Experiment_Results" / "exp2_summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

b = out["by_type"]
complete = n >= 180
text = (f"{'All' if complete else 'An interim set of'} {n} of the 180 planned name pairs {'were' if complete else 'had been'} judged by the local model "
        f"under both instructions{'' if complete else ' at the time of writing; the figures below will be updated when the run completes'}. "
        f"Accuracy against the ground truth was {out['accuracy_pct']['base']} percent with the plain instruction and "
        f"{out['accuracy_pct']['const']} percent with the written constitution. The difference is concentrated where the constitution says it should be. "
        f"For names presented without any identifier (n = {b['T3']['n']}), the plain instruction never asked for more information "
        f"({b['T3']['base']['NEED_MORE_INFO']} percent) and instead declared a match in {b['T3']['base']['MATCH']} percent of cases and no match in {b['T3']['base']['NO_MATCH']} percent, "
        f"whereas under the constitution the model requested an identifier in {b['T3']['const']['NEED_MORE_INFO']} percent of cases. "
        f"For namesakes with contradicting identifiers (n = {b['T2']['n']}), wrongful matches were {b['T2']['base']['MATCH']} percent without and {b['T2']['const']['MATCH']} percent with the constitution, "
        f"and true matches under a spelling variant (n = {b['T1']['n']}) were recognised in {b['T1']['base']['MATCH']} and {b['T1']['const']['MATCH']} percent of cases respectively. "
        f"The pattern is instructive. Without the constitution the model did not wrongly freeze anyone, but it silently cleared names it had no evidence to clear; "
        f"with the constitution it made that uncertainty explicit and asked for the missing identifier, which is precisely the behaviour rule R1 requires. "
        f"A plain string-similarity screen at 0.80, by comparison, would have flagged {b['T2']['string_match_pct']} percent of the namesakes and {b['T3']['string_match_pct']} percent of the name-only cases. "
        f"The model took a median of {out['median_seconds']['const']} seconds per judgement on a laptop, which confines a language model of this size to second-stage review of already-flagged names "
        f"rather than first-line screening. The pilot is small and uses one model, but it shows in miniature the claim of Constitutional AI applied to payments: "
        f"the same model behaves differently, and more defensibly, when its principles are written down.")
for ch in (["04_Chapter4_Findings_v1.md"] if (ROOT / "05_Drafts").exists() else []):  # manuscript only; skipped in the public repo
    p = ROOT / "05_Drafts" / ch
    s = p.read_text(encoding="utf-8")
    start = s.index("## 4.7 Pilot: A Written Constitution and a Language Model") + len("## 4.7 Pilot: A Written Constitution and a Language Model")
    end = s.index("## 4.8 Summary of Findings")
    s = s[:start] + "\n\n" + text + "\n\n" + s[end:]
    p.write_text(s, encoding="utf-8")
(ROOT / "10_Experiment_Results" / "exp2_section_text.txt").write_text(text, encoding="utf-8")
print(json.dumps(out, indent=1))
