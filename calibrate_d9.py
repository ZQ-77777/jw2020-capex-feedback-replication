"""
D9 calibration: which guidance counts as an "earnings forecast" when dropping same-day capex forecasts?

    python pull_wrds.py guidance_earn      # once: other earnings-type guidance (GPS, NET, PRE, EBITDA, ...)
    python calibrate_d9.py                 # -> output/calibrate_d9.csv

Builds the sample under each definition and reports SAMPLE characteristics only (no regressions), so the choice
is disciplined by the paper's reported sample, not by the results. Pick the definition closest to the targets,
set CONCURRENT_MEASURES in config.py, record it under D9 in REPLICATION_NOTES.md, then run run_all.py.
"""
from __future__ import annotations

import pandas as pd

import build_capex_sample
import config as C
import utils as U

VARIANTS = {
    "EPS only": ("EPS",),
    "EPS + GAAP EPS": ("EPS", "GPS"),
    "EPS + GPS + NET + PRE": ("EPS", "GPS", "NET", "PRE"),
    "all earnings-type": ("EPS",) + tuple(C.EXTRA_EARNINGS_MEASURES),
}
TARGET = {"final N": 17577, "dropped at w3 (%)": 47.4, "EA_DUM mean": 0.559, "range share": 0.3448,
          "CAPEX_ADJ mean": 7.421, "CAPEX_ADJ median": 0.0, "CAR mean": -0.148}


def one(measures):
    C.CONCURRENT_MEASURES = measures
    build_capex_sample.build()
    wf = pd.read_csv(C.OUT / "sample_waterfall.csv").set_index("step")["ours"]
    c = U.load("capex_sample")
    return {"final N": len(c),
            "dropped at w3 (%)": round(100 * (1 - wf["w3_not_concurrent_eps"] / wf["w2_with_car"]), 1),
            "EA_DUM mean": round(c["EA_DUM"].mean(), 3),
            "range share": round((c["FTYPE"] == "range").mean(), 4),
            "CAPEX_ADJ mean": round(c["CAPEX_ADJ"].mean(), 3),
            "CAPEX_ADJ median": round(c["CAPEX_ADJ"].median(), 3),
            "CAR mean": round(c["CAR"].mean(), 3)}


def main():
    rows = {"paper": TARGET}
    for name, ms in VARIANTS.items():
        print(f"\n==== D9 variant: {name} {ms}")
        rows[name] = one(ms)
    t = pd.DataFrame(rows).T
    print("\n" + t.to_string())
    t.to_csv(C.OUT / "calibrate_d9.csv")
    print(f"\nsaved {C.OUT / 'calibrate_d9.csv'}. Re-run run_all.py after setting CONCURRENT_MEASURES "
          f"(the last variant built here is what data/interim now holds).")


if __name__ == "__main__":
    main()
