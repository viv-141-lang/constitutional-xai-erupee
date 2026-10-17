# Constitutional XAI for Cross-Border e-Rupee Payments: Code and Data

Replication package for the working paper:

> **A Constitutional AI Framework for Transparent, Traceable and Accountable Cross-Border e-Rupee Payments**
> Vivek, School of Commerce, Finance and Accountancy, CHRIST (Deemed to be University). Working paper, October 2026.

The paper argues that when artificial intelligence screens programmable central bank digital currency (CBDC) payments, every automated hold or freeze must be **traced, explained, contestable and correctable** (the *4T-A principle*: Transparency, Traceability, Trust, Accountability). It implements this as a three-tier architecture: purpose-bound welfare rules at the domestic edge (Tier 1), a neuro-symbolic core in which a learned risk model proposes and a small machine-readable constitution decides (Tier 2), and cross-border attestations that share conclusions rather than personal data (Tier 3).

## What is in this repository

| Folder | Contents |
|---|---|
| `scripts/` | All code that produces every number and figure in the paper |
| `10_Experiment_Results/` | Outputs: results tables (CSV/JSON), Shapley values, latencies and the hash-chained audit log |
| `06_Figures/` | The paper's 16 figures as PNG (see the figure map below) |
| `02_Sources_PDF/ofac/` | Placeholder for the public OFAC SDN list (not redistributed; see below) |

## The experiments

| Study | Data | Script(s) | Key result |
|---|---|---|---|
| **Experiment 1**: black-box AML screening vs constitutional layer (Tier 2) | **Synthetic** cross-border payments (seed 42; robustness on seeds 1–20) | `experiment_4ta.py`, `ablation_4ta.py`, `robustness_4ta.py`, `scenarios_figures_4ta.py` | Of 409 payments the black box froze, 191 were legitimate; the constitution released 100 under monitoring, sent 23 for verification and held 68 with reasons. Wrongful freezes 129.5 → 46.1 per 10,000 with 85.2% of illicit payments still frozen or monitored. Across 20 seeds the name-group gap falls from 55.7 to 4.8. Median 36 ms per decision |
| **Experiment 2**: written constitution and a local language model (pilot) | 180 **fictional** payee and watch-list pairs | `ollama_constitution_test.py`, `exp2_analyse.py` | Under a plain instruction the model cleared all 50 name-only pairs; under the written constitution it asked for an identifier every time. Accuracy 72.2% → 100% |
| **Experiment 3**: purpose-bound welfare payments (Tier 1) | **Synthetic** 20,000 students and 20,000 farmers, four payment regimes on identical draws (seed 42; 20 seeds) | `welfare_4ta.py`, `fig_welfare.py` | The hybrid payee rule gives students about 4× and farmers 1.6× the payees of an approved list; the full design controls 95.5% of misuse (20-seed mean 93.1%) against 81.9% for an approved list |
| **Real-data name test** | **Real** OFAC SDN list (7,509 individuals) and 64 constructed names in each of six naming conventions | `ofac_name_collision_v2.py` | At similarity 0.80: 37.5% of Arabic-origin names flagged (95% CI 26.7–49.7) vs 1.6% of Anglo names (p < 0.001); Indic-origin names 4.7% (not significant, p = 0.62) |
| Scenarios S1–S5 | Constructed payments | `scenarios_figures_4ta.py` | Four walkthroughs plus a layering ring visible only on a shared monitoring network |

The inter-coder reliability of the policy analysis (Cohen's κ = 0.60, quadratic-weighted κ = 0.83) is in `10_Experiment_Results/intercoder_reliability.json`.

`ofac_name_collision_test.py` and `ofac_name_collision*.json/csv` without `_v2` are the earlier three-group version of the name test. They are kept for reference; the paper reports the six-group `_v2` version.

## Figure map

File names keep their working numbers; the paper numbers figures in order of appearance.

| Paper | File | Script |
|---|---|---|
| Figure 1 | `Fig01_Payments_Evolution_Timeline.png` | `fig01_timeline.py` |
| Figure 2 | `Fig02_Conceptual_Framework.png` | `fig02_framework.py` |
| Figure 3 | `Fig03_Research_Design.png` | `fig_design_diagrams.py` |
| Figure 4 | `Fig04_Data_Sources_Flow.png` | `fig_data_findings.py` |
| Figure 5 | `Fig05_Synthetic_Data_Profile.png` | `fig_data_findings.py` |
| Figure 6 | `Fig04_Friction_Matrix.png` | `fig_design_diagrams.py` |
| Figure 7 | `Fig05_Three_Tier_Architecture.png` | `fig_design_diagrams.py` |
| Figure 8 | `Fig08_Decision_Flow.png` | `fig_data_findings.py` |
| Figure 9 | `Fig09_Ablation_Robustness.png` | `fig_data_findings.py` |
| Figure 10 | `Fig06_Policy_Frontier_and_Bias.png` | `scenarios_figures_4ta.py` |
| Figure 11 | `Fig07_Shapley_and_Latency.png` | `scenarios_figures_4ta.py` |
| Figure 12 | `Fig12_Scenario_Paths.png` | `fig_data_findings.py` |
| Figure 13 | `Fig08_Shared_Monitoring_Network.png` | `scenarios_figures_4ta.py` |
| Figure 14 | `Fig09_OFAC_Name_Collisions.png` | `ofac_name_collision_v2.py` |
| Figure 15 | `Fig16_Welfare_Choice_Misuse.png` | `fig_welfare.py` |
| Figure 16 | `Fig10_Adoption_Pathway.png` | `fig_design_diagrams.py` |

## How to reproduce

```bash
python -m pip install -r requirements.txt
cd scripts
python experiment_4ta.py          # Experiment 1: main run (results.json, audit_log.jsonl, test_decisions.csv, ...)
python ablation_4ta.py            # Experiment 1: rule ablation and proportionality sweep
python robustness_4ta.py          # Experiment 1: 20 seeds x 2 name-bias settings, stronger baselines
python scenarios_figures_4ta.py   # Scenarios S1-S5 and Figures 10, 11, 13
python fig_data_findings.py       # Figures 4, 5, 8, 9, 12 (needs the four runs above)
python welfare_4ta.py             # Experiment 3: welfare regimes, seed 42 and 20 seeds
python fig_welfare.py             # Figure 15
python fig01_timeline.py; python fig02_framework.py; python fig_design_diagrams.py   # Figures 1-3, 6, 7, 16
```

Run the scripts in this order: later scripts read the CSV files written by earlier ones.

**Real-data name test** needs the public SDN list. Download `SDN.CSV` from the US Treasury's [Sanctions List Service](https://sanctionslistservice.ofac.treas.gov/) into `02_Sources_PDF/ofac/`, then run `python ofac_name_collision_v2.py`. Results depend on the list version; the paper used the version of 17 October 2026.

**Experiment 2** needs [Ollama](https://ollama.com) running locally with `qwen3:8b`. Run `python ollama_constitution_test.py`, then `python exp2_analyse.py`. It takes several hours on a laptop CPU at temperature 0. No data leaves the machine.

**Reproducibility check.** Every script fixes its random seeds. The final hash of the audit chain (`audit_chain_head` in `results.json`) fingerprints all 409 logged decisions of Experiment 1, so a rerun can be compared with the published results by that single value.

## Important caveats

- Experiments 1 and 3 use **synthetic** data. They demonstrate mechanism and feasibility, not field performance. Generator assumptions are stated in `DATA_ASSUMPTIONS` in `experiment_4ta.py` and in `ASSUME` in `welfare_4ta.py` (also written to `welfare_assumptions.json`). In Experiment 3, detection, audit and resolution rates are assumptions; tamper detection is measured by actually editing the hash chain.
- Test names in Experiment 2 and the name test are constructed and refer to no real person. Name groups are defined by **naming convention**, not by the religion or ethnicity of any individual.
- Rule thresholds are design parameters for illustration. In practice they must be set and owned by an accountable authority.

## Licence

Code: MIT (see `LICENSE`). Results data and figures: CC BY 4.0 (see `LICENSE-DATA`). The OFAC SDN list is a US Government publication and is not redistributed here.

## How to cite

See `CITATION.cff`. A DOI will be added after archiving on Zenodo.
