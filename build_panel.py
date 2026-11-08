"""
Step 04 - firm-quarter panel for Table 6 (likelihood of issuing a capex forecast).

  TREAT_{i,a}       = 1 if firm i issues a (sample) capex forecast in calendar quarter a
  NOISE_SIGNAL_{a-1} = 1 if |noise| / |signal| of quarter-end Q is above the median, where
                      Q_{i,q} = b * MFFLOW_{i,q} + firm FE + year-qtr FE + e   (Dessaint et al. 2018)
                      noise = |b_hat * MFFLOW|, signal = |e_hat|                (D28)
  controls at a-1   : LEV, SIZE, TANG, ROA, NEG_ROA, ROA_VOL
  NOISE_SIGNAL_LO/HI_ERC = NOISE_SIGNAL x 1{industry ERC below/above the Panel C median}
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
import utils as U
from build_capex_sample import firm_industry, load_funda, load_fundq
from hdfe import hdfe_ols


def build() -> pd.DataFrame:
    q = load_fundq()
    q = q[q["datadate"].notna()].copy()
    q["qid"] = U.qid(q["datadate"]).astype(int)
    q = q.sort_values(["gvkey", "qid", "datadate"]).drop_duplicates(["gvkey", "qid"], keep="last")
    # gvkey -> permno at the fiscal-quarter end
    ccm = U.lower_cols(U.load("ccm", C.RAW))
    ccm["gvkey"] = ccm["gvkey"].astype(str).str.zfill(6)
    ccm["linkdt"] = U.to_dt(ccm["linkdt"]).fillna(pd.Timestamp("1900-01-01"))
    ccm["linkenddt"] = U.to_dt(ccm["linkenddt"]).fillna(pd.Timestamp("2099-12-31"))
    ccm["prio"] = ccm["linkprim"].map({"P": 0, "C": 1}).fillna(2)
    m = q[["gvkey", "datadate"]].merge(ccm[["gvkey", "lpermno", "linkdt", "linkenddt", "prio"]], on="gvkey")
    m = m[(m["datadate"] >= m["linkdt"]) & (m["datadate"] <= m["linkenddt"])]
    m = m.sort_values("prio").drop_duplicates(["gvkey", "datadate"])
    q = q.merge(m[["gvkey", "datadate", "lpermno"]].rename(columns={"lpermno": "permno"}),
                on=["gvkey", "datadate"], how="inner")
    q["permno"] = pd.to_numeric(q["permno"]).astype(int)

    at = q["atq"].where(q["atq"] > 0)
    q["Q"] = (q["atq"] - q["ceqq"] + q["mvq"]) / at
    q["LEV"] = (q["dlttq"].fillna(0) + q["dlcq"].fillna(0)) / at
    q["SIZE"] = np.log(q["mvq"].where(q["mvq"] > 0))
    q["TANG"] = q["ppentq"] / at
    q["ROA"] = q["ibq"] / at
    q["NEG_ROA"] = (q["ROA"] < 0).astype(float).where(q["ROA"].notna())
    q = q.sort_values(["gvkey", "qid"])
    q["ROA_VOL"] = q.groupby("gvkey")["ROA"].transform(
        lambda s: s.rolling(C.ROA_VOL_MIN_Q, min_periods=C.ROA_VOL_MIN_Q).std())

    # noise-to-signal decomposition of Q
    mf = U.load("mf_pressure")[["permno", "qid", "MFFLOW"]]
    q = q.merge(mf, on=["permno", "qid"], how="left")
    reg = q.dropna(subset=["Q", "MFFLOW"]).copy()
    reg["Q"] = U.winsorize(reg["Q"])
    r = hdfe_ols(reg, "Q", ["MFFLOW"], ["gvkey", "qid"], cluster="gvkey", keep_resid=True)
    reg["NOISE"] = (r.coef["MFFLOW"] * reg["MFFLOW"]).abs()
    reg["SIGNAL"] = r.resid.reindex(reg.index).abs()
    reg["NS"] = reg["NOISE"] / reg["SIGNAL"].where(reg["SIGNAL"] > 0)
    reg["NOISE_SIGNAL"] = (reg["NS"] > reg["NS"].median()).astype(float).where(reg["NS"].notna())
    q = q.merge(reg[["gvkey", "qid", "NOISE_SIGNAL", "NS"]], on=["gvkey", "qid"], how="left")
    print(f"[panel] Q on MFFLOW: b = {r.coef['MFFLOW']:.4f} (se {r.se['MFFLOW']:.4f}), N = {r.nobs:,}")

    # lag explanatory variables by one quarter (consecutive quarters only)
    lagv = ["NOISE_SIGNAL", "LEV", "SIZE", "TANG", "ROA", "NEG_ROA", "ROA_VOL"]
    lag = q[["gvkey", "qid", *lagv]].copy()
    lag["qid"] += 1
    q = q[["gvkey", "permno", "qid"]].merge(lag, on=["gvkey", "qid"], how="left")

    cap = U.load("capex_sample")[["gvkey", "qid"]].drop_duplicates()
    cap["TREAT"] = 1
    q = q.merge(cap, on=["gvkey", "qid"], how="left")
    q["TREAT"] = q["TREAT"].fillna(0).astype(int)
    lo, hi = U.label_to_qid(C.PANEL_FIRST_Q), U.label_to_qid(C.PANEL_LAST_Q)
    q = q[(q["qid"] >= lo) & (q["qid"] <= hi)].copy()
    q["YQ"] = (q["qid"] // 4) * 10 + q["qid"] % 4 + 1

    # ERC split, using the same threshold as Table 5 Panel C (median across capex-sample obs)
    funda = load_funda()
    q["IND"] = firm_industry(q["gvkey"].astype(str), funda).values
    if U.exists("industry_erc"):
        erc = U.load("industry_erc").rename(columns={"sic2": "IND"})
        q = q.merge(erc, on="IND", how="left")
        thr = U.load("capex_sample")["ERC"].median()
        lo_erc = (q["ERC"] <= thr).astype(float).where(q["ERC"].notna())
        q["NOISE_SIGNAL_LO_ERC"] = q["NOISE_SIGNAL"] * lo_erc
        q["NOISE_SIGNAL_HI_ERC"] = q["NOISE_SIGNAL"] * (1 - lo_erc)
    for v in ("LEV", "SIZE", "TANG", "ROA", "ROA_VOL"):
        q[v] = U.winsorize(q[v])
    U.save(q, "forecast_panel")
    print(f"[panel] firm-quarters {len(q):,}; TREAT mean {q['TREAT'].mean():.4f} (paper 0.07)")
    return q


if __name__ == "__main__":
    build()
