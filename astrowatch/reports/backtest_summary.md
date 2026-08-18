# Astrowatch Event Backtest Summary

Generated: 2026-08-17T18:16:19.101929+00:00  
Dataset: `cricket-wc-finals-v1`  
Model variant: `complete`

## Scientific status (read first)

This report measures the predictive performance of THIS PROJECT'S IMPLEMENTED ALGORITHM under its stated assumptions, on a very small (n=6) real historical dataset. It does NOT prove or disprove astrology scientifically, and no number below should be read as such -- see BACKTEST.md.

## Overview

- Total events in dataset: 6
- Completed (status=OK): 6
- Excluded / INSUFFICIENT_DATA / DATA_UNAVAILABLE: 0

## Metrics (real, computed)

- Top-1 accuracy: 0.3333333333333333
- Mean Brier score: 0.6407565860116669
- Mean multiclass log loss: 0.8378050975756755
- Mean reciprocal rank: 0.6666666666666666
- Mean predicted rank of actual winner: 1.6666666666666667

## Calibration

- Claimable: False
- Calibration is NOT claimed to be demonstrated -- this dataset has only 6 completed predictions, far below the 30-sample threshold this project requires before making any calibration-quality claim (see build spec Section 12).

| Confidence bin | n | mean predicted confidence | actual success rate |
|---|---|---|---|
| 0%-20% | 0 | None | None |
| 20%-40% | 0 | None | None |
| 40%-60% | 3 | 0.5142886420491427 | 0.6666666666666666 |
| 60%-80% | 3 | 0.6307963414051555 | 0.0 |
| 80%-100% | 0 | None | None |

## All predictions

| Event | Status | Predicted | Actual | Correct | Brier | Log loss | Rank of actual |
|---|---|---|---|---|---|---|---|
| 2003 ICC Cricket World Cup | OK | australia | australia | True | 0.46227810650887574 | 0.6554068525770982 | 1 |
| 2007 ICC Cricket World Cup | OK | sri_lanka | australia | False | 0.829766750052343 | 1.0331459802365235 | 2 |
| 2011 ICC Cricket World Cup | OK | sri_lanka | india | False | 0.7441161535645542 | 0.9415204302500352 | 2 |
| 2015 ICC Cricket World Cup | OK | australia | australia | True | 0.473199288002848 | 0.666339916328802 | 1 |
| 2019 ICC Cricket World Cup | OK | new_zealand | england | False | 0.8148767003281889 | 1.0169649593409027 | 2 |
| 2023 ICC Cricket World Cup | OK | india | australia | False | 0.5203025176131916 | 0.7134524467206909 | 2 |
