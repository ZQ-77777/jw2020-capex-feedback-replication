"""
Where does the sample gap come from?  (sample characteristics only -- no regression is run here)

    python diagnose_gap.py            # -> output/sample_gap.md, output/sample_gap_choice.json

Our final sample is 18,866 forecasts / 2,180 firms; the paper's is 17,577 / 1,790.
Forecasts differ by -6.8% but firms by -17.9%: whatever the paper removed hit firms with
few forecasts much harder than the average firm.  This script tests candidate explanations
against that fingerprint and against the paper's Table 1 moments.

  [1] Waterfall alignment: in our pipeline the IBES->CRSP link happens at step 1, so the
      paper's 3,885-forecast loss at "matching to CRSP" has no counterpart in our step 2.
  [2] Where the gap sits in time: forecasts and first-time forecasters by year vs Table 1B.
  [3] Data vintage: I/B/E/S ACTDATS (activation date of each guidance record).  Records
      activated after the paper was submitted (21 Jul 2018) could not have been in its data.
      Caveat: if ACTDATS is reset when a record is revised, this also drops revised old records.
  [4] Unstated filters that are common in this literature, applied as row filters
      (row filters commute with every step of the build, so filtering the final sample
      gives the same rows as filtering at step 1):
        shrcd 10/11 (ordinary common shares) | exchcd 1-3 (NYSE/AMEX/NASDAQ) |
        >= 12 months of CRSP history (estimation-window requirement of event-study tools) |
        I/B/E/S-CRSP link score <= 1
  [5] Pre-specified choice: the variant whose sample moments are closest to the paper
      (distance D below) is written to output/sample_gap_choice.json.  t3_diagnostics.py
      re-estimates Table 3 on it ONCE, whatever the result.

Distance (fixed before looking at any regression):
  D = |N/17577 - 1| + |firms/1790 - 1| + |EA_DUM - 0.559| + |range share - 0.345|
      + |other share - 0.102| + |mean CAPEX_ADJ - 7.421| / 7.421 + |mean CAR - (-0.148)|
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import build_capex_sample as B
import config as C
import paper_targets as P
import utils as U

PAPER_SUBMITTED = pd.Timestamp("2018-07-21")      # "Received July 21, 2018"
PAPER = dict(N=17577, firms=1790, EA_DUM=0.559, CAR_mean=-0.148, ADJ_mean=7.421, ADJ_median=0.0,
             point=0.553, range=0.3448, other=0.1022, higher_spread=9570 / 17340)
MOMENTS = ["N", "firms", "EA_DUM", "CAR_mean", "ADJ_mean", "ADJ_median", "range", "other", "higher_spread"]


# ============================================================================ helpers
def moments(c: pd.DataFrame) -> dict:
    ft = c["FTYPE"].value_counts(normalize=True)
    hs = pd.to_numeric(c.get("HIGHER_SPREAD"), errors="coerce")
    return dict(N=len(c), firms=c["gvkey"].nunique(), EA_DUM=c["EA_DUM"].mean(),
                CAR_mean=pd.to_numeric(c["CAR"], errors="coerce").mean(),
                ADJ_mean=c["CAPEX_ADJ"].mean(), ADJ_median=c["CAPEX_ADJ"].median(),
                point=ft.get("point", 0.0), range=ft.get("range", 0.0), other=ft.get("other", 0.0),
                higher_spread=hs.mean())


def distance(m: dict) -> float:
    return (abs(m["N"] / PAPER["N"] - 1) + abs(m["firms"] / PAPER["firms"] - 1)
            + abs(m["EA_DUM"] - PAPER["EA_DUM"]) + abs(m["range"] - PAPER["range"])
            + abs(m["other"] - PAPER["other"]) + abs(m["ADJ_mean"] - PAPER["ADJ_mean"]) / PAPER["ADJ_mean"]
            + abs(m["CAR_mean"] - PAPER["CAR_mean"]))


def toward_paper(m: dict, base: dict) -> str:
    keys = ["N", "firms", "EA_DUM", "CAR_mean", "ADJ_mean", "range", "other"]
    k = sum(abs(m[x] - PAPER[x]) < abs(base[x] - PAPER[x]) for x in keys)
    return f"{k}/{len(keys)}"


def attach_crsp_info(c: pd.DataFrame) -> pd.DataFrame:
    """shrcd / exchcd valid at the announcement date, and months of CRSP history before it."""
    n = U.lower_cols(U.load("msenames", C.RAW))
    n["namedt"], n["nameendt"] = U.to_dt(n["namedt"]), U.to_dt(n["nameendt"]).fillna(pd.Timestamp("2099-12-31"))
    n["permno"] = pd.to_numeric(n["permno"]).astype("Int64")
    c = c.copy()
    c["permno"] = pd.to_numeric(c["permno"]).astype("Int64")
    c["_rid"] = np.arange(len(c))
    m = c[["_rid", "permno", "anndats"]].merge(n[["permno", "namedt", "nameendt", "shrcd", "exchcd"]], on="permno")
    m = m[(m["anndats"] >= m["namedt"]) & (m["anndats"] <= m["nameendt"])].drop_duplicates("_rid")
    c = c.merge(m[["_rid", "shrcd", "exchcd"]], on="_rid", how="left")
    first = n.groupby("permno")["namedt"].min()
    c["crsp_months"] = (c["anndats"] - c["permno"].map(first)).dt.days / 30.44
    c["shrcd"] = pd.to_numeric(c["shrcd"], errors="coerce")
    c["exchcd"] = pd.to_numeric(c["exchcd"], errors="coerce")
    return c.drop(columns="_rid")


FILTERS = {
    "shrcd 10/11": lambda c: c["shrcd"].isin([10, 11]),
    "exchcd 1-3": lambda c: c["exchcd"].isin([1, 2, 3]),
    "CRSP history >= 12m": lambda c: c["crsp_months"] >= 12,
    "IBES link score <= 1": lambda c: pd.to_numeric(c.get("score"), errors="coerce") <= 1,
}
COMBOS = {
    "shrcd 10/11 + exchcd 1-3": ["shrcd 10/11", "exchcd 1-3"],
    "shrcd + exchcd + history": ["shrcd 10/11", "exchcd 1-3", "CRSP history >= 12m"],
}


def row_mask(c: pd.DataFrame, name: str) -> pd.Series:
    parts = COMBOS.get(name, [name])
    m = pd.Series(True, index=c.index)
    for p in parts:
        m &= FILTERS[p](c).fillna(False).astype(bool)
    return m


def refresh(c: pd.DataFrame) -> pd.DataFrame:
    """Re-winsorise from the raw columns and re-standardise on THIS sample (a new full sample, D14/D27)."""
    c = c.copy()
    for v in C.WINSOR_VARS + (["CAPEX_FORE", "CAPEX_ACT", "LAG_CAPX_MIL", "SIZE"] if C.WINSOR_LEVELS else []):
        if v + "_raw" in c:
            c[v] = U.winsorize(c[v + "_raw"])
    c["CAR_POS"], c["CAR_NEG"] = c["CAR"].clip(lower=0), c["CAR"].clip(upper=0)
    for v in ("CAR", "CAR_POS", "CAR_NEG", "MKTRET", "CAR_PRE", "SF_CAR"):
        if v in c:
            c[v + "_z"] = U.zscore(c[v])
    return c


def load_variant(name: str) -> pd.DataFrame:
    """Used by t3_diagnostics.py: the main sample, a row-filtered variant, or the point-in-time rebuild."""
    if name in ("main", None):
        return U.load("capex_sample")
    if name.startswith("PIT"):
        c = U.load("capex_sample_pit")
        extra = name.split("+", 1)[1].strip() if "+" in name else ""
        if not extra:
            return c
        c = attach_crsp_info(c)
        return refresh(c[row_mask(c, extra)])
    c = attach_crsp_info(U.load("capex_sample"))
    return refresh(c[row_mask(c, name)])


# ============================================================================ point-in-time rebuild
def rebuild_point_in_time(cutoff: pd.Timestamp) -> pd.DataFrame | None:
    """Rebuild the sample using only guidance records activated on or before `cutoff`.
    The main sample files are backed up and restored, so data/interim keeps the main specification."""
    raw = U.lower_cols(U.load("guidance", C.RAW).head(5))
    if "actdats" not in raw:
        print("[gap] ibes.det_guidance has no ACTDATS column in data/raw -> point-in-time test skipped")
        return None
    orig = B.clean_guidance

    def clean_pit():
        g = orig()
        a = U.to_dt(g["actdats"])
        print(f"[gap] PIT: dropping {(a > cutoff).sum():,} of {len(g):,} guidance records activated after {cutoff.date()}")
        return g[a.isna() | (a <= cutoff)]

    tmp = Path(tempfile.mkdtemp())
    backups = [p for p in (C.INTERIM / "capex_sample.parquet", C.INTERIM / "capex_sample.pkl",
                           C.OUT / "sample_waterfall.csv") if p.exists()]
    for p in backups:
        shutil.copy2(p, tmp / p.name)
    try:
        B.clean_guidance = clean_pit
        c = B.build()
        wf = pd.read_csv(C.OUT / "sample_waterfall.csv")
        U.save(c, "capex_sample_pit")
        wf.to_csv(C.OUT / "sample_waterfall_pit.csv", index=False)
    finally:
        B.clean_guidance = orig
        for p in (C.INTERIM / "capex_sample.parquet", C.INTERIM / "capex_sample.pkl"):
            p.unlink(missing_ok=True)
        for p in backups:
            shutil.copy2(tmp / p.name, p)
        shutil.rmtree(tmp, ignore_errors=True)
    return c


# ============================================================================ main
def main():
    md = ["# Sample gap diagnostics\n",
          "Sample characteristics only; no regression is run. Paper: 17,577 forecasts, 1,790 firms.\n"]
    c = attach_crsp_info(U.load("capex_sample"))
    base = moments(c)

    # [1] waterfall alignment
    wf = pd.read_csv(C.OUT / "sample_waterfall.csv")
    g = B.classify(B.annual_forecasts(B.clean_guidance(), C.MEASURE_CAPEX))
    g = g[(g["anndats"] >= C.FCST_FIRST) & (g["anndats"] <= C.FCST_LAST)].copy()
    g["qid"] = U.qid(g["anndats"]).astype(int)
    g = g.sort_values(["ticker", "qid", "anndats", "anntims"]).drop_duplicates(["ticker", "qid"], keep="first")
    g = U.link_ibes_permno(g, U.load("ibcrsphist", C.RAW), "anndats")
    n0, n_perm = len(g), int(g["permno"].notna().sum())
    g = U.link_permno_gvkey(g, U.load("ccm", C.RAW), "anndats")
    n_gv = int(g["gvkey"].notna().sum())
    md.append("\n## [1] Waterfall alignment\n")
    md.append(f"After the firm-quarter collapse: {n0:,} forecasts. With an I/B/E/S->CRSP link: {n_perm:,} "
              f"(lost {n0 - n_perm:,}). With a CCM link to Compustat: {n_gv:,}. With actual capex: "
              f"{int(wf.loc[wf.step == 'w1_matched_compustat', 'ours'].iloc[0]):,}.\n\n"
              "Our step 1 already requires a CRSP PERMNO, so the paper's step-2 loss (40,785 -> 36,900) cannot "
              "be compared with ours (41,452 -> 41,443). The comparable count is the one AFTER the CRSP "
              f"requirement: ours {int(wf.loc[wf.step == 'w2_with_car', 'ours'].iloc[0]):,} vs the paper's 36,900.\n")
    md.append(wf.to_markdown(index=False))

    # [2] by year
    first = c.groupby("gvkey")["YEAR"].min()
    yr = pd.DataFrame({"ours": c.groupby("YEAR").size(), "ours_first": first.value_counts()}).fillna(0).astype(int)
    yr["paper"] = yr.index.map(lambda y: P.T1B.get(y, (np.nan, np.nan))[0])
    yr["paper_first"] = yr.index.map(lambda y: P.T1B.get(y, (np.nan, np.nan))[1])
    yr["gap"] = yr["ours"] - yr["paper"]
    yr["gap_first"] = yr["ours_first"] - yr["paper_first"]
    pre = yr.loc[yr.index <= 2009, "gap"].sum()
    md.append("\n## [2] Where the gap sits in time (Table 1 Panel B)\n")
    md.append(yr.to_markdown())
    md.append(f"\nNet gap 2003-2009: {pre:+,.0f}; 2010-2015: {yr.loc[yr.index >= 2010, 'gap'].sum():+,.0f}. "
              f"Extra first-time forecasters: {yr['gap_first'].sum():+,.0f} firms.\n")

    # [3] activation dates
    rows = {}
    md.append("\n## [3] Data vintage: I/B/E/S activation dates (ACTDATS)\n")
    if "actdats" in c:
        a = U.to_dt(c["actdats"])
        lag = (a - c["anndats"]).dt.days
        t = pd.DataFrame({"N": c.groupby("YEAR").size(),
                          "median lag (days)": lag.groupby(c["YEAR"]).median(),
                          "share lag > 365d": (lag > 365).groupby(c["YEAR"]).mean(),
                          "share activated after 21 Jul 2018": (a > PAPER_SUBMITTED).groupby(c["YEAR"]).mean()})
        md.append(t.to_markdown(floatfmt=".3f"))
        md.append(f"\nWhole sample: {(a > PAPER_SUBMITTED).mean():.1%} of final-sample forecasts were activated after "
                  "the paper was submitted. If this share is large and concentrated in early years, records were "
                  "back-filled after the authors drew their data.\n")
        pit = rebuild_point_in_time(PAPER_SUBMITTED)
        if pit is not None:
            pit = attach_crsp_info(pit)
            rows["PIT (actdats <= 2018-07-21)"] = moments(pit)
            for k in COMBOS:
                rows[f"PIT + {k}"] = moments(pit[row_mask(pit, k)])
            md.append("\nPoint-in-time waterfall:\n\n" + pd.read_csv(C.OUT / "sample_waterfall_pit.csv").to_markdown(index=False))
    else:
        md.append("No ACTDATS column in the downloaded guidance table: re-pull `ibes.det_guidance` with all columns.\n")

    # [4] row filters
    md.append("\n## [4] Candidate filters (row filters on the main sample)\n")
    sc = c.assign(shrcd=c["shrcd"].fillna(-1).astype(int)).groupby("shrcd").agg(
        forecasts=("gvkey", "size"), firms=("gvkey", "nunique"))
    md.append("Share codes in the final sample:\n\n" + sc.to_markdown())
    for k in list(FILTERS) + list(COMBOS):
        rows[k] = moments(c[row_mask(c, k)])

    # [5] comparison table + pre-specified choice
    tab = {"paper": PAPER, "main": base, **rows}
    out = pd.DataFrame(tab).T[MOMENTS]
    out["forecasts vs main"] = out["N"] / base["N"] - 1
    out["firms vs main"] = out["firms"] / base["firms"] - 1
    out.loc["paper", ["forecasts vs main", "firms vs main"]] = [PAPER["N"] / base["N"] - 1, PAPER["firms"] / base["firms"] - 1]
    out["D (distance)"] = [np.nan] + [distance(m) for m in list(tab.values())[1:]]
    out["moments toward paper"] = [""] + ["-"] + [toward_paper(m, base) for m in rows.values()]
    md.append("\n## [5] Variants vs the paper\n")
    md.append("Fingerprint to match: the paper row's 'forecasts vs main' and 'firms vs main' (on WRDS data: -6.8% and -17.9%).\n\n")
    md.append(out.to_markdown(floatfmt=".3f"))
    cand = out.iloc[1:]["D (distance)"]
    choice = cand.idxmin()
    md.append(f"\n**Pre-specified choice (smallest D): `{choice}`** (D = {cand.min():.3f}; main D = {cand['main']:.3f}). "
              "t3_diagnostics.py re-estimates Table 3 on this variant once and reports it whatever the result.\n")
    C.OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(C.OUT / "sample_gap.csv")
    (C.OUT / "sample_gap_choice.json").write_text(json.dumps({"variant": choice, "D": float(cand.min())}, indent=2))
    (C.OUT / "sample_gap.md").write_text("\n".join(md), encoding="utf-8")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(out.to_string())
    print(f"\nchoice: {choice}\nsaved {C.OUT / 'sample_gap.md'}")


if __name__ == "__main__":
    main()
