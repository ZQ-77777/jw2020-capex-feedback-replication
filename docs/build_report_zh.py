"""
Build docs/REPORT_PREDATA_zh.html - the pre-data replication report for Tables 1-3 (Chinese).

    python docs/build_report_zh.py

Prose lives in docs/report_zh_template.html; this script inserts (i) source excerpts cut from the
package with their real line numbers, (ii) the three tables with one explanation card per cell.
Re-run it after any code change so the line numbers stay right.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import paper_targets as P  # noqa: E402
from report import PAPER_STARS  # noqa: E402
from report_tools import code_block, func_span, js_notes, line_of, one_line, ref, region_span  # noqa: E402

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
R("collapse", BC, 'wf.append(("w0_ibes_capex_forecasts"', "# ---- link IBES", "计数与 firm-quarter 去重（D6）")
R("link_actual", BC, "# ---- link IBES", "# ---- market reaction", "链接三库并取实际 capex")
F("link_ibes", UT, "link_ibes_permno")
F("link_ccm", UT, "link_permno_gvkey")
R("waterfall_car", BC, "# ---- market reaction", "# ---- drop forecasts concurrent", "样本第 2 步：有五日 CAR")
R("waterfall_eps", BC, "# ---- drop forecasts concurrent", "# ---- one observation per firm-quarter, if not", "样本第 3、4 步")
F("daily", UT, "daily_with_tidx")
F("day0", UT, "day0")
F("event_window", UT, "event_window")
F("car", UT, "car")
R("event_vars", BC, "# ---- event-study variables", "# ---- EA_DUM and SURP", "MKTRET、CAR_PRE、价差分组")
R("ea_surp", BC, "# ---- EA_DUM and SURP", "# ---- SIZE", "EA_DUM 与 SURP")
F("load_fundq", BC, "load_fundq")
F("load_funda", BC, "load_funda")
R("size", BC, "# ---- SIZE", "# ---- LAG_CAPX", "SIZE")
R("lag_capx", BC, "# ---- LAG_CAPX", "# ---- asset growth", "LAG_CAPX")
F("firm_industry", BC, "firm_industry")
R("fe_ids", BC, "# ---- fixed effects / clusters", "# ---- falsification", "固定效应与聚类变量")
R("sf_car", BC, "# ---- falsification", 'if C.SCOPE != "t13":', "SF_CAR")
R("winsor_z", BC, "# ---- winsorise", 'U.save(c, "capex_sample")', "缩尾与标准化")
F("winsorize", UT, "winsorize")
F("zscore", UT, "zscore")
F("demean", HD, "demean")
F("fe_dof", HD, "_fe_dof")
F("hdfe_ols", HD, "hdfe_ols")
F("diff_test", HD, "diff_test")
R("table1", TB, "def table1(c):", "# D14 check", "Table 1 统计量")
F("table2", TB, "table2")
F("table3", TB, "table3")


def A(key):            # link to an anchored excerpt
    f, a, b, _ = ANCH[key]
    return ref(f, a, b, anchor="code-" + key)


def CODE(key):         # the excerpt itself
    f, a, b, t = ANCH[key]
    return code_block(f, a, b, t, anchor="code-" + key)


# ----------------------------------------------------------------------------- notes shared with the study guide
GUIDE = HERE.parent / "GUIDE.html"
AN, N2, N3 = js_notes(GUIDE, "AN"), js_notes(GUIDE, "N2"), js_notes(GUIDE, "N3")


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
        zh="资本支出预测值", unit="百万美元", sym="F",
        fx="F = val_1（点预测、开放式）；F = (val_1 + val_2) / 2（区间预测）",
        chain=["<code>ibes.det_guidance</code>：measure = CPX，pdicity = ANN，2002–2016 年发布",
               f"统一换算为百万美元（{A('clean_guidance')}）",
               f"每个公告日只留最近一个财年、最新一次修订（{A('annual_forecasts')}）",
               f"按 val_1 / val_2 判断点、区间、开放式，并求 F（{A('classify')}）",
               "经过 §4 的样本筛选后进入最终样本；金额变量<b>不缩尾</b>（D14）"],
        code=["classify"], win=False),
    "CAPEX_ACT": dict(
        zh="实际资本支出", unit="百万美元", sym="A",
        fx="A = CAPX（被预测财年；Compustat 财年末 datadate 的年月 = IBES prd_yr / prd_mon）",
        chain=[f"IBES ticker → PERMNO（公告日有效的链接，{A('link_ibes')}）",
               f"PERMNO → GVKEY（CCM LU/LC 链接，主链接优先，{A('link_ccm')}）",
               f"按 (GVKEY, 年月) 合并 <code>comp.funda.capx</code>（{A('link_actual')}）",
               "找不到实际值的预测在样本第 1 步被删除；<b>不缩尾</b>"],
        code=["link_actual"], win=False),
    "CAPEX_ADJ": dict(
        zh="资本支出调整（因变量）", unit="%", sym="CAPEX_ADJ",
        fx="CAPEX_ADJ = 100 × (A − H) / F 若 A &gt; H；100 × (A − L) / F 若 A &lt; L；否则 0。点预测 L = H = F；区间预测 L、H 为下界和上界，F 为中点",
        chain=["由 F、L、H（Table 1 第 1 行）和 A（第 2 行）计算",
               f"分段公式（{A('capex_adj')}）",
               f"按全样本 1% / 99% 分位缩尾（{A('winsor_z')}）"],
        code=["capex_adj", "winsor_z"], win=True),
    "CAR": dict(
        zh="公告期累计超额收益", unit="%", sym="CAR",
        fx="CAR = 100 × Σ<sub>k=−2</sub><sup>+2</sup> (r<sub>i,t₀+k</sub> − r<sup>S&amp;P</sup><sub>t₀+k</sub>)，t₀ = 公告日或其后第一个交易日",
        chain=[f"日超额收益 ar = <code>dsf.ret</code> − <code>dsi.sprtrn</code>（{A('daily')}）",
               f"day 0 = 公告日或之后第一个交易日（{A('day0')}）",
               f"取 [−2, +2] 五天求和 × 100，五天必须齐全（{A('car')}）",
               f"缩尾（{A('winsor_z')}）；Table 1 报告的是缩尾后、<b>未标准化</b>的 CAR"],
        code=["car"], win=True),
    "SIZE": dict(
        zh="公司规模", unit="ln(百万美元)", sym="SIZE",
        fx="SIZE = ln(PRCCQ × CSHOQ)，取公告所在季度之前最后一个财季（183 天内）",
        chain=[f"<code>comp.fundq</code>：mvq = prccq × cshoq（{A('load_fundq')}）",
               f"merge_asof 到“公告季度第一天的前一天”之前最近的财季（{A('size')}）",
               "取自然对数；<b>不缩尾</b>"],
        code=["size"], win=False),
    "LAG_CAPX_MIL": dict(
        zh="上一财年资本支出", unit="百万美元", sym="CAPX<sub>t−1</sub>",
        fx="Table 1：CAPX<sub>t−1</sub>（百万美元）；回归中：LAG_CAPX = 100 × CAPX<sub>t−1</sub> / (PRCC_F × CSHO)<sub>t−1</sub>",
        chain=[f"<code>comp.funda</code>：公告日前最近一个已结束财年的 capx（400 天内，{A('lag_capx')}）",
               f"年初市值 mv = prcc_f × csho（{A('load_funda')}），仅用于回归口径",
               "Table 1 用百万美元口径（不缩尾）；回归用比例口径（缩尾）"],
        code=["lag_capx"], win=False),
    "SURP": dict(
        zh="盈余变化", unit="美元/股", sym="SURP",
        fx="若 EA_DUM = 1：SURP = EPSPXQ<sub>q</sub> − EPSPXQ<sub>q−4</sub> × AJEXQ<sub>q</sub> / AJEXQ<sub>q−4</sub>；否则 SURP = 0",
        chain=[f"<code>comp.fundq</code>：去年同季 EPS 按拆股调整到当前股本口径（{A('load_fundq')}，D32）",
               f"找到 |公告日 − rdq| ≤ 1 天的盈余公告（{A('ea_surp')}）",
               "没有同时发布的盈余公告时记 0；缩尾"],
        code=["ea_surp"], win=True),
    "EA_DUM": dict(
        zh="是否与盈余公告同时发布", unit="0/1", sym="EA_DUM",
        fx="EA_DUM = 1{ |anndats − rdq| ≤ 1 个日历日 }",
        chain=[f"<code>comp.fundq.rdq</code>（盈余公告日）与预测公告日比较（{A('ea_surp')}，D10）"],
        code=["ea_surp"], win=False),
}
COLS = [("Obs.", "观测数 N", "N = Σ<sub>i</sub> 1{x<sub>i</sub> 非缺失}", "len(s)"),
        ("Mean", "均值", "x̄ = (1/N) Σ<sub>i</sub> x<sub>i</sub>", "s.mean()"),
        ("Median", "中位数", "第 50 百分位数", "s.median()"),
        ("S.D.", "标准差", "s = √[ Σ<sub>i</sub> (x<sub>i</sub> − x̄)² / (N − 1) ]", "s.std()（pandas 默认 N − 1）"),
        ("Min", "最小值", "min<sub>i</sub> x<sub>i</sub>", "s.min()"),
        ("Max", "最大值", "max<sub>i</sub> x<sub>i</sub>", "s.max()")]
T1_LINE = one_line(TB, 'rows.append([v, f"{len(s):,}", s.mean()')
AN_KEY = {"LAG_CAPX_MIL": "LAG_CAPX"}


def check_t1(v, c):
    if c in (4, 5):
        return ("对照 <code>output/table1_winsor_check.csv</code>：论文的极值更接近原始极值还是 1% / 99% 分位，"
                "由此判断论文是否缩尾了这个变量（D14）。")
    if c == 0:
        return "与论文观测数比较；差异来自样本筛选（§4）或该变量的缺失。"
    if v == "EA_DUM":
        return "校准目标：0.559。偏离时检查 D10（±1 个日历日）和 rdq 的缺失比例。"
    if v == "CAPEX_ADJ" and c == 2:
        return "中位数应为 0；不为 0 时先检查区间预测是否识别正确（D3）。"
    if v == "CAPEX_ADJ" and c == 1:
        return "偏差大时检查单位（D4）、区间分母（D7）、缩尾（D14）。"
    return "均值、标准差与论文的差异应在可解释范围内（数据库已回溯修订）。"


def t1a():
    rows = []
    for ri, (v, tgt) in enumerate(P.T1A.items()):
        m = VAR[v]
        label = "LAG_CAPX" if v == "LAG_CAPX_MIL" else v
        CARDS[f"t1a-row-{ri}"] = card(f"Row：{label}（{m['zh']}）", [
            ("定义", m["fx"]), ("单位", m["unit"]), ("从原始数据到变量", ul(m["chain"])),
            ("是否缩尾", "是（1% / 99%）" if m["win"] else "否（金额水平变量，D14）"),
            ("代码", "；".join(A(k) for k in m["code"]))])
        tds = []
        for ci, (cn, czh, cfx, ccode) in enumerate(COLS):
            x = tgt[ci]
            shown = n0(x) if ci == 0 else fmt(x)
            k = f"t1a-{ri}-{ci}"
            note = AN.get(f"{AN_KEY.get(v, v)}|{ci}", "")
            CARDS[k] = card(f"Table 1A · {label} · {cn} = {shown}", [
                ("这个数", f"{czh}：论文中 {label}（{m['zh']}）的{czh}为 {shown}（单位：{m['unit']}）。"),
                ("说明了什么", note or "—"),
                ("计算公式", f"<div class='fx'>{cfx}</div>其中 x<sub>i</sub> 为第 i 个预测的 {label}："
                             f"<div class='fx'>{m['fx']}</div>"),
                ("从原始数据到这个数", ul(m["chain"] + [f"对最终样本的 {label} 计算{czh}"])),
                ("代码", "变量：" + "；".join(A(k) for k in m["code"]) + f"；统计量：<code>{ccode}</code>" + T1_LINE),
                ("复现时核对", check_t1(v, ci))])
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{shown}</td>')
        rows.append(f'<tr><th class="lab cx" tabindex="0" data-k="t1a-row-{ri}">{label}</th>{"".join(tds)}</tr>')
    for ci, (cn, czh, cfx, ccode) in enumerate(COLS):
        CARDS[f"t1a-col-{ci}"] = card(f"Column：{cn}（{czh}）", [
            ("公式", f"<div class='fx'>{cfx}</div>"), ("代码", f"<code>{ccode}</code>" + T1_LINE),
            ("为什么报告", ["说明样本量与缺失", "经济显著性的分母（CAPEX_ADJ 均值 7.421）",
                         "不受极端值影响；与均值比较判断偏态", "标准化变量的“一个单位”（CAR 的 8.974）",
                         "检查异常值、判断是否缩尾", "检查异常值、判断是否缩尾"][ci])])
    head = "".join(f'<th class="cx" tabindex="0" data-k="t1a-col-{i}">{c[0]}</th>' for i, c in enumerate(COLS))
    return f'<table class="anno"><thead><tr><th class="lab">Variable</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def t1b():
    rows = []
    prev = None
    for y, (f_, ft) in P.T1B.items():
        k1, k2 = f"t1b-{y}-0", f"t1b-{y}-1"
        chg = "" if prev is None else f"比上一年{'增加' if f_ >= prev else '减少'} {abs(f_ / prev - 1) * 100:.1f}%。"
        CARDS[k1] = card(f"Table 1B · {y} · Forecasts = {n0(f_)}", [
            ("这个数", f"{y} 年<b>发布</b>的公司-季度 capex 预测数（按公告日的日历年，不是被预测的财年）。{chg}"),
            ("计算公式", "<div class='fx'>N<sub>y</sub> = Σ<sub>i</sub> 1{ year(anndats<sub>i</sub>) = y }</div>"),
            ("代码", "<code>c.groupby(\"YEAR\").size()</code>" + one_line(TB, 'b = pd.DataFrame({"forecasts": c.groupby("YEAR").size()')),
            ("复现时核对", "早期年份明显偏少时，先看 <code>check_wrds.py</code> 打印的 IBES 原始逐年计数（覆盖面差异）。")])
        CARDS[k2] = card(f"Table 1B · {y} · First-time = {n0(ft)}", [
            ("这个数", f"{y} 年第一次出现在样本中的公司数；占当年预测数的 {ft / f_ * 100:.1f}%。"),
            ("计算公式", "<div class='fx'>首次年份<sub>j</sub> = min{ year(anndats<sub>i</sub>) : i 属于公司 j }；FT<sub>y</sub> = Σ<sub>j</sub> 1{首次年份<sub>j</sub> = y}</div>"),
            ("代码", one_line(TB, 'first = c.groupby("gvkey")["YEAR"].min()')),
            ("说明了什么", "13 年合计 1,790 家 = 样本公司总数；后期新公司越来越少，样本以持续披露的公司为主。")])
        rows.append(f'<tr><th class="lab">{y}</th><td class="cx" tabindex="0" data-k="{k1}">{n0(f_)}</td>'
                    f'<td class="cx" tabindex="0" data-k="{k2}">{n0(ft)}</td></tr>')
        prev = f_
    tot_f, tot_t = sum(v[0] for v in P.T1B.values()), sum(v[1] for v in P.T1B.values())
    CARDS["t1b-total"] = card(f"Total：{n0(tot_f)} 个预测，{n0(tot_t)} 家公司", [
        ("核对", f"逐年加总 = {n0(tot_f)}（= 最终样本量）；首次公司数加总 = {n0(tot_t)}（= 公司总数）。平均每家公司 {tot_f / tot_t:.1f} 个预测。")])
    rows.append(f'<tr class="sep"><th class="lab">Total</th><td class="cx" tabindex="0" data-k="t1b-total">{n0(tot_f)}</td>'
                f'<td class="cx" tabindex="0" data-k="t1b-total">{n0(tot_t)}</td></tr>')
    return ('<table class="anno"><thead><tr><th class="lab">Year</th><th>Forecasts</th><th>First-time</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def t1c():
    desc = {"point": ("Point（点预测）", "val_2 缺失或等于 val_1，且 range_desc 不属于开放式代码", "F = val_1；CAPEX_ADJ = 100 × (A − F) / F"),
            "range": ("Range（区间预测）", "val_2 非缺失且 ≠ val_1", "F = 中点；区间内 0，区间外按越过的边界"),
            "other": ("Others（开放式）", "range_desc 属于 <code>RANGE_DESC_OPEN_ENDED</code>（拿到数据后校准，D3）", "按 val_1 的点预测处理（D8）")}
    rows = []
    for i, (k, (n, sh)) in enumerate(P.T1C.items()):
        lab, rule, adj = desc[k]
        CARDS[f"t1c-{i}"] = card(f"Table 1C · {lab}：{n0(n)}（{sh:.2%}）", [
            ("分类规则", rule), ("CAPEX_ADJ 计算", adj),
            ("计算公式", "<div class='fx'>share<sub>type</sub> = N<sub>type</sub> / 17,577</div>"),
            ("代码", A("classify") + one_line(TB, 'pc = c["FTYPE"].value_counts()')),
            ("复现时核对", "这三个比例是校准 D3 的直接目标：在看任何回归之前，先让比例接近 55.30 / 34.48 / 10.22%。")])
        rows.append(f'<tr><th class="lab">{lab}</th><td class="cx" tabindex="0" data-k="t1c-{i}">{n0(n)}</td>'
                    f'<td class="cx" tabindex="0" data-k="t1c-{i}">{sh * 100:.2f}</td></tr>')
    return ('<table class="anno"><thead><tr><th class="lab">Type</th><th>Number</th><th>%</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


# ============================================================================= Tables 2 and 3
STD = {"CAR", "SF_CAR", "MKTRET", "CAR_PRE", "CAR_POS", "CAR_NEG"}
VREAD = {"CAR": "CAR 高一个标准差（8.974 个百分点）", "SF_CAR": "销售预测的反应高一个标准差", "MKTRET": "公告日大盘收益高一个标准差",
         "CAR_PRE": "伪事件日的反应高一个标准差", "SIZE": "ln(市值) 高 1（市值约 2.7 倍）",
         "LAG_CAPX": "上年 capex 占年初市值高 1 个百分点", "SURP": "每股盈余同比多 1 美元",
         "EA_DUM": "与盈余公告同日发布", "CAR_POS": "正面反应高一个标准差", "CAR_NEG": "负面反应部分高一个标准差（即不那么负）"}
VSEC = {"CAR": "v-car", "SF_CAR": "v-sf", "MKTRET": "v-mkt", "CAR_PRE": "v-mkt", "SIZE": "v-size", "LAG_CAPX": "v-lag",
        "SURP": "v-surp", "EA_DUM": "v-surp", "CAR_POS": "v-std", "CAR_NEG": "v-std"}
VZ = {"CAR": "CAR_z", "SF_CAR": "SF_CAR_z", "MKTRET": "MKTRET_z", "CAR_PRE": "CAR_PRE_z", "CAR_POS": "CAR_POS_z", "CAR_NEG": "CAR_NEG_z"}
T2SPEC = {1: ("CAPEX_ADJ = α + β·CAR_z", "无", "公司", "base"),
          2: ("CAPEX_ADJ = α + β·CAR_z + γ·SIZE", "无", "公司", "base"),
          3: ("CAPEX_ADJ = β·CAR_z + γ·SIZE + 年季 FE", "年季", "公司", "base"),
          4: ("CAPEX_ADJ = β·CAR_z + γ·SIZE + 公司 FE + 年季 FE", "公司、年季", "公司", "base"),
          5: ("同 (4)", "公司、年季", "两位 SIC 行业", "base"),
          6: ("CAPEX_ADJ = β·CAR_z + δ·SF_CAR_z + γ·SIZE + 公司 FE + 年季 FE", "公司、年季", "行业", "base 中有 SF_CAR 的子样本；SF_CAR 在子样本内标准化"),
          7: ("CAPEX_ADJ = β·CAR_z + δ₁·MKTRET_z + δ₂·CAR_PRE_z + γ·SIZE + FE", "公司、年季", "行业", "base"),
          8: ("CAPEX_ADJ = β·CAR_z + δ₁·MKTRET_z + δ₂·CAR_PRE_z + γ'(SIZE, LAG_CAPX, SURP, EA_DUM) + FE", "公司、年季", "行业", "base，再去掉控制变量缺失的观测")}
T3SPEC = {1: ("Table 2 (8) 的设定，只用 HIGHER_SPREAD = 0（价差未上升）", "lo"),
          2: ("Table 2 (8) 的设定，只用 HIGHER_SPREAD = 1（价差上升）", "hi"),
          3: ("CAR 换成 CAR_POS_z、CAR_NEG_z，HIGHER_SPREAD = 0", "lo"),
          4: ("CAR 换成 CAR_POS_z、CAR_NEG_z，HIGHER_SPREAD = 1", "hi")}
EST = ("<ol class='chain'>"
       "<li>取本列样本中所有回归变量、固定效应和聚类变量都非缺失的观测，得到 N。</li>"
       "<li>有固定效应时，用交替投影把 y 和每个 x 对各组固定效应反复去均值，直到收敛：x̃ ← x − x̄<sub>firm</sub>，x̃ ← x̃ − x̄<sub>yq</sub>，……（"
       + A("demean") + "）；没有固定效应时加常数项。</li>"
       "<li>β̂ = (X̃′X̃)<sup>−1</sup> X̃′ỹ，残差 û = ỹ − X̃β̂。</li>"
       "<li>聚类稳健方差：V̂ = c · (X̃′X̃)<sup>−1</sup> [ Σ<sub>g</sub> S<sub>g</sub>′S<sub>g</sub> ] (X̃′X̃)<sup>−1</sup>，"
       "S<sub>g</sub> = Σ<sub>i∈g</sub> x̃<sub>i</sub> û<sub>i</sub>，c = G/(G−1) · (N−1)/(N−K)，"
       "K = 回归变量数 + 未嵌套在聚类变量中的固定效应自由度（" + A("fe_dof") + "）。</li>"
       "<li>SE = √V̂<sub>jj</sub>；t = β̂ / SE；p = 2 · Pr( t<sub>G−1</sub> &gt; |t| )；*** / ** / * 对应 p &lt; 0.01 / 0.05 / 0.10。</li>"
       "</ol>全部在 " + A("hdfe_ols") + " 中实现。")


def coef_card(tab, v, m, b, se, stars, spec_rows, code_html, note):
    t = b / se
    lo, hi = b - 1.96 * se, b + 1.96 * se
    sig = ("1% 水平显著" if abs(t) >= 2.58 else "5% 水平显著" if abs(t) >= 1.96 else
           "10% 水平显著" if abs(t) >= 1.645 else "不显著（95% 置信区间包含 0）")
    read = f"{VREAD[v]} → CAPEX_ADJ {'高' if b >= 0 else '低'} {abs(b):.3f} 个百分点"
    if v in STD:
        read += f"，约为 CAPEX_ADJ 均值 7.421% 的 {b / 7.421 * 100:.1f}%"
    if v == "CAR_NEG":
        read = "CAR_NEG = min(CAR, 0) ≤ 0，系数为正表示反应越负 → 下调越多。" + read
    return card(f"{tab} · {v} · ({m}) = {fmt(b)}{stars} ({se:.3f})", [
        ("这个数", read + "。"),
        ("统计上", f"t = {t:.2f}（正态近似），95% 置信区间 [{lo:.2f}, {hi:.2f}]，{sig}。论文星号按 t(G−1) 判断，"
                  f"可能与正态近似略有不同。"),
        ("说明了什么", note or "—"),
        *spec_rows,
        ("怎么算出来", EST),
        ("变量从哪里来", f'<a href="#{VSEC[v]}">§5 中 {v} 的构造</a>' + (f"；回归中使用标准化后的 <code>{VZ[v]}</code> = (x − x̄)/s" if v in STD else "")),
        ("代码", code_html)])


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
            code = one_line(TB, f"R[{m}] = run(") + "完整函数：" + A("table2")
            CARDS[k] = coef_card("Table 2", v, m, b, se, st,
                                 [("本列回归", f"<div class='fx'>{eq}</div>样本：{smp}；固定效应：{fe}；聚类：{cl}")],
                                 code, N2.get(f"{v}|{m - 1}", ""))
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{fmt(b)}{st}<span class="se">({se:.3f})</span></td>')
        rows.append(f'<tr><th class="lab">{v}</th>{"".join(tds)}</tr>')
    fe = {m: T2SPEC[m][1] for m in range(1, 9)}
    cl = {m: T2SPEC[m][2] for m in range(1, 9)}
    bottom = [("Fixed effects", fe, "固定效应：<code>run(..., fe=...)</code> 的第 4 个参数，空列表 = 无固定效应。"),
              ("Clusters", cl, "聚类变量：<code>run(...)</code> 的第 5 个参数，<code>gvkey</code> = 公司，<code>IND</code> = 两位 SIC 行业（"
               + A("firm_industry") + "）。只影响标准误。"),
              ("Obs.", {m: n0(P.T2_N[m]) for m in range(1, 9)},
               "N = 本列回归中所有变量非缺失的观测数。(1)–(5)、(7) 相同（同一 base 样本，保留 singletons，D25）；(6) 需要有 SF_CAR；(8) 再去掉控制变量缺失的。"),
              ("Adj. R²", {m: f"{P.T2_R2[m]:.3f}" for m in range(1, 9)},
               "<div class='fx'>R² = 1 − Σû² / Σ(y − ȳ)²，Adj. R² = 1 − (1 − R²)(N − 1)/(N − k)</div>k = 回归变量数 + 全部固定效应自由度（含固定效应的解释力，reghdfe 口径）。")]
    for i, (lab, vals, expl) in enumerate(bottom):
        tds = []
        for m in range(1, 9):
            k = f"t2b-{i}-{m}"
            CARDS[k] = card(f"Table 2 · {lab} · ({m}) = {vals[m]}", [
                ("含义", expl), ("本列", f"<div class='fx'>{T2SPEC[m][0]}</div>"),
                ("代码", one_line(TB, f"R[{m}] = run(") + (A("hdfe_ols") if i >= 2 else ""))])
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{vals[m]}</td>')
        rows.append(f'<tr class="{"sep" if i == 0 else ""}"><th class="lab">{lab}</th>{"".join(tds)}</tr>')
    for m in range(1, 9):
        CARDS[f"t2-col-{m}"] = card(f"Column：Table 2 ({m})", [
            ("回归", f"<div class='fx'>{T2SPEC[m][0]}</div>"), ("样本", T2SPEC[m][3]),
            ("固定效应 / 聚类", f"{T2SPEC[m][1]} / {T2SPEC[m][2]}"), ("代码", one_line(TB, f"R[{m}] = run("))])
    head = "".join(f'<th class="cx" tabindex="0" data-k="t2-col-{m}">({m})</th>' for m in range(1, 9))
    return f'<table class="anno"><thead><tr><th class="lab"></th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


T3PKEY = {"CAR": "CAR", "CAR_POS": "CAR_POS", "CAR_NEG": "CAR_NEG", "MKTRET": "MKTRET_12", "CAR_PRE": "CAR_PRE_12"}
T3PNEEDLE = {"CAR": 'pv = {"CAR": diff_test', "MKTRET_12": '"MKTRET_12": diff_test', "CAR_PRE_12": '"CAR_PRE_12": diff_test',
             "CAR_POS": 'for v, k in (("CAR_POS_z", "CAR_POS")', "CAR_NEG": 'for v, k in (("CAR_POS_z", "CAR_POS")',
             "MKTRET_34": 'for v, k in (("CAR_POS_z", "CAR_POS")', "CAR_PRE_34": 'for v, k in (("CAR_POS_z", "CAR_POS")'}
DIFF = ("<div class='fx'>H₀：β<sub>Higher</sub> = β<sub>Lower</sub>；"
        "t = (β̂₁ − β̂₀) / √(V̂₁₁ + V̂₀₀ − 2V̂₁₀)，p = 2 · Pr( t<sub>G−1</sub> &gt; |t| )</div>"
        "β̂₁、β̂₀ 来自同一个合并回归：所有变量都乘以分组虚拟变量，公司和年季固定效应也按分组拆开，"
        "因此点估计与分开回归完全相同，而协方差 V̂ 是联合的、按行业聚类（相当于 Stata 的 <code>suest</code>）。实现："
        + A("diff_test") + "。")


def t3():
    names = ["CAR", "CAR_POS", "CAR_NEG", "MKTRET", "CAR_PRE"]
    rows = []
    for v in names:
        tds = []
        for m in range(1, 5):
            if (v, m) not in P.T3:
                tds.append("<td></td>")
                continue
            b, se = P.T3[(v, m)]
            st = PAPER_STARS.get(("T3", v, m), "")
            k = f"t3-{v}-{m}"
            spec, grp = T3SPEC[m]
            needle = {1: '1: run(lo, "CAPEX_ADJ"', 2: '2: run(hi, "CAPEX_ADJ"', 3: '3: run(lo, "CAPEX_ADJ"',
                      4: '4: run(hi, "CAPEX_ADJ"'}[m]
            CARDS[k] = coef_card("Table 3", v, m, b, se, st, [
                ("本列回归", spec + "；控制变量 SIZE、LAG_CAPX、SURP、EA_DUM、MKTRET_z、CAR_PRE_z；公司 + 年季固定效应；按行业聚类。"),
                ("分组规则", f"<a href='#v-spread'>§5 价差分组</a>：HIGHER_SPREAD = 1{{ 平均价差[−2,+2] &gt; 平均价差[−10,−3] }}")],
                one_line(TB, needle) + "完整函数：" + A("table3"), N3.get(f"{v}|{m - 1}", ""))
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{fmt(b)}{st}<span class="se">({se:.3f})</span></td>')
        pk = T3PKEY[v]
        pv = P.T3_P.get(pk)
        alt = {"MKTRET": "MKTRET_34", "CAR_PRE": "CAR_PRE_34"}.get(v)
        shown = f"{pv:.3f}" + (f" / {P.T3_P[alt]:.3f}" if alt else "")
        k = f"t3p-{v}"
        CARDS[k] = card(f"Table 3 · 组间差异 p · {v} = {shown}", [
            ("这个数", f"{v} 在 Lower 与 Higher 两组之间的系数差异的 p 值" + ("（前者比较 (1)(2)，后者比较 (3)(4)）" if alt else "") + "。"),
            ("计算公式", DIFF),
            ("代码", one_line(TB, T3PNEEDLE[pk])),
            ("说明了什么", {"CAR": "0.019：两组差异在 5% 水平显著，是 Table 3 最关键的数字。",
                         "CAR_POS": "0.099：好评效应的组间差异在 10% 水平显著。",
                         "CAR_NEG": "0.262：差评效应在两组之间没有显著差异。",
                         "MKTRET": "两组对大盘收益的敏感度没有差别。", "CAR_PRE": "两组对伪事件日反应的敏感度没有差别。"}[v])])
        tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{shown}</td>')
        rows.append(f'<tr><th class="lab">{v}</th>{"".join(tds)}</tr>')
    for i, (lab, vals, expl) in enumerate([
            ("Obs.", [n0(P.T3_N[m]) for m in range(1, 5)],
             "两组样本量。7,770 + 9,570 = 17,340，比 Table 2 (8) 少 165 个（缺少买卖报价，价差无法计算）。"),
            ("Adj. R²", [f"{P.T3_R2[m]:.3f}" for m in range(1, 5)],
             "含固定效应的调整 R²（公式见 Table 2 的 Adj. R² 行）。")]):
        tds = []
        for m in range(1, 5):
            k = f"t3b-{i}-{m}"
            CARDS[k] = card(f"Table 3 · {lab} · ({m}) = {vals[m - 1]}", [("含义", expl), ("本列", T3SPEC[m][0])])
            tds.append(f'<td class="cx" tabindex="0" data-k="{k}">{vals[m - 1]}</td>')
        rows.append(f'<tr class="{"sep" if i == 0 else ""}"><th class="lab">{lab}</th>{"".join(tds)}<td></td></tr>')
    for m in range(1, 5):
        CARDS[f"t3-col-{m}"] = card(f"Column：Table 3 ({m})", [("回归", T3SPEC[m][0]), ("代码", one_line(TB, {1: '1: run(lo', 2: '2: run(hi', 3: '3: run(lo', 4: '4: run(hi'}[m]))])
    head = "".join(f'<th class="cx" tabindex="0" data-k="t3-col-{m}">({m}) {"Lower" if m % 2 else "Higher"}</th>' for m in range(1, 5))
    return (f'<table class="anno"><thead><tr><th class="lab"></th>{head}<th>p of diff.</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


# ============================================================================= assemble
def main():
    tpl = (HERE / "report_zh_template.html").read_text(encoding="utf-8")
    tables = {"T1A": t1a(), "T1B": t1b(), "T1C": t1c(), "T2": t2(), "T3": t3()}
    out = tpl
    for k, v in tables.items():
        out = out.replace("{{TABLE_" + k + "}}", v)
    out = re.sub(r"\{\{CODE:([a-z0-9_]+)\}\}", lambda m: CODE(m.group(1)), out)
    out = re.sub(r"\{\{REF:([a-z0-9_]+)\}\}", lambda m: A(m.group(1)), out)
    out = out.replace("{{CARDS_JSON}}", json.dumps(CARDS, ensure_ascii=False).replace("</", "<\\/"))
    out = out.replace("{{DATE}}", dt.date.today().isoformat())
    left = re.findall(r"\{\{[^}]+\}\}", out)
    if left:
        raise SystemExit(f"unfilled placeholders: {sorted(set(left))[:10]}")
    dst = HERE / "REPORT_PREDATA_zh.html"
    dst.write_text(out, encoding="utf-8")
    print(f"written {dst} ({len(out) // 1024} KB, {len(CARDS)} cell cards, {len(ANCH)} code excerpts)")


if __name__ == "__main__":
    main()
