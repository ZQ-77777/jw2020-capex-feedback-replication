# Replication of Jayaraman and Wu (2020), Tables 1-3

Jayaraman, S. and J. S. Wu (2020). Should I Stay or Should I Grow? Using Voluntary Disclosure to Elicit Market Feedback. Review of Financial Studies 33(8): 3854-3888.

Zhang Qi · 10 November 2026

## 1. Summary

- Final sample: 18,866 forecasts, 2,180 firms (paper 17,577 / 1,790)
- Sign agreement 14/19; significance agreement 17/19; within one paper SE 13/19

The main estimate, Table 2 model (8), is 0.988*** (SE 0.219) against 0.849*** (0.304) in the paper: a one-standard-deviation higher market reaction to a capex forecast goes with a 0.99 percentage-point larger upward revision of actual capex, 25.1% of the mean adjustment (paper 11.4%). Table 3: the effect is 0.880** when event-window spreads rise and 0.674** when they fall (paper 1.206** and -0.295; difference p = 0.672 vs 0.019). The paper's pattern - an effect only when the forecast draws in informed trading - is not reproduced.

### Scorecard of key coefficients

| Coefficient    | Paper    | Ours     |   (ours - paper) / paper SE | Sign    | Significance (10%)   | Within 1 paper SE   |
|:---------------|:---------|:---------|----------------------------:|:--------|:---------------------|:--------------------|
| T2 (1) CAR     | 1.193*** | 1.193*** |                       -0    | match   | match                | match               |
| T2 (2) CAR     | 1.207*** | 1.228*** |                        0.06 | match   | match                | match               |
| T2 (3) CAR     | 1.196*** | 1.276*** |                        0.21 | match   | match                | match               |
| T2 (4) CAR     | 0.975*** | 1.017*** |                        0.14 | match   | match                | match               |
| T2 (5) CAR     | 0.975*** | 1.017*** |                        0.13 | match   | match                | match               |
| T2 (6) CAR     | 0.672*   | 0.996*   |                        0.88 | match   | match                | match               |
| T2 (7) CAR     | 1.006*** | 1.014*** |                        0.02 | match   | match                | match               |
| T2 (8) CAR     | 0.849*** | 0.988*** |                        0.46 | match   | match                | match               |
| T2 (6) SF_CAR  | 0.039    | 0.393    |                        5.8  | match   | match                | differs             |
| T2 (7) MKTRET  | -0.252   | 0.161    |                        1.34 | differs | match                | partial             |
| T2 (8) MKTRET  | -0.202   | 0.169    |                        1.15 | differs | match                | partial             |
| T2 (7) CAR_PRE | 0.305    | 0.369    |                        0.32 | match   | match                | match               |
| T2 (8) CAR_PRE | 0.230    | 0.344    |                        0.58 | match   | match                | match               |
| T3 (1) CAR     | -0.295   | 0.674**  |                        2.6  | differs | differs              | differs             |
| T3 (2) CAR     | 1.206**  | 0.880**  |                       -0.66 | match   | match                | match               |
| T3 (3) CAR_POS | -0.203   | 0.122    |                        0.78 | differs | match                | match               |
| T3 (4) CAR_POS | 0.893*   | 0.676*   |                       -0.48 | match   | match                | match               |
| T3 (3) CAR_NEG | -0.045   | 0.803*   |                        4.82 | differs | differs              | differs             |
| T3 (4) CAR_NEG | 0.185    | 0.412    |                        1.76 | match   | match                | partial             |

Paper stars as printed in the working paper. 'partial' = within two paper standard errors.

## 2. Data and sample

Capex, sales and EPS guidance come from I/B/E/S Guidance (ibes.det_guidance); actual capex and accounting variables from Compustat (comp.funda, comp.fundq); returns, the S&P 500 return and closing bid/ask quotes from CRSP (crsp.dsf, crsp.dsi). I/B/E/S tickers are linked to CRSP PERMNOs with the WRDS link table valid on the announcement date, and PERMNOs to GVKEYs with the CCM link history (LU/LC links). The forecasted fiscal year is matched to the Compustat fiscal year whose datadate has the same year and month as the I/B/E/S period end.

| Step                                               |   Ours |   Paper | Difference   |
|:---------------------------------------------------|-------:|--------:|:-------------|
| I/B/E/S annual capex forecasts, 2002-2016          | 49,999 |         |              |
| one forecast per firm-quarter (first)              | 43,422 |         |              |
| matched to Compustat actual capex                  | 41,452 |  40,785 | +1.6%        |
| with a five-day CRSP market reaction               | 41,443 |  36,900 | +12.3%       |
| not issued on the day of an earnings forecast (D9) | 20,344 |  19,427 | +4.7%        |
| issued 2003-2015 (final sample)                    | 18,866 |  17,577 | +7.3%        |

Paper counts from Section 2.2. The paper's arithmetic is exact (36,900 - 17,473 - 1,850 = 17,577), so the collapse to firm-quarters is applied before the first count (decision D6).

Data vintage: WRDS tables pulled between 2026-11-09 19:49 and 2026-11-10 02:52 (data/raw/_pull_log.csv). I/B/E/S Guidance and Compustat have been revised since the paper was written, so exact equality of counts is not expected.

## 3. Table 1: descriptive statistics

### Panel A

| Variable     |   Obs. |    Mean |   Median |     S.D. |     Min |       Max |
|:-------------|-------:|--------:|---------:|---------:|--------:|----------:|
| CAPEX_FORE   | 18,866 | 551.05  |  100     | 1430.43  |   2     | 10500     |
| paper        | 17,577 | 586.539 |  120     | 1318.43  |   2     |  8000     |
| CAPEX_ACT    | 18,866 | 574.861 |   96.703 | 1505.33  |   0.517 | 10861     |
| paper        | 17,577 | 654.077 |  123.512 | 1527.15  |   0     |  9496     |
| CAPEX_ADJ    | 18,866 |   3.945 |   -0.326 |   44.512 | -88.676 |   261.366 |
| paper        | 17,577 |   7.421 |    0     |   48.482 | -77.05  |   290.91  |
| CAR          | 18,866 |   0.318 |    0.219 |    9.283 | -28.384 |    29.42  |
| paper        | 17,577 |  -0.148 |    0.069 |    8.974 | -31.359 |    25.35  |
| SIZE         | 18,849 |   7.347 |    7.278 |    1.645 |   3.665 |    11.705 |
| paper        | 17,577 |   7.378 |    7.344 |    1.629 |   1.366 |    11.3   |
| LAG_CAPX_MIL | 18,854 | 554.977 |   92.609 | 1492.62  |   0.587 | 11027     |
| paper        | 17,546 | 611.045 |  118.307 | 1398.01  |   0     |  8620.08  |
| SURP         | 18,840 |  -0.016 |    0     |    0.815 |  -4.258 |     3.436 |
| paper        | 17,577 |  -0.033 |    0     |    0.783 |  -4.684 |     3.212 |
| EA_DUM       | 18,866 |   0.662 |    1     |    0.473 |   0     |     1     |
| paper        | 17,577 |   0.559 |    1     |    0.497 |   0     |     1     |

CAPEX_FORE, CAPEX_ACT and LAG_CAPX in $ millions; CAPEX_ADJ and CAR in percent. Grey rows: working paper (May 2019).

Winsorisation is not described in the paper. The table below compares our raw extremes and 1st/99th percentiles with the paper's min and max; where 'paper closer to' says winsorised, the paper most likely truncated that variable (decision D14).

| Variable     |   raw min |      p1 |       p99 |    raw max |   paper min |   paper max | paper closer to   | we winsorise   |
|:-------------|----------:|--------:|----------:|-----------:|------------:|------------:|:------------------|:---------------|
| CAPEX_FORE   |     0.2   |   2     | 10500     |  41000     |       2     |    8000     | winsorised        | yes            |
| CAPEX_ACT    |  -401.609 |   0.517 | 10861     |  40145     |       0     |    9496     | winsorised        | yes            |
| CAPEX_ADJ    | -2108.05  | -88.676 |   261.366 | 111314     |     -77.05  |     290.91  | winsorised        | yes            |
| CAR          |  -108.721 | -28.384 |    29.42  |    121.032 |     -31.359 |      25.35  | winsorised        | yes            |
| SIZE         |     1.203 |   3.665 |    11.705 |     13.122 |       1.366 |      11.3   | raw               | yes            |
| LAG_CAPX_MIL |  -330     |   0.587 | 11027     |  40145     |       0     |    8620.08  | winsorised        | yes            |
| SURP         |  -154.86  |  -4.258 |     3.436 |    144.92  |      -4.684 |       3.212 | winsorised        | yes            |

### Panel B: capex forecasts by year

|   Year |   Forecasts (ours) |   Forecasts (paper) |   First-time (ours) |   First-time (paper) |
|-------:|-------------------:|--------------------:|--------------------:|---------------------:|
|   2003 |                 42 |                  22 |                  40 |                   22 |
|   2004 |                354 |                 226 |                 178 |                  121 |
|   2005 |                639 |                 488 |                 222 |                  181 |
|   2006 |              1,038 |                 874 |                 280 |                  235 |
|   2007 |                972 |                 841 |                 242 |                  197 |
|   2008 |              1,738 |               1,560 |                 275 |                  234 |
|   2009 |              2,231 |               2,064 |                 290 |                  225 |
|   2010 |              2,086 |               1,974 |                 156 |                  133 |
|   2011 |              2,139 |               2,048 |                 144 |                  122 |
|   2012 |              2,108 |               1,993 |                 120 |                   96 |
|   2013 |              1,959 |               1,931 |                  87 |                   87 |
|   2014 |              1,820 |               1,779 |                  77 |                   73 |
|   2015 |              1,740 |               1,777 |                  69 |                   64 |

### Panel C: forecast types

| Type   |   Ours | Share   |   Paper | Paper share   |
|:-------|-------:|:--------|--------:|:--------------|
| point  | 10,300 | 54.60%  |   9,720 | 55.30%        |
| range  |  8,044 | 42.64%  |   6,061 | 34.48%        |
| other  |    522 | 2.77%   |   1,796 | 10.22%        |

Range forecasts: CAPEX_ADJ is zero inside the range and measured from the violated end-point outside it, scaled by the range midpoint (D7). Open-ended forecasts are treated as points (D8).

## 4. Table 2: capex adjustments and the market reaction to capex forecasts

Dependent variable: CAPEX_ADJ, the percentage deviation of actual from forecasted capex. CAR, SF_CAR, MKTRET and CAR_PRE are standardised (mean 0, SD 1), so each coefficient is the change in CAPEX_ADJ in percentage points for a one-SD change. Robust standard errors in parentheses; *, **, *** = 10/5/1%, two-tailed, t with G-1 degrees of freedom.

|               | (1)             | (2)             | (3)             | (4)             | (5)             | (6)           | (7)             | (8)              |
|:--------------|:----------------|:----------------|:----------------|:----------------|:----------------|:--------------|:----------------|:-----------------|
| CAR           | 1.193***(0.331) | 1.228***(0.329) | 1.276***(0.336) | 1.017***(0.260) | 1.017***(0.220) | 0.996*(0.521) | 1.014***(0.220) | 0.988***(0.219)  |
| paper         | 1.193***(0.372) | 1.207***(0.371) | 1.196***(0.377) | 0.975***(0.294) | 0.975***(0.322) | 0.672*(0.370) | 1.006***(0.326) | 0.849***(0.304)  |
| SF_CAR        |                 |                 |                 |                 |                 | 0.393(0.643)  |                 |                  |
| paper         |                 |                 |                 |                 |                 | 0.039(0.061)  |                 |                  |
| MKTRET        |                 |                 |                 |                 |                 |               | 0.161(0.322)    | 0.169(0.322)     |
| paper         |                 |                 |                 |                 |                 |               | -0.252(0.308)   | -0.202(0.322)    |
| CAR_PRE       |                 |                 |                 |                 |                 |               | 0.369(0.235)    | 0.344(0.238)     |
| paper         |                 |                 |                 |                 |                 |               | 0.305(0.200)    | 0.230(0.197)     |
| SIZE          |                 | 0.743(0.499)    | 0.708(0.518)    | 2.080**(0.951)  | 2.080**(0.986)  | 4.074(2.784)  | 2.093**(0.986)  | 1.139(1.107)     |
| paper         |                 | 1.485**(0.632)  | 1.411**(0.653)  | 0.419(1.302)    | 0.419(1.128)    | 3.351(2.203)  | 0.444(1.131)    | -1.513(1.415)    |
| LAG_CAPX      |                 |                 |                 |                 |                 |               |                 | -0.084***(0.029) |
| paper         |                 |                 |                 |                 |                 |               |                 | -0.160***(0.032) |
| SURP          |                 |                 |                 |                 |                 |               |                 | 0.228(0.343)     |
| paper         |                 |                 |                 |                 |                 |               |                 | 0.213(0.385)     |
| EA_DUM        |                 |                 |                 |                 |                 |               |                 | -1.408(1.104)    |
| paper         |                 |                 |                 |                 |                 |               |                 | -0.108(0.619)    |
| Obs.          | 18,849          | 18,849          | 18,849          | 18,849          | 18,849          | 3,791         | 18,846          | 18,764           |
| paper         | 17,577          | 17,577          | 17,577          | 17,577          | 17,577          | 3,456         | 17,577          | 17,505           |
| Adj. R²       | 0.001           | 0.001           | 0.002           | 0.501           | 0.501           | 0.568         | 0.501           | 0.502            |
| paper         | 0.001           | 0.003           | 0.007           | 0.523           | 0.523           | 0.648         | 0.523           | 0.526            |
| Fixed effects | None            | None            | Yr-qtr          | Firm, yr-qtr    | Firm, yr-qtr    | Firm, yr-qtr  | Firm, yr-qtr    | Firm, yr-qtr     |
| Clusters      | Firm (2178)     | Firm (2178)     | Firm (2178)     | Firm (2178)     | Industry (67)   | Industry (62) | Industry (67)   | Industry (67)    |

Model (6) uses the 3,791 forecasts with a sales forecast for the same fiscal period (paper 3,456); median distance between the two announcements 86 days (paper 86). Industry = two-digit SIC, fixed per firm (D18).

## 5. Table 3: information asymmetry and the sign of the reaction

Columns (1) and (3): forecasts whose mean relative bid-ask spread over days [-2, +2] is not above the mean over days [-10, -3] ('Lower spreads'); columns (2) and (4): above ('Higher spreads'). CAR_POS = max(CAR, 0) and CAR_NEG = min(CAR, 0), each standardised (D35). All models include the controls of Table 2 model (8), firm and year-quarter fixed effects, and industry clusters.

|               | (1)            | (2)            | (3)           | (4)           |
|:--------------|:---------------|:---------------|:--------------|:--------------|
| CAR           | 0.674**(0.327) | 0.880**(0.350) |               |               |
| paper         | -0.295(0.372)  | 1.206**(0.497) |               |               |
| CAR_POS       |                |                | 0.122(0.360)  | 0.676*(0.388) |
| paper         |                |                | -0.203(0.419) | 0.893*(0.455) |
| CAR_NEG       |                |                | 0.803*(0.455) | 0.412(0.394)  |
| paper         |                |                | -0.045(0.176) | 0.185(0.129)  |
| MKTRET        | -0.022(0.588)  | 0.256(0.318)   | -0.018(0.588) | 0.257(0.318)  |
| paper         | 0.103(0.539)   | -0.327(0.654)  | 0.104(0.538)  | -0.323(0.655) |
| CAR_PRE       | 0.061(0.301)   | 0.349(0.347)   | 0.060(0.302)  | 0.349(0.346)  |
| paper         | 0.452(0.375)   | 0.124(0.302)   | 0.451(0.376)  | 0.130(0.305)  |
| Obs.          | 8,135          | 10,542         | 8,135         | 10,542        |
| paper         | 7,770          | 9,570          | 7,770         | 9,570         |
| Adj. R²       | 0.503          | 0.515          | 0.503         | 0.515         |
| paper         | 0.512          | 0.531          | 0.512         | 0.531         |
| Fixed effects | Firm, yr-qtr   | Firm, yr-qtr   | Firm, yr-qtr  | Firm, yr-qtr  |
| Clusters      | Industry (67)  | Industry (67)  | Industry (67) | Industry (67) |

### p-values of the difference between Lower and Higher spreads

| Coefficient         |   Ours |   Paper |
|:--------------------|-------:|--------:|
| CAR, (1) vs (2)     |  0.672 |   0.019 |
| MKTRET, (1) vs (2)  |  0.588 |   0.656 |
| CAR_PRE, (1) vs (2) |  0.556 |   0.54  |
| CAR_POS, (3) vs (4) |  0.232 |   0.099 |
| CAR_NEG, (3) vs (4) |  0.52  |   0.262 |
| MKTRET, (3) vs (4)  |  0.592 |   0.658 |
| CAR_PRE, (3) vs (4) |  0.555 |   0.549 |

The paper does not say how the difference was tested. We estimate one pooled model in which every regressor and both fixed effects are interacted with the split, with a joint industry-clustered covariance (the analogue of Stata suest); point estimates equal the separate regressions.

## 6. Numbers quoted in the text

### Economic magnitudes (coefficient / mean CAPEX_ADJ)

| Coefficient   |   Ours | Ours % of mean   | Paper   | Source                                                |
|:--------------|-------:|:-----------------|:--------|:------------------------------------------------------|
| T2 (1) CAR    |  1.193 | 30.2%            | 16.1%   | Sec. 1 and 3.1: 1.193 / 7.421                         |
| T2 (4) CAR    |  1.017 | 25.8%            | 13.1%   | Sec. 3.1: 0.975 / 7.421 with firm and time FE         |
| T2 (8) CAR    |  0.988 | 25.1%            | 11.4%   | Sec. 3.1: 0.849 / 7.421 with all controls             |
| T3 (2) CAR    |  0.88  | 22.3%            | 16.2%   | Sec. 3.2.1: Higher spreads, upward adjustment         |
| T3 (1) CAR    |  0.674 | 17.1%            | -3.9%   | Sec. 3.2.1: Lower spreads, downward and insignificant |

Our mean CAPEX_ADJ is 3.945% (paper 7.421%).

### Moments and footnotes

| Moment                                       |    Ours |   Paper |
|:---------------------------------------------|--------:|--------:|
| corr(SURP, CAR) [fn 22]                      |   0.069 |   0.08  |
| corr(SURP, CAPEX_ADJ) [fn 22]                |   0     |   0.001 |
| median CAR, capex forecasts (%) [fn 20]      |   0.219 |   0.069 |
| median SF_CAR, sales forecasts (%) [fn 20]   |   0.447 |   0.457 |
| mean CFO_t+1 (% assets) [Sec 3.3]            |  10.011 |  10.5   |
| mean CAPEX_ADJ (%) [Table 1]                 |   3.945 |   7.421 |
| sd CAR (%) [fn 15]                           |   9.283 |   8.974 |
| share Higher spreads [Table 3: 9,570/17,340] |   0.564 |   0.552 |
| share MF_OF=1 [Table 5 E2: 4,432/17,505]     |         |   0.253 |
| mean CAR (%) [fn 15]                         |   0.318 |  -0.148 |
| t-stat of mean CAR [fn 15: sig. at 5%]       |   4.699 |         |
| min CAR (%) [Table 1]                        | -28.384 | -31.359 |
| max CAR (%) [Table 1]                        |  29.42  |  25.35  |
| share point forecasts [Table 1C]             |   0.546 |   0.553 |
| share range forecasts [Table 1C]             |   0.426 |   0.345 |
| share other forecasts [Table 1C]             |   0.028 |   0.102 |

## 7. Robustness reported in the text

| Specification                                    | CAR (ours)       |   Obs. | Paper              |
|:-------------------------------------------------|:-----------------|-------:|:-------------------|
| Baseline, Table 2 model (8)                      | 0.988*** (0.219) | 18,764 | 0.849***           |
| CAPEX_ADJ relative to the range midpoint (fn 17) | 0.987*** (0.235) | 18,764 | robust (no number) |
| Point and range forecasts only (fn 17)           | 0.979*** (0.206) | 18,243 | robust (no number) |
| Forecasts from 2009 on (fn 23)                   | 1.199*** (0.258) | 14,008 | robust (no number) |
| + industry x year FE (fn 19)                     | 0.779*** (0.241) | 18,764 | 0.800**            |
| + state x year FE (fn 19)                        | 0.752*** (0.221) | 17,932 | 0.968***           |
| + asset growth control (fn 18)                   | 0.960*** (0.219) | 18,745 | robust (no number) |

## 8. Calibration on WRDS data

The switches below were set against sample characteristics only, before Tables 2 and 3 were read under each setting. Every choice is a switch in `config.py` and is logged in `REPLICATION_NOTES.md`.

- **D3, open-ended forecasts.** Set from the I/B/E/S Guidance User Guide (Thomson Reuters, 2009, Appendix 2): codes 03, 04, 10–13 and 15–17 ("more than", "at least", "less than", "not to exceed", ...) are open-ended; 01, 06 and 08 are ranges; 02 and 14 are point forecasts. Under this coding the point share matches the paper (54.6% vs 55.3%), but open-ended forecasts are 2.8% of the final sample against 10.2%, and ranges 42.6% against 34.5%.
- **D4, units.** Guidance values are recorded in millions or billions. After conversion, the median ratio of actual to forecast capex is 0.99.
- **D9, "concurrent with an earnings forecast".** Four definitions were compared (table below). Counting all earnings-type guidance (EPS, GAAP EPS, net income, pretax income, EBITDA, EBITDA per share, operating profit, FFO) as an earnings forecast brings the final sample closest to the paper: 18,866 against 17,577, and 20,344 against 19,427 after this step. EPS-only guidance is reported as a robustness check (§9).
- **D10, earnings announcement window.** A same-day match gives an EA_DUM mean of 0.662, against 0.899 within ±1 day and 0.559 in the paper. Same day is adopted; ±1 day is a robustness check (§9).
- **D14, winsorisation (revised).** The pre-data inference that dollar levels were not winsorised (from the paper's minimum of 0.000 for actual capex) was overturned by the data: zero capex is common enough that the 1st percentile is itself about 0. In the first WRDS run (EPS-only definition, 22,961 forecasts) the 99th percentile of actual capex was exactly 9,496, the paper's maximum; in the final sample the 1st percentile of forecast capex equals the paper's minimum of 2.0, and for every Table 1 variable except SIZE the paper's extremes are closer to our 1st/99th percentiles than to our raw extremes. All Table 1 variables are therefore winsorised at 1% and 99%. For SIZE the evidence is mixed (the paper's minimum is close to our raw minimum, its maximum close to our 99th percentile); SIZE is kept winsorised, which matters little because it is a control.
- **Extraction fixes.** Two technical issues in the WRDS download were fixed before estimation (repeated row indices in chunked downloads; nullable pyarrow data types). Neither changes any variable definition.

### D9: sample characteristics under four definitions (no regressions)

| Definition of an earnings forecast   |   final N |   dropped at w3 (%) |   EA_DUM mean |   range share |   CAPEX_ADJ mean |   CAPEX_ADJ median |   CAR mean |
|:-------------------------------------|----------:|--------------------:|--------------:|--------------:|-----------------:|-------------------:|-----------:|
| paper                                |    17,577 |                47.4 |         0.559 |         0.345 |            7.421 |              0     |     -0.148 |
| EPS only                             |    22,961 |                39.9 |         0.902 |         0.448 |            2.867 |             -0.385 |      0.287 |
| EPS + GAAP EPS                       |    22,117 |                42   |         0.902 |         0.445 |            3.557 |             -0.276 |      0.271 |
| EPS + GPS + NET + PRE                |    21,146 |                44.6 |         0.901 |         0.441 |            3.805 |             -0.185 |      0.29  |
| all earnings-type                    |    18,866 |                50.9 |         0.899 |         0.426 |            3.945 |             -0.326 |      0.318 |

Produced by calibrate_d9.py. Only sample characteristics were compared when choosing the definition.

## 9. Table 3 sensitivity

Table 3's two tests re-estimated under the alternative settings of D9 and D10, and, as a diagnostic not in the paper, separately for forecasts issued with and without an earnings announcement. Lo = spreads do not rise, Hi = spreads rise; p = p-value of the Lo-Hi difference.

### Does the effect depend on rising spreads? (Table 3 models 1-2)

| Setting                    |   N Lo |   N Hi | CAR Lo          | CAR Hi           |   p of difference |
|:---------------------------|-------:|-------:|:----------------|:-----------------|------------------:|
| paper                      |  7,770 |  9,570 | -0.295          | 1.206            |             0.019 |
| 1. main specification      |  8,135 | 10,542 | 0.674** (0.327) | 0.880** (0.350)  |             0.672 |
| 2. D9: EPS only            |  9,842 | 12,859 | 0.637** (0.311) | 0.899*** (0.309) |             0.555 |
| 3. D10: EA within +/-1 day |  8,132 | 10,539 | 0.645* (0.326)  | 0.873** (0.349)  |             0.641 |
| 4. diagnostic: EA_DUM = 0  |  2,925 |  3,412 | 0.709 (0.666)   | 2.180** (0.841)  |             0.139 |
| 5. diagnostic: EA_DUM = 1  |  5,210 |  7,130 | 0.586 (0.418)   | 0.409 (0.404)    |             0.781 |

### Positive vs negative reactions (Table 3 models 3-4)

| Setting                    | CAR_POS Lo     | CAR_POS Hi     |   p CAR_POS | CAR_NEG Lo     | CAR_NEG Hi     |   p CAR_NEG |
|:---------------------------|:---------------|:---------------|------------:|:---------------|:---------------|------------:|
| paper                      | -0.203         | 0.893          |       0.099 | -0.045         | 0.185          |       0.262 |
| 1. main specification      | 0.122 (0.360)  | 0.676* (0.388) |       0.232 | 0.803* (0.455) | 0.412 (0.394)  |       0.52  |
| 2. D9: EPS only            | 0.123 (0.347)  | 0.638 (0.417)  |       0.312 | 0.747* (0.410) | 0.467 (0.406)  |       0.627 |
| 3. D10: EA within +/-1 day | 0.117 (0.367)  | 0.685* (0.394) |       0.234 | 0.769* (0.456) | 0.396 (0.395)  |       0.548 |
| 4. diagnostic: EA_DUM = 0  | -0.133 (0.888) | 1.205 (1.315)  |       0.442 | 1.192 (1.049)  | 1.425* (0.831) |       0.889 |
| 5. diagnostic: EA_DUM = 1  | 0.354 (0.500)  | 0.556 (0.370)  |       0.773 | 0.362 (0.572)  | -0.018 (0.383) |       0.562 |

Produced by t3_sensitivity.py. The variants were specified before their results were seen; the main specification is not changed on the basis of these tables.

## 10. Implementation choices

The paper leaves the following choices open. Each is a switch in config.py; the full log with the evidence for each choice is in REPLICATION_NOTES.md.

| ID   | Choice                                       | Setting used                                                       |
|:-----|:---------------------------------------------|:-------------------------------------------------------------------|
| D2   | Sample years                                 | 2003-2015                                                          |
| D3   | Open-ended range_desc codes                  | 03, 04, 10, 11, 12, 13, 15, 16, 17                                 |
| D5   | Horizon / nearest fiscal year                | <= 24 months; nearest only = True                                  |
| D6   | Firm-quarter collapse                        | keep first; before waterfall = True                                |
| D7   | Range denominator                            | mid                                                                |
| D8   | Open-ended forecasts                         | val1_as_point                                                      |
| D9   | Guidance counted as an earnings forecast     | EPS, GPS, NET, PRE, EBT, EBS, OPR, FFO                             |
| D9   | Earnings-forecast concurrency window (days)  | 0                                                                  |
| D10  | EA_DUM window (days)                         | 0                                                                  |
| D11  | After-close shift of day 0                   | False                                                              |
| D12  | Returns required in CAR                      | 5                                                                  |
| D13  | Min. gap capex-sales forecast (trading days) | 5                                                                  |
| D14  | Winsorised variables                         | CAPEX_ADJ, CAR, CAR_PRE, SF_CAR, SURP, LAG_CAPX; levels too = True |
| D15  | LAG_CAPX in regressions                      | mv_pct                                                             |
| D17  | Spread unit                                  | percent                                                            |
| D18  | Industry                                     | sic2                                                               |
| D25  | Singletons dropped                           | False                                                              |
| D26  | Degrees-of-freedom convention                | reghdfe                                                            |
| D27  | Standardisation sample                       | full                                                               |
| D32  | SURP split-adjusted                          | True                                                               |
| D35  | CAR_POS / CAR_NEG                            | split raw CAR at 0, then standardise                               |

## 11. Where the replication differs, and why

Items that differ from the paper by more than one of the paper's standard errors (coefficients), by more than a quarter of a standard deviation (Table 1 means) or by more than 10% (sample size), with the decisions most likely responsible:

| Item           |   Paper |   Ours |   Gap | Look at                                               |
|:---------------|--------:|-------:|------:|:------------------------------------------------------|
| T2 (6) SF_CAR  |   0.039 |  0.393 |  5.8  | D13 (which sales forecast)                            |
| T2 (7) MKTRET  |  -0.252 |  0.161 |  1.34 | D11 (day 0)                                           |
| T2 (8) MKTRET  |  -0.202 |  0.169 |  1.15 | D11 (day 0)                                           |
| T3 (1) CAR     |  -0.295 |  0.674 |  2.6  | D11 (day 0), D12 (missing returns), D14 (winsorising) |
| T3 (3) CAR_POS |  -0.203 |  0.122 |  0.78 | D35 (split then standardise), D17 (spread split)      |
| T3 (3) CAR_NEG |  -0.045 |  0.803 |  4.82 | D35, D17                                              |
| T3 (4) CAR_NEG |   0.185 |  0.412 |  1.76 | D35, D17                                              |

General sources of difference: (i) I/B/E/S Guidance, Compustat and CRSP have been revised since 2019; (ii) the numbers compared here come from the May 2019 working paper, and the published version may differ; (iii) the paper does not state its winsorisation, its treatment of open-ended forecasts, its industry definition, or how the difference tests were computed.

## 12. Discussion

### What replicates

- **Sample.** 18,866 forecasts by 2,180 firms against 17,577 by 1,790, a difference of 7.3%. Yearly counts track the paper closely, especially from 2010 on (for example 1,959 vs 1,931 in 2013 and 1,740 vs 1,777 in 2015).
- **Table 2.** The CAR coefficient is positive and significant in all eight models and within one of the paper's standard errors in each: 1.193 against 1.193 in model (1), 0.988 against 0.849 with all controls in model (8). Firm fixed effects lower it by a similar proportion (−20% vs −18%), and the adjusted R² with firm fixed effects is 0.50 against 0.52. The three placebo reactions (SF_CAR, MKTRET, CAR_PRE) are insignificant, as in the paper.
- **Figures quoted in the text.** corr(SURP, CAR) is 0.069 (paper 0.08); the median sales-forecast reaction is 0.447% (0.457%); the median distance between capex and sales forecasts is 86 days (86); mean future CFO is 10.0% of assets (10.5%); 56.4% of forecasts see rising spreads (55.2%). The fixed-effect robustness checks of footnote 19 give 0.78 and 0.75 (0.80 and 0.97).

Because our mean CAPEX_ADJ is lower (3.9% vs 7.4%), the same coefficient is a larger share of the mean; the effect in percentage points is what replicates.

### What does not replicate

- **Table 3.** The effect appears whether or not spreads rise: 0.674** where they do not and 0.880** where they do, with a difference p-value of 0.672 (paper: −0.295, 1.206** and p = 0.019). The result is the same under the narrow definition of an earnings forecast (p = 0.555) and the ±1-day announcement window (p = 0.641). Positive reactions are significant only where spreads rise (0.676* vs 0.122), as in the paper, but that difference is not significant either (p = 0.232; paper 0.099).
- **Moments that differ under every setting.** Mean CAR is +0.32% (t = 4.7) against −0.15%; mean CAPEX_ADJ is 3.9% against 7.4%, and its median −0.33% against 0.000; ranges are 42.6% of forecasts against 34.5%, and open-ended forecasts 2.8% against 10.2%; EA_DUM is 0.662 against 0.559.
- **Sample step 2.** The paper loses 3,885 forecasts when requiring a five-day CRSP return; we lose 9. The paper does not say what else this step required.

### Possible explanations

1. **Data vintage.** I/B/E/S Guidance has been revised since the paper was written. The forecast-type split, the distribution of CAPEX_ADJ and the sign of the mean CAR differ under every specification tried, which points to the data rather than to a coding choice.
2. **Spread measure.** We use CRSP daily closing quotes; the paper does not state its source. The share of forecasts with rising spreads matches, but a split with the same share can sort different forecasts into each group.
3. **Unstated choices.** The paper does not report how the difference tests were computed or what step 2 of the sample construction required beyond CRSP returns.

### A diagnostic split

Among forecasts not issued with an earnings announcement (N = 6,337), the coefficient is 2.180** where spreads rise and 0.709 where they do not (difference p = 0.139). Among forecasts issued with an announcement (N = 12,340), neither group shows an effect (0.586 and 0.409). This is consistent with earnings news in the announcement window masking the capex-specific information that the spread split is meant to capture. The split is not in the paper and the difference is not significant, so it is a lead for further work rather than evidence that Table 3 replicates.

### Conclusion

Tables 1 and 2 replicate closely: the market reaction to a capex forecast predicts the subsequent revision of actual capex, with magnitudes, robustness and placebo results in line with the paper. The cross-sectional evidence in Table 3 that ties this relation to informed trading does not replicate in current WRDS data under any of the specifications tried. The analysis was stopped at this point rather than searching further over specifications.

## 13. Reproducibility

Code: Python package jw2020 (no Stata needed). Fixed-effects OLS with clustered standard errors is implemented in hdfe.py following Stata reghdfe: fixed effects absorbed by alternating projections; V = c(X'X)-1[ΣgXg'ugug'Xg](X'X)-1 with c = G/(G-1)·(N-1)/(N-K); fixed effects nested in the cluster variable are not counted in K. tests/test_hdfe.py checks the estimator against least squares with dummy variables to 1e-8.

```
python check_wrds.py
python pull_wrds.py
python diagnose.py
python run_all.py
```

Generated 2026-11-10 14:39 with Python 3.11.18, pandas 2.2.3, numpy 2.4.6. Data: WRDS.
