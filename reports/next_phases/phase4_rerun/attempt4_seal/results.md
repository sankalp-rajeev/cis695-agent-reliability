# Phase 4 attempt 4: pre-registered label-free seal

Manifest: `69122ab64f197afc04756aad0b8e937422d1e407bb03ca29851c33a943ddaa25`; 1799 files, 3488110239 bytes.

| Quantity | Value | Prediction | Falsification |
|---|---:|---|---|
| H1 | 35774/37614 (95.1082%) | met | not falsified |
| H1b | 12013/13853 (86.7177%) | met | not falsified |
| H2 | 58/83 (69.8795%) | met | not falsified |

H1 **secondary informational**, INVALID_ID removed from B1: 35774/37074 (96.4935%). The primary denominator and thresholds are unchanged.

H2 secondary, including REGRESSION_ERROR: 59/83.

H3: Policy S yes/no = 26/83 versus B2 = 21 (change +5). Descriptive only; no prediction/falsification thresholds were registered.

## Four policy reports

| Policy | INVALID_ID accounting | PASS | FAIL | REGRESSION_ERROR | INCOMPLETE | NOT_AVAILABLE | BASELINE_UNRELIABLE | Yes/no primary | Secondary incl. REGRESSION_ERROR |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C | excluded | 52 | 6 | 1 | 19 | 5 | 0 | 58 | 59 |
| C | missing | 42 | 6 | 1 | 29 | 5 | 0 | 48 | 49 |
| S | excluded | 20 | 6 | 1 | 51 | 5 | 0 | 26 | 27 |
| S | missing | 19 | 6 | 1 | 52 | 5 | 0 | 25 | 26 |

## INVALID_ID accounting differences

| Policy | Task | Excluded | Missing |
|---|---|---|---|
| C | `astropy__astropy-7606` | PASS | INCOMPLETE |
| C | `django__django-16612` | PASS | INCOMPLETE |
| C | `matplotlib__matplotlib-22719` | PASS | INCOMPLETE |
| C | `pytest-dev__pytest-6202` | PASS | INCOMPLETE |
| C | `pytest-dev__pytest-7236` | PASS | INCOMPLETE |
| C | `pytest-dev__pytest-7521` | PASS | INCOMPLETE |
| C | `scikit-learn__scikit-learn-12585` | PASS | INCOMPLETE |
| C | `pylint-dev__pylint-4970` | PASS | INCOMPLETE |
| C | `pytest-dev__pytest-7432` | PASS | INCOMPLETE |
| C | `scikit-learn__scikit-learn-14894` | PASS | INCOMPLETE |
| S | `matplotlib__matplotlib-22719` | PASS | INCOMPLETE |

## Remaining skips

Selected-tree SKIPPED slots; each slot has one reason group. Exact captured reasons and overlapping strict nonbinary task groups are in results.json.

| Reason group | Slots |
|---|---:|
| MODULE_DISABLED | 36 |
| OPTIONAL_DEPENDENCY_OR_FEATURE | 398 |
| OTHER_RECORDED_SKIP | 4558 |
| PLATFORM_OR_INTERPRETER | 4 |
| REASON_NOT_CAPTURED | 484 |

**CPU-conditioned tests (separate):** 12 fixed selected families, covering 76 frozen-original native tree instances; 0 remain SKIPPED selected tree slots. Current selected-tree statuses: `{"passed": 24}`. Current concrete native-tree statuses: `{"passed": 76}`.

## Integrity

**PASS**: 6 original native FAIL tasks reconciled; 0 unexplained disappearing native FAILs. Run bytes were reverified before and after computation.

| Original native FAIL task | Present as FAIL under all four policies |
|---|---|
| `django__django-14140` | Yes |
| `pytest-dev__pytest-5809` | Yes |
| `django__django-12209` | Yes |
| `django__django-14631` | Yes |
| `matplotlib__matplotlib-25479` | Yes |
| `sphinx-doc__sphinx-10435` | Yes |

## Cap hits

No benchmark or cap retries were performed by the seal computation.

| Task | Tree | Scope | NOT_REACHED | TIMEOUT | Budget seconds |
|---|---|---|---:|---:|---:|
| `sympy__sympy-24562` | base | initial | 463 | 1 | 1800 |
| `sympy__sympy-24562` | patched | initial | 463 | 1 | 1800 |

## Category totals

Initial selected tree slots for INVALID_ID/NOT_REACHED/TIMEOUT/COLLECTION_ERROR/COLLECTOR_FALLBACK; selected final Policy C families for FLAKY/REGRESSION_ERROR; flagged tasks for GENERATED_INPUT_CHANGED. Policy copies and confirmations do not inflate initial-slot counts.

| Category | Count |
|---|---:|
| INVALID_ID | 572 |
| FLAKY | 0 |
| REGRESSION_ERROR | 5 |
| NOT_REACHED | 932 |
| TIMEOUT | 2 |
| COLLECTION_ERROR | 1934 |
| COLLECTOR_FALLBACK | 0 |
| GENERATED_INPUT_CHANGED | 0 |

**Confirmation-run count:** 72 actual isolated tree calls, counted once from native_passes minus the two initial calls and checked against the primary stored report.

## Per-task label-free table

| Task | Policy C | Policy S | Base admitted/selected | Patched admitted/selected |
|---|---|---|---:|---:|
| `astropy__astropy-13977` | INCOMPLETE | INCOMPLETE | 3019/3080 | 3019/3080 |
| `astropy__astropy-7606` | PASS | INCOMPLETE | 737/738 | 737/738 |
| `django__django-10973` | REGRESSION_ERROR | REGRESSION_ERROR | 13/13 | 7/13 |
| `django__django-11820` | INCOMPLETE | INCOMPLETE | 3123/3167 | 3123/3167 |
| `django__django-12965` | PASS | INCOMPLETE | 17/17 | 17/17 |
| `django__django-14140` | FAIL | FAIL | 2291/2334 | 2291/2334 |
| `django__django-15037` | PASS | INCOMPLETE | 679/679 | 679/679 |
| `django__django-15930` | INCOMPLETE | INCOMPLETE | 4349/4416 | 4349/4416 |
| `django__django-16612` | PASS | INCOMPLETE | 770/771 | 770/771 |
| `matplotlib__matplotlib-14623` | NOT_AVAILABLE | NOT_AVAILABLE | 0/0 | 0/0 |
| `matplotlib__matplotlib-20488` | PASS | INCOMPLETE | 828/828 | 828/828 |
| `matplotlib__matplotlib-22719` | PASS | PASS | 39/40 | 39/40 |
| `matplotlib__matplotlib-24026` | PASS | INCOMPLETE | 611/611 | 611/611 |
| `matplotlib__matplotlib-25287` | PASS | INCOMPLETE | 2/2 | 2/2 |
| `mwaskom__seaborn-3069` | PASS | PASS | 150/150 | 150/150 |
| `pallets__flask-5014` | PASS | INCOMPLETE | 203/203 | 203/203 |
| `pydata__xarray-4629` | PASS | PASS | 22/22 | 22/22 |
| `pydata__xarray-6599` | PASS | INCOMPLETE | 58/58 | 58/58 |
| `pydata__xarray-6744` | PASS | INCOMPLETE | 362/362 | 362/362 |
| `pylint-dev__pylint-4661` | PASS | PASS | 4/4 | 4/4 |
| `pylint-dev__pylint-6528` | PASS | PASS | 217/217 | 217/217 |
| `pylint-dev__pylint-6903` | NOT_AVAILABLE | NOT_AVAILABLE | 0/0 | 0/0 |
| `pytest-dev__pytest-10051` | INCOMPLETE | INCOMPLETE | 275/275 | 275/275 |
| `pytest-dev__pytest-5787` | INCOMPLETE | INCOMPLETE | 140/206 | 140/206 |
| `pytest-dev__pytest-5809` | FAIL | FAIL | 4/4 | 4/4 |
| `pytest-dev__pytest-6202` | PASS | INCOMPLETE | 241/268 | 241/268 |
| `pytest-dev__pytest-7236` | PASS | INCOMPLETE | 51/102 | 51/102 |
| `pytest-dev__pytest-7521` | PASS | INCOMPLETE | 88/90 | 88/90 |
| `scikit-learn__scikit-learn-10908` | PASS | PASS | 46/46 | 46/46 |
| `scikit-learn__scikit-learn-12585` | PASS | INCOMPLETE | 768/769 | 768/769 |
| `scikit-learn__scikit-learn-14141` | PASS | PASS | 3/3 | 3/3 |
| `sphinx-doc__sphinx-10323` | PASS | PASS | 40/40 | 40/40 |
| `sphinx-doc__sphinx-7910` | PASS | PASS | 16/16 | 16/16 |
| `sympy__sympy-13480` | INCOMPLETE | INCOMPLETE | 762/781 | 762/781 |
| `sympy__sympy-17318` | PASS | PASS | 21/21 | 21/21 |
| `sympy__sympy-19783` | PASS | INCOMPLETE | 729/729 | 729/729 |
| `sympy__sympy-24562` | INCOMPLETE | INCOMPLETE | 198/662 | 198/662 |
| `astropy__astropy-14365` | PASS | PASS | 8/8 | 8/8 |
| `astropy__astropy-14508` | NOT_AVAILABLE | NOT_AVAILABLE | 0/0 | 0/0 |
| `django__django-11095` | PASS | INCOMPLETE | 836/836 | 836/836 |
| `django__django-11299` | INCOMPLETE | INCOMPLETE | 699/747 | 699/747 |
| `django__django-12209` | FAIL | FAIL | 3275/3319 | 3275/3319 |
| `django__django-13023` | INCOMPLETE | INCOMPLETE | 449/459 | 449/459 |
| `django__django-13033` | PASS | PASS | 4/4 | 4/4 |
| `django__django-13158` | INCOMPLETE | INCOMPLETE | 816/873 | 816/873 |
| `django__django-13212` | INCOMPLETE | INCOMPLETE | 1283/1383 | 1283/1383 |
| `django__django-13297` | INCOMPLETE | INCOMPLETE | 7827/8152 | 7827/8152 |
| `django__django-13569` | PASS | INCOMPLETE | 342/342 | 342/342 |
| `django__django-13786` | INCOMPLETE | INCOMPLETE | 449/460 | 449/460 |
| `django__django-13807` | PASS | INCOMPLETE | 66/66 | 66/66 |
| `django__django-13820` | PASS | PASS | 262/262 | 262/262 |
| `django__django-14631` | FAIL | FAIL | 4351/4468 | 4351/4468 |
| `django__django-15103` | PASS | PASS | 47/47 | 47/47 |
| `django__django-15278` | PASS | INCOMPLETE | 306/306 | 306/306 |
| `django__django-15375` | PASS | INCOMPLETE | 430/430 | 430/430 |
| `django__django-15499` | INCOMPLETE | INCOMPLETE | 513/526 | 513/526 |
| `django__django-15572` | PASS | INCOMPLETE | 84/84 | 84/84 |
| `django__django-16082` | INCOMPLETE | INCOMPLETE | 175/181 | 175/181 |
| `django__django-16136` | INCOMPLETE | INCOMPLETE | 3822/3925 | 3822/3925 |
| `django__django-16255` | PASS | PASS | 47/47 | 47/47 |
| `django__django-16315` | PASS | INCOMPLETE | 18/18 | 18/18 |
| `django__django-16631` | PASS | PASS | 478/478 | 478/478 |
| `django__django-16667` | PASS | INCOMPLETE | 272/272 | 272/272 |
| `matplotlib__matplotlib-20676` | PASS | INCOMPLETE | 736/736 | 736/736 |
| `matplotlib__matplotlib-22871` | PASS | PASS | 54/54 | 54/54 |
| `matplotlib__matplotlib-23299` | PASS | INCOMPLETE | 46/46 | 46/46 |
| `matplotlib__matplotlib-23476` | INCOMPLETE | INCOMPLETE | 680/694 | 680/694 |
| `matplotlib__matplotlib-24177` | NOT_AVAILABLE | NOT_AVAILABLE | 0/0 | 0/0 |
| `matplotlib__matplotlib-24637` | PASS | INCOMPLETE | 16/16 | 16/16 |
| `matplotlib__matplotlib-24970` | PASS | INCOMPLETE | 80/80 | 80/80 |
| `matplotlib__matplotlib-25122` | PASS | PASS | 54/54 | 54/54 |
| `matplotlib__matplotlib-25479` | FAIL | FAIL | 88/88 | 88/88 |
| `matplotlib__matplotlib-26291` | PASS | PASS | 107/107 | 107/107 |
| `pydata__xarray-4695` | PASS | INCOMPLETE | 277/277 | 277/277 |
| `pydata__xarray-4966` | NOT_AVAILABLE | NOT_AVAILABLE | 0/0 | 0/0 |
| `pylint-dev__pylint-4970` | PASS | INCOMPLETE | 169/204 | 169/204 |
| `pylint-dev__pylint-7277` | PASS | PASS | 70/70 | 70/70 |
| `pytest-dev__pytest-7432` | PASS | INCOMPLETE | 216/268 | 216/268 |
| `scikit-learn__scikit-learn-14629` | INCOMPLETE | INCOMPLETE | 2773/2789 | 2773/2789 |
| `scikit-learn__scikit-learn-14894` | PASS | INCOMPLETE | 1917/1919 | 1917/1919 |
| `sphinx-doc__sphinx-10435` | FAIL | FAIL | 90/90 | 90/90 |
| `sphinx-doc__sphinx-10466` | PASS | INCOMPLETE | 344/344 | 344/344 |
| `sympy__sympy-14711` | INCOMPLETE | INCOMPLETE | 419/429 | 419/429 |

## Counts by task

| Task | INVALID_ID | FLAKY | REGRESSION_ERROR | NOT_REACHED | TIMEOUT | COLLECTION_ERROR | COLLECTOR_FALLBACK | GENERATED_INPUT_CHANGED | Confirmation runs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `astropy__astropy-13977` | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `astropy__astropy-7606` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-10973` | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 30 |
| `django__django-11820` | 32 | 0 | 0 | 0 | 0 | 52 | 0 | 0 | 0 |
| `django__django-12965` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-14140` | 0 | 0 | 0 | 0 | 0 | 86 | 0 | 0 | 12 |
| `django__django-15037` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-15930` | 10 | 0 | 0 | 2 | 0 | 120 | 0 | 0 | 0 |
| `django__django-16612` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-14623` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-20488` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-22719` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-24026` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-25287` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `mwaskom__seaborn-3069` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pallets__flask-5014` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pydata__xarray-4629` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pydata__xarray-6599` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pydata__xarray-6744` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pylint-dev__pylint-4661` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pylint-dev__pylint-6528` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pylint-dev__pylint-6903` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pytest-dev__pytest-10051` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pytest-dev__pytest-5787` | 2 | 0 | 0 | 0 | 0 | 130 | 0 | 0 | 0 |
| `pytest-dev__pytest-5809` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| `pytest-dev__pytest-6202` | 54 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pytest-dev__pytest-7236` | 102 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pytest-dev__pytest-7521` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `scikit-learn__scikit-learn-10908` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `scikit-learn__scikit-learn-12585` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `scikit-learn__scikit-learn-14141` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sphinx-doc__sphinx-10323` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sphinx-doc__sphinx-7910` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sympy__sympy-13480` | 0 | 0 | 0 | 0 | 0 | 32 | 0 | 0 | 0 |
| `sympy__sympy-17318` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sympy__sympy-19783` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sympy__sympy-24562` | 0 | 0 | 0 | 926 | 2 | 0 | 0 | 0 | 0 |
| `astropy__astropy-14365` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `astropy__astropy-14508` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-11095` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-11299` | 0 | 0 | 0 | 0 | 0 | 94 | 0 | 0 | 0 |
| `django__django-12209` | 32 | 0 | 0 | 0 | 0 | 52 | 0 | 0 | 6 |
| `django__django-13023` | 4 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| `django__django-13033` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-13158` | 0 | 0 | 0 | 0 | 0 | 112 | 0 | 0 | 0 |
| `django__django-13212` | 24 | 0 | 0 | 0 | 0 | 174 | 0 | 0 | 0 |
| `django__django-13297` | 44 | 0 | 0 | 2 | 0 | 586 | 0 | 0 | 0 |
| `django__django-13569` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-13786` | 0 | 0 | 0 | 0 | 0 | 22 | 0 | 0 | 0 |
| `django__django-13807` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-13820` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-14631` | 12 | 0 | 0 | 2 | 0 | 212 | 0 | 0 | 6 |
| `django__django-15103` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-15278` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-15375` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-15499` | 0 | 0 | 0 | 0 | 0 | 26 | 0 | 0 | 0 |
| `django__django-15572` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-16082` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 0 |
| `django__django-16136` | 24 | 0 | 0 | 0 | 0 | 182 | 0 | 0 | 0 |
| `django__django-16255` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-16315` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-16631` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `django__django-16667` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-20676` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-22871` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-23299` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-23476` | 2 | 0 | 0 | 0 | 0 | 26 | 0 | 0 | 0 |
| `matplotlib__matplotlib-24177` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-24637` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-24970` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-25122` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `matplotlib__matplotlib-25479` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| `matplotlib__matplotlib-26291` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pydata__xarray-4695` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pydata__xarray-4966` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pylint-dev__pylint-4970` | 70 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pylint-dev__pylint-7277` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `pytest-dev__pytest-7432` | 104 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `scikit-learn__scikit-learn-14629` | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `scikit-learn__scikit-learn-14894` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sphinx-doc__sphinx-10435` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| `sphinx-doc__sphinx-10466` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sympy__sympy-14711` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Fix 5 residual identities were reconstructed from its hash-pinned original captures, static overlay and gap provenance using the exact embedded Fix 5 parser. The reconstruction must reproduce 23,761 admitted B1 slots and the 13,853 fixed residual before any live hypothesis is calculated. INVALID_ID is never admitted. Expansion admission is unanimous, and collector fallback is excluded.

No correctness labels, oracle data, label joins, Docker, benchmark execution, quarantined attempts, or post-hoc quantities were used.
