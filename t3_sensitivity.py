"""
Table 3 sensitivity (pre-specified before looking at the variants' results):

    python t3_sensitivity.py            # -> output/t3_sensitivity.csv / .md

Re-estimates Table 3's two tests (CAR, and CAR_POS / CAR_NEG, Lower vs Higher spreads) under
  1. the main specification (config.py as set)
  2. D9 narrow: only EPS guidance counts as an "earnings forecast"
  3. D10 wide: earnings announcement within +/-1 calendar day
  4. diagnostic: forecasts NOT issued with an earnings announcement (EA_DUM = 0)
  5. diagnostic: forecasts issued with an earnings announcement (EA_DUM = 1)
Variants 4-5 split the main sample; EA_DUM (and SURP, which is 0 when EA_DUM = 0) drop out of the controls there.
The baseline sample is rebuilt last, so data/interim is left as the main specification.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import build_capex_sample
import config as C
import utils as U
from hdfe import diff_test, hdfe_ols

FE = ["gvkey", "YQ"]
CTRL8 = ["SIZE", "LAG_CAPX", "SURP", "EA_DUM", "MKTRET_z", "CAR_PRE_z"]
PAPER = dict(N_lo=7770, N_hi=9570, CAR_lo=-0.295, CAR_hi=1.206, p_CAR=0.019,
             POS_lo=-0.203, POS_hi=0.893, p_POS=0.099, NEG_lo=-0.045, NEG_hi=0.185, p_NEG=0.262)


def stars(p):
    return "***" if p < .01 else "**" if p < .05 else "*" if p < .10 else ""


def t3(c, ctrl):
    s = c.dropna(subset=["CAPEX_ADJ", "CAR_z", "HIGHER_SPREAD", *ctrl])
    lo, hi = s[s["HIGHER_SPREAD"] == 0], s[s["HIGHER_SPREAD"] == 1]
    X1, X2 = ["CAR_z", *ctrl], ["CAR_POS_z", "CAR_NEG_z", *ctrl]
    r = {}
    for g, d in (("lo", lo), ("hi", hi)):
        a = hdfe_ols(d, "CAPEX_ADJ", X1, FE, "IND")
        b = hdfe_ols(d, "CAPEX_ADJ", X2, FE, "IND")
        r[f"N_{g}"] = int(a.nobs)
        r[f"CAR_{g}"] = f"{a.coef['CAR_z']:.3f}{stars(a.p['CAR_z'])} ({a.se['CAR_z']:.3f})"
        r[f"POS_{g}"] = f"{b.coef['CAR_POS_z']:.3f}{stars(b.p['CAR_POS_z'])} ({b.se['CAR_POS_z']:.3f})"
        r[f"NEG_{g}"] = f"{b.coef['CAR_NEG_z']:.3f}{stars(b.p['CAR_NEG_z'])} ({b.se['CAR_NEG_z']:.3f})"
    r["p_CAR"] = round(diff_test(s, "CAPEX_ADJ", X1, FE, "IND", "HIGHER_SPREAD", "CAR_z"), 3)
    r["p_POS"] = round(diff_test(s, "CAPEX_ADJ", X2, FE, "IND", "HIGHER_SPREAD", "CAR_POS_z"), 3)
    r["p_NEG"] = round(diff_test(s, "CAPEX_ADJ", X2, FE, "IND", "HIGHER_SPREAD", "CAR_NEG_z"), 3)
    return r


def rebuilt(**settings):
    keep = {k: getattr(C, k) for k in settings}
    for k, v in settings.items():
        setattr(C, k, v)
    try:
        build_capex_sample.build()
        return U.load("capex_sample")
    finally:
        for k, v in keep.items():
            setattr(C, k, v)


def main():
    rows = {"paper": PAPER}
    print("\n==== D9 narrow: EPS only")
    rows["2. D9: EPS only"] = t3(rebuilt(CONCURRENT_MEASURES=("EPS",)), CTRL8)
    print("\n==== D10 wide: +/-1 day")
    rows["3. D10: EA within +/-1 day"] = t3(rebuilt(EA_CONCURRENT_DAYS=1), CTRL8)
    print("\n==== main specification (rebuilt last, so data/interim keeps it)")
    base = rebuilt()
    rows["1. main specification"] = t3(base, CTRL8)
    ctrl_sub = [x for x in CTRL8 if x not in ("EA_DUM", "SURP")]
    rows["4. diagnostic: EA_DUM = 0"] = t3(base[base["EA_DUM"] == 0], ctrl_sub)
    rows["5. diagnostic: EA_DUM = 1"] = t3(base[base["EA_DUM"] == 1], ctrl_sub + ["SURP"])
    order = ["N_lo", "N_hi", "CAR_lo", "CAR_hi", "p_CAR", "POS_lo", "POS_hi", "p_POS", "NEG_lo", "NEG_hi", "p_NEG"]
    t = pd.DataFrame(rows).T[order].sort_index()
    t.to_csv(C.OUT / "t3_sensitivity.csv")
    (C.OUT / "t3_sensitivity.md").write_text(
        "# Table 3 sensitivity\n\nlo = Lower spreads, hi = Higher spreads; p_* = p-value of the Lower-Higher difference.\n\n"
        + t.to_markdown(), encoding="utf-8")
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print("\n" + t.to_string())
    print(f"\nsaved {C.OUT / 't3_sensitivity.md'}")


if __name__ == "__main__":
    main()
