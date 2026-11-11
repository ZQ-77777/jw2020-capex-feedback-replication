"""
Why does Table 3 not replicate?  Pre-specified tests (see docs/t3_preregistration.md).

    python diagnose_gap.py      # first: picks the sample variant closest to the paper (no regressions)
    python t3_diagnostics.py    # -> output/t3_diagnostics.md / .csv

Every test below was written down, with what each explanation predicts, BEFORE it was run.
All results are reported whatever they show; the main specification is not changed.

  A  How far is our difference from the paper's?   CI of (Higher - Lower); test against 1.501
  B  Continuous spread change                       CAR x dSPREAD in one pooled regression
  C  Extreme terciles of the spread change          drop the middle third (less misclassification)
  D  The paper's own robustness samples             post-2008 (fn 24); point + range only, and
                                                    CAPEX_ADJ relative to the range midpoint (fn 18)
  E  Sample variant closest to the paper            chosen by diagnose_gap.py on sample moments
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

import config as C
import utils as U
from diagnose_gap import load_variant, refresh
from hdfe import hdfe_ols

FE = ["gvkey", "YQ"]
CTRL8 = ["SIZE", "LAG_CAPX", "SURP", "EA_DUM", "MKTRET_z", "CAR_PRE_z"]
PAPER_DIFF, PAPER_P = 1.206 - (-0.295), 0.019
PAPER_LO = (-0.295, 0.372)


def stars(p):
    return "***" if p < .01 else "**" if p < .05 else "*" if p < .10 else ""


def diff_est(d: pd.DataFrame, X: list[str], group: str, var: str = "CAR_z", y: str = "CAPEX_ADJ",
             paper_diff: float = PAPER_DIFF) -> dict:
    """Fully interacted pooled model (= two split regressions, joint clustered covariance, like suest)."""
    d = d.dropna(subset=[group, y, *X]).copy()
    d[group] = d[group].astype(int)
    cols = []
    for g in (0, 1):
        ind = (d[group] == g).astype(float)
        for x in X:
            d[f"{x}__g{g}"] = pd.to_numeric(d[x], errors="coerce") * ind
            cols.append(f"{x}__g{g}")
    fe_i = []
    for f in FE:
        d[f + "__x"] = d[f].astype(str) + "|" + d[group].astype(str)
        fe_i.append(f + "__x")
    r = hdfe_ols(d, y, cols, fe_i, "IND")
    a, b = f"{var}__g1", f"{var}__g0"
    diff = r.coef[a] - r.coef[b]
    se = float(np.sqrt(r.vcov.loc[a, a] + r.vcov.loc[b, b] - 2 * r.vcov.loc[a, b]))
    dfree = r.n_clusters - 1
    tcrit = stats.t.ppf(0.975, dfree)
    return dict(N_lo=int((d[group] == 0).sum()), N_hi=int((d[group] == 1).sum()),
                b_lo=r.coef[b], se_lo=float(np.sqrt(r.vcov.loc[b, b])),
                b_hi=r.coef[a], se_hi=float(np.sqrt(r.vcov.loc[a, a])),
                diff=diff, se_diff=se, p_diff=float(2 * stats.t.sf(abs(diff / se), dfree)),
                ci_lo=diff - tcrit * se, ci_hi=diff + tcrit * se,
                p_vs_paper=float(2 * stats.t.sf(abs((diff - paper_diff) / se), dfree)), G=int(r.n_clusters),
                paper_diff=paper_diff)


def fmt(r: dict) -> dict:
    return {"N (lo/hi)": f"{r['N_lo']:,} / {r['N_hi']:,}",
            "CAR lower": f"{r['b_lo']:.3f}{stars(2 * stats.t.sf(abs(r['b_lo'] / r['se_lo']), r['G'] - 1))} ({r['se_lo']:.3f})",
            "CAR higher": f"{r['b_hi']:.3f}{stars(2 * stats.t.sf(abs(r['b_hi'] / r['se_hi']), r['G'] - 1))} ({r['se_hi']:.3f})",
            "diff (SE)": f"{r['diff']:.3f} ({r['se_diff']:.3f})", "p diff": round(r["p_diff"], 3),
            "95% CI of diff": f"[{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]",
            "paper diff": r["paper_diff"],
            "paper diff in CI?": "yes" if r["ci_lo"] <= r["paper_diff"] <= r["ci_hi"] else "no",
            "p (diff = paper)": round(r["p_vs_paper"], 3)}


def spread_change(c: pd.DataFrame) -> pd.Series:
    """Log change in the relative spread, event [-2,2] vs pre-event [-10,-3]; winsorised and z-scored."""
    ok = (c["SPREAD_PRE"] > 0) & (c["SPREAD_EVT"] > 0)
    x = np.log(c["SPREAD_EVT"].where(ok) / c["SPREAD_PRE"].where(ok))
    return U.zscore(U.winsorize(x))


def midpoint_adj(c: pd.DataFrame) -> pd.Series:
    """fn 18 robustness: CAPEX_ADJ relative to the midpoint of a range (no zero band inside the range)."""
    act, fore = c["CAPEX_ACT_raw"], c["CAPEX_FORE_raw"]       # CAPEX_FORE = midpoint for ranges (D7)
    return U.winsorize((act - fore) / fore.where(fore > 0) * 100.0)


def main():
    c = U.load("capex_sample")
    X = ["CAR_z", *CTRL8]
    rows, md = {}, ["# Table 3 diagnostics\n",
                    "Pre-specified in docs/t3_preregistration.md. lo = spreads do not rise, hi = spreads rise. "
                    "Controls, fixed effects (firm, year-quarter) and industry clustering as in Table 2 (8).\n"]

    # A: main specification, with the CI of the difference
    a = diff_est(c, X, "HIGHER_SPREAD")
    rows["A. main specification"] = fmt(a)
    se_paper = PAPER_DIFF / stats.norm.isf(PAPER_P / 2)
    z = (PAPER_DIFF - a["diff"]) / np.sqrt(se_paper ** 2 + a["se_diff"] ** 2)
    zlo = (a["b_lo"] - PAPER_LO[0]) / np.sqrt(PAPER_LO[1] ** 2 + a["se_lo"] ** 2)
    pos = diff_est(c, ["CAR_POS_z", "CAR_NEG_z", *CTRL8], "HIGHER_SPREAD", "CAR_POS_z",
                   paper_diff=0.893 - (-0.203))          # paper Table 3 (4) - (3)
    rows["A2. CAR_POS (positive reactions)"] = fmt(pos)

    # B: continuous spread change, pooled
    d = c.copy()
    d["DSPR_z"] = spread_change(d)
    d["CARxDSPR"] = d["CAR_z"] * d["DSPR_z"]
    rb = hdfe_ols(d, "CAPEX_ADJ", ["CAR_z", "CARxDSPR", "DSPR_z", *CTRL8], FE, "IND")
    pb = float(2 * stats.t.sf(abs(rb.coef["CARxDSPR"] / rb.se["CARxDSPR"]), rb.n_clusters - 1))

    # C: extreme terciles of the spread change
    q1, q2 = d["DSPR_z"].quantile([1 / 3, 2 / 3])
    d["TOP_TERC"] = np.where(d["DSPR_z"] <= q1, 0.0, np.where(d["DSPR_z"] >= q2, 1.0, np.nan))
    rows["C. bottom vs top tercile of spread change"] = fmt(diff_est(d, X, "TOP_TERC"))

    # D: the paper's own robustness samples
    rows["D1. post-2008 (fn 24)"] = fmt(diff_est(refresh(c[c["YEAR"] >= 2009]), X, "HIGHER_SPREAD"))
    rows["D2. point + range only (fn 18)"] = fmt(diff_est(refresh(c[c["FTYPE"] != "other"]), X, "HIGHER_SPREAD"))
    m = c.copy()
    m["CAPEX_ADJ"] = midpoint_adj(m)
    rows["D3. CAPEX_ADJ vs range midpoint (fn 18)"] = fmt(diff_est(m, X, "HIGHER_SPREAD"))

    # E: the sample variant chosen on sample moments
    ch = C.OUT / "sample_gap_choice.json"
    if ch.exists():
        v = json.loads(ch.read_text())["variant"]
        if v != "main":
            rows[f"E. closest sample variant: {v}"] = fmt(diff_est(load_variant(v), X, "HIGHER_SPREAD"))
        else:
            md.append("\nE: diagnose_gap.py found no variant closer to the paper than the main sample.\n")
    else:
        md.append("\nE: run diagnose_gap.py first.\n")

    t = pd.DataFrame(rows).T
    md.append("\n## Split tests (A, C, D, E)\n\n" + t.to_markdown())
    md.append(f"\n\nPaper: lower −0.295 (0.372), higher 1.206** (0.497), difference 1.501, p = 0.019 "
              f"(implied SE of the difference ≈ {se_paper:.3f}).\n")
    md.append("\n## A. How far apart are the two results?\n")
    md.append(f"- Our difference {a['diff']:.3f}, 95% CI [{a['ci_lo']:.2f}, {a['ci_hi']:.2f}] "
              f"({a['G']} industry clusters). The paper's 1.501 is {'inside' if a['ci_lo'] <= PAPER_DIFF <= a['ci_hi'] else 'outside'} it "
              f"(p = {a['p_vs_paper']:.3f} for H0: our difference = 1.501).\n")
    md.append(f"- Taking the paper's own uncertainty into account (two estimates treated as independent), "
              f"the gap between the two differences is {PAPER_DIFF - a['diff']:.3f}, z = {z:.2f}, "
              f"p = {2 * stats.norm.sf(abs(z)):.3f}. The samples overlap heavily, so this p-value is conservative.\n")
    md.append(f"- Lower-spread group: ours {a['b_lo']:.3f} vs the paper's −0.295; z = {zlo:.2f}, "
              f"p = {2 * stats.norm.sf(abs(zlo)):.3f} (the paper's prediction is no effect in this group).\n")
    md.append("\n## B. Continuous spread change (pooled)\n")
    md.append(f"CAPEX_ADJ on CAR, CAR × ΔSPREAD, ΔSPREAD and controls; ΔSPREAD = log(event/pre-event spread), "
              f"z-scored. N = {rb.nobs:,}.\n\n"
              f"| | coef | SE | p |\n|---|---|---|---|\n"
              f"| CAR | {rb.coef['CAR_z']:.3f} | {rb.se['CAR_z']:.3f} | "
              f"{2 * stats.t.sf(abs(rb.coef['CAR_z'] / rb.se['CAR_z']), rb.n_clusters - 1):.3f} |\n"
              f"| CAR × ΔSPREAD | {rb.coef['CARxDSPR']:.3f} | {rb.se['CARxDSPR']:.3f} | {pb:.3f} |\n"
              f"| ΔSPREAD | {rb.coef['DSPR_z']:.3f} | {rb.se['DSPR_z']:.3f} | "
              f"{2 * stats.t.sf(abs(rb.coef['DSPR_z'] / rb.se['DSPR_z']), rb.n_clusters - 1):.3f} |\n")
    md.append("\nHow to read each test against the explanations: docs/t3_preregistration.md.\n")
    t.to_csv(C.OUT / "t3_diagnostics.csv")
    (C.OUT / "t3_diagnostics.md").write_text("\n".join(md), encoding="utf-8")
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(t.to_string())
    print(f"\nB: CAR x dSPREAD = {rb.coef['CARxDSPR']:.3f} (SE {rb.se['CARxDSPR']:.3f}, p {pb:.3f})")
    print(f"saved {C.OUT / 't3_diagnostics.md'}")


if __name__ == "__main__":
    main()
