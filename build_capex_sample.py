"""
Step 02b - build the capex-forecast sample (unit: firm-quarter) with every variable used in
Tables 1-5.  Variable names follow the paper.  Sample waterfall is written to
output/sample_waterfall.csv next to the paper's counts.

Paper waterfall (Section 2.2):
  IBES annual capex forecasts matched to Compustat (2002-2016) ........ 40,785
  with CRSP short-window market reaction ................................ 36,900
  less: made concurrently with an earnings forecast ..................... -17,473
  less: made in 2016 (no actual capex yet) .............................. -1,850
  final: 17,577 forecasts, 1,790 firms, 2003-2015
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
import utils as U

PAPER_WATERFALL = {"w1_matched_compustat": 40785, "w2_with_car": 36900,
                   "w3_not_concurrent_eps": 36900 - 17473, "w4_drop_2016": 17577}


# ============================================================================ guidance
def clean_guidance() -> pd.DataFrame:
    g = U.lower_cols(U.load("guidance", C.RAW))
    g["anndats"] = U.to_dt(g["anndats"])
    for c in ("measure", "pdicity", "ticker"):
        g[c] = g[c].astype(str).str.upper().str.strip()
    if C.REQUIRE_USFIRM and "usfirm" in g:
        g = g[pd.to_numeric(g["usfirm"], errors="coerce") == 1]
    if C.REQUIRE_USD and "curr" in g:
        g = g[g["curr"].isna() | g["curr"].astype(str).str.upper().str.strip().eq("USD")]
    g["prd_end"] = U.month_end(g["prd_yr"], g["prd_mon"])
    for c in ("val_1", "val_2"):
        g[c] = pd.to_numeric(g[c], errors="coerce")
    if "units" in g:
        mult = g["units"].astype(str).str.upper().str.strip().map(C.UNITS_TO_MILLIONS)
        is_money = g["measure"].isin([C.MEASURE_CAPEX, C.MEASURE_SALES])
        for c in ("val_1", "val_2"):
            g.loc[is_money, c] = g.loc[is_money, c] * mult[is_money].fillna(1.0)
    if "anntims" not in g:
        g["anntims"] = "00:00:00"
    return g.dropna(subset=["anndats"])


def annual_forecasts(g: pd.DataFrame, measure: str) -> pd.DataFrame:
    """One record per (ticker, announcement date): nearest fiscal period, latest revision."""
    f = g[(g["measure"] == measure) & (g["pdicity"] == C.PDICITY_ANNUAL)].dropna(subset=["val_1", "prd_end"])
    f = f[(f["prd_end"] > f["anndats"]) &
          (f["prd_end"] <= f["anndats"] + pd.DateOffset(months=C.MAX_HORIZON_MONTHS))]
    f = f.sort_values(["ticker", "anndats", "prd_end", "anntims"])
    f = f.drop_duplicates(["ticker", "anndats", "prd_end"], keep="last")
    if C.NEAREST_PERIOD_ONLY:
        f = f.drop_duplicates(["ticker", "anndats"], keep="first")
    return f.reset_index(drop=True)


def classify(c: pd.DataFrame) -> pd.DataFrame:
    """Point / range / other (open-ended) forecasts, Table 1 Panel C."""
    c = c.copy()
    v1, v2 = c["val_1"], c["val_2"]
    is_range = v2.notna() & v1.notna() & (v2 != v1)
    rd = c["range_desc"].astype(str).str.strip().str.zfill(2) if "range_desc" in c else pd.Series("", index=c.index)
    is_other = ~is_range & rd.isin({str(x).zfill(2) for x in C.RANGE_DESC_OPEN_ENDED})
    c["FTYPE"] = np.select([is_range, is_other], ["range", "other"], "point")
    c["F_LO"] = np.where(is_range, np.fmin(v1, v2), v1)
    c["F_HI"] = np.where(is_range, np.fmax(v1, v2), v1)
    c["CAPEX_FORE"] = np.where(is_range, (c["F_LO"] + c["F_HI"]) / 2.0, v1)  # D7: range midpoint
    return c[c["CAPEX_FORE"] > 0]


def capex_adj(act, lo, hi, fore) -> np.ndarray:
    """(%) actual vs forecast; for ranges, distance to the violated bound, zero inside (Sec. 2.2)."""
    up, dn = act > hi, act < lo
    num = np.where(up, act - hi, np.where(dn, act - lo, 0.0))
    if C.RANGE_SCALER == "bound":
        den = np.where(up, hi, np.where(dn, lo, fore))
    else:
        den = fore
    out = num / den * 100.0
    return np.where(np.isfinite(act), out, np.nan)


# ============================================================================ accounting
def load_funda() -> pd.DataFrame:
    a = U.lower_cols(U.load("funda", C.RAW))
    a["datadate"] = U.to_dt(a["datadate"])
    a["gvkey"] = a["gvkey"].astype(str).str.zfill(6)
    for c in ("capx", "at", "ib", "ni", "oancf", "csho", "prcc_f", "ceq", "dltt", "dlc", "ppent", "fyear"):
        a[c] = pd.to_numeric(a[c], errors="coerce")
    a = a.sort_values(["gvkey", "datadate"]).drop_duplicates(["gvkey", "datadate"], keep="last")
    a["ym"] = a["datadate"].dt.year * 100 + a["datadate"].dt.month
    a["mv"] = a["prcc_f"] * a["csho"]
    return a


def load_fundq() -> pd.DataFrame:
    q = U.lower_cols(U.load("fundq", C.RAW))
    q["datadate"], q["rdq"] = U.to_dt(q["datadate"]), U.to_dt(q["rdq"])
    q["gvkey"] = q["gvkey"].astype(str).str.zfill(6)
    for c in ("epspxq", "atq", "ibq", "niq", "cshoq", "prccq", "ceqq", "dlttq", "dlcq", "ppentq", "fyearq", "fqtr"):
        if c in q:
            q[c] = pd.to_numeric(q[c], errors="coerce")
    q = q.sort_values(["gvkey", "datadate"]).drop_duplicates(["gvkey", "datadate"], keep="last")
    if "ajexq" in q:
        q["ajexq"] = pd.to_numeric(q["ajexq"], errors="coerce")
    else:
        q["ajexq"] = np.nan
    lag = q[["gvkey", "fyearq", "fqtr", "epspxq", "ajexq"]].rename(columns={"epspxq": "eps_lag4", "ajexq": "ajexq_lag4"})
    lag["fyearq"] = lag["fyearq"] + 1
    q = q.merge(lag.drop_duplicates(["gvkey", "fyearq", "fqtr"]), on=["gvkey", "fyearq", "fqtr"], how="left")
    if C.SURP_SPLIT_ADJUST:   # D32: EPS_{q-4} on the share basis of quarter q (Compustat: adjusted EPS = EPS/AJEX)
        f = (q["ajexq"] / q["ajexq_lag4"]).where((q["ajexq"] > 0) & (q["ajexq_lag4"] > 0))
        q["eps_lag4"] = q["eps_lag4"] * f.fillna(1.0)
    q["mvq"] = q["prccq"] * q["cshoq"]
    return q


def firm_industry(gvkeys: pd.Series, funda: pd.DataFrame) -> pd.Series:
    """D18: one industry per firm (modal historical SIC, else header SIC) so firm FE nest in clusters."""
    comp = U.lower_cols(U.load("company", C.RAW))
    comp["gvkey"] = comp["gvkey"].astype(str).str.zfill(6)
    s = funda.dropna(subset=["sich"]).groupby("gvkey")["sich"].agg(lambda x: x.mode().iloc[0])
    hdr = comp.drop_duplicates("gvkey").set_index("gvkey")["sic"]
    sic = gvkeys.map(s).fillna(gvkeys.map(pd.to_numeric(hdr, errors="coerce")))
    return U.sic2(sic)


# ============================================================================ industry ERC
def industry_erc(cal: U.TradingCalendar, fundq: pd.DataFrame, funda: pd.DataFrame) -> pd.DataFrame:
    e = U.lower_cols(U.load("ea_daily", C.RAW))
    e["date"], e["rdq"] = U.to_dt(e["date"]), U.to_dt(e["rdq"])
    e["gvkey"] = e["gvkey"].astype(str).str.zfill(6)
    e["tidx"] = cal.index_exact(e["date"])
    e["t0"] = cal.on_or_after(e["rdq"])
    e["k"] = e["tidx"] - e["t0"]
    e["ar"] = pd.to_numeric(e["ret"], errors="coerce") - pd.to_numeric(e["sprtrn"], errors="coerce")
    lo, hi = C.EA_CAR_WIN
    w = e[(e["k"] >= lo) & (e["k"] <= hi)].drop_duplicates(["gvkey", "rdq", "k"])
    ea = w.groupby(["gvkey", "rdq"])["ar"].agg(["sum", "count"]).reset_index()
    ea = ea[ea["count"] == hi - lo + 1].rename(columns={"sum": "ea_car"})
    ea["sic2"] = firm_industry(ea["gvkey"], funda).values
    if C.ERC_METHOD == "slope":
        fq = fundq.dropna(subset=["rdq"])[["gvkey", "rdq", "epspxq", "eps_lag4", "prccq"]]
        ea = ea.merge(fq.drop_duplicates(["gvkey", "rdq"]), on=["gvkey", "rdq"], how="left")
        ea["sue"] = U.winsorize((ea["epspxq"] - ea["eps_lag4"]) / ea["prccq"])
        ea = ea.dropna(subset=["sue", "ea_car"])
        ea["xy"], ea["xx"] = ea["ea_car"] * ea["sue"], ea["sue"] ** 2
        a = ea.groupby("sic2").agg(n=("sue", "size"), x=("sue", "mean"), y=("ea_car", "mean"),
                                   xy=("xy", "mean"), xx=("xx", "mean"))
        out = ((a["xy"] - a["x"] * a["y"]) / (a["xx"] - a["x"] ** 2)).where(a["n"] >= 30).rename("ERC")
    else:
        out = ea.groupby("sic2")["ea_car"].agg(lambda x: x.abs().mean() if len(x) >= 30 else np.nan).rename("ERC")
    out = out.reset_index().dropna()
    U.save(out, "industry_erc")
    return out


# ============================================================================ main build
def build() -> pd.DataFrame:
    wf = []
    dsi = U.lower_cols(U.load("dsi", C.RAW))
    cal = U.TradingCalendar(dsi["date"])
    daily = U.daily_with_tidx(U.load("dsf", C.RAW), dsi, cal)
    dsi["date"] = U.to_dt(dsi["date"])
    mkt = pd.Series(pd.to_numeric(dsi["sprtrn"], errors="coerce").values, index=cal.index_exact(dsi["date"]))
    ibl, ccm = U.load("ibcrsphist", C.RAW), U.load("ccm", C.RAW)
    funda, fundq = load_funda(), load_fundq()

    g = clean_guidance()
    c = classify(annual_forecasts(g, C.MEASURE_CAPEX))
    c = c[(c["anndats"] >= C.FCST_FIRST) & (c["anndats"] <= C.FCST_LAST)]
    wf.append(("w0_ibes_capex_forecasts", len(c)))
    c["qid"] = U.qid(c["anndats"]).astype(int)
    if C.ONE_PER_FIRM_QUARTER and C.COLLAPSE_AT_START:                 # D6: firm = IBES ticker here
        c = c.sort_values(["ticker", "qid", "anndats", "anntims"]).drop_duplicates(
            ["ticker", "qid"], keep=C.ONE_PER_FIRM_QUARTER).reset_index(drop=True)
        wf.append(("w0b_one_per_firm_quarter", len(c)))

    # ---- link IBES -> CRSP -> Compustat and attach ACTUAL capex of the forecasted fiscal year
    c = U.link_ibes_permno(c, ibl, "anndats")
    c = U.link_permno_gvkey(c, ccm, "anndats").dropna(subset=["permno", "gvkey"])
    c["gvkey"] = c["gvkey"].astype(str).str.zfill(6)
    if C.SHRCD_FILTER:                                             # D23 (off by default)
        c = U.shrcd_at(c, U.load("msenames", C.RAW), "anndats")
        c = c[c["shrcd"].isin(C.SHRCD_FILTER)]
    c["ym"] = c["prd_end"].dt.year * 100 + c["prd_end"].dt.month
    act = funda[["gvkey", "ym", "capx", "at", "datadate", "fyear"]].rename(
        columns={"capx": "CAPEX_ACT", "at": "AT_T", "datadate": "fy_datadate"})
    c = c.merge(act, on=["gvkey", "ym"], how="left")
    c = c.dropna(subset=["permno", "gvkey", "CAPEX_ACT"]).reset_index(drop=True)
    wf.append(("w1_matched_compustat", len(c)))

    # ---- market reaction
    c["eid"] = np.arange(len(c))
    c["t0"] = U.day0(c, cal)
    c["CAR"] = c["eid"].map(U.car(c, daily, *C.CAR_WIN, min_obs=C.MIN_RET_OBS))
    c = c.dropna(subset=["CAR"]).reset_index(drop=True)
    wf.append(("w2_with_car", len(c)))

    # ---- drop forecasts concurrent with an EPS forecast (D9)
    eps = g[g["measure"] == C.MEASURE_EPS][["ticker", "anndats"]].drop_duplicates()
    m = c[["eid", "ticker", "anndats"]].merge(eps.rename(columns={"anndats": "eps_dt"}), on="ticker")
    hit = m.loc[(m["anndats"] - m["eps_dt"]).dt.days.abs() <= C.EPS_CONCURRENT_DAYS, "eid"].unique()
    c = c[~c["eid"].isin(hit)].reset_index(drop=True)
    wf.append(("w3_not_concurrent_eps", len(c)))

    yr = c["anndats"].dt.year
    n2002 = int((yr < C.KEEP_FROM_YEAR).sum())
    c = c[(yr >= C.KEEP_FROM_YEAR) & (yr < C.DROP_FROM_YEAR)].reset_index(drop=True)      # D2
    wf.append(("w4_drop_2016", len(c)))
    if n2002:
        print(f"[capex] note: {n2002:,} forecasts before {C.KEEP_FROM_YEAR} removed together with 2016 "
              f"(paper's final sample starts in 2003; its waterfall implies none survived to this step)")

    # ---- one observation per firm-quarter, if not already done at the start (D6)
    if C.ONE_PER_FIRM_QUARTER and not C.COLLAPSE_AT_START:
        c = c.sort_values(["gvkey", "qid", "anndats"]).drop_duplicates(
            ["gvkey", "qid"], keep=C.ONE_PER_FIRM_QUARTER).reset_index(drop=True)
        wf.append(("w5_one_per_firm_quarter", len(c)))

    # ---- capex adjustment
    c["CAPEX_ADJ"] = capex_adj(c["CAPEX_ACT"].values, c["F_LO"].values, c["F_HI"].values, c["CAPEX_FORE"].values)

    # ---- event-study variables
    c["MKTRET"] = c["t0"].map(mkt) * 100.0
    c["t0_pre"] = cal.on_or_before(c["anndats"] - pd.Timedelta(days=C.CAR_PRE_SHIFT_CAL_DAYS))
    c["CAR_PRE"] = c["eid"].map(U.car(c, daily, *C.CAR_WIN, t0_col="t0_pre", min_obs=C.MIN_RET_OBS))
    w = U.event_window(c, daily, C.SPREAD_PRE_WIN[0], C.SPREAD_POST_WIN[1], ["spread"])
    pre = w[w["k"].between(*C.SPREAD_PRE_WIN)].groupby("eid")["spread"].agg(["mean", "count"])
    evt = w[w["k"].between(*C.SPREAD_EVT_WIN)].groupby("eid")["spread"].agg(["mean", "count"])
    c["SPREAD_PRE"] = c["eid"].map(pre["mean"].where(pre["count"] >= 4))
    c["SPREAD_EVT"] = c["eid"].map(evt["mean"].where(evt["count"] >= 3))
    c["HIGHER_SPREAD"] = np.where(c[["SPREAD_PRE", "SPREAD_EVT"]].notna().all(axis=1),
                                  (c["SPREAD_EVT"] > c["SPREAD_PRE"]).astype(float), np.nan)

    # ---- EA_DUM and SURP (D10)
    fq = fundq.dropna(subset=["rdq"])[["gvkey", "rdq", "epspxq", "eps_lag4"]]
    m = c[["eid", "gvkey", "anndats"]].merge(fq, on="gvkey")
    m["dist"] = (m["anndats"] - m["rdq"]).dt.days.abs()
    m = m[m["dist"] <= C.EA_CONCURRENT_DAYS].sort_values(["eid", "dist"]).drop_duplicates("eid")
    c["EA_DUM"] = c["eid"].isin(m["eid"]).astype(int)
    c["SURP"] = c["eid"].map(m.set_index("eid").eval("epspxq - eps_lag4"))
    c.loc[c["EA_DUM"] == 0, "SURP"] = 0.0

    # ---- SIZE: log MV at end of the quarter preceding the forecast quarter (Compustat quarterly)
    c["qstart_m1"] = (c["anndats"].dt.to_period("Q").dt.start_time - pd.Timedelta(days=1)).astype("datetime64[ns]")
    left = c[["eid", "gvkey", "qstart_m1"]].sort_values("qstart_m1")
    right = fundq[["gvkey", "datadate", "mvq"]].dropna().sort_values("datadate")
    left["gvkey"], right["gvkey"] = left["gvkey"].astype(str), right["gvkey"].astype(str)
    s = pd.merge_asof(left, right, left_on="qstart_m1", right_on="datadate", by="gvkey",
                      direction="backward", tolerance=pd.Timedelta(days=183))
    c["MV"] = c["eid"].map(s.set_index("eid")["mvq"])
    c["SIZE"] = np.log(c["MV"].where(c["MV"] > 0))

    # ---- LAG_CAPX: most recent completed fiscal year before the forecast (D15)
    left = c[["eid", "gvkey", "anndats"]].copy()
    left["key"] = left["anndats"] - pd.Timedelta(days=1)
    left = left.sort_values("key")
    right = funda[["gvkey", "datadate", "capx", "mv", "at"]].dropna(subset=["capx"]).sort_values("datadate")
    left["gvkey"], right["gvkey"] = left["gvkey"].astype(str), right["gvkey"].astype(str)
    s = pd.merge_asof(left, right, left_on="key", right_on="datadate", by="gvkey",
                      direction="backward", tolerance=pd.Timedelta(days=400)).set_index("eid")
    c["LAG_CAPX_MIL"] = c["eid"].map(s["capx"])
    c["LAG_CAPX"] = c["eid"].map(s["capx"] / s["mv"].where(s["mv"] > 0) * 100.0)
    c["AT_PREV_FY"] = c["eid"].map(s["at"])

    # ---- asset growth to the end of the forecast's fiscal quarter (footnote 18 robustness)
    left = c[["eid", "gvkey", "anndats"]].sort_values("anndats")
    right = fundq[["gvkey", "datadate", "atq"]].dropna().sort_values("datadate")
    left["gvkey"], right["gvkey"] = left["gvkey"].astype(str), right["gvkey"].astype(str)
    s = pd.merge_asof(left, right, left_on="anndats", right_on="datadate", by="gvkey",
                      direction="forward", tolerance=pd.Timedelta(days=100)).set_index("eid")
    c["ASSET_GROWTH"] = c["eid"].map(s["atq"]) / c["AT_PREV_FY"].where(c["AT_PREV_FY"] > 0) - 1

    # ---- future performance (Table 4): fiscal year t+1 of the forecasted year t
    nxt = funda[["gvkey", "fyear", "oancf", "ib", "ni", "at"]].copy()
    nxt["fyear"] = nxt["fyear"] - 1
    nxt = nxt.rename(columns={"oancf": "oancf1", "ib": "ib1", "ni": "ni1", "at": "at1"})
    c["fyear"] = pd.to_numeric(c["fyear"], errors="coerce")
    c = c.merge(nxt.drop_duplicates(["gvkey", "fyear"]), on=["gvkey", "fyear"], how="left")
    scal = c["at1"] if C.PERF_SCALER == "at_same_year" else c["AT_T"]
    scal = scal.where(scal > 0)
    c["CFO1"], c["IBEI1"], c["NI1"] = (c["oancf1"] / scal * 100, c["ib1"] / scal * 100, c["ni1"] / scal * 100)
    at_t = c["AT_T"].where(c["AT_T"] > 0)
    c["CAPEX_AT"] = c["CAPEX_ACT"] / at_t * 100
    c["FORE_AT"] = c["CAPEX_FORE"] / at_t * 100

    # ---- fixed effects / clusters
    c["IND"] = firm_industry(c["gvkey"].astype(str), funda).values
    comp = U.lower_cols(U.load("company", C.RAW))
    comp["gvkey"] = comp["gvkey"].astype(str).str.zfill(6)
    if "state" in comp:
        c["STATE"] = c["gvkey"].astype(str).map(comp.drop_duplicates("gvkey").set_index("gvkey")["state"])
    c["YQ"] = c["anndats"].dt.year * 10 + c["anndats"].dt.quarter
    c["YEAR"] = c["anndats"].dt.year

    # ---- falsification: market reaction to the closest sales forecast for the same fiscal period
    s = annual_forecasts(g, C.MEASURE_SALES)
    s = U.link_ibes_permno(s, ibl, "anndats").dropna(subset=["permno"]).reset_index(drop=True)
    s["eid"] = np.arange(len(s))
    s["t0"] = U.day0(s, cal)
    s["SF_CAR"] = s["eid"].map(U.car(s, daily, *C.CAR_WIN, min_obs=C.MIN_RET_OBS))
    m = c[["eid", "ticker", "prd_end", "t0", "anndats"]].merge(
        s[["ticker", "prd_end", "t0", "anndats", "SF_CAR"]].dropna(), on=["ticker", "prd_end"], suffixes=("", "_s"))
    m = m[(m["t0"] - m["t0_s"]).abs() >= C.SF_MIN_GAP_TDAYS]
    m["dist"] = (m["anndats"] - m["anndats_s"]).dt.days.abs()
    m = m.sort_values(["eid", "dist"]).drop_duplicates("eid").set_index("eid")
    c["SF_CAR"], c["SF_DIST_DAYS"] = c["eid"].map(m["SF_CAR"]), c["eid"].map(m["dist"])

    if C.SCOPE != "t13":
        c = attach_cross_sectional(c, cal, fundq, funda)

    # ---- winsorise (D14) and standardise (D27); keep every raw version for the Table 1 check
    levels = ["CAPEX_FORE", "CAPEX_ACT", "LAG_CAPX_MIL", "SIZE"]
    wvars = list(C.WINSOR_VARS) + (levels if C.WINSOR_LEVELS else [])
    for v in dict.fromkeys(wvars + levels + ["MKTRET"]):
        if v in c:
            c[v + "_raw"] = c[v]
            if v in wvars:
                c[v] = U.winsorize(c[v])
    c["CAR_POS"], c["CAR_NEG"] = c["CAR"].clip(lower=0), c["CAR"].clip(upper=0)   # D35: split raw CAR, then z-score
    for v in ("CAR", "CAR_POS", "CAR_NEG", "MKTRET", "CAR_PRE", "SF_CAR"):
        c[v + "_z"] = U.zscore(c[v])

    U.save(c, "capex_sample")
    wfd = pd.DataFrame(wf, columns=["step", "ours"])
    wfd["paper"] = wfd["step"].map(PAPER_WATERFALL)
    C.OUT.mkdir(parents=True, exist_ok=True)
    wfd.to_csv(C.OUT / "sample_waterfall.csv", index=False)
    print(wfd.to_string(index=False))
    print(f"[capex] final N = {len(c):,}, firms = {c['gvkey'].nunique():,}, "
          f"years {c['YEAR'].min()}-{c['YEAR'].max()}")
    return c


def attach_cross_sectional(c, cal, fundq, funda) -> pd.DataFrame:
    """MF_OF (Panel E2), PIN (A), INSIDER (B), ERC (C), pay duration (D)."""
    # mutual-fund outflows of the PREVIOUS quarter
    if U.exists("mf_pressure"):
        mf = U.load("mf_pressure")
        mf = mf.assign(qid=mf["qid"] + 1)[["permno", "qid", "MFFLOW", "OUTFLOW", "MF_OF"]]
        c = c.merge(mf, on=["permno", "qid"], how="left")
        if C.MF_MISSING_AS_ZERO:                                   # D37
            miss = c["OUTFLOW"].isna()
            c.loc[miss, ["MFFLOW", "OUTFLOW"]] = 0.0
            c.loc[miss, "MF_OF"] = 0
            print(f"[capex] MF pressure missing for {miss.sum():,} forecasts -> set to 0 (D37)")
        if C.MF_MEDIAN_UNIVERSE == "sample":
            c["MF_OF"] = (c["OUTFLOW"] > c["OUTFLOW"].median()).astype(float).where(c["OUTFLOW"].notna())
    # PIN as of the quarter before the forecast
    pin_f = C.EXTERNAL / "pin.csv"
    if pin_f.exists():
        p = U.lower_cols(pd.read_csv(pin_f))
        qcol = "qtr" if "qtr" in p else "quarter"
        p["qid"] = p["year"].astype(int) * 4 + p[qcol].astype(int) - 1 + C.PIN_QUARTER_LAG
        c = c.merge(p[["permno", "qid", "pin"]].rename(columns={"pin": "PIN"}).drop_duplicates(["permno", "qid"]),
                    on=["permno", "qid"], how="left")
    # insider transactions (buys + sells) per quarter / MV (D20)
    if U.exists("insider", C.RAW):
        it = U.lower_cols(U.load("insider", C.RAW))
        if "cleanse" in it:
            it = it[it["cleanse"].isin(["R", "H"]) | it["cleanse"].isna()]
        it["trandate"] = U.to_dt(it["trandate"])
        it["cusip8"] = it["cusip6"].astype(str).str.strip() + it["cusip2"].astype(str).str.strip()
        it = U.permno_from_ncusip(it, U.load("msenames", C.RAW), "cusip8", "trandate").dropna(subset=["permno"])
        it["qid"] = U.qid(it["trandate"]).astype(int) + (1 if C.INSIDER_QUARTER == "prev" else 0)
        it["permno"] = it["permno"].astype(int)
        cnt = it.groupby(["permno", "qid"]).size().rename("N_INSIDER").reset_index()
        c = c.merge(cnt, on=["permno", "qid"], how="left")
        if not C.INSIDER_ZERO_AS_MISSING:                          # D31
            c["N_INSIDER"] = c["N_INSIDER"].fillna(0)
        c["INSIDER"] = c["N_INSIDER"] / c["MV"].where(c["MV"] > 0)
    # industry ERC
    if U.exists("ea_daily", C.RAW):
        erc = industry_erc(cal, fundq, funda)
        c = c.merge(erc.rename(columns={"sic2": "IND"}), on="IND", how="left")
    # CEO pay duration (Gopalan et al. 2014)
    pd_f = C.EXTERNAL / "pay_duration.csv"
    if pd_f.exists():
        d = U.lower_cols(pd.read_csv(pd_f, dtype={"gvkey": str}))
        d["gvkey"] = d["gvkey"].str.zfill(6)
        d["year"] = d["year"].astype(int) + (1 if C.PAY_DURATION_YEAR == "prev" else 0)
        c = c.merge(d[["gvkey", "year", "duration"]].rename(columns={"year": "YEAR", "duration": "PAY_DUR"})
                    .drop_duplicates(["gvkey", "YEAR"]), on=["gvkey", "YEAR"], how="left")
    return c


if __name__ == "__main__":
    build()
