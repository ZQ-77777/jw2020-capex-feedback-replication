"""
Numbers reported in the paper, keyed as (table, model, variable) -> (coef, se).
Source: working-paper version dated May 2019 (IIM Bangalore Accounting Research Conference).
!! The published RFS version (Aug 2020) may differ: before reporting, re-check every number
!! against the published PDF (HKUST library -> academic.oup.com, doi:10.1093/rfs/hhz132)
!! and edit this file.
"""

T1A = {  # variable: (N, mean, median, sd, min, max)
    "CAPEX_FORE": (17577, 586.539, 120.000, 1318.429, 2.000, 8000.000),
    "CAPEX_ACT": (17577, 654.077, 123.512, 1527.146, 0.000, 9496.000),
    "CAPEX_ADJ": (17577, 7.421, 0.000, 48.482, -77.050, 290.910),
    "CAR": (17577, -0.148, 0.069, 8.974, -31.359, 25.350),
    "SIZE": (17577, 7.378, 7.344, 1.629, 1.366, 11.300),
    "LAG_CAPX_MIL": (17546, 611.045, 118.307, 1398.011, 0.000, 8620.081),
    "SURP": (17577, -0.033, 0.000, 0.783, -4.684, 3.212),
    "EA_DUM": (17577, 0.559, 1.000, 0.497, 0.000, 1.000),
}
T1B = {2003: (22, 22), 2004: (226, 121), 2005: (488, 181), 2006: (874, 235), 2007: (841, 197),
       2008: (1560, 234), 2009: (2064, 225), 2010: (1974, 133), 2011: (2048, 122), 2012: (1993, 96),
       2013: (1931, 87), 2014: (1779, 73), 2015: (1777, 64)}
T1C = {"point": (9720, 0.5530), "range": (6061, 0.3448), "other": (1796, 0.1022)}

T2 = {
    ("CAR", 1): (1.193, 0.372), ("CAR", 2): (1.207, 0.371), ("CAR", 3): (1.196, 0.377),
    ("CAR", 4): (0.975, 0.294), ("CAR", 5): (0.975, 0.322), ("CAR", 6): (0.672, 0.370),
    ("CAR", 7): (1.006, 0.326), ("CAR", 8): (0.849, 0.304),
    ("SF_CAR", 6): (0.039, 0.061),
    ("MKTRET", 7): (-0.252, 0.308), ("MKTRET", 8): (-0.202, 0.322),
    ("CAR_PRE", 7): (0.305, 0.200), ("CAR_PRE", 8): (0.230, 0.197),
    ("SIZE", 2): (1.485, 0.632), ("SIZE", 3): (1.411, 0.653), ("SIZE", 4): (0.419, 1.302),
    ("SIZE", 5): (0.419, 1.128), ("SIZE", 6): (3.351, 2.203), ("SIZE", 7): (0.444, 1.131),
    ("SIZE", 8): (-1.513, 1.415),
    ("LAG_CAPX", 8): (-0.160, 0.032), ("SURP", 8): (0.213, 0.385), ("EA_DUM", 8): (-0.108, 0.619),
}
T2_N = {1: 17577, 2: 17577, 3: 17577, 4: 17577, 5: 17577, 6: 3456, 7: 17577, 8: 17505}
T2_R2 = {1: 0.001, 2: 0.003, 3: 0.007, 4: 0.523, 5: 0.523, 6: 0.648, 7: 0.523, 8: 0.526}

T3 = {
    ("CAR", 1): (-0.295, 0.372), ("CAR", 2): (1.206, 0.497),
    ("CAR_POS", 3): (-0.203, 0.419), ("CAR_POS", 4): (0.893, 0.455),
    ("CAR_NEG", 3): (-0.045, 0.176), ("CAR_NEG", 4): (0.185, 0.129),
    ("MKTRET", 1): (0.103, 0.539), ("MKTRET", 2): (-0.327, 0.654),
    ("MKTRET", 3): (0.104, 0.538), ("MKTRET", 4): (-0.323, 0.655),
    ("CAR_PRE", 1): (0.452, 0.375), ("CAR_PRE", 2): (0.124, 0.302),
    ("CAR_PRE", 3): (0.451, 0.376), ("CAR_PRE", 4): (0.130, 0.305),
}
T3_P = {"CAR": 0.019, "MKTRET_12": 0.656, "CAR_PRE_12": 0.540,
        "CAR_POS": 0.099, "CAR_NEG": 0.262, "MKTRET_34": 0.658, "CAR_PRE_34": 0.549}
T3_N = {1: 7770, 2: 9570, 3: 7770, 4: 9570}

T4 = {
    ("CAPEX", 1): (0.393, 0.278), ("CAPEX_FORE", 2): (0.541, 0.302), ("CAPEX_ADJ_MKT", 2): (0.206, 0.057),
    ("CAPEX_ADJ_OTH", 2): (0.080, 0.117), ("CAPEX_FORE", 3): (0.535, 0.309), ("CAPEX_ADJ_MKT", 3): (0.184, 0.056),
    ("CAPEX_ADJ_OTH", 3): (0.065, 0.119),
    ("CAPEX", 4): (0.948, 1.666), ("CAPEX_FORE", 5): (0.338, 1.816), ("CAPEX_ADJ_MKT", 5): (0.829, 0.185),
    ("CAPEX_ADJ_OTH", 5): (0.395, 0.798), ("CAPEX_FORE", 6): (0.922, 1.584), ("CAPEX_ADJ_MKT", 6): (0.862, 0.188),
    ("CAPEX_ADJ_OTH", 6): (0.535, 0.799),
    ("CAPEX", 7): (0.871, 1.663), ("CAPEX_FORE", 8): (0.202, 1.814), ("CAPEX_ADJ_MKT", 8): (0.860, 0.190),
    ("CAPEX_ADJ_OTH", 8): (0.385, 0.798), ("CAPEX_FORE", 9): (0.794, 1.581), ("CAPEX_ADJ_MKT", 9): (0.894, 0.193),
    ("CAPEX_ADJ_OTH", 9): (0.528, 0.800),
}
T4_N = {1: 16353, 2: 16353, 3: 16311, 4: 16370, 5: 16370, 6: 16327, 7: 16370, 8: 16370, 9: 16327}

# Table 5: CAR coefficient in columns (1)-(6) = All low/high, Lower spreads low/high, Higher spreads low/high
T5 = {
    "A_PIN": dict(coef=[-0.054, 1.246, -1.404, -0.244, -0.397, 1.604], se=[0.616, 0.508, 1.222, 1.116, 0.761, 0.952],
                  p=[0.076, 0.573, 0.058], n=[3946, 3861, 1847, 1750, 2070, 2080]),
    "B_INSIDER": dict(coef=[1.737, 0.420, 1.702, 0.507, 2.388, -0.171], se=[0.597, 0.611, 1.164, 1.416, 1.313, 0.844],
                      p=[0.153, 0.512, 0.130], n=[4548, 4557, 1989, 1982, 2514, 2544]),
    "C_ERC": dict(coef=[1.561, 0.199, 0.683, -0.886, 2.001, 0.364], se=[0.437, 0.283, 0.841, 0.486, 0.601, 0.408],
                  p=[0.007, 0.128, 0.020], n=[8833, 8672, 3897, 3873, 4832, 4738]),
    "D_PAYDUR": dict(coef=[-1.083, 0.603, 0.197, -0.319, -1.329, 1.649], se=[0.583, 0.726, 1.200, 1.408, 0.871, 1.275],
                     p=[0.083, 0.804, 0.047], n=[1485, 1484, 687, 663, 794, 808]),
    "E2_MFOF": dict(coef=[0.555, 1.203, -0.253, -0.948, 0.573, 2.172], se=[0.348, 0.426, 0.444, 1.053, 0.531, 0.935],
                    p=[0.176, 0.494, 0.027], n=[13073, 4432, 5798, 1972, 7144, 2426]),
}

T5E1 = {
    ("EVENT", 1): (0.014, 0.001), ("EVENT", 2): (0.015, 0.001), ("EVENT", 3): (0.015, 0.001),
    ("EVENT", 4): (0.009, 0.001), ("EVENT", 5): (0.009, 0.001),
    ("MF_OF", 4): (-0.022, 0.005), ("MF_OF", 5): (-0.022, 0.004),
    ("EVENT_x_MF_OF", 4): (0.013, 0.002), ("EVENT_x_MF_OF", 5): (0.007, 0.002),
    ("CAPEX", 5): (-0.015, 0.006), ("EVENT_x_CAPEX", 5): (0.001, 0.002), ("MF_OF_x_CAPEX", 5): (0.005, 0.005),
    ("EVENT_x_MF_OF_x_CAPEX", 5): (0.006, 0.003),
    ("SIZE", 3): (-0.131, 0.012), ("SIZE", 4): (-0.132, 0.012), ("SIZE", 5): (-0.133, 0.007),
    ("TURNOVER", 3): (-5.700, 0.722), ("TURNOVER", 4): (-5.780, 0.734), ("TURNOVER", 5): (-7.899, 0.547),
    ("RETVOL", 3): (3.961, 0.643), ("RETVOL", 4): (3.944, 0.639), ("RETVOL", 5): (4.557, 0.329),
}
T5E1_N = {1: 233619, 2: 233619, 3: 233619, 4: 233619, 5: 940177}

T6 = {
    ("NOISE_SIGNAL", 1): (0.005, 0.001), ("NOISE_SIGNAL", 2): (0.004, 0.001),
    ("NOISE_SIGNAL_LO_ERC", 3): (0.009, 0.002), ("NOISE_SIGNAL_HI_ERC", 3): (-0.000, 0.002),
    ("NOISE_SIGNAL_LO_ERC", 4): (0.008, 0.002), ("NOISE_SIGNAL_HI_ERC", 4): (-0.001, 0.002),
    ("LEV", 2): (0.020, 0.008), ("SIZE", 2): (0.018, 0.002), ("TANG", 2): (0.070, 0.017),
    ("ROA", 2): (-0.026, 0.010), ("NEG_ROA", 2): (0.002, 0.002), ("ROA_VOL", 2): (0.029, 0.017),
}
T6_N = {1: 250316, 2: 250316, 3: 250343, 4: 250343}

# ---------------------------------------------------------------- Tables 1-3: everything else the text says
T3_R2 = {1: 0.512, 2: 0.531, 3: 0.512, 4: 0.531}
MEAN_CAPEX_ADJ = 7.421

# Economic magnitudes quoted in the text = coefficient / mean CAPEX_ADJ
MAGNITUDES = [  # (table, model, var, paper % of mean, where)
    ("T2", 1, "CAR", 16.1, "Sec. 1 and 3.1: 1.193 / 7.421"),
    ("T2", 4, "CAR", 13.1, "Sec. 3.1: 0.975 / 7.421 with firm and time FE"),
    ("T2", 8, "CAR", 11.4, "Sec. 3.1: 0.849 / 7.421 with all controls"),
    ("T3", 2, "CAR", 16.2, "Sec. 3.2.1: Higher spreads, upward adjustment"),
    ("T3", 1, "CAR", -3.9, "Sec. 3.2.1: Lower spreads, downward and insignificant"),
]

# Numbers quoted in the text and footnotes that belong to Tables 1-3
TEXT_T13 = {
    "mean_CAR": (-0.148, "fn 15: mean CAR -14.8 bp, significant at 5%"),
    "sd_CAR": (8.974, "fn 15: SD of CAR"),
    "median_CAR": (0.069, "fn 20: median market reaction to capex forecasts (%)"),
    "median_SF_CAR": (0.457, "fn 20: median market reaction to sales forecasts (%)"),
    "n_SF": (3456, "fn 21: capex forecasts with a sales forecast for the same fiscal period"),
    "median_SF_dist": (86, "fn 21: median days between the sales and the capex forecast"),
    "corr_SURP_CAR": (0.08, "fn 22: correlation, significant at 1%"),
    "corr_SURP_ADJ": (0.001, "fn 22: correlation, insignificant"),
    "share_point": (0.5530, "Table 1C"), "share_range": (0.3448, "Table 1C"), "share_other": (0.1022, "Table 1C"),
    "n_lower": (7770, "Table 3 N, lower spreads"), "n_higher": (9570, "Table 3 N, higher spreads"),
}
# Footnote robustness that comes with numbers (fn 19); the others (fn 17, 18, 23) are "robust" without numbers
ROBUST = {"ind_x_year_FE": (0.800, "**"), "state_x_year_FE": (0.968, "***")}
