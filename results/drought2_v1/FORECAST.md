# Rabi drought v2 - 15-day district soil-deficit forecast

Target: mean district deficit area over (t, t+15] >= 0.5. Inputs <= t-8 d. Train 1990-2006, validation 2007-13 (reported; thresholds and selection by leave-one-season-out within training, amendment A1), evaluation 2014-22 (whole seasons). Rows are correlated issue dates of 3 districts. Model selection by LOSO training F1 among operational models: **Logistic regression (combined)**.

## Evaluation rows

| model | subset | threshold | loso_train_f1 | loso_train_pr_auc | validation_positives | n | positives | warnings | precision | recall | f1 | pr_auc | roc_auc | brier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Persistence (area last 15 d >= 0.5) | all | 0.5 | 0.716 |  | 0 | 675 | 71 | 76 | 0.724 | 0.775 | 0.748 |  |  |  |
| Persistence (area last 15 d >= 0.5) | new onset | 0.5 | 0.716 |  | 0 | 599 | 16 | 0 |  | 0.0 | 0.0 |  |  |  |
| Climatology (district x calendar) | all | 0.062 | 0.286 | 0.124 | 0 | 675 | 71 | 648 | 0.103 | 0.944 | 0.186 | 0.109 | 0.486 | 0.1 |
| Climatology (district x calendar) | new onset | 0.062 | 0.286 | 0.124 | 0 | 599 | 16 | 578 | 0.028 | 1.0 | 0.054 | 0.031 | 0.461 | 0.048 |
| Conditional transition | all | 0.267 | 0.667 | 0.714 | 0 | 675 | 71 | 93 | 0.731 | 0.958 | 0.829 | 0.759 | 0.979 | 0.036 |
| Conditional transition | new onset | 0.267 | 0.667 | 0.714 | 0 | 599 | 16 | 17 | 0.765 | 0.812 | 0.788 | 0.784 | 0.99 | 0.016 |
| Logistic regression (soil) | all | 0.733 | 0.731 | 0.809 | 0 | 675 | 71 | 91 | 0.725 | 0.93 | 0.815 | 0.774 | 0.981 | 0.038 |
| Logistic regression (soil) | new onset | 0.733 | 0.731 | 0.809 | 0 | 599 | 16 | 16 | 0.688 | 0.688 | 0.688 | 0.807 | 0.995 | 0.012 |
| XGBoost (soil) | all | 0.19 | 0.729 | 0.713 | 0 | 675 | 71 | 95 | 0.726 | 0.972 | 0.831 | 0.75 | 0.976 | 0.037 |
| XGBoost (soil) | new onset | 0.19 | 0.729 | 0.713 | 0 | 599 | 16 | 21 | 0.762 | 1.0 | 0.865 | 0.737 | 0.995 | 0.008 |
| Logistic regression (weather) | all | 0.642 | 0.722 | 0.729 | 0 | 675 | 71 | 42 | 0.643 | 0.38 | 0.478 | 0.608 | 0.954 | 0.056 |
| Logistic regression (weather) | new onset | 0.642 | 0.722 | 0.729 | 0 | 599 | 16 | 12 | 0.833 | 0.625 | 0.714 | 0.792 | 0.988 | 0.018 |
| XGBoost (weather) | all | 0.618 | 0.691 | 0.637 | 0 | 675 | 71 | 2 | 1.0 | 0.028 | 0.055 | 0.436 | 0.872 | 0.096 |
| XGBoost (weather) | new onset | 0.618 | 0.691 | 0.637 | 0 | 599 | 16 | 0 |  | 0.0 | 0.0 | 0.653 | 0.951 | 0.023 |
| Logistic regression (combined) | all | 0.778 | 0.762 | 0.787 | 0 | 675 | 71 | 78 | 0.795 | 0.873 | 0.832 | 0.769 | 0.981 | 0.034 |
| Logistic regression (combined) | new onset | 0.778 | 0.762 | 0.787 | 0 | 599 | 16 | 11 | 0.909 | 0.625 | 0.741 | 0.901 | 0.997 | 0.01 |
| XGBoost (combined) | all | 0.312 | 0.725 | 0.742 | 0 | 675 | 71 | 85 | 0.741 | 0.887 | 0.808 | 0.768 | 0.981 | 0.035 |
| XGBoost (combined) | new onset | 0.312 | 0.725 | 0.742 | 0 | 599 | 16 | 13 | 0.769 | 0.625 | 0.69 | 0.754 | 0.995 | 0.013 |
| ORACLE: XGBoost soil + future rain (not operational) | all | 0.104 | 0.737 | 0.785 | 0 | 675 | 71 | 97 | 0.732 | 1.0 | 0.845 | 0.813 | 0.985 | 0.03 |
| ORACLE: XGBoost soil + future rain (not operational) | new onset | 0.104 | 0.737 | 0.785 | 0 | 599 | 16 | 22 | 0.727 | 1.0 | 0.842 | 0.777 | 0.995 | 0.011 |

## District-season events (evaluation)

| model | deficit_district_seasons | caught | warned_district_seasons | warned_with_correct | district_seasons |
|---|---|---|---|---|---|
| Persistence (area last 15 d >= 0.5) | 4 | 4 | 4 | 4 | 27 |
| Climatology (district x calendar) | 4 | 4 | 27 | 4 | 27 |
| Conditional transition | 4 | 4 | 5 | 4 | 27 |
| Logistic regression (soil) | 4 | 4 | 5 | 4 | 27 |
| XGBoost (soil) | 4 | 4 | 4 | 4 | 27 |
| Logistic regression (weather) | 4 | 4 | 4 | 4 | 27 |
| XGBoost (weather) | 4 | 1 | 1 | 1 | 27 |
| Logistic regression (combined) | 4 | 4 | 4 | 4 | 27 |
| XGBoost (combined) | 4 | 4 | 4 | 4 | 27 |
| ORACLE: XGBoost soil + future rain (not operational) | 4 | 4 | 5 | 4 | 27 |

## Coverage

| season | ok |
|---|---|
| 1990 | 75 |
| 1991 | 75 |
| 1992 | 75 |
| 1993 | 75 |
| 1994 | 75 |
| 1995 | 75 |
| 1996 | 75 |
| 1997 | 75 |
| 1998 | 75 |
| 1999 | 75 |
| 2000 | 75 |
| 2001 | 75 |
| 2002 | 75 |
| 2003 | 75 |
| 2004 | 75 |
| 2005 | 75 |
| 2006 | 75 |
| 2007 | 75 |
| 2008 | 75 |
| 2009 | 75 |
| 2010 | 75 |
| 2011 | 75 |
| 2012 | 75 |
| 2013 | 75 |
| 2014 | 75 |
| 2015 | 75 |
| 2016 | 75 |
| 2017 | 75 |
| 2018 | 75 |
| 2019 | 75 |
| 2020 | 75 |
| 2021 | 75 |
| 2022 | 75 |
