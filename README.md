# Replication: Jayaraman & Wu (2020), Tables 1–3

Jayaraman, S. and J. S. Wu (2020). **Should I Stay or Should I Grow? Using Voluntary Disclosure to Elicit Market Feedback.** *Review of Financial Studies* 33(8): 3854–3888. doi:10.1093/rfs/hhz132

Prepared by Zhang Qi. Python (pandas, numpy, scipy); an optional Stata script cross-checks the regressions.

**Final report:** [`output/replication_report.html`](output/replication_report.html) (Markdown: [`output/replication_report.md`](output/replication_report.md)). Data pulled from WRDS on 9–10 November 2026.

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

* **Tables 1 and 2 replicate.** The sample is within 7.3% of the paper's, and all eight CAR coefficients in Table 2 are within one of the paper's standard errors. Placebo reactions, the fixed-effect robustness checks of footnote 19, and the figures quoted in the text (for example the 86-day median distance to sales forecasts) match.
* **Table 3 does not replicate.** The market reaction predicts capex revisions whether or not bid-ask spreads rise. This holds under every alternative specification tried (`output/t3_sensitivity.md`). Among forecasts not issued with an earnings announcement the pattern points in the paper's direction (2.180** vs 0.709), but the difference is not significant (p = 0.139).
* **Persistent differences.** Some differences remain under every specification and point to the data vintage rather than to the code: mean CAR is +0.32% (paper −0.15%), mean CAPEX_ADJ is 3.9% (7.4%), and ranges are 42.6% of forecasts (34.5%).

The report's §12 discusses these results; `REPLICATION_NOTES.md` documents every implementation choice and the evidence behind it.

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
python report.py             # rebuild the report with the sensitivity tables

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
| `report.py`, `docs/calibration.md`, `docs/discussion.md` | Final report; the two Markdown files hold its editable text |
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

WRDS data are licensed: `data/` is excluded from version control and nothing in this repository contains firm-level data. The files in `output/` hold aggregate results only.

## Notes

* The paper's numbers in `paper_targets.py` come from the May 2019 working paper, the only openly available full text; they should be checked against the published version.
* Exact equality is not expected: I/B/E/S Guidance, Compustat and CRSP have been revised since 2019, and the paper leaves 37 implementation choices unstated. Choices were calibrated on sample characteristics before reading results, and the analysis was stopped there rather than searching over specifications.
