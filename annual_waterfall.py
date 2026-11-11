"""
Annual sample waterfall (年度样本筛选流程表): where, year by year, does our sample part from the paper's?

    python annual_waterfall.py      # -> output/annual_waterfall.md / annual_waterfall.csv

Re-traces the steps of build_capex_sample.build() by announcement year and checks that the yearly counts add
up to output/sample_waterfall.csv.  Steps (k):
  S0  I/B/E/S raw records       annual capex guidance rows (US firm, USD), announced 2002-2016
  S1  one per announcement      nearest fiscal year, latest revision, positive forecast
  S2  one per firm-quarter      first forecast of each (IBES ticker, calendar quarter)            (D6)
  S3  Compustat match           IBES -> CRSP -> CCM link and actual capex of the forecast year
  S4  CRSP market reaction      all five daily returns in [-2, 2]
  S5  not with an earnings fcst no earnings-type guidance on the same day                          (D9)
  Final                         S5 for 2003-2015 = Table 1 Panel B
Retention rate  R(t,k) = N(t,k) / N(t,k-1).

The paper reports only its final count by year (Table 1 Panel B) and its step totals for all years together,
so its yearly retention rates cannot be computed.  Two comparisons are still possible:
  (a) paper final(t) / our N(t,k): the share of our step-k forecasts that the paper's final sample would keep.
      If this ratio is flat across years at step k, the paper's later steps treat all years alike and the
      year-specific gap arises at or before k; where it bends, a step is acting differently by year.
  (b) the step at which our yearly profile already departs from the paper's: year shares at each step.
Sample characteristics only; no regression is run.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import build_capex_sample as B
import config as C
import paper_targets as P
import utils as U

STEPS = ["S0 I/B/E/S raw", "S1 one per announcement", "S2 one per firm-quarter", "S3 Compustat match",
         "S4 CRSP reaction", "S5 not with earnings fcst"]
LABEL_ZH = {"S0 I/B/E/S raw": "I/B/E/S 原始记录", "S1 one per announcement": "每次公告一条",
            "S2 one per firm-quarter": "公司-季度去重", "S3 Compustat match": "匹配 Compustat",
            "S4 CRSP reaction": "有 CRSP 市场反应", "S5 not with earnings fcst": "非盈利预测同日（最终）"}


def trace() -> dict[str, pd.Series]:
    """Same operations as build() up to w3, returning the announcement year of every surviving record."""
    years = {}
    yr = lambda d: d["anndats"].dt.year
    g = B.clean_guidance()
    raw = g[(g["measure"] == C.MEASURE_CAPEX) & (g["pdicity"] == C.PDICITY_ANNUAL)]
    raw = raw[(raw["anndats"] >= C.FCST_FIRST) & (raw["anndats"] <= C.FCST_LAST)]
    years[STEPS[0]] = yr(raw)

    c = B.classify(B.annual_forecasts(g, C.MEASURE_CAPEX))
    c = c[(c["anndats"] >= C.FCST_FIRST) & (c["anndats"] <= C.FCST_LAST)]
    years[STEPS[1]] = yr(c)
    c["qid"] = U.qid(c["anndats"]).astype(int)
    if C.ONE_PER_FIRM_QUARTER and C.COLLAPSE_AT_START:
        c = c.sort_values(["ticker", "qid", "anndats", "anntims"]).drop_duplicates(
            ["ticker", "qid"], keep=C.ONE_PER_FIRM_QUARTER).reset_index(drop=True)
    years[STEPS[2]] = yr(c)

    funda = B.load_funda()
    c = U.link_ibes_permno(c, U.load("ibcrsphist", C.RAW), "anndats")
    c = U.link_permno_gvkey(c, U.load("ccm", C.RAW), "anndats").dropna(subset=["permno", "gvkey"])
    c["gvkey"] = c["gvkey"].astype(str).str.zfill(6)
    if C.SHRCD_FILTER:
        c = U.shrcd_at(c, U.load("msenames", C.RAW), "anndats")
        c = c[c["shrcd"].isin(C.SHRCD_FILTER)]
    c["ym"] = c["prd_end"].dt.year * 100 + c["prd_end"].dt.month
    c = c.merge(funda[["gvkey", "ym", "capx"]].rename(columns={"capx": "CAPEX_ACT"}), on=["gvkey", "ym"], how="left")
    c = c.dropna(subset=["permno", "gvkey", "CAPEX_ACT"]).reset_index(drop=True)
    years[STEPS[3]] = yr(c)

    dsi = U.lower_cols(U.load("dsi", C.RAW))
    cal = U.TradingCalendar(dsi["date"])
    daily = U.daily_with_tidx(U.load("dsf", C.RAW), dsi, cal)
    c["eid"] = np.arange(len(c))
    c["t0"] = U.day0(c, cal)
    c["CAR"] = c["eid"].map(U.car(c, daily, *C.CAR_WIN, min_obs=C.MIN_RET_OBS))
    c = c.dropna(subset=["CAR"]).reset_index(drop=True)
    years[STEPS[4]] = yr(c)

    def not_concurrent(c, measures):
        eps = g[g["measure"] == C.MEASURE_EPS][["ticker", "anndats"]]
        extra = [m for m in measures if m != C.MEASURE_EPS]
        if extra:
            ge = U.lower_cols(U.load("guidance_earn", C.RAW))
            ge["ticker"] = ge["ticker"].astype(str).str.upper().str.strip()
            ge["anndats"] = U.to_dt(ge["anndats"])
            ge = ge[ge["measure"].astype(str).str.upper().str.strip().isin(extra)]
            eps = pd.concat([eps, ge[["ticker", "anndats"]]], ignore_index=True)
        eps = eps.dropna().drop_duplicates()
        m = c[["eid", "ticker", "anndats"]].merge(eps.rename(columns={"anndats": "eps_dt"}), on="ticker")
        hit = m.loc[(m["anndats"] - m["eps_dt"]).dt.days.abs() <= C.EPS_CONCURRENT_DAYS, "eid"].unique()
        return c[~c["eid"].isin(hit)]

    years[STEPS[5]] = yr(not_concurrent(c, C.CONCURRENT_MEASURES))
    years["S5 (EPS only)"] = yr(not_concurrent(c, (C.MEASURE_EPS,)))
    return years


def main():
    ys = trace()
    yrs = list(range(2002, 2017))
    n = pd.DataFrame({k: v.value_counts().reindex(yrs, fill_value=0) for k, v in ys.items()})
    n.index.name = "year"
    n["paper final"] = [P.T1B.get(y, (np.nan,))[0] for y in yrs]

    # consistency with the build's waterfall
    wf = pd.read_csv(C.OUT / "sample_waterfall.csv").set_index("step")["ours"]
    checks = {"S1 one per announcement": "w0_ibes_capex_forecasts", "S2 one per firm-quarter": "w0b_one_per_firm_quarter",
              "S3 Compustat match": "w1_matched_compustat", "S4 CRSP reaction": "w2_with_car",
              "S5 not with earnings fcst": "w3_not_concurrent_eps"}
    bad = [f"{k}: {int(n[k].sum()):,} vs {int(wf[v]):,}" for k, v in checks.items() if v in wf and int(n[k].sum()) != int(wf[v])]
    final = U.load("capex_sample")["anndats"].dt.year.value_counts()
    fin_ok = all(int(n.loc[y, STEPS[5]]) == int(final.get(y, 0)) for y in range(2003, 2016))
    if bad or not fin_ok:
        print("[annual] WARNING: trace does not reproduce the build:", bad, "final by year ok:", fin_ok)

    # retention rates
    r = pd.DataFrame(index=n.index)
    for a, b in zip(STEPS[:-1], STEPS[1:]):
        r[f"R {b.split()[0]}"] = n[b] / n[a].replace(0, np.nan)
    r["R S5 (EPS only)"] = n["S5 (EPS only)"] / n[STEPS[4]].replace(0, np.nan)

    # (a) paper final / ours at each step
    span = n.loc[2003:2015]
    imp = pd.DataFrame({f"paper/{k.split()[0]}": span["paper final"] / span[k].replace(0, np.nan) for k in STEPS})
    # (b) year shares at each step vs paper final
    sh = pd.DataFrame({k.split()[0]: span[k] / span[k].sum() for k in STEPS})
    sh["paper"] = span["paper final"] / span["paper final"].sum()
    early = (span.index <= 2009)
    early_share = pd.Series({k: sh.loc[early, k].sum() for k in sh})

    # totals vs the paper's waterfall (all years)
    tot = pd.DataFrame({"ours": n[STEPS].sum()})
    tot["paper"] = [np.nan, np.nan, np.nan, 40785, 36900, 19427]

    md = ["# Annual sample waterfall\n",
          "Counts by announcement year. R(t,k) = N(t,k)/N(t,k−1). Paper: final counts by year (Table 1 Panel B) "
          "and step totals only.\n",
          "\n## Counts\n", n.astype("Int64").to_markdown(),
          "\n\n## Retention rates R(t,k)\n", r.to_markdown(floatfmt=".3f"),
          "\n\n## (a) Paper final / our count at each step, 2003–2015\n", imp.to_markdown(floatfmt=".3f"),
          "\n\n## (b) Share of 2003–2009 in each step (paper final: "
          f"{early_share['paper']:.3f})\n", early_share.to_frame("2003–2009 share").to_markdown(floatfmt=".3f"),
          "\n\n## Totals\n", tot.to_markdown(floatfmt=",.0f"),
          f"\n\nTrace reproduces build: {'yes' if not bad and fin_ok else 'NO — ' + '; '.join(bad)}\n"]
    C.OUT.mkdir(parents=True, exist_ok=True)
    n.to_csv(C.OUT / "annual_waterfall.csv")
    r.to_csv(C.OUT / "annual_retention.csv")
    imp.to_csv(C.OUT / "annual_paper_ratio.csv")
    (C.OUT / "annual_waterfall.md").write_text("\n".join(md), encoding="utf-8")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(n.to_string()); print(r.round(3).to_string()); print(imp.round(3).to_string()); print(early_share.round(3))
    print(f"saved {C.OUT / 'annual_waterfall.md'}")


if __name__ == "__main__":
    main()
