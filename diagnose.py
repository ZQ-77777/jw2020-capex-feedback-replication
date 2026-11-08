"""
Run this FIRST after pulling data (before trusting any regression):  python diagnose.py

It prints what you need to set the ambiguous switches in config.py:
  1. measure / pdicity codes present in ibes.det_guidance              -> D1
  2. range_desc x (val_2 missing) cross-tab for capex forecasts         -> D3 (open-ended codes)
     target split (Table 1 Panel C): point 55.30% / range 34.48% / other 10.22%
  3. 'units' codes and the actual/forecast ratio by unit                -> D4 (median ratio should be ~1)
  4. EA_DUM share for several concurrency windows                       -> D10 (target mean 0.559)
  5. share of capex forecasts concurrent with EPS guidance              -> D9 (paper drops 17,473/36,900 = 47%)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
import utils as U
from build_capex_sample import annual_forecasts, clean_guidance, load_funda, load_fundq


def main():
    g = clean_guidance()
    print("\n[1] measure x pdicity (rows) in det_guidance:")
    print(pd.crosstab(g["measure"], g["pdicity"]))

    c = annual_forecasts(g, C.MEASURE_CAPEX)
    print(f"\n[2] capex annual forecasts: {len(c):,}")
    if "range_desc" in c:
        print(pd.crosstab(c["range_desc"].astype(str), c["val_2"].isna().map({True: "val_2 missing", False: "val_2 present"})))
    rng = (c["val_2"].notna() & (c["val_2"] != c["val_1"])).mean()
    print(f"   share with distinct val_2 (= range): {rng:.4f}  (paper range share 0.3448)")

    if "units" in c:
        c = U.link_ibes_permno(c, U.load("ibcrsphist", C.RAW), "anndats")
        c = U.link_permno_gvkey(c, U.load("ccm", C.RAW), "anndats").dropna(subset=["gvkey"])
        c["gvkey"] = c["gvkey"].astype(str).str.zfill(6)
        a = load_funda()
        c["ym"] = c["prd_end"].dt.year * 100 + c["prd_end"].dt.month
        c = c.merge(a[["gvkey", "ym", "capx"]], on=["gvkey", "ym"], how="left")
        c["ratio"] = c["capx"] / c["val_1"]
        print("\n[3] units -> N and median(actual capx / val_1)  (should be ~1 after UNITS_TO_MILLIONS):")
        print(c.groupby(c["units"].astype(str))["ratio"].agg(["count", "median"]))

        q = load_fundq().dropna(subset=["rdq"])[["gvkey", "rdq"]]
        m = c[["gvkey", "anndats"]].reset_index().merge(q, on="gvkey")
        m["dist"] = (m["anndats"] - m["rdq"]).dt.days.abs()
        dmin = m.groupby("index")["dist"].min().reindex(c.index)
        print("\n[4] share of capex forecasts within N calendar days of an EA (target EA_DUM mean 0.559 in final sample):")
        for n in (0, 1, 2, 3):
            print(f"   N={n}: {(dmin <= n).mean():.3f}")

    eps = g[g["measure"] == C.MEASURE_EPS][["ticker", "anndats"]].drop_duplicates()
    m = c[["ticker", "anndats"]].reset_index().merge(eps.rename(columns={"anndats": "e"}), on="ticker")
    m["dist"] = (m["anndats"] - m["e"]).dt.days.abs()
    dmin = m.groupby("index")["dist"].min().reindex(c.index)
    print("\n[5] share of capex forecasts with EPS guidance within N days (paper drops 47% at this step):")
    for n in (0, 1, 2):
        print(f"   N={n}: {(dmin <= n).mean():.3f}")


if __name__ == "__main__":
    main()
