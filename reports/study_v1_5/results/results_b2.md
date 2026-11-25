# Study v1.5 batch 2 alone (held-out check of S1-S3)

## Scope: headline (batch, minus headline exclusions)

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 43 | 27.9% [16.7%, 42.7%] | 87.5% [52.9%, 97.8%] | 3.14 | 3.14 | 58.3% [32.0%, 80.7%] | 3.2% [0.6%, 16.2%] | 51.6% [34.8%, 68.0%] | 25.0% [8.9%, 53.2%] | 37.2% [24.4%, 52.1%] | 55.1% [25.7%, 77.6%] | 0.000173 |
| claude-sonnet-4 | 45 | 68.9% [54.3%, 80.5%] | 100.0% [75.8%, 100.0%] | 1.45 | 1.45 | 38.7% [23.7%, 56.2%] | 0.0% [0.0%, 21.5%] | 57.1% [32.6%, 78.6%] | 12.9% [5.1%, 28.9%] | 46.7% [32.9%, 60.9%] | 38.7% [12.5%, 56.2%] | 0.00852 |
| gemini-2.5-flash | 30 | 36.7% [21.9%, 54.5%] | 88.9% [56.5%, 98.0%] | 2.42 | 2.42 | 72.7% [43.4%, 90.3%] | 5.3% [0.9%, 24.6%] | 73.7% [51.2%, 88.2%] | 9.1% [1.6%, 37.7%] | 20.0% [9.5%, 37.3%] | 67.5% [32.3%, 85.5%] | 0.000223 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 118 | 45.8% [37.0%, 54.7%] | 93.1% [78.0%, 98.1%] | 2.03 | 1.96 | 50.0% [37.1%, 62.9%] | 3.1% [0.9%, 10.7%] | 59.4% [47.1%, 70.5%] | 14.8% [7.7%, 26.6%] | 36.4% [28.3%, 45.4%] | 46.9% [31.9%, 60.0%] | 1.69e-09 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 45 tasks, 10000 usable): H1 precision − base rate 95% CI [35.1%, 59.2%] → supported; H2 held-back difference 95% CI [29.5%, 63.6%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 43 | 27.9% [16.7%, 42.7%] | 100.0% [51.0%, 100.0%] | 3.58 | 3.58 | 33.3% [13.8%, 60.9%] | 0.0% [0.0%, 11.0%] | 32.3% [18.6%, 49.9%] | 25.0% [8.9%, 53.2%] | 60.5% [45.6%, 73.6%] | 33.3% [10.9%, 60.9%] | 0.00401 |
| claude-sonnet-4 | 45 | 68.9% [54.3%, 80.5%] | 100.0% [67.6%, 100.0%] | 1.45 | 1.45 | 25.8% [13.7%, 43.2%] | 0.0% [0.0%, 21.5%] | 42.9% [21.4%, 67.4%] | 9.7% [3.3%, 24.9%] | 62.2% [47.6%, 74.9%] | 25.8% [1.1%, 43.2%] | 0.0436 |
| gemini-2.5-flash | 30 | 36.7% [21.9%, 54.5%] | 100.0% [51.0%, 100.0%] | 2.73 | 2.73 | 36.4% [15.2%, 64.6%] | 0.0% [0.0%, 16.8%] | 31.6% [15.4%, 54.0%] | 9.1% [1.6%, 37.7%] | 63.3% [45.5%, 78.1%] | 36.4% [9.3%, 64.6%] | 0.012 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 118 | 45.8% [37.0%, 54.7%] | 100.0% [80.6%, 100.0%] | 2.19 | 1.98 | 29.6% [19.1%, 42.8%] | 0.0% [0.0%, 5.7%] | 34.4% [23.9%, 46.6%] | 13.0% [6.4%, 24.4%] | 61.9% [52.9%, 70.1%] | 29.6% [17.7%, 42.8%] | 9.06e-07 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 45 tasks, 10000 usable): H1 precision − base rate 95% CI [43.4%, 65.0%] → supported; H2 held-back difference 95% CI [15.4%, 45.1%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 43 | 27.9% [16.7%, 42.7%] | 40.0% [16.8%, 68.7%] | 1.43 | 1.43 | 33.3% [13.8%, 60.9%] | 19.4% [9.2%, 36.3%] | 41.9% [26.4%, 59.2%] | 25.0% [8.9%, 53.2%] | 39.5% [26.4%, 54.4%] | 14.0% [-11.9%, 43.4%] | 0.427 |
| claude-sonnet-4 | 45 | 68.9% [54.3%, 80.5%] | 100.0% [72.2%, 100.0%] | 1.45 | 1.45 | 32.3% [18.6%, 49.9%] | 0.0% [0.0%, 21.5%] | 64.3% [38.8%, 83.7%] | 12.9% [5.1%, 28.9%] | 48.9% [35.0%, 63.0%] | 32.3% [6.7%, 49.9%] | 0.0192 |
| gemini-2.5-flash | 30 | 36.7% [21.9%, 54.5%] | 80.0% [37.6%, 96.4%] | 2.18 | 2.18 | 36.4% [15.2%, 64.6%] | 5.3% [0.9%, 24.6%] | 36.8% [19.1%, 59.0%] | 18.2% [5.1%, 47.7%] | 53.3% [36.1%, 69.8%] | 31.1% [2.4%, 59.7%] | 0.0472 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 118 | 45.8% [37.0%, 54.7%] | 72.0% [52.4%, 85.7%] | 1.57 | 1.56 | 33.3% [22.2%, 46.6%] | 10.9% [5.4%, 20.9%] | 45.3% [33.7%, 57.4%] | 16.7% [9.0%, 28.7%] | 46.6% [37.9%, 55.6%] | 22.4% [7.5%, 36.8%] | 0.00352 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 45 tasks, 10000 usable): H1 precision − base rate 95% CI [9.2%, 42.3%] → supported; H2 held-back difference 95% CI [6.9%, 39.0%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 43 | 27.9% [16.7%, 42.7%] | 87.5% [52.9%, 97.8%] | 3.14 | 3.14 | 58.3% [32.0%, 80.7%] | 3.2% [0.6%, 16.2%] | 51.6% [34.8%, 68.0%] | 25.0% [8.9%, 53.2%] | 37.2% [24.4%, 52.1%] | 55.1% [25.7%, 77.6%] | 0.000173 |
| claude-sonnet-4 | 45 | 68.9% [54.3%, 80.5%] | 95.0% [76.4%, 99.1%] | 1.38 | 1.38 | 61.3% [43.8%, 76.3%] | 7.1% [1.3%, 31.5%] | 57.1% [32.6%, 78.6%] | 12.9% [5.1%, 28.9%] | 28.9% [17.7%, 43.4%] | 54.1% [24.2%, 70.2%] | 0.000888 |
| gemini-2.5-flash | 30 | 36.7% [21.9%, 54.5%] | 88.9% [56.5%, 98.0%] | 2.42 | 2.42 | 72.7% [43.4%, 90.3%] | 5.3% [0.9%, 24.6%] | 73.7% [51.2%, 88.2%] | 9.1% [1.6%, 37.7%] | 20.0% [9.5%, 37.3%] | 67.5% [32.3%, 85.5%] | 0.000223 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 118 | 45.8% [37.0%, 54.7%] | 91.9% [78.7%, 97.2%] | 2.01 | 1.76 | 63.0% [49.6%, 74.6%] | 4.7% [1.6%, 12.9%] | 59.4% [47.1%, 70.5%] | 14.8% [7.7%, 26.6%] | 29.7% [22.2%, 38.4%] | 58.3% [42.6%, 70.3%] | 2.49e-12 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 45 tasks, 10000 usable): H1 precision − base rate 95% CI [35.0%, 56.8%] → supported; H2 held-back difference 95% CI [39.3%, 75.5%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 43 | 27.9% [16.7%, 42.7%] | 88.9% [56.5%, 98.0%] | 3.19 | 3.19 | 66.7% [39.1%, 86.2%] | 3.2% [0.6%, 16.2%] | 48.4% [32.0%, 65.2%] | 16.7% [4.7%, 44.8%] | 39.5% [26.4%, 54.4%] | 63.4% [32.9%, 83.1%] | 2.76e-05 |
| claude-sonnet-4 | 45 | 68.9% [54.3%, 80.5%] | 100.0% [75.8%, 100.0%] | 1.45 | 1.45 | 38.7% [23.7%, 56.2%] | 0.0% [0.0%, 21.5%] | 57.1% [32.6%, 78.6%] | 9.7% [3.3%, 24.9%] | 48.9% [35.0%, 63.0%] | 38.7% [12.5%, 56.2%] | 0.00852 |
| gemini-2.5-flash | 30 | 36.7% [21.9%, 54.5%] | 80.0% [49.0%, 94.3%] | 2.18 | 2.18 | 72.7% [43.4%, 90.3%] | 10.5% [2.9%, 31.4%] | 68.4% [46.0%, 84.6%] | 9.1% [1.6%, 37.7%] | 20.0% [9.5%, 37.3%] | 62.2% [26.2%, 81.3%] | 0.000974 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 118 | 45.8% [37.0%, 54.7%] | 90.3% [75.1%, 96.7%] | 1.97 | 1.94 | 51.9% [38.9%, 64.6%] | 4.7% [1.6%, 12.9%] | 56.2% [44.1%, 67.7%] | 11.1% [5.2%, 22.2%] | 38.1% [29.9%, 47.1%] | 47.2% [31.8%, 60.3%] | 3.09e-09 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 45 tasks, 10000 usable): H1 precision − base rate 95% CI [32.5%, 55.8%] → supported; H2 held-back difference 95% CI [28.5%, 64.4%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 43 | 27.9% [16.7%, 42.7%] | 88.9% [56.5%, 98.0%] | 3.19 | 3.19 | 66.7% [39.1%, 86.2%] | 3.2% [0.6%, 16.2%] | 48.4% [32.0%, 65.2%] | 16.7% [4.7%, 44.8%] | 39.5% [26.4%, 54.4%] | 63.4% [32.9%, 83.1%] | 2.76e-05 |
| claude-sonnet-4 | 45 | 68.9% [54.3%, 80.5%] | 95.2% [77.3%, 99.2%] | 1.38 | 1.38 | 64.5% [46.9%, 78.9%] | 7.1% [1.3%, 31.5%] | 57.1% [32.6%, 78.6%] | 9.7% [3.3%, 24.9%] | 28.9% [17.7%, 43.4%] | 57.4% [27.4%, 72.9%] | 0.000356 |
| gemini-2.5-flash | 30 | 36.7% [21.9%, 54.5%] | 80.0% [49.0%, 94.3%] | 2.18 | 2.18 | 72.7% [43.4%, 90.3%] | 10.5% [2.9%, 31.4%] | 68.4% [46.0%, 84.6%] | 9.1% [1.6%, 37.7%] | 20.0% [9.5%, 37.3%] | 62.2% [26.2%, 81.3%] | 0.000974 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 118 | 45.8% [37.0%, 54.7%] | 90.0% [76.9%, 96.0%] | 1.97 | 1.74 | 66.7% [53.4%, 77.8%] | 6.2% [2.5%, 15.0%] | 56.2% [44.1%, 67.7%] | 11.1% [5.2%, 22.2%] | 30.5% [22.9%, 39.3%] | 60.4% [44.5%, 72.1%] | 1.69e-12 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 45 tasks, 10000 usable): H1 precision − base rate 95% CI [33.7%, 54.2%] → supported; H2 held-back difference 95% CI [41.0%, 77.8%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

24 tasks, 62 patches. ACCEPT rate correct 38.7% [23.7%, 56.2%], wrong 3.2% [0.6%, 16.2%]. Correct/wrong pairs in the same task: concordant 14, discordant 1, ties 23.

### V4 on correct public patches vs gold on the same tasks

54 correct public patches: V4 full pass 88.9% [77.8%, 94.8%]; gold on the same tasks 87.0% [75.6%, 93.6%]. Cells: {'public_pass__gold_pass': 46, 'public_pass__gold_not': 2, 'public_not__gold_pass': 1, 'public_not__gold_not': 5}.

- H3 (all): 0 of 48 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.4% (none).
- H3 (headline_scope): 0 of 45 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.9% (none).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 45 | 2 | 43 | 12 |
| claude-sonnet-4 | 45 | 0 | 45 | 31 |
| gemini-2.5-flash | 41 | 2 | 30 | 11 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-8638, claude-sonnet-4/sphinx-doc__sphinx-9698, gpt-4.1-mini/pytest-dev__pytest-8399.

## Scope: sensitivity: all tasks (no exclusions)

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 45 | 26.7% [16.0%, 41.0%] | 87.5% [52.9%, 97.8%] | 3.28 | 3.28 | 58.3% [32.0%, 80.7%] | 3.0% [0.5%, 15.3%] | 51.5% [35.2%, 67.5%] | 25.0% [8.9%, 53.2%] | 37.8% [25.1%, 52.4%] | 55.3% [26.2%, 77.8%] | 0.000124 |
| claude-sonnet-4 | 48 | 66.7% [52.5%, 78.3%] | 100.0% [75.8%, 100.0%] | 1.50 | 1.50 | 37.5% [22.9%, 54.7%] | 0.0% [0.0%, 19.4%] | 56.2% [33.2%, 76.9%] | 12.5% [5.0%, 28.1%] | 47.9% [34.5%, 61.7%] | 37.5% [13.3%, 54.7%] | 0.00411 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 88.9% [56.5%, 98.0%] | 2.99 | 2.99 | 72.7% [43.4%, 90.3%] | 3.8% [0.7%, 18.9%] | 73.1% [53.9%, 86.3%] | 9.1% [1.6%, 37.7%] | 21.6% [11.4%, 37.2%] | 68.9% [36.0%, 86.7%] | 3.49e-05 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 130 | 42.3% [34.2%, 50.9%] | 93.1% [78.0%, 98.1%] | 2.20 | 2.11 | 49.1% [36.4%, 61.9%] | 2.7% [0.7%, 9.2%] | 60.0% [48.7%, 70.3%] | 14.5% [7.6%, 26.2%] | 36.9% [29.1%, 45.5%] | 46.4% [32.1%, 59.4%] | 1.41e-10 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 48 tasks, 10000 usable): H1 precision − base rate 95% CI [38.4%, 62.6%] → supported; H2 held-back difference 95% CI [28.9%, 61.9%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 45 | 26.7% [16.0%, 41.0%] | 100.0% [51.0%, 100.0%] | 3.75 | 3.75 | 33.3% [13.8%, 60.9%] | 0.0% [0.0%, 10.4%] | 33.3% [19.8%, 50.4%] | 25.0% [8.9%, 53.2%] | 60.0% [45.5%, 73.0%] | 33.3% [11.2%, 60.9%] | 0.00332 |
| claude-sonnet-4 | 48 | 66.7% [52.5%, 78.3%] | 100.0% [67.6%, 100.0%] | 1.50 | 1.50 | 25.0% [13.3%, 42.1%] | 0.0% [0.0%, 19.4%] | 43.8% [23.1%, 66.8%] | 9.4% [3.2%, 24.2%] | 62.5% [48.4%, 74.8%] | 25.0% [2.4%, 42.1%] | 0.0394 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 100.0% [51.0%, 100.0%] | 3.36 | 3.36 | 36.4% [15.2%, 64.6%] | 0.0% [0.0%, 12.9%] | 42.3% [25.5%, 61.1%] | 9.1% [1.6%, 37.7%] | 56.8% [40.9%, 71.3%] | 36.4% [11.6%, 64.6%] | 0.005 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 130 | 42.3% [34.2%, 50.9%] | 100.0% [80.6%, 100.0%] | 2.36 | 2.11 | 29.1% [18.8%, 42.1%] | 0.0% [0.0%, 4.9%] | 38.7% [28.5%, 50.0%] | 12.7% [6.3%, 24.0%] | 60.0% [51.4%, 68.0%] | 29.1% [17.7%, 42.1%] | 2.45e-07 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 48 tasks, 10000 usable): H1 precision − base rate 95% CI [47.3%, 67.9%] → supported; H2 held-back difference 95% CI [15.2%, 44.1%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 45 | 26.7% [16.0%, 41.0%] | 40.0% [16.8%, 68.7%] | 1.50 | 1.50 | 33.3% [13.8%, 60.9%] | 18.2% [8.6%, 34.4%] | 42.4% [27.2%, 59.2%] | 25.0% [8.9%, 53.2%] | 40.0% [27.0%, 54.5%] | 15.2% [-10.2%, 44.4%] | 0.418 |
| claude-sonnet-4 | 48 | 66.7% [52.5%, 78.3%] | 100.0% [72.2%, 100.0%] | 1.50 | 1.50 | 31.2% [18.0%, 48.6%] | 0.0% [0.0%, 19.4%] | 62.5% [38.6%, 81.5%] | 15.6% [6.9%, 31.8%] | 47.9% [34.5%, 61.7%] | 31.2% [7.8%, 48.6%] | 0.0196 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 66.7% [30.0%, 90.3%] | 2.24 | 2.24 | 36.4% [15.2%, 64.6%] | 7.7% [2.1%, 24.1%] | 46.2% [28.8%, 64.5%] | 18.2% [5.1%, 47.7%] | 45.9% [31.0%, 61.6%] | 28.7% [1.8%, 57.5%] | 0.0515 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 130 | 42.3% [34.2%, 50.9%] | 69.2% [50.0%, 83.5%] | 1.64 | 1.62 | 32.7% [21.8%, 45.9%] | 10.7% [5.5%, 19.7%] | 48.0% [37.1%, 59.1%] | 18.2% [10.2%, 30.3%] | 44.6% [36.3%, 53.2%] | 22.1% [7.9%, 36.2%] | 0.00335 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 48 tasks, 10000 usable): H1 precision − base rate 95% CI [9.8%, 43.2%] → supported; H2 held-back difference 95% CI [7.0%, 37.9%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 45 | 26.7% [16.0%, 41.0%] | 87.5% [52.9%, 97.8%] | 3.28 | 3.28 | 58.3% [32.0%, 80.7%] | 3.0% [0.5%, 15.3%] | 51.5% [35.2%, 67.5%] | 25.0% [8.9%, 53.2%] | 37.8% [25.1%, 52.4%] | 55.3% [26.2%, 77.8%] | 0.000124 |
| claude-sonnet-4 | 48 | 66.7% [52.5%, 78.3%] | 95.0% [76.4%, 99.1%] | 1.43 | 1.43 | 59.4% [42.3%, 74.5%] | 6.2% [1.1%, 28.3%] | 56.2% [33.2%, 76.9%] | 12.5% [5.0%, 28.1%] | 31.2% [19.9%, 45.3%] | 53.1% [25.2%, 69.1%] | 0.000465 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 88.9% [56.5%, 98.0%] | 2.99 | 2.99 | 72.7% [43.4%, 90.3%] | 3.8% [0.7%, 18.9%] | 73.1% [53.9%, 86.3%] | 9.1% [1.6%, 37.7%] | 21.6% [11.4%, 37.2%] | 68.9% [36.0%, 86.7%] | 3.49e-05 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 130 | 42.3% [34.2%, 50.9%] | 91.9% [78.7%, 97.2%] | 2.17 | 1.87 | 61.8% [48.6%, 73.5%] | 4.0% [1.4%, 11.1%] | 60.0% [48.7%, 70.3%] | 14.5% [7.6%, 26.2%] | 30.8% [23.5%, 39.2%] | 57.8% [42.8%, 69.8%] | 1.43e-13 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 48 tasks, 10000 usable): H1 precision − base rate 95% CI [38.4%, 60.3%] → supported; H2 held-back difference 95% CI [38.7%, 74.0%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 45 | 26.7% [16.0%, 41.0%] | 88.9% [56.5%, 98.0%] | 3.33 | 3.33 | 66.7% [39.1%, 86.2%] | 3.0% [0.5%, 15.3%] | 45.5% [29.8%, 62.0%] | 16.7% [4.7%, 44.8%] | 42.2% [29.0%, 56.7%] | 63.6% [33.4%, 83.3%] | 1.87e-05 |
| claude-sonnet-4 | 48 | 66.7% [52.5%, 78.3%] | 100.0% [75.8%, 100.0%] | 1.50 | 1.50 | 37.5% [22.9%, 54.7%] | 0.0% [0.0%, 19.4%] | 50.0% [28.0%, 72.0%] | 9.4% [3.2%, 24.2%] | 52.1% [38.3%, 65.5%] | 37.5% [13.3%, 54.7%] | 0.00411 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 80.0% [49.0%, 94.3%] | 2.69 | 2.69 | 72.7% [43.4%, 90.3%] | 7.7% [2.1%, 24.1%] | 69.2% [50.0%, 83.5%] | 9.1% [1.6%, 37.7%] | 21.6% [11.4%, 37.2%] | 65.0% [31.4%, 83.4%] | 0.000158 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 130 | 42.3% [34.2%, 50.9%] | 90.3% [75.1%, 96.7%] | 2.13 | 2.09 | 50.9% [38.1%, 63.6%] | 4.0% [1.4%, 11.1%] | 54.7% [43.4%, 65.4%] | 10.9% [5.1%, 21.8%] | 40.0% [32.0%, 48.6%] | 46.9% [32.2%, 59.9%] | 3.18e-10 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 48 tasks, 10000 usable): H1 precision − base rate 95% CI [35.7%, 59.4%] → supported; H2 held-back difference 95% CI [28.2%, 63.0%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 45 | 26.7% [16.0%, 41.0%] | 88.9% [56.5%, 98.0%] | 3.33 | 3.33 | 66.7% [39.1%, 86.2%] | 3.0% [0.5%, 15.3%] | 45.5% [29.8%, 62.0%] | 16.7% [4.7%, 44.8%] | 42.2% [29.0%, 56.7%] | 63.6% [33.4%, 83.3%] | 1.87e-05 |
| claude-sonnet-4 | 48 | 66.7% [52.5%, 78.3%] | 95.2% [77.3%, 99.2%] | 1.43 | 1.43 | 62.5% [45.3%, 77.1%] | 6.2% [1.1%, 28.3%] | 50.0% [28.0%, 72.0%] | 9.4% [3.2%, 24.2%] | 33.3% [21.7%, 47.5%] | 56.2% [28.2%, 71.7%] | 0.000186 |
| gemini-2.5-flash | 37 | 29.7% [17.5%, 45.8%] | 80.0% [49.0%, 94.3%] | 2.69 | 2.69 | 72.7% [43.4%, 90.3%] | 7.7% [2.1%, 24.1%] | 69.2% [50.0%, 83.5%] | 9.1% [1.6%, 37.7%] | 21.6% [11.4%, 37.2%] | 65.0% [31.4%, 83.4%] | 0.000158 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 130 | 42.3% [34.2%, 50.9%] | 90.0% [76.9%, 96.0%] | 2.13 | 1.86 | 65.5% [52.3%, 76.6%] | 5.3% [2.1%, 12.9%] | 54.7% [43.4%, 65.4%] | 10.9% [5.1%, 21.8%] | 33.1% [25.6%, 41.5%] | 60.1% [44.9%, 71.8%] | 6.58e-14 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 48 tasks, 10000 usable): H1 precision − base rate 95% CI [37.1%, 58.1%] → supported; H2 held-back difference 95% CI [40.6%, 76.7%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

25 tasks, 66 patches. ACCEPT rate correct 37.5% [22.9%, 54.7%], wrong 2.9% [0.5%, 14.9%]. Correct/wrong pairs in the same task: concordant 16, discordant 1, ties 24.

### V4 on correct public patches vs gold on the same tasks

55 correct public patches: V4 full pass 89.1% [78.2%, 94.9%]; gold on the same tasks 87.3% [76.0%, 93.7%]. Cells: {'public_pass__gold_pass': 47, 'public_pass__gold_not': 2, 'public_not__gold_pass': 1, 'public_not__gold_not': 5}.

- H3 (all): 0 of 48 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.4% (none).
- H3 (headline_scope): 0 of 48 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.4% (none).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 48 | 3 | 45 | 12 |
| claude-sonnet-4 | 48 | 0 | 48 | 32 |
| gemini-2.5-flash | 48 | 2 | 37 | 11 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-8638, claude-sonnet-4/sphinx-doc__sphinx-9698, gpt-4.1-mini/pytest-dev__pytest-8399.

## Scope: sensitivity: headline minus tasks with generator recall

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 27 | 29.6% [15.9%, 48.5%] | 100.0% [61.0%, 100.0%] | 3.38 | 3.38 | 75.0% [40.9%, 92.9%] | 0.0% [0.0%, 16.8%] | 47.4% [27.3%, 68.3%] | 0.0% [0.0%, 32.4%] | 44.4% [27.6%, 62.7%] | 75.0% [37.0%, 92.9%] | 9.46e-05 |
| claude-sonnet-4 | 28 | 64.3% [45.8%, 79.3%] | 100.0% [67.6%, 100.0%] | 1.56 | 1.56 | 44.4% [24.6%, 66.3%] | 0.0% [0.0%, 27.8%] | 80.0% [49.0%, 94.3%] | 11.1% [3.1%, 32.8%] | 35.7% [20.7%, 54.2%] | 44.4% [10.3%, 66.3%] | 0.0251 |
| gemini-2.5-flash | 17 | 29.4% [13.3%, 53.1%] | 100.0% [51.0%, 100.0%] | 3.40 | 3.40 | 80.0% [37.6%, 96.4%] | 0.0% [0.0%, 24.2%] | 83.3% [55.2%, 95.3%] | 0.0% [0.0%, 43.4%] | 17.6% [6.2%, 41.0%] | 80.0% [31.1%, 96.4%] | 0.0021 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 72 | 43.1% [32.3%, 54.6%] | 100.0% [82.4%, 100.0%] | 2.32 | 2.22 | 58.1% [40.8%, 73.6%] | 0.0% [0.0%, 8.6%] | 65.9% [50.5%, 78.4%] | 6.5% [1.8%, 20.7%] | 34.7% [24.8%, 46.2%] | 58.1% [38.8%, 73.6%] | 4.98e-09 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 28 tasks, 10000 usable): H1 precision − base rate 95% CI [43.2%, 70.6%] → supported; H2 held-back difference 95% CI [34.5%, 77.5%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 27 | 29.6% [15.9%, 48.5%] | 100.0% [51.0%, 100.0%] | 3.38 | 3.38 | 50.0% [21.5%, 78.5%] | 0.0% [0.0%, 16.8%] | 31.6% [15.4%, 54.0%] | 0.0% [0.0%, 32.4%] | 63.0% [44.2%, 78.5%] | 50.0% [16.9%, 78.5%] | 0.00399 |
| claude-sonnet-4 | 28 | 64.3% [45.8%, 79.3%] | 100.0% [56.6%, 100.0%] | 1.56 | 1.56 | 27.8% [12.5%, 50.9%] | 0.0% [0.0%, 27.8%] | 60.0% [31.3%, 83.2%] | 5.6% [1.0%, 25.8%] | 57.1% [39.1%, 73.5%] | 27.8% [-3.9%, 50.9%] | 0.128 |
| gemini-2.5-flash | 17 | 29.4% [13.3%, 53.1%] | 100.0% [34.2%, 100.0%] | 3.40 | 3.40 | 40.0% [11.8%, 76.9%] | 0.0% [0.0%, 24.2%] | 41.7% [19.3%, 68.0%] | 0.0% [0.0%, 43.4%] | 58.8% [36.0%, 78.4%] | 40.0% [2.8%, 76.9%] | 0.0735 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 72 | 43.1% [32.3%, 54.6%] | 100.0% [74.1%, 100.0%] | 2.32 | 2.21 | 35.5% [21.1%, 53.1%] | 0.0% [0.0%, 8.6%] | 41.5% [27.8%, 56.6%] | 3.2% [0.6%, 16.2%] | 59.7% [48.2%, 70.3%] | 35.5% [18.8%, 53.1%] | 2.8e-05 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 28 tasks, 9995 usable): H1 precision − base rate 95% CI [43.2%, 70.6%] → supported; H2 held-back difference 95% CI [14.8%, 55.6%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 27 | 29.6% [15.9%, 48.5%] | 57.1% [25.0%, 84.2%] | 1.93 | 1.93 | 50.0% [21.5%, 78.5%] | 15.8% [5.5%, 37.6%] | 47.4% [27.3%, 68.3%] | 0.0% [0.0%, 32.4%] | 40.7% [24.5%, 59.3%] | 34.2% [-1.6%, 64.5%] | 0.145 |
| claude-sonnet-4 | 28 | 64.3% [45.8%, 79.3%] | 100.0% [61.0%, 100.0%] | 1.56 | 1.56 | 33.3% [16.3%, 56.3%] | 0.0% [0.0%, 27.8%] | 90.0% [59.6%, 98.2%] | 11.1% [3.1%, 32.8%] | 39.3% [23.6%, 57.6%] | 33.3% [0.8%, 56.3%] | 0.0619 |
| gemini-2.5-flash | 17 | 29.4% [13.3%, 53.1%] | 100.0% [34.2%, 100.0%] | 3.40 | 3.40 | 40.0% [11.8%, 76.9%] | 0.0% [0.0%, 24.2%] | 41.7% [19.3%, 68.0%] | 0.0% [0.0%, 43.4%] | 58.8% [36.0%, 78.4%] | 40.0% [2.8%, 76.9%] | 0.0735 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 72 | 43.1% [32.3%, 54.6%] | 80.0% [54.8%, 93.0%] | 1.86 | 1.84 | 38.7% [23.7%, 56.2%] | 7.3% [2.5%, 19.4%] | 56.1% [41.0%, 70.1%] | 6.5% [1.8%, 20.7%] | 44.4% [33.5%, 55.9%] | 31.4% [12.1%, 49.5%] | 0.00246 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 28 tasks, 10000 usable): H1 precision − base rate 95% CI [15.2%, 56.9%] → supported; H2 held-back difference 95% CI [9.5%, 52.7%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 27 | 29.6% [15.9%, 48.5%] | 100.0% [61.0%, 100.0%] | 3.38 | 3.38 | 75.0% [40.9%, 92.9%] | 0.0% [0.0%, 16.8%] | 47.4% [27.3%, 68.3%] | 0.0% [0.0%, 32.4%] | 44.4% [27.6%, 62.7%] | 75.0% [37.0%, 92.9%] | 9.46e-05 |
| claude-sonnet-4 | 28 | 64.3% [45.8%, 79.3%] | 100.0% [74.1%, 100.0%] | 1.56 | 1.56 | 61.1% [38.6%, 79.7%] | 0.0% [0.0%, 27.8%] | 80.0% [49.0%, 94.3%] | 11.1% [3.1%, 32.8%] | 25.0% [12.7%, 43.4%] | 61.1% [25.4%, 79.7%] | 0.00155 |
| gemini-2.5-flash | 17 | 29.4% [13.3%, 53.1%] | 100.0% [51.0%, 100.0%] | 3.40 | 3.40 | 80.0% [37.6%, 96.4%] | 0.0% [0.0%, 24.2%] | 83.3% [55.2%, 95.3%] | 0.0% [0.0%, 43.4%] | 17.6% [6.2%, 41.0%] | 80.0% [31.1%, 96.4%] | 0.0021 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 72 | 43.1% [32.3%, 54.6%] | 100.0% [84.5%, 100.0%] | 2.32 | 2.09 | 67.7% [50.1%, 81.4%] | 0.0% [0.0%, 8.6%] | 65.9% [50.5%, 78.4%] | 6.5% [1.8%, 20.7%] | 30.6% [21.1%, 42.0%] | 67.7% [48.2%, 81.4%] | 5.74e-11 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 28 tasks, 10000 usable): H1 precision − base rate 95% CI [43.2%, 70.6%] → supported; H2 held-back difference 95% CI [45.2%, 86.2%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 27 | 29.6% [15.9%, 48.5%] | 100.0% [61.0%, 100.0%] | 3.38 | 3.38 | 75.0% [40.9%, 92.9%] | 0.0% [0.0%, 16.8%] | 42.1% [23.1%, 63.7%] | 0.0% [0.0%, 32.4%] | 48.1% [30.7%, 66.0%] | 75.0% [37.0%, 92.9%] | 9.46e-05 |
| claude-sonnet-4 | 28 | 64.3% [45.8%, 79.3%] | 100.0% [67.6%, 100.0%] | 1.56 | 1.56 | 44.4% [24.6%, 66.3%] | 0.0% [0.0%, 27.8%] | 80.0% [49.0%, 94.3%] | 5.6% [1.0%, 25.8%] | 39.3% [23.6%, 57.6%] | 44.4% [10.3%, 66.3%] | 0.0251 |
| gemini-2.5-flash | 17 | 29.4% [13.3%, 53.1%] | 80.0% [37.6%, 96.4%] | 2.72 | 2.72 | 80.0% [37.6%, 96.4%] | 8.3% [1.5%, 35.4%] | 75.0% [46.8%, 91.1%] | 0.0% [0.0%, 43.4%] | 17.6% [6.2%, 41.0%] | 71.7% [21.3%, 89.4%] | 0.00986 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 72 | 43.1% [32.3%, 54.6%] | 94.7% [75.4%, 99.1%] | 2.20 | 2.15 | 58.1% [40.8%, 73.6%] | 2.4% [0.4%, 12.6%] | 61.0% [45.7%, 74.3%] | 3.2% [0.6%, 16.2%] | 37.5% [27.2%, 49.0%] | 55.6% [35.6%, 71.3%] | 7.3e-08 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 28 tasks, 10000 usable): H1 precision − base rate 95% CI [38.5%, 65.2%] → supported; H2 held-back difference 95% CI [31.7%, 75.8%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 27 | 29.6% [15.9%, 48.5%] | 100.0% [61.0%, 100.0%] | 3.38 | 3.38 | 75.0% [40.9%, 92.9%] | 0.0% [0.0%, 16.8%] | 42.1% [23.1%, 63.7%] | 0.0% [0.0%, 32.4%] | 48.1% [30.7%, 66.0%] | 75.0% [37.0%, 92.9%] | 9.46e-05 |
| claude-sonnet-4 | 28 | 64.3% [45.8%, 79.3%] | 100.0% [75.8%, 100.0%] | 1.56 | 1.56 | 66.7% [43.7%, 83.7%] | 0.0% [0.0%, 27.8%] | 80.0% [49.0%, 94.3%] | 5.6% [1.0%, 25.8%] | 25.0% [12.7%, 43.4%] | 66.7% [30.7%, 83.7%] | 0.000883 |
| gemini-2.5-flash | 17 | 29.4% [13.3%, 53.1%] | 80.0% [37.6%, 96.4%] | 2.72 | 2.72 | 80.0% [37.6%, 96.4%] | 8.3% [1.5%, 35.4%] | 75.0% [46.8%, 91.1%] | 0.0% [0.0%, 43.4%] | 17.6% [6.2%, 41.0%] | 71.7% [21.3%, 89.4%] | 0.00986 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 72 | 43.1% [32.3%, 54.6%] | 95.7% [79.0%, 99.2%] | 2.22 | 2.01 | 71.0% [53.4%, 83.9%] | 2.4% [0.4%, 12.6%] | 61.0% [45.7%, 74.3%] | 3.2% [0.6%, 16.2%] | 31.9% [22.3%, 43.4%] | 68.5% [48.2%, 81.6%] | 2.14e-10 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 28 tasks, 10000 usable): H1 precision − base rate 95% CI [39.9%, 65.4%] → supported; H2 held-back difference 95% CI [46.2%, 86.8%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

15 tasks, 37 patches. ACCEPT rate correct 36.8% [19.1%, 59.0%], wrong 0.0% [0.0%, 17.6%]. Correct/wrong pairs in the same task: concordant 7, discordant 0, ties 15.

### V4 on correct public patches vs gold on the same tasks

31 correct public patches: V4 full pass 90.3% [75.1%, 96.7%]; gold on the same tasks 83.9% [67.4%, 92.9%]. Cells: {'public_pass__gold_pass': 26, 'public_pass__gold_not': 2, 'public_not__gold_pass': 0, 'public_not__gold_not': 3}.

- H3 (all): 0 of 48 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.4% (none).
- H3 (headline_scope): 0 of 28 gold patches REJECTed, point 0.0%, Wilson 95% upper 12.1% (none).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 28 | 1 | 27 | 8 |
| claude-sonnet-4 | 28 | 0 | 28 | 18 |
| gemini-2.5-flash | 25 | 2 | 17 | 5 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-8638.

## Label checks

- gpt-4.1-mini: no label 2 (django__django-13513, sympy__sympy-13031); official patch sha256 mismatch 0 (none).
- claude-sonnet-4: no label 0 (none); official patch sha256 mismatch 0 (none).
- gemini-2.5-flash: no label 10 (astropy__astropy-14995, django__django-11734, django__django-13363, django__django-13551, django__django-15022, django__django-16493, matplotlib__matplotlib-20859, pytest-dev__pytest-7571, sphinx-doc__sphinx-9711, sympy__sympy-20801); official patch sha256 mismatch 0 (none).
