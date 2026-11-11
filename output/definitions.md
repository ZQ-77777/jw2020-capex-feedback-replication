# Forecast-level definitions

Sample characteristics only. Paper Table 1: EA_DUM 0.559; point / range / other 55.3% / 34.5% / 10.2%; CAPEX_ADJ mean 7.421, median 0.000; CAR mean −0.148.


## [1] I/B/E/S range_desc codes in the final sample

| range_desc   | label                   |   other |   point |   range |   All |   share |   with val_2 != val_1 |
|:-------------|:------------------------|--------:|--------:|--------:|------:|--------:|----------------------:|
| 01           | between (区间)          |       0 |       8 |    8003 |  8011 |   0.425 |                  8003 |
| 02           | about (约)              |       0 |   10290 |       0 | 10290 |   0.545 |                     0 |
| 03           | more than (多于)        |     132 |       0 |       0 |   132 |   0.007 |                     0 |
| 04           | at least (至少)         |       2 |       0 |       0 |     2 |   0.000 |                     0 |
| 06           | high end of (上端)      |       0 |       0 |      20 |    20 |   0.001 |                    20 |
| 08           | low end of (下端)       |       0 |       1 |      21 |    22 |   0.001 |                    21 |
| 10           | less than (少于)        |     296 |       0 |       0 |   296 |   0.016 |                     0 |
| 12           |                         |      25 |       0 |       0 |    25 |   0.001 |                     0 |
| 13           |                         |      16 |       0 |       0 |    16 |   0.001 |                     0 |
| 14           | comfortable with (认可) |       0 |       1 |       0 |     1 |   0.000 |                     0 |
| 15           |                         |       1 |       0 |       0 |     1 |   0.000 |                     0 |
| 16           |                         |       1 |       0 |       0 |     1 |   0.000 |                     0 |
| 17           |                         |      49 |       0 |       0 |    49 |   0.003 |                     0 |
| All          |                         |     522 |   10300 |    8044 | 18866 |   1.000 |                  8044 |


## [2]+[3] Definition grid (sorted by distance D)

D9 changes the sample; the type rule changes FTYPE and CAPEX_ADJ; the EA definition changes EA_DUM only.


| D9                        | type_rule         | EA_def           |     N |   firms |   w3_drop |   EA_DUM |   point |   range |   other |   ADJ_mean |   ADJ_median |   ADJ_zero |   CAR_mean |       D |
|:--------------------------|:------------------|:-----------------|------:|--------:|----------:|---------:|--------:|--------:|--------:|-----------:|-------------:|-----------:|-----------:|--------:|
| paper                     |                   |                  | 17577 |    1790 |     0.474 |    0.559 |   0.553 |   0.345 |   0.102 |      7.421 |        0.000 |    nan     |     -0.148 | nan     |
| V3 any other guidance     | R2 by code only   | E0 RDQ same day  | 15387 |    1908 |     0.599 |    0.633 |   0.566 |   0.403 |   0.031 |      5.580 |        0.000 |      0.099 |      0.290 |   1.080 |
| V3 any other guidance     | R1 06/08 -> other | E0 RDQ same day  | 15387 |    1908 |     0.599 |    0.633 |   0.566 |   0.403 |   0.031 |      5.580 |        0.000 |      0.099 |      0.290 |   1.080 |
| V3 any other guidance     | R2 by code only   | E2 IBES same day | 15387 |    1908 |     0.599 |    0.635 |   0.566 |   0.403 |   0.031 |      5.580 |        0.000 |      0.099 |      0.290 |   1.082 |
| V3 any other guidance     | R1 06/08 -> other | E2 IBES same day | 15387 |    1908 |     0.599 |    0.635 |   0.566 |   0.403 |   0.031 |      5.580 |        0.000 |      0.099 |      0.290 |   1.082 |
| V3 any other guidance     | R0 current        | E0 RDQ same day  | 15387 |    1908 |     0.599 |    0.633 |   0.566 |   0.405 |   0.029 |      5.557 |        0.000 |      0.099 |      0.290 |   1.087 |
| V3 any other guidance     | R0 current        | E2 IBES same day | 15387 |    1908 |     0.599 |    0.635 |   0.566 |   0.405 |   0.029 |      5.557 |        0.000 |      0.099 |      0.290 |   1.090 |
| V4 earnings-type +/-1 day | R2 by code only   | E0 RDQ same day  | 16917 |    1982 |     0.560 |    0.732 |   0.548 |   0.420 |   0.031 |      4.362 |       -0.352 |      0.107 |      0.287 |   1.311 |
| V4 earnings-type +/-1 day | R1 06/08 -> other | E0 RDQ same day  | 16917 |    1982 |     0.560 |    0.732 |   0.549 |   0.420 |   0.031 |      4.362 |       -0.352 |      0.107 |      0.287 |   1.311 |
| V4 earnings-type +/-1 day | R2 by code only   | E2 IBES same day | 16917 |    1982 |     0.560 |    0.736 |   0.548 |   0.420 |   0.031 |      4.362 |       -0.352 |      0.107 |      0.287 |   1.315 |
| V4 earnings-type +/-1 day | R1 06/08 -> other | E2 IBES same day | 16917 |    1982 |     0.560 |    0.736 |   0.549 |   0.420 |   0.031 |      4.362 |       -0.352 |      0.107 |      0.287 |   1.315 |
| V4 earnings-type +/-1 day | R0 current        | E0 RDQ same day  | 16917 |    1982 |     0.560 |    0.732 |   0.549 |   0.423 |   0.029 |      4.346 |       -0.352 |      0.108 |      0.287 |   1.318 |
| V4 earnings-type +/-1 day | R0 current        | E2 IBES same day | 16917 |    1982 |     0.560 |    0.736 |   0.549 |   0.423 |   0.029 |      4.346 |       -0.352 |      0.108 |      0.287 |   1.322 |
| V3 any other guidance     | R2 by code only   | E1 RDQ +/-1      | 15387 |    1908 |     0.599 |    0.890 |   0.566 |   0.403 |   0.031 |      5.580 |        0.000 |      0.099 |      0.290 |   1.337 |
| V3 any other guidance     | R1 06/08 -> other | E1 RDQ +/-1      | 15387 |    1908 |     0.599 |    0.890 |   0.566 |   0.403 |   0.031 |      5.580 |        0.000 |      0.099 |      0.290 |   1.337 |
| V3 any other guidance     | R2 by code only   | E3 IBES +/-1     | 15387 |    1908 |     0.599 |    0.891 |   0.566 |   0.403 |   0.031 |      5.580 |        0.000 |      0.099 |      0.290 |   1.338 |
| V3 any other guidance     | R1 06/08 -> other | E3 IBES +/-1     | 15387 |    1908 |     0.599 |    0.891 |   0.566 |   0.403 |   0.031 |      5.580 |        0.000 |      0.099 |      0.290 |   1.338 |
| V3 any other guidance     | R0 current        | E1 RDQ +/-1      | 15387 |    1908 |     0.599 |    0.890 |   0.566 |   0.405 |   0.029 |      5.557 |        0.000 |      0.099 |      0.290 |   1.345 |
| V3 any other guidance     | R0 current        | E3 IBES +/-1     | 15387 |    1908 |     0.599 |    0.891 |   0.566 |   0.405 |   0.029 |      5.557 |        0.000 |      0.099 |      0.290 |   1.346 |
| V4 earnings-type +/-1 day | R2 by code only   | E1 RDQ +/-1      | 16917 |    1982 |     0.560 |    0.889 |   0.548 |   0.420 |   0.031 |      4.362 |       -0.352 |      0.107 |      0.287 |   1.468 |


## One change at a time (from the current specification)

| D9                         | type_rule         | EA_def           |     N |   firms |   w3_drop |   EA_DUM |   point |   range |   other |   ADJ_mean |   ADJ_median |   ADJ_zero |   CAR_mean |     D |
|:---------------------------|:------------------|:-----------------|------:|--------:|----------:|---------:|--------:|--------:|--------:|-----------:|-------------:|-----------:|-----------:|------:|
| V2 earnings-type (current) | R0 current        | E0 RDQ same day  | 18866 |    2180 |     0.509 |    0.662 |   0.546 |   0.426 |   0.028 |      3.945 |       -0.326 |      0.108 |      0.318 | 1.484 |
| V2 earnings-type (current) | R2 by code only   | E0 RDQ same day  | 18866 |    2180 |     0.509 |    0.662 |   0.545 |   0.424 |   0.030 |      3.964 |       -0.326 |      0.108 |      0.318 | 1.477 |
| V2 earnings-type (current) | R1 06/08 -> other | E0 RDQ same day  | 18866 |    2180 |     0.509 |    0.662 |   0.546 |   0.424 |   0.030 |      3.964 |       -0.326 |      0.108 |      0.318 | 1.477 |
| V2 earnings-type (current) | R0 current        | E2 IBES same day | 18866 |    2180 |     0.509 |    0.665 |   0.546 |   0.426 |   0.028 |      3.945 |       -0.326 |      0.108 |      0.318 | 1.487 |
| V2 earnings-type (current) | R0 current        | E1 RDQ +/-1      | 18866 |    2180 |     0.509 |    0.899 |   0.546 |   0.426 |   0.028 |      3.945 |       -0.326 |      0.108 |      0.318 | 1.721 |
| V2 earnings-type (current) | R0 current        | E3 IBES +/-1     | 18866 |    2180 |     0.509 |    0.900 |   0.546 |   0.426 |   0.028 |      3.945 |       -0.326 |      0.108 |      0.318 | 1.722 |
| V3 any other guidance      | R0 current        | E0 RDQ same day  | 15387 |    1908 |     0.599 |    0.633 |   0.566 |   0.405 |   0.029 |      5.557 |        0.000 |      0.099 |      0.290 | 1.087 |
| V4 earnings-type +/-1 day  | R0 current        | E0 RDQ same day  | 16917 |    1982 |     0.560 |    0.732 |   0.549 |   0.423 |   0.029 |      4.346 |       -0.352 |      0.108 |      0.287 | 1.318 |
| V1 EPS only                | R0 current        | E0 RDQ same day  | 22961 |    2456 |     0.399 |    0.682 |   0.526 |   0.448 |   0.026 |      2.867 |       -0.385 |      0.114 |      0.287 | 2.031 |


## [4] Mean CAR (%)

| | mean CAR |
|---|---|
| current sample | 0.318 |
| EA_DUM = 1 | 0.313 |
| EA_DUM = 0 | 0.327 |
| re-weighted to EA_DUM = 0.559 | 0.319 |
| market = CRSP value-weighted (unwinsorised) | 0.336 |
| paper | −0.148 |



## [5] Pre-specified choice

Smallest D: **V3 any other guidance · R2 by code only · E0 RDQ same day** (D = 1.080; current specification D = 1.484).


Table 3 (CAR), estimated once on this specification:


| N (lo/hi)     | CAR lower     | CAR higher      | diff (SE)     |   p diff | 95% CI of diff   |   paper diff | paper diff in CI?   |   p (diff = paper) |
|:--------------|:--------------|:----------------|:--------------|---------:|:-----------------|-------------:|:--------------------|-------------------:|
| 6,683 / 8,608 | 0.340 (0.343) | 1.032** (0.445) | 0.692 (0.561) |    0.222 | [-0.43, 1.81]    |        1.501 | yes                 |              0.154 |