# Rabi drought v2 - 15-day district soil-deficit forecast

Target: mean district deficit area over (t, t+15] >= 0.5. Inputs <= t-8 d. Train 1990-2006, validation 2007-13 (reported; thresholds and selection by leave-one-season-out within training, amendment A1), evaluation 2014-22 (whole seasons). Rows are correlated issue dates of 3 districts. Model selection by LOSO training F1 among operational models: **Logistic regression (soil)**.

## Evaluation rows

| model | subset | threshold | loso_train_f1 | loso_train_pr_auc | validation_positives | n | positives | warnings | precision | recall | f1 | pr_auc | roc_auc | brier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Persistence (area last 15 d >= 0.5) | all | 0.5 | 0.844 |  | 0 | 675 | 52 | 52 | 0.538 | 0.538 | 0.538 |  |  |  |
| Persistence (area last 15 d >= 0.5) | new onset | 0.5 | 0.844 |  | 0 | 623 | 24 | 0 |  | 0.0 | 0.0 |  |  |  |
| Climatology (district x calendar) | all | 0.125 | 0.343 | 0.141 | 0 | 675 | 52 | 675 | 0.077 | 1.0 | 0.143 | 0.095 | 0.53 | 0.088 |
| Climatology (district x calendar) | new onset | 0.125 | 0.343 | 0.141 | 0 | 623 | 24 | 623 | 0.039 | 1.0 | 0.074 | 0.059 | 0.555 | 0.066 |
| Conditional transition | all | 0.202 | 0.845 | 0.786 | 0 | 675 | 52 | 84 | 0.476 | 0.769 | 0.588 | 0.417 | 0.83 | 0.062 |
| Conditional transition | new onset | 0.202 | 0.845 | 0.786 | 0 | 623 | 24 | 32 | 0.375 | 0.5 | 0.429 | 0.18 | 0.688 | 0.039 |
| Logistic regression (soil) | all | 0.618 | 0.885 | 0.896 | 0 | 675 | 52 | 92 | 0.489 | 0.865 | 0.625 | 0.515 | 0.958 | 0.063 |
| Logistic regression (soil) | new onset | 0.618 | 0.885 | 0.896 | 0 | 623 | 24 | 44 | 0.409 | 0.75 | 0.529 | 0.447 | 0.969 | 0.038 |
| XGBoost (soil) | all | 0.361 | 0.874 | 0.916 | 0 | 675 | 52 | 104 | 0.471 | 0.942 | 0.628 | 0.545 | 0.962 | 0.065 |
| XGBoost (soil) | new onset | 0.361 | 0.874 | 0.916 | 0 | 623 | 24 | 57 | 0.404 | 0.958 | 0.568 | 0.572 | 0.978 | 0.042 |
| Logistic regression (weather) | all | 0.754 | 0.717 | 0.736 | 0 | 675 | 52 | 66 | 0.439 | 0.558 | 0.492 | 0.484 | 0.94 | 0.078 |
| Logistic regression (weather) | new onset | 0.754 | 0.717 | 0.736 | 0 | 623 | 24 | 30 | 0.333 | 0.417 | 0.37 | 0.309 | 0.946 | 0.056 |
| XGBoost (weather) | all | 0.122 | 0.75 | 0.733 | 0 | 675 | 52 | 26 | 0.577 | 0.288 | 0.385 | 0.497 | 0.917 | 0.066 |
| XGBoost (weather) | new onset | 0.122 | 0.75 | 0.733 | 0 | 623 | 24 | 12 | 0.583 | 0.292 | 0.389 | 0.36 | 0.918 | 0.034 |
| Logistic regression (combined) | all | 0.507 | 0.882 | 0.868 | 0 | 675 | 52 | 61 | 0.443 | 0.519 | 0.478 | 0.545 | 0.955 | 0.049 |
| Logistic regression (combined) | new onset | 0.507 | 0.882 | 0.868 | 0 | 623 | 24 | 24 | 0.333 | 0.333 | 0.333 | 0.408 | 0.968 | 0.028 |
| XGBoost (combined) | all | 0.198 | 0.861 | 0.911 | 0 | 675 | 52 | 84 | 0.524 | 0.846 | 0.647 | 0.599 | 0.965 | 0.046 |
| XGBoost (combined) | new onset | 0.198 | 0.861 | 0.911 | 0 | 623 | 24 | 44 | 0.455 | 0.833 | 0.588 | 0.551 | 0.976 | 0.026 |
| ORACLE: XGBoost soil + future rain (not operational) | all | 0.349 | 0.875 | 0.93 | 0 | 675 | 52 | 95 | 0.516 | 0.942 | 0.667 | 0.583 | 0.969 | 0.048 |
| ORACLE: XGBoost soil + future rain (not operational) | new onset | 0.349 | 0.875 | 0.93 | 0 | 623 | 24 | 50 | 0.44 | 0.917 | 0.595 | 0.5 | 0.979 | 0.032 |

## District-season events (evaluation)

| model | deficit_district_seasons | caught | warned_district_seasons | warned_with_correct | district_seasons |
|---|---|---|---|---|---|
| Persistence (area last 15 d >= 0.5) | 5 | 4 | 5 | 4 | 27 |
| Climatology (district x calendar) | 5 | 5 | 27 | 5 | 27 |
| Conditional transition | 5 | 5 | 5 | 5 | 27 |
| Logistic regression (soil) | 5 | 5 | 5 | 5 | 27 |
| XGBoost (soil) | 5 | 5 | 5 | 5 | 27 |
| Logistic regression (weather) | 5 | 3 | 3 | 3 | 27 |
| XGBoost (weather) | 5 | 2 | 2 | 2 | 27 |
| Logistic regression (combined) | 5 | 5 | 5 | 5 | 27 |
| XGBoost (combined) | 5 | 5 | 5 | 5 | 27 |
| ORACLE: XGBoost soil + future rain (not operational) | 5 | 5 | 5 | 5 | 27 |

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
