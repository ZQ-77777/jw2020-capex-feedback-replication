# Replication: Jayaraman & Wu (2020), Tables 1–3

Jayaraman, S. and J. S. Wu (2020). **Should I Stay or Should I Grow? Using Voluntary Disclosure to Elicit Market Feedback.** *Review of Financial Studies* 33(8): 3854–3888. doi:10.1093/rfs/hhz132

Prepared by Zhang Qi. Python (pandas, numpy, scipy); an optional Stata script cross-checks the regressions.

**Final report:** [`docs/report/JW2020_Replication_Report_EN.pdf`](docs/report/JW2020_Replication_Report_EN.pdf) (English) and [`docs/report/JW2020_Replication_Report_ZH.pdf`](docs/report/JW2020_Replication_Report_ZH.pdf) (Chinese). Data pulled from WRDS on 9–10 November 2026. All benchmark numbers were checked against the published version.

## Results at a glance

| | Paper | This replication |
|---|---|---|
| Final sample | 17,577 forecasts, 1,790 firms | 18,866 forecasts, 2,180 firms (+7.3%) |
| Table 2 (1): CAR | 1.193*** | 1.193*** |
| Table 2 (4): CAR, firm and year-quarter FE | 0.975*** | 1.017*** |
| Table 2 (8): CAR, all controls | 0.849*** | 0.988*** |
| Table 2 placebos (SF_CAR, MKTRET, CAR_PRE) | insignificant | insignificant |
| Table 3: CAR, spreads do not rise / rise | −0.295 / 1.206** | 0.674** / 0.880** |
| Table 3: p-value of the difference | 0.019 | 0.672 |

* **Tables 1 and 2 replicate.** The sample is within 7.3% of the paper's, and all eight CAR coefficients in Table 2 are within one of the paper's standard errors. Placebo reactions, the fixed-effect robustness checks of footnote 20, and the figures quoted in the text (for example the 86-day median distance to sales forecasts) match.
* **Table 3 does not replicate.** The market reaction predicts capex revisions whether or not bid-ask spreads rise: the difference is 0.21 with a 95% interval of [−0.76, 1.18], which excludes the paper's 1.50 (p = 0.010).
* **Pre-registered diagnostics** (`docs/t3_preregistration.md`, `t3_diagnostics.py`): a noisy spread measure is rejected (continuous and extreme-tercile tests show no stronger effect); I/B/E/S backfilling is ruled out (3 of 326,000 records activated after the paper's submission); firm-level filters do not restore the pattern. The paper's pattern appears only partly, from 2009 on (difference 1.08, p = 0.058) and under the definitions closest to the paper (0.69, p = 0.222).
* **Where the remaining gaps come from** (`annual_waterfall.py`, `diagnose_definitions.py`, `docs/definitions_preregistration.md`): the early-year sample gap arises at a step of the paper with no counterpart here, most likely its CRSP match (3,885 forecasts dropped vs 9). EA_DUM (0.662 vs 0.559), the share of open-ended forecasts (2.8% vs 10.2%) and mean CAR (+0.32% vs −0.15%) depend on forecast-level coding that the paper does not state and that current I/B/E/S codes cannot reproduce.
* **Reach of Table 3.** Appendix A of the report maps which later tests rely on the spread split: Table 5 E2a/E2b depend on it entirely, Table 5 C does not.

`REPLICATION_NOTES.md` documents every implementation choice and the evidence behind it.

## How to run

The step-by-step guide, including WRDS account setup and two-factor login, is in `WRDS_GUIDE.md` (Chinese).

```bash
pip install -r requirements.txt
python preflight.py          # environment, packages, both test suites, data status -> next command

# WRDS (needs I/B/E/S Guidance, CRSP, Compustat)
export WRDS_USERNAME=<account>          # Windows: setx WRDS_USERNAME "<account>"
python check_wrds.py         # permissions, column names, I/B/E/S coding   -> output/wrds_check.md
python pull_wrds.py          # 10 tables for Tables 1-3                  -> data/raw/ + _pull_log.csv

# calibration on sample characteristics only (no regressions)
python diagnose.py           # forecast types, units, EA and EPS concurrency
python calibrate_d9.py       # four definitions of an "earnings forecast" -> output/calibrate_d9.csv

# estimation and report
python run_all.py            # sample, Tables 1-3, report                  -> output/
python t3_sensitivity.py     # Table 3 under alternative settings          -> output/t3_sensitivity.md
python report.py             # rebuild the HTML report with the sensitivity tables

# diagnostics (sample characteristics first; each regression pre-registered in docs/)
python diagnose_gap.py       # where the sample gap comes from               -> output/sample_gap.md
python t3_diagnostics.py     # pre-registered Table 3 diagnostics            -> output/t3_diagnostics.md
python annual_waterfall.py   # annual sample waterfall and retention rates   -> output/annual_waterfall.md
python diagnose_definitions.py --pull   # forecast-level definitions (two small extra WRDS pulls) -> output/definitions.md

# optional: Stata cross-check of Tables 2-3 on the identical rows
cd stata && stata -b do tables_2_3.do && cd ..
python compare_stata.py      # -> output/stata_crosscheck.md
```

Without WRDS access, `python tests/test_hdfe.py` and `python tests/run_synthetic.py` verify the estimator and the whole pipeline on synthetic data with a planted effect (about 40 seconds).

## Files

| File | Role |
|---|---|
| `config.py` | Every implementation choice as a switch, tagged with its decision ID (D1–D37) |
| `preflight.py` | Readiness check and next command |
| `check_wrds.py`, `pull_wrds.py` | WRDS access check; download (logs date and row count of each table) |
| `diagnose.py`, `calibrate_d9.py` | Calibration of the I/B/E/S coding switches on sample characteristics |
| `build_capex_sample.py` | Sample construction and all variables |
| `tables.py` | Tables 1–3, figures quoted in the text, robustness, winsorisation check, Stata export |
| `hdfe.py` | Fixed-effects OLS with clustered standard errors and difference tests (Stata `reghdfe` conventions) |
| `t3_sensitivity.py` | Table 3 under pre-specified alternative settings |
| `diagnose_gap.py` | Sample-gap diagnostics: waterfall alignment, data vintage (ACTDATS), firm-level filters |
| `t3_diagnostics.py` | Pre-registered Table 3 diagnostics (continuous, terciles, robustness samples, closest sample) |
| `annual_waterfall.py` | Annual sample waterfall with retention rates R(t,k) and ratios to the paper |
| `diagnose_definitions.py` | Forecast-level definitions (forecast type, EA_DUM, earnings forecast) and one Table 3 run |
| `docs/t3_preregistration.md`, `docs/definitions_preregistration.md` | Pre-registrations written before the diagnostics were run |
| `docs/report/` | Final reports (PDF, Chinese and English) |
| `report.py`, `docs/calibration.md`, `docs/discussion.md` | HTML report from `run_all.py` (superseded by `docs/report/`); the two Markdown files hold its text |
| `stata/tables_2_3.do`, `compare_stata.py` | Stata re-estimation and cell-by-cell comparison |
| `paper_targets.py` | Every number reported in the paper, for comparison |
| `utils.py` | Links, event windows, data loading (normalises WRDS pyarrow types) |
| `tests/` | Estimator test, synthetic data generator, end-to-end test |
| `REPLICATION_NOTES.md` | Decision log D1–D37, calibration evidence, results summary (Chinese) |
| `WRDS_GUIDE.md` | WRDS account, download, calibration and troubleshooting (Chinese) |
| `GUIDE.html` | Study guide with a cell-by-cell explanation of Tables 1–3 (Chinese) |
| `docs/REPORT_PREDATA_en.html`, `docs/REPORT_PREDATA_zh.html` | Pre-data report (archived, 7 November 2026) |
| `build_mf_pressure.py`, `build_spread_panel.py`, `build_panel.py` | Tables 4–6 (run with `JW_SCOPE=all`; outside this replication) |

## Data

The ten WRDS tables used for Tables 1–3:

| WRDS table | Used for |
|---|---|
| `ibes.det_guidance` | Capex (CPX), sales (SAL) and EPS guidance |
| `ibes.det_guidance` (other measures) → `guidance_earn` | GPS, NET, PRE, EBITDA, EBS, OPR and FFO guidance dates, for the definition of an earnings forecast (D9) |
| `wrdsapps_link_crsp_ibes.ibcrsphist`, `crsp.ccmxpf_lnkhist` | I/B/E/S ticker → PERMNO → GVKEY |
| `comp.funda`, `comp.fundq`, `comp.company` | Actual capex, SIZE, LAG_CAPX, SURP, earnings announcement dates, industry |
| `crsp.dsf` (event windows only), `crsp.dsi`, `crsp.msenames` | CAR, S&P 500 return, bid-ask spreads |
| `ibes.det_guidance` (all other measures) → `guidance_other`; `ibes.actu_epsus` → `ibes_ea` | Diagnostics only: alternative definitions of an earnings forecast and of EA_DUM |

WRDS data are licensed: `data/` is excluded from version control and nothing in this repository contains firm-level data. The files in `output/` hold aggregate results only.

## Notes

* The numbers in `paper_targets.py` were checked item by item against the published version (RFS 33(8)); Tables 1–3 are identical. The Internet Appendix has not been checked.
* Exact equality is not expected: I/B/E/S Guidance, Compustat and CRSP have been revised since 2019, and the paper leaves 37 implementation choices unstated. Choices were calibrated on sample characteristics before reading results, and the analysis was stopped there rather than searching over specifications.
