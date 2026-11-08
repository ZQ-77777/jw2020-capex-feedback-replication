"""
Step 00 - run this FIRST, the day you get WRDS access:   python check_wrds.py

For every table the pipeline needs it checks
  (a) that your account can read it (subscription / permission),
  (b) which of the alternative schema names exists (WRDS renames libraries over time),
  (c) that every column the code uses is present.
Then it probes IBES Guidance: measure x periodicity counts, range_desc / units / curr codes,
and capex (CPX) annual forecasts per year, next to Table 1 Panel B of the paper.

Writes output/wrds_check.md. Exit code 1 if a required table is unreadable or misses columns.
Costs one Duo push. Reads only 1 row per table plus a few GROUP BY counts (a minute or two).
"""
from __future__ import annotations

import datetime as dt
import sys

import pandas as pd

import config as C
import paper_targets as P

# (key in pull_wrds, candidate tables in order, purpose, required columns, required?)
TABLES = [
    ("guidance", ["ibes.det_guidance"], "IBES Guidance: capex / sales / EPS forecasts",
     ["ticker", "measure", "pdicity", "prd_yr", "prd_mon", "anndats", "val_1", "val_2"], True),
    ("ibcrsphist", ["wrdsapps_link_crsp_ibes.ibcrsphist", "wrdsapps.ibcrsphist"], "IBES ticker -> PERMNO",
     ["ticker", "permno", "sdate", "edate", "score"], True),
    ("ccm", ["crsp.ccmxpf_lnkhist"], "PERMNO -> GVKEY",
     ["gvkey", "lpermno", "linktype", "linkprim", "linkdt", "linkenddt"], True),
    ("funda", ["comp.funda"], "annual accounting: capx, at, ib, ni, oancf",
     ["gvkey", "datadate", "fyear", "capx", "at", "ib", "ni", "oancf", "csho", "prcc_f", "sich"], True),
    ("fundq", ["comp.fundq"], "quarterly accounting, rdq, EPS",
     ["gvkey", "datadate", "fyearq", "fqtr", "rdq", "epspxq", "ajexq", "atq", "ibq", "cshoq", "prccq",
      "ceqq", "dlttq", "dlcq", "ppentq"], True),
    ("company", ["comp.company"], "header SIC, state", ["gvkey", "sic", "state"], True),
    ("msenames", ["crsp.msenames"], "CUSIP history, share code", ["permno", "namedt", "nameendt", "ncusip", "shrcd"], True),
    ("dsf", ["crsp.dsf"], "daily returns, closing bid/ask", ["permno", "date", "ret", "prc", "vol", "shrout", "bid", "ask"], True),
    ("dsi", ["crsp.dsi"], "S&P 500 daily return", ["date", "sprtrn"], True),
    ("msf", ["crsp.msf"], "monthly price / volume", ["permno", "date", "prc", "vol", "shrout", "ret"], True),
    ("insider", ["tr_insiders.table1", "tfn.table1"], "insider transactions (Table 5B)",
     ["cusip6", "cusip2", "trandate", "trancode", "cleanse"], False),
    ("mf_tna", ["crsp.monthly_tna_ret_nav", "crsp_q_mutualfunds.monthly_tna_ret_nav", "crspq.monthly_tna_ret_nav"],
     "fund TNA and returns (flows)", ["crsp_fundno", "caldt", "mtna", "mret"], False),
    ("mflink1", ["mfl.mflink1"], "CRSP fund -> WFICN", ["crsp_fundno", "wficn"], False),
    ("mflink2", ["mfl.mflink2"], "Thomson fund -> WFICN", ["fdate", "fundno", "wficn"], False),
    ("s12", ["tfn.s12", "tr_mutualfunds.s12"], "fund holdings", ["fdate", "fundno", "rdate", "cusip", "shares"], False),
]


def _try(db, sql):
    try:
        return db.raw_sql(sql), None
    except Exception as e:  # permission denied / relation does not exist / ...
        try:
            db.connection.rollback()
        except Exception:
            pass
        return None, str(e).strip().splitlines()[0][:160]


def check_tables(db) -> tuple[pd.DataFrame, dict]:
    rows, found = [], {}
    from pull_wrds import T13_TABLES
    for key, cands, purpose, cols, required in TABLES:
        if C.SCOPE == "t13" and key not in T13_TABLES:
            rows.append(dict(key=key, table=cands[0], status="not needed for Tables 1-3", required=False,
                             missing="", purpose=purpose, error=""))
            continue
        status, used, missing, err = "NO ACCESS / NOT FOUND", "", [], ""
        for t in cands:
            df, e = _try(db, f"SELECT * FROM {t} LIMIT 1")
            if df is None:
                err = e
                continue
            have = {c.lower() for c in df.columns}
            missing = [c for c in cols if c not in have]
            status, used, err = ("OK" if not missing else "COLUMNS MISSING"), t, ""
            found[key] = (t, have)
            break
        rows.append(dict(key=key, table=used or " / ".join(cands), status=status, required=required,
                         missing=", ".join(missing), purpose=purpose, error=err))
    return pd.DataFrame(rows), found


def probe_guidance(db, have: set) -> list[str]:
    t = "ibes.det_guidance"
    out = []
    win = f"anndats BETWEEN '{C.FCST_FIRST}' AND '{C.FCST_LAST}'"
    df, e = _try(db, f"""SELECT measure, pdicity, COUNT(*) AS n FROM {t}
                         WHERE {win} AND measure IN ('{C.MEASURE_CAPEX}','{C.MEASURE_SALES}','{C.MEASURE_EPS}')
                         GROUP BY 1, 2 ORDER BY 1, 2""")
    out.append("### Guidance rows by measure x pdicity (2002-2016)\n\n" + (df.to_markdown(index=False) if df is not None else e))
    if df is not None and not (df["measure"].str.upper() == C.MEASURE_CAPEX).any():
        out.append(f"\n**WARNING:** no rows with measure = '{C.MEASURE_CAPEX}'. Look at the full list below and fix "
                   f"MEASURE_CAPEX in config.py (D1).")
        m, _ = _try(db, f"SELECT measure, COUNT(*) AS n FROM {t} WHERE {win} GROUP BY 1 ORDER BY 2 DESC LIMIT 40")
        if m is not None:
            out.append(m.to_markdown(index=False))

    cpx = f"measure = '{C.MEASURE_CAPEX}' AND pdicity = '{C.PDICITY_ANNUAL}' AND {win}"
    for col in ("range_desc", "units", "curr", "usfirm"):
        if col in have:
            d, e = _try(db, f"""SELECT {col}, COUNT(*) AS n,
                                       SUM(CASE WHEN val_2 IS NULL THEN 1 ELSE 0 END) AS val2_missing
                                FROM {t} WHERE {cpx} GROUP BY 1 ORDER BY 2 DESC LIMIT 30""")
            out.append(f"\n### CPX annual: codes in `{col}` (sets D3 / D4)\n\n" + (d.to_markdown(index=False) if d is not None else e))
        else:
            out.append(f"\n`{col}` is not a column of {t}; the code skips filters that use it.")

    d, e = _try(db, f"""SELECT EXTRACT(YEAR FROM anndats)::int AS year, COUNT(*) AS forecasts,
                               COUNT(DISTINCT ticker) AS firms
                        FROM {t} WHERE {cpx} GROUP BY 1 ORDER BY 1""")
    if d is not None:
        d["paper_final_forecasts"] = d["year"].map(lambda y: P.T1B.get(int(y), (None,))[0])
        out.append("\n### CPX annual forecasts by announcement year, raw (before any filter) vs paper's FINAL sample\n\n"
                   "Raw counts must be well above the paper's numbers (the paper later drops ~half as concurrent "
                   "with EPS guidance). A raw count BELOW the paper's for some year means coverage or coding differs.\n\n"
                   + d.to_markdown(index=False))
    else:
        out.append(e)
    return out


def run(db) -> int:
    tab, found = check_tables(db)
    lines = [f"# WRDS access check — {dt.datetime.now():%Y-%m-%d %H:%M}\n",
             f"Account: `{C.WRDS_USERNAME or '(prompted)'}`\n", "## Tables\n", tab.to_markdown(index=False)]
    if "guidance" in found:
        lines += ["\n## IBES Guidance probe\n", *probe_guidance(db, found["guidance"][1])]
    alt = {k: v[0] for k, v in found.items()}
    renamed = [f"- `{k}` found as `{t}`" for k, t in alt.items()
               if t != next(x[1][0] for x in TABLES if x[0] == k)]
    if renamed:
        lines += ["\n## Tables found under an alternative name\n",
                  "pull_wrds.py already tries these names in order; nothing to change.\n", *renamed]
    bad_req = tab[(tab["required"]) & (tab["status"] != "OK")]
    bad_opt = tab[(~tab["required"]) & (~tab["status"].isin(["OK", "not needed for Tables 1-3"]))]
    lines.append("\n## Verdict\n")
    if len(bad_req):
        lines.append("**Cannot run the core tables (1-4).** Fix these first: " + ", ".join(bad_req["key"]) +
                     ". 'NO ACCESS' = your account/institution lacks the subscription; 'COLUMNS MISSING' = "
                     "WRDS renamed a column: run db.describe_table(library, table) and edit the SELECT in pull_wrds.py.")
    else:
        lines.append("Core tables OK: Tables 1-3 can be built." if C.SCOPE == "t13"
                     else "Core tables OK: Tables 1-4 and Table 5 Panel C can be built.")
    if len(bad_opt):
        lines.append("\nOptional sources unavailable: " + ", ".join(bad_opt["key"]) +
                     ". The pipeline skips the tables that need them (insider -> Table 5B; "
                     "mf_tna / mflink / s12 -> Table 5 E1, E2 and Table 6).")
    text = "\n".join(lines)
    C.OUT.mkdir(parents=True, exist_ok=True)
    (C.OUT / "wrds_check.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"\nsaved: {C.OUT / 'wrds_check.md'}")
    return 1 if len(bad_req) else 0


def main():
    from pull_wrds import connect
    db = connect()
    try:
        code = run(db)
    finally:
        db.close()
    sys.exit(code)


if __name__ == "__main__":
    main()
