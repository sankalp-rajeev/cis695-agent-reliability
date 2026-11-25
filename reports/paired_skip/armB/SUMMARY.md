# Arm B paired-skip replay

The replay covers 51 gpt-4.1-mini Arm B patches. V2 was recomputed from stored evidence for 40 patches. For the 11 tasks with no executed tests, the four stored S and C variants agreed on V2 `NOT_AVAILABLE` and on the decision. Both P variants carry those results forward. The frozen v1.4.1 decision rule used the stored V1, V3, and V4 values.

Before joining correctness labels, the replay reproduced 5 ACCEPT, 42 FLAG, and 4 REJECT under S with `INVALID_ID` excluded, and 20 ACCEPT, 27 FLAG, and 4 REJECT under C. The ACCEPT sets satisfied S ⊆ P ⊆ C under both `INVALID_ID` variants. P and C agreed on every task in both variants. [Label-free decisions](decisions_label_free.csv) · [Decision counts](counts_label_free.csv) · [P/C decision differences](p_vs_c_differences.csv)

The committed labels identify 25 correct patches and 26 wrong patches. Held back means FLAG or REJECT. The last column subtracts the correct-patch held-back rate from the wrong-patch held-back rate.

## INVALID_ID excluded

| Policy | ACCEPT (correct + wrong) | Precision (95% Wilson CI) | Coverage | Correct patches accepted | Wrong held back | Correct held back | Difference |
|---|---:|---:|---:|---:|---:|---:|---:|
| S | 5 (4 + 1) | 80.0% [37.6%, 96.4%] | 5/51 (9.8%) | 4/25 (16.0%) | 96.2% | 84.0% | +12.2 pp |
| C | 20 (16 + 4) | 80.0% [58.4%, 91.9%] | 20/51 (39.2%) | 16/25 (64.0%) | 84.6% | 36.0% | +48.6 pp |
| P | 20 (16 + 4) | 80.0% [58.4%, 91.9%] | 20/51 (39.2%) | 16/25 (64.0%) | 84.6% | 36.0% | +48.6 pp |

## INVALID_ID missing

| Policy | ACCEPT (correct + wrong) | Precision (95% Wilson CI) | Coverage | Correct patches accepted | Wrong held back | Correct held back | Difference |
|---|---:|---:|---:|---:|---:|---:|---:|
| S | 5 (4 + 1) | 80.0% [37.6%, 96.4%] | 5/51 (9.8%) | 4/25 (16.0%) | 96.2% | 84.0% | +12.2 pp |
| C | 13 (9 + 4) | 69.2% [42.4%, 87.3%] | 13/51 (25.5%) | 9/25 (36.0%) | 84.6% | 64.0% | +20.6 pp |
| P | 13 (9 + 4) | 69.2% [42.4%, 87.3%] | 13/51 (25.5%) | 9/25 (36.0%) | 84.6% | 64.0% | +20.6 pp |

Policy P was designed after the Arm B and DeepSeek correctness labels were seen, so the replay is exploratory. Policy S remains primary. Adopting P as primary requires a protocol amendment frozen before Arm A and the 200-task run.

The DeepSeek Phase 4 V2 run directory was not found on this machine. The DeepSeek replay is pending.
