# Earlier chronological drought stress check

**Post hoc diagnostic:** chosen after viewing the seasonal prevalence table. This is historical development evidence, not a fresh test. Main production-candidate models are unchanged.

Train 2001-2013; validate 2014-2016; evaluate 2017-2019. Same fixed 1981-2000 reference. Five regional cells. Only 2018 contains drought targets in this evaluation, so apparent sample size overstates independent drought events.

## Selected models

| horizon | model | scope | n | drought_cases | drought_ap | drought_auc | precision | recall | warnings |
|---|---|---|---|---|---|---|---|---|---|
| 7 | Logistic soil | all | 375 | 35 | 0.788 | 0.969 | 0.578 | 0.743 | 45 |
| 7 | Logistic soil | new_onset | 337 | 6 | 0.152 | 0.937 | 0.071 | 0.167 | 14 |
| 15 | HGB leaves7 soil+weather | all | 375 | 30 | 0.641 | 0.956 | 0.510 | 0.833 | 49 |
| 15 | HGB leaves7 soil+weather | new_onset | 337 | 8 | 0.168 | 0.919 | 0.214 | 0.375 | 14 |
| 30 | HGB leaves7 soil | all | 375 | 29 | 0.363 | 0.855 | 0.217 | 0.517 | 69 |
| 30 | HGB leaves7 soil | new_onset | 337 | 15 | 0.113 | 0.822 | 0.088 | 0.200 | 34 |

## Baselines

| horizon | model | scope | n | drought_cases | drought_ap | drought_auc | precision | recall | warnings |
|---|---|---|---|---|---|---|---|---|---|
| 7 | Percentile persistence | all | 375 | 35 | 0.575 | 0.894 | 0.674 | 0.829 | 43 |
| 7 | Percentile persistence | new_onset | 337 | 6 | 0.036 | 0.573 | 0.125 | 0.167 | 8 |
| 7 | Conditional transition | all | 375 | 35 | 0.747 | 0.970 | 0.633 | 0.886 | 49 |
| 7 | Conditional transition | new_onset | 337 | 6 | 0.226 | 0.906 | 0.214 | 0.500 | 14 |
| 7 | Soil analog k25 | all | 375 | 35 | 0.828 | 0.978 | 0.667 | 0.857 | 45 |
| 7 | Soil analog k25 | new_onset | 337 | 6 | 0.209 | 0.953 | 0.182 | 0.333 | 11 |
| 15 | Percentile persistence | all | 375 | 30 | 0.429 | 0.854 | 0.535 | 0.767 | 43 |
| 15 | Percentile persistence | new_onset | 337 | 8 | 0.080 | 0.616 | 0.250 | 0.250 | 8 |
| 15 | Conditional transition | all | 375 | 30 | 0.654 | 0.971 | 0.519 | 0.900 | 52 |
| 15 | Conditional transition | new_onset | 337 | 8 | 0.443 | 0.978 | 0.353 | 0.750 | 17 |
| 15 | Soil analog k25 | all | 375 | 30 | 0.589 | 0.950 | 0.438 | 0.700 | 48 |
| 15 | Soil analog k25 | new_onset | 337 | 8 | 0.243 | 0.927 | 0.118 | 0.250 | 17 |
| 30 | Percentile persistence | all | 375 | 29 | 0.178 | 0.681 | 0.302 | 0.448 | 43 |
| 30 | Percentile persistence | new_onset | 337 | 15 | 0.045 | 0.488 | 0.000 | 0.000 | 8 |
| 30 | Conditional transition | all | 375 | 29 | 0.388 | 0.900 | 0.325 | 0.862 | 77 |
| 30 | Conditional transition | new_onset | 337 | 15 | 0.272 | 0.916 | 0.286 | 0.800 | 42 |
| 30 | Soil analog k25 | all | 375 | 29 | 0.255 | 0.810 | 0.194 | 0.690 | 103 |
| 30 | Soil analog k25 | new_onset | 337 | 15 | 0.088 | 0.730 | 0.092 | 0.400 | 65 |

## All candidates

| horizon | model | scope | n | drought_cases | drought_ap | drought_auc | precision | recall | warnings |
|---|---|---|---|---|---|---|---|---|---|
| 7 | Percentile persistence | all | 375 | 35 | 0.575 | 0.894 | 0.674 | 0.829 | 43 |
| 7 | Percentile persistence | new_onset | 337 | 6 | 0.036 | 0.573 | 0.125 | 0.167 | 8 |
| 7 | Seasonal climatology | all | 375 | 35 | 0.214 | 0.783 | 0.200 | 0.943 | 165 |
| 7 | Seasonal climatology | new_onset | 337 | 6 | 0.028 | 0.564 | 0.031 | 0.667 | 130 |
| 7 | Conditional transition | all | 375 | 35 | 0.747 | 0.970 | 0.633 | 0.886 | 49 |
| 7 | Conditional transition | new_onset | 337 | 6 | 0.226 | 0.906 | 0.214 | 0.500 | 14 |
| 7 | Damped trend | all | 375 | 35 | 0.542 | 0.867 | 0.675 | 0.771 | 40 |
| 7 | Damped trend | new_onset | 337 | 6 | 0.018 | 0.491 | 0.000 | 0.000 | 6 |
| 7 | Logistic soil | all | 375 | 35 | 0.788 | 0.969 | 0.578 | 0.743 | 45 |
| 7 | Logistic soil | new_onset | 337 | 6 | 0.152 | 0.937 | 0.071 | 0.167 | 14 |
| 7 | RF leaf5 soil | all | 375 | 35 | 0.801 | 0.977 | 0.737 | 0.800 | 38 |
| 7 | RF leaf5 soil | new_onset | 337 | 6 | 0.189 | 0.942 | 0.167 | 0.167 | 6 |
| 7 | RF leaf15 soil | all | 375 | 35 | 0.844 | 0.980 | 0.714 | 0.857 | 42 |
| 7 | RF leaf15 soil | new_onset | 337 | 6 | 0.170 | 0.947 | 0.222 | 0.333 | 9 |
| 7 | HGB leaves7 soil | all | 375 | 35 | 0.894 | 0.985 | 0.744 | 0.829 | 39 |
| 7 | HGB leaves7 soil | new_onset | 337 | 6 | 0.254 | 0.958 | 0.250 | 0.333 | 8 |
| 7 | HGB leaves15 soil | all | 375 | 35 | 0.869 | 0.982 | 0.744 | 0.829 | 39 |
| 7 | HGB leaves15 soil | new_onset | 337 | 6 | 0.248 | 0.947 | 0.250 | 0.333 | 8 |
| 7 | Logistic soil+weather | all | 375 | 35 | 0.678 | 0.943 | 0.531 | 0.743 | 49 |
| 7 | Logistic soil+weather | new_onset | 337 | 6 | 0.101 | 0.899 | 0.143 | 0.500 | 21 |
| 7 | RF leaf5 soil+weather | all | 375 | 35 | 0.676 | 0.964 | 0.690 | 0.829 | 42 |
| 7 | RF leaf5 soil+weather | new_onset | 337 | 6 | 0.140 | 0.901 | 0.200 | 0.333 | 10 |
| 7 | RF leaf15 soil+weather | all | 375 | 35 | 0.684 | 0.964 | 0.707 | 0.829 | 41 |
| 7 | RF leaf15 soil+weather | new_onset | 337 | 6 | 0.141 | 0.913 | 0.222 | 0.333 | 9 |
| 7 | HGB leaves7 soil+weather | all | 375 | 35 | 0.811 | 0.977 | 0.644 | 0.829 | 45 |
| 7 | HGB leaves7 soil+weather | new_onset | 337 | 6 | 0.172 | 0.943 | 0.091 | 0.167 | 11 |
| 7 | HGB leaves15 soil+weather | all | 375 | 35 | 0.801 | 0.977 | 0.800 | 0.800 | 35 |
| 7 | HGB leaves15 soil+weather | new_onset | 337 | 6 | 0.178 | 0.945 | 0.250 | 0.167 | 4 |
| 7 | Soil analog k25 | all | 375 | 35 | 0.828 | 0.978 | 0.667 | 0.857 | 45 |
| 7 | Soil analog k25 | new_onset | 337 | 6 | 0.209 | 0.953 | 0.182 | 0.333 | 11 |
| 7 | Equal learned ensemble | all | 375 | 35 | 0.832 | 0.981 | 0.725 | 0.829 | 40 |
| 7 | Equal learned ensemble | new_onset | 337 | 6 | 0.209 | 0.954 | 0.143 | 0.167 | 7 |
| 15 | Percentile persistence | all | 375 | 30 | 0.429 | 0.854 | 0.535 | 0.767 | 43 |
| 15 | Percentile persistence | new_onset | 337 | 8 | 0.080 | 0.616 | 0.250 | 0.250 | 8 |
| 15 | Seasonal climatology | all | 375 | 30 | 0.189 | 0.745 | 0.080 | 1.000 | 375 |
| 15 | Seasonal climatology | new_onset | 337 | 8 | 0.032 | 0.457 | 0.024 | 1.000 | 337 |
| 15 | Conditional transition | all | 375 | 30 | 0.654 | 0.971 | 0.519 | 0.900 | 52 |
| 15 | Conditional transition | new_onset | 337 | 8 | 0.443 | 0.978 | 0.353 | 0.750 | 17 |
| 15 | Damped trend | all | 375 | 30 | 0.337 | 0.800 | 0.465 | 0.667 | 43 |
| 15 | Damped trend | new_onset | 337 | 8 | 0.032 | 0.547 | 0.091 | 0.125 | 11 |
| 15 | Logistic soil | all | 375 | 30 | 0.669 | 0.952 | 0.385 | 0.833 | 65 |
| 15 | Logistic soil | new_onset | 337 | 8 | 0.174 | 0.932 | 0.103 | 0.375 | 29 |
| 15 | RF leaf5 soil | all | 375 | 30 | 0.658 | 0.970 | 0.591 | 0.867 | 44 |
| 15 | RF leaf5 soil | new_onset | 337 | 8 | 0.326 | 0.969 | 0.455 | 0.625 | 11 |
| 15 | RF leaf15 soil | all | 375 | 30 | 0.588 | 0.963 | 0.523 | 0.767 | 44 |
| 15 | RF leaf15 soil | new_onset | 337 | 8 | 0.261 | 0.952 | 0.182 | 0.250 | 11 |
| 15 | HGB leaves7 soil | all | 375 | 30 | 0.691 | 0.966 | 0.585 | 0.800 | 41 |
| 15 | HGB leaves7 soil | new_onset | 337 | 8 | 0.290 | 0.939 | 0.273 | 0.375 | 11 |
| 15 | HGB leaves15 soil | all | 375 | 30 | 0.630 | 0.962 | 0.556 | 0.833 | 45 |
| 15 | HGB leaves15 soil | new_onset | 337 | 8 | 0.239 | 0.926 | 0.214 | 0.375 | 14 |
| 15 | Logistic soil+weather | all | 375 | 30 | 0.453 | 0.924 | 0.320 | 0.800 | 75 |
| 15 | Logistic soil+weather | new_onset | 337 | 8 | 0.102 | 0.880 | 0.079 | 0.375 | 38 |
| 15 | RF leaf5 soil+weather | all | 375 | 30 | 0.498 | 0.952 | 0.523 | 0.767 | 44 |
| 15 | RF leaf5 soil+weather | new_onset | 337 | 8 | 0.225 | 0.944 | 0.182 | 0.250 | 11 |
| 15 | RF leaf15 soil+weather | all | 375 | 30 | 0.478 | 0.951 | 0.441 | 0.867 | 59 |
| 15 | RF leaf15 soil+weather | new_onset | 337 | 8 | 0.232 | 0.946 | 0.208 | 0.625 | 24 |
| 15 | HGB leaves7 soil+weather | all | 375 | 30 | 0.641 | 0.956 | 0.510 | 0.833 | 49 |
| 15 | HGB leaves7 soil+weather | new_onset | 337 | 8 | 0.168 | 0.919 | 0.214 | 0.375 | 14 |
| 15 | HGB leaves15 soil+weather | all | 375 | 30 | 0.612 | 0.956 | 0.564 | 0.733 | 39 |
| 15 | HGB leaves15 soil+weather | new_onset | 337 | 8 | 0.163 | 0.923 | 0.182 | 0.250 | 11 |
| 15 | Soil analog k25 | all | 375 | 30 | 0.589 | 0.950 | 0.438 | 0.700 | 48 |
| 15 | Soil analog k25 | new_onset | 337 | 8 | 0.243 | 0.927 | 0.118 | 0.250 | 17 |
| 15 | Equal learned ensemble | all | 375 | 30 | 0.597 | 0.963 | 0.491 | 0.867 | 53 |
| 15 | Equal learned ensemble | new_onset | 337 | 8 | 0.241 | 0.946 | 0.211 | 0.500 | 19 |
| 30 | Percentile persistence | all | 375 | 29 | 0.178 | 0.681 | 0.302 | 0.448 | 43 |
| 30 | Percentile persistence | new_onset | 337 | 15 | 0.045 | 0.488 | 0.000 | 0.000 | 8 |
| 30 | Seasonal climatology | all | 375 | 29 | 0.107 | 0.499 | 0.077 | 1.000 | 375 |
| 30 | Seasonal climatology | new_onset | 337 | 15 | 0.042 | 0.162 | 0.045 | 1.000 | 337 |
| 30 | Conditional transition | all | 375 | 29 | 0.388 | 0.900 | 0.325 | 0.862 | 77 |
| 30 | Conditional transition | new_onset | 337 | 15 | 0.272 | 0.916 | 0.286 | 0.800 | 42 |
| 30 | Damped trend | all | 375 | 29 | 0.240 | 0.748 | 0.354 | 0.586 | 48 |
| 30 | Damped trend | new_onset | 337 | 15 | 0.092 | 0.612 | 0.222 | 0.267 | 18 |
| 30 | Logistic soil | all | 375 | 29 | 0.337 | 0.858 | 0.225 | 0.862 | 111 |
| 30 | Logistic soil | new_onset | 337 | 15 | 0.118 | 0.830 | 0.151 | 0.733 | 73 |
| 30 | RF leaf5 soil | all | 375 | 29 | 0.321 | 0.884 | 0.293 | 0.414 | 41 |
| 30 | RF leaf5 soil | new_onset | 337 | 15 | 0.181 | 0.873 | 0.154 | 0.133 | 13 |
| 30 | RF leaf15 soil | all | 375 | 29 | 0.369 | 0.891 | 0.278 | 0.517 | 54 |
| 30 | RF leaf15 soil | new_onset | 337 | 15 | 0.190 | 0.881 | 0.105 | 0.133 | 19 |
| 30 | HGB leaves7 soil | all | 375 | 29 | 0.363 | 0.855 | 0.217 | 0.517 | 69 |
| 30 | HGB leaves7 soil | new_onset | 337 | 15 | 0.113 | 0.822 | 0.088 | 0.200 | 34 |
| 30 | HGB leaves15 soil | all | 375 | 29 | 0.368 | 0.860 | 0.227 | 0.586 | 75 |
| 30 | HGB leaves15 soil | new_onset | 337 | 15 | 0.119 | 0.828 | 0.079 | 0.200 | 38 |
| 30 | Logistic soil+weather | all | 375 | 29 | 0.260 | 0.836 | 0.167 | 0.517 | 90 |
| 30 | Logistic soil+weather | new_onset | 337 | 15 | 0.100 | 0.790 | 0.019 | 0.067 | 52 |
| 30 | RF leaf5 soil+weather | all | 375 | 29 | 0.301 | 0.871 | 0.257 | 0.655 | 74 |
| 30 | RF leaf5 soil+weather | new_onset | 337 | 15 | 0.140 | 0.845 | 0.158 | 0.400 | 38 |
| 30 | RF leaf15 soil+weather | all | 375 | 29 | 0.315 | 0.878 | 0.277 | 0.621 | 65 |
| 30 | RF leaf15 soil+weather | new_onset | 337 | 15 | 0.163 | 0.856 | 0.172 | 0.333 | 29 |
| 30 | HGB leaves7 soil+weather | all | 375 | 29 | 0.456 | 0.874 | 0.221 | 0.655 | 86 |
| 30 | HGB leaves7 soil+weather | new_onset | 337 | 15 | 0.125 | 0.834 | 0.104 | 0.333 | 48 |
| 30 | HGB leaves15 soil+weather | all | 375 | 29 | 0.424 | 0.874 | 0.228 | 0.724 | 92 |
| 30 | HGB leaves15 soil+weather | new_onset | 337 | 15 | 0.122 | 0.837 | 0.127 | 0.467 | 55 |
| 30 | Soil analog k25 | all | 375 | 29 | 0.255 | 0.810 | 0.194 | 0.690 | 103 |
| 30 | Soil analog k25 | new_onset | 337 | 15 | 0.088 | 0.730 | 0.092 | 0.400 | 65 |
| 30 | Equal learned ensemble | all | 375 | 29 | 0.316 | 0.868 | 0.218 | 0.655 | 87 |
| 30 | Equal learned ensemble | new_onset | 337 | 15 | 0.124 | 0.841 | 0.102 | 0.333 | 49 |

Deterministic baseline thresholds are 0.5. Learned models and validation selection are unchanged. New-onset truth is used only for scoring. These are repeated cell-dates and modelled soil targets, not independent field drought cases.
