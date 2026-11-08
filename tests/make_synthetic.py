"""
Synthetic data with EXACTLY the schemas returned by pull_wrds.py, so the whole pipeline can be
tested without WRDS.  A known effect is planted:

    CAPEX_ADJ (point forecasts) = 3.0 * CAR_z * 1{event raises spreads} + noise

so Table 2 should show a positive CAR coefficient and Table 3 should show it only in the
"Higher spreads" column.  Numbers are NOT meant to resemble the paper's magnitudes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C  # noqa: E402
import utils as U   # noqa: E402

BETA_TRUE = 3.0
SICS = [1311, 1381, 2086, 2834, 2911, 3571, 3674, 3711, 4512, 4911, 5812, 7372, 4813, 2621]


def bday_on_or_after(days: pd.DatetimeIndex, d):
    i = days.searchsorted(pd.Timestamp(d))
    return days[min(i, len(days) - 1)]


def make(n_firms=250, seed=7):
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(C.PULL_START, C.PULL_END)
    T = len(days)
    mkt = rng.normal(0.0003, 0.01, T)
    dsi = pd.DataFrame({"date": days, "sprtrn": mkt, "vwretd": mkt})

    firms = pd.DataFrame({"i": np.arange(n_firms)})
    firms["gvkey"] = [f"{100000 + i}" for i in firms["i"]]
    firms["permno"] = 10000 + firms["i"]
    firms["ticker"] = [f"T{i:04d}" for i in firms["i"]]
    firms["ncusip"] = [f"{i:06d}10" for i in firms["i"]]
    firms["sic"] = rng.choice(SICS, n_firms)
    firms["K"] = np.exp(rng.normal(4.5, 1.2, n_firms))          # capex scale, $ millions

    # ---------------------------------------------------------------- daily stock file (arrays per firm)
    RET, PRC, SHR, VOL, BID, ASK = {}, {}, {}, {}, {}, {}
    for _, f in firms.iterrows():
        beta, sd = rng.uniform(0.5, 1.5), rng.uniform(0.01, 0.03)
        ret = beta * mkt + rng.normal(0, sd, T)
        prc = rng.uniform(15, 80) * np.cumprod(1 + ret)
        shr = rng.uniform(2e4, 5e5) * np.ones(T)
        s = rng.uniform(0.0005, 0.004) * np.exp(rng.normal(0, 0.15, T))
        p = f.permno
        RET[p], PRC[p], SHR[p] = ret, prc, shr
        VOL[p] = shr * 1000 * rng.uniform(0.002, 0.012, T)
        BID[p], ASK[p] = prc * (1 - s / 2), prc * (1 + s / 2)
    tix = {d: k for k, d in enumerate(days)}

    def last_before(p, d):
        k = days.searchsorted(pd.Timestamp(d), side="right") - 1
        return float(PRC[p][k]), float(SHR[p][k]) / 1000.0

    # ---------------------------------------------------------------- quarterly accounting + EAs
    fq_rows = []
    for _, f in firms.iterrows():
        eps = 0.5
        for qe in pd.date_range("1999-03-31", "2017-12-31", freq="QE"):
            eps = 0.7 * eps + 0.15 + rng.normal(0, 0.25)
            rdq = bday_on_or_after(days, qe + pd.Timedelta(days=int(rng.integers(25, 45))))
            prc, sh = last_before(f.permno, qe)
            at = f.K * 10 * rng.uniform(0.9, 1.1)
            fq_rows.append(dict(gvkey=f.gvkey, datadate=qe, fyearq=qe.year, fqtr=qe.quarter, fyr=12, rdq=rdq,
                                epspxq=eps, ajexq=1.0, atq=at, ibq=at * rng.normal(0.02, 0.02), niq=at * rng.normal(0.02, 0.02),
                                saleq=at * 0.3, cshoq=sh, prccq=prc, ceqq=at * 0.4, dlttq=at * rng.uniform(0.1, 0.3),
                                dlcq=at * 0.05, ppentq=at * rng.uniform(0.2, 0.4), curcdq="USD"))
    fundq = pd.DataFrame(fq_rows)

    # ---------------------------------------------------------------- guidance + planted effect
    g_rows, cpx_events = [], []
    for _, f in firms.iterrows():
        q4 = fundq[(fundq.gvkey == f.gvkey) & (fundq.fqtr == 4)].set_index("fyearq")["rdq"]
        for y in range(2002, 2017):
            if rng.random() > 0.75:
                continue
            dates = [q4.get(y - 1) if rng.random() < 0.55 else
                     bday_on_or_after(days, pd.Timestamp(f"{y}-03-01") + pd.Timedelta(days=int(rng.integers(0, 110))))]
            if rng.random() < 0.3:
                dates.append(bday_on_or_after(days, pd.Timestamp(f"{y}-08-01") + pd.Timedelta(days=int(rng.integers(0, 60)))))
            Fy = f.K * np.exp(rng.normal(0, 0.1))
            for j, d in enumerate(dates):
                u = rng.random()
                ftype = "point" if u < 0.55 else "range" if u < 0.90 else "other"
                v1 = Fy * (0.95 if ftype == "range" else 1.0)
                v2 = Fy * 1.05 if ftype == "range" else np.nan
                g_rows.append(dict(ticker=f.ticker, cusip=f.ncusip, cname=f"FIRM {f.i}", measure="CPX", pdicity="ANN",
                                   anndats=d, anntims=rng.choice(["08:00:00", "16:30:00"]), prd_yr=y, prd_mon=12,
                                   val_1=v1, val_2=v2, mean_at_date=np.nan,
                                   range_desc={"point": "PT", "range": "RG", "other": "OPEN"}[ftype],
                                   units="M", curr="USD", usfirm=1, action="N"))
                hs = rng.random() < 0.5
                cpx_events.append(dict(permno=f.permno, gvkey=f.gvkey, y=y, d=d, first=(j == 0), hs=hs, F=Fy))
                if rng.random() < 0.45:   # concurrent EPS guidance -> must be dropped
                    g_rows.append(dict(ticker=f.ticker, measure="EPS", pdicity="QTR", anndats=d, prd_yr=y, prd_mon=12,
                                       val_1=0.5, val_2=np.nan, units="", curr="USD", usfirm=1, anntims="08:00:00"))
            if rng.random() < 0.4:        # stand-alone sales guidance for the same fiscal year
                d = bday_on_or_after(days, pd.Timestamp(f"{y}-05-15") + pd.Timedelta(days=int(rng.integers(0, 60))))
                g_rows.append(dict(ticker=f.ticker, measure="SAL", pdicity="ANN", anndats=d, prd_yr=y, prd_mon=12,
                                   val_1=f.K * 3, val_2=np.nan, units="M", curr="USD", usfirm=1, anntims="08:00:00"))
            for _ in range(2):            # other EPS guidance
                d = bday_on_or_after(days, pd.Timestamp(f"{y}-01-01") + pd.Timedelta(days=int(rng.integers(0, 360))))
                g_rows.append(dict(ticker=f.ticker, measure="EPS", pdicity="ANN", anndats=d, prd_yr=y, prd_mon=12,
                                   val_1=2.0, val_2=np.nan, units="", curr="USD", usfirm=1, anntims="08:00:00"))
    guidance = pd.DataFrame(g_rows)
    ev = pd.DataFrame(cpx_events)

    # widen spreads in [-2,2] for 'hs' events and compute the realised CAR of each event
    cars = []
    for _, e in ev.iterrows():
        t0, p = tix[e.d], e.permno
        sl = slice(max(t0 - 2, 0), t0 + 3)
        cars.append((RET[p][sl] - mkt[sl]).sum() * 100)
        if e.hs:
            mid, half = (BID[p][sl] + ASK[p][sl]) / 2, (ASK[p][sl] - BID[p][sl]) / 2 * 2.5
            BID[p][sl], ASK[p][sl] = mid - half, mid + half
    dsf = pd.concat([pd.DataFrame({"permno": p, "date": days, "ret": RET[p], "prc": PRC[p], "vol": VOL[p],
                                   "shrout": SHR[p], "bid": BID[p], "ask": ASK[p]}) for p in firms.permno],
                    ignore_index=True)
    ev["CAR"] = cars
    ev["CARz"] = (ev["CAR"] - ev["CAR"].mean()) / ev["CAR"].std()
    ev["planted"] = BETA_TRUE * ev["CARz"] * ev["hs"]
    first = ev[ev["first"]].set_index(["gvkey", "y"])

    # ---------------------------------------------------------------- annual accounting
    fa_rows = []
    for _, f in firms.iterrows():
        for y in range(1999, 2019):
            at = f.K * 10 * rng.uniform(0.95, 1.05)
            key = (f.gvkey, y)
            if key in first.index:
                e = first.loc[key]
                capx = e.F * (1 + (e.planted + rng.normal(0, 15)) / 100)
            else:
                capx = f.K * np.exp(rng.normal(0, 0.1))
            prev = (f.gvkey, y - 1)
            mk = first.loc[prev, "planted"] if prev in first.index else 0.0
            oancf = at * (0.10 + 0.004 * mk + rng.normal(0, 0.03))
            prc, sh = last_before(f.permno, f"{y}-12-31")
            fa_rows.append(dict(gvkey=f.gvkey, datadate=pd.Timestamp(f"{y}-12-31"), fyear=y, fyr=12, capx=capx,
                                at=at, ib=oancf * 0.6, ni=oancf * 0.55, oancf=oancf, csho=sh, prcc_f=prc,
                                ceq=at * 0.4, dltt=at * 0.2, dlc=at * 0.05, ppent=at * 0.3, sich=f.sic, curcd="USD"))
    funda = pd.DataFrame(fa_rows)

    # ---------------------------------------------------------------- links, names, monthly file
    far = pd.Timestamp("2099-12-31")
    ibl = pd.DataFrame({"ticker": firms.ticker, "permno": firms.permno, "ncusip": firms.ncusip,
                        "sdate": pd.Timestamp("1990-01-01"), "edate": far, "score": 1})
    ccm = pd.DataFrame({"gvkey": firms.gvkey, "lpermno": firms.permno, "lpermco": firms.permno, "linktype": "LC",
                        "linkprim": "P", "linkdt": pd.Timestamp("1990-01-01"), "linkenddt": pd.NaT})
    company = firms[["gvkey", "sic"]].assign(state=rng.choice(["TX", "CA", "NY", "IL", "OH", "PA"], n_firms))
    names = pd.DataFrame({"permno": firms.permno, "namedt": pd.Timestamp("1990-01-01"), "nameendt": far,
                          "ncusip": firms.ncusip, "shrcd": 11, "exchcd": 1})
    dsf["ym"] = dsf.date.dt.to_period("M")
    msf = dsf.groupby(["permno", "ym"]).agg(date=("date", "last"), prc=("prc", "last"), vol=("vol", "sum"),
                                            shrout=("shrout", "last"),
                                            ret=("ret", lambda r: np.prod(1 + r) - 1)).reset_index(drop=False)
    msf["vol"] = msf["vol"] / 100.0                      # CRSP msf volume is in hundreds of shares
    msf = msf.drop(columns="ym")
    dsf = dsf.drop(columns="ym")

    ea = fundq[(fundq.rdq >= C.FCST_FIRST) & (fundq.rdq <= C.FCST_LAST)][["gvkey", "rdq"]]
    ea = ea.merge(firms[["gvkey", "permno"]], on="gvkey")
    rows = []
    dsf_i = dsf.set_index("permno")
    for p, grp in ea.groupby("permno"):
        dd = dsf_i.loc[p, ["date", "ret"]]
        for _, r in grp.iterrows():
            w = dd[(dd.date >= r.rdq - pd.Timedelta(days=7)) & (dd.date <= r.rdq + pd.Timedelta(days=7))]
            rows.append(w.assign(gvkey=r.gvkey, rdq=r.rdq, permno=p))
    ea_daily = pd.concat(rows, ignore_index=True).merge(dsi[["date", "sprtrn"]], on="date")

    ins = []
    for _, f in firms.iterrows():
        n = rng.poisson(12 * 15)
        d = pd.to_datetime(rng.integers(pd.Timestamp("2002-01-01").value // 10**9,
                                        pd.Timestamp("2016-12-31").value // 10**9, n), unit="s").normalize()
        ins.append(pd.DataFrame({"cusip6": f.ncusip[:6], "cusip2": f.ncusip[6:], "trandate": d,
                                 "trancode": rng.choice(["P", "S"], n), "cleanse": "R", "acqdisp": "A",
                                 "personid": rng.integers(1, 50, n)}))
    insider = pd.concat(ins, ignore_index=True)

    # ---------------------------------------------------------------- mutual funds
    months = pd.date_range("2001-06-30", "2016-12-31", freq="ME")
    tna_rows, l2_rows, s12_rows = [], [], []
    for j in range(40):
        tna = rng.uniform(200, 3000)
        holds = rng.choice(firms.index, 40, replace=False)
        for m in months:
            r = rng.normal(0.006, 0.04)
            flow = rng.normal(0, 0.035) if m.month % 3 else rng.normal(0, 0.035)
            tna = max(tna * (1 + r) + tna * flow, 5)
            tna_rows.append(dict(crsp_fundno=j + 1, caldt=m, mtna=tna, mret=r))
            if m.month % 3 == 0:
                l2_rows.append(dict(fdate=m, fundno=9001 + j, wficn=5001 + j))
                for h in holds:
                    f = firms.loc[h]
                    s12_rows.append(dict(fdate=m, fundno=9001 + j, rdate=m, cusip=f.ncusip,
                                         shares=tna * 1e6 / 40 / 40.0))
    mf_tna = pd.DataFrame(tna_rows)
    mflink1 = pd.DataFrame({"crsp_fundno": np.arange(1, 41), "wficn": 5001 + np.arange(40)})
    mflink2 = pd.DataFrame(l2_rows)
    s12 = pd.DataFrame(s12_rows)

    tables = dict(guidance=guidance, ibcrsphist=ibl, ccm=ccm, funda=funda, fundq=fundq, company=company,
                  msenames=names, dsi=dsi, msf=msf, insider=insider, mf_tna=mf_tna, mflink1=mflink1,
                  mflink2=mflink2, ea_daily=ea_daily, dsf=dsf, s12=s12)
    C.RAW.mkdir(parents=True, exist_ok=True)
    (C.RAW / "_SYNTHETIC").write_text("synthetic test data - not WRDS\n")
    for k, v in tables.items():
        U.save(v, k, C.RAW)
        print(f"  synthetic {k}: {len(v):,} rows")

    C.EXTERNAL.mkdir(parents=True, exist_ok=True)
    pin = pd.DataFrame([(p, y, q, rng.beta(2, 8)) for p in firms.permno for y in range(2002, 2011) for q in range(1, 5)],
                       columns=["permno", "year", "qtr", "pin"])
    pin.to_csv(C.EXTERNAL / "pin.csv", index=False)
    dur = pd.DataFrame([(g, y, rng.uniform(0.5, 3.0)) for g in firms.gvkey for y in range(2006, 2010)],
                       columns=["gvkey", "year", "duration"])
    dur.to_csv(C.EXTERNAL / "pay_duration.csv", index=False)


if __name__ == "__main__":
    make()
