# Study v1.5 final results: batch 1 + batch 2 (B3)

## Scope: headline (batch, minus headline exclusions)

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 72.2% [49.1%, 87.5%] | 3.22 | 3.22 | 59.1% [38.7%, 76.7%] | 6.6% [2.8%, 14.5%] | 51.3% [40.3%, 62.2%] | 13.6% [4.7%, 33.3%] | 38.8% [29.7%, 48.7%] | 52.5% [30.7%, 70.6%] | 4.67e-07 |
| claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 88.0% [70.0%, 95.8%] | 1.30 | 1.30 | 31.9% [22.1%, 43.6%] | 9.1% [3.1%, 23.6%] | 45.5% [29.8%, 62.0%] | 13.0% [7.0%, 23.0%] | 52.0% [42.4%, 61.4%] | 22.8% [5.3%, 35.9%] | 0.0137 |
| gemini-2.5-flash | 65 | 35.4% [24.9%, 47.5%] | 93.3% [70.2%, 98.8%] | 2.64 | 2.64 | 60.9% [40.8%, 77.8%] | 2.4% [0.4%, 12.3%] | 64.3% [49.2%, 77.0%] | 17.4% [7.0%, 37.1%] | 29.2% [19.6%, 41.2%] | 58.5% [36.1%, 75.6%] | 1.68e-07 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 265 | 43.0% [37.2%, 49.0%] | 84.5% [73.1%, 91.6%] | 1.96 | 1.87 | 43.0% [34.3%, 52.2%] | 6.0% [3.2%, 10.9%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 41.5% [35.7%, 47.5%] | 37.0% [27.0%, 46.6%] | 3.19e-13 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 102 tasks, 10000 usable): H1 precision − base rate 95% CI [30.9%, 51.7%] → supported; H2 held-back difference 95% CI [25.3%, 48.6%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 85.7% [48.7%, 97.4%] | 3.82 | 3.82 | 27.3% [13.2%, 48.2%] | 1.3% [0.2%, 7.1%] | 25.0% [16.6%, 35.8%] | 13.6% [4.7%, 33.3%] | 70.4% [60.7%, 78.5%] | 26.0% [10.7%, 46.9%] | 0.000422 |
| claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 87.5% [64.0%, 96.5%] | 1.29 | 1.29 | 20.3% [12.5%, 31.2%] | 6.1% [1.7%, 19.6%] | 36.4% [22.2%, 53.4%] | 8.7% [4.0%, 17.7%] | 66.7% [57.1%, 75.1%] | 14.2% [-1.4%, 26.0%] | 0.083 |
| gemini-2.5-flash | 65 | 35.4% [24.9%, 47.5%] | 100.0% [61.0%, 100.0%] | 2.83 | 2.83 | 26.1% [12.5%, 46.5%] | 0.0% [0.0%, 8.4%] | 31.0% [19.1%, 46.0%] | 13.0% [4.5%, 32.1%] | 66.2% [54.0%, 76.5%] | 26.1% [10.2%, 46.5%] | 0.00122 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 265 | 43.0% [37.2%, 49.0%] | 89.7% [73.6%, 96.4%] | 2.08 | 1.79 | 22.8% [16.1%, 31.3%] | 2.0% [0.7%, 5.7%] | 29.1% [22.5%, 36.8%] | 10.5% [6.1%, 17.5%] | 67.9% [62.1%, 73.3%] | 20.8% [13.1%, 29.4%] | 6.99e-08 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 102 tasks, 10000 usable): H1 precision − base rate 95% CI [34.3%, 58.0%] → supported; H2 held-back difference 95% CI [12.2%, 30.5%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 43.8% [23.1%, 66.8%] | 1.95 | 1.95 | 31.8% [16.4%, 52.7%] | 11.8% [6.4%, 21.0%] | 32.9% [23.4%, 44.1%] | 18.2% [7.3%, 38.5%] | 54.1% [44.2%, 63.6%] | 20.0% [2.0%, 41.5%] | 0.0447 |
| claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 77.3% [56.6%, 89.9%] | 1.14 | 1.14 | 24.6% [16.0%, 36.0%] | 15.2% [6.7%, 30.9%] | 51.5% [35.2%, 67.5%] | 13.0% [7.0%, 23.0%] | 52.9% [43.3%, 62.3%] | 9.5% [-8.5%, 23.6%] | 0.316 |
| gemini-2.5-flash | 65 | 35.4% [24.9%, 47.5%] | 69.2% [42.4%, 87.3%] | 1.96 | 1.96 | 39.1% [22.2%, 59.2%] | 9.5% [3.8%, 22.1%] | 40.5% [27.0%, 55.5%] | 17.4% [7.0%, 37.1%] | 47.7% [36.0%, 59.6%] | 29.6% [8.5%, 50.5%] | 0.008 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 265 | 43.0% [37.2%, 49.0%] | 64.7% [51.0%, 76.4%] | 1.50 | 1.43 | 28.9% [21.4%, 37.9%] | 11.9% [7.7%, 18.1%] | 39.1% [31.7%, 47.0%] | 14.9% [9.5%, 22.6%] | 52.1% [46.1%, 58.0%] | 17.0% [7.3%, 26.9%] | 0.000828 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 102 tasks, 10000 usable): H1 precision − base rate 95% CI [9.8%, 33.2%] → supported; H2 held-back difference 95% CI [7.1%, 27.6%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 72.2% [49.1%, 87.5%] | 3.22 | 3.22 | 59.1% [38.7%, 76.7%] | 6.6% [2.8%, 14.5%] | 51.3% [40.3%, 62.2%] | 13.6% [4.7%, 33.3%] | 38.8% [29.7%, 48.7%] | 52.5% [30.7%, 70.6%] | 4.67e-07 |
| claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 89.1% [77.0%, 95.3%] | 1.32 | 1.32 | 59.4% [47.6%, 70.2%] | 15.2% [6.7%, 30.9%] | 45.5% [29.8%, 62.0%] | 13.0% [7.0%, 23.0%] | 31.4% [23.2%, 40.9%] | 44.3% [24.6%, 58.0%] | 3.57e-05 |
| gemini-2.5-flash | 65 | 35.4% [24.9%, 47.5%] | 93.3% [70.2%, 98.8%] | 2.64 | 2.64 | 60.9% [40.8%, 77.8%] | 2.4% [0.4%, 12.3%] | 64.3% [49.2%, 77.0%] | 17.4% [7.0%, 37.1%] | 29.2% [19.6%, 41.2%] | 58.5% [36.1%, 75.6%] | 1.68e-07 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 265 | 43.0% [37.2%, 49.0%] | 86.1% [76.8%, 92.0%] | 2.00 | 1.68 | 59.6% [50.5%, 68.2%] | 7.3% [4.1%, 12.6%] | 53.6% [45.7%, 61.4%] | 14.0% [8.8%, 21.6%] | 33.6% [28.2%, 39.5%] | 52.4% [41.8%, 61.5%] | 6.17e-21 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 102 tasks, 10000 usable): H1 precision − base rate 95% CI [34.4%, 51.7%] → supported; H2 held-back difference 95% CI [40.1%, 64.4%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 73.7% [51.2%, 88.2%] | 3.28 | 3.28 | 63.6% [43.0%, 80.3%] | 6.6% [2.8%, 14.5%] | 47.4% [36.5%, 58.4%] | 9.1% [2.5%, 27.8%] | 41.8% [32.6%, 51.7%] | 57.1% [34.9%, 74.1%] | 7.08e-08 |
| claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 88.5% [71.0%, 96.0%] | 1.31 | 1.31 | 33.3% [23.4%, 45.1%] | 9.1% [3.1%, 23.6%] | 39.4% [24.7%, 56.3%] | 10.1% [5.0%, 19.5%] | 54.9% [45.2%, 64.2%] | 24.2% [6.7%, 37.4%] | 0.00814 |
| gemini-2.5-flash | 65 | 35.4% [24.9%, 47.5%] | 88.2% [65.7%, 96.7%] | 2.49 | 2.49 | 65.2% [44.9%, 81.2%] | 4.8% [1.3%, 15.8%] | 59.5% [44.5%, 73.0%] | 13.0% [4.5%, 32.1%] | 30.8% [20.9%, 42.8%] | 60.5% [37.3%, 76.8%] | 2.32e-07 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 265 | 43.0% [37.2%, 49.0%] | 83.9% [72.8%, 91.0%] | 1.95 | 1.87 | 45.6% [36.8%, 54.8%] | 6.6% [3.6%, 11.8%] | 49.0% [41.2%, 56.9%] | 10.5% [6.1%, 17.5%] | 44.2% [38.3%, 50.2%] | 39.0% [28.8%, 48.6%] | 1.11e-13 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 102 tasks, 10000 usable): H1 precision − base rate 95% CI [30.8%, 50.6%] → supported; H2 held-back difference 95% CI [26.9%, 50.9%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 98 | 22.4% [15.3%, 31.7%] | 73.7% [51.2%, 88.2%] | 3.28 | 3.28 | 63.6% [43.0%, 80.3%] | 6.6% [2.8%, 14.5%] | 47.4% [36.5%, 58.4%] | 9.1% [2.5%, 27.8%] | 41.8% [32.6%, 51.7%] | 57.1% [34.9%, 74.1%] | 7.08e-08 |
| claude-sonnet-4 | 102 | 67.6% [58.1%, 75.9%] | 89.6% [77.8%, 95.5%] | 1.32 | 1.32 | 62.3% [50.5%, 72.8%] | 15.2% [6.7%, 30.9%] | 39.4% [24.7%, 56.3%] | 10.1% [5.0%, 19.5%] | 33.3% [24.9%, 42.9%] | 47.2% [27.5%, 60.7%] | 6.49e-06 |
| gemini-2.5-flash | 65 | 35.4% [24.9%, 47.5%] | 88.2% [65.7%, 96.7%] | 2.49 | 2.49 | 65.2% [44.9%, 81.2%] | 4.8% [1.3%, 15.8%] | 59.5% [44.5%, 73.0%] | 13.0% [4.5%, 32.1%] | 30.8% [20.9%, 42.8%] | 60.5% [37.3%, 76.8%] | 2.32e-07 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 265 | 43.0% [37.2%, 49.0%] | 85.7% [76.7%, 91.6%] | 1.99 | 1.68 | 63.2% [54.0%, 71.4%] | 7.9% [4.6%, 13.4%] | 49.0% [41.2%, 56.9%] | 10.5% [6.1%, 17.5%] | 35.8% [30.3%, 41.8%] | 55.2% [44.6%, 64.2%] | 1.63e-22 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 102 tasks, 10000 usable): H1 precision − base rate 95% CI [34.5%, 50.9%] → supported; H2 held-back difference 95% CI [42.9%, 67.3%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

53 tasks, 139 patches. ACCEPT rate correct 32.4% [22.4%, 44.2%], wrong 5.6% [2.2%, 13.6%]. Correct/wrong pairs in the same task: concordant 23, discordant 4, ties 59.

### V4 on correct public patches vs gold on the same tasks

114 correct public patches: V4 full pass 85.1% [77.4%, 90.5%]; gold on the same tasks 83.3% [75.4%, 89.1%]. Cells: {'public_pass__gold_pass': 92, 'public_pass__gold_not': 5, 'public_not__gold_pass': 3, 'public_not__gold_not': 14}.

- H3 (all): 1 of 108 gold patches REJECTed, point 0.9%, Wilson 95% upper 5.1% (sympy__sympy-14248).
- H3 (headline_scope): 1 of 102 gold patches REJECTed, point 1.0%, Wilson 95% upper 5.3% (sympy__sympy-14248).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 102 | 2 | 98 | 22 |
| claude-sonnet-4 | 102 | 0 | 102 | 69 |
| gemini-2.5-flash | 86 | 5 | 65 | 23 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-8035, claude-sonnet-4/sphinx-doc__sphinx-8638, claude-sonnet-4/sphinx-doc__sphinx-9591, claude-sonnet-4/sphinx-doc__sphinx-9698, gemini-2.5-flash/sphinx-doc__sphinx-9591, gpt-4.1-mini/pytest-dev__pytest-8399, gpt-4.1-mini/sphinx-doc__sphinx-8035, gpt-4.1-mini/sphinx-doc__sphinx-9658.

## Scope: sensitivity: all tasks (no exclusions)

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 103 | 22.3% [15.4%, 31.3%] | 73.7% [51.2%, 88.2%] | 3.30 | 3.30 | 60.9% [40.8%, 77.8%] | 6.2% [2.7%, 13.8%] | 52.5% [41.7%, 63.1%] | 13.0% [4.5%, 32.1%] | 37.9% [29.1%, 47.5%] | 54.6% [33.2%, 72.0%] | 8.32e-08 |
| claude-sonnet-4 | 108 | 67.6% [58.3%, 75.7%] | 88.5% [71.0%, 96.0%] | 1.31 | 1.31 | 31.5% [22.0%, 42.9%] | 8.6% [3.0%, 22.4%] | 45.7% [30.5%, 61.8%] | 13.7% [7.6%, 23.4%] | 51.9% [42.5%, 61.0%] | 22.9% [6.2%, 35.6%] | 0.00864 |
| gemini-2.5-flash | 87 | 27.6% [19.3%, 37.8%] | 93.3% [70.2%, 98.8%] | 3.38 | 3.38 | 58.3% [38.8%, 75.5%] | 1.6% [0.3%, 8.5%] | 71.4% [59.3%, 81.1%] | 16.7% [6.7%, 35.9%] | 26.4% [18.3%, 36.6%] | 56.7% [36.1%, 74.0%] | 4.74e-09 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 298 | 40.3% [34.9%, 45.9%] | 85.0% [73.9%, 91.9%] | 2.11 | 1.96 | 42.5% [34.0%, 51.4%] | 5.1% [2.7%, 9.3%] | 57.9% [50.5%, 64.9%] | 14.2% [9.0%, 21.5%] | 39.6% [34.2%, 45.2%] | 37.4% [28.0%, 46.7%] | 2.16e-15 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 108 tasks, 10000 usable): H1 precision − base rate 95% CI [34.4%, 54.3%] → supported; H2 held-back difference 95% CI [25.9%, 48.6%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 103 | 22.3% [15.4%, 31.3%] | 87.5% [52.9%, 97.8%] | 3.92 | 3.92 | 30.4% [15.6%, 50.9%] | 1.2% [0.2%, 6.7%] | 26.2% [17.9%, 36.8%] | 13.0% [4.5%, 32.1%] | 68.9% [59.5%, 77.1%] | 29.2% [13.4%, 49.6%] | 8.46e-05 |
| claude-sonnet-4 | 108 | 67.6% [58.3%, 75.7%] | 87.5% [64.0%, 96.5%] | 1.29 | 1.29 | 19.2% [11.8%, 29.7%] | 5.7% [1.6%, 18.6%] | 37.1% [23.2%, 53.7%] | 9.6% [4.7%, 18.5%] | 66.7% [57.3%, 74.8%] | 13.5% [-1.4%, 24.7%] | 0.0844 |
| gemini-2.5-flash | 87 | 27.6% [19.3%, 37.8%] | 100.0% [61.0%, 100.0%] | 3.62 | 3.62 | 25.0% [12.0%, 44.9%] | 0.0% [0.0%, 5.7%] | 49.2% [37.3%, 61.2%] | 12.5% [4.3%, 31.0%] | 54.0% [43.6%, 64.1%] | 25.0% [10.8%, 44.9%] | 0.000267 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 298 | 40.3% [34.9%, 45.9%] | 90.0% [74.4%, 96.5%] | 2.24 | 1.89 | 22.5% [15.9%, 30.8%] | 1.7% [0.6%, 4.8%] | 36.5% [29.8%, 43.8%] | 10.8% [6.4%, 17.7%] | 63.8% [58.2%, 69.0%] | 20.8% [13.5%, 29.1%] | 3.71e-09 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 108 tasks, 10000 usable): H1 precision − base rate 95% CI [38.1%, 60.2%] → supported; H2 held-back difference 95% CI [12.4%, 30.1%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 103 | 22.3% [15.4%, 31.3%] | 47.1% [26.2%, 69.0%] | 2.11 | 2.11 | 34.8% [18.8%, 55.1%] | 11.2% [6.0%, 20.0%] | 33.8% [24.3%, 44.6%] | 17.4% [7.0%, 37.1%] | 53.4% [43.8%, 62.7%] | 23.5% [5.3%, 44.5%] | 0.0211 |
| claude-sonnet-4 | 108 | 67.6% [58.3%, 75.7%] | 78.3% [58.1%, 90.3%] | 1.16 | 1.16 | 24.7% [16.2%, 35.6%] | 14.3% [6.3%, 29.4%] | 51.4% [35.6%, 67.0%] | 15.1% [8.6%, 25.0%] | 51.9% [42.5%, 61.0%] | 10.4% [-6.9%, 24.0%] | 0.316 |
| gemini-2.5-flash | 87 | 27.6% [19.3%, 37.8%] | 60.0% [35.7%, 80.2%] | 2.17 | 2.17 | 37.5% [21.2%, 57.3%] | 9.5% [4.4%, 19.3%] | 55.6% [43.3%, 67.2%] | 16.7% [6.7%, 35.9%] | 37.9% [28.5%, 48.4%] | 28.0% [9.0%, 48.4%] | 0.00396 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 298 | 40.3% [34.9%, 45.9%] | 63.6% [50.4%, 75.1%] | 1.58 | 1.49 | 29.2% [21.8%, 37.8%] | 11.2% [7.4%, 16.7%] | 44.9% [37.8%, 52.3%] | 15.8% [10.4%, 23.4%] | 48.3% [42.7%, 54.0%] | 17.9% [8.7%, 27.4%] | 0.000125 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 108 tasks, 10000 usable): H1 precision − base rate 95% CI [12.1%, 34.2%] → supported; H2 held-back difference 95% CI [8.3%, 27.9%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 103 | 22.3% [15.4%, 31.3%] | 73.7% [51.2%, 88.2%] | 3.30 | 3.30 | 60.9% [40.8%, 77.8%] | 6.2% [2.7%, 13.8%] | 52.5% [41.7%, 63.1%] | 13.0% [4.5%, 32.1%] | 37.9% [29.1%, 47.5%] | 54.6% [33.2%, 72.0%] | 8.32e-08 |
| claude-sonnet-4 | 108 | 67.6% [58.3%, 75.7%] | 89.6% [77.8%, 95.5%] | 1.33 | 1.33 | 58.9% [47.4%, 69.5%] | 14.3% [6.3%, 29.4%] | 45.7% [30.5%, 61.8%] | 13.7% [7.6%, 23.4%] | 31.5% [23.5%, 40.7%] | 44.6% [25.7%, 57.9%] | 1.01e-05 |
| gemini-2.5-flash | 87 | 27.6% [19.3%, 37.8%] | 93.8% [71.7%, 98.9%] | 3.40 | 3.40 | 62.5% [42.7%, 78.8%] | 1.6% [0.3%, 8.5%] | 71.4% [59.3%, 81.1%] | 16.7% [6.7%, 35.9%] | 25.3% [17.3%, 35.3%] | 60.9% [40.0%, 77.3%] | 7.02e-10 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 298 | 40.3% [34.9%, 45.9%] | 86.7% [77.8%, 92.4%] | 2.15 | 1.75 | 60.0% [51.1%, 68.3%] | 6.2% [3.5%, 10.7%] | 57.9% [50.5%, 64.9%] | 14.2% [9.0%, 21.5%] | 31.9% [26.8%, 37.4%] | 53.8% [43.8%, 62.6%] | 5.12e-25 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 108 tasks, 10000 usable): H1 precision − base rate 95% CI [38.6%, 54.4%] → supported; H2 held-back difference 95% CI [42.0%, 65.0%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 103 | 22.3% [15.4%, 31.3%] | 75.0% [53.1%, 88.8%] | 3.36 | 3.36 | 65.2% [44.9%, 81.2%] | 6.2% [2.7%, 13.8%] | 46.2% [35.7%, 57.1%] | 8.7% [2.4%, 26.8%] | 42.7% [33.6%, 52.4%] | 59.0% [37.3%, 75.3%] | 1.18e-08 |
| claude-sonnet-4 | 108 | 67.6% [58.3%, 75.7%] | 89.3% [72.8%, 96.3%] | 1.32 | 1.32 | 34.2% [24.4%, 45.7%] | 8.6% [3.0%, 22.4%] | 37.1% [23.2%, 53.7%] | 9.6% [4.7%, 18.5%] | 55.6% [46.2%, 64.6%] | 25.7% [8.7%, 38.4%] | 0.00452 |
| gemini-2.5-flash | 87 | 27.6% [19.3%, 37.8%] | 88.2% [65.7%, 96.7%] | 3.20 | 3.20 | 62.5% [42.7%, 78.8%] | 3.2% [0.9%, 10.9%] | 68.3% [56.0%, 78.4%] | 12.5% [4.3%, 31.0%] | 27.6% [19.3%, 37.8%] | 59.3% [38.1%, 75.8%] | 5.26e-09 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 298 | 40.3% [34.9%, 45.9%] | 84.6% [73.9%, 91.4%] | 2.10 | 1.96 | 45.8% [37.2%, 54.7%] | 5.6% [3.1%, 10.0%] | 52.2% [44.9%, 59.5%] | 10.0% [5.8%, 16.7%] | 43.0% [37.5%, 48.6%] | 40.2% [30.5%, 49.5%] | 1.17e-16 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 108 tasks, 10000 usable): H1 precision − base rate 95% CI [34.5%, 53.6%] → supported; H2 held-back difference 95% CI [28.4%, 51.7%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 103 | 22.3% [15.4%, 31.3%] | 75.0% [53.1%, 88.8%] | 3.36 | 3.36 | 65.2% [44.9%, 81.2%] | 6.2% [2.7%, 13.8%] | 46.2% [35.7%, 57.1%] | 8.7% [2.4%, 26.8%] | 42.7% [33.6%, 52.4%] | 59.0% [37.3%, 75.3%] | 1.18e-08 |
| claude-sonnet-4 | 108 | 67.6% [58.3%, 75.7%] | 90.2% [79.0%, 95.7%] | 1.33 | 1.33 | 63.0% [51.5%, 73.2%] | 14.3% [6.3%, 29.4%] | 37.1% [23.2%, 53.7%] | 9.6% [4.7%, 18.5%] | 34.3% [26.0%, 43.6%] | 48.7% [29.8%, 61.7%] | 1.48e-06 |
| gemini-2.5-flash | 87 | 27.6% [19.3%, 37.8%] | 88.9% [67.2%, 96.9%] | 3.22 | 3.22 | 66.7% [46.7%, 82.0%] | 3.2% [0.9%, 10.9%] | 68.3% [56.0%, 78.4%] | 12.5% [4.3%, 31.0%] | 26.4% [18.3%, 36.6%] | 63.5% [42.1%, 79.0%] | 7.58e-10 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 298 | 40.3% [34.9%, 45.9%] | 86.5% [77.9%, 92.1%] | 2.15 | 1.75 | 64.2% [55.3%, 72.2%] | 6.7% [3.9%, 11.4%] | 52.2% [44.9%, 59.5%] | 10.0% [5.8%, 16.7%] | 34.9% [29.7%, 40.5%] | 57.4% [47.4%, 65.9%] | 2.8e-27 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 108 tasks, 10000 usable): H1 precision − base rate 95% CI [38.6%, 53.8%] → supported; H2 held-back difference 95% CI [45.5%, 68.8%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

58 tasks, 160 patches. ACCEPT rate correct 33.3% [23.7%, 44.6%], wrong 4.7% [1.8%, 11.5%]. Correct/wrong pairs in the same task: concordant 33, discordant 4, ties 65.

### V4 on correct public patches vs gold on the same tasks

120 correct public patches: V4 full pass 85.8% [78.5%, 91.0%]; gold on the same tasks 84.2% [76.6%, 89.6%]. Cells: {'public_pass__gold_pass': 98, 'public_pass__gold_not': 5, 'public_not__gold_pass': 3, 'public_not__gold_not': 14}.

- H3 (all): 1 of 108 gold patches REJECTed, point 0.9%, Wilson 95% upper 5.1% (sympy__sympy-14248).
- H3 (headline_scope): 1 of 108 gold patches REJECTed, point 0.9%, Wilson 95% upper 5.1% (sympy__sympy-14248).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 108 | 3 | 103 | 23 |
| claude-sonnet-4 | 108 | 0 | 108 | 73 |
| gemini-2.5-flash | 108 | 5 | 87 | 24 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-8035, claude-sonnet-4/sphinx-doc__sphinx-8638, claude-sonnet-4/sphinx-doc__sphinx-9591, claude-sonnet-4/sphinx-doc__sphinx-9698, gemini-2.5-flash/sphinx-doc__sphinx-9591, gpt-4.1-mini/pytest-dev__pytest-8399, gpt-4.1-mini/sphinx-doc__sphinx-8035, gpt-4.1-mini/sphinx-doc__sphinx-9658.

## Scope: sensitivity: headline minus tasks with generator recall

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 62 | 27.4% [17.9%, 39.6%] | 78.6% [52.4%, 92.4%] | 2.87 | 2.87 | 64.7% [41.3%, 82.7%] | 6.7% [2.3%, 17.9%] | 53.3% [39.1%, 67.1%] | 0.0% [0.0%, 18.4%] | 38.7% [27.6%, 51.2%] | 58.0% [32.1%, 76.5%] | 6.25e-06 |
| claude-sonnet-4 | 64 | 64.1% [51.8%, 74.7%] | 93.8% [71.7%, 98.9%] | 1.46 | 1.46 | 36.6% [23.6%, 51.9%] | 4.3% [0.8%, 21.0%] | 65.2% [44.9%, 81.2%] | 7.3% [2.5%, 19.4%] | 46.9% [35.2%, 58.9%] | 32.2% [11.1%, 47.9%] | 0.00558 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 100.0% [67.6%, 100.0%] | 3.36 | 3.36 | 72.7% [43.4%, 90.3%] | 0.0% [0.0%, 12.9%] | 65.4% [46.2%, 80.6%] | 9.1% [1.6%, 37.7%] | 29.7% [17.5%, 45.8%] | 72.7% [40.7%, 90.3%] | 4.27e-06 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 163 | 42.3% [35.0%, 50.0%] | 89.5% [75.9%, 95.8%] | 2.11 | 2.06 | 49.3% [37.8%, 60.8%] | 4.3% [1.7%, 10.4%] | 59.6% [49.5%, 68.9%] | 5.8% [2.3%, 14.0%] | 39.9% [32.7%, 47.5%] | 45.0% [32.0%, 56.8%] | 8.78e-12 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 64 tasks, 10000 usable): H1 precision − base rate 95% CI [33.9%, 60.2%] → supported; H2 held-back difference 95% CI [29.1%, 59.9%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 62 | 27.4% [17.9%, 39.6%] | 85.7% [48.7%, 97.4%] | 3.13 | 3.13 | 35.3% [17.3%, 58.7%] | 2.2% [0.4%, 11.6%] | 28.9% [17.7%, 43.4%] | 0.0% [0.0%, 18.4%] | 67.7% [55.4%, 78.0%] | 33.1% [12.8%, 56.5%] | 0.00117 |
| claude-sonnet-4 | 64 | 64.1% [51.8%, 74.7%] | 100.0% [72.2%, 100.0%] | 1.56 | 1.56 | 24.4% [13.8%, 39.3%] | 0.0% [0.0%, 14.3%] | 52.2% [33.0%, 70.8%] | 4.9% [1.3%, 16.1%] | 62.5% [50.3%, 73.3%] | 24.4% [6.6%, 39.3%] | 0.0103 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 100.0% [51.0%, 100.0%] | 3.36 | 3.36 | 36.4% [15.2%, 64.6%] | 0.0% [0.0%, 12.9%] | 38.5% [22.4%, 57.5%] | 0.0% [0.0%, 25.9%] | 62.2% [46.1%, 75.9%] | 36.4% [11.6%, 64.6%] | 0.005 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 163 | 42.3% [35.0%, 50.0%] | 95.2% [77.3%, 99.2%] | 2.25 | 2.10 | 29.0% [19.6%, 40.6%] | 1.1% [0.2%, 5.8%] | 37.2% [28.1%, 47.3%] | 2.9% [0.8%, 10.0%] | 64.4% [56.8%, 71.4%] | 27.9% [17.4%, 39.5%] | 7.65e-08 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 64 tasks, 10000 usable): H1 precision − base rate 95% CI [40.2%, 64.9%] → supported; H2 held-back difference 95% CI [15.7%, 41.6%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 62 | 27.4% [17.9%, 39.6%] | 63.6% [35.4%, 84.8%] | 2.32 | 2.32 | 41.2% [21.6%, 64.0%] | 8.9% [3.5%, 20.7%] | 40.0% [27.0%, 54.5%] | 5.9% [1.0%, 27.0%] | 51.6% [39.4%, 63.6%] | 32.3% [9.4%, 55.7%] | 0.00643 |
| claude-sonnet-4 | 64 | 64.1% [51.8%, 74.7%] | 92.3% [66.7%, 98.6%] | 1.44 | 1.44 | 29.3% [17.6%, 44.5%] | 4.3% [0.8%, 21.0%] | 73.9% [53.5%, 87.5%] | 12.2% [5.3%, 25.5%] | 45.3% [33.7%, 57.4%] | 24.9% [4.6%, 40.5%] | 0.0225 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 66.7% [35.4%, 87.9%] | 2.24 | 2.24 | 54.5% [28.0%, 78.7%] | 11.5% [4.0%, 29.0%] | 46.2% [28.8%, 64.5%] | 0.0% [0.0%, 25.9%] | 43.2% [28.7%, 59.1%] | 43.0% [11.3%, 68.3%] | 0.0106 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 163 | 42.3% [35.0%, 50.0%] | 75.8% [59.0%, 87.2%] | 1.79 | 1.78 | 36.2% [25.9%, 48.0%] | 8.5% [4.4%, 15.9%] | 50.0% [40.1%, 59.9%] | 8.7% [4.0%, 17.7%] | 47.2% [39.7%, 54.9%] | 27.7% [15.0%, 40.2%] | 2.04e-05 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 64 tasks, 10000 usable): H1 precision − base rate 95% CI [19.1%, 46.6%] → supported; H2 held-back difference 95% CI [13.8%, 42.1%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 62 | 27.4% [17.9%, 39.6%] | 78.6% [52.4%, 92.4%] | 2.87 | 2.87 | 64.7% [41.3%, 82.7%] | 6.7% [2.3%, 17.9%] | 53.3% [39.1%, 67.1%] | 0.0% [0.0%, 18.4%] | 38.7% [27.6%, 51.2%] | 58.0% [32.1%, 76.5%] | 6.25e-06 |
| claude-sonnet-4 | 64 | 64.1% [51.8%, 74.7%] | 93.1% [78.0%, 98.1%] | 1.45 | 1.45 | 65.9% [50.5%, 78.4%] | 8.7% [2.4%, 26.8%] | 65.2% [44.9%, 81.2%] | 7.3% [2.5%, 19.4%] | 26.6% [17.3%, 38.5%] | 57.2% [33.5%, 71.2%] | 7.18e-06 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 100.0% [67.6%, 100.0%] | 3.36 | 3.36 | 72.7% [43.4%, 90.3%] | 0.0% [0.0%, 12.9%] | 65.4% [46.2%, 80.6%] | 9.1% [1.6%, 37.7%] | 29.7% [17.5%, 45.8%] | 72.7% [40.7%, 90.3%] | 4.27e-06 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 163 | 42.3% [35.0%, 50.0%] | 90.2% [79.0%, 95.7%] | 2.13 | 1.86 | 66.7% [54.9%, 76.6%] | 5.3% [2.3%, 11.9%] | 59.6% [49.5%, 68.9%] | 5.8% [2.3%, 14.0%] | 31.9% [25.2%, 39.4%] | 61.3% [47.9%, 71.8%] | 1.04e-17 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 64 tasks, 10000 usable): H1 precision − base rate 95% CI [36.9%, 59.1%] → supported; H2 held-back difference 95% CI [46.4%, 75.0%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 62 | 27.4% [17.9%, 39.6%] | 78.6% [52.4%, 92.4%] | 2.87 | 2.87 | 64.7% [41.3%, 82.7%] | 6.7% [2.3%, 17.9%] | 46.7% [32.9%, 60.9%] | 0.0% [0.0%, 18.4%] | 43.5% [31.9%, 55.9%] | 58.0% [32.1%, 76.5%] | 6.25e-06 |
| claude-sonnet-4 | 64 | 64.1% [51.8%, 74.7%] | 93.8% [71.7%, 98.9%] | 1.46 | 1.46 | 36.6% [23.6%, 51.9%] | 4.3% [0.8%, 21.0%] | 56.5% [36.8%, 74.4%] | 4.9% [1.3%, 16.1%] | 51.6% [39.6%, 63.4%] | 32.2% [11.1%, 47.9%] | 0.00558 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 88.9% [56.5%, 98.0%] | 2.99 | 2.99 | 72.7% [43.4%, 90.3%] | 3.8% [0.7%, 18.9%] | 57.7% [38.9%, 74.5%] | 9.1% [1.6%, 37.7%] | 32.4% [19.6%, 48.5%] | 68.9% [36.0%, 86.7%] | 3.49e-05 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 163 | 42.3% [35.0%, 50.0%] | 87.2% [73.3%, 94.4%] | 2.06 | 2.03 | 49.3% [37.8%, 60.8%] | 5.3% [2.3%, 11.9%] | 52.1% [42.1%, 61.9%] | 4.3% [1.5%, 12.0%] | 44.2% [36.8%, 51.8%] | 44.0% [30.8%, 55.9%] | 5.64e-11 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 64 tasks, 10000 usable): H1 precision − base rate 95% CI [31.9%, 57.5%] → supported; H2 held-back difference 95% CI [28.2%, 58.8%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 62 | 27.4% [17.9%, 39.6%] | 78.6% [52.4%, 92.4%] | 2.87 | 2.87 | 64.7% [41.3%, 82.7%] | 6.7% [2.3%, 17.9%] | 46.7% [32.9%, 60.9%] | 0.0% [0.0%, 18.4%] | 43.5% [31.9%, 55.9%] | 58.0% [32.1%, 76.5%] | 6.25e-06 |
| claude-sonnet-4 | 64 | 64.1% [51.8%, 74.7%] | 93.3% [78.7%, 98.2%] | 1.46 | 1.46 | 68.3% [53.0%, 80.4%] | 8.7% [2.4%, 26.8%] | 56.5% [36.8%, 74.4%] | 4.9% [1.3%, 16.1%] | 29.7% [19.9%, 41.8%] | 59.6% [35.9%, 73.3%] | 4.15e-06 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 88.9% [56.5%, 98.0%] | 2.99 | 2.99 | 72.7% [43.4%, 90.3%] | 3.8% [0.7%, 18.9%] | 57.7% [38.9%, 74.5%] | 9.1% [1.6%, 37.7%] | 32.4% [19.6%, 48.5%] | 68.9% [36.0%, 86.7%] | 3.49e-05 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 163 | 42.3% [35.0%, 50.0%] | 88.7% [77.4%, 94.7%] | 2.09 | 1.83 | 68.1% [56.4%, 77.9%] | 6.4% [3.0%, 13.2%] | 52.1% [42.1%, 61.9%] | 4.3% [1.5%, 12.0%] | 35.6% [28.6%, 43.2%] | 61.7% [48.2%, 72.1%] | 1.67e-17 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 64 tasks, 10000 usable): H1 precision − base rate 95% CI [35.8%, 57.3%] → supported; H2 held-back difference 95% CI [46.9%, 75.6%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

30 tasks, 74 patches. ACCEPT rate correct 36.8% [23.4%, 52.7%], wrong 5.6% [1.5%, 18.1%]. Correct/wrong pairs in the same task: concordant 12, discordant 1, ties 31.

### V4 on correct public patches vs gold on the same tasks

69 correct public patches: V4 full pass 88.4% [78.8%, 94.0%]; gold on the same tasks 81.2% [70.4%, 88.6%]. Cells: {'public_pass__gold_pass': 56, 'public_pass__gold_not': 5, 'public_not__gold_pass': 0, 'public_not__gold_not': 8}.

- H3 (all): 1 of 108 gold patches REJECTed, point 0.9%, Wilson 95% upper 5.1% (sympy__sympy-14248).
- H3 (headline_scope): 1 of 64 gold patches REJECTed, point 1.6%, Wilson 95% upper 8.3% (sympy__sympy-14248).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 64 | 1 | 62 | 17 |
| claude-sonnet-4 | 64 | 0 | 64 | 41 |
| gemini-2.5-flash | 51 | 3 | 37 | 11 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-8638, claude-sonnet-4/sphinx-doc__sphinx-9591, gemini-2.5-flash/sphinx-doc__sphinx-9591, gpt-4.1-mini/sphinx-doc__sphinx-9658.

## Label checks

- gpt-4.1-mini: no label 4 (django__django-11149, django__django-13513, sphinx-doc__sphinx-8035, sympy__sympy-13031); official patch sha256 mismatch 0 (none).
- claude-sonnet-4: no label 0 (none); official patch sha256 mismatch 0 (none).
- gemini-2.5-flash: no label 17 (astropy__astropy-14995, django__django-11451, django__django-11734, django__django-13363, django__django-13401, django__django-13551, django__django-15022, django__django-16493, matplotlib__matplotlib-20859, pydata__xarray-3677, pydata__xarray-4687, pytest-dev__pytest-7571, scikit-learn__scikit-learn-25973, sphinx-doc__sphinx-9711, sympy__sympy-14531, sympy__sympy-20801, sympy__sympy-22456); official patch sha256 mismatch 0 (none).
