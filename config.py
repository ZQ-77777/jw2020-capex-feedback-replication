"""
Central configuration for the replication of
Jayaraman & Wu (2020), "Should I Stay or Should I Grow? Using Voluntary Disclosure
to Elicit Market Feedback", Review of Financial Studies 33(8): 3854-3888.

Every judgment call the paper leaves open is a NAMED SWITCH here and is documented in
REPLICATION_NOTES.md ("Decision log", items D1-D37). Change behaviour here, never inside
the code, so that every number in output/ can be traced to a documented choice.
"""
from pathlib import Path
import os

# ----------------------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("JW_DATA", ROOT / "data"))
RAW = DATA / "raw"            # untouched WRDS pulls
INTERIM = DATA / "interim"    # constructed samples
EXTERNAL = DATA / "external"  # files downloaded by hand (PIN, pay duration)
OUT = Path(os.environ.get("JW_OUT", ROOT / "output"))

WRDS_USERNAME = os.environ.get("WRDS_USERNAME")  # export WRDS_USERNAME=... (faculty/RA account)

# ----------------------------------------------------------------------------- scope
# 't13' = Tables 1-3 only (the assignment): pulls 9 WRDS tables, builds the forecast sample,
#         Tables 1-3 + the robustness/footnote numbers that belong to them, and the report.
# 'all' = every table in the paper (adds insider, mutual-fund, PIN, pay-duration inputs).
SCOPE = os.environ.get("JW_SCOPE", "t13")

# ----------------------------------------------------------------------------- sample window
FCST_FIRST = "2002-01-01"      # paper: initial sample of forecasts 2002-2016
FCST_LAST = "2016-12-31"
DROP_FROM_YEAR = 2016          # paper drops 1,850 forecasts made in 2016 (no actual capex yet)
KEEP_FROM_YEAR = 2003          # D2: final sample is 2003-2015 (Table 1 Panel B starts in 2003)
PULL_START = "2001-06-01"      # buffer for pre-event windows / lagged accounting data
PULL_END = "2017-12-31"        # buffer for post-event windows and FY t+1 performance
PANEL_FIRST_Q, PANEL_LAST_Q = "2003Q1", "2015Q4"   # Table 6 panel

# ----------------------------------------------------------------------------- IBES guidance
MEASURE_CAPEX, MEASURE_SALES, MEASURE_EPS = "CPX", "SAL", "EPS"   # D1: verify with diagnose.py
PDICITY_ANNUAL = "ANN"
REQUIRE_USFIRM = True          # keep usfirm == 1 when the column exists
REQUIRE_USD = True             # keep curr == 'USD' (or missing)
# D3: range_desc codes that denote open-ended ("more than / less than") forecasts.
#     Unknown ex ante -> run `python diagnose.py` and set so that the type split is close to
#     Table 1 Panel C (point 55.30%, range 34.48%, other 10.22%).
RANGE_DESC_OPEN_ENDED = set()
# D4: IBES 'units' code -> multiplier into US$ millions (Compustat capx is in $ millions).
#     Unknown codes are left untouched and reported by diagnose.py.
UNITS_TO_MILLIONS = {"M": 1.0, "MIL": 1.0, "B": 1000.0, "BIL": 1000.0, "K": 0.001, "THO": 0.001}
MAX_HORIZON_MONTHS = 24        # D5: drop forecasts for fiscal periods > 24 months ahead
NEAREST_PERIOD_ONLY = True     # D5: if one announcement covers FY t and t+1, keep FY t
ONE_PER_FIRM_QUARTER = "first" # D6: unit is a firm-quarter -> 'first' | 'last' | None
COLLAPSE_AT_START = True       # D6: collapse to firm-quarter BEFORE the waterfall (paper arithmetic is exact:
                               #      36,900 - 17,473 - 1,850 = 17,577, so no later collapse step exists)
RANGE_SCALER = "mid"           # D7: denominator of CAPEX_ADJ for ranges: 'mid' | 'bound'
OTHER_RULE = "val1_as_point"   # D8: open-ended forecasts treated as point at val_1

# ----------------------------------------------------------------------------- concurrency
EPS_CONCURRENT_DAYS = 0        # D9: drop capex forecast if EPS guidance within +/- N calendar days
EA_CONCURRENT_DAYS = 1         # D10: EA_DUM = 1 if |anndats - rdq| <= N calendar days
AFTER_CLOSE_SHIFT = False      # D11: day 0 -> next trading day if anntims >= 16:00:00

# ----------------------------------------------------------------------------- event windows (trading days)
CAR_WIN = (-2, 2)
SPREAD_PRE_WIN = (-10, -3)     # Table 3 split: event [-2,2] vs pre [-10,-3]
SPREAD_EVT_WIN = (-2, 2)
SPREAD_POST_WIN = (3, 10)      # Table 5 E1 non-event = [-10,-3] U [3,10]
EA_CAR_WIN = (-1, 1)           # ERC (Table 5 Panel C)
CAR_PRE_SHIFT_CAL_DAYS = 14    # CAR_PRE: pseudo event "two weeks prior"
MIN_RET_OBS = 5                # D12: require all 5 daily returns for CAR
SF_MIN_GAP_TDAYS = 5           # D13: sales-forecast window must not overlap the capex window
DSF_BUFFER_TDAYS = 30          # how much daily data to keep around each event when pulling

# ----------------------------------------------------------------------------- variable construction
WINSOR = (0.01, 0.99)          # D14: paper silent; Table 1 min/max look like 1/99 for RATIOS only
# D14: Table 1 shows min CAPEX_ACT = 0.000 and min LAG_CAPX = 0.000 -> dollar LEVELS are not winsorised
# (a 1st percentile of exactly zero capex among capex forecasters is implausible), while
# min CAPEX_ADJ = -77.05 (a zero-capex point forecast would give -100) -> RATIOS are.
# tables.py prints raw min / p1 / p99 / max next to the paper so this can be checked on real data.
WINSOR_VARS = ["CAPEX_ADJ", "CAR", "CAR_PRE", "SF_CAR", "SURP", "LAG_CAPX", "ASSET_GROWTH",
               "CFO1", "IBEI1", "NI1", "CAPEX_AT", "FORE_AT", "INSIDER"]
WINSOR_LEVELS = False          # D14 switch: True also winsorises CAPEX_FORE, CAPEX_ACT, LAG_CAPX_MIL, SIZE
LAG_CAPX_SCALE = "mv_pct"      # D15: regression LAG_CAPX = capx_{t-1}/MV_{t-1} * 100
PERF_SCALER = "at_same_year"   # D16: CFO_{t+1}/AT_{t+1} ('at_same_year') or /AT_t ('at_lag')
SPREAD_UNIT = 100.0            # D17: relative spread in percent (median 0.073 in paper)
INDUSTRY = "sic2"              # D18: clustering industry = 2-digit SIC
ERC_METHOD = "abs_car"         # D19: industry ERC = mean |CAR[-1,1]| ('abs_car') or slope on SUE ('slope')
INSIDER_QUARTER = "prev"       # D20: insider transactions in quarter before forecast ('prev'|'same')
INSIDER_ZERO_AS_MISSING = True # D31: quarters without P/S trades are missing, not 0 (Table 5B N = 9,105 of 17,505)
SURP_SPLIT_ADJUST = True       # D32: put EPS of the same quarter last year on today's share basis via ajexq
PIN_QUARTER_LAG = 1            # paper: PIN "as of the quarter prior"
MF_OUTFLOW_CUTOFF = -0.05      # Edmans et al. (2012): funds with flows <= -5% of TNA
MF_MEDIAN_UNIVERSE = "all"     # D21: median of outflow pressure over all CRSP firm-quarters ('all'|'sample')
MF_MISSING_AS_ZERO = True      # D37: no extreme-outflow holder / no s12 match -> OUTFLOW 0 (E2 N = 17,505 = T2(8) N)
ROA_VOL_MIN_Q = 8              # D22: ROA_VOL = sd of ROA over current + 7 past quarters
SHRCD_FILTER = None            # D23: e.g. (10, 11); paper does not mention a share-code filter
PAY_DURATION_YEAR = "same"     # D24: Gopalan et al. duration of year(anndats) ('same'|'prev')

# ----------------------------------------------------------------------------- estimation
DROP_SINGLETONS = False        # D25: N identical across Table 2 models (1)-(5) => singletons kept
DOF_MODE = "reghdfe"           # D26: 'reghdfe' (FE nested in cluster not counted) | 'areg'
STANDARDIZE_ON = "full"        # D27: z-score CAR etc. on full final sample (not within splits)
SPLIT_MEDIAN_ON = "estimation" # D36: Table 5 medians over the regression sample ('estimation') or all obs ('all')
T6_COMMON_SAMPLE = True        # D33: Table 6 models (1)/(2) share one sample (paper N identical: 250,316)
