# Table 3 diagnostics

Pre-specified in docs/t3_preregistration.md. lo = spreads do not rise, hi = spreads rise. Controls, fixed effects (firm, year-quarter) and industry clustering as in Table 2 (8).


## Split tests (A, C, D, E)

|                                           | N (lo/hi)      | CAR lower       | CAR higher       | diff (SE)      |   p diff | 95% CI of diff   |   paper diff | paper diff in CI?   |   p (diff = paper) |
|:------------------------------------------|:---------------|:----------------|:-----------------|:---------------|---------:|:-----------------|-------------:|:--------------------|-------------------:|
| A. main specification                     | 8,135 / 10,542 | 0.674** (0.327) | 0.880** (0.350)  | 0.206 (0.485)  |    0.672 | [-0.76, 1.18]    |        1.501 | no                  |              0.01  |
| A2. CAR_POS (positive reactions)          | 8,135 / 10,542 | 0.122 (0.360)   | 0.676* (0.388)   | 0.553 (0.458)  |    0.232 | [-0.36, 1.47]    |        1.096 | yes                 |              0.241 |
| C. bottom vs top tercile of spread change | 6,213 / 6,224  | 0.484 (0.486)   | 1.043* (0.529)   | 0.560 (0.714)  |    0.436 | [-0.87, 1.98]    |        1.501 | yes                 |              0.192 |
| D1. post-2008 (fn 24)                     | 6,029 / 7,978  | 0.341 (0.423)   | 1.422*** (0.339) | 1.081 (0.560)  |    0.058 | [-0.04, 2.20]    |        1.501 | yes                 |              0.456 |
| D2. point + range only (fn 18)            | 7,904 / 10,252 | 0.525 (0.352)   | 0.986*** (0.334) | 0.460 (0.501)  |    0.361 | [-0.54, 1.46]    |        1.501 | no                  |              0.042 |
| D3. CAPEX_ADJ vs range midpoint (fn 18)   | 8,135 / 10,542 | 0.590* (0.338)  | 0.903** (0.363)  | 0.314 (0.497)  |    0.531 | [-0.68, 1.31]    |        1.501 | no                  |              0.02  |
| E. closest sample variant: shrcd 10/11    | 7,265 / 9,390  | 0.913** (0.374) | 0.698* (0.384)   | -0.215 (0.541) |    0.692 | [-1.30, 0.86]    |        1.501 | no                  |              0.002 |


Paper: lower −0.295 (0.372), higher 1.206** (0.497), difference 1.501, p = 0.019 (implied SE of the difference ≈ 0.640).


## A. How far apart are the two results?

- Our difference 0.206, 95% CI [-0.76, 1.18] (67 industry clusters). The paper's 1.501 is outside it (p = 0.010 for H0: our difference = 1.501).

- Taking the paper's own uncertainty into account (two estimates treated as independent), the gap between the two differences is 1.295, z = 1.61, p = 0.107. The samples overlap heavily, so this p-value is conservative.

- Lower-spread group: ours 0.674 vs the paper's −0.295; z = 1.96, p = 0.050 (the paper's prediction is no effect in this group).


## B. Continuous spread change (pooled)

CAPEX_ADJ on CAR, CAR × ΔSPREAD, ΔSPREAD and controls; ΔSPREAD = log(event/pre-event spread), z-scored. N = 18,677.

| | coef | SE | p |
|---|---|---|---|
| CAR | 0.951 | 0.218 | 0.000 |
| CAR × ΔSPREAD | 0.071 | 0.264 | 0.789 |
| ΔSPREAD | -0.393 | 0.175 | 0.028 |


How to read each test against the explanations: docs/t3_preregistration.md.
