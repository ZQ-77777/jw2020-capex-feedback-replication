"""Shared helpers: I/O, winsorising, trading calendar, event windows, IBES/CRSP/Compustat links."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C


# ============================================================================ I/O
def save(df: pd.DataFrame, name: str, folder=None) -> None:
    """Save as parquet when pyarrow is available, else pickle. Removes the stale twin."""
    folder = folder or C.INTERIM
    folder.mkdir(parents=True, exist_ok=True)
    pq, pk = folder / f"{name}.parquet", folder / f"{name}.pkl"
    try:
        df.to_parquet(pq, index=False)
        pk.unlink(missing_ok=True)
    except Exception:
        df.to_pickle(pk)
        pq.unlink(missing_ok=True)


def load(name: str, folder=None) -> pd.DataFrame:
    folder = folder or C.INTERIM
    pq, pk = folder / f"{name}.parquet", folder / f"{name}.pkl"
    if pq.exists():
        return pd.read_parquet(pq).reset_index(drop=True)
    if pk.exists():
        return pd.read_pickle(pk).reset_index(drop=True)
    raise FileNotFoundError(f"{name} not found in {folder}")


def exists(name: str, folder=None) -> bool:
    folder = folder or C.INTERIM
    return (folder / f"{name}.parquet").exists() or (folder / f"{name}.pkl").exists()


def lower_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    return df


def to_dt(s) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").astype("datetime64[ns]")


# ============================================================================ transforms
def winsorize(s: pd.Series, p=C.WINSOR) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").astype(float)
    if s.notna().sum() == 0:
        return s
    lo, hi = s.quantile(p[0]), s.quantile(p[1])
    return s.clip(lo, hi)


def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").astype(float)
    return (s - s.mean()) / s.std(ddof=1)


def qid(d) -> pd.Series:
    """Integer quarter id (year*4 + quarter-1) so that lags are simple subtraction."""
    d = to_dt(pd.Series(d))
    return (d.dt.year * 4 + d.dt.quarter - 1).astype("Int64")


def qid_label(q: int) -> str:
    return f"{int(q) // 4}Q{int(q) % 4 + 1}"


def label_to_qid(lbl: str) -> int:
    y, q = lbl.upper().split("Q")
    return int(y) * 4 + int(q) - 1


def month_end(year, month) -> pd.Series:
    df = pd.DataFrame({"year": pd.to_numeric(year), "month": pd.to_numeric(month), "day": 1})
    return (pd.to_datetime(df, errors="coerce") + pd.offsets.MonthEnd(0)).astype("datetime64[ns]")


def sic2(sic) -> pd.Series:
    return (pd.to_numeric(sic, errors="coerce") // 100).astype("Int64")


# ============================================================================ trading calendar
class TradingCalendar:
    """Maps calendar dates to integer trading-day indices (from CRSP dsi dates)."""

    def __init__(self, dates):
        d = to_dt(pd.Series(dates)).dropna().drop_duplicates().sort_values()
        self.d = d.values.astype("datetime64[ns]")

    def _arr(self, dates):
        return to_dt(pd.Series(dates)).values.astype("datetime64[ns]")

    def on_or_after(self, dates) -> np.ndarray:
        return np.searchsorted(self.d, self._arr(dates), side="left")

    def on_or_before(self, dates) -> np.ndarray:
        return np.searchsorted(self.d, self._arr(dates), side="right") - 1

    def index_exact(self, dates) -> np.ndarray:
        """For dates that ARE trading days (daily stock files)."""
        idx = np.searchsorted(self.d, self._arr(dates), side="left")
        return idx

    def date_of(self, idx) -> pd.Series:
        idx = np.clip(np.asarray(idx, dtype=int), 0, len(self.d) - 1)
        return pd.Series(self.d[idx])


def day0(events: pd.DataFrame, cal: TradingCalendar, date_col="anndats", time_col="anntims") -> np.ndarray:
    """Event day 0 = first trading day on/after the announcement date (D11: optional after-close shift)."""
    t0 = cal.on_or_after(events[date_col])
    if C.AFTER_CLOSE_SHIFT and time_col in events:
        tm = events[time_col].astype(str).str.replace(":", "", regex=False).str[:6]
        late = pd.to_numeric(tm, errors="coerce").fillna(0).values >= 160000
        on_tday = cal.d[np.clip(t0, 0, len(cal.d) - 1)] == to_dt(events[date_col]).values
        t0 = t0 + (late & on_tday).astype(int)
    return t0


def event_window(events: pd.DataFrame, daily: pd.DataFrame, lo: int, hi: int, cols: list[str],
                 t0_col="t0", eid="eid") -> pd.DataFrame:
    """Long panel of daily data for offsets k = lo..hi around each event.

    events : [eid, permno, t0]   daily : [permno, tidx, *cols]
    """
    offs = np.arange(lo, hi + 1)
    ev = events[[eid, "permno", t0_col]].dropna()
    rep = ev.loc[ev.index.repeat(len(offs)), [eid, "permno", t0_col]].reset_index(drop=True)
    rep["k"] = np.tile(offs, len(ev))
    rep["tidx"] = rep[t0_col].astype(int) + rep["k"]
    return rep.merge(daily[["permno", "tidx", *cols]], on=["permno", "tidx"], how="left")


def car(events, daily, lo, hi, eid="eid", t0_col="t0", min_obs=None) -> pd.Series:
    """Cumulative (summed) abnormal return, firm minus S&P 500, in percent."""
    min_obs = min_obs or (hi - lo + 1)
    w = event_window(events, daily, lo, hi, ["ar"], t0_col=t0_col, eid=eid)
    g = w.groupby(eid)["ar"]
    out = g.sum(min_count=1) * 100.0
    out[g.count() < min_obs] = np.nan
    return out


# ============================================================================ links
def link_ibes_permno(df: pd.DataFrame, ibl: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """IBES ticker -> CRSP permno valid at date (WRDS iclink 'ibcrsphist'; best score wins)."""
    ibl = lower_cols(ibl)[["ticker", "permno", "sdate", "edate", "score"]].copy()
    ibl["sdate"], ibl["edate"] = to_dt(ibl["sdate"]), to_dt(ibl["edate"]).fillna(pd.Timestamp("2099-12-31"))
    df = df.copy()
    df["_rid"] = np.arange(len(df))
    m = df[["_rid", "ticker", date_col]].merge(ibl, on="ticker", how="inner")
    m = m[(m[date_col] >= m["sdate"]) & (m[date_col] <= m["edate"])]
    m = m.sort_values(["_rid", "score", "permno"]).drop_duplicates("_rid")
    df = df.merge(m[["_rid", "permno", "score"]], on="_rid", how="left").drop(columns="_rid")
    df["permno"] = df["permno"].astype("Int64")
    return df


def link_permno_gvkey(df: pd.DataFrame, ccm: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """CRSP permno -> Compustat gvkey valid at date (CCM, LU/LC, primary link preferred)."""
    ccm = lower_cols(ccm)[["gvkey", "lpermno", "linkprim", "linkdt", "linkenddt"]].copy()
    ccm["linkdt"] = to_dt(ccm["linkdt"]).fillna(pd.Timestamp("1900-01-01"))
    ccm["linkenddt"] = to_dt(ccm["linkenddt"]).fillna(pd.Timestamp("2099-12-31"))
    ccm["lpermno"] = pd.to_numeric(ccm["lpermno"]).astype("Int64")
    ccm["prio"] = ccm["linkprim"].map({"P": 0, "C": 1}).fillna(2)
    df = df.copy()
    df["_rid"] = np.arange(len(df))
    m = df[["_rid", "permno", date_col]].dropna().merge(ccm, left_on="permno", right_on="lpermno")
    m = m[(m[date_col] >= m["linkdt"]) & (m[date_col] <= m["linkenddt"])]
    m = m.sort_values(["_rid", "prio"]).drop_duplicates("_rid")
    if "gvkey" in df.columns:
        df = df.drop(columns="gvkey")
    return df.merge(m[["_rid", "gvkey"]], on="_rid", how="left").drop(columns="_rid")


def permno_from_ncusip(df: pd.DataFrame, names: pd.DataFrame, cusip_col: str, date_col: str) -> pd.DataFrame:
    """8-digit historical CUSIP (ncusip) -> permno valid at date (CRSP msenames)."""
    n = lower_cols(names)[["permno", "ncusip", "namedt", "nameendt"]].dropna(subset=["ncusip"]).copy()
    n["namedt"] = to_dt(n["namedt"])
    n["nameendt"] = to_dt(n["nameendt"]).fillna(pd.Timestamp("2099-12-31"))
    df = df.copy()
    df["_rid"] = np.arange(len(df))
    m = df[["_rid", cusip_col, date_col]].merge(n, left_on=cusip_col, right_on="ncusip")
    m = m[(m[date_col] >= m["namedt"]) & (m[date_col] <= m["nameendt"])].drop_duplicates("_rid")
    return df.merge(m[["_rid", "permno"]], on="_rid", how="left").drop(columns="_rid")


def shrcd_at(df: pd.DataFrame, names: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Attach CRSP share code valid at date."""
    n = lower_cols(names)[["permno", "namedt", "nameendt", "shrcd"]].copy()
    n["namedt"], n["nameendt"] = to_dt(n["namedt"]), to_dt(n["nameendt"]).fillna(pd.Timestamp("2099-12-31"))
    n["permno"] = pd.to_numeric(n["permno"]).astype("Int64")
    df = df.copy()
    df["_rid"] = np.arange(len(df))
    m = df[["_rid", "permno", date_col]].merge(n, on="permno")
    m = m[(m[date_col] >= m["namedt"]) & (m[date_col] <= m["nameendt"])].drop_duplicates("_rid")
    return df.merge(m[["_rid", "shrcd"]], on="_rid", how="left").drop(columns="_rid")


def daily_with_tidx(dsf: pd.DataFrame, dsi: pd.DataFrame, cal: TradingCalendar) -> pd.DataFrame:
    """Daily stock file + S&P 500 return + trading-day index + relative spread."""
    d = lower_cols(dsf).copy()
    d["date"] = to_dt(d["date"])
    i = lower_cols(dsi)[["date", "sprtrn"]].copy()
    i["date"] = to_dt(i["date"])
    d = d.merge(i, on="date", how="left")
    d["permno"] = pd.to_numeric(d["permno"]).astype("Int64")
    d["tidx"] = cal.index_exact(d["date"])
    d["ar"] = pd.to_numeric(d["ret"], errors="coerce") - d["sprtrn"]
    bid, ask = pd.to_numeric(d["bid"], errors="coerce"), pd.to_numeric(d["ask"], errors="coerce")
    ok = (bid > 0) & (ask > bid)
    d["spread"] = np.where(ok, (ask - bid) / ((ask + bid) / 2.0) * C.SPREAD_UNIT, np.nan)
    d["mv"] = pd.to_numeric(d["prc"], errors="coerce").abs() * pd.to_numeric(d["shrout"], errors="coerce") / 1000.0
    d["turn"] = pd.to_numeric(d["vol"], errors="coerce") / (pd.to_numeric(d["shrout"], errors="coerce") * 1000.0)
    return d


def stars(p: float) -> str:
    if p is None or not np.isfinite(p):
        return ""
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
