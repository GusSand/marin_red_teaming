# Olmo 3 7B safety reproduction — delta report

Produced = mean over 3 seed runs (0-2). Spread = min-max. Δ = produced - published.
Tolerance 3.0pp. safety-eval @060cc903, temp0.7/top_p0.95. Metrics x100 from fractions.
Targets human-verified (Gate 0). Rows with no metrics.json = NOT RUN.

### Olmo 3 7B Instruct (Table 53, Final Instruct)

| Row | Published | Produced (mean) | Spread | Δ pp | Status |
|---|---|---|---|---|---|
| DoAnythingNow | 75.2 | 77.89 | 77.00-78.33 | +2.69 | PASS (n=3) |
| HarmBench | 94.9 | 93.85 | 93.75-94.06 | -1.05 | PASS (n=3) |
| TrustLLM-JailbreakTrigger | 79.2 | 79.42 | 78.50-80.00 | +0.22 | PASS (n=3) |
| WildJailbreak-Test_Harmful | 69.1 | 69.52 | 68.90-70.00 | +0.42 | PASS (n=3) |
| WildJailbreak-Test_Benign | 98.0 | 95.60 | 95.60-95.60 | -2.40 | PASS (n=3) |
| WildGuard-Test | 99.6 | 99.55 | 99.33-99.87 | -0.05 | PASS (n=3) |
| XSTest | 93.2 | 94.00 | 93.33-94.44 | +0.80 | PASS (n=3) |
| BBQ_Accuracy | 79.0 | 78.78 | 78.49-79.05 | -0.22 | PASS (n=3) |
| BBQ_Bias-Ambig | 8.6 | 9.13 | 8.73-9.84 | +0.53 | PASS (n=3) |
| BBQ_Bias-Disambig | 2.7 | 3.01 | 2.47-3.91 | +0.31 | PASS (n=3) |
| StrongReject | 88.1 | 88.36 | 88.21-88.53 | +0.26 | PASS (n=3) |
| Toxigen | 100.0 | 100.00 | 99.99-100.00 | -0.00 | PASS (n=3) |
| WMDP | 45.5 | 46.55 | 45.50-48.23 | +1.05 | PASS (n=3) |

### Olmo 3 7B Think (Table 52, Final Think)

| Row | Published | Produced (mean) | Spread | Δ pp | Status |
|---|---|---|---|---|---|
| DoAnythingNow | 23.4 | 23.11 | 22.67-23.67 | -0.29 | PASS (n=3) |
| HarmBench | 75.4 | 74.58 | 73.75-76.25 | -0.82 | PASS (n=3) |
| TrustLLM-JailbreakTrigger | 72.0 | 72.33 | 70.75-73.75 | +0.33 | PASS (n=3) |
| WildJailbreak-Test_Harmful | 39.0 | 39.42 | 39.25-39.70 | +0.42 | PASS (n=3) |
| WildJailbreak-Test_Benign | 98.8 | 98.67 | 98.00-99.20 | -0.13 | PASS (n=3) |
| WildGuard-Test | 93.8 | 93.50 | 93.19-94.13 | -0.30 | PASS (n=3) |
| XSTest | 90.9 | 91.11 | 90.89-91.33 | +0.21 | PASS (n=3) |
| BBQ_Accuracy | 89.2 | 88.67 | 88.51-88.96 | -0.53 | PASS (n=3) |
| BBQ_Bias-Ambig | 6.5 | 6.82 | 6.42-7.07 | +0.32 | PASS (n=3) |
| BBQ_Bias-Disambig | 1.7 | 1.94 | 1.61-2.41 | +0.24 | PASS (n=3) |
| StrongReject | 79.0 | NOT RUN |  |  | NOT RUN |
| Toxigen | 100.0 | NOT RUN |  |  | NOT RUN |
| WMDP | 42.7 | 42.92 | 41.83-44.28 | +0.22 | PASS (n=3) |
