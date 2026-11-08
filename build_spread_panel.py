"""
Step 03 - event-day panel of bid-ask spreads (Table 5 Panel E1, Figure 1).

Unit: event x day, days [-10,10] around capex forecasts (CAPEX=1) and EPS forecasts (CAPEX=0).
  EVENT    = 1 for days [-2,2], 0 for [-10,-3] U [3,10]
  SPREAD   = (ask-bid)/midpoint, closing quotes from crsp.dsf, in percent (D17)
  SIZE, TURNOVER, RETVOL measured over the pre-announcement days [-10,-3]
  MF_OF    = above-median mutual-fund outflow pressure in the previous quarter
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
import utils as U
from build_capex_sample import clean_guidance


def build() -> pd.DataFrame:
    dsi = U.lower_cols(U.load("dsi", C.RAW))
    cal = U.TradingCalendar(dsi["date"])
    daily = U.daily_with_tidx(U.load("dsf", C.RAW), dsi, cal)

    cap = U.load("capex_sample")[["permno", "gvkey", "anndats", "qid", "t0"]].copy()
    cap["CAPEX"] = 1

    g = clean_guidance()
    e = g[g["measure"] == C.MEASURE_EPS][["ticker", "anndats"]].drop_duplicates()
    e = e[(e["anndats"].dt.year >= 2003) & (e["anndats"].dt.year < C.DROP_FROM_YEAR)]
    e = U.link_ibes_permno(e, U.load("ibcrsphist", C.RAW), "anndats")
    e = U.link_permno_gvkey(e, U.load("ccm", C.RAW), "anndats").dropna(subset=["permno", "gvkey"])
    e["gvkey"] = e["gvkey"].astype(str).str.zfill(6)
    e["qid"] = U.qid(e["anndats"]).astype(int)
    e["t0"] = U.day0(e, cal)
    e = e.drop_duplicates(["permno", "t0"])
    e["CAPEX"] = 0

    ev = pd.concat([cap, e[cap.columns]], ignore_index=True)
    ev["eid"] = np.arange(len(ev))
    w = U.event_window(ev, daily, C.SPREAD_PRE_WIN[0], C.SPREAD_POST_WIN[1], ["spread", "mv", "turn", "ret"])
    pre = w[w["k"].between(*C.SPREAD_PRE_WIN)].groupby("eid").agg(
        SIZE=("mv", lambda x: np.log(x.mean()) if x.mean() > 0 else np.nan),
        TURNOVER=("turn", "mean"), RETVOL=("ret", "std"))
    p = w.dropna(subset=["spread"]).merge(pre, left_on="eid", right_index=True, how="left")
    p = p.merge(ev[["eid", "gvkey", "anndats", "qid", "CAPEX"]], on="eid")
    p["EVENT"] = p["k"].between(*C.SPREAD_EVT_WIN).astype(int)
    p["SPREAD"] = U.winsorize(p["spread"])
    p["YQ"] = p["anndats"].dt.year * 10 + p["anndats"].dt.quarter
    if U.exists("mf_pressure"):
        mf = U.load("mf_pressure")
        mf = mf.assign(qid=mf["qid"] + 1)[["permno", "qid", "MF_OF"]]
        p["permno"] = p["permno"].astype(int)
        p = p.merge(mf, on=["permno", "qid"], how="left")
    for v in ("SIZE", "TURNOVER", "RETVOL"):
        p[v] = U.winsorize(p[v])
    U.save(p, "spread_panel")
    print(f"[spread] event-days {len(p):,} (capex {p['CAPEX'].sum():,}); events {p['eid'].nunique():,}")
    return p


if __name__ == "__main__":
    build()
