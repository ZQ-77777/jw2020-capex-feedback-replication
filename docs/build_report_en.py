"""
Build docs/REPORT_PREDATA_en.html - the pre-data replication report for Tables 1-3 (English).

    python docs/build_report_en.py

Counterpart of build_report_zh.py: same structure, same code excerpts (cut from the source files with
their real line numbers), English text. Prose lives in docs/report_en_template.html.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import paper_targets as P  # noqa: E402
import report_tools as RT  # noqa: E402
from report import PAPER_STARS  # noqa: E402
from report_tools import code_block, func_span, one_line, ref, region_span  # noqa: E402

RT.set_lang("en")
BC, UT, HD, TB, PW = "build_capex_sample.py", "utils.py", "hdfe.py", "tables.py", "pull_wrds.py"

# ----------------------------------------------------------------------------- code anchors
ANCH: dict[str, tuple[str, int, int, str]] = {}


def F(key, file, name, title=""):
    a, b = func_span(file, name)
    ANCH[key] = (file, a, b, title or name)


def R(key, file, start, end, title):
    a, b = region_span(file, start, end)
    ANCH[key] = (file, a, b, title)


F("pull_guidance", PW, "pull_guidance")
F("pull_dsf", PW, "pull_dsf_windows")
F("clean_guidance", BC, "clean_guidance")
F("annual_forecasts", BC, "annual_forecasts")
F("classify", BC, "classify")
F("capex_adj", BC, "capex_adj")
R("collapse", BC, 'wf.append(("w0_ibes_capex_forecasts"', "# ---- link IBES", "count and firm-quarter collapse (D6)")
R("link_actual", BC, "# ---- link IBES", "# ---- market reaction", "link the three databases and attach actual capex")
F("link_ibes", UT, "link_ibes_permno")
F("link_ccm", UT, "link_permno_gvkey")
R("waterfall_car", BC, "# ---- market reaction", "# ---- drop forecasts concurrent", "sample step 2: five-day CAR")
R("waterfall_eps", BC, "# ---- drop forecasts concurrent", "# ---- one observation per firm-quarter, if not", "sample steps 3 and 4")
F("daily", UT, "daily_with_tidx")
F("day0", UT, "day0")
F("event_window", UT, "event_window")
F("car", UT, "car")
R("event_vars", BC, "# ---- event-study variables", "# ---- EA_DUM and SURP", "MKTRET, CAR_PRE, spread split")
R("ea_surp", BC, "# ---- EA_DUM and SURP", "# ---- SIZE", "EA_DUM and SURP")
F("load_fundq", BC, "load_fundq")
F("load_funda", BC, "load_funda")
R("size", BC, "# ---- SIZE", "# ---- LAG_CAPX", "SIZE")
R("lag_capx", BC, "# ---- LAG_CAPX", "# ---- asset growth", "LAG_CAPX")
F("firm_industry", BC, "firm_industry")
R("fe_ids", BC, "# ---- fixed effects / clusters", "# ---- falsification", "fixed-effect and cluster identifiers")
R("sf_car", BC, "# ---- falsification", 'if C.SCOPE != "t13":', "SF_CAR")
R("winsor_z", BC, "# ---- winsorise", 'U.save(c, "capex_sample")', "winsorising and standardising")
F("winsorize", UT, "winsorize")
F("zscore", UT, "zscore")
F("demean", HD, "demean")
F("fe_dof", HD, "_fe_dof")
F("hdfe_ols", HD, "hdfe_ols")
F("diff_test", HD, "diff_test")
R("table1", TB, "def table1(c):", "# D14 check", "Table 1 statistics")
F("table2", TB, "table2")
F("table3", TB, "table3")


def A(key):
    f, a, b, _ = ANCH[key]
    return ref(f, a, b, anchor="code-" + key)


def CODE(key):
    f, a, b, t = ANCH[key]
    return code_block(f, a, b, t, anchor="code-" + key)


# ----------------------------------------------------------------------------- cell notes (English)
AN = {
    "CAPEX_FORE|0": "17,577 is the final sample: each row is one capex forecast by one firm in one calendar quarter. Table 2 models (1)–(5) and (7) use exactly these observations.",
    "CAPEX_FORE|1": "The average forecast is about $590 million: these are large decisions that managers have a strong incentive to get right. A few very large energy and telecom forecasts pull the mean up.",
    "CAPEX_FORE|2": "The median is $120 million, about one fifth of the mean: the typical forecast is far smaller than the average one. Mean ≫ median indicates a right-skewed distribution.",
    "CAPEX_FORE|3": "The standard deviation is 2.2 times the mean. Because dollar amounts span several orders of magnitude, the dependent variable is a percentage (CAPEX_ADJ) rather than a dollar difference, which would let a few large firms dominate.",
    "CAPEX_FORE|4": "$2 million: small firms also issue capex forecasts.",
    "CAPEX_FORE|5": "$8 billion: either the largest forecast or a 99th-percentile cap. <code>table1_winsor_check.csv</code> decides on the real data.",
    "CAPEX_ACT|0": "Every forecast has an actual capex value: sample step 1 requires Compustat data for the forecasted fiscal year.",
    "CAPEX_ACT|1": "654.1 is 11.5% above the mean forecast of 586.5: on average firms end up spending more than planned.",
    "CAPEX_ACT|2": "123.5 is only 2.9% above the median forecast of 120: the typical firm spends roughly as planned; the overspending comes mainly from large firms.",
    "CAPEX_ACT|3": "1,527 exceeds the forecast's 1,318: actual spending is more dispersed than planned spending, so plans are revised during the year.",
    "CAPEX_ACT|4": "A minimum of 0: some firms spent nothing in the year (for example, a cancelled project). It also indicates that dollar levels are not winsorised, since a 1st-percentile cap would be positive.",
    "CAPEX_ACT|5": "About $9.5 billion.",
    "CAPEX_ADJ|0": "The dependent variable has no missing values.",
    "CAPEX_ADJ|1": "An average upward revision of 7.421%. It is the denominator of the economic magnitudes in the text: 1.193 / 7.421 = 16.1% and 0.849 / 7.421 = 11.4%. It differs from (654.1 − 586.5) / 586.5 = 11.5% because CAPEX_ADJ averages firm-level ratios with equal weights, sets range forecasts met inside the range to 0, and is winsorised.",
    "CAPEX_ADJ|2": "A median of exactly 0: the typical forecast is met. This is the signature of the rule that range forecasts met inside the range count as 0 (Panel C: 34.48% are ranges). A non-zero median in the replication points first to the classification of forecast types (D3).",
    "CAPEX_ADJ|3": "48.5 is 6.5 times the mean: adjustments vary far more than their average. Table 2 asks how much of this variation is related to the market reaction.",
    "CAPEX_ADJ|4": "The largest downward revision is 77%. A point forecast followed by zero capex would give −100, which does not appear, so CAPEX_ADJ is winsorised.",
    "CAPEX_ADJ|5": "The largest upward revision is 291% (actual about 3.9 times the forecast).",
    "CAR|0": "Every forecast has a complete five-day return window: sample step 2 (40,785 → 36,900) requires it.",
    "CAR|1": "−0.148%, significant at 5% (footnote 15): on average the market reacts slightly negatively to spending plans.",
    "CAR|2": "A median close to zero: the typical forecast moves the price little, and positive and negative reactions roughly balance.",
    "CAR|3": "8.974% is the length of “one standard deviation” in Tables 2 and 3. Every CAR coefficient reads as the change in CAPEX_ADJ, in percentage points, for a reaction 8.974 points higher.",
    "CAR|4": "About −31%. Among 17,577 five-day windows more extreme returns almost surely occur, so this is most likely a winsorised value.",
    "CAR|5": "About +25%, asymmetric to the minimum, also consistent with 1% / 99% winsorising.",
    "SIZE|1": "e^7.378 ≈ $1.6 billion: a typical mid- to large-cap listed firm.",
    "SIZE|2": "e^7.344 ≈ $1.55 billion. Mean and median almost coincide: the log makes the heavily skewed market-value distribution nearly symmetric, which is why it is used.",
    "SIZE|3": "One standard deviation corresponds to a factor of e^1.629 ≈ 5.1 in market value.",
    "SIZE|4": "e^1.366 ≈ $3.9 million: a micro-cap.",
    "SIZE|5": "e^11.3 ≈ $81 billion. The largest firms in the sample period were worth far more, so either SIZE is winsorised or the largest firms rarely issue capex forecasts.",
    "LAG_CAPX|0": "17,546, 31 fewer than 17,577: no capex for the prior fiscal year (for example, newly listed firms). This is one reason the regression sample shrinks in Table 2 model (8).",
    "LAG_CAPX|1": "Prior-year actual 611.0 → this year's plan 586.5 → this year's actual 654.1: on average the plan is about 4% below last year's spending, while actual spending ends about 7% above it.",
    "LAG_CAPX|2": "118.3 → 120.0 → 123.5: the median firm grows slightly at each step.",
    "LAG_CAPX|4": "A minimum of 0, as for CAPEX_ACT: dollar levels are not winsorised.",
    "SURP|1": "EPS falls by about 3 cents a share year on year on average, close to zero.",
    "SURP|2": "A median of 0: the 44.1% of forecasts not issued with an earnings announcement have SURP set to 0.",
    "SURP|3": "$0.783 per share; its Table 2 coefficient reads per dollar of EPS change.",
    "SURP|4": "−$4.68 to +$3.21 per share, consistent with winsorising.",
    "EA_DUM|1": "55.9% of capex forecasts come with an earnings announcement: many firms give guidance on the earnings call. The announcement-window reaction may therefore mix in the earnings news, which is why it is controlled for.",
    "EA_DUM|2": "More than half are 1, so the median is 1.",
    "EA_DUM|3": "0.497 = √(0.559 × 0.441): the standard deviation of a 0/1 variable follows from its mean, a useful data check.",
    "EA_DUM|4": "A 0/1 variable.", "EA_DUM|5": "A 0/1 variable.",
}
N2 = {
    "CAR|0": "The relation exists: a more positive reaction goes with a larger upward revision. 1.193 / 7.421 = 16.1%, the figure quoted in the abstract and introduction.",
    "CAR|1": "Almost unchanged after adding SIZE (1.193 → 1.207): CAR is not proxying for firm size.",
    "CAR|2": "Almost unchanged after adding year-quarter fixed effects (1.207 → 1.196): the relation is not driven by aggregate conditions that raise both prices and investment.",
    "CAR|3": "Falls by about 18% with firm fixed effects (1.196 → 0.975) but stays significant at 1%: part of the association is across firms, but within the same firm a better reaction still goes with a larger revision. 0.975 / 7.421 = 13.1%.",
    "CAR|4": "Identical to model (4); the standard error rises from 0.294 to 0.322 with the more conservative industry clustering. In the replication these two coefficients must be identical.",
    "CAR|5": "0.672, significant only at 10%. The smaller coefficient partly reflects the 3,456-observation subsample, which also inflates the standard error. The point of this column is SF_CAR.",
    "CAR|6": "1.006 with two placebos added, close to 0.975 in model (5): the placebos do not absorb the CAR effect.",
    "CAR|7": "0.849*** with all controls: 11.4% of the mean adjustment, about $5 million at the mean forecast of $587 million. This is the paper's baseline estimate.",
    "SF_CAR|5": "0.039, essentially zero and insignificant, about one seventeenth of CAR (0.672): the reaction to the same fiscal year's sales forecast does not predict capex adjustments. Managers respond to the market's view of the capex plan itself, not to any good news.",
    "MKTRET|6": "Insignificant: managers do not adjust investment to the market's daily return.",
    "MKTRET|7": "Still insignificant.",
    "CAR_PRE|6": "0.305, insignificant: the firm is not already on a rising price-and-investment trend.",
    "CAR_PRE|7": "Still insignificant.",
    "SIZE|1": "1.485**: a firm about 2.7 times larger revises upward about 1.5 percentage points more.",
    "SIZE|2": "Still significant after controlling for time.",
    "SIZE|3": "0.419 and insignificant with firm fixed effects: the size effect is across firms (larger firms revise up more), not within a firm as it grows.",
    "SIZE|5": "3.351, insignificant; a different subsample with a large standard error.",
    "SIZE|7": "−1.513, insignificant; the sign flips but the standard error is large, so it should not be interpreted.",
    "LAG_CAPX|7": "−0.160***: the higher last year's capex relative to market value, the more this year's spending falls short of the plan, consistent with mean reversion. The size of the coefficient depends on the units: the paper does not report the distribution of the scaled LAG_CAPX; with a standard deviation of 10 points, one standard deviation would correspond to about 1.6 points of adjustment. This coefficient is the most sensitive to the unit choice (D15) and will be re-expressed per standard deviation on the real data.",
    "SURP|7": "0.213, insignificant: contemporaneous earnings news does not explain the adjustments. With footnote 22 (corr(SURP, CAR) = 0.08), CAR is not proxying for earnings news.",
    "EA_DUM|7": "−0.108, insignificant: forecasts issued with an earnings announcement are not revised differently.",
}
N3 = {
    "CAR|0": "−0.295, insignificant: when the forecast draws no informed trading, the market reaction does not predict the capex adjustment. −0.295 / 7.421 = −3.9%, if anything negative.",
    "CAR|1": "1.206**: when the forecast draws informed trading, a one-standard-deviation higher reaction goes with a 1.2-point larger upward revision (16.2% of the mean), larger than the full-sample 0.849, which mixes in the Lower group with no effect.",
    "CAR_POS|2": "−0.203, insignificant: positive reactions without informed trading do not move investment.",
    "CAR_POS|3": "0.893*: positive reactions that draw informed trading are followed by additional investment. t = 1.96 earns one star because the paper clusters by industry and uses t(G − 1).",
    "CAR_NEG|2": "−0.045, close to zero.",
    "CAR_NEG|3": "0.185, insignificant: negative reactions do not lead to significant cuts, consistent with Edmans, Goldstein &amp; Jiang (2015), where negative information is traded into prices less, and inconsistent with a disciplining channel.",
    "MKTRET|0": "Insignificant.",
    "MKTRET|1": "Insignificant; difference from (1) p = 0.656: the Higher group is not simply more sensitive to all information.",
    "MKTRET|2": "Almost the same as (1) (0.104 vs 0.103): splitting CAR leaves the other coefficients unchanged.",
    "MKTRET|3": "Almost the same as (2); difference from (3) p = 0.658.",
    "CAR_PRE|0": "0.452, insignificant.",
    "CAR_PRE|1": "0.124, insignificant; difference from (1) p = 0.540: reactions on ordinary days matter in neither group.",
    "CAR_PRE|2": "Almost the same as (1).",
    "CAR_PRE|3": "Almost the same as (2); difference from (3) p = 0.549.",
}


def fmt(x, d=3):
    return f"{x:,.{d}f}".replace("-", "−")


def n0(x):
    return f"{int(round(x)):,}"


def card(title, rows):
    h = f"<h5>{title}</h5><dl>"
    for k, v in rows:
        if v:
            h += f"<dt>{k}</dt><dd>{v}</dd>"
    return h + "</dl>"


def ul(items):
    return "<ol class='chain'>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"


CARDS: dict[str, str] = {}

# ============================================================================= Table 1 Panel A
VAR = {
    "CAPEX_FORE": dict(
        name="capex forecast", unit="$ million",
        fx="F = val_1 (point and open-ended forecasts); F = (val_1 + val_2) / 2 (range forecasts)",
        chain=["<code>ibes.det_guidance</code>: measure = CPX, pdicity = ANN, announced 2002–2016",
               f"values converted to $ million ({A('clean_guidance')})",
               f"per announcement date, nearest fiscal year and latest revision only ({A('annual_forecasts')})",
               f"point, range or open-ended from val_1 / val_2, and F computed ({A('classify')})",
               "enters the final sample after the steps in §5; a dollar level, <b>not winsorised</b> (D14)"],
        code=["classify"], win=False),
    "CAPEX_ACT": dict(
        name="actual capex", unit="$ million",
        fx="A = CAPX of the forecasted fiscal year (Compustat datadate year and month = I/B/E/S prd_yr / prd_mon)",
        chain=[f"I/B/E/S ticker → PERMNO, link valid on the announcement date ({A('link_ibes')})",
               f"PERMNO → GVKEY, CCM LU/LC links, primary first ({A('link_ccm')})",
               f"merge <code>comp.funda.capx</code> on (GVKEY, year-month) ({A('link_actual')})",
               "forecasts without an actual value drop out at sample step 1; <b>not winsorised</b>"],
        code=["link_actual"], win=False),
    "CAPEX_ADJ": dict(
        name="capex adjustment (dependent variable)", unit="%",
        fx="CAPEX_ADJ = 100 × (A − H) / F if A &gt; H; 100 × (A − L) / F if A &lt; L; 0 otherwise. Point forecasts: L = H = F; range forecasts: L, H are the bounds and F the midpoint",
        chain=["computed from F, L, H (row 1) and A (row 2)",
               f"piecewise formula ({A('capex_adj')})",
               f"winsorised at the full-sample 1st / 99th percentiles ({A('winsor_z')})"],
        code=["capex_adj", "winsor_z"], win=True),
    "CAR": dict(
        name="announcement-window cumulative abnormal return", unit="%",
        fx="CAR = 100 × Σ<sub>k=−2</sub><sup>+2</sup> (r<sub>i,t₀+k</sub> − r<sup>S&amp;P</sup><sub>t₀+k</sub>), t₀ = announcement date or the next trading day",
        chain=[f"daily abnormal return ar = <code>dsf.ret</code> − <code>dsi.sprtrn</code> ({A('daily')})",
               f"day 0 = first trading day on or after the announcement ({A('day0')})",
               f"sum over days −2 to +2, × 100; all five returns required ({A('car')})",
               f"winsorised ({A('winsor_z')}); Table 1 reports the winsorised, <b>unstandardised</b> CAR"],
        code=["car"], win=True),
    "SIZE": dict(
        name="firm size", unit="ln($ million)",
        fx="SIZE = ln(PRCCQ × CSHOQ) at the last fiscal quarter ending before the forecast's calendar quarter (within 183 days)",
        chain=[f"<code>comp.fundq</code>: mvq = prccq × cshoq ({A('load_fundq')})",
               f"merge_asof to the latest fiscal quarter ending by the day before the forecast quarter starts ({A('size')})",
               "natural log; <b>not winsorised</b>"],
        code=["size"], win=False),
    "LAG_CAPX_MIL": dict(
        name="prior-year capex", unit="$ million",
        fx="Table 1: CAPX<sub>t−1</sub> ($ million); regressions: LAG_CAPX = 100 × CAPX<sub>t−1</sub> / (PRCC_F × CSHO)<sub>t−1</sub>",
        chain=[f"<code>comp.funda</code>: capx of the latest fiscal year ended before the forecast (within 400 days, {A('lag_capx')})",
               f"start-of-year market value mv = prcc_f × csho ({A('load_funda')}), used only in the regression version",
               "Table 1 uses $ million (not winsorised); regressions use the scaled version (winsorised)"],
        code=["lag_capx"], win=False),
    "SURP": dict(
        name="earnings change", unit="$ per share",
        fx="If EA_DUM = 1: SURP = EPSPXQ<sub>q</sub> − EPSPXQ<sub>q−4</sub> × AJEXQ<sub>q</sub> / AJEXQ<sub>q−4</sub>; otherwise SURP = 0",
        chain=[f"<code>comp.fundq</code>: EPS of the same quarter a year earlier, split-adjusted to today's share basis ({A('load_fundq')}, D32)",
               f"earnings announcement with |announcement date − rdq| ≤ 1 day ({A('ea_surp')})",
               "0 when no earnings announcement accompanies the forecast; winsorised"],
        code=["ea_surp"], win=True),
    "EA_DUM": dict(
        name="issued with an earnings announcement", unit="0/1",
        fx="EA_DUM = 1{ |anndats − rdq| ≤ 1 calendar day }",
        chain=[f"<code>comp.fundq.rdq</code> (earnings announcement date) compared with the forecast date ({A('ea_surp')}, D10)"],
        code=["ea_surp"], win=False),
}
COLS = [("Obs.", "number of observations", "N = Σ<sub>i</sub> 1{x<sub>i</sub> non-missing}", "len(s)"),
        ("Mean", "mean", "x̄ = (1/N) Σ<sub>i</sub> x<sub>i</sub>", "s.mean()"),
        ("Median", "median", "50th percentile", "s.median()"),
        ("S.D.", "standard deviation", "s = √[ Σ<sub>i</sub> (x<sub>i</sub> − x̄)² / (N − 1) ]", "s.std() (pandas default N − 1)"),
        ("Min", "minimum", "min<sub>i</sub> x<sub>i</sub>", "s.min()"),
        ("Max", "maximum", "max<sub>i</sub> x<sub>i</sub>", "s.max()")]
WHY = ["sample size and missing values", "denominator of the economic magnitudes (CAPEX_ADJ mean 7.421)",
       "robust to extremes; compared with the mean it reveals skewness", "the “one unit” of a standardised variable (8.974 for CAR)",
       "checks outliers and whether the variable is winsorised", "checks outliers and whether the variable is winsorised"]
T1_LINE = one_line(TB, 'rows.append([v, f"{len(s):,}", s.mean()')
AN_KEY = {"LAG_CAPX_MIL": "LAG_CAPX"}


def check_t1(v, c):
    if c in (4, 5):
        return ("Compare with <code>output/table1_winsor_check.csv</code>: whether the paper's extreme is closer to the raw "
                "extreme or to the 1st / 99th percentile tells whether the paper winsorised this variable (D14).")
    if c == 0:
        return "Compare with the paper's count; gaps come from the sample steps (§5) or from missing values of this variable."
    if v == "EA_DUM":
        return "Calibration target 0.559; if off, check D10 (±1 calendar day) and the share of missing rdq."
    if v == "CAPEX_ADJ" and c == 2:
        return "Should be 0; if not, check first that range forecasts are classified correctly (D3)."
    if v == "CAPEX_ADJ" and c == 1:
        return "If far off, check units (D4), the range denominator (D7) and winsorising (D14)."
    return "Differences from the paper should be explainable (the databases have been revised since 2019)."


def t1a():
    rows = []
    for ri, (v, tgt) in enumerate(P.T1A.items()):
        m = VAR[v]
        label = "LAG_CAPX" if v == "LAG_CAPX_MIL" else v
        CARDS[f"t1a-row-{ri}"] = card(f"Row: {label} ({m['name']})", [
            ("Definition", m["fx"]), ("Unit", m["unit"]), ("From raw data", ul(m["chain"])),
            ("Winsorised", "Yes (1% / 99%)" if m["win"] else "No (dollar level, D14)"),
            ("Code", "; ".join(A(k) for k in m["code"]))])
        tds = []
        for ci, (cn, cname, cfx, ccode) in enumerate(COLS):
            x = tgt[ci]
            shown = n0(x) if ci == 0 else fmt(x)
            k = f"t1a-{ri}-{ci}"
            CARDS[k] = card(f"Table 1A · {label} · {cn} = {shown}", [
                ("The number", f"The paper's {cname} of {label} ({m['name']}) is {shown} (unit: {m['unit']})."),
                ("What it shows", AN.get(f"{AN_KEY.get(v, v)}|{ci}", "") or "—"),
                ("Formula", f"<div class='fx'>{cfx}</div>where x<sub>i</sub> is forecast i's {label}:<div class='fx'>{m['fx']}</div>"),
                ("From raw data to this number", ul(m["chain"] + [f"{cname} of {label} over the final sample"])),
                ("Code", "Variable: " + "; ".join(A(k) for k in m["code"]) + f"; statistic: <code>{ccode}</code>" + T1_LINE),
                ("Check when replicating", check_t1(v, ci))])
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{shown}</td>')
        rows.append(f'<tr><th class="lab cx" tabindex="0" data-k="t1a-row-{ri}">{label}</th>{"".join(tds)}</tr>')
    for ci, (cn, cname, cfx, ccode) in enumerate(COLS):
        CARDS[f"t1a-col-{ci}"] = card(f"Column: {cn} ({cname})", [
            ("Formula", f"<div class='fx'>{cfx}</div>"), ("Code", f"<code>{ccode}</code>" + T1_LINE), ("Why reported", WHY[ci])])
    head = "".join(f'<th class="cx" tabindex="0" data-k="t1a-col-{i}">{c[0]}</th>' for i, c in enumerate(COLS))
    return f'<table class="anno"><thead><tr><th class="lab">Variable</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def t1b():
    rows, prev = [], None
    for y, (f_, ft) in P.T1B.items():
        k1, k2 = f"t1b-{y}-0", f"t1b-{y}-1"
        chg = "" if prev is None else f" {'Up' if f_ >= prev else 'Down'} {abs(f_ / prev - 1) * 100:.1f}% on the previous year."
        CARDS[k1] = card(f"Table 1B · {y} · Forecasts = {n0(f_)}", [
            ("The number", f"Capex forecasts (firm-quarters) <b>announced</b> in {y}, by calendar year of the announcement, not the forecasted fiscal year.{chg}"),
            ("Formula", "<div class='fx'>N<sub>y</sub> = Σ<sub>i</sub> 1{ year(anndats<sub>i</sub>) = y }</div>"),
            ("Code", "<code>c.groupby(\"YEAR\").size()</code>" + one_line(TB, 'b = pd.DataFrame({"forecasts": c.groupby("YEAR").size()')),
            ("Check when replicating", "If early years are short, compare with the raw I/B/E/S counts by year printed by <code>check_wrds.py</code> (coverage differences).")])
        CARDS[k2] = card(f"Table 1B · {y} · First-time = {n0(ft)}", [
            ("The number", f"Firms appearing in the sample for the first time in {y}; {ft / f_ * 100:.1f}% of that year's forecasts."),
            ("Formula", "<div class='fx'>first year<sub>j</sub> = min{ year(anndats<sub>i</sub>) : i belongs to firm j }; FT<sub>y</sub> = Σ<sub>j</sub> 1{first year<sub>j</sub> = y}</div>"),
            ("Code", one_line(TB, 'first = c.groupby("gvkey")["YEAR"].min()')),
            ("What it shows", "The 13 years sum to 1,790, the number of firms; fewer new firms enter later, so the sample is dominated by firms that keep disclosing.")])
        rows.append(f'<tr><th class="lab">{y}</th><td class="cx" tabindex="0" data-k="{k1}">{n0(f_)}</td>'
                    f'<td class="cx" tabindex="0" data-k="{k2}">{n0(ft)}</td></tr>')
        prev = f_
    tf, tt = sum(v[0] for v in P.T1B.values()), sum(v[1] for v in P.T1B.values())
    CARDS["t1b-total"] = card(f"Total: {n0(tf)} forecasts, {n0(tt)} firms", [
        ("Check", f"Forecasts sum to {n0(tf)} (= final sample); first-time firms sum to {n0(tt)} (= number of firms). {tf / tt:.1f} forecasts per firm on average.")])
    rows.append(f'<tr class="sep"><th class="lab">Total</th><td class="cx" tabindex="0" data-k="t1b-total">{n0(tf)}</td>'
                f'<td class="cx" tabindex="0" data-k="t1b-total">{n0(tt)}</td></tr>')
    return ('<table class="anno"><thead><tr><th class="lab">Year</th><th>Forecasts</th><th>First-time</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def t1c():
    desc = {"point": ("Point", "val_2 missing or equal to val_1, and range_desc not an open-ended code", "F = val_1; CAPEX_ADJ = 100 × (A − F) / F"),
            "range": ("Range", "val_2 non-missing and ≠ val_1", "F = midpoint; 0 inside the range, distance to the violated bound outside"),
            "other": ("Others (open-ended)", "range_desc in <code>RANGE_DESC_OPEN_ENDED</code> (calibrated on the data, D3)", "treated as a point at val_1 (D8)")}
    rows = []
    for i, (k, (n, sh)) in enumerate(P.T1C.items()):
        lab, rule, adj = desc[k]
        CARDS[f"t1c-{i}"] = card(f"Table 1C · {lab}: {n0(n)} ({sh:.2%})", [
            ("Classification", rule), ("CAPEX_ADJ", adj),
            ("Formula", "<div class='fx'>share<sub>type</sub> = N<sub>type</sub> / 17,577</div>"),
            ("Code", A("classify") + one_line(TB, 'pc = c["FTYPE"].value_counts()')),
            ("Check when replicating", "These shares are the direct target for D3: before reading any regression, bring them close to 55.30 / 34.48 / 10.22%.")])
        rows.append(f'<tr><th class="lab">{lab}</th><td class="cx" tabindex="0" data-k="t1c-{i}">{n0(n)}</td>'
                    f'<td class="cx" tabindex="0" data-k="t1c-{i}">{sh * 100:.2f}</td></tr>')
    return ('<table class="anno"><thead><tr><th class="lab">Type</th><th>Number</th><th>%</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


# ============================================================================= Tables 2 and 3
STD = {"CAR", "SF_CAR", "MKTRET", "CAR_PRE", "CAR_POS", "CAR_NEG"}
VREAD = {"CAR": "A one-standard-deviation (8.974-point) higher CAR", "SF_CAR": "A one-standard-deviation higher sales-forecast reaction",
         "MKTRET": "A one-standard-deviation higher market return on day 0", "CAR_PRE": "A one-standard-deviation higher pseudo-event reaction",
         "SIZE": "A one-unit higher ln(market value) (about 2.7 times larger)", "LAG_CAPX": "Prior-year capex one point higher relative to start-of-year market value",
         "SURP": "EPS one dollar higher than a year earlier", "EA_DUM": "Issuing with an earnings announcement",
         "CAR_POS": "A one-standard-deviation higher positive reaction", "CAR_NEG": "A one-standard-deviation higher (less negative) negative reaction"}
VSEC = {"CAR": "v-car", "SF_CAR": "v-sf", "MKTRET": "v-mkt", "CAR_PRE": "v-mkt", "SIZE": "v-size", "LAG_CAPX": "v-lag",
        "SURP": "v-surp", "EA_DUM": "v-surp", "CAR_POS": "v-std", "CAR_NEG": "v-std"}
VZ = {"CAR": "CAR_z", "SF_CAR": "SF_CAR_z", "MKTRET": "MKTRET_z", "CAR_PRE": "CAR_PRE_z", "CAR_POS": "CAR_POS_z", "CAR_NEG": "CAR_NEG_z"}
T2SPEC = {1: ("CAPEX_ADJ = α + β·CAR_z", "none", "firm", "base"),
          2: ("CAPEX_ADJ = α + β·CAR_z + γ·SIZE", "none", "firm", "base"),
          3: ("CAPEX_ADJ = β·CAR_z + γ·SIZE + year-quarter FE", "year-quarter", "firm", "base"),
          4: ("CAPEX_ADJ = β·CAR_z + γ·SIZE + firm FE + year-quarter FE", "firm, year-quarter", "firm", "base"),
          5: ("as (4)", "firm, year-quarter", "two-digit SIC industry", "base"),
          6: ("CAPEX_ADJ = β·CAR_z + δ·SF_CAR_z + γ·SIZE + firm FE + year-quarter FE", "firm, year-quarter", "industry", "observations in base with SF_CAR; SF_CAR standardised within this subsample"),
          7: ("CAPEX_ADJ = β·CAR_z + δ₁·MKTRET_z + δ₂·CAR_PRE_z + γ·SIZE + FE", "firm, year-quarter", "industry", "base"),
          8: ("CAPEX_ADJ = β·CAR_z + δ₁·MKTRET_z + δ₂·CAR_PRE_z + γ′(SIZE, LAG_CAPX, SURP, EA_DUM) + FE", "firm, year-quarter", "industry", "base, less observations with missing controls")}
T3SPEC = {1: "Table 2 model (8) on HIGHER_SPREAD = 0 (spreads do not rise)",
          2: "Table 2 model (8) on HIGHER_SPREAD = 1 (spreads rise)",
          3: "CAR replaced by CAR_POS_z and CAR_NEG_z, HIGHER_SPREAD = 0",
          4: "CAR replaced by CAR_POS_z and CAR_NEG_z, HIGHER_SPREAD = 1"}
EST = ("<ol class='chain'>"
       "<li>Keep the observations of the column's sample with all regressors, fixed effects and the cluster variable non-missing: N.</li>"
       "<li>With fixed effects, demean y and each x by alternating projections until convergence: x̃ ← x − x̄<sub>firm</sub>, x̃ ← x̃ − x̄<sub>yq</sub>, … ("
       + A("demean") + "); without fixed effects, add a constant.</li>"
       "<li>β̂ = (X̃′X̃)<sup>−1</sup> X̃′ỹ, residuals û = ỹ − X̃β̂.</li>"
       "<li>Cluster-robust variance: V̂ = c · (X̃′X̃)<sup>−1</sup> [ Σ<sub>g</sub> S<sub>g</sub>′S<sub>g</sub> ] (X̃′X̃)<sup>−1</sup>, "
       "S<sub>g</sub> = Σ<sub>i∈g</sub> x̃<sub>i</sub> û<sub>i</sub>, c = G/(G−1) · (N−1)/(N−K), "
       "K = number of regressors + degrees of freedom of fixed effects not nested in the cluster variable (" + A("fe_dof") + ").</li>"
       "<li>SE = √V̂<sub>jj</sub>; t = β̂ / SE; p = 2 · Pr( t<sub>G−1</sub> &gt; |t| ); *** / ** / * for p &lt; 0.01 / 0.05 / 0.10.</li>"
       "</ol>All implemented in " + A("hdfe_ols") + ".")


def coef_card(tab, v, m, b, se, stars, spec_rows, code_html, note):
    t = b / se
    lo, hi = b - 1.96 * se, b + 1.96 * se
    sig = ("significant at 1%" if abs(t) >= 2.58 else "significant at 5%" if abs(t) >= 1.96 else
           "significant at 10%" if abs(t) >= 1.645 else "insignificant (the 95% interval contains 0)")
    read = f"{VREAD[v]} goes with a CAPEX_ADJ {abs(b):.3f} percentage points {'higher' if b >= 0 else 'lower'}"
    if v in STD:
        read += f", {b / 7.421 * 100:.1f}% of the mean CAPEX_ADJ of 7.421%"
    if v == "CAR_NEG":
        read = "CAR_NEG = min(CAR, 0) ≤ 0, so a positive coefficient means a more negative reaction goes with a larger cut. " + read
    return card(f"{tab} · {v} · ({m}) = {fmt(b)}{stars} ({se:.3f})", [
        ("The number", read + "."),
        ("Statistics", f"t = {t:.2f} (normal approximation), 95% interval [{lo:.2f}, {hi:.2f}], {sig}. The paper's stars use t(G−1) "
                       f"and can differ slightly from the normal approximation."),
        ("What it shows", note or "—"),
        *spec_rows,
        ("How it is computed", EST),
        ("Where the variable comes from", f'<a href="#{VSEC[v]}">construction of {v} in §6</a>' + (f"; the regression uses the standardised <code>{VZ[v]}</code> = (x − x̄)/s" if v in STD else "")),
        ("Code", code_html)])


def t2():
    names = ["CAR", "SF_CAR", "MKTRET", "CAR_PRE", "SIZE", "LAG_CAPX", "SURP", "EA_DUM"]
    rows = []
    for v in names:
        tds = []
        for m in range(1, 9):
            if (v, m) not in P.T2:
                tds.append("<td></td>")
                continue
            b, se = P.T2[(v, m)]
            st = PAPER_STARS.get(("T2", v, m), "")
            k = f"t2-{v}-{m}"
            eq, fe, cl, smp = T2SPEC[m]
            CARDS[k] = coef_card("Table 2", v, m, b, se, st,
                                 [("This column", f"<div class='fx'>{eq}</div>Sample: {smp}; fixed effects: {fe}; clusters: {cl}")],
                                 one_line(TB, f"R[{m}] = run(") + "Full function: " + A("table2"), N2.get(f"{v}|{m - 1}", ""))
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{fmt(b)}{st}<span class="se">({se:.3f})</span></td>')
        rows.append(f'<tr><th class="lab">{v}</th>{"".join(tds)}</tr>')
    bottom = [("Fixed effects", {m: T2SPEC[m][1] for m in range(1, 9)}, "Fixed effects: the 4th argument of <code>run(...)</code>; an empty list means none."),
              ("Clusters", {m: T2SPEC[m][2] for m in range(1, 9)}, "Cluster variable: the 5th argument of <code>run(...)</code>; <code>gvkey</code> = firm, <code>IND</code> = two-digit SIC industry ("
               + A("firm_industry") + "). Affects only the standard errors."),
              ("Obs.", {m: n0(P.T2_N[m]) for m in range(1, 9)},
               "N = observations with every variable of the column non-missing. Identical in (1)–(5) and (7) (one base sample, singletons kept, D25); (6) needs SF_CAR; (8) also drops missing controls."),
              ("Adj. R²", {m: f"{P.T2_R2[m]:.3f}" for m in range(1, 9)},
               "<div class='fx'>R² = 1 − Σû² / Σ(y − ȳ)², Adj. R² = 1 − (1 − R²)(N − 1)/(N − k)</div>k = regressors + all fixed-effect degrees of freedom (includes the fixed effects' explanatory power, as reghdfe).")]
    for i, (lab, vals, expl) in enumerate(bottom):
        tds = []
        for m in range(1, 9):
            k = f"t2b-{i}-{m}"
            CARDS[k] = card(f"Table 2 · {lab} · ({m}) = {vals[m]}", [
                ("Meaning", expl), ("This column", f"<div class='fx'>{T2SPEC[m][0]}</div>"),
                ("Code", one_line(TB, f"R[{m}] = run(") + (A("hdfe_ols") if i >= 2 else ""))])
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{vals[m]}</td>')
        rows.append(f'<tr class="{"sep" if i == 0 else ""}"><th class="lab">{lab}</th>{"".join(tds)}</tr>')
    for m in range(1, 9):
        CARDS[f"t2-col-{m}"] = card(f"Column: Table 2 ({m})", [
            ("Regression", f"<div class='fx'>{T2SPEC[m][0]}</div>"), ("Sample", T2SPEC[m][3]),
            ("Fixed effects / clusters", f"{T2SPEC[m][1]} / {T2SPEC[m][2]}"), ("Code", one_line(TB, f"R[{m}] = run("))])
    head = "".join(f'<th class="cx" tabindex="0" data-k="t2-col-{m}">({m})</th>' for m in range(1, 9))
    return f'<table class="anno"><thead><tr><th class="lab"></th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


T3PKEY = {"CAR": "CAR", "CAR_POS": "CAR_POS", "CAR_NEG": "CAR_NEG", "MKTRET": "MKTRET_12", "CAR_PRE": "CAR_PRE_12"}
T3PNEEDLE = {"CAR": 'pv = {"CAR": diff_test', "MKTRET_12": '"MKTRET_12": diff_test', "CAR_PRE_12": '"CAR_PRE_12": diff_test',
             "CAR_POS": 'for v, k in (("CAR_POS_z", "CAR_POS")', "CAR_NEG": 'for v, k in (("CAR_POS_z", "CAR_POS")'}
DIFF = ("<div class='fx'>H₀: β<sub>Higher</sub> = β<sub>Lower</sub>; "
        "t = (β̂₁ − β̂₀) / √(V̂₁₁ + V̂₀₀ − 2V̂₁₀), p = 2 · Pr( t<sub>G−1</sub> &gt; |t| )</div>"
        "β̂₁ and β̂₀ come from one pooled regression in which every regressor is multiplied by the group indicator and the firm and "
        "year-quarter fixed effects are split by group, so the point estimates equal the separate regressions while V̂ is joint and "
        "industry-clustered (the analogue of Stata <code>suest</code>). Implementation: " + A("diff_test") + ".")
T3NEEDLE = {1: '1: run(lo, "CAPEX_ADJ"', 2: '2: run(hi, "CAPEX_ADJ"', 3: '3: run(lo, "CAPEX_ADJ"', 4: '4: run(hi, "CAPEX_ADJ"'}


def t3():
    rows = []
    for v in ["CAR", "CAR_POS", "CAR_NEG", "MKTRET", "CAR_PRE"]:
        tds = []
        for m in range(1, 5):
            if (v, m) not in P.T3:
                tds.append("<td></td>")
                continue
            b, se = P.T3[(v, m)]
            st = PAPER_STARS.get(("T3", v, m), "")
            k = f"t3-{v}-{m}"
            CARDS[k] = coef_card("Table 3", v, m, b, se, st, [
                ("This column", T3SPEC[m] + "; controls SIZE, LAG_CAPX, SURP, EA_DUM, MKTRET_z, CAR_PRE_z; firm and year-quarter fixed effects; industry clusters."),
                ("Split", "<a href='#v-spread'>spread split in §6</a>: HIGHER_SPREAD = 1{ mean spread[−2,+2] &gt; mean spread[−10,−3] }")],
                one_line(TB, T3NEEDLE[m]) + "Full function: " + A("table3"), N3.get(f"{v}|{m - 1}", ""))
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{fmt(b)}{st}<span class="se">({se:.3f})</span></td>')
        pk = T3PKEY[v]
        alt = {"MKTRET": "MKTRET_34", "CAR_PRE": "CAR_PRE_34"}.get(v)
        shown = f"{P.T3_P[pk]:.3f}" + (f" / {P.T3_P[alt]:.3f}" if alt else "")
        k = f"t3p-{v}"
        CARDS[k] = card(f"Table 3 · p of difference · {v} = {shown}", [
            ("The number", f"p-value of the difference in the {v} coefficient between the Lower and Higher groups" + (" (first (1) vs (2), then (3) vs (4))" if alt else "") + "."),
            ("Formula", DIFF), ("Code", one_line(TB, T3PNEEDLE[pk])),
            ("What it shows", {"CAR": "0.019: the difference is significant at 5%, the key number of Table 3.",
                               "CAR_POS": "0.099: the difference in the positive-reaction effect is significant at 10%.",
                               "CAR_NEG": "0.262: no significant difference for negative reactions.",
                               "MKTRET": "The two groups are equally (in)sensitive to the market return.",
                               "CAR_PRE": "The two groups are equally (in)sensitive to pseudo-event reactions."}[v])])
        tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{shown}</td>')
        rows.append(f'<tr><th class="lab">{v}</th>{"".join(tds)}</tr>')
    for i, (lab, vals, expl) in enumerate([
            ("Obs.", [n0(P.T3_N[m]) for m in range(1, 5)],
             "Group sizes. 7,770 + 9,570 = 17,340, 165 fewer than Table 2 model (8): no bid-ask quotes to compute spreads."),
            ("Adj. R²", [f"{P.T3_R2[m]:.3f}" for m in range(1, 5)], "Adjusted R² including fixed effects (formula in the Table 2 Adj. R² row).")]):
        tds = []
        for m in range(1, 5):
            k = f"t3b-{i}-{m}"
            CARDS[k] = card(f"Table 3 · {lab} · ({m}) = {vals[m - 1]}", [("Meaning", expl), ("This column", T3SPEC[m])])
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{vals[m - 1]}</td>')
        rows.append(f'<tr class="{"sep" if i == 0 else ""}"><th class="lab">{lab}</th>{"".join(tds)}<td></td></tr>')
    for m in range(1, 5):
        CARDS[f"t3-col-{m}"] = card(f"Column: Table 3 ({m})", [("Regression", T3SPEC[m]), ("Code", one_line(TB, T3NEEDLE[m]))])
    head = "".join(f'<th class="cx" tabindex="0" data-k="t3-col-{m}">({m}) {"Lower" if m % 2 else "Higher"}</th>' for m in range(1, 5))
    return (f'<table class="anno"><thead><tr><th class="lab"></th>{head}<th>p of diff.</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def main():
    tpl = (HERE / "report_en_template.html").read_text(encoding="utf-8")
    out = tpl
    for k, v in {"T1A": t1a(), "T1B": t1b(), "T1C": t1c(), "T2": t2(), "T3": t3()}.items():
        out = out.replace("{{TABLE_" + k + "}}", v)
    out = re.sub(r"\{\{CODE:([a-z0-9_]+)\}\}", lambda m: CODE(m.group(1)), out)
    out = re.sub(r"\{\{REF:([a-z0-9_]+)\}\}", lambda m: A(m.group(1)), out)
    out = out.replace("{{CARDS_JSON}}", json.dumps(CARDS, ensure_ascii=False).replace("</", "<\\/"))
    left = re.findall(r"\{\{[^}]+\}\}", out)
    if left:
        raise SystemExit(f"unfilled placeholders: {sorted(set(left))[:10]}")
    dst = HERE / "REPORT_PREDATA_en.html"
    dst.write_text(out, encoding="utf-8")
    print(f"written {dst} ({len(out) // 1024} KB, {len(CARDS)} cell cards, {len(ANCH)} code excerpts)")


if __name__ == "__main__":
    main()
