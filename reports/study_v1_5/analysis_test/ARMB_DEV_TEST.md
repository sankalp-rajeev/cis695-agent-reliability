# Arm B dev test (analysis script end-to-end)

## Scope: headline (batch, minus headline exclusions)

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [20.7%, 49.7%] → supported; H2 held-back difference 95% CI [41.7%, 84.3%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 81.2% [57.0%, 93.4%] | 1.66 | 1.66 | 52.0% [33.5%, 70.0%] | 11.5% [4.0%, 29.0%] | 23.1% [11.0%, 42.1%] | 0.0% [0.0%, 13.3%] | 56.9% [43.3%, 69.5%] | 40.5% [15.0%, 59.9%] | 0.00253 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 81.2% [57.0%, 93.4%] | 1.66 | 1.66 | 52.0% [33.5%, 70.0%] | 11.5% [4.0%, 29.0%] | 23.1% [11.0%, 42.1%] | 0.0% [0.0%, 13.3%] | 56.9% [43.3%, 69.5%] | 40.5% [15.0%, 59.9%] | 0.00253 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [13.7%, 51.0%] → supported; H2 held-back difference 95% CI [16.7%, 63.0%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 70.8% [50.8%, 85.1%] | 1.45 | 1.45 | 68.0% [48.4%, 82.8%] | 26.9% [13.7%, 46.1%] | 42.3% [25.5%, 61.1%] | 4.0% [0.7%, 19.5%] | 29.4% [18.7%, 43.0%] | 41.1% [13.7%, 60.9%] | 0.00501 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 70.8% [50.8%, 85.1%] | 1.45 | 1.45 | 68.0% [48.4%, 82.8%] | 26.9% [13.7%, 46.1%] | 42.3% [25.5%, 61.1%] | 4.0% [0.7%, 19.5%] | 29.4% [18.7%, 43.0%] | 41.1% [13.7%, 60.9%] | 0.00501 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [7.5%, 37.3%] → supported; H2 held-back difference 95% CI [14.4%, 65.3%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [20.7%, 49.7%] → supported; H2 held-back difference 95% CI [41.7%, 84.3%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [20.7%, 49.7%] → supported; H2 held-back difference 95% CI [41.7%, 84.3%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [20.7%, 49.7%] → supported; H2 held-back difference 95% CI [41.7%, 84.3%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

0 tasks, 0 patches. ACCEPT rate correct n/a, wrong n/a. Correct/wrong pairs in the same task: concordant 0, discordant 0, ties 0.

### V4 on correct public patches vs gold on the same tasks

25 correct public patches: V4 full pass 80.0% [60.9%, 91.1%]; gold on the same tasks 84.0% [65.3%, 93.6%]. Cells: {'public_pass__gold_pass': 20, 'public_pass__gold_not': 0, 'public_not__gold_pass': 1, 'public_not__gold_not': 4}.

- H3 (all): 0 of 51 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.0% (none).
- H3 (headline_scope): 0 of 51 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.0% (none).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini-armB | 51 | 0 | 51 | 25 |

Conflict markers fired only on lines starting `=======`: none.

## Scope: sensitivity: all tasks (no exclusions)

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [20.7%, 49.7%] → supported; H2 held-back difference 95% CI [41.7%, 84.3%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 81.2% [57.0%, 93.4%] | 1.66 | 1.66 | 52.0% [33.5%, 70.0%] | 11.5% [4.0%, 29.0%] | 23.1% [11.0%, 42.1%] | 0.0% [0.0%, 13.3%] | 56.9% [43.3%, 69.5%] | 40.5% [15.0%, 59.9%] | 0.00253 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 81.2% [57.0%, 93.4%] | 1.66 | 1.66 | 52.0% [33.5%, 70.0%] | 11.5% [4.0%, 29.0%] | 23.1% [11.0%, 42.1%] | 0.0% [0.0%, 13.3%] | 56.9% [43.3%, 69.5%] | 40.5% [15.0%, 59.9%] | 0.00253 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [13.7%, 51.0%] → supported; H2 held-back difference 95% CI [16.7%, 63.0%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 70.8% [50.8%, 85.1%] | 1.45 | 1.45 | 68.0% [48.4%, 82.8%] | 26.9% [13.7%, 46.1%] | 42.3% [25.5%, 61.1%] | 4.0% [0.7%, 19.5%] | 29.4% [18.7%, 43.0%] | 41.1% [13.7%, 60.9%] | 0.00501 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 70.8% [50.8%, 85.1%] | 1.45 | 1.45 | 68.0% [48.4%, 82.8%] | 26.9% [13.7%, 46.1%] | 42.3% [25.5%, 61.1%] | 4.0% [0.7%, 19.5%] | 29.4% [18.7%, 43.0%] | 41.1% [13.7%, 60.9%] | 0.00501 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [7.5%, 37.3%] → supported; H2 held-back difference 95% CI [14.4%, 65.3%] → supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [20.7%, 49.7%] → supported; H2 held-back difference 95% CI [41.7%, 84.3%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [20.7%, 49.7%] → supported; H2 held-back difference 95% CI [41.7%, 84.3%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |
| pooled (gpt-4.1-mini-armB) | 51 | 49.0% [35.9%, 62.3%] | 83.3% [64.1%, 93.3%] | 1.70 | 1.70 | 80.0% [60.9%, 91.1%] | 15.4% [6.2%, 33.5%] | 26.9% [13.7%, 46.1%] | 0.0% [0.0%, 13.3%] | 39.2% [27.0%, 52.9%] | 64.6% [38.2%, 79.1%] | 4.28e-06 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 51 tasks, 10000 usable): H1 precision − base rate 95% CI [20.7%, 49.7%] → supported; H2 held-back difference 95% CI [41.7%, 84.3%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

0 tasks, 0 patches. ACCEPT rate correct n/a, wrong n/a. Correct/wrong pairs in the same task: concordant 0, discordant 0, ties 0.

### V4 on correct public patches vs gold on the same tasks

25 correct public patches: V4 full pass 80.0% [60.9%, 91.1%]; gold on the same tasks 84.0% [65.3%, 93.6%]. Cells: {'public_pass__gold_pass': 20, 'public_pass__gold_not': 0, 'public_not__gold_pass': 1, 'public_not__gold_not': 4}.

- H3 (all): 0 of 51 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.0% (none).
- H3 (headline_scope): 0 of 51 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.0% (none).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini-armB | 51 | 0 | 51 | 25 |

Conflict markers fired only on lines starting `=======`: none.

## Scope: sensitivity: headline minus tasks with generator recall

### v1.5 frozen (headline)

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 35 | 54.3% [38.2%, 69.5%] | 80.0% [58.4%, 91.9%] | 1.47 | 1.47 | 84.2% [62.4%, 94.5%] | 25.0% [10.2%, 49.5%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 31.4% [18.6%, 48.0%] | 59.2% [26.4%, 77.2%] | 0.000632 |
| pooled (gpt-4.1-mini-armB) | 35 | 54.3% [38.2%, 69.5%] | 80.0% [58.4%, 91.9%] | 1.47 | 1.47 | 84.2% [62.4%, 94.5%] | 25.0% [10.2%, 49.5%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 31.4% [18.6%, 48.0%] | 59.2% [26.4%, 77.2%] | 0.000632 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 35 tasks, 10000 usable): H1 precision − base rate 95% CI [11.4%, 42.3%] → supported; H2 held-back difference 95% CI [31.0%, 83.3%] → supported.

### v1.4.1, same signals

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 35 | 54.3% [38.2%, 69.5%] | 78.6% [52.4%, 92.4%] | 1.45 | 1.45 | 57.9% [36.3%, 76.9%] | 18.8% [6.6%, 43.0%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 48.6% [33.0%, 64.4%] | 39.1% [6.7%, 61.7%] | 0.0364 |
| pooled (gpt-4.1-mini-armB) | 35 | 54.3% [38.2%, 69.5%] | 78.6% [52.4%, 92.4%] | 1.45 | 1.45 | 57.9% [36.3%, 76.9%] | 18.8% [6.6%, 43.0%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 48.6% [33.0%, 64.4%] | 39.1% [6.7%, 61.7%] | 0.0364 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 35 tasks, 10000 usable): H1 precision − base rate 95% CI [4.7%, 44.6%] → supported; H2 held-back difference 95% CI [7.8%, 67.4%] → supported.

### V1+V2 only

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 35 | 54.3% [38.2%, 69.5%] | 68.4% [46.0%, 84.6%] | 1.26 | 1.26 | 68.4% [46.0%, 84.6%] | 37.5% [18.5%, 61.4%] | 43.8% [23.1%, 66.8%] | 5.3% [0.9%, 24.6%] | 22.9% [12.1%, 39.0%] | 30.9% [-1.8%, 55.9%] | 0.0946 |
| pooled (gpt-4.1-mini-armB) | 35 | 54.3% [38.2%, 69.5%] | 68.4% [46.0%, 84.6%] | 1.26 | 1.26 | 68.4% [46.0%, 84.6%] | 37.5% [18.5%, 61.4%] | 43.8% [23.1%, 66.8%] | 5.3% [0.9%, 24.6%] | 22.9% [12.1%, 39.0%] | 30.9% [-1.8%, 55.9%] | 0.0946 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 35 tasks, 10000 usable): H1 precision − base rate 95% CI [-1.2%, 30.4%] → not supported; H2 held-back difference 95% CI [-2.6%, 61.7%] → not supported.

### S1: risk flags informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 35 | 54.3% [38.2%, 69.5%] | 80.0% [58.4%, 91.9%] | 1.47 | 1.47 | 84.2% [62.4%, 94.5%] | 25.0% [10.2%, 49.5%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 31.4% [18.6%, 48.0%] | 59.2% [26.4%, 77.2%] | 0.000632 |
| pooled (gpt-4.1-mini-armB) | 35 | 54.3% [38.2%, 69.5%] | 80.0% [58.4%, 91.9%] | 1.47 | 1.47 | 84.2% [62.4%, 94.5%] | 25.0% [10.2%, 49.5%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 31.4% [18.6%, 48.0%] | 59.2% [26.4%, 77.2%] | 0.000632 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 35 tasks, 10000 usable): H1 precision − base rate 95% CI [11.4%, 42.3%] → supported; H2 held-back difference 95% CI [31.0%, 83.3%] → supported.

### S2: V1 manipulation findings informational

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 35 | 54.3% [38.2%, 69.5%] | 80.0% [58.4%, 91.9%] | 1.47 | 1.47 | 84.2% [62.4%, 94.5%] | 25.0% [10.2%, 49.5%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 31.4% [18.6%, 48.0%] | 59.2% [26.4%, 77.2%] | 0.000632 |
| pooled (gpt-4.1-mini-armB) | 35 | 54.3% [38.2%, 69.5%] | 80.0% [58.4%, 91.9%] | 1.47 | 1.47 | 84.2% [62.4%, 94.5%] | 25.0% [10.2%, 49.5%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 31.4% [18.6%, 48.0%] | 59.2% [26.4%, 77.2%] | 0.000632 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 35 tasks, 10000 usable): H1 precision − base rate 95% CI [11.4%, 42.3%] → supported; H2 held-back difference 95% CI [31.0%, 83.3%] → supported.

### S3: S1 and S2

| system | n | base rate | ACCEPT precision [95% CI] | lift | lift (accept-weighted) | coverage | false-accept rate | wrong rejected | correct rejected | FLAG rate | held-back diff [Newcombe] | Fisher p |
|---|---:|---|---|---:|---:|---|---|---|---|---|---|---:|
| gpt-4.1-mini-armB | 35 | 54.3% [38.2%, 69.5%] | 80.0% [58.4%, 91.9%] | 1.47 | 1.47 | 84.2% [62.4%, 94.5%] | 25.0% [10.2%, 49.5%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 31.4% [18.6%, 48.0%] | 59.2% [26.4%, 77.2%] | 0.000632 |
| pooled (gpt-4.1-mini-armB) | 35 | 54.3% [38.2%, 69.5%] | 80.0% [58.4%, 91.9%] | 1.47 | 1.47 | 84.2% [62.4%, 94.5%] | 25.0% [10.2%, 49.5%] | 25.0% [10.2%, 49.5%] | 0.0% [0.0%, 16.8%] | 31.4% [18.6%, 48.0%] | 59.2% [26.4%, 77.2%] | 0.000632 |

Bootstrap (task-clustered, 10000 resamples, seed 20261126, 35 tasks, 10000 usable): H1 precision − base rate 95% CI [11.4%, 42.3%] → supported; H2 held-back difference 95% CI [31.0%, 83.3%] → supported.

### Within-task comparison (v1.5 frozen; tasks where systems disagree on correctness)

0 tasks, 0 patches. ACCEPT rate correct n/a, wrong n/a. Correct/wrong pairs in the same task: concordant 0, discordant 0, ties 0.

### V4 on correct public patches vs gold on the same tasks

19 correct public patches: V4 full pass 84.2% [62.4%, 94.5%]; gold on the same tasks 84.2% [62.4%, 94.5%]. Cells: {'public_pass__gold_pass': 16, 'public_pass__gold_not': 0, 'public_not__gold_pass': 0, 'public_not__gold_not': 3}.

- H3 (all): 0 of 51 gold patches REJECTed, point 0.0%, Wilson 95% upper 7.0% (none).
- H3 (headline_scope): 0 of 35 gold patches REJECTed, point 0.0%, Wilson 95% upper 9.9% (none).

### RQ1 and data

| system | patches in scope | empty | non-empty labelled | resolved |
|---|---:|---:|---:|---:|
| gpt-4.1-mini-armB | 35 | 0 | 35 | 19 |

Conflict markers fired only on lines starting `=======`: none.

## Label checks

- gpt-4.1-mini-armB: no label 0 (none); official patch sha256 mismatch 0 (none).
