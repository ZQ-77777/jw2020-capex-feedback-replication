"""
High-dimensional fixed-effects OLS with cluster-robust standard errors.

Written to mimic Stata `reghdfe` (default, DOF_MODE='reghdfe') or `areg` (DOF_MODE='areg')
so results are comparable with the paper, which was almost surely estimated in Stata.
No external dependency beyond numpy/scipy/pandas, so it runs anywhere; if `pyfixest` is
installed, tests/test_hdfe_vs_pyfixest.py cross-checks the numbers.

Small-sample correction (as in Stata):  V = c * (X'X)^-1 [sum_g X_g'u_g u_g'X_g] (X'X)^-1,
c = G/(G-1) * (N-1)/(N-K), p-values from t(G-1).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

import config as C


@dataclass
class Result:
    coef: pd.Series
    se: pd.Series
    vcov: pd.DataFrame
    nobs: int
    r2: float
    adj_r2: float
    within_r2: float
    n_clusters: int | None
    df_resid: int
    resid: pd.Series = field(repr=False, default=None)
    label: str = ""

    @property
    def t(self):
        return self.coef / self.se

    @property
    def p(self):
        df = (self.n_clusters - 1) if self.n_clusters else self.df_resid
        return pd.Series(2 * stats.t.sf(np.abs(self.t.values), df), index=self.coef.index)

    def summary(self) -> pd.DataFrame:
        return pd.DataFrame({"coef": self.coef, "se": self.se, "t": self.t, "p": self.p})


def _group_means(M, codes, counts):
    out = np.empty((len(counts), M.shape[1]))
    for j in range(M.shape[1]):
        out[:, j] = np.bincount(codes, weights=M[:, j], minlength=len(counts)) / counts
    return out


def demean(M: np.ndarray, fe_codes: list[np.ndarray], tol=1e-10, maxit=10_000) -> np.ndarray:
    """Method of alternating projections (exact in one pass for a single FE)."""
    if not fe_codes:
        return M
    M = M.astype(float).copy()
    counts = [np.bincount(c) for c in fe_codes]
    if len(fe_codes) == 1:
        return M - _group_means(M, fe_codes[0], counts[0])[fe_codes[0]]
    scale = 1.0 + np.abs(M).max()
    for _ in range(maxit):
        prev = M.copy()
        for c, n in zip(fe_codes, counts):
            M -= _group_means(M, c, n)[c]
        if np.abs(M - prev).max() < tol * scale:
            break
    return M


def _drop_singletons(d: pd.DataFrame, fe: list[str]) -> pd.DataFrame:
    while True:
        keep = np.ones(len(d), bool)
        for f in fe:
            keep &= d.groupby(f)[f].transform("size").values > 1
        if keep.all():
            return d
        d = d[keep]


def _fe_dof(codes: list[np.ndarray]) -> int:
    """Number of estimable FE parameters (reghdfe logic: exact redundancy for first two FEs)."""
    if not codes:
        return 0
    levels = [c.max() + 1 for c in codes]
    if len(codes) == 1:
        return levels[0]
    a, b = codes[0], codes[1]
    n1, n2 = levels[0], levels[1]
    g = coo_matrix((np.ones(len(a)), (a, b + n1)), shape=(n1 + n2, n1 + n2))
    ncomp, _ = connected_components(g, directed=False)
    dof = n1 + n2 - ncomp
    for lv in levels[2:]:
        dof += lv - 1
    return dof


def _nested(d: pd.DataFrame, fe: str, cl: str) -> bool:
    return bool((d.groupby(fe)[cl].nunique() <= 1).all())


def hdfe_ols(df: pd.DataFrame, y: str, X: list[str], fe: list[str] | None = None,
             cluster: str | None = None, label: str = "", keep_resid: bool = False,
             drop_singletons: bool | None = None, dof_mode: str | None = None) -> Result:
    fe = list(fe or [])
    drop_singletons = C.DROP_SINGLETONS if drop_singletons is None else drop_singletons
    dof_mode = dof_mode or C.DOF_MODE
    cols = [y, *X, *fe] + ([cluster] if cluster and cluster not in fe else [])
    d = df[cols].copy()
    for c in [y, *X]:
        d[c] = pd.to_numeric(d[c], errors="coerce").astype(float)
    d = d.replace([np.inf, -np.inf], np.nan).dropna()
    if fe and drop_singletons:
        d = _drop_singletons(d, fe)
    n = len(d)
    if n == 0:
        raise ValueError(f"[{label}] no observations")
    codes = [pd.factorize(d[f])[0] for f in fe]
    Y = d[y].values.reshape(-1, 1)
    Xm = d[X].values
    if fe:
        Z = demean(np.hstack([Y, Xm]), codes)
        Yd, Xd = Z[:, :1], Z[:, 1:]
        names = list(X)
    else:
        Yd, Xd = Y, np.hstack([Xm, np.ones((n, 1))])
        names = list(X) + ["_cons"]
    # drop perfectly collinear columns (e.g. an indicator absorbed by FE)
    keep = np.ones(Xd.shape[1], bool)
    if Xd.shape[1]:
        q, r = np.linalg.qr(Xd)
        diag = np.abs(np.diag(r))
        keep = diag > 1e-9 * max(1.0, diag.max())
    Xd = Xd[:, keep]
    names = [nm for nm, k in zip(names, keep) if k]
    XtX_inv = np.linalg.pinv(Xd.T @ Xd)
    beta = XtX_inv @ Xd.T @ Yd
    u = (Yd - Xd @ beta).ravel()
    p = Xd.shape[1]

    fe_dof_all = _fe_dof(codes)
    if cluster and dof_mode == "reghdfe":
        # reghdfe: FE nested within the cluster variable use no degrees of freedom.
        # e.g. firm FE nested in firm/industry clusters + year-qtr FE  ->  K_fe = L_yq - 1
        nested = [_nested(d, f, cluster) for f in fe]
        fe_dof_k = fe_dof_all - _fe_dof([c for c, nst in zip(codes, nested) if nst])
    else:
        fe_dof_k = fe_dof_all
    K = p + fe_dof_k

    if cluster:
        g = pd.factorize(d[cluster])[0]
        G = g.max() + 1
        S = np.zeros((G, p))
        for j in range(p):
            S[:, j] = np.bincount(g, weights=Xd[:, j] * u, minlength=G)
        meat = S.T @ S
        c = G / (G - 1) * (n - 1) / (n - K)
    else:
        G = None
        meat = (Xd * u[:, None]).T @ (Xd * u[:, None])
        c = n / (n - K)
    V = c * XtX_inv @ meat @ XtX_inv

    tss = ((Y.ravel() - Y.mean()) ** 2).sum()
    ssr = (u ** 2).sum()
    r2 = 1 - ssr / tss
    k_adj = p + fe_dof_all if fe else p
    adj = 1 - (1 - r2) * (n - 1) / (n - k_adj) if n > k_adj else np.nan
    tss_w = (Yd.ravel() ** 2).sum() if fe else tss
    wr2 = 1 - ssr / tss_w
    res = Result(coef=pd.Series(beta.ravel(), index=names),
                 se=pd.Series(np.sqrt(np.diag(V)), index=names),
                 vcov=pd.DataFrame(V, index=names, columns=names),
                 nobs=n, r2=r2, adj_r2=adj, within_r2=wr2,
                 n_clusters=G, df_resid=n - K, label=label)
    if keep_resid:
        res.resid = pd.Series(u, index=d.index)
    return res


def diff_test(df: pd.DataFrame, y: str, X: list[str], fe: list[str], cluster: str,
              group: str, var: str) -> float:
    """p-value of H0: b_var(group=1) == b_var(group=0) from a fully interacted pooled model.

    All regressors AND fixed effects are interacted with the group, so the point estimates
    equal those from the two separate regressions; the covariance is joint (cluster-robust),
    which is the analogue of Stata `suest`.
    """
    d = df.dropna(subset=[group]).copy()
    d[group] = d[group].astype(int)
    cols = []
    for g in (0, 1):
        ind = (d[group] == g).astype(float)
        for x in X:
            nm = f"{x}__g{g}"
            d[nm] = pd.to_numeric(d[x], errors="coerce") * ind
            cols.append(nm)
    fe_i = []
    for f in fe:
        nm = f"{f}__x"
        d[nm] = d[f].astype(str) + "|" + d[group].astype(str)
        fe_i.append(nm)
    if not fe:
        d["_g1"] = (d[group] == 1).astype(float)
        cols.append("_g1")
    r = hdfe_ols(d, y, cols, fe_i, cluster)
    a, b = f"{var}__g1", f"{var}__g0"
    if a not in r.coef or b not in r.coef:
        return np.nan
    diff = r.coef[a] - r.coef[b]
    se = np.sqrt(r.vcov.loc[a, a] + r.vcov.loc[b, b] - 2 * r.vcov.loc[a, b])
    return float(2 * stats.t.sf(abs(diff / se), r.n_clusters - 1))
