"""
How did the authors define their forecast-level variables?  (预测层面定义的反推)

    python diagnose_definitions.py --pull   # once: two small extra WRDS pulls (see [0]); asks for Duo once
    python diagnose_definitions.py          # -> output/definitions.md / definitions_grid.csv

Firm-level filters move neither EA_DUM, nor the forecast-type shares, nor mean CAR, nor mean CAPEX_ADJ
(diagnose_gap.py).  These four moments depend on how EACH forecast is coded, so this script varies the
forecast-level definitions the paper leaves open and asks which combination reproduces Table 1:

  [1] forecast type (D3)      R0 current: range if val_2 != val_1; open-ended codes -> other
                              R1 also "high end of" / "low end of" (06, 08) -> other
                              R2 by I/B/E/S code only: 01 -> range, 02/14 -> point, all else -> other
  [2] EA_DUM (D10)            E0 Compustat RDQ same day | E1 RDQ +/-1 day
                              E2 I/B/E/S actual EPS announcement date same day | E3 I/B/E/S +/-1 day
  [3] "earnings forecast" (D9) V1 EPS only | V2 earnings-type measures (current) | V3 any other guidance
                              measure on the same day | V4 V2 within +/-1 day
  [4] CAR                      mean by EA_DUM; mean re-weighted to the paper's EA_DUM; S&P 500 vs CRSP VW index

Sample characteristics only.  Pre-specified (docs/definitions_preregistration.md): the combination with the
smallest distance D to Table 1 is chosen BEFORE any regression; Table 3 is then estimated once on it.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

import build_capex_sample as B
import config as C
import utils as U
from diagnose_gap import PAPER, distance, refresh

CODE_LABEL = {"01": "between (区间)", "02": "about (约)", "03": "more than (多于)", "04": "at least (至少)",
              "06": "high end of (上端)", "08": "low end of (下端)", "10": "less than (少于)",
              "14": "comfortable with (认可)"}
OPEN = {str(x).zfill(2) for x in C.RANGE_DESC_OPEN_ENDED}
RULES = {"R0 current": dict(other=OPEN, code_only=False),
         "R1 06/08 -> other": dict(other=OPEN | {"06", "08"}, code_only=False),
         "R2 by code only": dict(other=None, code_only=True)}
D9_VARIANTS = {"V1 EPS only": dict(measures=("EPS",), days=0, src="guidance_earn"),
               "V2 earnings-type (current)": dict(measures=None, days=0, src="guidance_earn"),
               "V3 any other guidance": dict(measures="ALL", days=0, src="guidance_other"),
               "V4 earnings-type +/-1 day": dict(measures=None, days=1, src="guidance_earn")}


# ============================================================================ [0] extra pulls
def pull():
    from pull_wrds import connect, first_ok, _log
    db = connect()
    try:
        q = (f"SELECT DISTINCT ticker, measure, anndats FROM ibes.det_guidance WHERE measure <> '{C.MEASURE_CAPEX}' "
             f"AND anndats BETWEEN '{C.FCST_FIRST}' AND '{C.FCST_LAST}'")
        df = db.raw_sql(q); U.save(df, "guidance_other", C.RAW); _log("guidance_other", len(df), 0, "ok")
        print(f"guidance_other: {len(df):,} rows; measures: {sorted(df['measure'].astype(str).unique())[:40]}")
        sql = [f"SELECT DISTINCT ticker, pends, anndats FROM {t} WHERE pdicity = 'QTR' "
               f"AND anndats BETWEEN '{C.PULL_START}' AND '{C.PULL_END}'" for t in ("ibes.actu_epsus", "ibes.act_epsus")]
        df = first_ok(db, sql); U.save(df, "ibes_ea", C.RAW); _log("ibes_ea", len(df), 0, "ok")
        print(f"ibes_ea: {len(df):,} rows")
    finally:
        db.close()


def has(name):
    return any((C.RAW / f"{name}{ext}").exists() for ext in (".parquet", ".pkl"))


# ============================================================================ [1] forecast type
def classify_rule(c: pd.DataFrame, rule: dict) -> pd.DataFrame:
    c = c.copy()
    v1, v2 = c["val_1"], c["val_2"]
    rd = c["range_desc"].astype(str).str.strip().str.zfill(2) if "range_desc" in c else pd.Series("", index=c.index)
    two = v2.notna() & v1.notna() & (v2 != v1)
    if rule["code_only"]:
        is_range = two & rd.eq("01")
        is_other = ~rd.isin(["01", "02", "14"]) | (rd.eq("01") & ~two)
    else:
        is_other = rd.isin(rule["other"])
        is_range = two & ~is_other
    c["FTYPE"] = np.select([is_range, is_other], ["range", "other"], "point")
    c["F_LO"] = np.where(is_range, np.fmin(v1, v2), v1)
    c["F_HI"] = np.where(is_range, np.fmax(v1, v2), v1)
    c["CAPEX_FORE_raw"] = np.where(is_range, (c["F_LO"] + c["F_HI"]) / 2.0, v1)
    c["CAPEX_ADJ_raw"] = B.capex_adj(c["CAPEX_ACT_raw"].values, c["F_LO"].values, c["F_HI"].values,
                                     c["CAPEX_FORE_raw"].values)
    c["CAPEX_ADJ"] = U.winsorize(c["CAPEX_ADJ_raw"])
    return c


# ============================================================================ [2] EA_DUM
def ea_flags(c: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=c.index)
    fq = B.load_fundq().dropna(subset=["rdq"])[["gvkey", "rdq"]]
    m = c[["gvkey", "anndats"]].reset_index().merge(fq, on="gvkey")
    d = (m["anndats"] - m["rdq"]).dt.days.abs()
    out["E0 RDQ same day"] = c.index.isin(m.loc[d == 0, "index"])
    out["E1 RDQ +/-1"] = c.index.isin(m.loc[d <= 1, "index"])
    if has("ibes_ea"):
        a = U.lower_cols(U.load("ibes_ea", C.RAW))
        a["ticker"] = a["ticker"].astype(str).str.upper().str.strip()
        a["anndats"] = U.to_dt(a["anndats"])
        m = c[["ticker", "anndats"]].reset_index().merge(a[["ticker", "anndats"]].rename(columns={"anndats": "ea"}),
                                                         on="ticker")
        d = (m["anndats"] - m["ea"]).dt.days.abs()
        out["E2 IBES same day"] = c.index.isin(m.loc[d == 0, "index"])
        out["E3 IBES +/-1"] = c.index.isin(m.loc[d <= 1, "index"])
    return out.astype(int)


def surp_for(c: pd.DataFrame, ea: pd.Series) -> pd.Series:
    """SURP for a new EA definition: the built SURP where it exists, else the RDQ closest within 3 days."""
    s = c["SURP_raw"] if "SURP_raw" in c else c["SURP"]
    s = s.where(c["EA_DUM"] == 1)
    need = (ea == 1) & s.isna()
    if need.any():
        fq = B.load_fundq().dropna(subset=["rdq"])[["gvkey", "rdq", "epspxq", "eps_lag4"]]
        m = c.loc[need, ["gvkey", "anndats"]].reset_index().merge(fq, on="gvkey")
        m["d"] = (m["anndats"] - m["rdq"]).dt.days.abs()
        m = m[m["d"] <= 3].sort_values(["index", "d"]).drop_duplicates("index").set_index("index")
        s.loc[m.index] = (m["epspxq"] - m["eps_lag4"]).values
    return s.where(ea == 1, 0.0).fillna(0.0)


# ============================================================================ [3] D9 rebuilds
def rebuild(name: str, spec: dict) -> pd.DataFrame | None:
    if spec["src"] == "guidance_other" and not has("guidance_other"):
        print(f"[def] {name}: data/raw/guidance_other missing -> run with --pull first; skipped")
        return None
    saved = (C.CONCURRENT_MEASURES, C.EPS_CONCURRENT_DAYS, U.load)
    tmp = Path(tempfile.mkdtemp())
    backups = [p for p in (C.INTERIM / "capex_sample.parquet", C.INTERIM / "capex_sample.pkl",
                           C.OUT / "sample_waterfall.csv") if p.exists()]
    for p in backups:
        shutil.copy2(p, tmp / p.name)
    try:
        if spec["measures"] == "ALL":
            other = U.lower_cols(saved[2]("guidance_other", C.RAW))
            ms = sorted(set(other["measure"].astype(str).str.upper().str.strip()) - {C.MEASURE_CAPEX})
            C.CONCURRENT_MEASURES = tuple(ms)
            U.load = lambda n, d=C.INTERIM, _l=saved[2]: _l("guidance_other" if n == "guidance_earn" else n, d)
            B.U.load = U.load
        elif spec["measures"]:
            C.CONCURRENT_MEASURES = spec["measures"]
        C.EPS_CONCURRENT_DAYS = spec["days"]
        c = B.build()
        wf = pd.read_csv(C.OUT / "sample_waterfall.csv")
        c.attrs["w3_drop"] = 1 - wf.loc[wf.step == "w3_not_concurrent_eps", "ours"].iloc[0] / \
            wf.loc[wf.step == "w2_with_car", "ours"].iloc[0]
        U.save(c, "capex_sample_def_" + name.split()[0])
        return c
    finally:
        C.CONCURRENT_MEASURES, C.EPS_CONCURRENT_DAYS, U.load = saved
        B.U.load = saved[2]
        for p in (C.INTERIM / "capex_sample.parquet", C.INTERIM / "capex_sample.pkl"):
            p.unlink(missing_ok=True)
        for p in backups:
            shutil.copy2(tmp / p.name, p)
        shutil.rmtree(tmp, ignore_errors=True)


# ============================================================================ [4] CAR
def car_vw_shift(c: pd.DataFrame) -> pd.Series:
    """CAR against the CRSP value-weighted index = CAR + sum over [-2,2] of (S&P 500 - VW) returns, in %."""
    dsi = U.lower_cols(U.load("dsi", C.RAW))
    if "vwretd" not in dsi:
        return pd.Series(np.nan, index=c.index)
    cal = U.TradingCalendar(dsi["date"])
    dsi["date"] = U.to_dt(dsi["date"])
    diff = pd.Series((pd.to_numeric(dsi["sprtrn"], errors="coerce") - pd.to_numeric(dsi["vwretd"], errors="coerce")).values,
                     index=cal.index_exact(dsi["date"])) * 100.0
    t0 = pd.to_numeric(c["t0"], errors="coerce")
    shift = sum(t0.add(k).map(diff) for k in range(C.CAR_WIN[0], C.CAR_WIN[1] + 1))
    return c["CAR_raw"] + shift


# ============================================================================ moments
def mom(c: pd.DataFrame, ea: pd.Series) -> dict:
    ft = c["FTYPE"].value_counts(normalize=True)
    adj = c["CAPEX_ADJ"]
    return dict(N=len(c), firms=c["gvkey"].nunique(), EA_DUM=ea.mean(), CAR_mean=c["CAR"].mean(),
                ADJ_mean=adj.mean(), ADJ_median=adj.median(), ADJ_zero=(c["CAPEX_ADJ_raw"] == 0).mean(),
                point=ft.get("point", 0.0), range=ft.get("range", 0.0), other=ft.get("other", 0.0))


def main():
    if "--pull" in sys.argv:
        pull()
    main_c = U.load("capex_sample")
    md = ["# Forecast-level definitions\n", "Sample characteristics only. Paper Table 1: EA_DUM 0.559; point / range / "
          "other 55.3% / 34.5% / 10.2%; CAPEX_ADJ mean 7.421, median 0.000; CAR mean −0.148.\n"]

    # [1] codes in the final sample
    rd = main_c["range_desc"].astype(str).str.strip().str.zfill(2) if "range_desc" in main_c else pd.Series("NA", index=main_c.index)
    two = main_c["val_2"].notna() & (main_c["val_2"] != main_c["val_1"])
    t = pd.crosstab(rd.rename("range_desc"), main_c["FTYPE"], margins=True)
    t["share"] = t["All"] / len(main_c)
    t["with val_2 != val_1"] = two.groupby(rd).sum().reindex(t.index).fillna(two.sum()).astype(int)
    t.insert(0, "label", [CODE_LABEL.get(i, "") for i in t.index])
    md += ["\n## [1] I/B/E/S range_desc codes in the final sample\n", t.to_markdown(floatfmt=".3f")]

    # [3] D9 variants (rebuild), then the grid
    samples = {}
    for name, spec in D9_VARIANTS.items():
        if name.startswith("V2"):
            samples[name] = main_c.copy()
            wf = pd.read_csv(C.OUT / "sample_waterfall.csv")
            samples[name].attrs["w3_drop"] = 1 - wf.loc[wf.step == "w3_not_concurrent_eps", "ours"].iloc[0] / \
                wf.loc[wf.step == "w2_with_car", "ours"].iloc[0]
        else:
            s = rebuild(name, spec)
            if s is not None:
                samples[name] = s

    rows, keep = [], {}
    for (vn, s), (rn, rule) in product(samples.items(), RULES.items()):
        cr = classify_rule(s, rule)
        eas = ea_flags(cr)
        for en in eas:
            m = mom(cr, eas[en])
            m.update(D9=vn, type_rule=rn, EA_def=en, w3_drop=s.attrs.get("w3_drop", np.nan), D=distance(m))
            rows.append(m)
        keep[(vn, rn)] = (cr, eas)
    grid = pd.DataFrame(rows).sort_values("D")
    cols = ["D9", "type_rule", "EA_def", "N", "firms", "w3_drop", "EA_DUM", "point", "range", "other",
            "ADJ_mean", "ADJ_median", "ADJ_zero", "CAR_mean", "D"]
    paper = dict(D9="paper", type_rule="", EA_def="", N=17577, firms=1790, w3_drop=0.474, EA_DUM=0.559, point=0.553,
                 range=0.3448, other=0.1022, ADJ_mean=7.421, ADJ_median=0.0, ADJ_zero=np.nan, CAR_mean=-0.148, D=np.nan)
    show = pd.concat([pd.DataFrame([paper]), grid], ignore_index=True)[cols]
    md += ["\n\n## [2]+[3] Definition grid (sorted by distance D)\n",
           "D9 changes the sample; the type rule changes FTYPE and CAPEX_ADJ; the EA definition changes EA_DUM only.\n\n",
           show.head(20).to_markdown(index=False, floatfmt=".3f")]

    # one-at-a-time effects from the current specification
    base = grid[(grid.D9.str.startswith("V2")) & (grid.type_rule == "R0 current") & (grid.EA_def == "E0 RDQ same day")]
    oat = pd.concat([base,
                     grid[(grid.D9.str.startswith("V2")) & (grid.EA_def == "E0 RDQ same day") & (grid.type_rule != "R0 current")],
                     grid[(grid.D9.str.startswith("V2")) & (grid.type_rule == "R0 current") & (grid.EA_def != "E0 RDQ same day")],
                     grid[(~grid.D9.str.startswith("V2")) & (grid.type_rule == "R0 current") & (grid.EA_def == "E0 RDQ same day")]])
    md += ["\n\n## One change at a time (from the current specification)\n", oat[cols].to_markdown(index=False, floatfmt=".3f")]

    # [4] CAR
    c0 = main_c
    m1, m0 = c0.loc[c0.EA_DUM == 1, "CAR"].mean(), c0.loc[c0.EA_DUM == 0, "CAR"].mean()
    vw = car_vw_shift(c0)
    md += ["\n\n## [4] Mean CAR (%)\n",
           f"| | mean CAR |\n|---|---|\n| current sample | {c0['CAR'].mean():.3f} |\n| EA_DUM = 1 | {m1:.3f} |\n"
           f"| EA_DUM = 0 | {m0:.3f} |\n| re-weighted to EA_DUM = 0.559 | {0.559 * m1 + 0.441 * m0:.3f} |\n"
           f"| market = CRSP value-weighted (unwinsorised) | {vw.mean():.3f} |\n| paper | −0.148 |\n"]

    # [5] pre-specified choice and one Table 3 estimate
    best = grid.iloc[0]
    md += [f"\n\n## [5] Pre-specified choice\n\nSmallest D: **{best.D9} · {best.type_rule} · {best.EA_def}** "
           f"(D = {best.D:.3f}; current specification D = {base.D.iloc[0]:.3f}).\n"]
    if (best.D9, best.type_rule, best.EA_def) != (base.D9.iloc[0], base.type_rule.iloc[0], base.EA_def.iloc[0]):
        from t3_diagnostics import CTRL8, diff_est, fmt
        cr, eas = keep[(best.D9, best.type_rule)]
        cr = cr.copy()
        new_ea = pd.Series(eas[best.EA_def].values, index=cr.index)
        cr["SURP_raw"] = surp_for(cr, new_ea).values        # uses the built EA_DUM before it is replaced
        cr["EA_DUM"] = new_ea.values
        cr = refresh(cr)
        r = fmt(diff_est(cr, ["CAR_z", *CTRL8], "HIGHER_SPREAD"))
        md += ["\nTable 3 (CAR), estimated once on this specification:\n\n", pd.DataFrame([r]).to_markdown(index=False)]
    else:
        md += ["\nThe current specification is already the closest; no new Table 3 estimate.\n"]

    C.OUT.mkdir(parents=True, exist_ok=True)
    show.to_csv(C.OUT / "definitions_grid.csv", index=False)
    (C.OUT / "definitions.md").write_text("\n".join(md), encoding="utf-8")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(show.head(15).round(3).to_string())
    print(f"saved {C.OUT / 'definitions.md'}")


if __name__ == "__main__":
    main()
