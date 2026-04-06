# Evaluation Summary

- Model: `gpt-4o`
- Cases: `6`
- Normalized cost formula: `$0.01 / 1K tokens`

## Scoreboard

| Mode | Success Rate | Avg Latency (ms) | P50 (ms) | P99 (ms) | Avg Tokens | Total Normalized Cost | Avg Steps | Tool Calls |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 16.67% | 2717.39 | 2380.07 | 4359.31 | 230.83 | $0.0138 | 1 | 0 |
| agent_v1 | 66.67% | 3264.79 | 3411.73 | 3797.09 | 1163.33 | $0.0698 | 1.67 | 4 |
| agent_v2 | 100.0% | 2899.15 | 2789.23 | 3663.68 | 1882.17 | $0.1129 | 1.83 | 5 |

## Case Breakdown

| Case | Baseline | Agent v1 | Agent v2 |
| :--- | :---: | :---: | :---: |
| Case 1 | Fail | Pass | Pass |
| Case 2 | Fail | Pass | Pass |
| Case 3 | Fail | Pass | Pass |
| Case 4 | Fail | Fail | Pass |
| Case 5 | Fail | Fail | Pass |
| Case 6 | Pass | Pass | Pass |
