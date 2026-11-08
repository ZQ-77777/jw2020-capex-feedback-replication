* =============================================================================
* Jayaraman & Wu (2020, RFS) - Tables 2 and 3 re-estimated with reghdfe
* Purpose: independent cross-check of the Python estimator (hdfe.py).
* Author : Zhang Qi
*
* Run AFTER  python run_all.py  (which writes the regression sample), from this folder:
*     cd stata
*     do tables_2_3.do
* Then, from the package root:
*     python compare_stata.py          -> output/stata_crosscheck.md
*
* Reads : ../data/interim/capex_sample_for_stata.csv   (firm-level, WRDS-derived: do not share)
* Writes: ../output/stata_estimates.csv               (coefficients only)
* Needs : ssc install ftools, replace
*         ssc install reghdfe, replace
* Conventions matched to the Python code (REPLICATION_NOTES.md):
*   - singletons kept (D25)            -> option keepsingletons
*   - reghdfe degrees of freedom (D26) -> reghdfe default
*   - CAR, MKTRET, CAR_PRE, CAR_POS, CAR_NEG already standardised on the full sample (D27)
*   - SF_CAR standardised within the model (6) sub-sample, as in tables.py
*   - difference tests: one model with every regressor AND both fixed effects
*     interacted with the spread split (analogue of suest)
* =============================================================================
version 15
clear all
set more off

import delimited "../data/interim/capex_sample_for_stata.csv", case(lower) stringcols(1) clear
egen long firm = group(gvkey)
global ctrl8 "size lag_capx surp ea_dum mktret_z car_pre_z"

capture postclose est
postfile est str4 table int model str16 var double(coef se nobs) ///
    using "../output/stata_estimates.dta", replace

capture program drop keep_coefs
program define keep_coefs
    args tab mod
    local vars : colnames e(b)
    foreach v of local vars {
        if "`v'" == "_cons" continue
        post est ("`tab'") (`mod') ("`v'") (_b[`v']) (_se[`v']) (e(N))
    }
end

* ------------------------------------------------------------------ Table 2
gen byte base = !missing(capex_adj, car_z, size)

reghdfe capex_adj car_z if base, noabsorb vce(cluster firm) keepsingletons
keep_coefs T2 1
reghdfe capex_adj car_z size if base, noabsorb vce(cluster firm) keepsingletons
keep_coefs T2 2
reghdfe capex_adj car_z size if base, absorb(yq) vce(cluster firm) keepsingletons
keep_coefs T2 3
reghdfe capex_adj car_z size if base, absorb(firm yq) vce(cluster firm) keepsingletons
keep_coefs T2 4
reghdfe capex_adj car_z size if base, absorb(firm yq) vce(cluster ind) keepsingletons
keep_coefs T2 5

preserve
keep if base & !missing(sf_car)
egen double sf_car_z = std(sf_car)
reghdfe capex_adj car_z sf_car_z size, absorb(firm yq) vce(cluster ind) keepsingletons
keep_coefs T2 6
restore

reghdfe capex_adj car_z mktret_z car_pre_z size if base, absorb(firm yq) vce(cluster ind) keepsingletons
keep_coefs T2 7
reghdfe capex_adj car_z $ctrl8 if base, absorb(firm yq) vce(cluster ind) keepsingletons
keep_coefs T2 8

* ------------------------------------------------------------------ Table 3
gen byte s3 = !missing(capex_adj, car_z, higher_spread, size, lag_capx, surp, ea_dum, mktret_z, car_pre_z)

reghdfe capex_adj car_z $ctrl8 if s3 & higher_spread == 0, absorb(firm yq) vce(cluster ind) keepsingletons
keep_coefs T3 1
reghdfe capex_adj car_z $ctrl8 if s3 & higher_spread == 1, absorb(firm yq) vce(cluster ind) keepsingletons
keep_coefs T3 2
reghdfe capex_adj car_pos_z car_neg_z $ctrl8 if s3 & higher_spread == 0, absorb(firm yq) vce(cluster ind) keepsingletons
keep_coefs T3 3
reghdfe capex_adj car_pos_z car_neg_z $ctrl8 if s3 & higher_spread == 1, absorb(firm yq) vce(cluster ind) keepsingletons
keep_coefs T3 4

* p-values of the Lower vs Higher differences (stored with table = "T3P", coef = p-value)
reghdfe capex_adj c.(car_z $ctrl8)#i.higher_spread if s3, ///
    absorb(firm#higher_spread yq#higher_spread) vce(cluster ind) keepsingletons
foreach v in car_z mktret_z car_pre_z {
    test 1.higher_spread#c.`v' = 0.higher_spread#c.`v'
    post est ("T3P") (12) ("`v'") (r(p)) (.) (e(N))
}
reghdfe capex_adj c.(car_pos_z car_neg_z $ctrl8)#i.higher_spread if s3, ///
    absorb(firm#higher_spread yq#higher_spread) vce(cluster ind) keepsingletons
foreach v in car_pos_z car_neg_z mktret_z car_pre_z {
    test 1.higher_spread#c.`v' = 0.higher_spread#c.`v'
    post est ("T3P") (34) ("`v'") (r(p)) (.) (e(N))
}

postclose est
use "../output/stata_estimates.dta", clear
export delimited using "../output/stata_estimates.csv", replace
list, sepby(table model) noobs
