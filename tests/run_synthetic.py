"""
End-to-end test without WRDS:  python tests/run_synthetic.py        (Tables 1-3)
                               python tests/run_synthetic.py --all  (every table)
Generates synthetic raw tables, runs every step, and checks that the planted effect is recovered.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ["JW_DATA"] = str(HERE / "synthetic_data")
os.environ["JW_OUT"] = str(HERE / "synthetic_output")
if "--all" in sys.argv:                       # test every table, not only Tables 1-3
    os.environ["JW_SCOPE"] = "all"
sys.path.insert(0, str(HERE.parent))

import config as C  # noqa: E402

C.RANGE_DESC_OPEN_ENDED = {"OPEN"}   # synthetic coding; real codes come from diagnose.py

import pandas as pd  # noqa: E402

import make_synthetic  # noqa: E402
import run_all  # noqa: E402


def main():
    if "--keep" not in sys.argv or not (C.RAW / "dsf.pkl").exists():
        make_synthetic.make()
    run_all.main()
    est = pd.read_csv(C.OUT / "estimates_long.csv")
    car = est[(est.table == "T2") & (est["var"] == "CAR")].set_index("model")
    print("\nT2 CAR coefficients:\n", car[["coef", "se", "p", "nobs"]])
    assert (car["coef"] > 0).all(), "planted positive effect not recovered"
    assert car.loc[8, "p"] < 0.05
    t3 = est[(est.table == "T3") & (est["var"] == "CAR")].set_index("model")
    assert t3.loc[2, "coef"] > t3.loc[1, "coef"] + 1.0, "Higher-spread column should carry the effect"
    wf = pd.read_csv(C.OUT / "sample_waterfall.csv")
    assert wf["ours"].is_monotonic_decreasing
    # internal consistency that mirrors the paper's reported N
    n2 = car["nobs"]
    assert n2.loc[[1, 2, 3, 4, 5, 7]].nunique() == 1, "T2 (1)-(5),(7) must share one sample (paper: 17,577)"
    assert n2.loc[8] <= n2.loc[7], "T2 (8) adds controls, so N cannot grow (paper: 17,505 < 17,577)"
    assert t3.loc[1, "nobs"] + t3.loc[2, "nobs"] <= n2.loc[8], "T3 halves come from the T2(8) sample"
    assert "w5_one_per_firm_quarter" not in set(wf["step"]), "collapse must happen before the waterfall (D6)"
    assert {"T2", "T3", "ROB"} <= set(est.table)
    import json
    extra = json.loads((C.OUT / "results_extra.json").read_text())
    assert {"magnitudes", "text", "t1_stats", "t3_p"} <= set(extra), "report inputs missing"
    rep = (C.OUT / "replication_report.html").read_text()
    assert "DEMO REPORT" in rep and "Table 3" in rep, "report not written or not flagged as demo"
    if C.SCOPE == "all":
        assert {"T4", "T5E1", "T6"} <= set(est.table), "some tables did not run"
        e2 = est[(est.table == "T5E2_MFOF") & (est["var"] == "CAR")].set_index("model")["nobs"]
        assert e2.loc[1] + e2.loc[2] == n2.loc[8], "E2 halves must add up to T2(8) N (paper: 13,073+4,432=17,505)"
        t6 = est[(est.table == "T6")].groupby("model")["nobs"].first()
        assert t6.loc[1] == t6.loc[2], "T6 (1),(2) must share one sample (paper: 250,316)"
        t6v = set(est[est.table == "T6"]["var"])
        assert {"LEV", "TANG", "ROA_VOL"} <= t6v, f"T6 controls missing: {t6v}"
    print("\nALL SYNTHETIC CHECKS PASSED")


if __name__ == "__main__":
    main()
