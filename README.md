# Constitutional XAI for Cross-Border e-Rupee Payments: Code and Data

Replication package for the working paper:

> **A Constitutional AI Framework for Transparent, Traceable and Accountable Cross-Border e-Rupee Payments**
> Vivek, School of Commerce, Finance and Accountancy, CHRIST (Deemed to be University). Working paper, October 2026.

The paper argues that when artificial intelligence screens programmable central bank digital currency (CBDC) payments across borders, every automated hold or freeze must be **traced, explained, contestable and correctable** (the *4T-A principle*: Transparency, Traceability, Trust, Accountability). It implements this as a neuro-symbolic layer, in which a learned risk model proposes and a small machine-readable constitution decides, and evaluates it in three experiments.

## What is in this repository

| Folder | Contents |
|---|---|
| `scripts/` | All code that produces every number and figure in the paper |
| `10_Experiment_Results/` | Outputs: results tables (CSV/JSON), Shapley values, latencies and the hash-chained audit log |
| `06_Figures/` | Figures 1–10 as PNG |
| `02_Sources_PDF/ofac/` | Placeholder for the public OFAC SDN list (not redistributed; see below) |

## The three experiments

| # | Experiment | Data | Script(s) | Key result |
|---|---|---|---|---|
| 1 | Black-box screening vs constitutional layer | **Synthetic** 60,000 cross-border payments (seed 42) | `experiment_4ta.py`, `ablation_4ta.py`, `scenarios_figures_4ta.py` | Wrongful freezes of legitimate payments 129.5 → 46.1 per 10,000 (−64%); illicit payments frozen *or monitored* unchanged at 85.2%; name-group gap 41.0 → 4.6; 100% of freezes explained; median 36 ms per decision |
| 2 | Written constitution and a local language model (pilot) | 180 **fictional** payee and watch-list pairs | `ollama_constitution_test.py`, `exp2_analyse.py` | See `exp2_summary.json` |
| 3 | Name collisions on a real sanctions list | **Real** OFAC SDN list (7,509 individuals) and 80 constructed names per group | `ofac_name_collision_test.py` | At threshold 0.80: 11.2% of South Asian-transliterated names flagged vs 1.2% of Anglo names (Fisher p = 0.018); 26.2% flagged under some spelling (p < 0.001) |

The inter-coder reliability of the policy analysis (Cohen's κ = 0.60, weighted κ = 0.83) is in `10_Experiment_Results/intercoder_reliability.json`.

## How to reproduce

```bash
python -m pip install -r requirements.txt
cd scripts
python experiment_4ta.py          # Experiment 1: main run (writes results.json, audit_log.jsonl, ...)
python ablation_4ta.py            # Experiment 1: rule ablation and proportionality sweep
python scenarios_figures_4ta.py   # Scenarios S1–S5 and Figures 6–8
python fig01_timeline.py; python fig02_framework.py; python fig_design_diagrams.py   # Figures 1–5, 9
```

**Reproducibility check.** Running `experiment_4ta.py` and `ablation_4ta.py` from a fresh copy of this repository reproduced every reported number and an identical `ablation.csv`. It also reproduced the same final hash of the audit chain (`audit_chain_head` in `results.json`), which shows that all 409 logged decisions are identical.

**Experiment 3** needs the public SDN list. Download `SDN.CSV` from the US Treasury's [Sanctions List Service](https://sanctionslistservice.ofac.treas.gov/) into `02_Sources_PDF/ofac/`, then run `python ofac_name_collision_test.py`. Results depend on the list version; the paper used the version of 17 October 2026.

**Experiment 2** needs [Ollama](https://ollama.com) running locally with `qwen3:8b`. It takes several hours on a laptop CPU. No data leaves the machine.

## Important caveats

- Experiment 1 uses **synthetic** data. It demonstrates mechanism and feasibility, not field performance. All generator assumptions are stated in `DATA_ASSUMPTIONS` in `experiment_4ta.py`, including the assumption that transliterated names receive higher spurious name-match scores, which Experiment 3 tests on real data.
- Test names in Experiments 2 and 3 are constructed and refer to no real person. Name groups are defined by **naming convention**, not by the religion or ethnicity of any individual.
- Rule thresholds are design parameters for illustration. In practice they must be set and owned by an accountable authority.

## Licence

Code: MIT (see `LICENSE`). Results data and figures: CC BY 4.0 (see `LICENSE-DATA`). The OFAC SDN list is a US Government publication and is not redistributed here.

## How to cite

See `CITATION.cff`. A DOI will be added after archiving on Zenodo.
