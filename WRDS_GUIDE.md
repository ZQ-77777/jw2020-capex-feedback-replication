# WRDS 实操指南 — 用 WRDS 数据跑 Jayaraman & Wu (2020) 复现

对应代码包 `jw2020/`。本指南从"拿到账号"开始，一直写到"拿到第一张对照表"。
每一步都写明：要做什么、要运行什么命令、成功时看到什么、出错时怎么办。

> 阅读顺序：§1–§3 是准备工作（只做一次）；§4–§7 是正式下载与校准；§8–§10 是参考资料，遇到问题时再查。

---

## 0. 整体流程一览

```
拿到 WRDS 账号 + 开通 Duo
  → 配好 Python 环境（§2）
  → 第一次连接，保存密码（§3）
  → python check_wrds.py            检查权限和字段名（§4）
  → python pull_wrds.py             下载约 16 张表（§5）
  → 核对下载结果（§6）
  → python diagnose.py              校准 IBES 编码开关（§7）
  → python run_all.py               构建样本、跑全部表格
  → 先看 sample_waterfall.csv 和 Table 1，再看回归
```

整套流程第一次跑，预计半天到一天，大部分时间是在等 `crsp.dsf` 和 `tfn.s12` 下载。

---

## 1. 账号、权限与合规（先读）

### 1.1 账号

- WRDS 账号以个人名义注册，绑定学校邮箱。HKUST 的订阅通过图书馆管理；学生账号通常需要老师担保 (faculty sponsor)。
- 如果你用的是老师项目下的账号，请按老师和学校的要求使用。**不要和别人共用账号、密码或 Duo 设备。**

### 1.2 Duo 双因素认证 (MFA)

WRDS 要求所有账号启用 Duo。第一次在网页登录 WRDS 时，系统会引导你注册；注册邀请也会发到账号绑定的邮箱，邮件标题是 *WRDS Two-Factor Authentication by Duo*。

对本项目的影响：**每次在 Python 里调用 `wrds.Connection()` 建立连接，手机都会收到一次 Duo 推送。** 要在几分钟内点"批准"，否则连接超时，需要重来。

所以本代码包的设计是：一次运行只建立一个连接。`pull_wrds.py` 下载全部表格只需要批准一次推送。

### 1.3 你需要哪些数据库订阅

| WRDS 库 | 用途 | 缺了会怎样 |
|---|---|---|
| **IBES Guidance** (`ibes.det_guidance`) | capex / 销售 / EPS 管理层预测——本文核心 | 无法复现，必须有 |
| CRSP (股票，日度和月度) | 收益、CAR、买卖价差 | 无法复现，必须有 |
| Compustat North America | 实际 capex、财务变量 | 无法复现，必须有 |
| CRSP/Compustat Merged (CCM) | PERMNO ↔ GVKEY 链接 | 无法复现，必须有 |
| WRDS 链接表 (`wrdsapps_link_crsp_ibes`) | IBES ↔ CRSP 链接 | 无法复现，必须有 |
| Thomson Reuters Insiders (`tr_insiders`) | Table 5 Panel B | 跳过 5B |
| CRSP Mutual Funds + MFLINKS + Thomson s12 | 共同基金抛售压力 | 跳过 5-E1、5-E2、Table 6 |

IBES Guidance 往往是**单独订阅**的，最容易缺。`check_wrds.py`（§4）会直接告诉你有没有。

### 1.4 合规底线

WRDS 数据是付费授权数据：

- **不能**上传到公开的 GitHub、网盘或分享给没有授权的人。代码包里的 `.gitignore` 已经排除了 `data/` 和 `output/`；交给老师时只给代码和汇总后的结果表。
- **可以**发表或交付汇总统计和回归结果（这正是复现报告的内容）。
- 记录数据的下载时间（`data/raw/_pull_log.csv` 会自动记录），写进报告的"数据版本"说明。

---

## 2. 配置 Python 环境（只做一次）

建议使用独立环境，避免和课程作业的包版本冲突。

```bash
# 用 conda（推荐）
conda create -n jw2020 python=3.11 -y
conda activate jw2020

cd jw2020
pip install -r requirements.txt     # pandas, numpy, scipy, matplotlib, tabulate, wrds，以及可选的 pyarrow / pyfixest
```

先不连 WRDS，验证环境是否装好（约 1–3 分钟）：

```bash
python tests/test_hdfe.py        # 最后一行应为: HDFE TESTS PASSED
python tests/run_synthetic.py    # 最后一行应为: ALL SYNTHETIC CHECKS PASSED
```

两个都通过，说明代码在你的电脑上可以正常运行。之后如果出问题，就可以排除"环境装坏了"这个原因。

**可选：** 装 `pyarrow`，中间数据就会存成 parquet（更快、更小）；不装则自动存成 pickle，功能完全一样。

---

## 3. 第一次连接 WRDS，保存密码（只做一次）

### 3.1 设置用户名环境变量

`config.py` 从环境变量 `WRDS_USERNAME` 读取用户名。

```bash
# macOS / Linux（写进 ~/.zshrc 或 ~/.bashrc 可以永久生效）
export WRDS_USERNAME=你的WRDS用户名

# Windows（命令提示符；设置后需要重新打开一个窗口才生效）
setx WRDS_USERNAME "你的WRDS用户名"
```

### 3.2 建立连接并保存密码文件 (pgpass)

```bash
python
```

```python
import wrds
db = wrds.Connection(wrds_username="你的WRDS用户名")
# 1) 提示输入密码
# 2) 手机收到 Duo 推送 -> 点"批准"
# 3) 问 "Create .pgpass file now [y/n]?" -> 输入 y
db.list_libraries()[:10]     # 能打印出库名，说明连接成功
db.close()
```

`.pgpass` 保存后，以后连接就不再询问密码（Duo 推送仍然每次都有）。它的存放位置是：

- macOS / Linux：`~/.pgpass`，权限必须是 600。如果提示权限问题，运行 `chmod 600 ~/.pgpass`。
- Windows：`%APPDATA%\postgresql\pgpass.conf`。

如果没有出现保存提示，可以手动保存：在连接成功后的 Python 里运行 `db.create_pgpass_file()`。

### 3.3 几个以后常用的探索命令

```python
db.list_libraries()                              # 你能访问的全部库
db.list_tables(library="ibes")                   # 某个库里的表
db.describe_table(library="ibes", table="det_guidance")   # 字段名、类型
db.raw_sql("SELECT * FROM ibes.det_guidance LIMIT 5")     # 看几行样例
```

---

## 4. 第一步：权限与字段自检

```bash
python check_wrds.py
```

批准一次 Duo 推送，大约 1–2 分钟后，屏幕上会打印一份报告，同时保存为 `output/wrds_check.md`。报告分三部分。

### 4.1 Tables 表：逐表的状态

| status | 含义 | 怎么办 |
|---|---|---|
| `OK` | 能读，字段齐全 | 无需处理 |
| `NO ACCESS / NOT FOUND` | 账号无权限，或该表不存在 | 看 `error` 列：`permission denied` 是没订阅，需要问图书馆或老师；`does not exist` 是改了名，用 `db.list_tables()` 找新名字 |
| `COLUMNS MISSING` | 表能读，但缺某些字段 | 用 `describe_table` 找到新的字段名，修改 `pull_wrds.py` 里对应的 SELECT |

"Tables found under an alternative name" 一节只是提示 WRDS 换过库名（例如内部人数据在 `tfn.table1` 而不是 `tr_insiders.table1`）。`pull_wrds.py` 会按顺序尝试这些名字，**不需要改任何东西**。

### 4.2 IBES Guidance probe：这是最关键的输出

1. **measure × pdicity 计数。** 要看到 `CPX / ANN` 有大量记录。如果完全没有 `CPX`，报告会列出全部 measure 代码，按实际代码修改 `config.py` 的 `MEASURE_CAPEX`（决策 D1）。
2. **`range_desc` / `units` / `curr` 的取值分布。** 把这部分**截图存档**。§7 校准 D3（哪些代码表示"多于/少于"这类开放式预测）和 D4（单位）都靠它。
3. **CPX 年度预测按年计数。** 原始数（未经任何筛选）应该**明显大于**论文最终样本数（论文后面还会删掉约一半与 EPS 预测同日发布的）。如果某一年原始数反而低于论文数，说明数据覆盖或编码和作者当时不同，要在报告里注明。

### 4.3 Verdict 结论

- *Core tables OK*：可以继续。
- *Cannot run the core tables*：先解决列出的问题，不要往下跑。
- *Optional sources unavailable*：可以继续，相应的表会被自动跳过并在输出里注明。

---

## 5. 下载数据

> **只做 Table 1–3（默认 `SCOPE = "t13"`）时**，`pull_wrds.py` 只下载 9 张表：guidance、ibcrsphist、ccm、funda、fundq、company、msenames、dsi、dsf。
> 下文的内部人交易、共同基金和 s12 表都不需要，§1.3 中标为“跳过”的订阅缺了也不影响。

### 5.1 一次全部下载

```bash
python pull_wrds.py
```

全程只需要一次 Duo 批准。数据存在 `data/raw/`，每张表一个文件；每下载一张表，都会往 `data/raw/_pull_log.csv` 追加一行（表名、行数、耗时、状态、时间）。

**下载顺序有依赖，不要打乱：**

1. `guidance`、`ibcrsphist`、`dsi` 必须在 `dsf` 之前：`dsf` 只下载有预测事件的股票、事件前后 ±30 个交易日的数据，要先知道事件在哪里。
2. `mf_tna`、`mflink1`、`mflink2` 必须在 `s12` 之前：`s12` 只下载当季资金流出超过 5% 的基金的持仓。

`pull_wrds.py` 里的默认顺序已经满足这两条。

### 5.2 各表说明

行数是**量级估计**，仅用于判断"是否明显不对"。

| 名称 | WRDS 表 | 筛选 | 量级 | 备注 |
|---|---|---|---|---|
| guidance | `ibes.det_guidance` | CPX/SAL/EPS，2002–2016 | 数十万行 | 核心 |
| ibcrsphist | 链接表 | 全部 | 数万行 | |
| ccm | `crsp.ccmxpf_lnkhist` | LU/LC，P/C | 数万行 | |
| funda / fundq | `comp.funda` / `comp.fundq` | INDL/STD/D/C | 约 20 万 / 约 100 万 | |
| company | `comp.company` | 全部 | 数万行 | |
| msenames / dsi / msf | CRSP | 2001-06 至 2017 | 数万 / 数千 / 百万级 | |
| insider | `tr_insiders.table1` | 仅 P、S 交易，2001–2016 | 数百万 | 较慢 |
| mf_tna, mflink1/2 | CRSP 共同基金 | 2001–2016 | 数百万 | |
| ea_daily | fundq × CCM × dsf 联合查询 | 盈余公告前后 ±7 天 | 数百万 | 在服务器端完成连接，较慢 |
| dsf | `crsp.dsf` | 分批（每批 400 只股票）、只保留事件窗口 | 数百万 | **最慢** |
| s12 | `tfn.s12` | 逐季度、只取大额流出基金 | 千万级 | **最慢** |

### 5.3 只重新下载某几张表

断线、超时或某张表失败时，不用从头再来：

```bash
python pull_wrds.py dsf s12          # 只重新下载这两张（会覆盖旧文件）
```

运行结束时，屏幕上会直接打印失败的表名和可以复制使用的重跑命令。

### 5.4 关于 CRSP 新旧格式 (SIZ / CIZ)

CRSP 在 2025 年初停止更新旧格式 (SIZ)，最后一期数据截至 2024-12-31。`crsp.dsf`、`crsp.msf`、`crsp.dsi`、`crsp.msenames` 这些旧表仍然可以查询，只是不再更新。本文样本是 2001–2017 年，**直接用旧表即可**，代码也是按旧表写的。

只有在 WRDS 将来彻底下架旧表时，才需要改用新格式（`crsp.dsf_v2` 等，字段名不同，例如日收益是 `dlyret`）。到那时要改的只有 `pull_wrds.py`，后续代码不用动。

### 5.5 实用建议

- 连稳定的网络（校园网或有线），并关掉电脑睡眠。
- 第一次可以分两段跑：先 `python pull_wrds.py guidance ibcrsphist ccm funda fundq company msenames dsi msf`，确认无误后再跑其余的大表。
- 磁盘预留 5–10 GB。

---

## 6. 下载后核对（5 分钟，不要跳过）

```bash
python - <<'EOF'
import pandas as pd, config as C, utils as U
print(pd.read_csv(C.RAW / "_pull_log.csv").to_string(index=False))
g = U.lower_cols(U.load("guidance", C.RAW))
print(g["measure"].value_counts())
g["anndats"] = pd.to_datetime(g["anndats"])
cpx = g[(g["measure"] == "CPX") & (g["pdicity"] == "ANN")]
print(cpx.groupby(cpx["anndats"].dt.year).size())
EOF
```

检查清单：

- ☐ 日志里没有 `FAILED`；如果有，按 §5.3 重新下载。
- ☐ 每张表的行数不是 0，和 §5.2 的量级大体一致。
- ☐ CPX 逐年数量和 `check_wrds.py` 报告里的数量一致。
- ☐ `dsf` 的日期覆盖 2002–2016，并且有 `bid`、`ask` 两列。

---

## 7. 校准 IBES 编码（diagnose.py）

```bash
python diagnose.py
```

这一步不需要连 WRDS，读的是已经下载的数据。它输出 5 块内容，每块对应 `config.py` 里的一个开关。

**原则：先用这些和回归结果无关的目标把开关定下来，再看回归系数。** 不要根据回归结果反过来调开关，那会变成挑规格 (specification search)。

| 输出块 | 对应开关 | 校准目标 | 怎么调 |
|---|---|---|---|
| [1] measure × pdicity | D1 `MEASURE_*` | 有 CPX / SAL / EPS | 按实际代码修改 |
| [2] range_desc × val_2 是否缺失 | D3 `RANGE_DESC_OPEN_ENDED` | 预测类型比例：point 55.30% / range 34.48% / other 10.22% | `val_2` 缺失、但 `range_desc` 表示"多于/少于"的代码，加入这个集合 |
| [3] 按 units 分组的 实际/预测 中位数 | D4 `UNITS_TO_MILLIONS` | 每种单位下的中位数 ≈ 1 | 中位数约 1000 的单位，说明需要 ×1000 换算 |
| [4] 不同天数窗口下 EA_DUM 的比例 | D10 `EA_CONCURRENT_DAYS` | 0.559 | 选最接近的天数 |
| [5] 与 EPS 预测同日的比例 | D9 `EPS_CONCURRENT_DAYS` | 约 47%（17,473 / 36,900） | 一般用 0 天 |

每改一次开关，都在 `REPLICATION_NOTES.md` 第 4 节对应的 D# 行下面记一笔：改成了什么、依据是什么。

然后运行：

```bash
python run_all.py
```

结果的阅读顺序：

1. `output/sample_waterfall.csv`：和论文的 40,785 → 36,900 → 19,427 → 17,577 逐步对照。
2. `output/tables.md` 中的 Table 1：样本描述统计。
3. `output/tables.md` 末尾的 "Moments quoted in the text"：正文里引用过的统计量。
4. 最后才看回归表。

成功的标准：样本量在 ±5–10% 以内，核心系数的符号相同、显著性格局相同、数量级接近。

---

## 8. 手工数据（不在 WRDS 上）

把这两个文件放在 `data/external/`，缺了代码会跳过对应的 Panel，并在输出里注明。

| 文件 | 字段 | 来源 | 影响 |
|---|---|---|---|
| `pin.csv` | `permno, year, qtr, pin` | Brown, Hillegeist & Lo 的季度 PIN 估计，Stephen Brown 在个人主页公开，数据截至 2010 年 | Table 5 Panel A |
| `pay_duration.csv` | `gvkey, year, duration` | Gopalan, Milbourn, Song & Thakor (2014)。作者当年是向 Todd Milbourn 索取的，2006–2009 年 | Table 5 Panel D |

拿到 PIN 文件后，检查一下列名。如果原文件用 CUSIP 而不是 PERMNO 标识股票，需要先用 `crsp.msenames` 转换。

---

## 9. 常见报错与解决

| 报错（关键字） | 原因 | 解决 |
|---|---|---|
| `PAM authentication failed` | 密码错误，或没有批准 Duo / 没有注册 Duo | 确认已注册 Duo；重新连接并及时点批准；改过密码要更新 `.pgpass` |
| 连接卡住，最后超时 | Duo 推送没有批准 | 检查手机 Duo App 的通知权限；重新运行 |
| `permission denied for schema xxx` | 没有订阅这个库 | 问图书馆或老师；可选数据库缺了就接受对应的表被跳过 |
| `relation "xxx" does not exist` | 表名改了 | `db.list_tables(library=...)` 找新名字，加到 `pull_wrds.py` 的候选列表 |
| `column "xxx" does not exist` | 字段名改了 | `db.describe_table(...)` 查新名字，修改对应的 SELECT |
| `current transaction is aborted` | 上一条 SQL 出错后连接处于中止状态 | 代码出错时会自动 rollback；手动探索时运行 `db.connection.rollback()` |
| `SSL connection has been closed unexpectedly` / `server closed the connection` | 长查询时网络断开 | 用 §5.3 只重新下载这张表；网络不稳时，把 `pull_dsf_windows` 的 `chunk` 从 400 改成 200 |
| `MemoryError` / 内存不足 | `dsf` 或 `s12` 太大 | 关掉其他程序；把 chunk 调小；装 `pyarrow` |
| `FileNotFoundError: xxx not found in data/raw` | 这张表没有下载成功 | 查看 `_pull_log.csv`，重新下载这张表 |
| `ModuleNotFoundError: tabulate` | 少装了包 | `pip install -r requirements.txt` |
| synthetic 测试通过，但真实数据报 `KeyError` | WRDS 返回的列名和预期不同 | 先跑 `check_wrds.py` 看缺哪一列 |

---

## 10. 附录

### 10.1 手动探索常用 SQL

```python
import wrds; db = wrds.Connection()

# capex 预测样例，人工看看编码
db.raw_sql("""
  SELECT ticker, anndats, prd_yr, prd_mon, val_1, val_2, range_desc, units
  FROM ibes.det_guidance
  WHERE measure = 'CPX' AND pdicity = 'ANN' AND anndats BETWEEN '2010-01-01' AND '2010-03-31'
  LIMIT 30""")

# 论文附录 1 的例子：Newfield Exploration 2010-04-26 的 capex 预测（核对编码的好样本）
db.raw_sql("""
  SELECT ticker, cname, anndats, prd_yr, val_1, val_2, range_desc
  FROM ibes.det_guidance
  WHERE measure = 'CPX' AND anndats BETWEEN '2010-04-20' AND '2010-04-30'
    AND cname ILIKE '%NEWFIELD%'""")
```

如果报错说没有 `cname` 字段，先用 `db.describe_table("ibes", "det_guidance")` 查看公司名所在的字段；也可以去掉这个条件，直接按 ticker 查。

Newfield 的例子很有用：论文说它在 2010 年 4 月预测 capex 16 亿美元，实际 19.71 亿美元，CAPEX_ADJ = +23.2%。用它可以手工验证单位 (D4) 和 CAPEX_ADJ 的计算。

### 10.2 如果 Python 连接用不了

可以在 WRDS 网页查询界面 (Web Query) 手动下载同样的表，选择同样的字段和日期范围，导出为 CSV。然后用 pandas 读入，用 `utils.save(df, "表名", C.RAW)` 保存。名称要和 `pull_wrds.PULLS` 里的键一致，后续代码就完全不受影响。

`dsf` 和 `s12` 体量太大，不适合网页下载。如果走这条路，优先保证核心表（§1.3 中"必须有"的几张），Table 5-E 和 Table 6 可以暂时放下。

### 10.3 报告中"数据与版本"一节的写法建议

> 数据于 YYYY-MM-DD 通过 WRDS 下载（见 `_pull_log.csv`）。IBES Guidance、Compustat 与 CRSP 在论文撰写后均有回溯修订，因此样本量与原文存在差异。所有构造选择见 REPLICATION_NOTES 决策日志 D1–D37。
