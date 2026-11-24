# Study v1.5 batch 1 results (gpt-4.1-mini labels from our grader, B14)

## Scope: headline (batch, minus headline exclusions)

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 55 | 18.2% [10.2%, 30.3%] | 60.0% [31.3%, 83.2%] | 3.30 | 3.30 | 60.0% [31.3%, 83.2%] | 8.9% [3.5%, 20.7%] | 51.1% [37.0%, 65.0%] | 0.0% [0.0%, 27.8%] | 40.0% [28.1%, 53.2%] | 51.1% [20.0%, 74.9%] | 0.00113 |
| claude-sonnet-4 | 57 | 66.7% [53.7%, 77.5%] | 76.9% [49.7%, 91.8%] | 1.15 | 1.15 | 26.3% [15.0%, 42.0%] | 15.8% [5.5%, 37.6%] | 36.8% [19.1%, 59.0%] | 13.2% [5.8%, 27.3%] | 56.1% [43.3%, 68.2%] | 10.5% [-14.0%, 29.3%] | 0.51 |
| gemini-2.5-flash | 35 | 34.3% [20.8%, 50.8%] | 100.0% [61.0%, 100.0%] | 2.92 | 2.92 | 50.0% [25.4%, 74.6%] | 0.0% [0.0%, 14.3%] | 56.5% [36.8%, 74.4%] | 25.0% [8.9%, 53.2%] | 37.1% [23.2%, 53.7%] | 50.0% [21.5%, 74.6%] | 0.000569 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 147 | 40.8% [33.2%, 48.9%] | 75.9% [57.9%, 87.8%] | 1.86 | 1.75 | 36.7% [25.6%, 49.3%] | 8.0% [4.0%, 15.7%] | 49.4% [39.2%, 59.7%] | 13.3% [6.9%, 24.2%] | 45.6% [37.7%, 53.6%] | 28.6% [15.2%, 41.9%] | 3.36e-05 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 57 tasks, 10000 usable): H1 precision − base rate 95% CI [17.6%, 51.1%] → supported; H2 held-back difference 95% CI [12.6%, 44.1%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 55 | 18.2% [10.2%, 30.3%] | 66.7% [20.8%, 93.9%] | 3.67 | 3.67 | 20.0% [5.7%, 51.0%] | 2.2% [0.4%, 11.6%] | 20.0% [10.9%, 33.8%] | 0.0% [0.0%, 27.8%] | 78.2% [65.6%, 87.1%] | 17.8% [0.7%, 48.8%] | 0.0818 |
| claude-sonnet-4 | 57 | 66.7% [53.7%, 77.5%] | 75.0% [40.9%, 92.9%] | 1.12 | 1.12 | 15.8% [7.4%, 30.4%] | 10.5% [2.9%, 31.4%] | 31.6% [15.4%, 54.0%] | 7.9% [2.7%, 20.8%] | 70.2% [57.3%, 80.5%] | 5.3% [-17.2%, 21.7%] | 0.706 |
| gemini-2.5-flash | 35 | 34.3% [20.8%, 50.8%] | 100.0% [34.2%, 100.0%] | 2.92 | 2.92 | 16.7% [4.7%, 44.8%] | 0.0% [0.0%, 14.3%] | 30.4% [15.6%, 50.9%] | 16.7% [4.7%, 44.8%] | 68.6% [52.0%, 81.4%] | 16.7% [-2.0%, 44.8%] | 0.111 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 147 | 40.8% [33.2%, 48.9%] | 76.9% [49.7%, 91.8%] | 1.88 | 1.52 | 16.7% [9.3%, 28.0%] | 3.4% [1.2%, 9.7%] | 25.3% [17.3%, 35.3%] | 8.3% [3.6%, 18.1%] | 72.8% [65.1%, 79.3%] | 13.2% [3.6%, 24.8%] | 0.00749 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 57 tasks, 10000 usable): H1 precision − base rate 95% CI [13.0%, 58.1%] → supported; H2 held-back difference 95% CI [3.5%, 24.6%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 55 | 18.2% [10.2%, 30.3%] | 50.0% [18.8%, 81.2%] | 2.75 | 2.75 | 30.0% [10.8%, 60.3%] | 6.7% [2.3%, 17.9%] | 26.7% [16.0%, 41.0%] | 10.0% [1.8%, 40.4%] | 65.5% [52.3%, 76.6%] | 23.3% [1.1%, 54.0%] | 0.0663 |
| claude-sonnet-4 | 57 | 66.7% [53.7%, 77.5%] | 58.3% [32.0%, 80.7%] | 0.88 | 0.88 | 18.4% [9.2%, 33.4%] | 26.3% [11.8%, 48.8%] | 42.1% [23.1%, 63.7%] | 13.2% [5.8%, 27.3%] | 56.1% [43.3%, 68.2%] | -7.9% [-32.2%, 13.0%] | 0.509 |
| gemini-2.5-flash | 35 | 34.3% [20.8%, 50.8%] | 62.5% [30.6%, 86.3%] | 1.82 | 1.82 | 41.7% [19.3%, 68.0%] | 13.0% [4.5%, 32.1%] | 43.5% [25.6%, 63.2%] | 16.7% [4.7%, 44.8%] | 42.9% [28.0%, 59.1%] | 28.6% [-0.8%, 56.3%] | 0.0912 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 147 | 40.8% [33.2%, 48.9%] | 57.7% [38.9%, 74.5%] | 1.41 | 1.27 | 25.0% [15.8%, 37.2%] | 12.6% [7.2%, 21.2%] | 34.5% [25.3%, 44.9%] | 13.3% [6.9%, 24.2%] | 56.5% [48.4%, 64.2%] | 12.4% [-0.3%, 25.7%] | 0.0774 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 57 tasks, 10000 usable): H1 precision − base rate 95% CI [-1.4%, 32.6%] → not supported; H2 held-back difference 95% CI [-0.9%, 26.1%] → not supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 55 | 18.2% [10.2%, 30.3%] | 60.0% [31.3%, 83.2%] | 3.30 | 3.30 | 60.0% [31.3%, 83.2%] | 8.9% [3.5%, 20.7%] | 51.1% [37.0%, 65.0%] | 0.0% [0.0%, 27.8%] | 40.0% [28.1%, 53.2%] | 51.1% [20.0%, 74.9%] | 0.00113 |
| claude-sonnet-4 | 57 | 66.7% [53.7%, 77.5%] | 84.6% [66.5%, 93.8%] | 1.27 | 1.27 | 57.9% [42.2%, 72.1%] | 21.1% [8.5%, 43.3%] | 36.8% [19.1%, 59.0%] | 13.2% [5.8%, 27.3%] | 33.3% [22.5%, 46.3%] | 36.8% [9.6%, 55.8%] | 0.0114 |
| gemini-2.5-flash | 35 | 34.3% [20.8%, 50.8%] | 100.0% [61.0%, 100.0%] | 2.92 | 2.92 | 50.0% [25.4%, 74.6%] | 0.0% [0.0%, 14.3%] | 56.5% [36.8%, 74.4%] | 25.0% [8.9%, 53.2%] | 37.1% [23.2%, 53.7%] | 50.0% [21.5%, 74.6%] | 0.000569 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 147 | 40.8% [33.2%, 48.9%] | 81.0% [66.7%, 90.0%] | 1.98 | 1.60 | 56.7% [44.1%, 68.4%] | 9.2% [4.7%, 17.1%] | 49.4% [39.2%, 59.7%] | 13.3% [6.9%, 24.2%] | 36.7% [29.4%, 44.8%] | 47.5% [32.6%, 60.1%] | 4.49e-10 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 57 tasks, 10000 usable): H1 precision − base rate 95% CI [27.3%, 52.8%] → supported; H2 held-back difference 95% CI [30.7%, 63.1%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 55 | 18.2% [10.2%, 30.3%] | 60.0% [31.3%, 83.2%] | 3.30 | 3.30 | 60.0% [31.3%, 83.2%] | 8.9% [3.5%, 20.7%] | 46.7% [32.9%, 60.9%] | 0.0% [0.0%, 27.8%] | 43.6% [31.4%, 56.7%] | 51.1% [20.0%, 74.9%] | 0.00113 |
| claude-sonnet-4 | 57 | 66.7% [53.7%, 77.5%] | 78.6% [52.4%, 92.4%] | 1.18 | 1.18 | 28.9% [17.0%, 44.8%] | 15.8% [5.5%, 37.6%] | 26.3% [11.8%, 48.8%] | 10.5% [4.2%, 24.1%] | 59.6% [46.7%, 71.4%] | 13.2% [-11.7%, 32.0%] | 0.343 |
| gemini-2.5-flash | 35 | 34.3% [20.8%, 50.8%] | 100.0% [64.6%, 100.0%] | 2.92 | 2.92 | 58.3% [32.0%, 80.7%] | 0.0% [0.0%, 14.3%] | 52.2% [33.0%, 70.8%] | 16.7% [4.7%, 44.8%] | 40.0% [25.6%, 56.4%] | 58.3% [28.3%, 80.7%] | 0.000118 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 147 | 40.8% [33.2%, 48.9%] | 77.4% [60.2%, 88.6%] | 1.90 | 1.77 | 40.0% [28.6%, 52.6%] | 8.0% [4.0%, 15.7%] | 43.7% [33.7%, 54.1%] | 10.0% [4.7%, 20.1%] | 49.0% [41.0%, 57.0%] | 32.0% [18.2%, 45.2%] | 6.97e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 57 tasks, 10000 usable): H1 precision − base rate 95% CI [20.2%, 51.7%] → supported; H2 held-back difference 95% CI [15.6%, 47.6%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 55 | 18.2% [10.2%, 30.3%] | 60.0% [31.3%, 83.2%] | 3.30 | 3.30 | 60.0% [31.3%, 83.2%] | 8.9% [3.5%, 20.7%] | 46.7% [32.9%, 60.9%] | 0.0% [0.0%, 27.8%] | 43.6% [31.4%, 56.7%] | 51.1% [20.0%, 74.9%] | 0.00113 |
| claude-sonnet-4 | 57 | 66.7% [53.7%, 77.5%] | 85.2% [67.5%, 94.1%] | 1.28 | 1.28 | 60.5% [44.7%, 74.4%] | 21.1% [8.5%, 43.3%] | 26.3% [11.8%, 48.8%] | 10.5% [4.2%, 24.1%] | 36.8% [25.5%, 49.8%] | 39.5% [12.2%, 58.2%] | 0.00585 |
| gemini-2.5-flash | 35 | 34.3% [20.8%, 50.8%] | 100.0% [64.6%, 100.0%] | 2.92 | 2.92 | 58.3% [32.0%, 80.7%] | 0.0% [0.0%, 14.3%] | 52.2% [33.0%, 70.8%] | 16.7% [4.7%, 44.8%] | 40.0% [25.6%, 56.4%] | 58.3% [28.3%, 80.7%] | 0.000118 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 147 | 40.8% [33.2%, 48.9%] | 81.8% [68.0%, 90.5%] | 2.00 | 1.62 | 60.0% [47.4%, 71.4%] | 9.2% [4.7%, 17.1%] | 43.7% [33.7%, 54.1%] | 10.0% [4.7%, 20.1%] | 40.1% [32.6%, 48.2%] | 50.8% [35.9%, 63.1%] | 4.65e-11 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 57 tasks, 10000 usable): H1 precision − base rate 95% CI [28.5%, 53.2%] → supported; H2 held-back difference 95% CI [33.9%, 66.3%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

29 tasks, 77 patches. ACCEPT rate correct 27.0% [15.4%, 43.0%], wrong 7.5% [2.6%, 19.9%]. Correct/wrong pairs in the same task: concordant 9, discordant 3, ties 36.

### V4 on correct public patches vs gold on the same tasks

60 correct public patches: V4 full pass 81.7% [70.1%, 89.4%]; gold on the same tasks 80.0% [68.2%, 88.2%]. Cells: {'public_pass__gold_pass': 46, 'public_pass__gold_not': 3, 'public_not__gold_pass': 2, 'public_not__gold_not': 9}.

- H3 (all): 1 of 60 gold patches REJECTed, point 1.7%, Wilson 95% upper 8.9% (sympy__sympy-14248).
- H3 (headline_scope): 1 of 57 gold patches REJECTed, point 1.8%, Wilson 95% upper 9.3% (sympy__sympy-14248).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 57 | 0 | 55 | 10 |
| claude-sonnet-4 | 57 | 0 | 57 | 38 |
| gemini-2.5-flash | 45 | 3 | 35 | 12 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-8035, claude-sonnet-4/sphinx-doc__sphinx-9591, gemini-2.5-flash/sphinx-doc__sphinx-9591, gpt-4.1-mini/sphinx-doc__sphinx-8035, gpt-4.1-mini/sphinx-doc__sphinx-9658.

## Scope: sensitivity: all tasks (no exclusions)

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 58 | 19.0% [10.9%, 30.9%] | 63.6% [35.4%, 84.8%] | 3.36 | 3.36 | 63.6% [35.4%, 84.8%] | 8.5% [3.4%, 19.9%] | 53.2% [39.2%, 66.7%] | 0.0% [0.0%, 25.9%] | 37.9% [26.6%, 50.8%] | 55.1% [24.6%, 76.9%] | 0.000271 |
| claude-sonnet-4 | 60 | 68.3% [55.8%, 78.7%] | 78.6% [52.4%, 92.4%] | 1.15 | 1.15 | 26.8% [15.7%, 41.9%] | 15.8% [5.5%, 37.6%] | 36.8% [19.1%, 59.0%] | 14.6% [6.9%, 28.4%] | 55.0% [42.5%, 66.9%] | 11.0% [-13.4%, 29.3%] | 0.515 |
| gemini-2.5-flash | 50 | 26.0% [15.9%, 39.6%] | 100.0% [61.0%, 100.0%] | 3.85 | 3.85 | 46.2% [23.2%, 70.9%] | 0.0% [0.0%, 9.4%] | 70.3% [54.2%, 82.5%] | 23.1% [8.2%, 50.3%] | 30.0% [19.1%, 43.8%] | 46.2% [21.4%, 70.9%] | 0.000108 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 168 | 38.7% [31.7%, 46.2%] | 77.4% [60.2%, 88.6%] | 2.00 | 1.82 | 36.9% [26.2%, 49.1%] | 6.8% [3.3%, 13.4%] | 56.3% [46.7%, 65.5%] | 13.8% [7.5%, 24.3%] | 41.7% [34.5%, 49.2%] | 30.1% [17.6%, 42.8%] | 2.37e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 60 tasks, 10000 usable): H1 precision − base rate 95% CI [22.1%, 53.9%] → supported; H2 held-back difference 95% CI [15.0%, 44.9%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 58 | 19.0% [10.9%, 30.9%] | 75.0% [30.1%, 95.4%] | 3.95 | 3.95 | 27.3% [9.7%, 56.6%] | 2.1% [0.4%, 11.1%] | 21.3% [12.0%, 34.9%] | 0.0% [0.0%, 25.9%] | 75.9% [63.5%, 85.0%] | 25.1% [5.4%, 54.5%] | 0.0191 |
| claude-sonnet-4 | 60 | 68.3% [55.8%, 78.7%] | 75.0% [40.9%, 92.9%] | 1.10 | 1.10 | 14.6% [6.9%, 28.4%] | 10.5% [2.9%, 31.4%] | 31.6% [15.4%, 54.0%] | 9.8% [3.9%, 22.5%] | 70.0% [57.5%, 80.1%] | 4.1% [-18.2%, 19.9%] | 1 |
| gemini-2.5-flash | 50 | 26.0% [15.9%, 39.6%] | 100.0% [34.2%, 100.0%] | 3.85 | 3.85 | 15.4% [4.3%, 42.2%] | 0.0% [0.0%, 9.4%] | 54.1% [38.4%, 69.0%] | 15.4% [4.3%, 42.2%] | 52.0% [38.5%, 65.2%] | 15.4% [0.9%, 42.2%] | 0.0637 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 168 | 38.7% [31.7%, 46.2%] | 78.6% [52.4%, 92.4%] | 2.03 | 1.63 | 16.9% [9.7%, 27.8%] | 2.9% [1.0%, 8.2%] | 35.0% [26.4%, 44.5%] | 9.2% [4.3%, 18.7%] | 66.7% [59.2%, 73.4%] | 14.0% [5.1%, 25.1%] | 0.00267 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 60 tasks, 10000 usable): H1 precision − base rate 95% CI [18.1%, 60.0%] → supported; H2 held-back difference 95% CI [4.7%, 24.2%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 58 | 19.0% [10.9%, 30.9%] | 57.1% [25.0%, 84.2%] | 3.01 | 3.01 | 36.4% [15.2%, 64.6%] | 6.4% [2.2%, 17.2%] | 27.7% [16.9%, 41.8%] | 9.1% [1.6%, 37.7%] | 63.8% [50.9%, 74.9%] | 30.0% [6.2%, 58.5%] | 0.0195 |
| claude-sonnet-4 | 60 | 68.3% [55.8%, 78.7%] | 61.5% [35.5%, 82.3%] | 0.90 | 0.90 | 19.5% [10.2%, 34.0%] | 26.3% [11.8%, 48.8%] | 42.1% [23.1%, 63.7%] | 14.6% [6.9%, 28.4%] | 55.0% [42.5%, 66.9%] | -6.8% [-31.1%, 13.7%] | 0.737 |
| gemini-2.5-flash | 50 | 26.0% [15.9%, 39.6%] | 55.6% [26.7%, 81.1%] | 2.14 | 2.14 | 38.5% [17.7%, 64.5%] | 10.8% [4.3%, 24.7%] | 62.2% [46.1%, 75.9%] | 15.4% [4.3%, 42.2%] | 32.0% [20.8%, 45.8%] | 27.7% [2.7%, 54.5%] | 0.0397 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 168 | 38.7% [31.7%, 46.2%] | 58.6% [40.7%, 74.5%] | 1.52 | 1.35 | 26.2% [17.0%, 38.0%] | 11.7% [6.8%, 19.3%] | 42.7% [33.6%, 52.4%] | 13.8% [7.5%, 24.3%] | 51.2% [43.7%, 58.6%] | 14.5% [2.6%, 27.3%] | 0.0208 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 60 tasks, 10000 usable): H1 precision − base rate 95% CI [3.3%, 34.8%] → supported; H2 held-back difference 95% CI [2.1%, 27.1%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 58 | 19.0% [10.9%, 30.9%] | 63.6% [35.4%, 84.8%] | 3.36 | 3.36 | 63.6% [35.4%, 84.8%] | 8.5% [3.4%, 19.9%] | 53.2% [39.2%, 66.7%] | 0.0% [0.0%, 25.9%] | 37.9% [26.6%, 50.8%] | 55.1% [24.6%, 76.9%] | 0.000271 |
| claude-sonnet-4 | 60 | 68.3% [55.8%, 78.7%] | 85.7% [68.5%, 94.3%] | 1.25 | 1.25 | 58.5% [43.4%, 72.2%] | 21.1% [8.5%, 43.3%] | 36.8% [19.1%, 59.0%] | 14.6% [6.9%, 28.4%] | 31.7% [21.3%, 44.2%] | 37.5% [10.5%, 56.1%] | 0.0114 |
| gemini-2.5-flash | 50 | 26.0% [15.9%, 39.6%] | 100.0% [64.6%, 100.0%] | 3.85 | 3.85 | 53.8% [29.1%, 76.8%] | 0.0% [0.0%, 9.4%] | 70.3% [54.2%, 82.5%] | 23.1% [8.2%, 50.3%] | 28.0% [17.5%, 41.7%] | 53.8% [27.4%, 76.8%] | 1.72e-05 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 168 | 38.7% [31.7%, 46.2%] | 82.6% [69.3%, 90.9%] | 2.14 | 1.65 | 58.5% [46.3%, 69.6%] | 7.8% [4.0%, 14.6%] | 56.3% [46.7%, 65.5%] | 13.8% [7.5%, 24.3%] | 32.7% [26.1%, 40.2%] | 50.7% [36.8%, 62.5%] | 7.85e-13 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 60 tasks, 10000 usable): H1 precision − base rate 95% CI [32.2%, 55.0%] → supported; H2 held-back difference 95% CI [34.3%, 65.6%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 58 | 19.0% [10.9%, 30.9%] | 63.6% [35.4%, 84.8%] | 3.36 | 3.36 | 63.6% [35.4%, 84.8%] | 8.5% [3.4%, 19.9%] | 46.8% [33.3%, 60.8%] | 0.0% [0.0%, 25.9%] | 43.1% [31.2%, 55.9%] | 55.1% [24.6%, 76.9%] | 0.000271 |
| claude-sonnet-4 | 60 | 68.3% [55.8%, 78.7%] | 81.2% [57.0%, 93.4%] | 1.19 | 1.19 | 31.7% [19.6%, 47.0%] | 15.8% [5.5%, 37.6%] | 26.3% [11.8%, 48.8%] | 9.8% [3.9%, 22.5%] | 58.3% [45.7%, 69.9%] | 15.9% [-9.0%, 34.3%] | 0.228 |
| gemini-2.5-flash | 50 | 26.0% [15.9%, 39.6%] | 100.0% [64.6%, 100.0%] | 3.85 | 3.85 | 53.8% [29.1%, 76.8%] | 0.0% [0.0%, 9.4%] | 67.6% [51.5%, 80.4%] | 15.4% [4.3%, 42.2%] | 32.0% [20.8%, 45.8%] | 53.8% [27.4%, 76.8%] | 1.72e-05 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 168 | 38.7% [31.7%, 46.2%] | 79.4% [63.2%, 89.7%] | 2.05 | 1.82 | 41.5% [30.4%, 53.7%] | 6.8% [3.3%, 13.4%] | 50.5% [41.0%, 59.9%] | 9.2% [4.3%, 18.7%] | 45.2% [37.9%, 52.8%] | 34.7% [21.8%, 47.4%] | 7.85e-08 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 60 tasks, 10000 usable): H1 precision − base rate 95% CI [25.7%, 54.9%] → supported; H2 held-back difference 95% CI [19.2%, 49.6%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 58 | 19.0% [10.9%, 30.9%] | 63.6% [35.4%, 84.8%] | 3.36 | 3.36 | 63.6% [35.4%, 84.8%] | 8.5% [3.4%, 19.9%] | 46.8% [33.3%, 60.8%] | 0.0% [0.0%, 25.9%] | 43.1% [31.2%, 55.9%] | 55.1% [24.6%, 76.9%] | 0.000271 |
| claude-sonnet-4 | 60 | 68.3% [55.8%, 78.7%] | 86.7% [70.3%, 94.7%] | 1.27 | 1.27 | 63.4% [48.1%, 76.4%] | 21.1% [8.5%, 43.3%] | 26.3% [11.8%, 48.8%] | 9.8% [3.9%, 22.5%] | 35.0% [24.2%, 47.6%] | 42.4% [15.3%, 60.4%] | 0.00479 |
| gemini-2.5-flash | 50 | 26.0% [15.9%, 39.6%] | 100.0% [67.6%, 100.0%] | 3.85 | 3.85 | 61.5% [35.5%, 82.3%] | 0.0% [0.0%, 9.4%] | 67.6% [51.5%, 80.4%] | 15.4% [4.3%, 42.2%] | 30.0% [19.1%, 43.8%] | 61.5% [33.9%, 82.3%] | 2.4e-06 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 168 | 38.7% [31.7%, 46.2%] | 83.7% [71.0%, 91.5%] | 2.16 | 1.66 | 63.1% [50.9%, 73.8%] | 7.8% [4.0%, 14.6%] | 50.5% [41.0%, 59.9%] | 9.2% [4.3%, 18.7%] | 36.3% [29.4%, 43.8%] | 55.3% [41.4%, 66.7%] | 1.33e-14 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 60 tasks, 10000 usable): H1 precision − base rate 95% CI [33.8%, 55.7%] → supported; H2 held-back difference 95% CI [38.7%, 69.7%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

33 tasks, 94 patches. ACCEPT rate correct 30.2% [18.6%, 45.1%], wrong 5.9% [2.0%, 15.9%]. Correct/wrong pairs in the same task: concordant 17, discordant 3, ties 41.

### V4 on correct public patches vs gold on the same tasks

65 correct public patches: V4 full pass 83.1% [72.2%, 90.3%]; gold on the same tasks 81.5% [70.4%, 89.1%]. Cells: {'public_pass__gold_pass': 51, 'public_pass__gold_not': 3, 'public_not__gold_pass': 2, 'public_not__gold_not': 9}.

- H3 (all): 1 of 60 gold patches REJECTed, point 1.7%, Wilson 95% upper 8.9% (sympy__sympy-14248).
- H3 (headline_scope): 1 of 60 gold patches REJECTed, point 1.7%, Wilson 95% upper 8.9% (sympy__sympy-14248).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 60 | 0 | 58 | 11 |
| claude-sonnet-4 | 60 | 0 | 60 | 41 |
| gemini-2.5-flash | 60 | 3 | 50 | 13 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-8035, claude-sonnet-4/sphinx-doc__sphinx-9591, gemini-2.5-flash/sphinx-doc__sphinx-9591, gpt-4.1-mini/sphinx-doc__sphinx-8035, gpt-4.1-mini/sphinx-doc__sphinx-9658.

## Scope: sensitivity: headline minus tasks with generator recall

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 35 | 25.7% [14.2%, 42.1%] | 62.5% [30.6%, 86.3%] | 2.43 | 2.43 | 55.6% [26.7%, 81.1%] | 11.5% [4.0%, 29.0%] | 57.7% [38.9%, 74.5%] | 0.0% [0.0%, 29.9%] | 34.3% [20.8%, 50.8%] | 44.0% [10.3%, 70.7%] | 0.0151 |
| claude-sonnet-4 | 36 | 63.9% [47.6%, 77.5%] | 87.5% [52.9%, 97.8%] | 1.37 | 1.37 | 30.4% [15.6%, 50.9%] | 7.7% [1.4%, 33.3%] | 53.8% [29.1%, 76.8%] | 4.3% [0.8%, 21.0%] | 55.6% [39.6%, 70.5%] | 22.7% [-6.9%, 44.1%] | 0.213 |
| gemini-2.5-flash | 20 | 30.0% [14.5%, 51.9%] | 100.0% [51.0%, 100.0%] | 3.33 | 3.33 | 66.7% [30.0%, 90.3%] | 0.0% [0.0%, 21.5%] | 50.0% [26.8%, 73.2%] | 16.7% [3.0%, 56.4%] | 40.0% [21.9%, 61.3%] | 66.7% [24.1%, 90.3%] | 0.0031 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 91 | 41.8% [32.2%, 52.0%] | 80.0% [58.4%, 91.9%] | 1.92 | 1.91 | 42.1% [27.9%, 57.8%] | 7.5% [3.0%, 17.9%] | 54.7% [41.5%, 67.3%] | 5.3% [1.5%, 17.3%] | 44.0% [34.2%, 54.2%] | 34.6% [17.0%, 50.9%] | 0.000183 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 36 tasks, 10000 usable): H1 precision − base rate 95% CI [18.2%, 59.3%] → supported; H2 held-back difference 95% CI [14.5%, 54.2%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 35 | 25.7% [14.2%, 42.1%] | 66.7% [20.8%, 93.9%] | 2.59 | 2.59 | 22.2% [6.3%, 54.7%] | 3.8% [0.7%, 18.9%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 29.9%] | 71.4% [54.9%, 83.7%] | 18.4% [-3.5%, 51.0%] | 0.156 |
| claude-sonnet-4 | 36 | 63.9% [47.6%, 77.5%] | 100.0% [56.6%, 100.0%] | 1.57 | 1.57 | 21.7% [9.7%, 41.9%] | 0.0% [0.0%, 22.8%] | 46.2% [23.2%, 70.9%] | 4.3% [0.8%, 21.0%] | 66.7% [50.3%, 79.8%] | 21.7% [-4.1%, 41.9%] | 0.136 |
| gemini-2.5-flash | 20 | 30.0% [14.5%, 51.9%] | 100.0% [34.2%, 100.0%] | 3.33 | 3.33 | 33.3% [9.7%, 70.0%] | 0.0% [0.0%, 21.5%] | 35.7% [16.3%, 61.2%] | 0.0% [0.0%, 39.0%] | 65.0% [43.3%, 81.9%] | 33.3% [1.3%, 70.0%] | 0.0789 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 91 | 41.8% [32.2%, 52.0%] | 90.0% [59.6%, 98.2%] | 2.16 | 1.97 | 23.7% [13.0%, 39.2%] | 1.9% [0.3%, 9.9%] | 34.0% [22.7%, 47.4%] | 2.6% [0.5%, 13.5%] | 68.1% [58.0%, 76.8%] | 21.8% [8.4%, 37.4%] | 0.00142 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 36 tasks, 10000 usable): H1 precision − base rate 95% CI [27.8%, 68.1%] → supported; H2 held-back difference 95% CI [8.6%, 38.1%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 35 | 25.7% [14.2%, 42.1%] | 75.0% [30.1%, 95.4%] | 2.92 | 2.92 | 33.3% [12.1%, 64.6%] | 3.8% [0.7%, 18.9%] | 34.6% [19.4%, 53.8%] | 11.1% [2.0%, 43.5%] | 60.0% [43.6%, 74.4%] | 29.5% [3.4%, 60.9%] | 0.0441 |
| claude-sonnet-4 | 36 | 63.9% [47.6%, 77.5%] | 85.7% [48.7%, 97.4%] | 1.34 | 1.34 | 26.1% [12.5%, 46.5%] | 7.7% [1.4%, 33.3%] | 61.5% [35.5%, 82.3%] | 13.0% [4.5%, 32.1%] | 50.0% [34.5%, 65.5%] | 18.4% [-10.6%, 39.7%] | 0.382 |
| gemini-2.5-flash | 20 | 30.0% [14.5%, 51.9%] | 57.1% [25.0%, 84.2%] | 1.90 | 1.90 | 66.7% [30.0%, 90.3%] | 21.4% [7.6%, 47.6%] | 50.0% [26.8%, 73.2%] | 0.0% [0.0%, 39.0%] | 30.0% [14.5%, 51.9%] | 45.2% [0.2%, 72.7%] | 0.122 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 91 | 41.8% [32.2%, 52.0%] | 72.2% [49.1%, 87.5%] | 1.73 | 1.71 | 34.2% [21.2%, 50.1%] | 9.4% [4.1%, 20.3%] | 45.3% [32.7%, 58.5%] | 10.5% [4.2%, 24.1%] | 49.5% [39.4%, 59.5%] | 24.8% [7.9%, 41.5%] | 0.00645 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 36 tasks, 10000 usable): H1 precision − base rate 95% CI [9.7%, 48.9%] → supported; H2 held-back difference 95% CI [6.7%, 43.9%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 35 | 25.7% [14.2%, 42.1%] | 62.5% [30.6%, 86.3%] | 2.43 | 2.43 | 55.6% [26.7%, 81.1%] | 11.5% [4.0%, 29.0%] | 57.7% [38.9%, 74.5%] | 0.0% [0.0%, 29.9%] | 34.3% [20.8%, 50.8%] | 44.0% [10.3%, 70.7%] | 0.0151 |
| claude-sonnet-4 | 36 | 63.9% [47.6%, 77.5%] | 88.9% [67.2%, 96.9%] | 1.39 | 1.39 | 69.6% [49.1%, 84.4%] | 15.4% [4.3%, 42.2%] | 53.8% [29.1%, 76.8%] | 4.3% [0.8%, 21.0%] | 27.8% [15.8%, 44.0%] | 54.2% [20.4%, 72.7%] | 0.00451 |
| gemini-2.5-flash | 20 | 30.0% [14.5%, 51.9%] | 100.0% [51.0%, 100.0%] | 3.33 | 3.33 | 66.7% [30.0%, 90.3%] | 0.0% [0.0%, 21.5%] | 50.0% [26.8%, 73.2%] | 16.7% [3.0%, 56.4%] | 40.0% [21.9%, 61.3%] | 66.7% [24.1%, 90.3%] | 0.0031 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 91 | 41.8% [32.2%, 52.0%] | 83.3% [66.4%, 92.7%] | 2.00 | 1.69 | 65.8% [49.9%, 78.8%] | 9.4% [4.1%, 20.3%] | 54.7% [41.5%, 67.3%] | 5.3% [1.5%, 17.3%] | 33.0% [24.2%, 43.1%] | 56.4% [37.1%, 70.4%] | 1.69e-08 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 36 tasks, 10000 usable): H1 precision − base rate 95% CI [26.2%, 58.2%] → supported; H2 held-back difference 95% CI [36.4%, 75.0%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 35 | 25.7% [14.2%, 42.1%] | 62.5% [30.6%, 86.3%] | 2.43 | 2.43 | 55.6% [26.7%, 81.1%] | 11.5% [4.0%, 29.0%] | 50.0% [32.1%, 67.9%] | 0.0% [0.0%, 29.9%] | 40.0% [25.6%, 56.4%] | 44.0% [10.3%, 70.7%] | 0.0151 |
| claude-sonnet-4 | 36 | 63.9% [47.6%, 77.5%] | 87.5% [52.9%, 97.8%] | 1.37 | 1.37 | 30.4% [15.6%, 50.9%] | 7.7% [1.4%, 33.3%] | 38.5% [17.7%, 64.5%] | 4.3% [0.8%, 21.0%] | 61.1% [44.9%, 75.2%] | 22.7% [-6.9%, 44.1%] | 0.213 |
| gemini-2.5-flash | 20 | 30.0% [14.5%, 51.9%] | 100.0% [51.0%, 100.0%] | 3.33 | 3.33 | 66.7% [30.0%, 90.3%] | 0.0% [0.0%, 21.5%] | 42.9% [21.4%, 67.4%] | 16.7% [3.0%, 56.4%] | 45.0% [25.8%, 65.8%] | 66.7% [24.1%, 90.3%] | 0.0031 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 91 | 41.8% [32.2%, 52.0%] | 80.0% [58.4%, 91.9%] | 1.92 | 1.91 | 42.1% [27.9%, 57.8%] | 7.5% [3.0%, 17.9%] | 45.3% [32.7%, 58.5%] | 5.3% [1.5%, 17.3%] | 49.5% [39.4%, 59.5%] | 34.6% [17.0%, 50.9%] | 0.000183 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 36 tasks, 10000 usable): H1 precision − base rate 95% CI [18.2%, 59.3%] → supported; H2 held-back difference 95% CI [14.5%, 54.2%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini | 35 | 25.7% [14.2%, 42.1%] | 62.5% [30.6%, 86.3%] | 2.43 | 2.43 | 55.6% [26.7%, 81.1%] | 11.5% [4.0%, 29.0%] | 50.0% [32.1%, 67.9%] | 0.0% [0.0%, 29.9%] | 40.0% [25.6%, 56.4%] | 44.0% [10.3%, 70.7%] | 0.0151 |
| claude-sonnet-4 | 36 | 63.9% [47.6%, 77.5%] | 88.9% [67.2%, 96.9%] | 1.39 | 1.39 | 69.6% [49.1%, 84.4%] | 15.4% [4.3%, 42.2%] | 38.5% [17.7%, 64.5%] | 4.3% [0.8%, 21.0%] | 33.3% [20.2%, 49.7%] | 54.2% [20.4%, 72.7%] | 0.00451 |
| gemini-2.5-flash | 20 | 30.0% [14.5%, 51.9%] | 100.0% [51.0%, 100.0%] | 3.33 | 3.33 | 66.7% [30.0%, 90.3%] | 0.0% [0.0%, 21.5%] | 42.9% [21.4%, 67.4%] | 16.7% [3.0%, 56.4%] | 45.0% [25.8%, 65.8%] | 66.7% [24.1%, 90.3%] | 0.0031 |
| pooled (gpt-4.1-mini, claude-sonnet-4, gemini-2.5-flash) | 91 | 41.8% [32.2%, 52.0%] | 83.3% [66.4%, 92.7%] | 2.00 | 1.69 | 65.8% [49.9%, 78.8%] | 9.4% [4.1%, 20.3%] | 45.3% [32.7%, 58.5%] | 5.3% [1.5%, 17.3%] | 38.5% [29.1%, 48.7%] | 56.4% [37.1%, 70.4%] | 1.69e-08 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 36 tasks, 10000 usable): H1 precision − base rate 95% CI [26.2%, 58.2%] → supported; H2 held-back difference 95% CI [36.4%, 75.0%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

15 tasks, 37 patches. ACCEPT rate correct 36.8% [19.1%, 59.0%], wrong 11.1% [3.1%, 32.8%]. Correct/wrong pairs in the same task: concordant 5, discordant 1, ties 16.

### V4 on correct public patches vs gold on the same tasks

38 correct public patches: V4 full pass 86.8% [72.7%, 94.2%]; gold on the same tasks 78.9% [63.7%, 88.9%]. Cells: {'public_pass__gold_pass': 30, 'public_pass__gold_not': 3, 'public_not__gold_pass': 0, 'public_not__gold_not': 5}.

- H3 (all): 1 of 60 gold patches REJECTed, point 1.7%, Wilson 95% upper 8.9% (sympy__sympy-14248).
- H3 (headline_scope): 1 of 36 gold patches REJECTed, point 2.8%, Wilson 95% upper 14.2% (sympy__sympy-14248).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini | 36 | 0 | 35 | 9 |
| claude-sonnet-4 | 36 | 0 | 36 | 23 |
| gemini-2.5-flash | 26 | 1 | 20 | 6 |

Conflict markers fired only on lines starting `=======`: claude-sonnet-4/sphinx-doc__sphinx-9591, gemini-2.5-flash/sphinx-doc__sphinx-9591, gpt-4.1-mini/sphinx-doc__sphinx-9658.

## Label checks

- gpt-4.1-mini: no label 2 (django__django-11149, sphinx-doc__sphinx-8035); official patch sha256 mismatch 0 (none).
- claude-sonnet-4: no label 0 (none); official patch sha256 mismatch 0 (none).
- gemini-2.5-flash: no label 7 (django__django-11451, django__django-13401, pydata__xarray-3677, pydata__xarray-4687, scikit-learn__scikit-learn-25973, sympy__sympy-14531, sympy__sympy-22456); official patch sha256 mismatch 0 (none).
