# 复现说明 Replication Notes — Jayaraman & Wu (2020, RFS)

作者 Zhang Qi · 对应代码包 `jw2020/` · 本文件是“每一个数字从哪里来”的唯一说明。
凡标 **D#** (D1–D37) 的地方都对应 `config.py` 里一个可切换的开关 (switch) 或代码中的注释标签。
最后更新：2026-11-12（WRDS 数据下载于 2026-11-09 至 11-10，见 `data/raw/_pull_log.csv`）。

---

## 当前状态与结果 (status and results)

复现范围：Table 1–3。最终报告：`docs/report/JW2020_Replication_Report_ZH.pdf`（中文）、`docs/report/JW2020_Replication_Report_EN.pdf`（英文）。

| | 论文 | 本复现 |
|---|---|---|
| 最终样本 | 17,577 个预测，1,790 家公司 | 18,866 个预测，2,180 家公司（+7.3%） |
| T2 (1) CAR | 1.193*** | 1.193*** |
| T2 (4) CAR（公司 + 年季 FE） | 0.975*** | 1.017*** |
| T2 (8) CAR（全部控制变量） | 0.849*** | 0.988*** |
| T2 安慰剂 SF_CAR / MKTRET / CAR_PRE | 均不显著 | 均不显著 |
| T3 CAR：价差未升 / 上升 | −0.295 / 1.206** | 0.674** / 0.880** |
| T3 组间差异 p 值 | 0.019 | 0.672 |

* **Table 1–2 复现成功。** 样本量差 7.3%；Table 2 的 8 个 CAR 系数全部在论文的一个标准误以内；三个安慰剂不显著；脚注 20 的固定效应稳健性（0.78、0.75，论文 0.80、0.97）和正文引用的数字（如销售预测相隔天数中位数 86 天，与论文相同）都对得上。
* **Table 3 没有复现。** 两组都有效应，差异不显著；在 D9、D10 的备选设定下结论不变（`output/t3_sensitivity.md`）。诊断性拆分：不与财报同日发布的预测中，价差上升组 2.180**、未升组 0.709，方向与论文一致，但差异 p = 0.139，不显著。
* **所有设定下都存在的差异**（指向数据版本，而非代码）：CAR 均值 +0.32%（论文 −0.15%）；CAPEX_ADJ 均值 3.9%（7.4%）、中位数 −0.33%（0.000）；区间预测占 42.6%（34.5%），开放式占 2.8%（10.2%）；EA_DUM 0.662（0.559）；样本第 2 步论文删除 3,885 个，我们只删除 9 个。
* **预先登记的诊断（§4d）**：价差度量噪音被排除；I/B/E/S 事后回填被排除；公司层面过滤不能恢复论文模式。论文模式只在 2009 年后（差异 1.08，p = 0.058）和最接近论文的定义下（0.69，p = 0.222）部分出现。
* **分析在此停止。** 所有开关都按样本特征校准，诊断检验运行前已登记，没有为了让 Table 3 显著而继续搜索设定。

---

## 0. 论文在做什么 (one-paragraph summary)

管理层发布 **资本支出预测 (capex forecast, IBES Guidance 中 measure = CPX)** 之后，市场的反应
(**CAR**, 5 日 [-2,2] 超额收益 = 个股收益 − S&P 500 收益) 是否会“反馈 (feedback effect)”到管理层
最终的实际资本支出？因变量 **CAPEX_ADJ** = 实际 capex 相对预测值的偏离 (%)。

* **H1 (Tables 2–5)**：CAR 越高 → 实际 capex 向上调整越多。识别不靠外生冲击，而是靠
  “机制细节” (Rajan–Zingales 式)：效应只应出现在 **公告期价差上升 (Higher spreads, 信息交易增加)**、
  **正向反应 (CAR_POS, Edmans et al. 2015 的 limits-to-arbitrage)**、**外部知情交易多 (High PIN)**、
  **内部人信息少 (Low INSIDER)**、**ERC 小的行业**、**CEO 更长期导向**、**共同基金被动抛售之后 (MF_OF = 1)**；
  且 “市场驱动的调整” 预测更好的未来业绩 (Table 4)。
* **H2 (Table 6)**：当常规股价被非基本面噪音 (mutual-fund fire sales) 污染时，管理层更可能主动发布 capex 预测去“征求”反馈。

## 1. 表格对照 (table map)

| 表 | 内容 | 样本/单位 | 规格 | 代码 |
|---|---|---|---|---|
| T1 A/B/C | 描述统计 / 逐年 / 预测类型 | 17,577 firm-quarters | — | `tables.table1` |
| T2 (1)–(8) | CAPEX_ADJ ~ CAR | 同上 | (1)(2) 无 FE；(3) 年季 FE；(4)–(8) 公司+年季 FE；(1)–(4) 按公司聚类，(5)–(8) 按行业聚类 | `table2` |
| T3 | 按价差升/降分样本；CAR_POS / CAR_NEG | 7,770 / 9,570 | 同 T2(8) 控制变量 | `table3` |
| T4 | 未来业绩 ~ capex 三分解 | 16,3xx | 公司+年季 FE，按公司聚类 | `table4` |
| T5 A–D, E2 | 横截面分组 × 价差分组 | 见表 | 同 T2(8)，每组 6 列 + 3 个差异 p 值 | `table5` |
| T5 E1 | 价差 ~ EVENT × MF_OF (× CAPEX) | event-day | 公司+年季 FE，按公司聚类 | `table5e1` |
| T6 | 发布概率 LPM ~ NOISE_SIGNAL | 25 万 firm-quarters | 公司+年季 FE，按公司聚类 | `table6` |
| Fig. 1 | 正交化价差：事件期 vs 非事件期 | event-day | — | `figure1` |
| 正文 | 稳健性 (fn 17–19, 23) 与文中引用的矩 | — | — | `robustness`, `text_checks` |

## 2. 样本构建 (sample waterfall)

| 步骤 | 论文 | 我们（WRDS） | 代码中的实现 |
|---|---|---|---|
| IBES 年度 capex 预测（2002–2016） | — | 49,999 | `det_guidance` (CPX, ANN, US, USD) → 每个 (ticker, 公告日) 保留最近财年、最新修订 |
| 每个公司-季度只留第一条 (D6) | — | 43,422 | 在第一步计数之前去重 |
| 匹配到 Compustat 实际 capex | 40,785 | 41,452 (+1.6%) | iclink → CCM → `funda.capx` 非缺失 |
| 有 CRSP 短窗口市场反应 | 36,900 | 41,443 (+12.3%) | CAR[-2,2] 五天收益齐全 (D12) |
| 删除与盈利预测同时发布的 | 19,427 | 20,344 (+4.7%) | 同一 ticker 同一天有任一盈利类指引 (EPS、GPS、NET、PRE、EBT、EBS、OPR、FFO) (D9) |
| 删除 2016 年发布的 | 17,577 | 18,866 (+7.3%) | 只保留 2003–2015 年发布的 (D2) |
| **最终** | **17,577 / 1,790 家公司** | **18,866 / 2,180 家公司** | |

> 算术检查：36,900 − 17,473 − 1,850 = 17,577，**一个不差**。所以论文在这几步之后没有任何额外删除——
> firm-quarter 去重必须发生在 40,785 之前 (D6)，2002 年的预测也不可能活到这一步 (D2)。
> 代码在 `sample_waterfall.csv` 里逐步对照这四个数。
> 第 2 步是唯一明显对不上的环节：论文在这一步删除了 3,885 个，我们只删除 9 个；论文没有说明这一步除了 CRSP 收益之外还有什么要求。

## 3. 变量字典 (variable dictionary)

时点约定：forecast 发布在日历季度 *a*；预测的财年为 *t*。

| 变量 | 论文定义 | 构造 (WRDS 字段) | 时点 |
|---|---|---|---|
| CAPEX_FORE | 预测值 ($m) | point/other：`val_1`；range：(`val_1`+`val_2`)/2 | 公告日 |
| CAPEX_ACT | 实际 capex ($m) | `funda.capx`，`datadate` 的年月 = IBES `prd_yr`/`prd_mon` | 财年 t |
| **CAPEX_ADJ** | (实际 − 预测)/预测 × 100；range 预测落在区间内记 0，超出上界用 (实际 − 上界)/预测，低于下界用 (实际 − 下界)/预测 | `capex_adj()` | — |
| **CAR** | Σ_{d=-2..2} (ret − sprtrn) × 100 | `crsp.dsf.ret`, `crsp.dsi.sprtrn`；day 0 = 公告日或其后第一个交易日 | [-2,2] |
| CAR_POS / CAR_NEG | max(CAR,0) / min(CAR,0) | 各自标准化 | — |
| MKTRET | 公告日 S&P 500 收益 | `sprtrn`(day 0) × 100 | day 0 |
| CAR_PRE | 非公告日的伪反应：公告日前两周 | 以 “公告日 − 14 天” 当天或之前最后一个交易日为 day 0 | — |
| SF_CAR | 同一财年、距离最近的销售预测的 CAR | measure = SAL；两窗口不重叠 (D13) | — |
| SIZE | ln(股价 × 股数) | `ln(prccq × cshoq)`，取公告季度之前最后一个财季 | a−1 |
| LAG_CAPX | 上一年 capex / 年初市值 | `capx_{t-1} / (prcc_f × csho)_{t-1} × 100`；Table 1 报告的是 $m 版本 `LAG_CAPX_MIL` (D15) | t−1 |
| SURP | 当季 EPS − 去年同季 EPS | `epspxq_q − epspxq_{q-4} × ajexq_q / ajexq_{q-4}`（拆股调整，D32）；非同时发布时记 0 | 当季 |
| EA_DUM | capex 预测与盈利公告同时 | anndats = rdq（同一天，D10） | — |
| HIGHER_SPREAD | 事件期价差 > 事前价差 | 相对价差 (ask−bid)/mid × 100 (收盘报价 `bid`,`ask`)；均值 [-2,2] vs [-10,-3] | — |
| CFO / IBEI / NI_{t+1} | 下一年业绩 / 总资产 (%) | `oancf`,`ib`,`ni` 的 t+1 值 / `at_{t+1}` × 100 (D16) | t+1 |
| CAPEX, CAPEX_FORE, CAPEX_ADJ_MKT, CAPEX_ADJ_OTH | 实际 capex 三分解 / 总资产，标准化 | MKT$ = (β̂_CAR × CAR_z /100) × 预测值；OTH$ = 实际 − 预测 − MKT$；β̂ 取 T2 模型 (8) | t |
| PIN | Easley et al. (1996) PIN，Brown et al. 估计 | `data/external/pin.csv` | a−1 |
| INSIDER | 季度内部人交易笔数 (买+卖) / 市值 | TR `table1`，trancode ∈ {P,S}，cleanse ∈ {R,H}；无交易的季度记缺失 (D31) | a−1 (D20) |
| ERC | 行业层面季度盈余公告 [-1,1] 市场反应 | 两位 SIC 行业内 \|CAR[-1,1]\| 均值 (D19) | 全样本 |
| PAY_DUR | Gopalan et al. (2014) 薪酬久期 | `data/external/pay_duration.csv` | 公告年 |
| MF_OF | 上季度共同基金被动抛售压力高于中位数 | Edmans–Goldstein–Jiang (2012)，见 `build_mf_pressure.py`；匹配不到记 0 (D37) | a−1 |
| SPREAD, EVENT | 日度相对价差；EVENT = 1 for [-2,2]，0 for [-10,-3]∪[3,10] | `build_spread_panel.py` | 日 |
| SIZE, TURNOVER, RETVOL (E1) | 事前 [-10,-3] 的规模、换手率、收益波动 | ln(mean \|prc\|×shrout)、mean(vol/shrout)、sd(ret) | [-10,-3] |
| TREAT | 本季度是否发布 capex 预测 | 最终样本中的 (gvkey, 季度) | a |
| NOISE_SIGNAL | Q 的噪音/信号比 > 中位数 | Q ~ MFFLOW + FE；噪音 = \|b̂·MFFLOW\|，信号 = \|残差\| (D28) | a−1 |
| LEV, TANG, ROA, NEG_ROA, ROA_VOL | 杠杆、有形性、ROA、亏损、8 季 ROA 波动 | `(dlttq+dlcq)/atq`, `ppentq/atq`, `ibq/atq`, … | a−1 |

## 4. 决策日志 (decision log) —— 论文没说清的地方

格式：**论文原文/线索 → 最终设定 → 校准依据（含 WRDS 数据给出的证据）→ 备选**。
D2、D3、D4、D9、D10、D14 已用 WRDS 数据校准（详见下一节）；校准只看样本特征，不看回归结果。

| # | 问题 | 最终设定 | 校准依据 / 备选 |
|---|---|---|---|
| D1 | IBES Guidance 的 measure 代码 | CPX / SAL / EPS | `diagnose.py [1]` 打印实际代码 |
| D2 | 样本起点：初始 2002–2016，最终却是 2003–2015 (T1B 2003 年只有 22 个) | 只保留 2003–2015 (`KEEP_FROM_YEAR=2003`) | 瀑布算术精确 → 2002 年的预测没有活到最终样本。**WRDS 证实**：2002 年原始 CPX 年度预测只有 2 条，最终样本中被删除 1 条 |
| D3 | “Others” (more/less than) 在 IBES 中如何识别 | `RANGE_DESC_OPEN_ENDED` = 03、04、10–13、15–17 | 按 I/B/E/S Guidance User Guide (2009) 附录 2 的官方编码：01 between、06/08 high/low end of = 区间；02 about、14 comfortable with = 点；其余“多于/少于”类为开放式。**WRDS 结果**：点 54.6%（论文 55.3%）、区间 42.6%（34.5%）、开放式 2.8%（10.2%）。开放式在当前数据中本来就很少，不可能凑出 10%，属于数据版本或归类口径的差异 |
| D4 | `units` 单位 | millions→×1，billions→×1000 | WRDS 把单位拼写为 `millions` / `billions`（原代码只认缩写，已修正）；换算后实际/预测的中位数为 0.99 |
| D5 | 一次公告给出多个财年的预测 | 只留最近财年；剔除 >24 个月的 | 论文未提 |
| D6 | “unit of observation is a firm-quarter” —— 同季多次预测 | 保留季度内第一次，且**在瀑布第一步之前**按 (IBES ticker, 日历季度) 去重 (`COLLAPSE_AT_START=True`) | 瀑布算术精确，说明后面没有去重步骤；备选 `last`，或 `COLLAPSE_AT_START=False` (最后按 gvkey 去重) |
| D7 | range 预测的分母 “scaled by the forecast” | 区间中点 | `bound`：用被突破的边界 |
| D8 | open-ended 预测如何算 CAPEX_ADJ | 当作 `val_1` 的点预测 | 也可按单边处理 |
| D9 | “concurrently with an earnings forecast” | 同一天有**任一盈利类指引**：EPS、GPS (GAAP EPS)、NET、PRE、EBT (EBITDA)、EBS、OPR、FFO（`CONCURRENT_MEASURES`） | `calibrate_d9.py` 比较 4 种定义：只看 EPS 时最终样本 22,961（+31%），全部盈利类指标时 18,866（+7.3%），最接近论文；此步保留 20,344（论文 19,427）。只看 EPS 作为稳健性检验 |
| D10 | EA_DUM 的“同时” | 同一天（`EA_CONCURRENT_DAYS = 0`） | 最终样本 EA_DUM：同一天 0.662，±1 天 0.899，论文 0.559；约四分之一的预测与财报日错开一天（盘后发布）。±1 天作为稳健性检验 |
| D11 | 盘后发布是否顺延 day 0 | 不顺延 | 5 日窗口已覆盖；`AFTER_CLOSE_SHIFT=True` 做稳健性 |
| D12 | CAR 缺失天数 | 5 天全部要有 | — |
| D13 | SF_CAR 与 CAR 同日时完全共线 | 两窗口至少相隔 5 个交易日 | 目标：SF 样本 3,456，距离中位数 86 天 (fn 21) |
| D14 | 缩尾 | 所有 Table 1 变量 1%/99%（`WINSOR_VARS` + `WINSOR_LEVELS=True`） | **数据前的推断被 WRDS 数据推翻**：原以为 CAPEX_ACT 最小值 0.000 说明金额未缩尾，但实际数据里资本支出为 0 的公司很多，1% 分位数本身约为 0。第一次运行（只看 EPS）时 CAPEX_ACT 的 99% 分位数恰好是 9,496，等于论文最大值；最终样本中 CAPEX_FORE 的 1% 分位数 2.0 等于论文最小值；除 SIZE 外，论文极值都更接近我们的 1%/99% 分位数。SIZE 证据矛盾（最小值接近原始值，最大值接近 99% 分位），维持缩尾 |
| D15 | LAG_CAPX 单位：T1 是 $m，T2 注释说除以年初市值 | 回归用 % (×100) | 系数 −0.160 只有在 % 单位下才合理 |
| D16 | 业绩变量分母 | at_{t+1} | `at_lag`；目标：CFO 均值 10.5% |
| D17 | 价差单位 | 百分比 | 目标：非事件期价差中位数 0.073 |
| D18 | “industry” 聚类 | 两位 SIC，每家公司固定一个 (众数) | FF48；行业须对公司固定，否则公司 FE 不嵌套在聚类中 |
| D19 | ERC 的定义 “short-window stock market reaction” | 行业 \|CAR[-1,1]\| 均值 | `slope`：CAR 对 SUE 的斜率 |
| D20 | INSIDER 的季度 | 公告前一季 | `same` |
| D21 | MF_OF 中位数在哪个样本上算 | 全部 CRSP firm-quarters | E2 中 MF_OF=1 只占 25% (4,432/17,505)，说明中位数不是在 forecaster 样本里算的 |
| D22 | ROA_VOL | 当季 + 前 7 季 | — |
| D23 | 股票代码过滤 (shrcd 10/11) | 不过滤 | 论文未提 |
| D24 | 薪酬久期年份 | 公告当年 | `prev` |
| D25 | singleton 观测 | 保留 | T2 (1)–(5) 的 N 完全相同 → 未删 singleton (像 `areg`/`xtreg`) |
| D26 | 自由度修正 | `reghdfe` 惯例 | `areg`（测试数据中 SE 约高 2–3%，见 `tests/test_hdfe.py`） |
| D27 | 标准化在哪个样本上 | 全样本一次标准化，分组时不再重做 | 分组内重新标准化会改变系数大小 |
| D28 | 噪音/信号分解 (Dessaint et al. 2018) | Q ~ MFFLOW + 公司 FE + 年季 FE | 无 FE 的混合回归 |
| D29 | Table 6 的总体 | 所有 CCM 可链接的 Compustat firm-quarters，2003Q1–2015Q4 | 目标：N ≈ 250,316，TREAT 均值 0.07 |
| D30 | Table 4 的 “subsequent year” | 被预测财年 t 的下一财年 | — |
| D31 | 没有内部人交易的季度：0 还是缺失？ | 缺失 (`INSIDER_ZERO_AS_MISSING=True`) | T5B 两组合计 9,105，远小于 17,505 → 作者没有补 0 |
| D32 | SURP 跨拆股 | 用 `ajexq` 把去年同季 EPS 换算到当前股本口径 | 论文未提；不调整会在拆股季度产生虚假“意外” |
| D33 | Table 6 模型 (1) 与 (2) 的样本 | 共同样本 (所有控制变量非缺失) | 论文两列 N 都是 250,316 |
| D34 | CAPEX_ADJ_OTH 的定义 | 以美元计算：OTH$ = 实际 − 预测 − MKT$，再除以总资产 → 三部分精确相加等于 CAPEX | 论文写 CAPEX_ADJ − CAPEX_ADJ_MKT；对点预测两者相同，对区间预测不同 |
| D35 | CAR_POS / CAR_NEG 的标准化 | 先在 0 处切分原始 CAR，再分别标准化 | 备选：先标准化再切分 (fn 25 不能区分两者) |
| D36 | Table 5 中位数在哪个样本上算 | 回归样本内 (`SPLIT_MEDIAN_ON="estimation"`) | 论文各组几乎五五开 (如 4,548 / 4,557) |
| D37 | 匹配不到共同基金压力的公司-季度 | OUTFLOW 记 0、MF_OF = 0 | E2：13,073 + 4,432 = 17,505 = T2(8) 的 N → MF_OF 从不缺失 |

## 4b. 用 WRDS 数据校准的记录 (calibration log, 2026-11-09/10)

| 步骤 | 工具 | 发现 | 处理 |
|---|---|---|---|
| 权限与编码 | `check_wrds.py` | 9 张表全部可读；2002 年原始 CPX 预测只有 2 条（印证 D2）；`units` 为 `millions` / `billions`；有非美国公司和非美元币种 | D4 修正；US/USD 过滤保持 |
| 预测类型与单位 | `diagnose.py` | 50,004 个年度 capex 预测中，`range_desc` 01 占 45.5%、02 占 52.4%，开放式约 0.9%；实际/预测中位数 0.992 | D3 按官方编码设定；D4 无需再改 |
| 盈利预测的定义 | `calibrate_d9.py` | 见下表 | D9 选“全部盈利类指标” |
| 财报日窗口 | 构建两次样本比较 | EA_DUM：同一天 0.662，±1 天 0.899（论文 0.559） | D10 设为同一天 |
| 缩尾 | `table1_winsor_check.csv` | 金额变量的论文极值接近我们的 1%/99% 分位数 | D14 改为全部缩尾 |

`calibrate_d9.py` 的比较（只看样本特征，不跑回归）：

| 定义 | 最终 N | 第 3 步删除比例 | EA_DUM | 区间占比 | CAPEX_ADJ 均值 | CAR 均值 |
|---|---|---|---|---|---|---|
| 论文 | 17,577 | 47.4% | 0.559 | 0.345 | 7.421 | −0.148 |
| 只看 EPS | 22,961 | 39.9% | 0.902 | 0.448 | 2.867 | 0.287 |
| EPS + GPS | 22,117 | 42.0% | 0.902 | 0.445 | 3.557 | 0.271 |
| EPS + GPS + NET + PRE | 21,146 | 44.6% | 0.901 | 0.441 | 3.805 | 0.290 |
| **全部盈利类指标** | **18,866** | 50.9% | 0.899 | 0.426 | 3.945 | 0.318 |

（此表中的 EA_DUM 是在 D10 = ±1 天时计算的；D10 改为同一天后，主设定的 EA_DUM 为 0.662。）

**数据提取中修复的两个技术问题**（都不改变任何变量定义）：

1. `wrds.raw_sql` 分块读取后拼接，行号会重复，导致 dsf 的窗口筛选报错 → 改用位置索引，所有表读写时重置行号。
2. 新版 `wrds` 返回 pyarrow / 可空类型，缺失值为 `pd.NA`，`np.where` 无法判断 → `utils.load` 读入时统一转为 numpy 类型。

## 4c. Table 3 敏感性检验 (`t3_sensitivity.py`)

| 设定 | CAR 价差未升 | CAR 价差上升 | 差异 p | CAR_POS 未升 / 上升 | 差异 p |
|---|---|---|---|---|---|
| 论文 | −0.295 | 1.206** | 0.019 | −0.203 / 0.893* | 0.099 |
| 主设定 | 0.674** | 0.880** | 0.672 | 0.122 / 0.676* | 0.232 |
| D9：只看 EPS | 0.637** | 0.899*** | 0.555 | 0.123 / 0.638 | 0.312 |
| D10：±1 天 | 0.645* | 0.873** | 0.641 | 0.117 / 0.685* | 0.234 |
| 诊断：不与财报同日 (N = 6,337) | 0.709 | 2.180** | 0.139 | −0.133 / 1.205 | 0.442 |
| 诊断：与财报同日 (N = 12,340) | 0.586 | 0.409 | 0.781 | 0.354 / 0.556 | 0.773 |

这些设定在看到结果之前就已确定；主设定不因此表而改变。

## 4d. Table 3 诊断与样本差距（2026-11-10 至 11-12）

所有检验在运行前写入 `docs/t3_preregistration.md` 和 `docs/definitions_preregistration.md`；结果无论方向如何都报告。

| 检验 | 工具 | 结果 |
|---|---|---|
| 主设定差异的置信区间 | `t3_diagnostics.py` A | 0.206，95% CI [−0.76, 1.18]，排除论文的 1.501（p = 0.010） |
| 价差噪音：连续变量 / 极端三分位 | B / C | 交互项 0.071（p = 0.79）；差异 0.56（p = 0.44）→ 排除 |
| 论文稳健性样本 | D1–D3 | 2009 年后 1.081（p = 0.058）；仅点+区间 0.460；中点 0.314 |
| 最接近论文的样本（仅普通股） | E | −0.215（p = 0.692） |
| 数据回填 | `diagnose_gap.py` | 32.6 万条记录中仅 3 条激活于 2018-07-21 之后 → 排除 |
| 年度样本筛选 | `annual_waterfall.py` | 本复现前四步各年保留率稳定；论文最终 ÷ 第 4 步在 2003–2008 年为 0.15–0.42，2009 年起约 0.50 → 早年差距来自论文中无对应的步骤，最可能是其 CRSP 匹配 |
| 预测类型 | `diagnose_definitions.py` | 代码 06、08 仅 42 个（0.2%）；所有开放式代码合计 2.8%，无法得到论文的 10.2% |
| EA_DUM | 同上 | I/B/E/S 公告日 0.665，与 RDQ 0.662 几乎相同；±1 天 0.90 |
| “盈利预测”口径 | 同上 | 同日任何其他指引：公司 1,908、CAPEX_ADJ 中位数 0.000、删除比例 59.9%（论文 47.4%）；距离 1.484 → 1.080 |
| 最接近定义下的 Table 3 | 同上 | 未升 0.340、上升 1.032**，差异 0.692（p = 0.222） |
| CAR 均值 | 同上 | 按 EA_DUM 重新加权或换 VW 指数均无法解释（0.319、0.336） |

判定：E1（价差噪音）排除；E2（样本构成）不满足；E3（论文模式不稳健）基本成立，2009 年后为例外。Table 3 对“同日盈利预测”的定义敏感。

## 5. 估计细节 (estimation)

* 全部是 OLS（Table 6 也是线性概率模型 LPM）。`hdfe.py` 用交替投影 (alternating projections) 吸收固定效应，
  聚类稳健标准误小样本修正 `G/(G−1) × (N−1)/(N−K)`，p 值用 t(G−1)——与 Stata 一致。
  `tests/test_hdfe.py` 证明系数与 SE 和“全虚拟变量 OLS (areg)” 在 1e-8 精度上相同。
* **CAR、CAR_POS、CAR_NEG、MKTRET、CAR_PRE、SF_CAR 均标准化**（均值 0、标准差 1），所以系数 = 一个标准差对应的 CAPEX_ADJ 百分点。
* **组间差异 p 值**：把所有回归元和固定效应都与分组变量交互后合并估计 (fully interacted pooled model)，点估计与两个分组回归完全相同，协方差是联合聚类的——相当于 Stata `suest`。论文没说明用什么方法，这一点在报告里要写清楚。
* 工作论文里的笔误与不一致（按这里的理解实现，报告中写明）：
  1. T3/T5 注释写 “Model (9) of Table 2”，T2 只有 8 列 → 理解为模型 (8)。
  2. T4 注释写 “models (1)–(2)” 是 CFO，实际有 9 列；显著性说明重复了一遍。
  3. §3.4.4 写 “Less (More) long-term oriented … pay duration is **longer (shorter)** than the median”——方向写反了；久期越长 = 越长期导向，代码按后者。
  4. PIN 在 §3.4.1 引作 Brown et al. (2002)，在 §2.2 和参考文献里是 Brown, Hillegeist & Lo (2004)。
  5. T6 模型 (3)(4) 的 N (250,343) 比 (1)(2) (250,316) 还多，而变量只多不少——无法同时复现，见 D33。
  6. MF_OF 定义为 “above median”，但 E2 中 MF_OF=1 只占 25.3%（见 D21）。
  7. Polk & Sapienza 正文写 2009，参考文献写 2008。
  8. 附录 1：2014 年 11 月的 capex 预测说是 “for fiscal year 2016”，应为 2015。

## 6. 工作论文 vs 发表版

已逐项核对发表版（RFS 33(8): 3854–3888）：Table 1–3 的全部数字（系数、标准误、N、R²、p 值）与 `paper_targets.py` 中的工作论文数字完全相同。注意发表版脚注编号：区间中点稳健性为脚注 18，资产增长为脚注 19，行业×年 / 州×年固定效应为脚注 20，2008 年后样本为脚注 24。Internet Appendix 尚未核对。

## 7. 仍未解释的差异 (open differences)

* **Table 3 的组间差异**：主设定、2009 年后、最接近论文的定义下分别为 0.21、1.08、0.69，均未在 5% 水平显著（§4d）。
* **“其他”预测 10.2%**：当前 I/B/E/S 编码无法复原（开放式代码合计 2.8%），可能是旧编码或人工归类。
* **CAR 均值的符号**：不能由 EA_DUM 构成或市场指数解释。
* **样本早年差距与第 2 步**：论文删除 3,885 个、本复现删除 9 个；年度表显示差距集中在 2003–2008 年，论文未报告这一步的逐年数。
* **Table 4–6**：代码已写好（`JW_SCOPE=all`），不在本次范围内；附录 A 的证据链地图依据论文表格结构判断其对 Table 3 的依赖。

## 8. 执行清单 (checklist)

1. ☑ 核对发表版：Table 1–3 与工作论文数字完全相同（Internet Appendix 未核对）
2. ☑ 本地跑 `tests/test_hdfe.py`、`tests/run_synthetic.py`
3. ☑ `python check_wrds.py`：Table 1–3 所需的表全部可读
4. ☑ `pull_wrds.py`（另加 `guidance_earn`，用于 D9）
5. ☑ `diagnose.py`、`calibrate_d9.py` → 校准 D3、D4、D9、D10、D14，已记录在 §4、§4b
6. ☑ `run_all.py` → 样本瀑布、Table 1–3、最终报告
7. ☑ 偏离超过一个标准误的系数已在报告第 11 节列出，原因见第 12 节讨论
8. ☑ 稳健性：脚注 17–19、23（报告第 7 节）；D9、D10 对 Table 3 的影响（§4c）
9. ☐ Stata 交叉核对（`stata/tables_2_3.do` + `compare_stata.py`），需要有 Stata 的电脑
10. ☑ 预先登记的 Table 3 诊断（`diagnose_gap.py`、`t3_diagnostics.py`）
11. ☑ 年度样本筛选与预测层面定义（`annual_waterfall.py`、`diagnose_definitions.py --pull`）
12. ☑ 最终报告：`docs/report/`（中文、英文 PDF）

## 9. 可与老师讨论的下一步

1. Table 3 对不上的原因：是否值得用日内 TAQ 价差、或作者口径的价差重做价差分组？
2. 不与财报同日的子样本中出现了论文的模式（差异不显著）：是否值得作为扩展进一步研究？
3. 是否需要复现 Table 4–6（代码已写好，需额外下载内部人交易、共同基金和 s12 数据）？
4. 是否把样本延伸到 2016 年以后，检验结论在新样本中是否成立？
