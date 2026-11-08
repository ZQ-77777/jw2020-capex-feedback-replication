"""
Run the whole pipeline on data already in data/raw/ (from pull_wrds.py or tests/make_synthetic.py).

    python run_all.py            # build + Tables 1-3 + report (JW_SCOPE=all for every table)
    python run_all.py --pull     # first download from WRDS (needs WRDS_USERNAME)
"""
import sys
import time

import config as C
import utils as U


def step(name, fn):
    t = time.time()
    print(f"\n######## {name}")
    fn()
    print(f"######## {name} done in {time.time() - t:.1f}s")


def main():
    if "--pull" in sys.argv:
        import pull_wrds
        step("01 pull WRDS", pull_wrds.main)
    import build_capex_sample, build_mf_pressure, build_panel, build_spread_panel, report, tables
    print(f"scope = {C.SCOPE!r}  ({'Tables 1-3' if C.SCOPE == 't13' else 'all tables'}; set JW_SCOPE=all for everything)")
    have_mf = C.SCOPE != "t13" and U.exists("s12", C.RAW) and U.exists("mf_tna", C.RAW)
    if have_mf:
        step("02a mutual-fund pressure", build_mf_pressure.build)
    step("02b capex sample", build_capex_sample.build)
    if C.SCOPE != "t13":
        step("03 spread panel", build_spread_panel.build)
    if have_mf:
        step("04 forecast-likelihood panel", build_panel.build)
    step("05 tables", tables.main)
    step("06 replication report", report.main)


if __name__ == "__main__":
    main()
