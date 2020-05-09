Column Definitions
Note: the group number betwen baseline measurements and outcome measurements are not necessarily consistent (upon investigation perhaps 10% of them have switched orders)

- Columns from Baseline Measurements
    - g1f: # females in group 1
    - g1m: # males in group 1
    - g1t: g1f + g1m
    - g2f: # females in group 2
    - g2m: # males in group 2
    - g2t: g2f + g2m
    - imbal: np.abs(g1m / g1t - g2m / g2t)
    
- Columns from Outcome Measurements
    - g1_mean: reported mean in group 1
    - g2_mean: reported mean in group 2
    - num_parts1: # participants in group 1
    - num_parts2: # participants in group 2
    - num_measures1: # of measurements taken in group 1 (for example if each eye was measured)
    - num_measures2: # of measurements taken in group 2 (for example if each eye was measured)
    - g1_sd_sample: standard dev of mesurements in group 1
    - g2_sd_sample standard dev of mesurements in group 2
    - effect: 2-sample t-test ((abs diff in mean) / (sd estimator))
