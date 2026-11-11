# Sample gap diagnostics

Sample characteristics only; no regression is run. Paper: 17,577 forecasts, 1,790 firms.


## [1] Waterfall alignment

After the firm-quarter collapse: 43,422 forecasts. With an I/B/E/S->CRSP link: 42,601 (lost 821). With a CCM link to Compustat: 42,478. With actual capex: 41,452.

Our step 1 already requires a CRSP PERMNO, so the paper's step-2 loss (40,785 -> 36,900) cannot be compared with ours (41,452 -> 41,443). The comparable count is the one AFTER the CRSP requirement: ours 41,443 vs the paper's 36,900.

| step                     |   ours |   paper |
|:-------------------------|-------:|--------:|
| w0_ibes_capex_forecasts  |  49999 |     nan |
| w0b_one_per_firm_quarter |  43422 |     nan |
| w1_matched_compustat     |  41452 |   40785 |
| w2_with_car              |  41443 |   36900 |
| w3_not_concurrent_eps    |  20344 |   19427 |
| w4_drop_2016             |  18866 |   17577 |

## [2] Where the gap sits in time (Table 1 Panel B)

|   YEAR |   ours |   ours_first |   paper |   paper_first |   gap |   gap_first |
|-------:|-------:|-------------:|--------:|--------------:|------:|------------:|
|   2003 |     42 |           40 |      22 |            22 |    20 |          18 |
|   2004 |    354 |          178 |     226 |           121 |   128 |          57 |
|   2005 |    639 |          222 |     488 |           181 |   151 |          41 |
|   2006 |   1038 |          280 |     874 |           235 |   164 |          45 |
|   2007 |    972 |          242 |     841 |           197 |   131 |          45 |
|   2008 |   1738 |          275 |    1560 |           234 |   178 |          41 |
|   2009 |   2231 |          290 |    2064 |           225 |   167 |          65 |
|   2010 |   2086 |          156 |    1974 |           133 |   112 |          23 |
|   2011 |   2139 |          144 |    2048 |           122 |    91 |          22 |
|   2012 |   2108 |          120 |    1993 |            96 |   115 |          24 |
|   2013 |   1959 |           87 |    1931 |            87 |    28 |           0 |
|   2014 |   1820 |           77 |    1779 |            73 |    41 |           4 |
|   2015 |   1740 |           69 |    1777 |            64 |   -37 |           5 |

Net gap 2003-2009: +939; 2010-2015: +350. Extra first-time forecasters: +390 firms.


## [3] Data vintage: I/B/E/S activation dates (ACTDATS)

|   YEAR |        N |   median lag (days) |   share lag > 365d |   share activated after 21 Jul 2018 |
|-------:|---------:|--------------------:|-------------------:|------------------------------------:|
|   2003 |   42.000 |               6.000 |              0.024 |                               0.000 |
|   2004 |  354.000 |               4.000 |              0.003 |                               0.000 |
|   2005 |  639.000 |               0.000 |              0.000 |                               0.000 |
|   2006 | 1038.000 |               0.000 |              0.000 |                               0.000 |
|   2007 |  972.000 |               0.000 |              0.000 |                               0.000 |
|   2008 | 1738.000 |               1.000 |              0.000 |                               0.000 |
|   2009 | 2231.000 |               1.000 |              0.000 |                               0.000 |
|   2010 | 2086.000 |               1.000 |              0.000 |                               0.000 |
|   2011 | 2139.000 |               1.000 |              0.000 |                               0.000 |
|   2012 | 2108.000 |               4.000 |              0.000 |                               0.000 |
|   2013 | 1959.000 |               1.000 |              0.000 |                               0.000 |
|   2014 | 1820.000 |               2.000 |              0.000 |                               0.000 |
|   2015 | 1740.000 |               6.000 |              0.000 |                               0.000 |

Whole sample: 0.0% of final-sample forecasts were activated after the paper was submitted. If this share is large and concentrated in early years, records were back-filled after the authors drew their data.


Point-in-time waterfall:

| step                     |   ours |   paper |
|:-------------------------|-------:|--------:|
| w0_ibes_capex_forecasts  |  49998 |     nan |
| w0b_one_per_firm_quarter |  43421 |     nan |
| w1_matched_compustat     |  41451 |   40785 |
| w2_with_car              |  41442 |   36900 |
| w3_not_concurrent_eps    |  20343 |   19427 |
| w4_drop_2016             |  18866 |   17577 |

## [4] Candidate filters (row filters on the main sample)

Share codes in the final sample:

|   shrcd |   forecasts |   firms |
|--------:|------------:|--------:|
|      11 |       16819 |    1855 |
|      12 |         983 |     137 |
|      18 |         135 |      38 |
|      31 |         404 |      81 |
|      41 |          10 |       1 |
|      48 |          39 |      12 |
|      71 |         476 |      63 |

## [5] Variants vs the paper

Fingerprint to match: the paper row's 'forecasts vs main' and 'firms vs main' (on WRDS data: -6.8% and -17.9%).


|                                |         N |    firms |   EA_DUM |   CAR_mean |   ADJ_mean |   ADJ_median |   range |   other |   higher_spread |   forecasts vs main |   firms vs main |   D (distance) | moments toward paper   |
|:-------------------------------|----------:|---------:|---------:|-----------:|-----------:|-------------:|--------:|--------:|----------------:|--------------------:|----------------:|---------------:|:-----------------------|
| paper                          | 17577.000 | 1790.000 |    0.559 |     -0.148 |      7.421 |        0.000 |   0.345 |   0.102 |           0.552 |              -0.068 |          -0.179 |        nan     |                        |
| main                           | 18866.000 | 2180.000 |    0.662 |      0.318 |      3.945 |       -0.326 |   0.426 |   0.028 |           0.564 |               0.000 |           0.000 |          1.484 | -                      |
| PIT (actdats <= 2018-07-21)    | 18866.000 | 2180.000 |    0.662 |      0.318 |      3.945 |       -0.326 |   0.426 |   0.028 |           0.564 |               0.000 |           0.000 |          1.484 | 0/7                    |
| PIT + shrcd 10/11 + exchcd 1-3 | 16815.000 | 1855.000 |    0.662 |      0.348 |      3.602 |       -0.226 |   0.436 |   0.028 |           0.563 |              -0.109 |          -0.149 |          1.359 | 2/7                    |
| PIT + shrcd + exchcd + history | 16612.000 | 1836.000 |    0.662 |      0.343 |      3.567 |       -0.281 |   0.436 |   0.028 |           0.564 |              -0.119 |          -0.158 |          1.359 | 4/7                    |
| shrcd 10/11                    | 16819.000 | 1855.000 |    0.662 |      0.344 |      3.615 |       -0.222 |   0.436 |   0.028 |           0.563 |              -0.109 |          -0.149 |          1.354 | 2/7                    |
| exchcd 1-3                     | 18851.000 | 2180.000 |    0.662 |      0.322 |      3.927 |       -0.322 |   0.426 |   0.028 |           0.564 |              -0.001 |           0.000 |          1.490 | 4/7                    |
| CRSP history >= 12m            | 18618.000 | 2154.000 |    0.662 |      0.313 |      3.931 |       -0.351 |   0.426 |   0.028 |           0.564 |              -0.013 |          -0.012 |          1.453 | 6/7                    |
| IBES link score <= 1           | 18825.000 | 2169.000 |    0.662 |      0.326 |      3.957 |       -0.313 |   0.427 |   0.028 |           0.564 |              -0.002 |          -0.005 |          1.483 | 5/7                    |
| shrcd 10/11 + exchcd 1-3       | 16815.000 | 1855.000 |    0.662 |      0.348 |      3.602 |       -0.226 |   0.436 |   0.028 |           0.563 |              -0.109 |          -0.149 |          1.359 | 2/7                    |
| shrcd + exchcd + history       | 16612.000 | 1836.000 |    0.662 |      0.343 |      3.567 |       -0.281 |   0.436 |   0.028 |           0.564 |              -0.119 |          -0.158 |          1.359 | 4/7                    |

**Pre-specified choice (smallest D): `shrcd 10/11`** (D = 1.354; main D = 1.484). t3_diagnostics.py re-estimates Table 3 on this variant once and reports it whatever the result.
