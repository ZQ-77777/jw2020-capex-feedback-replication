"""
Checks hdfe.py against brute-force least-squares-with-dummies (what Stata `areg`/`reg i.firm i.yq`
computes), and checks diff_test against two separate regressions.   python tests/test_hdfe.py
If pyfixest is installed, also compares with pyfixest.feols (reghdfe conventions).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hdfe import diff_test, hdfe_ols  # noqa: E402


def fake(n=3000, nf=150, nq=40, nind=12, seed=1):
    r = np.random.default_rng(seed)
    firm = r.integers(0, nf, n)
    ind = firm % nind                       # firm nested in industry
    yq = r.integers(0, nq, n)
    a, t = r.normal(0, 1, nf), r.normal(0, 1, nq)
    x1, x2 = r.normal(0, 1, n) + 0.3 * a[firm], r.normal(0, 1, n)
    g = (r.random(n) < 0.5).astype(int)
    y = 0.8 * x1 - 0.5 * x2 + 0.6 * x1 * g + a[firm] + t[yq] + r.normal(0, 1 + 0.5 * ind / nind, n)
    return pd.DataFrame(dict(y=y, x1=x1, x2=x2, firm=firm, ind=ind, yq=yq, g=g))


def brute(d, X, cl):
    D = pd.get_dummies(d[["firm", "yq"]].astype(str), drop_first=False).astype(float)
    D = D.drop(columns=[c for c in D.columns if c.startswith("yq_")][:1])     # one yq dummy redundant
    Z = np.hstack([d[X].values, D.values])
    b, *_ = np.linalg.lstsq(Z, d["y"].values, rcond=None)
    u = d["y"].values - Z @ b
    K = np.linalg.matrix_rank(Z)
    inv = np.linalg.pinv(Z.T @ Z)
    gcode = pd.factorize(d[cl])[0]
    G = gcode.max() + 1
    S = np.vstack([np.bincount(gcode, weights=Z[:, j] * u, minlength=G) for j in range(Z.shape[1])]).T
    V = G / (G - 1) * (len(d) - 1) / (len(d) - K) * inv @ (S.T @ S) @ inv
    return b[:len(X)], np.sqrt(np.diag(V))[:len(X)]


def main():
    d = fake()
    X = ["x1", "x2"]
    for cl in ("firm", "ind"):
        b0, s0 = brute(d, X, cl)
        r = hdfe_ols(d, "y", X, ["firm", "yq"], cl, dof_mode="areg", drop_singletons=False)
        assert np.allclose(r.coef.values, b0, atol=1e-8), (r.coef.values, b0)
        assert np.allclose(r.se.values, s0, rtol=1e-6), (cl, r.se.values, s0)
        rr = hdfe_ols(d, "y", X, ["firm", "yq"], cl, dof_mode="reghdfe", drop_singletons=False)
        print(f"cluster={cl:4s} coef {r.coef.values.round(4)}  se(areg) {r.se.values.round(4)}  "
              f"se(reghdfe) {rr.se.values.round(4)}  brute {s0.round(4)}")
    # difference test == separate regressions
    sep = [hdfe_ols(d[d.g == k], "y", X, ["firm", "yq"], "ind").coef["x1"] for k in (0, 1)]
    p = diff_test(d, "y", X, ["firm", "yq"], "ind", "g", "x1")
    print(f"separate x1: {sep[0]:.4f} vs {sep[1]:.4f} (true diff 0.6) -> p = {p:.2e}")
    assert p < 0.01
    try:
        import pyfixest as pf
        m = pf.feols("y ~ x1 + x2 | firm + yq", data=d, vcov={"CRV1": "ind"})
        print("pyfixest:", m.coef().values.round(4), m.se().values.round(4))
    except ImportError:
        print("pyfixest not installed - skipped cross-check")
    print("HDFE TESTS PASSED")


if __name__ == "__main__":
    main()
