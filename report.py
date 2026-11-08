"""
Step 06 - write the replication report for Tables 1-3 from the pipeline outputs.

    python report.py          (run_all.py calls it automatically)

Reads   output/estimates_long.csv, output/results_extra.json, output/sample_waterfall.csv,
        output/table1_winsor_check.csv, data/raw/_pull_log.csv (if present)
Writes  output/replication_report.html   (print to PDF from the browser: A4 layout is built in)
        output/replication_report.md

If the data are the synthetic test data, every page carries a DEMO banner: the numbers then only show
the report's layout and must not be read as results.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import platform

import numpy as np
import pandas as pd

import config as C
import paper_targets as P

AUTHOR = "Zhang Qi"

# Significance stars printed in the working paper (cannot be recovered exactly from coef/se because the
# paper uses t(G-1) with few industry clusters).
PAPER_STARS = {
    ("T2", "CAR", m): "***" for m in (1, 2, 3, 4, 5, 7, 8)
} | {("T2", "CAR", 6): "*", ("T2", "SIZE", 2): "**", ("T2", "SIZE", 3): "**", ("T2", "LAG_CAPX", 8): "***",
     ("T3", "CAR", 2): "**", ("T3", "CAR_POS", 4): "*"}

KEY_COEFS = ([("T2", "CAR", m) for m in range(1, 9)] + [("T2", "SF_CAR", 6)] +
             [("T2", v, m) for v in ("MKTRET", "CAR_PRE") for m in (7, 8)] +
             [("T3", "CAR", 1), ("T3", "CAR", 2), ("T3", "CAR_POS", 3), ("T3", "CAR_POS", 4),
              ("T3", "CAR_NEG", 3), ("T3", "CAR_NEG", 4)])

# where to look when a number is off: variable -> decision IDs in REPLICATION_NOTES.md
HINTS = {
    "N": "D1 (codes), D2 (years), D5 (horizon), D6 (firm-quarter collapse), D9 (EPS concurrency)",
    "CAPEX_FORE": "D3 (forecast types), D4 (units), D7 (range scaler)",
    "CAPEX_ACT": "D4 (units), fiscal-year match prd_yr/prd_mon -> funda datadate",
    "CAPEX_ADJ": "D3, D4, D7, D8 (open-ended), D14 (winsorising)",
    "CAR": "D11 (day 0), D12 (missing returns), D14 (winsorising)",
    "SIZE": "SIZE source (Compustat quarterly at quarter a-1; CRSP is the alternative), D14",
    "LAG_CAPX": "D15 (scaling by MV), D14",
    "LAG_CAPX_MIL": "D15",
    "SURP": "D10 (EA window), D32 (split adjustment), D14",
    "EA_DUM": "D10 (EA window)",
    "SF_CAR": "D13 (which sales forecast)",
    "MKTRET": "D11 (day 0)",
    "CAR_PRE": "pseudo-event date (14 calendar days before)",
    "CAR_POS": "D35 (split then standardise), D17 (spread split)",
    "CAR_NEG": "D35, D17",
}

CSS = """
:root{--ink:#1b2333;--muted:#5b6578;--rule:#c9d0db;--bg:#ffffff;--soft:#f2f5f9;--good:#1f7a4d;--warn:#a5631a;--bad:#a83a3a;--acc:#1f4f8f}
@media (prefers-color-scheme: dark){:root{--ink:#e3e8f0;--muted:#a1abbb;--rule:#3a465a;--bg:#131a26;--soft:#1b2433;--good:#6fcf9b;--warn:#e7b26b;--bad:#ee8d8d;--acc:#8fb6ee}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.6 Georgia,"Times New Roman",serif}
.page{max-width:900px;margin:0 auto;padding:40px 28px 80px}
h1{font-size:27px;line-height:1.3;margin:0 0 6px}
h2{font-size:20px;margin:38px 0 8px;padding-top:10px;border-top:2px solid var(--ink)}
h3{font-size:16.5px;margin:22px 0 6px}
p{margin:8px 0}
.meta{color:var(--muted);font-size:14px}
.demo{border:2px solid var(--bad);color:var(--bad);padding:10px 14px;margin:16px 0;font:600 14.5px/1.5 Arial,sans-serif}
.wrap{overflow-x:auto;margin:10px 0}
table{border-collapse:collapse;width:100%;font:13.5px/1.45 Arial,Helvetica,sans-serif;font-variant-numeric:tabular-nums}
thead th{border-top:1.5px solid var(--ink);border-bottom:1px solid var(--ink);text-align:left;padding:5px 8px;font-weight:600}
td{padding:4px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
tbody tr:last-child td{border-bottom:1.5px solid var(--ink)}
td.num,th.num{text-align:right;white-space:nowrap}
tr.paper td{color:var(--muted);border-bottom-color:transparent}
tr.paper td:first-child{padding-left:20px}
.ok{color:var(--good);font-weight:600}.mid{color:var(--warn);font-weight:600}.no{color:var(--bad);font-weight:600}
.kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}
.kpi div{background:var(--soft);padding:10px 12px;font:13px/1.4 Arial,sans-serif}
.kpi b{display:block;font:600 22px/1.2 Georgia,serif;margin-bottom:2px}
.note{color:var(--muted);font-size:13.5px}
code{font:12.5px Menlo,Consolas,monospace;background:var(--soft);padding:1px 4px}
@media (max-width:640px){.kpi{grid-template-columns:1fr 1fr}.page{padding:24px 14px 60px}}
@media print{@page{size:A4;margin:16mm 14mm}body{font-size:11pt;background:#fff;color:#000}.page{max-width:none;padding:0}
 h2{break-after:avoid}table{break-inside:auto}tr{break-inside:avoid}.demo{position:running(x)}}
"""


# ============================================================================ helpers
def stars_p(p):
    if p is None or not np.isfinite(p):
        return ""
    return "***" if p < .01 else "**" if p < .05 else "*" if p < .10 else ""


def fnum(x, d=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return ""
    if isinstance(x, (int, np.integer)) or (isinstance(x, float) and float(x).is_integer() and abs(x) >= 1000):
        return f"{int(round(x)):,}"
    return f"{x:,.{d}f}"


class Doc:
    """Builds the HTML and Markdown versions side by side."""

    def __init__(self):
        self.h, self.m = [], []

    def head(self, txt, lvl=2):
        self.h.append(f"<h{lvl}>{html.escape(txt)}</h{lvl}>")
        self.m.append("\n" + "#" * lvl + " " + txt + "\n")

    def para(self, txt, cls=None):
        c = f' class="{cls}"' if cls else ""
        self.h.append(f"<p{c}>{txt}</p>")
        self.m.append("\n" + _strip(txt) + "\n")

    def raw(self, h, m=""):
        self.h.append(h)
        if m:
            self.m.append(m)

    def table(self, df: pd.DataFrame, num_cols=(), paper_rows=None, note=None):
        paper_rows = paper_rows or set()
        th = "".join(f'<th class="{"num" if c in num_cols else ""}">{html.escape(str(c))}</th>' for c in df.columns)
        body = []
        for i, row in enumerate(df.itertuples(index=False)):
            cls = ' class="paper"' if i in paper_rows else ""
            tds = "".join(f'<td class="{"num" if c in num_cols else ""}">{v}</td>'
                          for c, v in zip(df.columns, row))
            body.append(f"<tr{cls}>{tds}</tr>")
        self.h.append(f'<div class="wrap"><table><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')
        md = df.copy()
        md = md.map(_strip) if hasattr(md, "map") else md.applymap(_strip)
        self.m.append("\n" + md.to_markdown(index=False) + "\n")
        if note:
            self.para(note, "note")


def _strip(s):
    import re
    return html.unescape(re.sub(r"<[^>]+>", "", str(s)))


def verdict(ok, partial=False):
    if ok:
        return '<span class="ok">match</span>'
    return '<span class="mid">partial</span>' if partial else '<span class="no">differs</span>'


# ============================================================================ data
def load():
    est = pd.read_csv(C.OUT / "estimates_long.csv")
    extra = json.loads((C.OUT / "results_extra.json").read_text(encoding="utf-8"))
    wf = pd.read_csv(C.OUT / "sample_waterfall.csv")
    wc = pd.read_csv(C.OUT / "table1_winsor_check.csv") if (C.OUT / "table1_winsor_check.csv").exists() else None
    log_f = C.RAW / "_pull_log.csv"
    log = pd.read_csv(log_f) if log_f.exists() else None
    synthetic = (C.RAW / "_SYNTHETIC").exists()      # marker written by tests/make_synthetic.py
    return est, extra, wf, wc, log, synthetic


def coef(est, table, var, model):
    r = est[(est.table == table) & (est["var"] == var) & (est.model == model)]
    return None if r.empty else r.iloc[0]


def paper_cs(table, var, model):
    src = P.T2 if table == "T2" else P.T3
    return src.get((var, model), (np.nan, np.nan))


# ============================================================================ sections
def scorecard(doc, est):
    rows, n_sign, n_sig, n_close, n = [], 0, 0, 0, 0
    for tab, var, m in KEY_COEFS:
        r = coef(est, tab, var, m)
        pc, ps = paper_cs(tab, var, m)
        if r is None or not np.isfinite(pc):
            continue
        n += 1
        pst = PAPER_STARS.get((tab, var, m), "")
        ost = stars_p(r["p"])
        sign_ok = np.sign(r["coef"]) == np.sign(pc) or (abs(pc) < 1e-9)
        sig_ok = bool(pst) == bool(ost)
        z = (r["coef"] - pc) / ps if ps and np.isfinite(ps) else np.nan
        close = np.isfinite(z) and abs(z) <= 1
        n_sign += sign_ok; n_sig += sig_ok; n_close += close
        rows.append([f"{tab} ({m}) {var}", f"{pc:.3f}{pst}", f"{r['coef']:.3f}{ost}", f"{z:+.2f}" if np.isfinite(z) else "",
                     verdict(sign_ok), verdict(sig_ok), verdict(close, partial=np.isfinite(z) and abs(z) <= 2)])
    df = pd.DataFrame(rows, columns=["Coefficient", "Paper", "Ours", "(ours - paper) / paper SE",
                                     "Sign", "Significance (10%)", "Within 1 paper SE"])
    return df, dict(n=n, sign=n_sign, sig=n_sig, close=n_close)


def section_summary(doc, est, extra, wf, score):
    df, s = score
    r8 = coef(est, "T2", "CAR", 8)
    hi, lo = coef(est, "T3", "CAR", 2), coef(est, "T3", "CAR", 1)
    doc.head("1. Summary")
    n_paper = 17577
    doc.raw(f'''<div class="kpi">
<div><b>{extra["n_final"]:,}</b>capex forecasts (paper 17,577; {100 * (extra["n_final"] / n_paper - 1):+.1f}%)</div>
<div><b>{extra["n_firms"]:,}</b>firms (paper 1,790)</div>
<div><b>{s["sign"]}/{s["n"]}</b>key coefficients with the paper's sign</div>
<div><b>{s["sig"]}/{s["n"]}</b>with the paper's significance at 10%</div></div>''',
            f"\n- Final sample: {extra['n_final']:,} forecasts, {extra['n_firms']:,} firms (paper 17,577 / 1,790)"
            f"\n- Sign agreement {s['sign']}/{s['n']}; significance agreement {s['sig']}/{s['n']}; "
            f"within one paper SE {s['close']}/{s['n']}\n")
    txt = []
    if r8 is not None:
        txt.append(f"The main estimate, Table 2 model (8), is {r8['coef']:.3f}{stars_p(r8['p'])} (SE {r8['se']:.3f}) "
                   f"against 0.849*** (0.304) in the paper: a one-standard-deviation higher market reaction to a capex "
                   f"forecast goes with a {r8['coef']:.2f} percentage-point larger upward revision of actual capex, "
                   f"{r8['coef'] / extra['mean_CAPEX_ADJ'] * 100:.1f}% of the mean adjustment (paper 11.4%).")
    if hi is not None and lo is not None:
        pat = hi["coef"] > lo["coef"] and hi["p"] < .10 and lo["p"] >= .10
        p_d = extra.get("t3_p", {}).get("CAR")
        txt.append(f"Table 3: the effect is {hi['coef']:.3f}{stars_p(hi['p'])} when event-window spreads rise and "
                   f"{lo['coef']:.3f}{stars_p(lo['p'])} when they fall (paper 1.206** and -0.295; difference p = "
                   f"{p_d:.3f} vs 0.019). The paper's pattern - an effect only when the forecast draws in informed "
                   f"trading - is {'reproduced' if pat else 'not reproduced'}." if p_d is not None else "")
    doc.para(" ".join(t for t in txt if t))


def section_data(doc, wf, log):
    doc.head("2. Data and sample")
    doc.para("Capex, sales and EPS guidance come from I/B/E/S Guidance (<code>ibes.det_guidance</code>); actual capex and "
             "accounting variables from Compustat (<code>comp.funda</code>, <code>comp.fundq</code>); returns, the S&amp;P 500 "
             "return and closing bid/ask quotes from CRSP (<code>crsp.dsf</code>, <code>crsp.dsi</code>). I/B/E/S tickers are "
             "linked to CRSP PERMNOs with the WRDS link table valid on the announcement date, and PERMNOs to GVKEYs "
             "with the CCM link history (LU/LC links). The forecasted fiscal year is matched to the Compustat fiscal "
             "year whose <code>datadate</code> has the same year and month as the I/B/E/S period end.")
    w = wf.copy()
    w["paper"] = w["paper"].map(lambda x: fnum(x) if pd.notna(x) else "")
    w["diff"] = [f"{(o / p - 1) * 100:+.1f}%" if pd.notna(p) else "" for o, p in
                 zip(wf["ours"], wf["paper"])]
    w["ours"] = w["ours"].map(fnum)
    labels = {"w0_ibes_capex_forecasts": "I/B/E/S annual capex forecasts, 2002-2016",
              "w0b_one_per_firm_quarter": "one forecast per firm-quarter (first)",
              "w1_matched_compustat": "matched to Compustat actual capex",
              "w2_with_car": "with a five-day CRSP market reaction",
              "w3_not_concurrent_eps": "not issued on the day of an EPS forecast",
              "w4_drop_2016": "issued 2003-2015 (final sample)"}
    w["step"] = w["step"].map(lambda k: labels.get(k, k))
    doc.table(w.rename(columns={"step": "Step", "ours": "Ours", "paper": "Paper", "diff": "Difference"}),
              num_cols=("Ours", "Paper", "Difference"),
              note="Paper counts from Section 2.2. The paper's arithmetic is exact (36,900 - 17,473 - 1,850 = 17,577), "
                   "so the collapse to firm-quarters is applied before the first count (decision D6).")
    if log is not None:
        lg = log.sort_values("pulled_at").drop_duplicates("table", keep="last")
        doc.para(f"Data vintage: WRDS tables pulled between {lg['pulled_at'].min()} and {lg['pulled_at'].max()} "
                 f"(<code>data/raw/_pull_log.csv</code>). I/B/E/S Guidance and Compustat have been revised since the paper "
                 f"was written, so exact equality of counts is not expected.", "note")


def section_t1(doc, extra, wc):
    doc.head("3. Table 1: descriptive statistics")
    doc.head("Panel A", 3)
    rows, prow = [], set()
    for v, tgt in P.T1A.items():
        o = extra["t1_stats"].get(v)
        if o is None:
            continue
        rows.append([v, fnum(o[0]), *[fnum(x) for x in o[1:]]])
        rows.append(["paper", fnum(tgt[0]), *[fnum(x) for x in tgt[1:]]])
        prow.add(len(rows) - 1)
    doc.table(pd.DataFrame(rows, columns=["Variable", "Obs.", "Mean", "Median", "S.D.", "Min", "Max"]),
              num_cols=("Obs.", "Mean", "Median", "S.D.", "Min", "Max"), paper_rows=prow,
              note="CAPEX_FORE, CAPEX_ACT and LAG_CAPX in $ millions; CAPEX_ADJ and CAR in percent. "
                   "Grey rows: working paper (May 2019).")
    if wc is not None:
        w = wc.copy()
        for c in ("raw min", "p1", "p99", "raw max", "paper min", "paper max"):
            w[c] = w[c].map(lambda x: fnum(x))
        doc.para("Winsorisation is not described in the paper. The table below compares our raw extremes and "
                 "1st/99th percentiles with the paper's min and max; where 'paper closer to' says winsorised, the paper "
                 "most likely truncated that variable (decision D14).")
        doc.table(w, num_cols=("raw min", "p1", "p99", "raw max", "paper min", "paper max"))
    doc.head("Panel B: capex forecasts by year", 3)
    rows = []
    for y, (pf, pft) in P.T1B.items():
        o = extra["t1_years"].get(str(y), [None, None])
        rows.append([y, fnum(o[0]) if o[0] is not None else "", fnum(pf),
                     fnum(o[1]) if o[1] is not None else "", fnum(pft)])
    doc.table(pd.DataFrame(rows, columns=["Year", "Forecasts (ours)", "Forecasts (paper)",
                                          "First-time (ours)", "First-time (paper)"]),
              num_cols=("Forecasts (ours)", "Forecasts (paper)", "First-time (ours)", "First-time (paper)"))
    doc.head("Panel C: forecast types", 3)
    tot = sum(extra["t1_types"].values()) or 1
    rows = [[k, fnum(extra["t1_types"].get(k, 0)), f"{extra['t1_types'].get(k, 0) / tot:.2%}", fnum(n), f"{sh:.2%}"]
            for k, (n, sh) in P.T1C.items()]
    doc.table(pd.DataFrame(rows, columns=["Type", "Ours", "Share", "Paper", "Paper share"]),
              num_cols=("Ours", "Share", "Paper", "Paper share"),
              note="Range forecasts: CAPEX_ADJ is zero inside the range and measured from the violated end-point "
                   "outside it, scaled by the range midpoint (D7). Open-ended forecasts are treated as points (D8).")


def reg_table(doc, est, table, models, varorder, paper, paper_n, paper_r2, fe, cl):
    rows, prow = [], set()
    for v in varorder:
        line, pline, any_ = [v], ["paper"], False
        for m in models:
            r = coef(est, table, v, m)
            line.append(f"{r['coef']:.3f}{stars_p(r['p'])}<br>({r['se']:.3f})" if r is not None else "")
            pc, ps = paper.get((v, m), (np.nan, np.nan))
            pst = PAPER_STARS.get((table, v, m), "")
            pline.append(f"{pc:.3f}{pst}<br>({ps:.3f})" if np.isfinite(pc) else "")
            any_ |= r is not None or np.isfinite(pc)
        if any_:
            rows += [line, pline]
            prow.add(len(rows) - 1)
    def first(m, col):
        r = est[(est.table == table) & (est.model == m)]
        return r[col].iloc[0] if len(r) else np.nan
    rows.append(["Obs."] + [fnum(int(first(m, "nobs"))) if np.isfinite(first(m, "nobs")) else "" for m in models])
    rows.append(["paper"] + [fnum(paper_n.get(m)) for m in models]); prow.add(len(rows) - 1)
    rows.append(["Adj. R²"] + [f"{first(m, 'adj_r2'):.3f}" for m in models])
    rows.append(["paper"] + [f"{paper_r2[m]:.3f}" if m in paper_r2 else "" for m in models]); prow.add(len(rows) - 1)
    rows.append(["Fixed effects"] + [fe[m] for m in models])
    rows.append(["Clusters"] + [f"{cl[m]} ({int(first(m, 'clusters'))})" if np.isfinite(first(m, "clusters")) else cl[m]
                                for m in models])
    doc.table(pd.DataFrame(rows, columns=[""] + [f"({m})" for m in models]),
              num_cols=tuple(f"({m})" for m in models), paper_rows=prow)


def section_t2(doc, est, extra):
    doc.head("4. Table 2: capex adjustments and the market reaction to capex forecasts")
    doc.para("Dependent variable: CAPEX_ADJ, the percentage deviation of actual from forecasted capex. CAR, SF_CAR, "
             "MKTRET and CAR_PRE are standardised (mean 0, SD 1), so each coefficient is the change in CAPEX_ADJ in "
             "percentage points for a one-SD change. Robust standard errors in parentheses; *, **, *** = 10/5/1%, "
             "two-tailed, t with G-1 degrees of freedom.")
    fe = {1: "None", 2: "None", 3: "Yr-qtr", **{m: "Firm, yr-qtr" for m in range(4, 9)}}
    cl = {m: "Firm" if m <= 4 else "Industry" for m in range(1, 9)}
    reg_table(doc, est, "T2", list(range(1, 9)), ["CAR", "SF_CAR", "MKTRET", "CAR_PRE", "SIZE", "LAG_CAPX", "SURP", "EA_DUM"],
              P.T2, P.T2_N, P.T2_R2, fe, cl)
    doc.para(f"Model (6) uses the {extra.get('n_SF', 0):,} forecasts with a sales forecast for the same fiscal period "
             f"(paper 3,456); median distance between the two announcements {extra.get('median_SF_dist', float('nan')):.0f} "
             f"days (paper 86). Industry = two-digit SIC, fixed per firm (D18).", "note")


def section_t3(doc, est, extra):
    doc.head("5. Table 3: information asymmetry and the sign of the reaction")
    doc.para("Columns (1) and (3): forecasts whose mean relative bid-ask spread over days [-2, +2] is not above the "
             "mean over days [-10, -3] ('Lower spreads'); columns (2) and (4): above ('Higher spreads'). CAR_POS = "
             "max(CAR, 0) and CAR_NEG = min(CAR, 0), each standardised (D35). All models include the controls of "
             "Table 2 model (8), firm and year-quarter fixed effects, and industry clusters.")
    fe = {m: "Firm, yr-qtr" for m in range(1, 5)}
    cl = {m: "Industry" for m in range(1, 5)}
    reg_table(doc, est, "T3", [1, 2, 3, 4], ["CAR", "CAR_POS", "CAR_NEG", "MKTRET", "CAR_PRE"], P.T3, P.T3_N, P.T3_R2, fe, cl)
    p = extra.get("t3_p", {})
    names = {"CAR": "CAR, (1) vs (2)", "MKTRET_12": "MKTRET, (1) vs (2)", "CAR_PRE_12": "CAR_PRE, (1) vs (2)",
             "CAR_POS": "CAR_POS, (3) vs (4)", "CAR_NEG": "CAR_NEG, (3) vs (4)", "MKTRET_34": "MKTRET, (3) vs (4)",
             "CAR_PRE_34": "CAR_PRE, (3) vs (4)"}
    rows = [[names[k], f"{p[k]:.3f}" if p.get(k) is not None else "", f"{P.T3_P[k]:.3f}"] for k in names]
    doc.head("p-values of the difference between Lower and Higher spreads", 3)
    doc.table(pd.DataFrame(rows, columns=["Coefficient", "Ours", "Paper"]), num_cols=("Ours", "Paper"),
              note="The paper does not say how the difference was tested. We estimate one pooled model in which every "
                   "regressor and both fixed effects are interacted with the split, with a joint industry-clustered "
                   "covariance (the analogue of Stata suest); point estimates equal the separate regressions.")


def section_text(doc, extra):
    doc.head("6. Numbers quoted in the text")
    rows = [[d["coefficient"], f"{d['ours coef']:.3f}", f"{d['ours % of mean']:.1f}%", f"{d['paper % of mean']:.1f}%",
             d["source"]] for d in extra.get("magnitudes", [])]
    doc.head("Economic magnitudes (coefficient / mean CAPEX_ADJ)", 3)
    doc.table(pd.DataFrame(rows, columns=["Coefficient", "Ours", "Ours % of mean", "Paper", "Source"]),
              num_cols=("Ours", "Ours % of mean", "Paper"),
              note=f"Our mean CAPEX_ADJ is {extra['mean_CAPEX_ADJ']:.3f}% (paper 7.421%).")
    rows = [[t["moment"], fnum(t["ours"]), fnum(t["paper"]) if t["paper"] is not None else ""] for t in extra.get("text", [])]
    doc.head("Moments and footnotes", 3)
    doc.table(pd.DataFrame(rows, columns=["Moment", "Ours", "Paper"]), num_cols=("Ours", "Paper"))


def section_robust(doc, est):
    doc.head("7. Robustness reported in the text")
    lab = {1: "Baseline, Table 2 model (8)", 2: "CAPEX_ADJ relative to the range midpoint (fn 17)",
           3: "Point and range forecasts only (fn 17)", 4: "Forecasts from 2009 on (fn 23)",
           5: "+ industry x year FE (fn 19)", 6: "+ state x year FE (fn 19)", 7: "+ asset growth control (fn 18)"}
    paper = {5: "0.800**", 6: "0.968***"}
    rows = []
    for m, l in lab.items():
        r = coef(est, "ROB", "CAR", m)
        if r is None:
            continue
        rows.append([l, f"{r['coef']:.3f}{stars_p(r['p'])} ({r['se']:.3f})", fnum(int(r["nobs"])),
                     paper.get(m, "robust (no number)" if m > 1 else "0.849***")])
    doc.table(pd.DataFrame(rows, columns=["Specification", "CAR (ours)", "Obs.", "Paper"]), num_cols=("Obs.",))


def section_choices(doc):
    doc.head("8. Implementation choices")
    doc.para("The paper leaves the following choices open. Each is a switch in <code>config.py</code>; the full log "
             "with the evidence for each choice is in <code>REPLICATION_NOTES.md</code>.")
    items = [
        ("D2", "Sample years", f"{C.KEEP_FROM_YEAR}-{C.DROP_FROM_YEAR - 1}"),
        ("D3", "Open-ended range_desc codes", ", ".join(sorted(map(str, C.RANGE_DESC_OPEN_ENDED))) or "(none set)"),
        ("D5", "Horizon / nearest fiscal year", f"<= {C.MAX_HORIZON_MONTHS} months; nearest only = {C.NEAREST_PERIOD_ONLY}"),
        ("D6", "Firm-quarter collapse", f"keep {C.ONE_PER_FIRM_QUARTER}; before waterfall = {C.COLLAPSE_AT_START}"),
        ("D7", "Range denominator", C.RANGE_SCALER),
        ("D8", "Open-ended forecasts", C.OTHER_RULE),
        ("D9", "EPS-concurrency window (days)", C.EPS_CONCURRENT_DAYS),
        ("D10", "EA_DUM window (days)", C.EA_CONCURRENT_DAYS),
        ("D11", "After-close shift of day 0", C.AFTER_CLOSE_SHIFT),
        ("D12", "Returns required in CAR", C.MIN_RET_OBS),
        ("D13", "Min. gap capex-sales forecast (trading days)", C.SF_MIN_GAP_TDAYS),
        ("D14", "Winsorised variables", ", ".join(C.WINSOR_VARS[:6]) + f"; levels too = {C.WINSOR_LEVELS}"),
        ("D15", "LAG_CAPX in regressions", C.LAG_CAPX_SCALE),
        ("D17", "Spread unit", "percent" if C.SPREAD_UNIT == 100 else C.SPREAD_UNIT),
        ("D18", "Industry", C.INDUSTRY),
        ("D25", "Singletons dropped", C.DROP_SINGLETONS),
        ("D26", "Degrees-of-freedom convention", C.DOF_MODE),
        ("D27", "Standardisation sample", C.STANDARDIZE_ON),
        ("D32", "SURP split-adjusted", C.SURP_SPLIT_ADJUST),
        ("D35", "CAR_POS / CAR_NEG", "split raw CAR at 0, then standardise"),
    ]
    doc.table(pd.DataFrame([[a, b, html.escape(str(c))] for a, b, c in items], columns=["ID", "Choice", "Setting used"]))


def section_deviations(doc, est, extra, score):
    doc.head("9. Where the replication differs, and why")
    df, _ = score
    flagged = []
    for tab, var, m in KEY_COEFS:
        r = coef(est, tab, var, m)
        pc, ps = paper_cs(tab, var, m)
        if r is None or not np.isfinite(pc) or not ps:
            continue
        z = (r["coef"] - pc) / ps
        if abs(z) > 1 or np.sign(r["coef"]) != np.sign(pc):
            flagged.append([f"{tab} ({m}) {var}", f"{pc:.3f}", f"{r['coef']:.3f}", f"{z:+.2f}", HINTS.get(var, "")])
    for v, o in extra["t1_stats"].items():
        tgt = P.T1A[v]
        if tgt[3] and abs(o[1] - tgt[1]) > 0.25 * tgt[3]:
            flagged.append([f"Table 1 mean of {v}", fnum(tgt[1]), fnum(o[1]), "> 0.25 SD", HINTS.get(v, "")])
    if abs(extra["n_final"] / 17577 - 1) > 0.10:
        flagged.append(["Final sample size", "17,577", fnum(extra["n_final"]), f"{(extra['n_final'] / 17577 - 1):+.0%}", HINTS["N"]])
    if flagged:
        doc.para("Items that differ from the paper by more than one of the paper's standard errors (coefficients), by more "
                 "than a quarter of a standard deviation (Table 1 means) or by more than 10% (sample size), with the "
                 "decisions most likely responsible:")
        doc.table(pd.DataFrame(flagged, columns=["Item", "Paper", "Ours", "Gap", "Look at"]), num_cols=("Paper", "Ours", "Gap"))
    else:
        doc.para("No coefficient differs from the paper by more than one of the paper's standard errors, and the sample "
                 "and Table 1 means are within the tolerance bands.")
    doc.para("General sources of difference: (i) I/B/E/S Guidance, Compustat and CRSP have been revised since 2019; "
             "(ii) the numbers compared here come from the May 2019 working paper, and the published version may differ; "
             "(iii) the paper does not state its winsorisation, its treatment of open-ended forecasts, its industry "
             "definition, or how the difference tests were computed.", "note")


def section_repro(doc, log, synthetic):
    doc.head("10. Reproducibility")
    doc.para("Code: Python package <code>jw2020</code> (no Stata needed). Fixed-effects OLS with clustered standard "
             "errors is implemented in <code>hdfe.py</code> following Stata <code>reghdfe</code>: fixed effects absorbed "
             "by alternating projections; V = c(X'X)<sup>-1</sup>[&Sigma;<sub>g</sub>X<sub>g</sub>'u<sub>g</sub>u<sub>g</sub>'X<sub>g</sub>](X'X)<sup>-1</sup> "
             "with c = G/(G-1)&middot;(N-1)/(N-K); fixed effects nested in the cluster variable are not counted in K. "
             "<code>tests/test_hdfe.py</code> checks the estimator against least squares with dummy variables to 1e-8.")
    doc.raw("<pre><code>python check_wrds.py   # access and column check\npython pull_wrds.py    # 9 WRDS tables for Tables 1-3\n"
            "python diagnose.py     # calibrate I/B/E/S coding switches\npython run_all.py      # sample, Tables 1-3, this report</code></pre>",
            "\n```\npython check_wrds.py\npython pull_wrds.py\npython diagnose.py\npython run_all.py\n```\n")
    doc.para(f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} with Python {platform.python_version()}, pandas "
             f"{pd.__version__}, numpy {np.__version__}. Data: {'SYNTHETIC test data' if synthetic else 'WRDS'}.", "note")


# ============================================================================ main
def main():
    est, extra, wf, wc, log, synthetic = load()
    doc = Doc()
    title = "Replication of Jayaraman and Wu (2020), Tables 1-3"
    doc.raw(f"<h1>{title}</h1>", f"# {title}\n")
    doc.para("Jayaraman, S. and J. S. Wu (2020). Should I Stay or Should I Grow? Using Voluntary Disclosure to Elicit "
             "Market Feedback. <i>Review of Financial Studies</i> 33(8): 3854-3888.", "meta")
    doc.para(f"{AUTHOR} &middot; {dt.date.today():%d %B %Y}", "meta")
    if synthetic:
        demo = ("DEMO REPORT built from synthetic test data. It shows the layout only; none of the 'ours' numbers is a "
                "result. Run the pipeline on WRDS data to produce the real report.")
        doc.raw(f'<div class="demo">{demo}</div>', f"\n> **{demo}**\n")
    score = scorecard(doc, est)
    section_summary(doc, est, extra, wf, score)
    doc.head("Scorecard of key coefficients", 3)
    doc.table(score[0], num_cols=("Paper", "Ours", "(ours - paper) / paper SE"),
              note="Paper stars as printed in the working paper. 'partial' = within two paper standard errors.")
    section_data(doc, wf, log)
    section_t1(doc, extra, wc)
    section_t2(doc, est, extra)
    section_t3(doc, est, extra)
    section_text(doc, extra)
    section_robust(doc, est)
    section_choices(doc)
    section_deviations(doc, est, extra, score)
    section_repro(doc, log, synthetic)
    banner = f'<div class="demo">{demo}</div>' if synthetic else ""
    page = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>{title}</title><style>{CSS}</style></head>'
            f'<body><div class="page">{"".join(doc.h)}{banner}</div></body></html>')
    (C.OUT / "replication_report.html").write_text(page, encoding="utf-8")
    (C.OUT / "replication_report.md").write_text("".join(doc.m), encoding="utf-8")
    print(f"report: {C.OUT / 'replication_report.html'} (+ .md){'  [DEMO: synthetic data]' if synthetic else ''}")


if __name__ == "__main__":
    main()
