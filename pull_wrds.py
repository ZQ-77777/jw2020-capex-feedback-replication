"""
Step 01 - download everything from WRDS into data/raw/.

    export WRDS_USERNAME=<account>      # HKUST faculty/RA account
    python pull_wrds.py                 # all tables
    python pull_wrds.py guidance funda  # only some

Tables (WRDS PostgreSQL names; alternatives tried in order because WRDS renames schemas):
  ibes.det_guidance                          capex (CPX), sales (SAL), EPS guidance
  wrdsapps_link_crsp_ibes.ibcrsphist         IBES ticker -> PERMNO  (a.k.a. wrdsapps.ibcrsphist)
  crsp.ccmxpf_lnkhist                        PERMNO -> GVKEY
  comp.funda / comp.fundq / comp.company     accounting data, SIC
  crsp.dsf (event windows only), crsp.dsi, crsp.msf, crsp.msenames
  tr_insiders.table1 (a.k.a. tfn.table1)     insider transactions (Table 5B)
  crsp.monthly_tna_ret_nav, mfl.mflink1/2    fund flows (Table 5E, Table 6)
  tfn.s12 (a.k.a. tr_mutualfunds.s12)        fund holdings, only funds with extreme outflows
Hand-collected (put in data/external/, see README):
  pin.csv            Brown-Hillegeist-Lo PIN (permno, year, qtr, pin)
  pay_duration.csv   Gopalan-Milbourn-Song-Thakor (2014) pay duration (gvkey, year, duration)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import config as C
import utils as U

COMP_FILTER = "indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'"


def connect():
    import wrds  # pip install wrds
    return wrds.Connection(wrds_username=C.WRDS_USERNAME)


def first_ok(db, sqls: list[str]) -> pd.DataFrame:
    err = None
    for s in sqls:
        try:
            return db.raw_sql(s)
        except Exception as e:  # schema renamed / no subscription
            err = e
            try:
                db.connection.rollback()
            except Exception:
                pass
    raise err


def pull_guidance(db):
    return db.raw_sql(f"""
        SELECT * FROM ibes.det_guidance
        WHERE measure IN ('{C.MEASURE_CAPEX}','{C.MEASURE_SALES}','{C.MEASURE_EPS}')
          AND anndats BETWEEN '{C.FCST_FIRST}' AND '{C.FCST_LAST}'""")


def pull_guidance_earn(db):
    """Other earnings-type guidance (GPS, NET, PRE, EBITDA, ...): ticker, measure and date only, for the D9 test."""
    ms = "','".join(C.EXTRA_EARNINGS_MEASURES)
    return db.raw_sql(f"""
        SELECT DISTINCT ticker, measure, anndats FROM ibes.det_guidance
        WHERE measure IN ('{ms}')
          AND anndats BETWEEN '{C.FCST_FIRST}' AND '{C.FCST_LAST}'""")


def pull_ibcrsphist(db):
    return first_ok(db, [f"SELECT ticker, permno, ncusip, sdate, edate, score FROM {t}"
                         for t in ("wrdsapps_link_crsp_ibes.ibcrsphist", "wrdsapps.ibcrsphist")])


def pull_ccm(db):
    return db.raw_sql("""
        SELECT gvkey, lpermno, lpermco, linktype, linkprim, linkdt, linkenddt
        FROM crsp.ccmxpf_lnkhist
        WHERE linktype IN ('LU','LC') AND linkprim IN ('P','C')""")


def pull_funda(db):
    return db.raw_sql(f"""
        SELECT gvkey, datadate, fyear, fyr, capx, at, ib, ni, oancf, csho, prcc_f, ceq,
               dltt, dlc, ppent, sich, curcd
        FROM comp.funda
        WHERE {COMP_FILTER} AND datadate BETWEEN '1999-01-01' AND '2018-12-31'""")


def pull_fundq(db):
    return db.raw_sql(f"""
        SELECT gvkey, datadate, fyearq, fqtr, fyr, rdq, epspxq, ajexq, atq, ibq, niq, saleq,
               cshoq, prccq, ceqq, dlttq, dlcq, ppentq, curcdq
        FROM comp.fundq
        WHERE {COMP_FILTER} AND datadate BETWEEN '1999-01-01' AND '2017-12-31'""")


def pull_company(db):
    return db.raw_sql("SELECT gvkey, sic, state FROM comp.company")


def pull_msenames(db):
    return db.raw_sql("SELECT permno, namedt, nameendt, ncusip, shrcd, exchcd FROM crsp.msenames")


def pull_dsi(db):
    return db.raw_sql(f"SELECT date, sprtrn, vwretd FROM crsp.dsi "
                      f"WHERE date BETWEEN '{C.PULL_START}' AND '{C.PULL_END}'")


def pull_msf(db):
    return db.raw_sql(f"SELECT permno, date, prc, vol, shrout, ret FROM crsp.msf "
                      f"WHERE date BETWEEN '{C.PULL_START}' AND '{C.PULL_END}'")


def pull_insider(db):
    cols = "cusip6, cusip2, trandate, trancode, cleanse, acqdisp, personid"
    return first_ok(db, [f"""SELECT {cols} FROM {t}
                             WHERE trandate BETWEEN '{C.PULL_START}' AND '{C.FCST_LAST}'
                               AND trancode IN ('P','S')"""
                         for t in ("tr_insiders.table1", "tfn.table1")])


def pull_mf_tna(db):
    return first_ok(db, [f"""SELECT crsp_fundno, caldt, mtna, mret FROM {t}
                             WHERE caldt BETWEEN '{C.PULL_START}' AND '{C.FCST_LAST}'"""
                         for t in ("crsp.monthly_tna_ret_nav", "crsp_q_mutualfunds.monthly_tna_ret_nav",
                                   "crspq.monthly_tna_ret_nav")])


def pull_mflink1(db):
    return db.raw_sql("SELECT crsp_fundno, wficn FROM mfl.mflink1")


def pull_mflink2(db):
    return db.raw_sql("SELECT fdate, fundno, wficn FROM mfl.mflink2")


def pull_ea_daily(db):
    """Daily returns in [-7,+7] calendar days around every Compustat quarterly EA (for industry ERC)."""
    return db.raw_sql(f"""
        WITH ea AS (
          SELECT DISTINCT a.gvkey, a.rdq, b.lpermno AS permno
          FROM comp.fundq a JOIN crsp.ccmxpf_lnkhist b ON a.gvkey = b.gvkey
          WHERE a.{COMP_FILTER.replace(' AND ', ' AND a.')}
            AND a.rdq BETWEEN '{C.FCST_FIRST}' AND '{C.FCST_LAST}'
            AND b.linktype IN ('LU','LC') AND b.linkprim IN ('P','C')
            AND a.rdq >= b.linkdt AND (a.rdq <= b.linkenddt OR b.linkenddt IS NULL))
        SELECT ea.gvkey, ea.rdq, ea.permno, d.date, d.ret, i.sprtrn
        FROM ea
        JOIN crsp.dsf d ON d.permno = ea.permno AND d.date BETWEEN ea.rdq - 7 AND ea.rdq + 7
        JOIN crsp.dsi i ON i.date = d.date""")


def pull_dsf_windows(db, chunk=400):
    """crsp.dsf only for PERMNOs with guidance events, trimmed to +/-DSF_BUFFER_TDAYS around events."""
    g = U.lower_cols(U.load("guidance", C.RAW))
    g["anndats"] = U.to_dt(g["anndats"])
    g = g.dropna(subset=["anndats"]).drop_duplicates(["ticker", "anndats"])
    g = U.link_ibes_permno(g, U.load("ibcrsphist", C.RAW), "anndats").dropna(subset=["permno"])
    dsi = U.load("dsi", C.RAW)
    cal = U.TradingCalendar(dsi["date"])
    g["t0"] = cal.on_or_after(g["anndats"])
    b = C.DSF_BUFFER_TDAYS
    need = {}
    for p, t in zip(g["permno"].astype(int), g["t0"]):
        need.setdefault(p, []).append(t)
    permnos = sorted(need)
    out = []
    for i in range(0, len(permnos), chunk):
        ps = permnos[i:i + chunk]
        df = db.raw_sql(f"""SELECT permno, date, ret, prc, vol, shrout, bid, ask FROM crsp.dsf
                            WHERE permno IN ({','.join(map(str, ps))})
                              AND date BETWEEN '{C.PULL_START}' AND '{C.PULL_END}'""")
        df = df.reset_index(drop=True)          # wrds.raw_sql reads in chunks: its index can repeat
        df["date"] = U.to_dt(df["date"])
        df["tidx"] = cal.index_exact(df["date"])
        keep = np.zeros(len(df), bool)
        tidx = df["tidx"].to_numpy()
        for p, rows in df.groupby("permno").indices.items():   # positional row numbers
            t = np.sort(np.array(need[int(p)]))
            ti = tidx[rows]
            pos = np.searchsorted(t, ti)
            lo = np.abs(ti - t[np.clip(pos - 1, 0, len(t) - 1)])
            hi = np.abs(ti - t[np.clip(pos, 0, len(t) - 1)])
            keep[rows] = np.minimum(lo, hi) <= b
        out.append(df.loc[keep].drop(columns="tidx"))
        print(f"  dsf chunk {i // chunk + 1}/{(len(permnos) - 1) // chunk + 1}: kept {keep.sum():,}")
    return pd.concat(out, ignore_index=True)


def pull_s12_extreme(db):
    """Holdings at end of quarter q-1 of funds with flow <= cutoff in quarter q (Edmans et al. 2012)."""
    from build_mf_pressure import fund_quarter_flows
    flows = fund_quarter_flows(U.load("mf_tna", C.RAW), U.load("mflink1", C.RAW))
    ext = flows[flows["flow"] <= C.MF_OUTFLOW_CUTOFF]
    l2 = U.lower_cols(U.load("mflink2", C.RAW)).dropna(subset=["wficn"])
    out = []
    for q, grp in ext.groupby("qid"):
        rdate = (pd.Period(U.qid_label(q - 1), "Q").end_time.normalize()).strftime("%Y-%m-%d")
        fundnos = l2.loc[l2["wficn"].isin(grp["wficn"]), "fundno"].dropna().astype(int).unique()
        if len(fundnos) == 0:
            continue
        df = first_ok(db, [f"""SELECT fdate, fundno, rdate, cusip, shares FROM {t}
                               WHERE rdate = '{rdate}' AND fundno IN ({','.join(map(str, fundnos))})"""
                           for t in ("tfn.s12", "tr_mutualfunds.s12")])
        out.append(df)
        print(f"  s12 {rdate}: {len(df):,} rows")
    return pd.concat(out, ignore_index=True)


PULLS = {  # order matters: dsf / s12 rely on earlier pulls
    "guidance": pull_guidance, "guidance_earn": pull_guidance_earn, "ibcrsphist": pull_ibcrsphist, "ccm": pull_ccm,
    "funda": pull_funda, "fundq": pull_fundq, "company": pull_company,
    "msenames": pull_msenames, "dsi": pull_dsi, "msf": pull_msf,
    "insider": pull_insider, "mf_tna": pull_mf_tna, "mflink1": pull_mflink1,
    "mflink2": pull_mflink2, "ea_daily": pull_ea_daily,
    "dsf": pull_dsf_windows, "s12": pull_s12_extreme,
}


def _log(name, rows, secs, status):
    """Append to data/raw/_pull_log.csv: WRDS data are revised, so record WHEN each table was pulled."""
    f = C.RAW / "_pull_log.csv"
    row = pd.DataFrame([dict(table=name, rows=rows, seconds=round(secs, 1), status=status,
                             pulled_at=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))])
    try:
        row.to_csv(f, mode="a", header=not f.exists(), index=False)
    except OSError as e:                       # e.g. the log is open in Excel (Windows locks it)
        print(f"  (could not write {f.name}: {e}; close it if it is open in Excel)")


T13_TABLES = ["guidance", "guidance_earn", "ibcrsphist", "ccm", "funda", "fundq", "company", "msenames", "dsi", "dsf"]


def main(names=None):
    if not names and C.SCOPE == "t13":
        names = T13_TABLES               # Tables 1-3 need only these nine
    import time
    C.RAW.mkdir(parents=True, exist_ok=True)
    db = connect()                       # one connection -> one Duo push for the whole run
    failed = []
    try:
        for name in (names or PULLS):
            t = time.time()
            print(f"pulling {name} ...")
            try:
                df = PULLS[name](db).reset_index(drop=True)
            except Exception as e:       # no subscription / renamed table / dropped connection
                msg = str(e).strip().splitlines()[0][:200]
                print(f"  FAILED {name}: {msg}")
                _log(name, 0, time.time() - t, f"FAILED: {msg}")
                failed.append(name)
                try:
                    db.connection.rollback()
                except Exception:
                    pass
                continue
            U.save(df, name, C.RAW)
            _log(name, len(df), time.time() - t, "ok")
            print(f"  saved {name}: {len(df):,} rows ({time.time() - t:.0f}s)")
    finally:
        db.close()
    if failed:
        print(f"\nFAILED: {failed}. Re-run only these, e.g.  python pull_wrds.py {' '.join(failed)}")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
