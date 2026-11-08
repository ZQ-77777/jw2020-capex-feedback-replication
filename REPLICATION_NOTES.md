# 复现说明 Replication Notes — Jayaraman & Wu (2020, RFS)

作者 Zhang Qi · 对应代码包 `jw2020/` · 本文件是“每一个数字从哪里来”的唯一说明。
凡标 **D#** (D1–D37) 的地方都对应 `config.py` 里一个可切换的开关 (switch) 或代码中的注释标签。

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

| 步骤 | 论文 | 代码中的实现 |
|---|---|---|
| IBES 年度 capex 预测，经 IBES link 匹配到 Compustat (2002–2016) | 40,785 | `det_guidance` (CPX, ANN, US, USD) → 每个 (ticker, 公告日) 保留最近财年、最新修订 → iclink → CCM → `funda.capx` 非缺失 |
| 有 CRSP 短窗口市场反应 | 36,900 | CAR[-2,2] 五天收益齐全 (D12) |
| 删除与盈利预测同时发布的 | −17,473 | 同一 ticker 同一天有 EPS guidance (任意 pdicity) (D9) |
| 删除 2016 年发布的 | −1,850 | 2016 年 actual capex 尚不可得 |
| **最终** | **17,577 / 1,790 家公司 / 2003–2015** | 只保留 2003–2015 年发布的 (D2)；firm-quarter 去重在第一步之前完成 (D6) |

> 算术检查：36,900 − 17,473 − 1,850 = 17,577，**一个不差**。所以论文在这几步之后没有任何额外删除——
> firm-quarter 去重必须发生在 40,785 之前 (D6)，2002 年的预测也不可能活到这一步 (D2)。
> 代码在 `sample_waterfall.csv` 里逐步对照这四个数。

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
| EA_DUM | capex 预测与盈利公告同时 | \|anndats − rdq\| ≤ 1 天 (D10) | — |
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

格式：**论文原文/线索 → 默认选择 → 如何校准 (calibration target) → 备选**。
先跑 `python diagnose.py`，再按下面顺序校准，**校准完之前不要看回归结果**（避免按结果挑规格）。

| # | 问题 | 默认 | 校准依据 / 备选 |
|---|---|---|---|
| D1 | IBES Guidance 的 measure 代码 | CPX / SAL / EPS | `diagnose.py [1]` 打印实际代码 |
| D2 | 样本起点：初始 2002–2016，最终却是 2003–2015 (T1B 2003 年只有 22 个) | 只保留 2003–2015 (`KEEP_FROM_YEAR=2003`)，与 2016 年一起删除，删除数量打印出来 | 瀑布算术精确 → 2002 年的预测没有活到最终样本；若真实数据里 2002 年很多，说明 D1/D5 口径与作者不同 |
| D3 | “Others” (more/less than) 在 IBES 中如何识别 | `RANGE_DESC_OPEN_ENDED` 为空 | `diagnose.py [2]` 的 range_desc 交叉表；目标 point 55.30% / range 34.48% / other 10.22% |
| D4 | `units` 单位 | M→×1，B→×1000 | `diagnose.py [3]`：实际/预测的中位数应≈1 |
| D5 | 一次公告给出多个财年的预测 | 只留最近财年；剔除 >24 个月的 | 论文未提 |
| D6 | “unit of observation is a firm-quarter” —— 同季多次预测 | 保留季度内第一次，且**在瀑布第一步之前**按 (IBES ticker, 日历季度) 去重 (`COLLAPSE_AT_START=True`) | 瀑布算术精确，说明后面没有去重步骤；备选 `last`，或 `COLLAPSE_AT_START=False` (最后按 gvkey 去重) |
| D7 | range 预测的分母 “scaled by the forecast” | 区间中点 | `bound`：用被突破的边界 |
| D8 | open-ended 预测如何算 CAPEX_ADJ | 当作 `val_1` 的点预测 | 也可按单边处理 |
| D9 | “concurrently with an earnings forecast” | 同一天 (0 天) | 目标：此步删除比例 17,473/36,900 = 47.4%（`diagnose.py [5]`） |
| D10 | EA_DUM 的“同时” | ±1 个日历日 | 目标：EA_DUM 均值 0.559（`diagnose.py [4]`） |
| D11 | 盘后发布是否顺延 day 0 | 不顺延 | 5 日窗口已覆盖；`AFTER_CLOSE_SHIFT=True` 做稳健性 |
| D12 | CAR 缺失天数 | 5 天全部要有 | — |
| D13 | SF_CAR 与 CAR 同日时完全共线 | 两窗口至少相隔 5 个交易日 | 目标：SF 样本 3,456，距离中位数 86 天 (fn 21) |
| D14 | 缩尾 | 比率变量 1%/99%（`WINSOR_VARS`）；金额变量不缩尾（`WINSOR_LEVELS=False`） | T1 极值：CAR −31.4 / 25.4、CAPEX_ADJ −77.05（实际为 0 的点预测应为 −100）→ 比率缩尾；CAPEX_ACT、LAG_CAPX 最小值 0.000 → 金额未缩尾。`output/table1_winsor_check.csv` 用真实数据逐变量核对 |
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

## 6. 工作论文 vs 发表版 (重要)

代码里的目标数字来自 **2019 年 5 月工作论文**（唯一能公开拿到全文的版本）。发表版 (RFS 2020, 及其 Internet Appendix) 可能：
修改了样本量、表格编号、增加了稳健性检验，**最可能附有变量定义附录**——它能直接解决上面很多 D#。
**第一件事**：通过 HKUST 图书馆下载发表版 + Internet Appendix，逐项核对 `paper_targets.py` 和本文件第 3–4 节，不一致处一律以发表版为准并在此记录。

## 7. 预期差异与风险

* IBES Guidance 自 2019 年以来有回填和修订，Compustat/CRSP 也有重述 → 样本量不会完全一致；以 ±5–10% 为合理范围。
* 最可能偏离的环节：D3 (预测类型识别)、D9 (EPS 同时性)、D21/D28 (共同基金口径)、Table 5D (外部数据不全)。
* Table 5A 依赖 Brown 的 PIN 数据（到 2010 年为止），5D 依赖作者私下提供的薪酬久期数据；拿不到时代码会自动跳过并在输出里注明。
* 不要按结果调参：先用 §4 的“非结果类目标”（样本量、类型比例、EA_DUM 均值、价差中位数）定下开关，再看系数。

## 8. 执行清单 (checklist)

1. ☐ 读发表版 + Internet Appendix，更新 `paper_targets.py` 和 §3–4
2. ☐ 本地跑 `tests/test_hdfe.py`、`tests/run_synthetic.py`（无需 WRDS，确认环境正常）
3. ☐ `python check_wrds.py`：确认 IBES Guidance、TR Insiders、TR s12、CRSP MF、MFLinks 可读（详见 `WRDS_GUIDE.md`）
4. ☐ `pull_wrds.py`（如某表报错，单独重跑：`python pull_wrds.py s12`）
5. ☐ `diagnose.py` → 校准 D1/D3/D4/D9/D10，每改一次在 §4 记录
6. ☐ `run_all.py` → 先看 `sample_waterfall.csv` 与 Table 1，再看回归
7. ☐ 对每个偏离 >1 个标准误的核心系数，在报告里写出最可能的原因（指向某个 D#）
8. ☐ 稳健性：至少切换 D7、D9、D10、D14、D18、D26 各一次，报告核心系数是否稳定

## 9. 需要和老师确认的问题

1. 复现范围：全部表格，还是先做核心 (Tables 1–4) 再做 Table 5–6？
2. WRDS：用哪个账号；是否订阅 IBES Guidance 与 Thomson s12 / MFLinks？
3. PIN 与薪酬久期数据：是否可以联系作者，或用替代口径？
4. 交付形式：复现报告 (对照表 + 差异解释) 还是要 Stata 代码？
5. 是否需要把样本延伸到 2016 年以后（论文结论在新样本是否成立，是自然的拓展）？
