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
