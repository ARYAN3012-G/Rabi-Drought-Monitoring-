# Rabi early-drying risk model v1 - results

Rules: `docs/DETECT_v1.md` (fixed before the run). Train 2019-20..2021-22, validation 2022-23 (thresholds, ensemble weights), evaluation 2023-24..2025-26 - historical seasons already consulted during development, never used for fitting or choices here. Target = satellite-defined early drying (>= 21 days before the point's normal drying date), not field-verified drought.

## All eligible forecasts (mean over 5 seeds)

| horizon | model | n | positives | accuracy | balanced_accuracy | precision | recall | f1 | roc_auc | pr_auc |
|---|---|---|---|---|---|---|---|---|---|---|
| 7 | Logistic regression | 12030.0 | 2554.0 | 0.962 | 0.946 | 0.906 | 0.918 | 0.912 | 0.984 | 0.969 |
| 7 | Random forest | 12030.0 | 2554.0 | 0.959 | 0.951 | 0.88 | 0.938 | 0.907 | 0.99 | 0.979 |
| 7 | XGBoost | 12030.0 | 2554.0 | 0.955 | 0.949 | 0.862 | 0.939 | 0.898 | 0.991 | 0.978 |
| 7 | Ensemble (equal) | 12030.0 | 2554.0 | 0.963 | 0.951 | 0.898 | 0.931 | 0.914 | 0.99 | 0.978 |
| 7 | Ensemble (validation-weighted) | 12030.0 | 2554.0 | 0.963 | 0.951 | 0.899 | 0.931 | 0.915 | 0.99 | 0.978 |
| 7 | B: persistence (dried early already) | 12030.0 | 2554.0 | 0.98 | 0.954 | 1.0 | 0.908 | 0.952 | 0.954 | 0.927 |
| 7 | B: greenness below normal | 12030.0 | 2554.0 | 0.686 | 0.682 | 0.369 | 0.676 | 0.477 | 0.759 | 0.516 |
| 7 | B: drop from peak | 12030.0 | 2554.0 | 0.634 | 0.738 | 0.359 | 0.918 | 0.516 | 0.794 | 0.415 |
| 7 | B: early-drying rule | 12030.0 | 2554.0 | 0.803 | 0.581 | 0.617 | 0.196 | 0.297 | 0.581 | 0.291 |
| 15 | Logistic regression | 12030.0 | 2790.0 | 0.94 | 0.911 | 0.88 | 0.858 | 0.869 | 0.972 | 0.947 |
| 15 | Random forest | 12030.0 | 2790.0 | 0.941 | 0.928 | 0.854 | 0.904 | 0.878 | 0.983 | 0.964 |
| 15 | XGBoost | 12030.0 | 2790.0 | 0.948 | 0.922 | 0.901 | 0.874 | 0.887 | 0.982 | 0.961 |
| 15 | Ensemble (equal) | 12030.0 | 2790.0 | 0.944 | 0.924 | 0.874 | 0.887 | 0.88 | 0.981 | 0.961 |
| 15 | Ensemble (validation-weighted) | 12030.0 | 2790.0 | 0.945 | 0.924 | 0.876 | 0.887 | 0.881 | 0.981 | 0.961 |
| 15 | B: persistence (dried early already) | 12030.0 | 2790.0 | 0.961 | 0.915 | 1.0 | 0.831 | 0.908 | 0.915 | 0.87 |
| 15 | B: greenness below normal | 12030.0 | 2790.0 | 0.696 | 0.666 | 0.398 | 0.61 | 0.482 | 0.73 | 0.507 |
| 15 | B: drop from peak | 12030.0 | 2790.0 | 0.617 | 0.704 | 0.363 | 0.866 | 0.512 | 0.755 | 0.408 |
| 15 | B: early-drying rule | 12030.0 | 2790.0 | 0.774 | 0.547 | 0.559 | 0.124 | 0.203 | 0.547 | 0.273 |
| 30 | Logistic regression | 12030.0 | 3169.0 | 0.876 | 0.88 | 0.712 | 0.888 | 0.79 | 0.961 | 0.929 |
| 30 | Random forest | 12030.0 | 3169.0 | 0.915 | 0.9 | 0.819 | 0.87 | 0.843 | 0.974 | 0.947 |
| 30 | XGBoost | 12030.0 | 3169.0 | 0.897 | 0.891 | 0.768 | 0.878 | 0.818 | 0.97 | 0.94 |
| 30 | Ensemble (equal) | 12030.0 | 3169.0 | 0.898 | 0.9 | 0.756 | 0.905 | 0.824 | 0.972 | 0.944 |
| 30 | Ensemble (validation-weighted) | 12030.0 | 3169.0 | 0.9 | 0.9 | 0.764 | 0.899 | 0.826 | 0.972 | 0.944 |
| 30 | B: persistence (dried early already) | 12030.0 | 3169.0 | 0.929 | 0.866 | 1.0 | 0.731 | 0.845 | 0.866 | 0.802 |
| 30 | B: greenness below normal | 12030.0 | 3169.0 | 0.672 | 0.634 | 0.409 | 0.553 | 0.47 | 0.684 | 0.495 |
| 30 | B: drop from peak | 12030.0 | 3169.0 | 0.586 | 0.649 | 0.366 | 0.784 | 0.499 | 0.692 | 0.397 |
| 30 | B: early-drying rule | 12030.0 | 3169.0 | 0.733 | 0.515 | 0.447 | 0.053 | 0.095 | 0.515 | 0.273 |

## New onsets only (crop not yet dried at the issue date)

| horizon | model | n | positives | accuracy | balanced_accuracy | precision | recall | f1 | roc_auc | pr_auc |
|---|---|---|---|---|---|---|---|---|---|---|
| 7 | Logistic regression | 9712.0 | 236.0 | 0.953 | 0.544 | 0.1 | 0.114 | 0.107 | 0.831 | 0.085 |
| 7 | Random forest | 9712.0 | 236.0 | 0.949 | 0.645 | 0.186 | 0.326 | 0.218 | 0.894 | 0.165 |
| 7 | XGBoost | 9712.0 | 236.0 | 0.944 | 0.65 | 0.174 | 0.341 | 0.227 | 0.898 | 0.158 |
| 7 | Ensemble (equal) | 9712.0 | 236.0 | 0.954 | 0.612 | 0.181 | 0.253 | 0.209 | 0.895 | 0.15 |
| 7 | Ensemble (validation-weighted) | 9712.0 | 236.0 | 0.954 | 0.615 | 0.185 | 0.258 | 0.214 | 0.896 | 0.15 |
| 7 | B: persistence (dried early already) | 9712.0 | 236.0 |  |  |  |  |  | 0.5 |  |
| 7 | B: greenness below normal | 9712.0 | 236.0 | 0.677 | 0.463 | 0.019 | 0.237 | 0.034 | 0.468 | 0.022 |
| 7 | B: drop from peak | 9712.0 | 236.0 | 0.555 | 0.512 | 0.026 | 0.466 | 0.048 | 0.504 | 0.022 |
| 7 | B: early-drying rule | 9712.0 | 236.0 | 0.944 | 0.486 | 0.003 | 0.004 | 0.004 | 0.486 | 0.024 |
| 15 | Logistic regression | 9712.0 | 472.0 | 0.926 | 0.563 | 0.189 | 0.161 | 0.174 | 0.836 | 0.166 |
| 15 | Random forest | 9712.0 | 472.0 | 0.927 | 0.691 | 0.321 | 0.43 | 0.364 | 0.899 | 0.296 |
| 15 | XGBoost | 9712.0 | 472.0 | 0.936 | 0.614 | 0.309 | 0.257 | 0.273 | 0.894 | 0.255 |
| 15 | Ensemble (equal) | 9712.0 | 472.0 | 0.931 | 0.647 | 0.306 | 0.332 | 0.316 | 0.89 | 0.262 |
| 15 | Ensemble (validation-weighted) | 9712.0 | 472.0 | 0.931 | 0.646 | 0.309 | 0.33 | 0.317 | 0.891 | 0.263 |
| 15 | B: persistence (dried early already) | 9712.0 | 472.0 |  |  |  |  |  | 0.5 |  |
| 15 | B: greenness below normal | 9712.0 | 472.0 | 0.696 | 0.463 | 0.036 | 0.206 | 0.062 | 0.45 | 0.041 |
| 15 | B: drop from peak | 9712.0 | 472.0 | 0.534 | 0.457 | 0.04 | 0.373 | 0.072 | 0.441 | 0.039 |
| 15 | B: early-drying rule | 9712.0 | 472.0 | 0.923 | 0.487 | 0.007 | 0.004 | 0.005 | 0.487 | 0.048 |
| 30 | Logistic regression | 9712.0 | 851.0 | 0.846 | 0.727 | 0.303 | 0.582 | 0.399 | 0.856 | 0.293 |
| 30 | Random forest | 9712.0 | 851.0 | 0.895 | 0.723 | 0.418 | 0.515 | 0.461 | 0.904 | 0.425 |
| 30 | XGBoost | 9712.0 | 851.0 | 0.872 | 0.724 | 0.354 | 0.544 | 0.424 | 0.89 | 0.353 |
| 30 | Ensemble (equal) | 9712.0 | 851.0 | 0.873 | 0.772 | 0.373 | 0.648 | 0.473 | 0.897 | 0.39 |
| 30 | Ensemble (validation-weighted) | 9712.0 | 851.0 | 0.876 | 0.763 | 0.377 | 0.626 | 0.47 | 0.897 | 0.39 |
| 30 | B: persistence (dried early already) | 9712.0 | 851.0 |  |  |  |  |  | 0.5 |  |
| 30 | B: greenness below normal | 9712.0 | 851.0 | 0.667 | 0.443 | 0.054 | 0.17 | 0.082 | 0.413 | 0.069 |
| 30 | B: drop from peak | 9712.0 | 851.0 | 0.494 | 0.396 | 0.052 | 0.277 | 0.088 | 0.367 | 0.065 |
| 30 | B: early-drying rule | 9712.0 | 851.0 | 0.891 | 0.491 | 0.019 | 0.005 | 0.008 | 0.491 | 0.087 |

## Notes

- 7 d: validation PR-AUC LR 0.956, RF 0.970, XGB 0.970 -> weights 0.33, 0.33, 0.34
- 7 d, new onsets: AUC(weighted ensemble) - AUC(b_drop) 95% CI over points [+0.350, +0.429]
- 7 d: correctly warned new onsets 62 of 236; lead time before drying median 3 d (IQR 3-6)
- 15 d: validation PR-AUC LR 0.898, RF 0.942, XGB 0.945 -> weights 0.32, 0.34, 0.34
- 15 d, new onsets: AUC(weighted ensemble) - AUC(b_drop) 95% CI over points [+0.410, +0.486]
- 15 d: correctly warned new onsets 113 of 472; lead time before drying median 7 d (IQR 3-11)
- 30 d: validation PR-AUC LR 0.853, RF 0.907, XGB 0.905 -> weights 0.32, 0.34, 0.34
- 30 d, new onsets: AUC(weighted ensemble) - AUC(b_drop) 95% CI over points [+0.493, +0.566]
- 30 d: correctly warned new onsets 566 of 851; lead time before drying median 13 d (IQR 7-21)

## Drought check

Cell-season early-drying rate vs June-November rain ratio: Spearman -0.40 (n = 33); rate when rain < 80 % of normal 0.40 vs 0.22 otherwise.
