"""
Step -1: is this machine ready?        python preflight.py            (about 1 minute)
                                       python preflight.py --no-tests (seconds)

Checks the Python version, packages, package files, configuration, the WRDS user name, runs the two
test suites (estimator vs dummy-variable OLS; full pipeline on synthetic data), and looks at which
WRDS tables are already in data/raw. Ends with a verdict and the next command to run.
Writes output/preflight.md. Needs no WRDS access.
"""
from __future__ import annotations

import datetime as dt
import importlib
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import config as C
import utils as U

ROOT = Path(__file__).resolve().parent
REQUIRED = ["pandas", "numpy", "scipy", "tabulate"]
FOR_DOWNLOAD = ["wrds"]
OPTIONAL = {"pyarrow": "faster, smaller intermediate files", "matplotlib": "Figure 1 (only with JW_SCOPE=all)",
            "pyfixest": "extra estimator cross-check in tests/test_hdfe.py"}
FILES = ["config.py", "check_wrds.py", "pull_wrds.py", "diagnose.py", "run_all.py", "build_capex_sample.py",
         "tables.py", "hdfe.py", "utils.py", "report.py", "paper_targets.py", "compare_stata.py",
         "stata/tables_2_3.do", "tests/test_hdfe.py", "tests/run_synthetic.py", "tests/make_synthetic.py",
         "REPLICATION_NOTES.md", "WRDS_GUIDE.md", "GUIDE.html", "README.md", "requirements.txt"]
T13 = ["guidance", "ibcrsphist", "ccm", "funda", "fundq", "company", "msenames", "dsi", "dsf"]

rows: list[tuple[str, str, str]] = []          # (check, status, detail); status in OK / WARN / FAIL


def add(check, status, detail=""):
    rows.append((check, status, detail))
    mark = {"OK": "  ok ", "WARN": " warn", "FAIL": " FAIL"}[status]
    print(f"[{mark}] {check}{': ' + detail if detail else ''}")


def version(mod):
    try:
        m = importlib.import_module(mod)
        return getattr(m, "__version__", "installed")
    except Exception:
        return None


def run_test(script, args=()):
    t = time.time()
    r = subprocess.run([sys.executable, str(ROOT / script), *args], capture_output=True, text=True, cwd=ROOT)
    last = (r.stdout.strip().splitlines() or [""])[-1]
    return r.returncode == 0, f"{last} ({time.time() - t:.0f} s)", r


def main():
    print(f"Pre-flight check, {dt.datetime.now():%Y-%m-%d %H:%M}\n")
    v = sys.version_info
    add("Python >= 3.9", "OK" if v >= (3, 9) else "FAIL", platform.python_version())
    for p in REQUIRED:
        ver = version(p)
        add(f"package {p}", "OK" if ver else "FAIL", ver or "pip install -r requirements.txt")
    for p in FOR_DOWNLOAD:
        ver = version(p)
        add(f"package {p} (needed to download)", "OK" if ver else "WARN", ver or "pip install wrds")
    for p, why in OPTIONAL.items():
        ver = version(p)
        add(f"optional {p}", "OK" if ver else "WARN", ver or f"not installed; {why}")

    missing = [f for f in FILES if not (ROOT / f).exists()]
    add("package files", "OK" if not missing else "FAIL", f"{len(FILES) - len(missing)}/{len(FILES)} present"
        + (f"; missing {missing}" if missing else ""))

    add("scope", "OK", f"{C.SCOPE!r} ({'Tables 1-3' if C.SCOPE == 't13' else 'all tables'})")
    add("key switches", "OK", f"years {C.KEEP_FROM_YEAR}-{C.DROP_FROM_YEAR - 1}, range scaler {C.RANGE_SCALER}, "
        f"winsorise {C.WINSOR}, industry {C.INDUSTRY}, singletons dropped={C.DROP_SINGLETONS}")
    user = C.WRDS_USERNAME or os.environ.get("WRDS_USERNAME")
    add("WRDS user name", "OK" if user else "WARN", user or "not set: export WRDS_USERNAME=<account>")
    pg = Path.home() / (".pgpass" if os.name != "nt" else "AppData/Roaming/postgresql/pgpass.conf")
    add("saved WRDS password (.pgpass)", "OK" if pg.exists() else "WARN",
        "found" if pg.exists() else "not yet: created at the first wrds.Connection() (WRDS_GUIDE.md section 3)")
    for d in (C.RAW, C.INTERIM, C.OUT):
        try:
            d.mkdir(parents=True, exist_ok=True)
            (d / ".write_test").write_text("x")
            (d / ".write_test").unlink()
            add(f"writable {d.relative_to(ROOT) if d.is_relative_to(ROOT) else d}", "OK")
        except Exception as e:
            add(f"writable {d}", "FAIL", str(e))

    if "--no-tests" not in sys.argv:
        ok, msg, _ = run_test("tests/test_hdfe.py")
        add("estimator test (hdfe vs dummy-variable OLS)", "OK" if ok else "FAIL", msg)
        ok, msg, _ = run_test("tests/run_synthetic.py")
        add("end-to-end test on synthetic data", "OK" if ok else "FAIL", msg)
    else:
        add("tests", "WARN", "skipped (--no-tests)")

    synthetic_marker = (C.RAW / "_SYNTHETIC").exists()
    have = [t for t in T13 if U.exists(t, C.RAW)]
    if synthetic_marker:
        add("data/raw", "FAIL", "contains SYNTHETIC test data: delete data/raw before downloading WRDS data")
    elif have:
        add("WRDS tables in data/raw", "OK" if len(have) == len(T13) else "WARN",
            f"{len(have)}/{len(T13)}" + (f"; missing {[t for t in T13 if t not in have]}" if len(have) < len(T13) else ""))
    else:
        add("WRDS tables in data/raw", "WARN", "none yet")

    fails = [r for r in rows if r[1] == "FAIL"]
    if fails:
        verdict, nxt = "NOT READY: fix the FAIL lines above.", "pip install -r requirements.txt, then rerun"
    elif len(have) == len(T13) and not synthetic_marker:
        verdict, nxt = "READY TO RUN: all nine WRDS tables are present.", "python diagnose.py, then python run_all.py"
    else:
        verdict, nxt = "READY FOR DATA: code verified; download is the next step.", \
            "python check_wrds.py, then python pull_wrds.py (WRDS_GUIDE.md sections 4-5)"
    print(f"\n{verdict}\nNext: {nxt}")
    C.OUT.mkdir(parents=True, exist_ok=True)
    md = [f"# Pre-flight check, {dt.datetime.now():%Y-%m-%d %H:%M}\n", "| Check | Status | Detail |", "| --- | --- | --- |"]
    md += [f"| {a} | {b} | {c.replace('|', '/')} |" for a, b, c in rows]
    md += ["", f"**{verdict}** Next: `{nxt}`"]
    (C.OUT / "preflight.md").write_text("\n".join(md), encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
