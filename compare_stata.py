"""
Cross-check: Python (hdfe.py) vs Stata (reghdfe) for Tables 2 and 3.

    python run_all.py                 # Python estimates + data/interim/capex_sample_for_stata.csv
    (Stata) cd stata ; do tables_2_3.do
    python compare_stata.py           # -> output/stata_crosscheck.md

Both programs use the same rows, so coefficients should agree to rounding error (< 1e-6) and
standard errors to well under 0.1%. A larger gap means a convention differs (singletons, degrees of
freedom, standardisation) and is worth a line in the report.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import config as C

NAMES = {"car_z": "CAR", "sf_car_z": "SF_CAR", "mktret_z": "MKTRET", "car_pre_z": "CAR_PRE", "size": "SIZE",
         "lag_capx": "LAG_CAPX", "surp": "SURP", "ea_dum": "EA_DUM", "car_pos_z": "CAR_POS", "car_neg_z": "CAR_NEG"}
PKEYS = {(12, "car_z"): "CAR", (12, "mktret_z"): "MKTRET_12", (12, "car_pre_z"): "CAR_PRE_12",
         (34, "car_pos_z"): "CAR_POS", (34, "car_neg_z"): "CAR_NEG", (34, "mktret_z"): "MKTRET_34",
         (34, "car_pre_z"): "CAR_PRE_34"}
TOL_COEF, TOL_SE_REL = 1e-6, 1e-3


def main() -> int:
    st = pd.read_csv(C.OUT / "stata_estimates.csv")
    st.columns = [c.lower() for c in st.columns]
    py = pd.read_csv(C.OUT / "estimates_long.csv")
    extra = json.loads((C.OUT / "results_extra.json").read_text(encoding="utf-8"))

    coefs = st[st["table"] != "T3P"].copy()
    coefs["var"] = coefs["var"].map(NAMES)
    m = coefs.merge(py[py.table.isin(["T2", "T3"])][["table", "model", "var", "coef", "se", "nobs"]],
                    on=["table", "model", "var"], how="outer", suffixes=("_stata", "_python"), indicator=True)
    m["d_coef"] = (m["coef_stata"] - m["coef_python"]).abs()
    m["d_se_rel"] = ((m["se_stata"] - m["se_python"]) / m["se_python"]).abs()
    m["ok"] = (m["d_coef"] < TOL_COEF) & (m["d_se_rel"] < TOL_SE_REL) & (m["nobs_stata"] == m["nobs_python"])

    pv = st[st["table"] == "T3P"].copy()
    pv["key"] = [PKEYS.get((int(a), b)) for a, b in zip(pv["model"], pv["var"])]
    pv["p_python"] = pv["key"].map(extra.get("t3_p", {}))
    pv["d_p"] = (pv["coef"] - pv["p_python"]).abs()

    only = m[m["_merge"] != "both"]
    lines = ["# Stata (reghdfe) vs Python (hdfe.py): Tables 2 and 3\n",
             f"Coefficients compared: {int((m['_merge'] == 'both').sum())}; within tolerance "
             f"(|coef gap| < {TOL_COEF:g}, SE gap < {TOL_SE_REL:.1%}, same N): {int(m['ok'].sum())}.\n",
             f"Largest coefficient gap: {m['d_coef'].max():.2e}; largest relative SE gap: {m['d_se_rel'].max():.2e}.\n"]
    if len(only):
        lines.append("Rows present in only one program (check variable names / samples):\n\n" +
                     only[["table", "model", "var", "_merge"]].to_markdown(index=False) + "\n")
    show = m[m["_merge"] == "both"][["table", "model", "var", "coef_python", "coef_stata", "se_python", "se_stata",
                                     "nobs_python", "nobs_stata", "ok"]].sort_values(["table", "model", "var"])
    lines.append("## Coefficients\n\n" + show.to_markdown(index=False, floatfmt=".6f") + "\n")
    lines.append("## p-values of the Lower vs Higher differences (Table 3)\n\n" +
                 pv[["key", "p_python", "coef", "d_p"]].rename(columns={"coef": "p_stata"})
                 .to_markdown(index=False, floatfmt=".4f") + "\n")
    out = C.OUT / "stata_crosscheck.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:3]))
    print(f"written: {out}")
    return 0 if bool(m["ok"].all()) and only.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
