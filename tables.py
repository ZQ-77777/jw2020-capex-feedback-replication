"""
Step 05 - Tables 1-6 and Figure 1, each printed next to the paper's numbers.

Outputs (output/):
  tables.md              all tables, ours vs paper
  estimates_long.csv     every coefficient: table, model, var, coef, se, p, N, adj R2, paper coef/se
  figure1_spreads.png    Figure 1 panels A and B
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
import paper_targets as P
import utils as U
from hdfe import diff_test, hdfe_ols

FE = ["gvkey", "YQ"]
CTRL8 = ["SIZE", "LAG_CAPX", "SURP", "EA_DUM", "MKTRET_z", "CAR_PRE_z"]   # Table 2 model (8)
LONG: list[dict] = []
MD: list[str] = []
EXTRA: dict = {}      # scalar results for report.py


def rename(v: str) -> str:
    return v[:-2] if v.endswith("_z") else v


def run(df, y, X, fe, cl, table, model, paper=None, label=""):
    r = hdfe_ols(df, y, X, fe, cl, label=f"{table}-{model}")
    paper = paper or {}
    for v in r.coef.index:
        pc, ps = paper.get((rename(v), model), (np.nan, np.nan))
        LONG.append(dict(table=table, model=model, label=label, var=rename(v), coef=r.coef[v], se=r.se[v],
                         p=r.p[v], nobs=r.nobs, adj_r2=r.adj_r2, clusters=r.n_clusters,
                         paper_coef=pc, paper_se=ps))
    return r


def fmt(r, v):
    if r is None or v not in r.coef:
        return ""
    return f"{r.coef[v]:.3f}{U.stars(r.p[v])} ({r.se[v]:.3f})"


def fmt_paper(cs):
    if cs is None or not np.isfinite(cs[0]):
        return ""
    return f"{cs[0]:.3f} ({cs[1]:.3f})" if np.isfinite(cs[1]) else f"{cs[0]:.3f}"


def block(title, results: dict, varorder, paper=None, paper_n=None, notes="", paper_r2=None):
    rows = []
    for v in varorder:
        rows.append([v] + [fmt(r, v if v in r.coef else v + "_z") for r in results.values()])
        if paper:
            rows.append(["  paper"] + [fmt_paper(paper.get((rename(v), m))) for m in results])
    rows.append(["N"] + [f"{r.nobs:,}" for r in results.values()])
    if paper_n:
        rows.append(["  paper N"] + [f"{paper_n.get(m, ''):,}" if m in paper_n else "" for m in results])
    rows.append(["Adj. R2"] + [f"{r.adj_r2:.3f}" for r in results.values()])
    if paper_r2:
        rows.append(["  paper Adj. R2"] + [f"{paper_r2[m]:.3f}" if m in paper_r2 else "" for m in results])
    t = pd.DataFrame(rows, columns=[""] + [f"({m})" for m in results])
    MD.append(f"\n## {title}\n\n{notes}\n\n" + t.to_markdown(index=False) + "\n")
    print(f"\n== {title}\n" + t.to_string(index=False))


# ============================================================================ Table 1
def table1(c):
    rows = []
    for v, tgt in P.T1A.items():
        s = pd.to_numeric(c[v], errors="coerce").dropna()
        rows.append([v, f"{len(s):,}", s.mean(), s.median(), s.std(), s.min(), s.max()])
        rows.append(["  paper", f"{tgt[0]:,}", *tgt[1:]])
    t = pd.DataFrame(rows, columns=["Variable", "Obs", "Mean", "Median", "SD", "Min", "Max"])
    MD.append("\n## Table 1 Panel A - descriptive statistics\n\n" + t.to_markdown(index=False, floatfmt=".3f"))
    first = c.groupby("gvkey")["YEAR"].min()
    b = pd.DataFrame({"forecasts": c.groupby("YEAR").size(),
                      "first_time": first.value_counts().sort_index()}).fillna(0).astype(int)
    b["paper_forecasts"] = b.index.map(lambda y: P.T1B.get(y, (np.nan,))[0])
    b["paper_first_time"] = b.index.map(lambda y: P.T1B.get(y, (np.nan, np.nan))[1])
    MD.append("\n## Table 1 Panel B - forecasts by year\n\n" + b.to_markdown())
    pc = c["FTYPE"].value_counts().rename("ours").to_frame()
    pc["ours_share"] = pc["ours"] / pc["ours"].sum()
    pc["paper"] = pc.index.map(lambda k: P.T1C.get(k, (np.nan,))[0])
    pc["paper_share"] = pc.index.map(lambda k: P.T1C.get(k, (np.nan, np.nan))[1])
    MD.append("\n## Table 1 Panel C - forecast types\n\n" + pc.to_markdown(floatfmt=".4f"))
    # D14 check: is each variable winsorised in the paper? compare raw min/max and p1/p99 with the paper
    wrows = []
    for v, tgt in P.T1A.items():
        if v == "EA_DUM":
            continue
        raw = pd.to_numeric(c.get(v + "_raw", c[v]), errors="coerce").dropna()
        pmin, pmax = tgt[4], tgt[5]
        p1, p99 = raw.quantile(0.01), raw.quantile(0.99)
        closer = "winsorised" if abs(p1 - pmin) + abs(p99 - pmax) < abs(raw.min() - pmin) + abs(raw.max() - pmax) else "raw"
        wrows.append([v, raw.min(), p1, p99, raw.max(), pmin, pmax, closer,
                      "yes" if v in C.WINSOR_VARS or (C.WINSOR_LEVELS and v in ("CAPEX_FORE", "CAPEX_ACT", "LAG_CAPX_MIL", "SIZE")) else "no"])
    wt = pd.DataFrame(wrows, columns=["Variable", "raw min", "p1", "p99", "raw max", "paper min", "paper max",
                                      "paper closer to", "we winsorise"])
    wt.to_csv(C.OUT / "table1_winsor_check.csv", index=False)
    MD.append("\n### Winsorisation check (D14)\n\nIf 'paper closer to' disagrees with 'we winsorise' for a variable, "
              "flip it in config.WINSOR_VARS.\n\n" + wt.to_markdown(index=False, floatfmt=".3f"))
    EXTRA["t1_types"] = {k: int(v) for k, v in c["FTYPE"].value_counts().items()}
    EXTRA["t1_years"] = {int(y): [int(r.forecasts), int(r.first_time)] for y, r in b.iterrows()}
    EXTRA["t1_stats"] = {v: [int(pd.to_numeric(c[v], errors="coerce").notna().sum())] +
                         [float(x) for x in pd.to_numeric(c[v], errors="coerce").agg(["mean", "median", "std", "min", "max"])]
                         for v in P.T1A}
    print(t.to_string(index=False)); print(b.to_string()); print(pc.to_string())


# ============================================================================ Table 2
def table2(c):
    base = c.dropna(subset=["CAPEX_ADJ", "CAR_z", "SIZE"])
    R = {}
    R[1] = run(base, "CAPEX_ADJ", ["CAR_z"], [], "gvkey", "T2", 1, P.T2)
    R[2] = run(base, "CAPEX_ADJ", ["CAR_z", "SIZE"], [], "gvkey", "T2", 2, P.T2)
    R[3] = run(base, "CAPEX_ADJ", ["CAR_z", "SIZE"], ["YQ"], "gvkey", "T2", 3, P.T2)
    R[4] = run(base, "CAPEX_ADJ", ["CAR_z", "SIZE"], FE, "gvkey", "T2", 4, P.T2)
    R[5] = run(base, "CAPEX_ADJ", ["CAR_z", "SIZE"], FE, "IND", "T2", 5, P.T2)
    sf = base.dropna(subset=["SF_CAR"]).copy()
    sf["SF_CAR_z"] = U.zscore(sf["SF_CAR"])
    R[6] = run(sf, "CAPEX_ADJ", ["CAR_z", "SF_CAR_z", "SIZE"], FE, "IND", "T2", 6, P.T2)
    R[7] = run(base, "CAPEX_ADJ", ["CAR_z", "MKTRET_z", "CAR_PRE_z", "SIZE"], FE, "IND", "T2", 7, P.T2)
    R[8] = run(base, "CAPEX_ADJ", ["CAR_z", *CTRL8], FE, "IND", "T2", 8, P.T2)
    block("Table 2 - CAPEX_ADJ on market reaction to capex forecasts", R,
          ["CAR", "SF_CAR", "MKTRET", "CAR_PRE", "SIZE", "LAG_CAPX", "SURP", "EA_DUM"], P.T2, P.T2_N,
          "Clusters: firm (1)-(4), industry (5)-(8). FE: none (1)-(2), yr-qtr (3), firm+yr-qtr (4)-(8). "
          f"Median distance capex->sales forecast (model 6): {sf['SF_DIST_DAYS'].median():.0f} days (paper 86).",
          paper_r2=P.T2_R2)
    EXTRA["median_SF_dist"] = float(sf["SF_DIST_DAYS"].median())
    EXTRA["n_SF"] = int(R[6].nobs)
    return R[8]


# ============================================================================ Table 3
def table3(c):
    s = c.dropna(subset=["CAPEX_ADJ", "CAR_z", "HIGHER_SPREAD", *CTRL8])
    lo, hi = s[s["HIGHER_SPREAD"] == 0], s[s["HIGHER_SPREAD"] == 1]
    R = {1: run(lo, "CAPEX_ADJ", ["CAR_z", *CTRL8], FE, "IND", "T3", 1, P.T3),
         2: run(hi, "CAPEX_ADJ", ["CAR_z", *CTRL8], FE, "IND", "T3", 2, P.T3),
         3: run(lo, "CAPEX_ADJ", ["CAR_POS_z", "CAR_NEG_z", *CTRL8], FE, "IND", "T3", 3, P.T3),
         4: run(hi, "CAPEX_ADJ", ["CAR_POS_z", "CAR_NEG_z", *CTRL8], FE, "IND", "T3", 4, P.T3)}
    pv = {"CAR": diff_test(s, "CAPEX_ADJ", ["CAR_z", *CTRL8], FE, "IND", "HIGHER_SPREAD", "CAR_z"),
          "MKTRET_12": diff_test(s, "CAPEX_ADJ", ["CAR_z", *CTRL8], FE, "IND", "HIGHER_SPREAD", "MKTRET_z"),
          "CAR_PRE_12": diff_test(s, "CAPEX_ADJ", ["CAR_z", *CTRL8], FE, "IND", "HIGHER_SPREAD", "CAR_PRE_z")}
    X4 = ["CAR_POS_z", "CAR_NEG_z", *CTRL8]
    for v, k in (("CAR_POS_z", "CAR_POS"), ("CAR_NEG_z", "CAR_NEG"), ("MKTRET_z", "MKTRET_34"), ("CAR_PRE_z", "CAR_PRE_34")):
        pv[k] = diff_test(s, "CAPEX_ADJ", X4, FE, "IND", "HIGHER_SPREAD", v)
    ptab = pd.DataFrame({"ours": pv, "paper": P.T3_P}).round(3)
    block("Table 3 - lower vs higher event-window spreads; positive vs negative CAR", R,
          ["CAR", "CAR_POS", "CAR_NEG", "MKTRET", "CAR_PRE"], P.T3, P.T3_N,
          "(1),(3) Lower spreads; (2),(4) Higher spreads. Controls as Table 2 (8). FE firm+yr-qtr, cluster industry.",
          paper_r2=P.T3_R2)
    EXTRA["t3_p"] = {k: (None if not np.isfinite(v) else float(v)) for k, v in pv.items()}
    EXTRA["n_lower"], EXTRA["n_higher"] = int(R[1].nobs), int(R[2].nobs)
    MD.append("\np-values of differences (Lower vs Higher spreads):\n\n" + ptab.to_markdown())
    print(ptab.to_string())


# ============================================================================ Table 4
def table4(c, r8):
    b = r8.coef["CAR_z"]
    d = c.copy()
    pred_pct = b * d["CAR_z"]
    fore, act = d["CAPEX_FORE_raw"], d["CAPEX_ACT_raw"]          # un-winsorised: keeps ACT = FORE + MKT + OTH
    mkt = pred_pct / 100.0 * fore
    oth = act - fore - mkt                                     # D34: in $, so CAPEX = FORE + MKT + OTH exactly
    at = d["AT_T"].where(d["AT_T"] > 0)
    d["CAPEX_ADJ_MKT"] = U.winsorize(mkt / at * 100)
    d["CAPEX_ADJ_OTH"] = U.winsorize(oth / at * 100)
    for v, src in (("CAPEX", "CAPEX_AT"), ("CAPEX_FORE_AT", "FORE_AT"), ("CAPEX_ADJ_MKT", "CAPEX_ADJ_MKT"),
                   ("CAPEX_ADJ_OTH", "CAPEX_ADJ_OTH")):
        d[v + "_z"] = U.zscore(d[src])
    d = d.rename(columns={"CAPEX_FORE_AT_z": "CAPEX_FORE_z"})
    comp = ["CAPEX_FORE_z", "CAPEX_ADJ_MKT_z", "CAPEX_ADJ_OTH_z"]
    ctrl_all = ["SIZE", "LAG_CAPX", "SURP", "EA_DUM"]
    R, m = {}, 0
    for y in ("CFO1", "IBEI1", "NI1"):
        s = d.dropna(subset=[y, "SIZE", "CAPEX_z", *comp])
        R[m + 1] = run(s, y, ["CAPEX_z", "SIZE"], FE, "gvkey", "T4", m + 1, P.T4)
        R[m + 2] = run(s, y, [*comp, "SIZE"], FE, "gvkey", "T4", m + 2, P.T4)
        R[m + 3] = run(s, y, [*comp, *ctrl_all], FE, "gvkey", "T4", m + 3, P.T4)
        m += 3
    block("Table 4 - future performance (t+1) on capex components", R,
          ["CAPEX", "CAPEX_FORE", "CAPEX_ADJ_MKT", "CAPEX_ADJ_OTH", "SIZE"], P.T4, P.T4_N,
          f"(1)-(3) CFO, (4)-(6) IBEI, (7)-(9) NI, % of assets. CAPEX_ADJ_MKT = {b:.3f} x CAR_z (Table 2 model 8). "
          "FE firm+yr-qtr, cluster firm.")


# ============================================================================ Table 5
def split_panel(c, key, var, labels, title):
    """var: splitting variable. MF_OF is already 0/1; others split at the median (D36)."""
    s = c.dropna(subset=["CAPEX_ADJ", "CAR_z", var, *CTRL8]).copy()
    flag = "_F_" + var
    if var == "MF_OF":
        s[flag] = s[var].astype(int)
    else:
        ref = s[var] if C.SPLIT_MEDIAN_ON == "estimation" else c[var]
        s[flag] = (s[var] > ref.median()).astype(int)
    X = ["CAR_z", *CTRL8]
    R, pv, cols = {}, [], []
    subs = {"All": s, "Lower": s[s["HIGHER_SPREAD"] == 0], "Higher": s[s["HIGHER_SPREAD"] == 1]}
    m = 0
    for sname, sd in subs.items():
        for g in (0, 1):
            m += 1
            try:
                R[m] = run(sd[sd[flag] == g], "CAPEX_ADJ", X, FE, "IND", f"T5{key}", m, label=f"{sname}-{labels[g]}")
            except Exception as e:  # tiny subsamples in the synthetic test
                print(f"  [{key} {m}] skipped: {e}")
                R[m] = None
            cols.append(f"({m}) {sname}: {labels[g]}")
        try:
            pv.append(diff_test(sd, "CAPEX_ADJ", X, FE, "IND", flag, "CAR_z"))
        except Exception:
            pv.append(np.nan)
    t = P.T5[key]
    rows = [["CAR"] + [fmt(r, "CAR_z") for r in R.values()],
            ["  paper"] + [f"{a:.3f} ({b:.3f})" for a, b in zip(t["coef"], t["se"])],
            ["N"] + [f"{r.nobs:,}" if r else "" for r in R.values()],
            ["  paper N"] + [f"{n:,}" for n in t["n"]],
            ["p diff (ours)", f"{pv[0]:.3f}", "", f"{pv[1]:.3f}", "", f"{pv[2]:.3f}", ""],
            ["p diff (paper)", f"{t['p'][0]:.3f}", "", f"{t['p'][1]:.3f}", "", f"{t['p'][2]:.3f}", ""]]
    tab = pd.DataFrame(rows, columns=[""] + cols)
    MD.append(f"\n## Table 5 {title}\n\n" + tab.to_markdown(index=False))
    print(f"\n== Table 5 {title}\n" + tab.to_string(index=False))


def table5(c):
    panels = [("A_PIN", "PIN", ("Low PIN", "High PIN"), "Panel A - informed trading (PIN)"),
              ("B_INSIDER", "INSIDER", ("Low INSIDER", "High INSIDER"), "Panel B - insider trading"),
              ("C_ERC", "ERC", ("Smaller ERC", "Larger ERC"), "Panel C - investor catering (industry ERC)"),
              ("D_PAYDUR", "PAY_DUR", ("Less LT", "More LT"), "Panel D - CEO long-term orientation"),
              ("E2_MFOF", "MF_OF", ("MF_OF=0", "MF_OF=1"), "Panel E2 - mutual fund outflows")]
    for key, var, labels, title in panels:
        if var not in c or c[var].notna().sum() == 0:
            MD.append(f"\n## Table 5 {title}\n\n_skipped: {var} not available (see README, data/external)._\n")
            print(f"Table 5 {title}: skipped ({var} missing)")
            continue
        split_panel(c, key, var, labels, title)


def table5e1():
    if not U.exists("spread_panel"):
        return
    p = U.load("spread_panel")
    p["EVENT_x_MF_OF"] = p["EVENT"] * p["MF_OF"]
    p["EVENT_x_CAPEX"] = p["EVENT"] * p["CAPEX"]
    p["MF_OF_x_CAPEX"] = p["MF_OF"] * p["CAPEX"]
    p["EVENT_x_MF_OF_x_CAPEX"] = p["EVENT"] * p["MF_OF"] * p["CAPEX"]
    ctrl = ["SIZE", "TURNOVER", "RETVOL"]
    cap = p[p["CAPEX"] == 1].dropna(subset=["SPREAD", "EVENT", "MF_OF", *ctrl])
    allp = p.dropna(subset=["SPREAD", "EVENT", "MF_OF", *ctrl])
    T = P.T5E1
    R = {1: run(cap, "SPREAD", ["EVENT"], [], "gvkey", "T5E1", 1, T),
         2: run(cap, "SPREAD", ["EVENT"], FE, "gvkey", "T5E1", 2, T),
         3: run(cap, "SPREAD", ["EVENT", *ctrl], FE, "gvkey", "T5E1", 3, T),
         4: run(cap, "SPREAD", ["EVENT", "MF_OF", "EVENT_x_MF_OF", *ctrl], FE, "gvkey", "T5E1", 4, T),
         5: run(allp, "SPREAD", ["EVENT", "MF_OF", "EVENT_x_MF_OF", "CAPEX", "EVENT_x_CAPEX", "MF_OF_x_CAPEX",
                                 "EVENT_x_MF_OF_x_CAPEX", *ctrl], FE, "gvkey", "T5E1", 5, T)}
    med = cap.loc[cap["EVENT"] == 0, "SPREAD"].median()
    block("Table 5 Panel E1 - spreads around disclosures and mutual fund outflows", R,
          ["EVENT", "MF_OF", "EVENT_x_MF_OF", "CAPEX", "EVENT_x_CAPEX", "MF_OF_x_CAPEX", "EVENT_x_MF_OF_x_CAPEX",
           *ctrl], T, P.T5E1_N,
          f"Unit: event-day. Cluster firm. Median non-event spread (capex): {med:.3f} (paper 0.073).")
    figure1(cap, ctrl)


def figure1(cap, ctrl):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r = hdfe_ols(cap, "SPREAD", ctrl, FE, "gvkey", keep_resid=True)
    d = cap.loc[r.resid.index].copy()
    d["orth"] = r.resid + cap["SPREAD"].mean()
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    a = d.groupby("EVENT")["orth"].mean()
    ax[0].bar(["Non-event", "Event"], [a.get(0, np.nan), a.get(1, np.nan)], color=["#999", "#335"])
    ax[0].set_title("Panel A: non-event vs event")
    b = d.groupby(["MF_OF", "EVENT"])["orth"].mean().unstack()
    xs = np.arange(len(b.index))
    ax[1].bar(xs - 0.2, b.get(0), 0.4, label="Non-event", color="#999")
    ax[1].bar(xs + 0.2, b.get(1), 0.4, label="Event", color="#335")
    ax[1].set_xticks(xs, [f"MF_OF={int(i)}" for i in b.index])
    ax[1].legend(); ax[1].set_title("Panel B: by mutual fund outflows")
    for a_ in ax:
        a_.set_ylabel("Orthogonalized spread (%)")
    fig.tight_layout()
    fig.savefig(C.OUT / "figure1_spreads.png", dpi=150)
    MD.append("\n## Figure 1\n\n![Figure 1](figure1_spreads.png)\n")


# ============================================================================ robustness in the text
def robustness(c):
    """Footnotes 17-19, 23: alternative CAPEX_ADJ, point+range only, post-2008, ind x year / state x year FE,
    asset-growth control.  The paper reports numbers only for the two FE variants (0.800**, 0.968***)."""
    X = ["CAR_z", *CTRL8]
    b = c.dropna(subset=["CAPEX_ADJ", *X]).copy()
    b["CAPEX_ADJ_MID"] = U.winsorize((b["CAPEX_ACT_raw"] - b["CAPEX_FORE_raw"]) / b["CAPEX_FORE_raw"] * 100)
    b["IND_YEAR"] = b["IND"].astype(str) + "_" + b["YEAR"].astype(str)
    tgt = {("CAR", 5): (0.800, np.nan), ("CAR", 6): (0.968, np.nan)}
    R = {1: run(b, "CAPEX_ADJ", X, FE, "IND", "ROB", 1, tgt, "baseline T2(8)"),
         2: run(b, "CAPEX_ADJ_MID", X, FE, "IND", "ROB", 2, tgt, "adj. vs midpoint"),
         3: run(b[b["FTYPE"].isin(["point", "range"])], "CAPEX_ADJ", X, FE, "IND", "ROB", 3, tgt, "point+range"),
         4: run(b[b["YEAR"] >= 2009], "CAPEX_ADJ", X, FE, "IND", "ROB", 4, tgt, "post-2008"),
         5: run(b, "CAPEX_ADJ", X, [*FE, "IND_YEAR"], "IND", "ROB", 5, tgt, "+ind x year FE")}
    if "STATE" in b and b["STATE"].notna().any():
        b["STATE_YEAR"] = b["STATE"].astype(str) + "_" + b["YEAR"].astype(str)
        R[6] = run(b.dropna(subset=["STATE"]), "CAPEX_ADJ", X, [*FE, "STATE_YEAR"], "IND", "ROB", 6, tgt, "+state x year FE")
    R[7] = run(b, "CAPEX_ADJ", [*X, "ASSET_GROWTH"], FE, "IND", "ROB", 7, tgt, "+asset growth")
    block("Robustness reported in the text (footnotes 17-19, 23)", R, ["CAR", "ASSET_GROWTH"], tgt, None,
          "(1) baseline = Table 2 (8); (2) CAPEX_ADJ vs range midpoint; (3) point and range forecasts only; "
          "(4) forecasts from 2009 on; (5) + industry x year FE; (6) + state x year FE; (7) + asset growth.")


def magnitudes(c):
    """Economic magnitudes quoted in the text: coefficient (1 SD of CAR) / mean CAPEX_ADJ."""
    est = pd.DataFrame(LONG)
    mean_adj = c["CAPEX_ADJ"].mean()
    rows = []
    for tab, model, var, paper_pct, where in P.MAGNITUDES:
        r = est[(est.table == tab) & (est.model == model) & (est["var"] == var)]
        coef = float(r["coef"].iloc[0]) if len(r) else np.nan
        rows.append([f"{tab} ({model}) {var}", coef, mean_adj, coef / mean_adj * 100, paper_pct, where])
    t = pd.DataFrame(rows, columns=["coefficient", "ours coef", "ours mean CAPEX_ADJ", "ours % of mean",
                                    "paper % of mean", "source"])
    EXTRA["magnitudes"] = t.to_dict(orient="records")
    MD.append("\n## Economic magnitudes quoted in the text\n\n" + t.to_markdown(index=False, floatfmt=".2f"))
    print(t.to_string(index=False))


def text_checks(c):
    """Moments quoted in the text, useful as calibration targets."""
    rows = [("corr(SURP, CAR) [fn 22]", c[["SURP", "CAR"]].corr().iloc[0, 1], 0.08),
            ("corr(SURP, CAPEX_ADJ) [fn 22]", c[["SURP", "CAPEX_ADJ"]].corr().iloc[0, 1], 0.001),
            ("median CAR, capex forecasts (%) [fn 20]", c["CAR"].median(), 0.069),
            ("median SF_CAR, sales forecasts (%) [fn 20]", c["SF_CAR"].median(), 0.457),
            ("mean CFO_t+1 (% assets) [Sec 3.3]", c["CFO1"].mean(), 10.5),
            ("mean CAPEX_ADJ (%) [Table 1]", c["CAPEX_ADJ"].mean(), 7.421),
            ("sd CAR (%) [fn 15]", c["CAR"].std(), 8.974),
            ("share Higher spreads [Table 3: 9,570/17,340]", c["HIGHER_SPREAD"].mean(), 9570 / 17340),
            ("share MF_OF=1 [Table 5 E2: 4,432/17,505]", c["MF_OF"].mean() if "MF_OF" in c else np.nan, 4432 / 17505)]
    car = c["CAR"].dropna()
    tstat = car.mean() / (car.std() / np.sqrt(len(car)))
    rows += [("mean CAR (%) [fn 15]", car.mean(), -0.148), ("t-stat of mean CAR [fn 15: sig. at 5%]", tstat, np.nan),
             ("min CAR (%) [Table 1]", car.min(), -31.359), ("max CAR (%) [Table 1]", car.max(), 25.350)]
    for k, v in (("point", "share_point"), ("range", "share_range"), ("other", "share_other")):
        rows.append((f"share {k} forecasts [Table 1C]", (c["FTYPE"] == k).mean(), P.TEXT_T13[v][0]))
    t = pd.DataFrame(rows, columns=["moment", "ours", "paper"])
    EXTRA["text"] = [dict(moment=m, ours=(None if not np.isfinite(o) else float(o)),
                          paper=(None if p is None or not np.isfinite(p) else float(p))) for m, o, p in rows]
    MD.append("\n## Moments quoted in the text (calibration targets)\n\n" + t.to_markdown(index=False, floatfmt=".3f"))
    print(t.to_string(index=False))


# ============================================================================ Table 6
def table6():
    if not U.exists("forecast_panel"):
        return
    q = U.load("forecast_panel")
    ctrl = ["LEV", "SIZE", "TANG", "ROA", "NEG_ROA", "ROA_VOL"]
    q12 = q.dropna(subset=["TREAT", "NOISE_SIGNAL", *ctrl]) if C.T6_COMMON_SAMPLE else q    # D33
    R = {1: run(q12, "TREAT", ["NOISE_SIGNAL"], FE, "gvkey", "T6", 1, P.T6),
         2: run(q12, "TREAT", ["NOISE_SIGNAL", *ctrl], FE, "gvkey", "T6", 2, P.T6)}
    if "NOISE_SIGNAL_LO_ERC" in q:
        x34 = ["NOISE_SIGNAL_LO_ERC", "NOISE_SIGNAL_HI_ERC"]
        q34 = q.dropna(subset=["TREAT", *x34, *ctrl]) if C.T6_COMMON_SAMPLE else q
        R[3] = run(q34, "TREAT", x34, FE, "gvkey", "T6", 3, P.T6)
        R[4] = run(q34, "TREAT", [*x34, *ctrl], FE, "gvkey", "T6", 4, P.T6)
    block("Table 6 - mutual fund outflows and the likelihood of a capex forecast (LPM)", R,
          ["NOISE_SIGNAL", "NOISE_SIGNAL_LO_ERC", "NOISE_SIGNAL_HI_ERC", *ctrl], P.T6, P.T6_N,
          f"TREAT mean {q['TREAT'].mean():.4f} (paper 0.07). FE firm+yr-qtr, cluster firm.")


STATA_COLS = ["gvkey", "YQ", "IND", "CAPEX_ADJ", "CAR_z", "SIZE", "LAG_CAPX", "SURP", "EA_DUM", "MKTRET_z",
              "CAR_PRE_z", "SF_CAR", "HIGHER_SPREAD", "CAR_POS_z", "CAR_NEG_z"]


def export_for_stata(c):
    """Regression sample for stata/tables_2_3.do (cross-check of hdfe.py against reghdfe).
    Firm-level WRDS-derived data -> data/interim (git-ignored), never output/."""
    C.INTERIM.mkdir(parents=True, exist_ok=True)
    f = C.INTERIM / "capex_sample_for_stata.csv"
    c[[x for x in STATA_COLS if x in c]].to_csv(f, index=False)
    print(f"stata export: {f} ({len(c):,} rows)")


def main():
    C.OUT.mkdir(parents=True, exist_ok=True)
    c = U.load("capex_sample")
    export_for_stata(c)
    MD.append("# Replication of Jayaraman & Wu (2020, RFS) - results vs paper\n\n"
              "Cells: coef (se); stars at 10/5/1% (two-tailed, t with G-1 df). 'paper' rows: May-2019 version.\n")
    wf = C.OUT / "sample_waterfall.csv"
    if wf.exists():
        MD.append("\n## Sample waterfall\n\n" + pd.read_csv(wf).to_markdown(index=False))
    table1(c)
    r8 = table2(c)
    table3(c)
    magnitudes(c)
    if C.SCOPE != "t13":
        table4(c, r8)
        table5(c)
    robustness(c)
    text_checks(c)
    if C.SCOPE != "t13":
        table5e1()
        table6()
    (C.OUT / "tables.md").write_text("\n".join(MD), encoding="utf-8")
    pd.DataFrame(LONG).to_csv(C.OUT / "estimates_long.csv", index=False)
    import json
    EXTRA["scope"] = C.SCOPE
    EXTRA["n_final"], EXTRA["n_firms"] = int(len(c)), int(c["gvkey"].nunique())
    EXTRA["mean_CAPEX_ADJ"] = float(c["CAPEX_ADJ"].mean())
    (C.OUT / "results_extra.json").write_text(json.dumps(EXTRA, indent=1, default=float), encoding="utf-8")
    print(f"\nwritten: {C.OUT / 'tables.md'}, {C.OUT / 'estimates_long.csv'}")


if __name__ == "__main__":
    main()
