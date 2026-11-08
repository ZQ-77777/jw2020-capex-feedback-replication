"""
Step 02a - mutual-fund flow-driven price pressure (Edmans, Goldstein & Jiang 2012, JF).

For stock i in quarter q:
    MFFLOW_{i,q} = sum_{j: F_{j,q} <= -5%} F_{j,q} * Shares_{i,j,q-1} * Prc_{i,q-1}  /  DolVol_{i,q}
  F_{j,q}   = [TNA_{j,q} - TNA_{j,q-1}(1+R_{j,q})] / TNA_{j,q-1}   (fund = WFICN, share classes summed)
  Shares    = Thomson s12 holdings at the end of q-1 (hypothetical sale proportional to holdings)
  DolVol    = CRSP dollar volume in quarter q (msf vol is in HUNDREDS of shares)
MFFLOW <= 0; OUTFLOW = -MFFLOW >= 0 (more selling pressure = larger).
MF_OF_{i,q} = 1 if OUTFLOW_{i,q} > median OUTFLOW (D21).  The capex sample uses MF_OF of q-1
("periods that follow mutual fund outflows").
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
import utils as U


def fund_quarter_flows(tna: pd.DataFrame, link1: pd.DataFrame) -> pd.DataFrame:
    t = U.lower_cols(tna)
    t["caldt"] = U.to_dt(t["caldt"]) + pd.offsets.MonthEnd(0)
    t = t.merge(U.lower_cols(link1).dropna(subset=["wficn"]), on="crsp_fundno", how="inner")
    t = t.sort_values(["crsp_fundno", "caldt"])
    t["mtna"] = pd.to_numeric(t["mtna"], errors="coerce")
    t["mret"] = pd.to_numeric(t["mret"], errors="coerce")
    t["w"] = t.groupby("crsp_fundno")["mtna"].shift(1)          # lagged-TNA weights for returns
    t["w"] = t["w"].fillna(t["mtna"])
    t["wr"] = t["w"] * t["mret"]
    m = t.groupby(["wficn", "caldt"]).agg(tna=("mtna", "sum"), wr=("wr", "sum"), w=("w", "sum")).reset_index()
    m["ret"] = m["wr"] / m["w"]
    m["qid"] = U.qid(m["caldt"]).astype(int)
    m = m.sort_values(["wficn", "caldt"])
    q = m.groupby(["wficn", "qid"]).agg(
        tna=("tna", "last"), n=("ret", "count"),
        ret=("ret", lambda r: np.prod(1 + r.values) - 1)).reset_index()
    q = q[q["n"] == 3]                                            # full quarter of returns
    q = q.sort_values(["wficn", "qid"])
    q["tna_lag"] = q.groupby("wficn")["tna"].shift(1)
    q["qid_lag"] = q.groupby("wficn")["qid"].shift(1)
    q = q[(q["qid_lag"] == q["qid"] - 1) & (q["tna_lag"] > 0)]
    q["flow"] = (q["tna"] - q["tna_lag"] * (1 + q["ret"])) / q["tna_lag"]
    return q[["wficn", "qid", "flow", "tna_lag"]]


def build() -> pd.DataFrame:
    flows = fund_quarter_flows(U.load("mf_tna", C.RAW), U.load("mflink1", C.RAW))
    ext = flows[flows["flow"] <= C.MF_OUTFLOW_CUTOFF]

    h = U.lower_cols(U.load("s12", C.RAW))
    h["rdate"], h["fdate"] = U.to_dt(h["rdate"]), U.to_dt(h["fdate"])
    h = h.sort_values("fdate").drop_duplicates(["fundno", "rdate", "cusip"], keep="last")
    l2 = U.lower_cols(U.load("mflink2", C.RAW))
    l2["fdate"] = U.to_dt(l2["fdate"])
    h = h.merge(l2[["fdate", "fundno", "wficn"]].drop_duplicates(["fdate", "fundno"]),
                on=["fdate", "fundno"], how="inner")
    h["qid"] = U.qid(h["rdate"]).astype(int) + 1                  # flow quarter = holdings quarter + 1
    h = h.merge(ext[["wficn", "qid", "flow"]], on=["wficn", "qid"], how="inner")
    h = U.permno_from_ncusip(h, U.load("msenames", C.RAW), "cusip", "rdate").dropna(subset=["permno"])

    msf = U.lower_cols(U.load("msf", C.RAW))
    msf["date"] = U.to_dt(msf["date"])
    msf["qid"] = U.qid(msf["date"]).astype(int)
    msf["prc"] = pd.to_numeric(msf["prc"], errors="coerce").abs()
    msf["dvol"] = pd.to_numeric(msf["vol"], errors="coerce") * 100 * msf["prc"]
    qend = msf.sort_values("date").groupby(["permno", "qid"]).agg(
        prc_end=("prc", "last"), dvol=("dvol", "sum")).reset_index()
    prc_lag = qend[["permno", "qid", "prc_end"]].copy()
    prc_lag["qid"] += 1                                           # price at end of q-1
    h["permno"] = h["permno"].astype(int)
    h = h.merge(prc_lag, on=["permno", "qid"], how="left")
    h["hyp"] = h["flow"] * pd.to_numeric(h["shares"], errors="coerce") * h["prc_end"]
    num = h.groupby(["permno", "qid"])["hyp"].sum().rename("hyp").reset_index()

    out = qend[["permno", "qid", "dvol"]].merge(num, on=["permno", "qid"], how="left")
    out["hyp"] = out["hyp"].fillna(0.0)
    out = out[out["dvol"] > 0]
    out["MFFLOW"] = out["hyp"] / out["dvol"]
    out["OUTFLOW"] = -out["MFFLOW"]
    lo, hi = U.label_to_qid(C.PANEL_FIRST_Q) - 1, U.label_to_qid(C.PANEL_LAST_Q)
    ref = out[(out["qid"] >= lo) & (out["qid"] <= hi)]["OUTFLOW"]
    med = ref.median()
    out["MF_OF"] = (out["OUTFLOW"] > med).astype(int)
    print(f"[mf] firm-quarters {len(out):,}; share with any extreme-outflow holder "
          f"{(out['hyp'] < 0).mean():.3f}; median OUTFLOW {med:.6f}; MF_OF mean {out['MF_OF'].mean():.3f}")
    U.save(out[["permno", "qid", "MFFLOW", "OUTFLOW", "MF_OF"]], "mf_pressure")
    return out


if __name__ == "__main__":
    build()
