# Rerun arm results

## Decisions

| accounting | scope | ACCEPT | FLAG | REJECT |
| --- | --- | --- | --- | --- |
| S_invalid_excluded | all | 5 | 42 | 45 |
| S_invalid_excluded | patch | 5 | 42 | 4 |
| S_invalid_excluded | no_patch | 0 | 0 | 40 |
| S_invalid_excluded | provider_blocked | 0 | 0 | 1 |
| S_invalid_excluded | agent_infrastructure | 0 | 0 | 0 |
| S_invalid_missing | all | 5 | 42 | 45 |
| S_invalid_missing | patch | 5 | 42 | 4 |
| S_invalid_missing | no_patch | 0 | 0 | 40 |
| S_invalid_missing | provider_blocked | 0 | 0 | 1 |
| S_invalid_missing | agent_infrastructure | 0 | 0 | 0 |
| C_invalid_excluded | all | 20 | 27 | 45 |
| C_invalid_excluded | patch | 20 | 27 | 4 |
| C_invalid_excluded | no_patch | 0 | 0 | 40 |
| C_invalid_excluded | provider_blocked | 0 | 0 | 1 |
| C_invalid_excluded | agent_infrastructure | 0 | 0 | 0 |
| C_invalid_missing | all | 13 | 34 | 45 |
| C_invalid_missing | patch | 13 | 34 | 4 |
| C_invalid_missing | no_patch | 0 | 0 | 40 |
| C_invalid_missing | provider_blocked | 0 | 0 | 1 |
| C_invalid_missing | agent_infrastructure | 0 | 0 | 0 |

## Leakage

| kind | instance_id | role | findings |
| --- | --- | --- | --- |
| T3_name | django__django-15103 | generator | 1 |
| T3_name | django__django-15499 | generator | 1 |
| T3_name | matplotlib__matplotlib-24627 | generator | 1 |
| T3_name | matplotlib__matplotlib-24637 | generator | 1 |
| T3_name | matplotlib__matplotlib-24637 | repair | 1 |
| T3_content | astropy__astropy-14365 | generator | 1 |
| T3_content | astropy__astropy-14365 | repair | 1 |
| T3_content | django__django-11095 | generator | 3 |
| T3_content | django__django-11095 | repair | 1 |
| T3_content | django__django-12965 | generator | 1 |
| T3_content | django__django-13023 | generator | 1 |
| T3_content | django__django-13158 | generator | 1 |
| T3_content | django__django-13212 | generator | 2 |
| T3_content | django__django-13212 | repair | 3 |
| T3_content | django__django-13786 | generator | 3 |
| T3_content | django__django-13786 | repair | 2 |
| T3_content | django__django-13807 | generator | 6 |
| T3_content | django__django-13820 | generator | 2 |
| T3_content | django__django-13820 | repair | 2 |
| T3_content | django__django-14140 | generator | 1 |
| T3_content | django__django-14631 | repair | 2 |
| T3_content | django__django-15103 | generator | 3 |
| T3_content | django__django-15103 | repair | 1 |
| T3_content | django__django-15499 | generator | 2 |
| T3_content | django__django-15499 | repair | 1 |
| T3_content | django__django-15572 | generator | 3 |
| T3_content | django__django-15572 | repair | 2 |
| T3_content | django__django-16631 | generator | 9 |
| T3_content | django__django-16631 | repair | 1 |
| T3_content | matplotlib__matplotlib-21568 | repair | 1 |
| T3_content | matplotlib__matplotlib-22871 | generator | 1 |
| T3_content | matplotlib__matplotlib-23476 | generator | 1 |
| T3_content | matplotlib__matplotlib-24026 | generator | 3 |
| T3_content | matplotlib__matplotlib-24627 | generator | 1 |
| T3_content | matplotlib__matplotlib-24637 | generator | 1 |
| T3_content | matplotlib__matplotlib-25122 | generator | 2 |
| T3_content | matplotlib__matplotlib-25479 | generator | 1 |
| T3_content | matplotlib__matplotlib-26291 | generator | 1 |
| T3_content | pylint-dev__pylint-7277 | generator | 1 |
| T3_content | pytest-dev__pytest-5809 | generator | 1 |
| T3_content | scikit-learn__scikit-learn-14141 | generator | 1 |
| T3_content | sphinx-doc__sphinx-10435 | repair | 1 |
| T3_content | sphinx-doc__sphinx-10466 | generator | 1 |
| T3_content | sympy__sympy-13480 | generator | 2 |
| T3_content | sympy__sympy-13480 | repair | 1 |
| awareness | astropy__astropy-13398 | repair | 1 |
| awareness | astropy__astropy-14508 | repair | 1 |
| awareness | django__django-12965 | generator | 1 |
| awareness | django__django-13158 | repair | 1 |
| awareness | django__django-13212 | generator | 2 |
| awareness | django__django-13297 | generator | 2 |
| awareness | django__django-13820 | generator | 3 |
| awareness | django__django-13820 | repair | 1 |
| awareness | django__django-14140 | generator | 4 |
| awareness | django__django-15103 | generator | 1 |
| awareness | django__django-15278 | generator | 2 |
| awareness | django__django-15572 | generator | 3 |
| awareness | django__django-16082 | generator | 1 |
| awareness | django__django-16631 | generator | 2 |
| awareness | django__django-16631 | repair | 1 |
| awareness | matplotlib__matplotlib-20488 | generator | 1 |
| awareness | matplotlib__matplotlib-22871 | generator | 4 |
| awareness | matplotlib__matplotlib-23476 | generator | 2 |
| awareness | matplotlib__matplotlib-23476 | repair | 1 |
| awareness | matplotlib__matplotlib-24627 | generator | 3 |
| awareness | matplotlib__matplotlib-24627 | repair | 4 |
| awareness | matplotlib__matplotlib-24637 | generator | 1 |
| awareness | matplotlib__matplotlib-24637 | repair | 1 |
| awareness | matplotlib__matplotlib-25122 | generator | 2 |
| awareness | matplotlib__matplotlib-25479 | generator | 3 |
| awareness | matplotlib__matplotlib-25479 | repair | 1 |
| awareness | matplotlib__matplotlib-26291 | generator | 1 |
| awareness | matplotlib__matplotlib-26291 | repair | 1 |
| awareness | pydata__xarray-6744 | generator | 1 |
| awareness | pydata__xarray-6744 | repair | 1 |
| awareness | pylint-dev__pylint-6903 | generator | 2 |
| awareness | pylint-dev__pylint-6903 | repair | 1 |
| awareness | pylint-dev__pylint-7277 | generator | 1 |
| awareness | pytest-dev__pytest-5809 | repair | 2 |
| awareness | pytest-dev__pytest-6202 | generator | 2 |
| awareness | pytest-dev__pytest-7236 | generator | 2 |
| awareness | pytest-dev__pytest-7521 | repair | 1 |
| awareness | sphinx-doc__sphinx-10323 | generator | 2 |
| awareness | sphinx-doc__sphinx-10435 | repair | 1 |
| awareness | sphinx-doc__sphinx-10466 | generator | 3 |
| awareness | sphinx-doc__sphinx-7910 | generator | 2 |
| awareness | sympy__sympy-19783 | generator | 1 |
| awareness | sympy__sympy-19783 | repair | 1 |

## Leakage counts

| kind | tasks | findings |
| --- | --- | --- |
| T3_name | 4 | 5 |
| T3_content | 30 | 74 |
| T4 | 0 | 0 |
| awareness | 33 | 74 |

## Patch tasks

| instance_id | decision | correctness |
| --- | --- | --- |
| astropy__astropy-13398 | FLAG | wrong |
| astropy__astropy-14365 | ACCEPT | wrong |
| astropy__astropy-14508 | FLAG | wrong |
| astropy__astropy-7606 | FLAG | correct |
| django__django-11095 | FLAG | correct |
| django__django-12965 | FLAG | wrong |
| django__django-13023 | REJECT | wrong |
| django__django-13158 | FLAG | wrong |
| django__django-13212 | FLAG | wrong |
| django__django-13297 | FLAG | wrong |
| django__django-13786 | FLAG | wrong |
| django__django-13807 | FLAG | wrong |
| django__django-13820 | ACCEPT | correct |
| django__django-14140 | FLAG | wrong |
| django__django-15103 | FLAG | wrong |
| django__django-15278 | FLAG | correct |
| django__django-15499 | FLAG | correct |
| django__django-15572 | FLAG | correct |
| django__django-16082 | FLAG | correct |
| django__django-16255 | ACCEPT | correct |
| django__django-16612 | FLAG | correct |
| django__django-16631 | REJECT | wrong |
| django__django-16667 | REJECT | wrong |
| matplotlib__matplotlib-20488 | FLAG | wrong |
| matplotlib__matplotlib-22871 | FLAG | wrong |
| matplotlib__matplotlib-23476 | FLAG | wrong |
| matplotlib__matplotlib-24026 | FLAG | correct |
| matplotlib__matplotlib-24627 | FLAG | correct |
| matplotlib__matplotlib-24637 | REJECT | wrong |
| matplotlib__matplotlib-24970 | FLAG | correct |
| matplotlib__matplotlib-25122 | FLAG | correct |
| matplotlib__matplotlib-25287 | FLAG | correct |
| matplotlib__matplotlib-25332 | FLAG | correct |
| matplotlib__matplotlib-25479 | FLAG | wrong |
| matplotlib__matplotlib-26291 | FLAG | wrong |
| pydata__xarray-6744 | FLAG | wrong |
| pylint-dev__pylint-6903 | FLAG | correct |
| pylint-dev__pylint-7277 | FLAG | wrong |
| pytest-dev__pytest-5809 | FLAG | correct |
| pytest-dev__pytest-6202 | FLAG | correct |
| pytest-dev__pytest-7236 | FLAG | correct |
| pytest-dev__pytest-7432 | FLAG | correct |
| pytest-dev__pytest-7521 | FLAG | correct |
| scikit-learn__scikit-learn-10908 | ACCEPT | correct |
| scikit-learn__scikit-learn-12585 | FLAG | correct |
| scikit-learn__scikit-learn-14141 | ACCEPT | correct |
| sphinx-doc__sphinx-10323 | FLAG | wrong |
| sphinx-doc__sphinx-10466 | FLAG | wrong |
| sphinx-doc__sphinx-7910 | FLAG | wrong |
| sympy__sympy-13480 | FLAG | correct |
| sympy__sympy-19783 | FLAG | wrong |

## Decision by correctness

| accounting | cohort | decision | correct | wrong |
| --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | ACCEPT | 4 | 1 |
| S_invalid_excluded | primary | FLAG | 21 | 21 |
| S_invalid_excluded | primary | REJECT | 0 | 4 |
| S_invalid_excluded | including_no_patch | ACCEPT | 4 | 1 |
| S_invalid_excluded | including_no_patch | FLAG | 21 | 21 |
| S_invalid_excluded | including_no_patch | REJECT | 0 | 44 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | ACCEPT | 4 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | FLAG | 21 | 21 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | REJECT | 0 | 45 |
| S_invalid_excluded | excluding_T4 | ACCEPT | 4 | 1 |
| S_invalid_excluded | excluding_T4 | FLAG | 21 | 21 |
| S_invalid_excluded | excluding_T4 | REJECT | 0 | 4 |
| S_invalid_excluded | excluding_T4_and_T3_name | ACCEPT | 4 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | FLAG | 19 | 20 |
| S_invalid_excluded | excluding_T4_and_T3_name | REJECT | 0 | 3 |
| S_invalid_missing | primary | ACCEPT | 4 | 1 |
| S_invalid_missing | primary | FLAG | 21 | 21 |
| S_invalid_missing | primary | REJECT | 0 | 4 |
| S_invalid_missing | including_no_patch | ACCEPT | 4 | 1 |
| S_invalid_missing | including_no_patch | FLAG | 21 | 21 |
| S_invalid_missing | including_no_patch | REJECT | 0 | 44 |
| S_invalid_missing | including_no_patch_and_provider_blocked | ACCEPT | 4 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | FLAG | 21 | 21 |
| S_invalid_missing | including_no_patch_and_provider_blocked | REJECT | 0 | 45 |
| S_invalid_missing | excluding_T4 | ACCEPT | 4 | 1 |
| S_invalid_missing | excluding_T4 | FLAG | 21 | 21 |
| S_invalid_missing | excluding_T4 | REJECT | 0 | 4 |
| S_invalid_missing | excluding_T4_and_T3_name | ACCEPT | 4 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | FLAG | 19 | 20 |
| S_invalid_missing | excluding_T4_and_T3_name | REJECT | 0 | 3 |
| C_invalid_excluded | primary | ACCEPT | 16 | 4 |
| C_invalid_excluded | primary | FLAG | 9 | 18 |
| C_invalid_excluded | primary | REJECT | 0 | 4 |
| C_invalid_excluded | including_no_patch | ACCEPT | 16 | 4 |
| C_invalid_excluded | including_no_patch | FLAG | 9 | 18 |
| C_invalid_excluded | including_no_patch | REJECT | 0 | 44 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | ACCEPT | 16 | 4 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | FLAG | 9 | 18 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | REJECT | 0 | 45 |
| C_invalid_excluded | excluding_T4 | ACCEPT | 16 | 4 |
| C_invalid_excluded | excluding_T4 | FLAG | 9 | 18 |
| C_invalid_excluded | excluding_T4 | REJECT | 0 | 4 |
| C_invalid_excluded | excluding_T4_and_T3_name | ACCEPT | 16 | 4 |
| C_invalid_excluded | excluding_T4_and_T3_name | FLAG | 7 | 17 |
| C_invalid_excluded | excluding_T4_and_T3_name | REJECT | 0 | 3 |
| C_invalid_missing | primary | ACCEPT | 9 | 4 |
| C_invalid_missing | primary | FLAG | 16 | 18 |
| C_invalid_missing | primary | REJECT | 0 | 4 |
| C_invalid_missing | including_no_patch | ACCEPT | 9 | 4 |
| C_invalid_missing | including_no_patch | FLAG | 16 | 18 |
| C_invalid_missing | including_no_patch | REJECT | 0 | 44 |
| C_invalid_missing | including_no_patch_and_provider_blocked | ACCEPT | 9 | 4 |
| C_invalid_missing | including_no_patch_and_provider_blocked | FLAG | 16 | 18 |
| C_invalid_missing | including_no_patch_and_provider_blocked | REJECT | 0 | 45 |
| C_invalid_missing | excluding_T4 | ACCEPT | 9 | 4 |
| C_invalid_missing | excluding_T4 | FLAG | 16 | 18 |
| C_invalid_missing | excluding_T4 | REJECT | 0 | 4 |
| C_invalid_missing | excluding_T4_and_T3_name | ACCEPT | 9 | 4 |
| C_invalid_missing | excluding_T4_and_T3_name | FLAG | 14 | 17 |
| C_invalid_missing | excluding_T4_and_T3_name | REJECT | 0 | 3 |

## Metrics

| accounting | cohort | metric | k | n | reference_k | reference_n | estimate | lower | upper | method |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_excluded | primary | base_rate | 25 | 51 |  |  | 0.490196078 | 0.358574858 | 0.623190762 | Wilson 95% |
| S_invalid_excluded | primary | wrong_not_accepted | 25 | 26 |  |  | 0.961538462 | 0.811072209 | 0.993178015 | Wilson 95% |
| S_invalid_excluded | primary | all_not_accepted | 46 | 51 |  |  | 0.901960784 | 0.790217652 | 0.957391927 | Wilson 95% |
| S_invalid_excluded | primary | correct_not_accepted | 21 | 25 |  |  | 0.84 | 0.653463782 | 0.935965486 | Wilson 95% |
| S_invalid_excluded | primary | chance_difference | 25 | 26 | 46 | 51 | 0.0595776772 | -0.100774138 | 0.175713757 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_excluded | primary | wrong_correct_difference | 25 | 26 | 21 | 25 | 0.121538462 | -0.0569257297 | 0.310738942 | Newcombe 10 95% |
| S_invalid_excluded | primary | fisher_exact_p |  |  |  |  | 0.1906337 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_excluded | including_no_patch | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_excluded | including_no_patch | base_rate | 25 | 91 |  |  | 0.274725275 | 0.193551783 | 0.374147824 | Wilson 95% |
| S_invalid_excluded | including_no_patch | wrong_not_accepted | 65 | 66 |  |  | 0.984848485 | 0.919040797 | 0.997320359 | Wilson 95% |
| S_invalid_excluded | including_no_patch | all_not_accepted | 86 | 91 |  |  | 0.945054945 | 0.877751975 | 0.9763049 | Wilson 95% |
| S_invalid_excluded | including_no_patch | correct_not_accepted | 21 | 25 |  |  | 0.84 | 0.653463782 | 0.935965486 | Wilson 95% |
| S_invalid_excluded | including_no_patch | chance_difference | 65 | 66 | 86 | 91 | 0.0397935398 | -0.0330570714 | 0.108242334 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_excluded | including_no_patch | wrong_correct_difference | 65 | 66 | 21 | 25 | 0.144848485 | 0.0284868661 | 0.331801175 | Newcombe 10 95% |
| S_invalid_excluded | including_no_patch | fisher_exact_p |  |  |  |  | 0.0190955886 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_excluded | including_no_patch_and_provider_blocked | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_excluded | including_no_patch_and_provider_blocked | base_rate | 25 | 92 |  |  | 0.27173913 | 0.191357756 | 0.370418531 | Wilson 95% |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong_not_accepted | 66 | 67 |  |  | 0.985074627 | 0.920181376 | 0.997360428 | Wilson 95% |
| S_invalid_excluded | including_no_patch_and_provider_blocked | all_not_accepted | 87 | 92 |  |  | 0.945652174 | 0.879014695 | 0.976564936 | Wilson 95% |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct_not_accepted | 21 | 25 |  |  | 0.84 | 0.653463782 | 0.935965486 | Wilson 95% |
| S_invalid_excluded | including_no_patch_and_provider_blocked | chance_difference | 66 | 67 | 87 | 92 | 0.039422453 | -0.0324575365 | 0.107183021 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong_correct_difference | 66 | 67 | 21 | 25 | 0.145074627 | 0.0292277085 | 0.332014996 | Newcombe 10 95% |
| S_invalid_excluded | including_no_patch_and_provider_blocked | fisher_exact_p |  |  |  |  | 0.0183150183 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_excluded | excluding_T4 | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_excluded | excluding_T4 | base_rate | 25 | 51 |  |  | 0.490196078 | 0.358574858 | 0.623190762 | Wilson 95% |
| S_invalid_excluded | excluding_T4 | wrong_not_accepted | 25 | 26 |  |  | 0.961538462 | 0.811072209 | 0.993178015 | Wilson 95% |
| S_invalid_excluded | excluding_T4 | all_not_accepted | 46 | 51 |  |  | 0.901960784 | 0.790217652 | 0.957391927 | Wilson 95% |
| S_invalid_excluded | excluding_T4 | correct_not_accepted | 21 | 25 |  |  | 0.84 | 0.653463782 | 0.935965486 | Wilson 95% |
| S_invalid_excluded | excluding_T4 | chance_difference | 25 | 26 | 46 | 51 | 0.0595776772 | -0.100774138 | 0.175713757 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_excluded | excluding_T4 | wrong_correct_difference | 25 | 26 | 21 | 25 | 0.121538462 | -0.0569257297 | 0.310738942 | Newcombe 10 95% |
| S_invalid_excluded | excluding_T4 | fisher_exact_p |  |  |  |  | 0.1906337 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_excluded | excluding_T4_and_T3_name | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_excluded | excluding_T4_and_T3_name | base_rate | 23 | 47 |  |  | 0.489361702 | 0.352755549 | 0.627575464 | Wilson 95% |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong_not_accepted | 23 | 24 |  |  | 0.958333333 | 0.797581933 | 0.992606544 | Wilson 95% |
| S_invalid_excluded | excluding_T4_and_T3_name | all_not_accepted | 42 | 47 |  |  | 0.893617021 | 0.774057305 | 0.953695218 | Wilson 95% |
| S_invalid_excluded | excluding_T4_and_T3_name | correct_not_accepted | 19 | 23 |  |  | 0.826086957 | 0.628623522 | 0.930213465 | Wilson 95% |
| S_invalid_excluded | excluding_T4_and_T3_name | chance_difference | 23 | 24 | 42 | 47 | 0.0647163121 | -0.106894883 | 0.189091465 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong_correct_difference | 23 | 24 | 19 | 23 | 0.132246377 | -0.0592825827 | 0.332662097 | Newcombe 10 95% |
| S_invalid_excluded | excluding_T4_and_T3_name | fisher_exact_p |  |  |  |  | 0.188190665 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_missing | primary | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_missing | primary | base_rate | 25 | 51 |  |  | 0.490196078 | 0.358574858 | 0.623190762 | Wilson 95% |
| S_invalid_missing | primary | wrong_not_accepted | 25 | 26 |  |  | 0.961538462 | 0.811072209 | 0.993178015 | Wilson 95% |
| S_invalid_missing | primary | all_not_accepted | 46 | 51 |  |  | 0.901960784 | 0.790217652 | 0.957391927 | Wilson 95% |
| S_invalid_missing | primary | correct_not_accepted | 21 | 25 |  |  | 0.84 | 0.653463782 | 0.935965486 | Wilson 95% |
| S_invalid_missing | primary | chance_difference | 25 | 26 | 46 | 51 | 0.0595776772 | -0.100774138 | 0.175713757 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_missing | primary | wrong_correct_difference | 25 | 26 | 21 | 25 | 0.121538462 | -0.0569257297 | 0.310738942 | Newcombe 10 95% |
| S_invalid_missing | primary | fisher_exact_p |  |  |  |  | 0.1906337 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_missing | including_no_patch | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_missing | including_no_patch | base_rate | 25 | 91 |  |  | 0.274725275 | 0.193551783 | 0.374147824 | Wilson 95% |
| S_invalid_missing | including_no_patch | wrong_not_accepted | 65 | 66 |  |  | 0.984848485 | 0.919040797 | 0.997320359 | Wilson 95% |
| S_invalid_missing | including_no_patch | all_not_accepted | 86 | 91 |  |  | 0.945054945 | 0.877751975 | 0.9763049 | Wilson 95% |
| S_invalid_missing | including_no_patch | correct_not_accepted | 21 | 25 |  |  | 0.84 | 0.653463782 | 0.935965486 | Wilson 95% |
| S_invalid_missing | including_no_patch | chance_difference | 65 | 66 | 86 | 91 | 0.0397935398 | -0.0330570714 | 0.108242334 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_missing | including_no_patch | wrong_correct_difference | 65 | 66 | 21 | 25 | 0.144848485 | 0.0284868661 | 0.331801175 | Newcombe 10 95% |
| S_invalid_missing | including_no_patch | fisher_exact_p |  |  |  |  | 0.0190955886 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_missing | including_no_patch_and_provider_blocked | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_missing | including_no_patch_and_provider_blocked | base_rate | 25 | 92 |  |  | 0.27173913 | 0.191357756 | 0.370418531 | Wilson 95% |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong_not_accepted | 66 | 67 |  |  | 0.985074627 | 0.920181376 | 0.997360428 | Wilson 95% |
| S_invalid_missing | including_no_patch_and_provider_blocked | all_not_accepted | 87 | 92 |  |  | 0.945652174 | 0.879014695 | 0.976564936 | Wilson 95% |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct_not_accepted | 21 | 25 |  |  | 0.84 | 0.653463782 | 0.935965486 | Wilson 95% |
| S_invalid_missing | including_no_patch_and_provider_blocked | chance_difference | 66 | 67 | 87 | 92 | 0.039422453 | -0.0324575365 | 0.107183021 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong_correct_difference | 66 | 67 | 21 | 25 | 0.145074627 | 0.0292277085 | 0.332014996 | Newcombe 10 95% |
| S_invalid_missing | including_no_patch_and_provider_blocked | fisher_exact_p |  |  |  |  | 0.0183150183 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_missing | excluding_T4 | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_missing | excluding_T4 | base_rate | 25 | 51 |  |  | 0.490196078 | 0.358574858 | 0.623190762 | Wilson 95% |
| S_invalid_missing | excluding_T4 | wrong_not_accepted | 25 | 26 |  |  | 0.961538462 | 0.811072209 | 0.993178015 | Wilson 95% |
| S_invalid_missing | excluding_T4 | all_not_accepted | 46 | 51 |  |  | 0.901960784 | 0.790217652 | 0.957391927 | Wilson 95% |
| S_invalid_missing | excluding_T4 | correct_not_accepted | 21 | 25 |  |  | 0.84 | 0.653463782 | 0.935965486 | Wilson 95% |
| S_invalid_missing | excluding_T4 | chance_difference | 25 | 26 | 46 | 51 | 0.0595776772 | -0.100774138 | 0.175713757 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_missing | excluding_T4 | wrong_correct_difference | 25 | 26 | 21 | 25 | 0.121538462 | -0.0569257297 | 0.310738942 | Newcombe 10 95% |
| S_invalid_missing | excluding_T4 | fisher_exact_p |  |  |  |  | 0.1906337 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| S_invalid_missing | excluding_T4_and_T3_name | accept_precision | 4 | 5 |  |  | 0.8 | 0.375534627 | 0.963775892 | Wilson 95% |
| S_invalid_missing | excluding_T4_and_T3_name | base_rate | 23 | 47 |  |  | 0.489361702 | 0.352755549 | 0.627575464 | Wilson 95% |
| S_invalid_missing | excluding_T4_and_T3_name | wrong_not_accepted | 23 | 24 |  |  | 0.958333333 | 0.797581933 | 0.992606544 | Wilson 95% |
| S_invalid_missing | excluding_T4_and_T3_name | all_not_accepted | 42 | 47 |  |  | 0.893617021 | 0.774057305 | 0.953695218 | Wilson 95% |
| S_invalid_missing | excluding_T4_and_T3_name | correct_not_accepted | 19 | 23 |  |  | 0.826086957 | 0.628623522 | 0.930213465 | Wilson 95% |
| S_invalid_missing | excluding_T4_and_T3_name | chance_difference | 23 | 24 | 42 | 47 | 0.0647163121 | -0.106894883 | 0.189091465 | Newcombe 10 95% (approximate, overlapping cohorts) |
| S_invalid_missing | excluding_T4_and_T3_name | wrong_correct_difference | 23 | 24 | 19 | 23 | 0.132246377 | -0.0592825827 | 0.332662097 | Newcombe 10 95% |
| S_invalid_missing | excluding_T4_and_T3_name | fisher_exact_p |  |  |  |  | 0.188190665 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_excluded | primary | accept_precision | 16 | 20 |  |  | 0.8 | 0.583982566 | 0.919342338 | Wilson 95% |
| C_invalid_excluded | primary | base_rate | 25 | 51 |  |  | 0.490196078 | 0.358574858 | 0.623190762 | Wilson 95% |
| C_invalid_excluded | primary | wrong_not_accepted | 22 | 26 |  |  | 0.846153846 | 0.664688005 | 0.938499663 | Wilson 95% |
| C_invalid_excluded | primary | all_not_accepted | 31 | 51 |  |  | 0.607843137 | 0.470851589 | 0.729726591 | Wilson 95% |
| C_invalid_excluded | primary | correct_not_accepted | 9 | 25 |  |  | 0.36 | 0.202478807 | 0.554815024 | Wilson 95% |
| C_invalid_excluded | primary | chance_difference | 22 | 26 | 31 | 51 | 0.238310709 | 0.0197119262 | 0.403520982 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_excluded | primary | wrong_correct_difference | 22 | 26 | 9 | 25 | 0.486153846 | 0.21991571 | 0.66874814 | Newcombe 10 95% |
| C_invalid_excluded | primary | fisher_exact_p |  |  |  |  | 0.000531207797 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_excluded | including_no_patch | accept_precision | 16 | 20 |  |  | 0.8 | 0.583982566 | 0.919342338 | Wilson 95% |
| C_invalid_excluded | including_no_patch | base_rate | 25 | 91 |  |  | 0.274725275 | 0.193551783 | 0.374147824 | Wilson 95% |
| C_invalid_excluded | including_no_patch | wrong_not_accepted | 62 | 66 |  |  | 0.939393939 | 0.854270912 | 0.976181385 | Wilson 95% |
| C_invalid_excluded | including_no_patch | all_not_accepted | 71 | 91 |  |  | 0.78021978 | 0.684760761 | 0.852978753 | Wilson 95% |
| C_invalid_excluded | including_no_patch | correct_not_accepted | 9 | 25 |  |  | 0.36 | 0.202478807 | 0.554815024 | Wilson 95% |
| C_invalid_excluded | including_no_patch | chance_difference | 62 | 66 | 71 | 91 | 0.159174159 | 0.0471929206 | 0.261476361 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_excluded | including_no_patch | wrong_correct_difference | 62 | 66 | 9 | 25 | 0.579393939 | 0.366793791 | 0.741153769 | Newcombe 10 95% |
| C_invalid_excluded | including_no_patch | fisher_exact_p |  |  |  |  | 2.33075208e-08 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_excluded | including_no_patch_and_provider_blocked | accept_precision | 16 | 20 |  |  | 0.8 | 0.583982566 | 0.919342338 | Wilson 95% |
| C_invalid_excluded | including_no_patch_and_provider_blocked | base_rate | 25 | 92 |  |  | 0.27173913 | 0.191357756 | 0.370418531 | Wilson 95% |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong_not_accepted | 63 | 67 |  |  | 0.940298507 | 0.856304989 | 0.976540649 | Wilson 95% |
| C_invalid_excluded | including_no_patch_and_provider_blocked | all_not_accepted | 72 | 92 |  |  | 0.782608696 | 0.687929988 | 0.854632704 | Wilson 95% |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct_not_accepted | 9 | 25 |  |  | 0.36 | 0.202478807 | 0.554815024 | Wilson 95% |
| C_invalid_excluded | including_no_patch_and_provider_blocked | chance_difference | 63 | 67 | 72 | 92 | 0.157689812 | 0.0470445723 | 0.259068066 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong_correct_difference | 63 | 67 | 9 | 25 | 0.580298507 | 0.368148078 | 0.741935196 | Newcombe 10 95% |
| C_invalid_excluded | including_no_patch_and_provider_blocked | fisher_exact_p |  |  |  |  | 1.93885449e-08 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_excluded | excluding_T4 | accept_precision | 16 | 20 |  |  | 0.8 | 0.583982566 | 0.919342338 | Wilson 95% |
| C_invalid_excluded | excluding_T4 | base_rate | 25 | 51 |  |  | 0.490196078 | 0.358574858 | 0.623190762 | Wilson 95% |
| C_invalid_excluded | excluding_T4 | wrong_not_accepted | 22 | 26 |  |  | 0.846153846 | 0.664688005 | 0.938499663 | Wilson 95% |
| C_invalid_excluded | excluding_T4 | all_not_accepted | 31 | 51 |  |  | 0.607843137 | 0.470851589 | 0.729726591 | Wilson 95% |
| C_invalid_excluded | excluding_T4 | correct_not_accepted | 9 | 25 |  |  | 0.36 | 0.202478807 | 0.554815024 | Wilson 95% |
| C_invalid_excluded | excluding_T4 | chance_difference | 22 | 26 | 31 | 51 | 0.238310709 | 0.0197119262 | 0.403520982 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_excluded | excluding_T4 | wrong_correct_difference | 22 | 26 | 9 | 25 | 0.486153846 | 0.21991571 | 0.66874814 | Newcombe 10 95% |
| C_invalid_excluded | excluding_T4 | fisher_exact_p |  |  |  |  | 0.000531207797 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_excluded | excluding_T4_and_T3_name | accept_precision | 16 | 20 |  |  | 0.8 | 0.583982566 | 0.919342338 | Wilson 95% |
| C_invalid_excluded | excluding_T4_and_T3_name | base_rate | 23 | 47 |  |  | 0.489361702 | 0.352755549 | 0.627575464 | Wilson 95% |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong_not_accepted | 20 | 24 |  |  | 0.833333333 | 0.641469292 | 0.933213237 | Wilson 95% |
| C_invalid_excluded | excluding_T4_and_T3_name | all_not_accepted | 27 | 47 |  |  | 0.574468085 | 0.432819192 | 0.704863717 | Wilson 95% |
| C_invalid_excluded | excluding_T4_and_T3_name | correct_not_accepted | 7 | 23 |  |  | 0.304347826 | 0.156040244 | 0.508657564 | Wilson 95% |
| C_invalid_excluded | excluding_T4_and_T3_name | chance_difference | 20 | 24 | 27 | 47 | 0.258865248 | 0.026885009 | 0.432186926 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong_correct_difference | 20 | 24 | 7 | 23 | 0.528985507 | 0.248710143 | 0.707790245 | Newcombe 10 95% |
| C_invalid_excluded | excluding_T4_and_T3_name | fisher_exact_p |  |  |  |  | 0.000355119573 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_missing | primary | accept_precision | 9 | 13 |  |  | 0.692307692 | 0.42369343 | 0.873192964 | Wilson 95% |
| C_invalid_missing | primary | base_rate | 25 | 51 |  |  | 0.490196078 | 0.358574858 | 0.623190762 | Wilson 95% |
| C_invalid_missing | primary | wrong_not_accepted | 22 | 26 |  |  | 0.846153846 | 0.664688005 | 0.938499663 | Wilson 95% |
| C_invalid_missing | primary | all_not_accepted | 38 | 51 |  |  | 0.745098039 | 0.61131718 | 0.844542319 | Wilson 95% |
| C_invalid_missing | primary | correct_not_accepted | 16 | 25 |  |  | 0.64 | 0.445184976 | 0.797521193 | Wilson 95% |
| C_invalid_missing | primary | chance_difference | 22 | 26 | 38 | 51 | 0.101055807 | -0.105871756 | 0.263613698 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_missing | primary | wrong_correct_difference | 22 | 26 | 16 | 25 | 0.206153846 | -0.0341434235 | 0.421747546 | Newcombe 10 95% |
| C_invalid_missing | primary | fisher_exact_p |  |  |  |  | 0.116358664 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_missing | including_no_patch | accept_precision | 9 | 13 |  |  | 0.692307692 | 0.42369343 | 0.873192964 | Wilson 95% |
| C_invalid_missing | including_no_patch | base_rate | 25 | 91 |  |  | 0.274725275 | 0.193551783 | 0.374147824 | Wilson 95% |
| C_invalid_missing | including_no_patch | wrong_not_accepted | 62 | 66 |  |  | 0.939393939 | 0.854270912 | 0.976181385 | Wilson 95% |
| C_invalid_missing | including_no_patch | all_not_accepted | 78 | 91 |  |  | 0.857142857 | 0.770781863 | 0.914572419 | Wilson 95% |
| C_invalid_missing | including_no_patch | correct_not_accepted | 16 | 25 |  |  | 0.64 | 0.445184976 | 0.797521193 | Wilson 95% |
| C_invalid_missing | including_no_patch | chance_difference | 62 | 66 | 78 | 91 | 0.0822510823 | -0.0204333095 | 0.176120872 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_missing | including_no_patch | wrong_correct_difference | 62 | 66 | 16 | 25 | 0.299393939 | 0.120344069 | 0.497651877 | Newcombe 10 95% |
| C_invalid_missing | including_no_patch | fisher_exact_p |  |  |  |  | 0.000851152877 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_missing | including_no_patch_and_provider_blocked | accept_precision | 9 | 13 |  |  | 0.692307692 | 0.42369343 | 0.873192964 | Wilson 95% |
| C_invalid_missing | including_no_patch_and_provider_blocked | base_rate | 25 | 92 |  |  | 0.27173913 | 0.191357756 | 0.370418531 | Wilson 95% |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong_not_accepted | 63 | 67 |  |  | 0.940298507 | 0.856304989 | 0.976540649 | Wilson 95% |
| C_invalid_missing | including_no_patch_and_provider_blocked | all_not_accepted | 79 | 92 |  |  | 0.858695652 | 0.773114197 | 0.915523067 | Wilson 95% |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct_not_accepted | 16 | 25 |  |  | 0.64 | 0.445184976 | 0.797521193 | Wilson 95% |
| C_invalid_missing | including_no_patch_and_provider_blocked | chance_difference | 63 | 67 | 79 | 92 | 0.0816028553 | -0.019808516 | 0.174541966 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong_correct_difference | 63 | 67 | 16 | 25 | 0.300298507 | 0.121782857 | 0.498455986 | Newcombe 10 95% |
| C_invalid_missing | including_no_patch_and_provider_blocked | fisher_exact_p |  |  |  |  | 0.000776025524 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_missing | excluding_T4 | accept_precision | 9 | 13 |  |  | 0.692307692 | 0.42369343 | 0.873192964 | Wilson 95% |
| C_invalid_missing | excluding_T4 | base_rate | 25 | 51 |  |  | 0.490196078 | 0.358574858 | 0.623190762 | Wilson 95% |
| C_invalid_missing | excluding_T4 | wrong_not_accepted | 22 | 26 |  |  | 0.846153846 | 0.664688005 | 0.938499663 | Wilson 95% |
| C_invalid_missing | excluding_T4 | all_not_accepted | 38 | 51 |  |  | 0.745098039 | 0.61131718 | 0.844542319 | Wilson 95% |
| C_invalid_missing | excluding_T4 | correct_not_accepted | 16 | 25 |  |  | 0.64 | 0.445184976 | 0.797521193 | Wilson 95% |
| C_invalid_missing | excluding_T4 | chance_difference | 22 | 26 | 38 | 51 | 0.101055807 | -0.105871756 | 0.263613698 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_missing | excluding_T4 | wrong_correct_difference | 22 | 26 | 16 | 25 | 0.206153846 | -0.0341434235 | 0.421747546 | Newcombe 10 95% |
| C_invalid_missing | excluding_T4 | fisher_exact_p |  |  |  |  | 0.116358664 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |
| C_invalid_missing | excluding_T4_and_T3_name | accept_precision | 9 | 13 |  |  | 0.692307692 | 0.42369343 | 0.873192964 | Wilson 95% |
| C_invalid_missing | excluding_T4_and_T3_name | base_rate | 23 | 47 |  |  | 0.489361702 | 0.352755549 | 0.627575464 | Wilson 95% |
| C_invalid_missing | excluding_T4_and_T3_name | wrong_not_accepted | 20 | 24 |  |  | 0.833333333 | 0.641469292 | 0.933213237 | Wilson 95% |
| C_invalid_missing | excluding_T4_and_T3_name | all_not_accepted | 34 | 47 |  |  | 0.723404255 | 0.582414363 | 0.830634367 | Wilson 95% |
| C_invalid_missing | excluding_T4_and_T3_name | correct_not_accepted | 14 | 23 |  |  | 0.608695652 | 0.407855222 | 0.778423773 | Wilson 95% |
| C_invalid_missing | excluding_T4_and_T3_name | chance_difference | 20 | 24 | 34 | 47 | 0.109929078 | -0.109866525 | 0.282712599 | Newcombe 10 95% (approximate, overlapping cohorts) |
| C_invalid_missing | excluding_T4_and_T3_name | wrong_correct_difference | 20 | 24 | 14 | 23 | 0.224637681 | -0.0315252464 | 0.448942994 | Newcombe 10 95% |
| C_invalid_missing | excluding_T4_and_T3_name | fisher_exact_p |  |  |  |  | 0.11071771 | NOT_AVAILABLE | NOT_AVAILABLE | Two-sided Fisher exact |

## Wrong types

| accounting | cohort | type | wrong | ACCEPT | FLAG | REJECT | not_accepted | rate | lower | upper |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| S_invalid_excluded | primary | U | 11 | 1 | 10 | 0 | 10 | 0.909090909 | 0.622641561 | 0.983767827 |
| S_invalid_excluded | primary | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_excluded | including_no_patch | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| S_invalid_excluded | including_no_patch | U | 11 | 1 | 10 | 0 | 10 | 0.909090909 | 0.622641561 | 0.983767827 |
| S_invalid_excluded | including_no_patch | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | U | 11 | 1 | 10 | 0 | 10 | 0.909090909 | 0.622641561 | 0.983767827 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_excluded | excluding_T4 | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| S_invalid_excluded | excluding_T4 | U | 11 | 1 | 10 | 0 | 10 | 0.909090909 | 0.622641561 | 0.983767827 |
| S_invalid_excluded | excluding_T4 | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | R | 11 | 0 | 10 | 1 | 11 | 1 | 0.74116703 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | U | 10 | 1 | 9 | 0 | 9 | 0.9 | 0.59584997 | 0.982123787 |
| S_invalid_excluded | excluding_T4_and_T3_name | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_missing | primary | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| S_invalid_missing | primary | U | 11 | 1 | 10 | 0 | 10 | 0.909090909 | 0.622641561 | 0.983767827 |
| S_invalid_missing | primary | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_missing | including_no_patch | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| S_invalid_missing | including_no_patch | U | 11 | 1 | 10 | 0 | 10 | 0.909090909 | 0.622641561 | 0.983767827 |
| S_invalid_missing | including_no_patch | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | U | 11 | 1 | 10 | 0 | 10 | 0.909090909 | 0.622641561 | 0.983767827 |
| S_invalid_missing | including_no_patch_and_provider_blocked | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_missing | excluding_T4 | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| S_invalid_missing | excluding_T4 | U | 11 | 1 | 10 | 0 | 10 | 0.909090909 | 0.622641561 | 0.983767827 |
| S_invalid_missing | excluding_T4 | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | R | 11 | 0 | 10 | 1 | 11 | 1 | 0.74116703 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | U | 10 | 1 | 9 | 0 | 9 | 0.9 | 0.59584997 | 0.982123787 |
| S_invalid_missing | excluding_T4_and_T3_name | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_excluded | primary | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| C_invalid_excluded | primary | U | 11 | 4 | 7 | 0 | 7 | 0.636363636 | 0.353801173 | 0.84833529 |
| C_invalid_excluded | primary | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_excluded | including_no_patch | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| C_invalid_excluded | including_no_patch | U | 11 | 4 | 7 | 0 | 7 | 0.636363636 | 0.353801173 | 0.84833529 |
| C_invalid_excluded | including_no_patch | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | U | 11 | 4 | 7 | 0 | 7 | 0.636363636 | 0.353801173 | 0.84833529 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_excluded | excluding_T4 | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| C_invalid_excluded | excluding_T4 | U | 11 | 4 | 7 | 0 | 7 | 0.636363636 | 0.353801173 | 0.84833529 |
| C_invalid_excluded | excluding_T4 | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | R | 11 | 0 | 10 | 1 | 11 | 1 | 0.74116703 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | U | 10 | 4 | 6 | 0 | 6 | 0.6 | 0.312673768 | 0.831819671 |
| C_invalid_excluded | excluding_T4_and_T3_name | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_missing | primary | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| C_invalid_missing | primary | U | 11 | 4 | 7 | 0 | 7 | 0.636363636 | 0.353801173 | 0.84833529 |
| C_invalid_missing | primary | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_missing | including_no_patch | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| C_invalid_missing | including_no_patch | U | 11 | 4 | 7 | 0 | 7 | 0.636363636 | 0.353801173 | 0.84833529 |
| C_invalid_missing | including_no_patch | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | U | 11 | 4 | 7 | 0 | 7 | 0.636363636 | 0.353801173 | 0.84833529 |
| C_invalid_missing | including_no_patch_and_provider_blocked | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_missing | excluding_T4 | R | 12 | 0 | 10 | 2 | 12 | 1 | 0.75750599 | 1 |
| C_invalid_missing | excluding_T4 | U | 11 | 4 | 7 | 0 | 7 | 0.636363636 | 0.353801173 | 0.84833529 |
| C_invalid_missing | excluding_T4 | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | R | 11 | 0 | 10 | 1 | 11 | 1 | 0.74116703 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | U | 10 | 4 | 6 | 0 | 6 | 0.6 | 0.312673768 | 0.831819671 |
| C_invalid_missing | excluding_T4_and_T3_name | X | 3 | 0 | 1 | 2 | 3 | 1 | 0.438502964 | 1 |

## Signal attribution

| accounting | cohort | instance_id | correctness | decision | signal | outcome | absence | absence_detail | decision_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak: skipped; base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak2: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_simple: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_2d: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_mixin: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_inlines: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_inlines: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_only: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_select_related: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_as_tables: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | primary | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | primary | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | primary | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | primary | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/basic/tests.py::ModelTest::test_emptyqs_distinct: skipped; base: tests/basic/tests.py::ConcurrentSaveTests::test_concurrent_delete_with_save: skipped; base: tests/custom_lookups/tests.py::LookupTests::test_birthdate_month: skipped; base: tests/custom_lookups/tests.py::DateTimeLookupTests::test_datetime_output_field: skipped; base: tests/custom_lookups/tests.py::YearLteTests::test_year_lte: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/postgresql/tests.py::Tests::test_nodb_cursor: skipped; base: tests/backends/postgresql/tests.py::Tests::test_database_name_too_long: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_and_rollback: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_non_autocommit: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_isolation_level: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/mysql/test_schema.py::SchemaEditorTests::test_quote_value: skipped; base: tests/schema/tests.py::SchemaTests::test_inline_fk: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_index_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_binaryfield_mediumblob: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_geom_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_geom_col_name: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_raster_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_blank_geom_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_blank_raster_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_ignores_non_existing_directories_two_levels: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_uses_existing_parent_directories: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_multiple_patterns: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_files: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_directory_globs: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/expressions/tests.py::ExpressionOperatorTests::test_lefthand_bitwise_xor_not_supported: skipped; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation_different_srid: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geography_value: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_update_from_other_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select_multiple: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_inline_add_another_widgets: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_modifier_allows_multiple_section: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | primary | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | primary | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | primary | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | primary | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | primary | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | primary | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | primary | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_backend_macosx.py::test_cached_renderer: skipped; base: lib/matplotlib/tests/test_backend_macosx.py::test_savefig_rcparam: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_fig_close: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_sigint: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_other_signal_before_sigint: skipped | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_axes.py::test_centered_bar_label_nonlinear: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_vertical[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_horizontal[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_rc[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_formatter_ticker[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | primary | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped; base: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray; patched: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/python/integration.py::TestMockDecoration::test_unittest_mock_and_pypi_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_sorting: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_double_patch_issue473: skipped; base: testing/test_terminal.py::TestTerminal::test_runtest_location_shown_before_test_starts: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_runtest_not_collected: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_exceptions_with_skips: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_error: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_pdb: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_skip_property: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_capture.py::TestFDCapture::test_simple_many_check_open_files: skipped; base: testing/test_capture.py::TestStdCaptureFD::test_many: skipped; base: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams: skipped; base: raw SKIPPED: testing/test_capture.py::TestStdCaptureFD::test_many; base: raw SKIPPED: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_robust_scaler_attributes[X1-True-True] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | primary | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/test_build_epub.py::test_run_epubcheck: skipped; base: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck; patched: tests/test_build_epub.py::test_run_epubcheck: skipped; patched: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | primary | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/external/tests/test_sage.py::test_basics: skipped; base: sympy/external/tests/test_sage.py::test_complex: skipped; base: sympy/external/tests/test_sage.py::test_complex_fail: skipped; base: sympy/external/tests/test_sage.py::test_integer: skipped; base: sympy/external/tests/test_sage.py::test_real: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/physics/quantum/tests/test_dagger.py::test_numpy_dagger: skipped; base: sympy/physics/quantum/tests/test_dagger.py::test_scipy_sparse_dagger: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AssignmentBase: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AugmentedAssignment: skipped; base: sympy/core/tests/test_args.py::test_sympy__concrete__expr_with_limits__ExprWithLimits: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | primary | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak: skipped; base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak2: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_simple: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_2d: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_mixin: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_inlines: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_inlines: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_only: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_select_related: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_as_tables: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | including_no_patch | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | including_no_patch | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | including_no_patch | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | including_no_patch | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/basic/tests.py::ModelTest::test_emptyqs_distinct: skipped; base: tests/basic/tests.py::ConcurrentSaveTests::test_concurrent_delete_with_save: skipped; base: tests/custom_lookups/tests.py::LookupTests::test_birthdate_month: skipped; base: tests/custom_lookups/tests.py::DateTimeLookupTests::test_datetime_output_field: skipped; base: tests/custom_lookups/tests.py::YearLteTests::test_year_lte: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/postgresql/tests.py::Tests::test_nodb_cursor: skipped; base: tests/backends/postgresql/tests.py::Tests::test_database_name_too_long: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_and_rollback: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_non_autocommit: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_isolation_level: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/mysql/test_schema.py::SchemaEditorTests::test_quote_value: skipped; base: tests/schema/tests.py::SchemaTests::test_inline_fk: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_index_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_binaryfield_mediumblob: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_geom_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_geom_col_name: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_raster_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_blank_geom_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_blank_raster_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_ignores_non_existing_directories_two_levels: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_uses_existing_parent_directories: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_multiple_patterns: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_files: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_directory_globs: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/expressions/tests.py::ExpressionOperatorTests::test_lefthand_bitwise_xor_not_supported: skipped; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation_different_srid: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geography_value: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_update_from_other_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select_multiple: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_inline_add_another_widgets: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_modifier_allows_multiple_section: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | including_no_patch | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | including_no_patch | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | including_no_patch | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | including_no_patch | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | including_no_patch | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | including_no_patch | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | including_no_patch | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_backend_macosx.py::test_cached_renderer: skipped; base: lib/matplotlib/tests/test_backend_macosx.py::test_savefig_rcparam: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_fig_close: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_sigint: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_other_signal_before_sigint: skipped | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_axes.py::test_centered_bar_label_nonlinear: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_vertical[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_horizontal[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_rc[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_formatter_ticker[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped; base: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray; patched: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/python/integration.py::TestMockDecoration::test_unittest_mock_and_pypi_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_sorting: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_double_patch_issue473: skipped; base: testing/test_terminal.py::TestTerminal::test_runtest_location_shown_before_test_starts: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_runtest_not_collected: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_exceptions_with_skips: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_error: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_pdb: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_skip_property: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_capture.py::TestFDCapture::test_simple_many_check_open_files: skipped; base: testing/test_capture.py::TestStdCaptureFD::test_many: skipped; base: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams: skipped; base: raw SKIPPED: testing/test_capture.py::TestStdCaptureFD::test_many; base: raw SKIPPED: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_robust_scaler_attributes[X1-True-True] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/test_build_epub.py::test_run_epubcheck: skipped; base: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck; patched: tests/test_build_epub.py::test_run_epubcheck: skipped; patched: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/external/tests/test_sage.py::test_basics: skipped; base: sympy/external/tests/test_sage.py::test_complex: skipped; base: sympy/external/tests/test_sage.py::test_complex_fail: skipped; base: sympy/external/tests/test_sage.py::test_integer: skipped; base: sympy/external/tests/test_sage.py::test_real: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/physics/quantum/tests/test_dagger.py::test_numpy_dagger: skipped; base: sympy/physics/quantum/tests/test_dagger.py::test_scipy_sparse_dagger: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AssignmentBase: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AugmentedAssignment: skipped; base: sympy/core/tests/test_args.py::test_sympy__concrete__expr_with_limits__ExprWithLimits: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak: skipped; base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak2: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_simple: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_2d: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_mixin: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_inlines: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_inlines: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_only: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_select_related: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_as_tables: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/basic/tests.py::ModelTest::test_emptyqs_distinct: skipped; base: tests/basic/tests.py::ConcurrentSaveTests::test_concurrent_delete_with_save: skipped; base: tests/custom_lookups/tests.py::LookupTests::test_birthdate_month: skipped; base: tests/custom_lookups/tests.py::DateTimeLookupTests::test_datetime_output_field: skipped; base: tests/custom_lookups/tests.py::YearLteTests::test_year_lte: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/postgresql/tests.py::Tests::test_nodb_cursor: skipped; base: tests/backends/postgresql/tests.py::Tests::test_database_name_too_long: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_and_rollback: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_non_autocommit: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_isolation_level: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/mysql/test_schema.py::SchemaEditorTests::test_quote_value: skipped; base: tests/schema/tests.py::SchemaTests::test_inline_fk: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_index_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_binaryfield_mediumblob: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_geom_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_geom_col_name: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_raster_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_blank_geom_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_blank_raster_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_ignores_non_existing_directories_two_levels: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_uses_existing_parent_directories: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_multiple_patterns: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_files: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_directory_globs: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/expressions/tests.py::ExpressionOperatorTests::test_lefthand_bitwise_xor_not_supported: skipped; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation_different_srid: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geography_value: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_update_from_other_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select_multiple: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_inline_add_another_widgets: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_modifier_allows_multiple_section: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_backend_macosx.py::test_cached_renderer: skipped; base: lib/matplotlib/tests/test_backend_macosx.py::test_savefig_rcparam: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_fig_close: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_sigint: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_other_signal_before_sigint: skipped | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_axes.py::test_centered_bar_label_nonlinear: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_vertical[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_horizontal[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_rc[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_formatter_ticker[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped; base: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray; patched: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/python/integration.py::TestMockDecoration::test_unittest_mock_and_pypi_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_sorting: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_double_patch_issue473: skipped; base: testing/test_terminal.py::TestTerminal::test_runtest_location_shown_before_test_starts: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_runtest_not_collected: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_exceptions_with_skips: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_error: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_pdb: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_skip_property: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_capture.py::TestFDCapture::test_simple_many_check_open_files: skipped; base: testing/test_capture.py::TestStdCaptureFD::test_many: skipped; base: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams: skipped; base: raw SKIPPED: testing/test_capture.py::TestStdCaptureFD::test_many; base: raw SKIPPED: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_robust_scaler_attributes[X1-True-True] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/test_build_epub.py::test_run_epubcheck: skipped; base: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck; patched: tests/test_build_epub.py::test_run_epubcheck: skipped; patched: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/external/tests/test_sage.py::test_basics: skipped; base: sympy/external/tests/test_sage.py::test_complex: skipped; base: sympy/external/tests/test_sage.py::test_complex_fail: skipped; base: sympy/external/tests/test_sage.py::test_integer: skipped; base: sympy/external/tests/test_sage.py::test_real: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/physics/quantum/tests/test_dagger.py::test_numpy_dagger: skipped; base: sympy/physics/quantum/tests/test_dagger.py::test_scipy_sparse_dagger: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AssignmentBase: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AugmentedAssignment: skipped; base: sympy/core/tests/test_args.py::test_sympy__concrete__expr_with_limits__ExprWithLimits: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak: skipped; base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak2: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_simple: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_2d: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_mixin: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_inlines: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_inlines: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_only: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_select_related: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_as_tables: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | excluding_T4 | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | excluding_T4 | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | excluding_T4 | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | excluding_T4 | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/basic/tests.py::ModelTest::test_emptyqs_distinct: skipped; base: tests/basic/tests.py::ConcurrentSaveTests::test_concurrent_delete_with_save: skipped; base: tests/custom_lookups/tests.py::LookupTests::test_birthdate_month: skipped; base: tests/custom_lookups/tests.py::DateTimeLookupTests::test_datetime_output_field: skipped; base: tests/custom_lookups/tests.py::YearLteTests::test_year_lte: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/postgresql/tests.py::Tests::test_nodb_cursor: skipped; base: tests/backends/postgresql/tests.py::Tests::test_database_name_too_long: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_and_rollback: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_non_autocommit: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_isolation_level: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/mysql/test_schema.py::SchemaEditorTests::test_quote_value: skipped; base: tests/schema/tests.py::SchemaTests::test_inline_fk: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_index_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_binaryfield_mediumblob: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_geom_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_geom_col_name: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_raster_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_blank_geom_field: collection_error; base: tests/gis_tests/gis_migrations/test_operations.py::OperationTests::test_add_blank_raster_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_ignores_non_existing_directories_two_levels: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_uses_existing_parent_directories: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_multiple_patterns: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_files: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_directory_globs: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/expressions/tests.py::ExpressionOperatorTests::test_lefthand_bitwise_xor_not_supported: skipped; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation_different_srid: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geography_value: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_update_from_other_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select_multiple: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_inline_add_another_widgets: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_modifier_allows_multiple_section: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | excluding_T4 | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | excluding_T4 | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | excluding_T4 | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | excluding_T4 | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | excluding_T4 | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | excluding_T4 | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | excluding_T4 | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_backend_macosx.py::test_cached_renderer: skipped; base: lib/matplotlib/tests/test_backend_macosx.py::test_savefig_rcparam: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_fig_close: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_sigint: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_other_signal_before_sigint: skipped | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_axes.py::test_centered_bar_label_nonlinear: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_vertical[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_horizontal[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_rc[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_formatter_ticker[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped; base: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray; patched: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/python/integration.py::TestMockDecoration::test_unittest_mock_and_pypi_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_sorting: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_double_patch_issue473: skipped; base: testing/test_terminal.py::TestTerminal::test_runtest_location_shown_before_test_starts: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_runtest_not_collected: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_exceptions_with_skips: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_error: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_pdb: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_skip_property: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_capture.py::TestFDCapture::test_simple_many_check_open_files: skipped; base: testing/test_capture.py::TestStdCaptureFD::test_many: skipped; base: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams: skipped; base: raw SKIPPED: testing/test_capture.py::TestStdCaptureFD::test_many; base: raw SKIPPED: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_robust_scaler_attributes[X1-True-True] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/test_build_epub.py::test_run_epubcheck: skipped; base: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck; patched: tests/test_build_epub.py::test_run_epubcheck: skipped; patched: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/external/tests/test_sage.py::test_basics: skipped; base: sympy/external/tests/test_sage.py::test_complex: skipped; base: sympy/external/tests/test_sage.py::test_complex_fail: skipped; base: sympy/external/tests/test_sage.py::test_integer: skipped; base: sympy/external/tests/test_sage.py::test_real: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/physics/quantum/tests/test_dagger.py::test_numpy_dagger: skipped; base: sympy/physics/quantum/tests/test_dagger.py::test_scipy_sparse_dagger: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AssignmentBase: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AugmentedAssignment: skipped; base: sympy/core/tests/test_args.py::test_sympy__concrete__expr_with_limits__ExprWithLimits: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4 | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak: skipped; base: astropy/io/fits/tests/test_table.py::TestTableFunctions::test_reference_leak2: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_simple: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_2d: skipped; base: astropy/table/tests/test_table.py::TestPandas::test_mixin: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_stackeds: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_add_inlines: skipped; base: tests/admin_inlines/tests.py::SeleniumTests::test_delete_inlines: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_only: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_duplicate_columns_select_related: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_columns: skipped; base: tests/aggregation_regress/tests.py::AggregationTests::test_aggregate_unmanaged_model_as_tables: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/basic/tests.py::ModelTest::test_emptyqs_distinct: skipped; base: tests/basic/tests.py::ConcurrentSaveTests::test_concurrent_delete_with_save: skipped; base: tests/custom_lookups/tests.py::LookupTests::test_birthdate_month: skipped; base: tests/custom_lookups/tests.py::DateTimeLookupTests::test_datetime_output_field: skipped; base: tests/custom_lookups/tests.py::YearLteTests::test_year_lte: skipped | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/postgresql/tests.py::Tests::test_nodb_cursor: skipped; base: tests/backends/postgresql/tests.py::Tests::test_database_name_too_long: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_and_rollback: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_non_autocommit: skipped; base: tests/backends/postgresql/tests.py::Tests::test_connect_isolation_level: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/backends/mysql/test_schema.py::SchemaEditorTests::test_quote_value: skipped; base: tests/schema/tests.py::SchemaTests::test_inline_fk: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_inline_fk_index_update_data: skipped; base: tests/schema/tests.py::SchemaTests::test_add_binaryfield_mediumblob: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_ignores_non_existing_directories_two_levels: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_uses_existing_parent_directories: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watch_glob_multiple_patterns: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_files: skipped; base: tests/utils_tests/test_autoreload.py::WatchmanReloaderTests::test_watched_roots_contains_directory_globs: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/expressions/tests.py::ExpressionOperatorTests::test_lefthand_bitwise_xor_not_supported: skipped; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geometry_value_annotation_different_srid: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_geography_value: collection_error; base: tests/gis_tests/geoapp/test_expressions.py::GeoExpressionsTests::test_update_from_other_field: collection_error | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_select_multiple: skipped; base: tests/admin_views/test_autocomplete_view.py::SeleniumTests::test_inline_add_another_widgets: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_add_row_selection: skipped; base: tests/admin_changelist/tests.py::SeleniumTests::test_modifier_allows_multiple_section: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_backend_macosx.py::test_cached_renderer: skipped; base: lib/matplotlib/tests/test_backend_macosx.py::test_savefig_rcparam: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_fig_close: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_sigint: skipped; base: lib/matplotlib/tests/test_backend_qt.py::test_other_signal_before_sigint: skipped | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_axes.py::test_centered_bar_label_nonlinear: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_vertical[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_horizontal[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_label_loc_rc[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_axes.py::test_formatter_ticker[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; base: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_set_line_coll_dash_image[svg]; patched: raw SKIPPED: lib/matplotlib/tests/test_skew.py::test_skew_rectangle[svg] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped; base: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray: skipped; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray; base: raw SKIPPED: lib/matplotlib/tests/test_cbook.py::test_index_of_xarray; patched: lib/matplotlib/tests/test_cbook.py::test_reshape2d_xarray: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/python/integration.py::TestMockDecoration::test_unittest_mock_and_pypi_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_sorting: skipped; base: testing/python/integration.py::TestMockDecoration::test_mock_double_patch_issue473: skipped; base: testing/test_terminal.py::TestTerminal::test_runtest_location_shown_before_test_starts: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_runtest_not_collected: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_exceptions_with_skips: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_error: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_pdb: skipped; base: testing/test_unittest.py::TestTrialUnittest::test_trial_testcase_skip_property: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: testing/test_capture.py::TestFDCapture::test_simple_many_check_open_files: skipped; base: testing/test_capture.py::TestStdCaptureFD::test_many: skipped; base: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams: skipped; base: raw SKIPPED: testing/test_capture.py::TestStdCaptureFD::test_many; base: raw SKIPPED: testing/test_capture.py::test_py36_windowsconsoleio_workaround_non_standard_streams | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csc_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-True-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_scaler_n_samples_seen_with_nan[csr_matrix-False-True]; base: raw SKIPPED: sklearn/preprocessing/tests/test_data.py::test_robust_scaler_attributes[X1-True-True] | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: tests/test_build_epub.py::test_run_epubcheck: skipped; base: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck; patched: tests/test_build_epub.py::test_run_epubcheck: skipped; patched: raw SKIPPED: tests/test_build_epub.py::test_run_epubcheck | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/external/tests/test_sage.py::test_basics: skipped; base: sympy/external/tests/test_sage.py::test_complex: skipped; base: sympy/external/tests/test_sage.py::test_complex_fail: skipped; base: sympy/external/tests/test_sage.py::test_integer: skipped; base: sympy/external/tests/test_sage.py::test_real: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | V2 INCOMPLETE: base: sympy/physics/quantum/tests/test_dagger.py::test_numpy_dagger: skipped; base: sympy/physics/quantum/tests/test_dagger.py::test_scipy_sparse_dagger: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AssignmentBase: skipped; base: sympy/core/tests/test_args.py::test_sympy__codegen__ast__AugmentedAssignment: skipped; base: sympy/core/tests/test_args.py::test_sympy__concrete__expr_with_limits__ExprWithLimits: skipped | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | primary | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | primary | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | primary | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | primary | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | primary | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | primary | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | primary | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | primary | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | primary | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | primary | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | primary | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | primary | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | primary | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | primary | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | primary | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | primary | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | including_no_patch | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | including_no_patch | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | including_no_patch | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | including_no_patch | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | including_no_patch | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | including_no_patch | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | including_no_patch | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | including_no_patch | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | including_no_patch | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | including_no_patch | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | including_no_patch | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | excluding_T4 | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | excluding_T4 | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | excluding_T4 | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | excluding_T4 | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | excluding_T4 | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | excluding_T4 | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | excluding_T4 | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | excluding_T4 | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | excluding_T4 | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | excluding_T4 | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | excluding_T4 | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4 | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13807 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13807 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13807 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-13807 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-15278 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-15278 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-15278 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-15278 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-15572 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-15572 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-15572 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-15572 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| S_invalid_missing | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-24026 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-24026 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-24026 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-24026 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-24970 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-24970 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-24970 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-24970 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25287 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25287 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25287 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25287 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10466 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10466 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10466 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10466 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-19783 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-19783 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-19783 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-19783 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | primary | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | primary | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | primary | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | primary | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | primary | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | primary | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | primary | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | primary | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | primary | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | primary | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | primary | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | primary | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | primary | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | primary | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | primary | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | including_no_patch | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | including_no_patch | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | including_no_patch | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | including_no_patch | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | including_no_patch | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | including_no_patch | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | including_no_patch | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | including_no_patch | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | including_no_patch | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | including_no_patch | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | including_no_patch | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | excluding_T4 | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | excluding_T4 | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | excluding_T4 | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | excluding_T4 | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | excluding_T4 | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | excluding_T4 | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | excluding_T4 | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | excluding_T4 | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | excluding_T4 | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | excluding_T4 | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | excluding_T4 | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | PASS |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | primary | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | primary | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | primary | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | primary | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | primary | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | primary | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | primary | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | primary | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | primary | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | primary | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | primary | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | primary | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | primary | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | primary | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | primary | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | primary | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | including_no_patch | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | including_no_patch | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | including_no_patch | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | including_no_patch | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | including_no_patch | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | including_no_patch | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | including_no_patch | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | including_no_patch | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | including_no_patch | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | including_no_patch | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | including_no_patch | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | excluding_T4 | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | excluding_T4 | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | excluding_T4 | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | excluding_T4 | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | django__django-15103 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-15103 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-15103 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-15103 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | django__django-15499 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-15499 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-15499 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-15499 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | excluding_T4 | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | excluding_T4 | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | excluding_T4 | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | excluding_T4 | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | excluding_T4 | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | excluding_T4 | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | excluding_T4 | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-24627 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-24637 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4 | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-13398 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-14508 | wrong | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy-7606 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-11095 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-12965 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13023 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V3 | NOT_AVAILABLE | error | EXECUTOR_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13158 | wrong | FLAG | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13212 | wrong | FLAG | V4 | FAIL |  |  | regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13297 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-13786 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:prelisted_missing_evidence | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-14140 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16082 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16612 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V1 | PASS |  |  | regression test failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V2 | FAIL |  |  | regression test failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V3 | PASS |  |  | regression test failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16631 | wrong | REJECT | V4 | FAIL |  |  | regression test failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V1 | FAIL |  |  | integrity check failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V2 | NOT_AVAILABLE | error | NO_SELECTION | integrity check failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V3 | NOT_AVAILABLE | error | NO_PARSEABLE_PATCH | integrity check failed |
| C_invalid_missing | excluding_T4_and_T3_name | django__django-16667 | wrong | REJECT | V4 | NOT_AVAILABLE | error | V4_EXCEPTION:ContainerError | integrity check failed |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-20488 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-22871 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-23476 | wrong | FLAG | V4 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25122 | correct | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25332 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-25479 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib-26291 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pydata__xarray-6744 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V2 | NOT_AVAILABLE | nothing_to_check | no tests selected | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-6903 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint-7277 | wrong | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V1 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V2 | FAIL |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V3 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-5809 | correct | FLAG | V4 | PASS |  |  | signals disagree: regression FAIL, reproduction PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-6202 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:module_import_dependency_failure | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7236 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7432 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest-7521 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn-12585 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V1 | PASS |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V2 | NOT_AVAILABLE | error | RUN_HEALTH_G1:zero_collection_without_recorded_module_skip | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V3 | FAIL |  |  | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-10323 | wrong | FLAG | V4 | NOT_AVAILABLE | nothing_to_check | none of 3 kept tests gave a stable result on the patched tree (error) | v3_absolute_failure \| regression is NOT_AVAILABLE, not PASS \| no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V1 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V2 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V3 | PASS |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx-7910 | wrong | FLAG | V4 | FAIL |  |  | no issue-specific execution signal supports repair (reproduction is FAIL) |
| C_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V1 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V2 | NOT_AVAILABLE | incomplete | INCOMPLETE | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V3 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |
| C_invalid_missing | excluding_T4_and_T3_name | sympy__sympy-13480 | correct | FLAG | V4 | PASS |  |  | regression is NOT_AVAILABLE, not PASS |

## Signal counts

| accounting | cohort | correctness | signal | outcome | absence | tasks |
| --- | --- | --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | correct | V1 | PASS |  | 21 |
| S_invalid_excluded | primary | correct | V2 | FAIL |  | 1 |
| S_invalid_excluded | primary | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_excluded | primary | correct | V2 | NOT_AVAILABLE | incomplete | 16 |
| S_invalid_excluded | primary | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | primary | correct | V2 | PASS |  | 1 |
| S_invalid_excluded | primary | correct | V3 | PASS |  | 21 |
| S_invalid_excluded | primary | correct | V4 | FAIL |  | 1 |
| S_invalid_excluded | primary | correct | V4 | PASS |  | 20 |
| S_invalid_excluded | primary | wrong | V1 | FAIL |  | 2 |
| S_invalid_excluded | primary | wrong | V1 | PASS |  | 23 |
| S_invalid_excluded | primary | wrong | V2 | FAIL |  | 8 |
| S_invalid_excluded | primary | wrong | V2 | NOT_AVAILABLE | error | 5 |
| S_invalid_excluded | primary | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_excluded | primary | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_excluded | primary | wrong | V2 | PASS |  | 3 |
| S_invalid_excluded | primary | wrong | V3 | FAIL |  | 3 |
| S_invalid_excluded | primary | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | primary | wrong | V3 | PASS |  | 19 |
| S_invalid_excluded | primary | wrong | V4 | FAIL |  | 9 |
| S_invalid_excluded | primary | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | primary | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | primary | wrong | V4 | PASS |  | 11 |
| S_invalid_excluded | including_no_patch | correct | V1 | PASS |  | 21 |
| S_invalid_excluded | including_no_patch | correct | V2 | FAIL |  | 1 |
| S_invalid_excluded | including_no_patch | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_excluded | including_no_patch | correct | V2 | NOT_AVAILABLE | incomplete | 16 |
| S_invalid_excluded | including_no_patch | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | including_no_patch | correct | V2 | PASS |  | 1 |
| S_invalid_excluded | including_no_patch | correct | V3 | PASS |  | 21 |
| S_invalid_excluded | including_no_patch | correct | V4 | FAIL |  | 1 |
| S_invalid_excluded | including_no_patch | correct | V4 | PASS |  | 20 |
| S_invalid_excluded | including_no_patch | wrong | V1 | FAIL |  | 2 |
| S_invalid_excluded | including_no_patch | wrong | V1 | PASS |  | 23 |
| S_invalid_excluded | including_no_patch | wrong | V2 | FAIL |  | 8 |
| S_invalid_excluded | including_no_patch | wrong | V2 | NOT_AVAILABLE | error | 5 |
| S_invalid_excluded | including_no_patch | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_excluded | including_no_patch | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_excluded | including_no_patch | wrong | V2 | PASS |  | 3 |
| S_invalid_excluded | including_no_patch | wrong | V3 | FAIL |  | 3 |
| S_invalid_excluded | including_no_patch | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | including_no_patch | wrong | V3 | PASS |  | 19 |
| S_invalid_excluded | including_no_patch | wrong | V4 | FAIL |  | 9 |
| S_invalid_excluded | including_no_patch | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | including_no_patch | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | including_no_patch | wrong | V4 | PASS |  | 11 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V1 | PASS |  | 21 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | FAIL |  | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | incomplete | 16 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | PASS |  | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V3 | PASS |  | 21 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V4 | FAIL |  | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | V4 | PASS |  | 20 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V1 | FAIL |  | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V1 | PASS |  | 23 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | FAIL |  | 8 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | error | 5 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | PASS |  | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V3 | FAIL |  | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V3 | PASS |  | 19 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V4 | FAIL |  | 9 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V4 | PASS |  | 11 |
| S_invalid_excluded | excluding_T4 | correct | V1 | PASS |  | 21 |
| S_invalid_excluded | excluding_T4 | correct | V2 | FAIL |  | 1 |
| S_invalid_excluded | excluding_T4 | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_excluded | excluding_T4 | correct | V2 | NOT_AVAILABLE | incomplete | 16 |
| S_invalid_excluded | excluding_T4 | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | excluding_T4 | correct | V2 | PASS |  | 1 |
| S_invalid_excluded | excluding_T4 | correct | V3 | PASS |  | 21 |
| S_invalid_excluded | excluding_T4 | correct | V4 | FAIL |  | 1 |
| S_invalid_excluded | excluding_T4 | correct | V4 | PASS |  | 20 |
| S_invalid_excluded | excluding_T4 | wrong | V1 | FAIL |  | 2 |
| S_invalid_excluded | excluding_T4 | wrong | V1 | PASS |  | 23 |
| S_invalid_excluded | excluding_T4 | wrong | V2 | FAIL |  | 8 |
| S_invalid_excluded | excluding_T4 | wrong | V2 | NOT_AVAILABLE | error | 5 |
| S_invalid_excluded | excluding_T4 | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_excluded | excluding_T4 | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_excluded | excluding_T4 | wrong | V2 | PASS |  | 3 |
| S_invalid_excluded | excluding_T4 | wrong | V3 | FAIL |  | 3 |
| S_invalid_excluded | excluding_T4 | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | excluding_T4 | wrong | V3 | PASS |  | 19 |
| S_invalid_excluded | excluding_T4 | wrong | V4 | FAIL |  | 9 |
| S_invalid_excluded | excluding_T4 | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | excluding_T4 | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | excluding_T4 | wrong | V4 | PASS |  | 11 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V1 | PASS |  | 19 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | FAIL |  | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | incomplete | 15 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | nothing_to_check | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | PASS |  | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V3 | PASS |  | 19 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V4 | FAIL |  | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | V4 | PASS |  | 18 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V1 | FAIL |  | 2 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V1 | PASS |  | 21 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | FAIL |  | 7 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | error | 4 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | PASS |  | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V3 | FAIL |  | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V3 | PASS |  | 17 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V4 | FAIL |  | 7 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | V4 | PASS |  | 11 |
| S_invalid_missing | primary | correct | V1 | PASS |  | 21 |
| S_invalid_missing | primary | correct | V2 | FAIL |  | 1 |
| S_invalid_missing | primary | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_missing | primary | correct | V2 | NOT_AVAILABLE | incomplete | 16 |
| S_invalid_missing | primary | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | primary | correct | V2 | PASS |  | 1 |
| S_invalid_missing | primary | correct | V3 | PASS |  | 21 |
| S_invalid_missing | primary | correct | V4 | FAIL |  | 1 |
| S_invalid_missing | primary | correct | V4 | PASS |  | 20 |
| S_invalid_missing | primary | wrong | V1 | FAIL |  | 2 |
| S_invalid_missing | primary | wrong | V1 | PASS |  | 23 |
| S_invalid_missing | primary | wrong | V2 | FAIL |  | 8 |
| S_invalid_missing | primary | wrong | V2 | NOT_AVAILABLE | error | 5 |
| S_invalid_missing | primary | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_missing | primary | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_missing | primary | wrong | V2 | PASS |  | 3 |
| S_invalid_missing | primary | wrong | V3 | FAIL |  | 3 |
| S_invalid_missing | primary | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | primary | wrong | V3 | PASS |  | 19 |
| S_invalid_missing | primary | wrong | V4 | FAIL |  | 9 |
| S_invalid_missing | primary | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | primary | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | primary | wrong | V4 | PASS |  | 11 |
| S_invalid_missing | including_no_patch | correct | V1 | PASS |  | 21 |
| S_invalid_missing | including_no_patch | correct | V2 | FAIL |  | 1 |
| S_invalid_missing | including_no_patch | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_missing | including_no_patch | correct | V2 | NOT_AVAILABLE | incomplete | 16 |
| S_invalid_missing | including_no_patch | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | including_no_patch | correct | V2 | PASS |  | 1 |
| S_invalid_missing | including_no_patch | correct | V3 | PASS |  | 21 |
| S_invalid_missing | including_no_patch | correct | V4 | FAIL |  | 1 |
| S_invalid_missing | including_no_patch | correct | V4 | PASS |  | 20 |
| S_invalid_missing | including_no_patch | wrong | V1 | FAIL |  | 2 |
| S_invalid_missing | including_no_patch | wrong | V1 | PASS |  | 23 |
| S_invalid_missing | including_no_patch | wrong | V2 | FAIL |  | 8 |
| S_invalid_missing | including_no_patch | wrong | V2 | NOT_AVAILABLE | error | 5 |
| S_invalid_missing | including_no_patch | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_missing | including_no_patch | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_missing | including_no_patch | wrong | V2 | PASS |  | 3 |
| S_invalid_missing | including_no_patch | wrong | V3 | FAIL |  | 3 |
| S_invalid_missing | including_no_patch | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | including_no_patch | wrong | V3 | PASS |  | 19 |
| S_invalid_missing | including_no_patch | wrong | V4 | FAIL |  | 9 |
| S_invalid_missing | including_no_patch | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | including_no_patch | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | including_no_patch | wrong | V4 | PASS |  | 11 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V1 | PASS |  | 21 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | FAIL |  | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | incomplete | 16 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | PASS |  | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V3 | PASS |  | 21 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V4 | FAIL |  | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | V4 | PASS |  | 20 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V1 | FAIL |  | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V1 | PASS |  | 23 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | FAIL |  | 8 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | error | 5 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | PASS |  | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V3 | FAIL |  | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V3 | PASS |  | 19 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V4 | FAIL |  | 9 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | V4 | PASS |  | 11 |
| S_invalid_missing | excluding_T4 | correct | V1 | PASS |  | 21 |
| S_invalid_missing | excluding_T4 | correct | V2 | FAIL |  | 1 |
| S_invalid_missing | excluding_T4 | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_missing | excluding_T4 | correct | V2 | NOT_AVAILABLE | incomplete | 16 |
| S_invalid_missing | excluding_T4 | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | excluding_T4 | correct | V2 | PASS |  | 1 |
| S_invalid_missing | excluding_T4 | correct | V3 | PASS |  | 21 |
| S_invalid_missing | excluding_T4 | correct | V4 | FAIL |  | 1 |
| S_invalid_missing | excluding_T4 | correct | V4 | PASS |  | 20 |
| S_invalid_missing | excluding_T4 | wrong | V1 | FAIL |  | 2 |
| S_invalid_missing | excluding_T4 | wrong | V1 | PASS |  | 23 |
| S_invalid_missing | excluding_T4 | wrong | V2 | FAIL |  | 8 |
| S_invalid_missing | excluding_T4 | wrong | V2 | NOT_AVAILABLE | error | 5 |
| S_invalid_missing | excluding_T4 | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_missing | excluding_T4 | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_missing | excluding_T4 | wrong | V2 | PASS |  | 3 |
| S_invalid_missing | excluding_T4 | wrong | V3 | FAIL |  | 3 |
| S_invalid_missing | excluding_T4 | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | excluding_T4 | wrong | V3 | PASS |  | 19 |
| S_invalid_missing | excluding_T4 | wrong | V4 | FAIL |  | 9 |
| S_invalid_missing | excluding_T4 | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | excluding_T4 | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | excluding_T4 | wrong | V4 | PASS |  | 11 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V1 | PASS |  | 19 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V2 | FAIL |  | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | error | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | incomplete | 15 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | nothing_to_check | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V2 | PASS |  | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V3 | PASS |  | 19 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V4 | FAIL |  | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | V4 | PASS |  | 18 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V1 | FAIL |  | 2 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V1 | PASS |  | 21 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | FAIL |  | 7 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | error | 4 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | incomplete | 6 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | PASS |  | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V3 | FAIL |  | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V3 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V3 | PASS |  | 17 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V4 | FAIL |  | 7 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V4 | NOT_AVAILABLE | error | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | V4 | PASS |  | 11 |
| C_invalid_excluded | primary | correct | V1 | PASS |  | 9 |
| C_invalid_excluded | primary | correct | V2 | FAIL |  | 1 |
| C_invalid_excluded | primary | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_excluded | primary | correct | V2 | NOT_AVAILABLE | incomplete | 4 |
| C_invalid_excluded | primary | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | primary | correct | V2 | PASS |  | 1 |
| C_invalid_excluded | primary | correct | V3 | PASS |  | 9 |
| C_invalid_excluded | primary | correct | V4 | FAIL |  | 1 |
| C_invalid_excluded | primary | correct | V4 | PASS |  | 8 |
| C_invalid_excluded | primary | wrong | V1 | FAIL |  | 2 |
| C_invalid_excluded | primary | wrong | V1 | PASS |  | 20 |
| C_invalid_excluded | primary | wrong | V2 | FAIL |  | 8 |
| C_invalid_excluded | primary | wrong | V2 | NOT_AVAILABLE | error | 5 |
| C_invalid_excluded | primary | wrong | V2 | NOT_AVAILABLE | incomplete | 2 |
| C_invalid_excluded | primary | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_excluded | primary | wrong | V2 | PASS |  | 4 |
| C_invalid_excluded | primary | wrong | V3 | FAIL |  | 3 |
| C_invalid_excluded | primary | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | primary | wrong | V3 | PASS |  | 16 |
| C_invalid_excluded | primary | wrong | V4 | FAIL |  | 9 |
| C_invalid_excluded | primary | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | primary | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | primary | wrong | V4 | PASS |  | 8 |
| C_invalid_excluded | including_no_patch | correct | V1 | PASS |  | 9 |
| C_invalid_excluded | including_no_patch | correct | V2 | FAIL |  | 1 |
| C_invalid_excluded | including_no_patch | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_excluded | including_no_patch | correct | V2 | NOT_AVAILABLE | incomplete | 4 |
| C_invalid_excluded | including_no_patch | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | including_no_patch | correct | V2 | PASS |  | 1 |
| C_invalid_excluded | including_no_patch | correct | V3 | PASS |  | 9 |
| C_invalid_excluded | including_no_patch | correct | V4 | FAIL |  | 1 |
| C_invalid_excluded | including_no_patch | correct | V4 | PASS |  | 8 |
| C_invalid_excluded | including_no_patch | wrong | V1 | FAIL |  | 2 |
| C_invalid_excluded | including_no_patch | wrong | V1 | PASS |  | 20 |
| C_invalid_excluded | including_no_patch | wrong | V2 | FAIL |  | 8 |
| C_invalid_excluded | including_no_patch | wrong | V2 | NOT_AVAILABLE | error | 5 |
| C_invalid_excluded | including_no_patch | wrong | V2 | NOT_AVAILABLE | incomplete | 2 |
| C_invalid_excluded | including_no_patch | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_excluded | including_no_patch | wrong | V2 | PASS |  | 4 |
| C_invalid_excluded | including_no_patch | wrong | V3 | FAIL |  | 3 |
| C_invalid_excluded | including_no_patch | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | including_no_patch | wrong | V3 | PASS |  | 16 |
| C_invalid_excluded | including_no_patch | wrong | V4 | FAIL |  | 9 |
| C_invalid_excluded | including_no_patch | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | including_no_patch | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | including_no_patch | wrong | V4 | PASS |  | 8 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V1 | PASS |  | 9 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | FAIL |  | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | incomplete | 4 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V2 | PASS |  | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V3 | PASS |  | 9 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V4 | FAIL |  | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | V4 | PASS |  | 8 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V1 | FAIL |  | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V1 | PASS |  | 20 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | FAIL |  | 8 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | error | 5 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | incomplete | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V2 | PASS |  | 4 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V3 | FAIL |  | 3 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V3 | PASS |  | 16 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V4 | FAIL |  | 9 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | V4 | PASS |  | 8 |
| C_invalid_excluded | excluding_T4 | correct | V1 | PASS |  | 9 |
| C_invalid_excluded | excluding_T4 | correct | V2 | FAIL |  | 1 |
| C_invalid_excluded | excluding_T4 | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_excluded | excluding_T4 | correct | V2 | NOT_AVAILABLE | incomplete | 4 |
| C_invalid_excluded | excluding_T4 | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | excluding_T4 | correct | V2 | PASS |  | 1 |
| C_invalid_excluded | excluding_T4 | correct | V3 | PASS |  | 9 |
| C_invalid_excluded | excluding_T4 | correct | V4 | FAIL |  | 1 |
| C_invalid_excluded | excluding_T4 | correct | V4 | PASS |  | 8 |
| C_invalid_excluded | excluding_T4 | wrong | V1 | FAIL |  | 2 |
| C_invalid_excluded | excluding_T4 | wrong | V1 | PASS |  | 20 |
| C_invalid_excluded | excluding_T4 | wrong | V2 | FAIL |  | 8 |
| C_invalid_excluded | excluding_T4 | wrong | V2 | NOT_AVAILABLE | error | 5 |
| C_invalid_excluded | excluding_T4 | wrong | V2 | NOT_AVAILABLE | incomplete | 2 |
| C_invalid_excluded | excluding_T4 | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_excluded | excluding_T4 | wrong | V2 | PASS |  | 4 |
| C_invalid_excluded | excluding_T4 | wrong | V3 | FAIL |  | 3 |
| C_invalid_excluded | excluding_T4 | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | excluding_T4 | wrong | V3 | PASS |  | 16 |
| C_invalid_excluded | excluding_T4 | wrong | V4 | FAIL |  | 9 |
| C_invalid_excluded | excluding_T4 | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | excluding_T4 | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | excluding_T4 | wrong | V4 | PASS |  | 8 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V1 | PASS |  | 7 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | FAIL |  | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | incomplete | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | nothing_to_check | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V2 | PASS |  | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V3 | PASS |  | 7 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V4 | FAIL |  | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | V4 | PASS |  | 6 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V1 | FAIL |  | 2 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V1 | PASS |  | 18 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | FAIL |  | 7 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | error | 4 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | incomplete | 2 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V2 | PASS |  | 4 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V3 | FAIL |  | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V3 | PASS |  | 14 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V4 | FAIL |  | 7 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | V4 | PASS |  | 8 |
| C_invalid_missing | primary | correct | V1 | PASS |  | 16 |
| C_invalid_missing | primary | correct | V2 | FAIL |  | 1 |
| C_invalid_missing | primary | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_missing | primary | correct | V2 | NOT_AVAILABLE | incomplete | 11 |
| C_invalid_missing | primary | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | primary | correct | V2 | PASS |  | 1 |
| C_invalid_missing | primary | correct | V3 | PASS |  | 16 |
| C_invalid_missing | primary | correct | V4 | FAIL |  | 1 |
| C_invalid_missing | primary | correct | V4 | PASS |  | 15 |
| C_invalid_missing | primary | wrong | V1 | FAIL |  | 2 |
| C_invalid_missing | primary | wrong | V1 | PASS |  | 20 |
| C_invalid_missing | primary | wrong | V2 | FAIL |  | 8 |
| C_invalid_missing | primary | wrong | V2 | NOT_AVAILABLE | error | 5 |
| C_invalid_missing | primary | wrong | V2 | NOT_AVAILABLE | incomplete | 3 |
| C_invalid_missing | primary | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_missing | primary | wrong | V2 | PASS |  | 3 |
| C_invalid_missing | primary | wrong | V3 | FAIL |  | 3 |
| C_invalid_missing | primary | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | primary | wrong | V3 | PASS |  | 16 |
| C_invalid_missing | primary | wrong | V4 | FAIL |  | 9 |
| C_invalid_missing | primary | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | primary | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | primary | wrong | V4 | PASS |  | 8 |
| C_invalid_missing | including_no_patch | correct | V1 | PASS |  | 16 |
| C_invalid_missing | including_no_patch | correct | V2 | FAIL |  | 1 |
| C_invalid_missing | including_no_patch | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_missing | including_no_patch | correct | V2 | NOT_AVAILABLE | incomplete | 11 |
| C_invalid_missing | including_no_patch | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | including_no_patch | correct | V2 | PASS |  | 1 |
| C_invalid_missing | including_no_patch | correct | V3 | PASS |  | 16 |
| C_invalid_missing | including_no_patch | correct | V4 | FAIL |  | 1 |
| C_invalid_missing | including_no_patch | correct | V4 | PASS |  | 15 |
| C_invalid_missing | including_no_patch | wrong | V1 | FAIL |  | 2 |
| C_invalid_missing | including_no_patch | wrong | V1 | PASS |  | 20 |
| C_invalid_missing | including_no_patch | wrong | V2 | FAIL |  | 8 |
| C_invalid_missing | including_no_patch | wrong | V2 | NOT_AVAILABLE | error | 5 |
| C_invalid_missing | including_no_patch | wrong | V2 | NOT_AVAILABLE | incomplete | 3 |
| C_invalid_missing | including_no_patch | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_missing | including_no_patch | wrong | V2 | PASS |  | 3 |
| C_invalid_missing | including_no_patch | wrong | V3 | FAIL |  | 3 |
| C_invalid_missing | including_no_patch | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | including_no_patch | wrong | V3 | PASS |  | 16 |
| C_invalid_missing | including_no_patch | wrong | V4 | FAIL |  | 9 |
| C_invalid_missing | including_no_patch | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | including_no_patch | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | including_no_patch | wrong | V4 | PASS |  | 8 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V1 | PASS |  | 16 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | FAIL |  | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | incomplete | 11 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V2 | PASS |  | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V3 | PASS |  | 16 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V4 | FAIL |  | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | V4 | PASS |  | 15 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V1 | FAIL |  | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V1 | PASS |  | 20 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | FAIL |  | 8 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | error | 5 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | incomplete | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V2 | PASS |  | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V3 | FAIL |  | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V3 | PASS |  | 16 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V4 | FAIL |  | 9 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | V4 | PASS |  | 8 |
| C_invalid_missing | excluding_T4 | correct | V1 | PASS |  | 16 |
| C_invalid_missing | excluding_T4 | correct | V2 | FAIL |  | 1 |
| C_invalid_missing | excluding_T4 | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_missing | excluding_T4 | correct | V2 | NOT_AVAILABLE | incomplete | 11 |
| C_invalid_missing | excluding_T4 | correct | V2 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | excluding_T4 | correct | V2 | PASS |  | 1 |
| C_invalid_missing | excluding_T4 | correct | V3 | PASS |  | 16 |
| C_invalid_missing | excluding_T4 | correct | V4 | FAIL |  | 1 |
| C_invalid_missing | excluding_T4 | correct | V4 | PASS |  | 15 |
| C_invalid_missing | excluding_T4 | wrong | V1 | FAIL |  | 2 |
| C_invalid_missing | excluding_T4 | wrong | V1 | PASS |  | 20 |
| C_invalid_missing | excluding_T4 | wrong | V2 | FAIL |  | 8 |
| C_invalid_missing | excluding_T4 | wrong | V2 | NOT_AVAILABLE | error | 5 |
| C_invalid_missing | excluding_T4 | wrong | V2 | NOT_AVAILABLE | incomplete | 3 |
| C_invalid_missing | excluding_T4 | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_missing | excluding_T4 | wrong | V2 | PASS |  | 3 |
| C_invalid_missing | excluding_T4 | wrong | V3 | FAIL |  | 3 |
| C_invalid_missing | excluding_T4 | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | excluding_T4 | wrong | V3 | PASS |  | 16 |
| C_invalid_missing | excluding_T4 | wrong | V4 | FAIL |  | 9 |
| C_invalid_missing | excluding_T4 | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | excluding_T4 | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | excluding_T4 | wrong | V4 | PASS |  | 8 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V1 | PASS |  | 14 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V2 | FAIL |  | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | error | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | incomplete | 10 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V2 | NOT_AVAILABLE | nothing_to_check | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V2 | PASS |  | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V3 | PASS |  | 14 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V4 | FAIL |  | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | V4 | PASS |  | 13 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V1 | FAIL |  | 2 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V1 | PASS |  | 18 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | FAIL |  | 7 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | error | 4 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | incomplete | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | NOT_AVAILABLE | nothing_to_check | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V2 | PASS |  | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V3 | FAIL |  | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V3 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V3 | PASS |  | 14 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V4 | FAIL |  | 7 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V4 | NOT_AVAILABLE | error | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V4 | NOT_AVAILABLE | nothing_to_check | 2 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | V4 | PASS |  | 8 |

## Reason counts

| accounting | cohort | correctness | reason | tasks |
| --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_excluded | primary | correct | regression is NOT_AVAILABLE, not PASS | 19 |
| S_invalid_excluded | primary | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_excluded | primary | wrong | integrity check failed | 2 |
| S_invalid_excluded | primary | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| S_invalid_excluded | primary | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_excluded | primary | wrong | regression is NOT_AVAILABLE, not PASS | 12 |
| S_invalid_excluded | primary | wrong | regression test failed | 2 |
| S_invalid_excluded | primary | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_excluded | primary | wrong | v3_absolute_failure | 3 |
| S_invalid_excluded | including_no_patch | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_excluded | including_no_patch | correct | regression is NOT_AVAILABLE, not PASS | 19 |
| S_invalid_excluded | including_no_patch | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_excluded | including_no_patch | wrong | integrity check failed | 2 |
| S_invalid_excluded | including_no_patch | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| S_invalid_excluded | including_no_patch | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_excluded | including_no_patch | wrong | regression is NOT_AVAILABLE, not PASS | 12 |
| S_invalid_excluded | including_no_patch | wrong | regression test failed | 2 |
| S_invalid_excluded | including_no_patch | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_excluded | including_no_patch | wrong | v3_absolute_failure | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | regression is NOT_AVAILABLE, not PASS | 19 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | integrity check failed | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | regression is NOT_AVAILABLE, not PASS | 12 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | regression test failed | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | wrong | v3_absolute_failure | 3 |
| S_invalid_excluded | excluding_T4 | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_excluded | excluding_T4 | correct | regression is NOT_AVAILABLE, not PASS | 19 |
| S_invalid_excluded | excluding_T4 | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_excluded | excluding_T4 | wrong | integrity check failed | 2 |
| S_invalid_excluded | excluding_T4 | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| S_invalid_excluded | excluding_T4 | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_excluded | excluding_T4 | wrong | regression is NOT_AVAILABLE, not PASS | 12 |
| S_invalid_excluded | excluding_T4 | wrong | regression test failed | 2 |
| S_invalid_excluded | excluding_T4 | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_excluded | excluding_T4 | wrong | v3_absolute_failure | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | regression is NOT_AVAILABLE, not PASS | 17 |
| S_invalid_excluded | excluding_T4_and_T3_name | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | integrity check failed | 2 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 6 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | regression is NOT_AVAILABLE, not PASS | 11 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | regression test failed | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_excluded | excluding_T4_and_T3_name | wrong | v3_absolute_failure | 3 |
| S_invalid_missing | primary | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_missing | primary | correct | regression is NOT_AVAILABLE, not PASS | 19 |
| S_invalid_missing | primary | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_missing | primary | wrong | integrity check failed | 2 |
| S_invalid_missing | primary | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| S_invalid_missing | primary | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_missing | primary | wrong | regression is NOT_AVAILABLE, not PASS | 12 |
| S_invalid_missing | primary | wrong | regression test failed | 2 |
| S_invalid_missing | primary | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_missing | primary | wrong | v3_absolute_failure | 3 |
| S_invalid_missing | including_no_patch | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_missing | including_no_patch | correct | regression is NOT_AVAILABLE, not PASS | 19 |
| S_invalid_missing | including_no_patch | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_missing | including_no_patch | wrong | integrity check failed | 2 |
| S_invalid_missing | including_no_patch | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| S_invalid_missing | including_no_patch | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_missing | including_no_patch | wrong | regression is NOT_AVAILABLE, not PASS | 12 |
| S_invalid_missing | including_no_patch | wrong | regression test failed | 2 |
| S_invalid_missing | including_no_patch | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_missing | including_no_patch | wrong | v3_absolute_failure | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | regression is NOT_AVAILABLE, not PASS | 19 |
| S_invalid_missing | including_no_patch_and_provider_blocked | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | integrity check failed | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | regression is NOT_AVAILABLE, not PASS | 12 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | regression test failed | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_missing | including_no_patch_and_provider_blocked | wrong | v3_absolute_failure | 3 |
| S_invalid_missing | excluding_T4 | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_missing | excluding_T4 | correct | regression is NOT_AVAILABLE, not PASS | 19 |
| S_invalid_missing | excluding_T4 | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_missing | excluding_T4 | wrong | integrity check failed | 2 |
| S_invalid_missing | excluding_T4 | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| S_invalid_missing | excluding_T4 | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_missing | excluding_T4 | wrong | regression is NOT_AVAILABLE, not PASS | 12 |
| S_invalid_missing | excluding_T4 | wrong | regression test failed | 2 |
| S_invalid_missing | excluding_T4 | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_missing | excluding_T4 | wrong | v3_absolute_failure | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | regression is NOT_AVAILABLE, not PASS | 17 |
| S_invalid_missing | excluding_T4_and_T3_name | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | integrity check failed | 2 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 6 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | regression is NOT_AVAILABLE, not PASS | 11 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | regression test failed | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| S_invalid_missing | excluding_T4_and_T3_name | wrong | v3_absolute_failure | 3 |
| C_invalid_excluded | primary | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_excluded | primary | correct | regression is NOT_AVAILABLE, not PASS | 7 |
| C_invalid_excluded | primary | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_excluded | primary | wrong | integrity check failed | 2 |
| C_invalid_excluded | primary | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| C_invalid_excluded | primary | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_excluded | primary | wrong | regression is NOT_AVAILABLE, not PASS | 8 |
| C_invalid_excluded | primary | wrong | regression test failed | 2 |
| C_invalid_excluded | primary | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_excluded | primary | wrong | v3_absolute_failure | 3 |
| C_invalid_excluded | including_no_patch | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_excluded | including_no_patch | correct | regression is NOT_AVAILABLE, not PASS | 7 |
| C_invalid_excluded | including_no_patch | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_excluded | including_no_patch | wrong | integrity check failed | 2 |
| C_invalid_excluded | including_no_patch | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| C_invalid_excluded | including_no_patch | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_excluded | including_no_patch | wrong | regression is NOT_AVAILABLE, not PASS | 8 |
| C_invalid_excluded | including_no_patch | wrong | regression test failed | 2 |
| C_invalid_excluded | including_no_patch | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_excluded | including_no_patch | wrong | v3_absolute_failure | 3 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | regression is NOT_AVAILABLE, not PASS | 7 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | integrity check failed | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | regression is NOT_AVAILABLE, not PASS | 8 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | regression test failed | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | wrong | v3_absolute_failure | 3 |
| C_invalid_excluded | excluding_T4 | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_excluded | excluding_T4 | correct | regression is NOT_AVAILABLE, not PASS | 7 |
| C_invalid_excluded | excluding_T4 | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_excluded | excluding_T4 | wrong | integrity check failed | 2 |
| C_invalid_excluded | excluding_T4 | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| C_invalid_excluded | excluding_T4 | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_excluded | excluding_T4 | wrong | regression is NOT_AVAILABLE, not PASS | 8 |
| C_invalid_excluded | excluding_T4 | wrong | regression test failed | 2 |
| C_invalid_excluded | excluding_T4 | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_excluded | excluding_T4 | wrong | v3_absolute_failure | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | regression is NOT_AVAILABLE, not PASS | 5 |
| C_invalid_excluded | excluding_T4_and_T3_name | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | integrity check failed | 2 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 6 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | regression is NOT_AVAILABLE, not PASS | 7 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | regression test failed | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_excluded | excluding_T4_and_T3_name | wrong | v3_absolute_failure | 3 |
| C_invalid_missing | primary | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_missing | primary | correct | regression is NOT_AVAILABLE, not PASS | 14 |
| C_invalid_missing | primary | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_missing | primary | wrong | integrity check failed | 2 |
| C_invalid_missing | primary | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| C_invalid_missing | primary | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_missing | primary | wrong | regression is NOT_AVAILABLE, not PASS | 9 |
| C_invalid_missing | primary | wrong | regression test failed | 2 |
| C_invalid_missing | primary | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_missing | primary | wrong | v3_absolute_failure | 3 |
| C_invalid_missing | including_no_patch | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_missing | including_no_patch | correct | regression is NOT_AVAILABLE, not PASS | 14 |
| C_invalid_missing | including_no_patch | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_missing | including_no_patch | wrong | integrity check failed | 2 |
| C_invalid_missing | including_no_patch | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| C_invalid_missing | including_no_patch | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_missing | including_no_patch | wrong | regression is NOT_AVAILABLE, not PASS | 9 |
| C_invalid_missing | including_no_patch | wrong | regression test failed | 2 |
| C_invalid_missing | including_no_patch | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_missing | including_no_patch | wrong | v3_absolute_failure | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | regression is NOT_AVAILABLE, not PASS | 14 |
| C_invalid_missing | including_no_patch_and_provider_blocked | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | integrity check failed | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | regression is NOT_AVAILABLE, not PASS | 9 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | regression test failed | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_missing | including_no_patch_and_provider_blocked | wrong | v3_absolute_failure | 3 |
| C_invalid_missing | excluding_T4 | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_missing | excluding_T4 | correct | regression is NOT_AVAILABLE, not PASS | 14 |
| C_invalid_missing | excluding_T4 | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_missing | excluding_T4 | wrong | integrity check failed | 2 |
| C_invalid_missing | excluding_T4 | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 7 |
| C_invalid_missing | excluding_T4 | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_missing | excluding_T4 | wrong | regression is NOT_AVAILABLE, not PASS | 9 |
| C_invalid_missing | excluding_T4 | wrong | regression test failed | 2 |
| C_invalid_missing | excluding_T4 | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_missing | excluding_T4 | wrong | v3_absolute_failure | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | no issue-specific execution signal supports repair (reproduction is FAIL) | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | regression is NOT_AVAILABLE, not PASS | 12 |
| C_invalid_missing | excluding_T4_and_T3_name | correct | signals disagree: regression FAIL, reproduction PASS | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | integrity check failed | 2 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | no issue-specific execution signal supports repair (reproduction is FAIL) | 6 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | no issue-specific execution signal supports repair (reproduction is NOT_AVAILABLE) | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | regression is NOT_AVAILABLE, not PASS | 8 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | regression test failed | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | signals disagree: regression FAIL, reproduction PASS | 6 |
| C_invalid_missing | excluding_T4_and_T3_name | wrong | v3_absolute_failure | 3 |

## Exploratory ablation

| accounting | cohort | forced_pass | decision | correct | wrong |
| --- | --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | V1 | ACCEPT | 4 | 1 |
| S_invalid_excluded | primary | V1 | FLAG | 21 | 23 |
| S_invalid_excluded | primary | V1 | REJECT | 0 | 2 |
| S_invalid_excluded | primary | V2 | ACCEPT | 24 | 12 |
| S_invalid_excluded | primary | V2 | FLAG | 1 | 12 |
| S_invalid_excluded | primary | V2 | REJECT | 0 | 2 |
| S_invalid_excluded | primary | V3 | ACCEPT | 4 | 1 |
| S_invalid_excluded | primary | V3 | FLAG | 21 | 21 |
| S_invalid_excluded | primary | V3 | REJECT | 0 | 4 |
| S_invalid_excluded | primary | V4 | ACCEPT | 5 | 4 |
| S_invalid_excluded | primary | V4 | FLAG | 20 | 20 |
| S_invalid_excluded | primary | V4 | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch | V1 | ACCEPT | 4 | 1 |
| S_invalid_excluded | including_no_patch | V1 | FLAG | 21 | 63 |
| S_invalid_excluded | including_no_patch | V1 | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch | V2 | ACCEPT | 24 | 12 |
| S_invalid_excluded | including_no_patch | V2 | FLAG | 1 | 12 |
| S_invalid_excluded | including_no_patch | V2 | REJECT | 0 | 42 |
| S_invalid_excluded | including_no_patch | V3 | ACCEPT | 4 | 1 |
| S_invalid_excluded | including_no_patch | V3 | FLAG | 21 | 21 |
| S_invalid_excluded | including_no_patch | V3 | REJECT | 0 | 44 |
| S_invalid_excluded | including_no_patch | V4 | ACCEPT | 5 | 4 |
| S_invalid_excluded | including_no_patch | V4 | FLAG | 20 | 20 |
| S_invalid_excluded | including_no_patch | V4 | REJECT | 0 | 42 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V1 | ACCEPT | 4 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V1 | FLAG | 21 | 64 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V1 | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V2 | ACCEPT | 24 | 12 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V2 | FLAG | 1 | 12 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V2 | REJECT | 0 | 43 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V3 | ACCEPT | 4 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V3 | FLAG | 21 | 21 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V3 | REJECT | 0 | 45 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V4 | ACCEPT | 5 | 4 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V4 | FLAG | 20 | 20 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | V4 | REJECT | 0 | 43 |
| S_invalid_excluded | excluding_T4 | V1 | ACCEPT | 4 | 1 |
| S_invalid_excluded | excluding_T4 | V1 | FLAG | 21 | 23 |
| S_invalid_excluded | excluding_T4 | V1 | REJECT | 0 | 2 |
| S_invalid_excluded | excluding_T4 | V2 | ACCEPT | 24 | 12 |
| S_invalid_excluded | excluding_T4 | V2 | FLAG | 1 | 12 |
| S_invalid_excluded | excluding_T4 | V2 | REJECT | 0 | 2 |
| S_invalid_excluded | excluding_T4 | V3 | ACCEPT | 4 | 1 |
| S_invalid_excluded | excluding_T4 | V3 | FLAG | 21 | 21 |
| S_invalid_excluded | excluding_T4 | V3 | REJECT | 0 | 4 |
| S_invalid_excluded | excluding_T4 | V4 | ACCEPT | 5 | 4 |
| S_invalid_excluded | excluding_T4 | V4 | FLAG | 20 | 20 |
| S_invalid_excluded | excluding_T4 | V4 | REJECT | 0 | 2 |
| S_invalid_excluded | excluding_T4_and_T3_name | V1 | ACCEPT | 4 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | V1 | FLAG | 19 | 22 |
| S_invalid_excluded | excluding_T4_and_T3_name | V1 | REJECT | 0 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | V2 | ACCEPT | 22 | 12 |
| S_invalid_excluded | excluding_T4_and_T3_name | V2 | FLAG | 1 | 10 |
| S_invalid_excluded | excluding_T4_and_T3_name | V2 | REJECT | 0 | 2 |
| S_invalid_excluded | excluding_T4_and_T3_name | V3 | ACCEPT | 4 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | V3 | FLAG | 19 | 20 |
| S_invalid_excluded | excluding_T4_and_T3_name | V3 | REJECT | 0 | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | V4 | ACCEPT | 5 | 4 |
| S_invalid_excluded | excluding_T4_and_T3_name | V4 | FLAG | 18 | 18 |
| S_invalid_excluded | excluding_T4_and_T3_name | V4 | REJECT | 0 | 2 |
| S_invalid_missing | primary | V1 | ACCEPT | 4 | 1 |
| S_invalid_missing | primary | V1 | FLAG | 21 | 23 |
| S_invalid_missing | primary | V1 | REJECT | 0 | 2 |
| S_invalid_missing | primary | V2 | ACCEPT | 24 | 12 |
| S_invalid_missing | primary | V2 | FLAG | 1 | 12 |
| S_invalid_missing | primary | V2 | REJECT | 0 | 2 |
| S_invalid_missing | primary | V3 | ACCEPT | 4 | 1 |
| S_invalid_missing | primary | V3 | FLAG | 21 | 21 |
| S_invalid_missing | primary | V3 | REJECT | 0 | 4 |
| S_invalid_missing | primary | V4 | ACCEPT | 5 | 4 |
| S_invalid_missing | primary | V4 | FLAG | 20 | 20 |
| S_invalid_missing | primary | V4 | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch | V1 | ACCEPT | 4 | 1 |
| S_invalid_missing | including_no_patch | V1 | FLAG | 21 | 63 |
| S_invalid_missing | including_no_patch | V1 | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch | V2 | ACCEPT | 24 | 12 |
| S_invalid_missing | including_no_patch | V2 | FLAG | 1 | 12 |
| S_invalid_missing | including_no_patch | V2 | REJECT | 0 | 42 |
| S_invalid_missing | including_no_patch | V3 | ACCEPT | 4 | 1 |
| S_invalid_missing | including_no_patch | V3 | FLAG | 21 | 21 |
| S_invalid_missing | including_no_patch | V3 | REJECT | 0 | 44 |
| S_invalid_missing | including_no_patch | V4 | ACCEPT | 5 | 4 |
| S_invalid_missing | including_no_patch | V4 | FLAG | 20 | 20 |
| S_invalid_missing | including_no_patch | V4 | REJECT | 0 | 42 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V1 | ACCEPT | 4 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V1 | FLAG | 21 | 64 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V1 | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V2 | ACCEPT | 24 | 12 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V2 | FLAG | 1 | 12 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V2 | REJECT | 0 | 43 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V3 | ACCEPT | 4 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V3 | FLAG | 21 | 21 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V3 | REJECT | 0 | 45 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V4 | ACCEPT | 5 | 4 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V4 | FLAG | 20 | 20 |
| S_invalid_missing | including_no_patch_and_provider_blocked | V4 | REJECT | 0 | 43 |
| S_invalid_missing | excluding_T4 | V1 | ACCEPT | 4 | 1 |
| S_invalid_missing | excluding_T4 | V1 | FLAG | 21 | 23 |
| S_invalid_missing | excluding_T4 | V1 | REJECT | 0 | 2 |
| S_invalid_missing | excluding_T4 | V2 | ACCEPT | 24 | 12 |
| S_invalid_missing | excluding_T4 | V2 | FLAG | 1 | 12 |
| S_invalid_missing | excluding_T4 | V2 | REJECT | 0 | 2 |
| S_invalid_missing | excluding_T4 | V3 | ACCEPT | 4 | 1 |
| S_invalid_missing | excluding_T4 | V3 | FLAG | 21 | 21 |
| S_invalid_missing | excluding_T4 | V3 | REJECT | 0 | 4 |
| S_invalid_missing | excluding_T4 | V4 | ACCEPT | 5 | 4 |
| S_invalid_missing | excluding_T4 | V4 | FLAG | 20 | 20 |
| S_invalid_missing | excluding_T4 | V4 | REJECT | 0 | 2 |
| S_invalid_missing | excluding_T4_and_T3_name | V1 | ACCEPT | 4 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | V1 | FLAG | 19 | 22 |
| S_invalid_missing | excluding_T4_and_T3_name | V1 | REJECT | 0 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | V2 | ACCEPT | 22 | 12 |
| S_invalid_missing | excluding_T4_and_T3_name | V2 | FLAG | 1 | 10 |
| S_invalid_missing | excluding_T4_and_T3_name | V2 | REJECT | 0 | 2 |
| S_invalid_missing | excluding_T4_and_T3_name | V3 | ACCEPT | 4 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | V3 | FLAG | 19 | 20 |
| S_invalid_missing | excluding_T4_and_T3_name | V3 | REJECT | 0 | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | V4 | ACCEPT | 5 | 4 |
| S_invalid_missing | excluding_T4_and_T3_name | V4 | FLAG | 18 | 18 |
| S_invalid_missing | excluding_T4_and_T3_name | V4 | REJECT | 0 | 2 |
| C_invalid_excluded | primary | V1 | ACCEPT | 16 | 4 |
| C_invalid_excluded | primary | V1 | FLAG | 9 | 20 |
| C_invalid_excluded | primary | V1 | REJECT | 0 | 2 |
| C_invalid_excluded | primary | V2 | ACCEPT | 24 | 12 |
| C_invalid_excluded | primary | V2 | FLAG | 1 | 12 |
| C_invalid_excluded | primary | V2 | REJECT | 0 | 2 |
| C_invalid_excluded | primary | V3 | ACCEPT | 16 | 4 |
| C_invalid_excluded | primary | V3 | FLAG | 9 | 18 |
| C_invalid_excluded | primary | V3 | REJECT | 0 | 4 |
| C_invalid_excluded | primary | V4 | ACCEPT | 17 | 7 |
| C_invalid_excluded | primary | V4 | FLAG | 8 | 17 |
| C_invalid_excluded | primary | V4 | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch | V1 | ACCEPT | 16 | 4 |
| C_invalid_excluded | including_no_patch | V1 | FLAG | 9 | 60 |
| C_invalid_excluded | including_no_patch | V1 | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch | V2 | ACCEPT | 24 | 12 |
| C_invalid_excluded | including_no_patch | V2 | FLAG | 1 | 12 |
| C_invalid_excluded | including_no_patch | V2 | REJECT | 0 | 42 |
| C_invalid_excluded | including_no_patch | V3 | ACCEPT | 16 | 4 |
| C_invalid_excluded | including_no_patch | V3 | FLAG | 9 | 18 |
| C_invalid_excluded | including_no_patch | V3 | REJECT | 0 | 44 |
| C_invalid_excluded | including_no_patch | V4 | ACCEPT | 17 | 7 |
| C_invalid_excluded | including_no_patch | V4 | FLAG | 8 | 17 |
| C_invalid_excluded | including_no_patch | V4 | REJECT | 0 | 42 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V1 | ACCEPT | 16 | 4 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V1 | FLAG | 9 | 61 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V1 | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V2 | ACCEPT | 24 | 12 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V2 | FLAG | 1 | 12 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V2 | REJECT | 0 | 43 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V3 | ACCEPT | 16 | 4 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V3 | FLAG | 9 | 18 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V3 | REJECT | 0 | 45 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V4 | ACCEPT | 17 | 7 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V4 | FLAG | 8 | 17 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | V4 | REJECT | 0 | 43 |
| C_invalid_excluded | excluding_T4 | V1 | ACCEPT | 16 | 4 |
| C_invalid_excluded | excluding_T4 | V1 | FLAG | 9 | 20 |
| C_invalid_excluded | excluding_T4 | V1 | REJECT | 0 | 2 |
| C_invalid_excluded | excluding_T4 | V2 | ACCEPT | 24 | 12 |
| C_invalid_excluded | excluding_T4 | V2 | FLAG | 1 | 12 |
| C_invalid_excluded | excluding_T4 | V2 | REJECT | 0 | 2 |
| C_invalid_excluded | excluding_T4 | V3 | ACCEPT | 16 | 4 |
| C_invalid_excluded | excluding_T4 | V3 | FLAG | 9 | 18 |
| C_invalid_excluded | excluding_T4 | V3 | REJECT | 0 | 4 |
| C_invalid_excluded | excluding_T4 | V4 | ACCEPT | 17 | 7 |
| C_invalid_excluded | excluding_T4 | V4 | FLAG | 8 | 17 |
| C_invalid_excluded | excluding_T4 | V4 | REJECT | 0 | 2 |
| C_invalid_excluded | excluding_T4_and_T3_name | V1 | ACCEPT | 16 | 4 |
| C_invalid_excluded | excluding_T4_and_T3_name | V1 | FLAG | 7 | 19 |
| C_invalid_excluded | excluding_T4_and_T3_name | V1 | REJECT | 0 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | V2 | ACCEPT | 22 | 12 |
| C_invalid_excluded | excluding_T4_and_T3_name | V2 | FLAG | 1 | 10 |
| C_invalid_excluded | excluding_T4_and_T3_name | V2 | REJECT | 0 | 2 |
| C_invalid_excluded | excluding_T4_and_T3_name | V3 | ACCEPT | 16 | 4 |
| C_invalid_excluded | excluding_T4_and_T3_name | V3 | FLAG | 7 | 17 |
| C_invalid_excluded | excluding_T4_and_T3_name | V3 | REJECT | 0 | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | V4 | ACCEPT | 17 | 7 |
| C_invalid_excluded | excluding_T4_and_T3_name | V4 | FLAG | 6 | 15 |
| C_invalid_excluded | excluding_T4_and_T3_name | V4 | REJECT | 0 | 2 |
| C_invalid_missing | primary | V1 | ACCEPT | 9 | 4 |
| C_invalid_missing | primary | V1 | FLAG | 16 | 20 |
| C_invalid_missing | primary | V1 | REJECT | 0 | 2 |
| C_invalid_missing | primary | V2 | ACCEPT | 24 | 12 |
| C_invalid_missing | primary | V2 | FLAG | 1 | 12 |
| C_invalid_missing | primary | V2 | REJECT | 0 | 2 |
| C_invalid_missing | primary | V3 | ACCEPT | 9 | 4 |
| C_invalid_missing | primary | V3 | FLAG | 16 | 18 |
| C_invalid_missing | primary | V3 | REJECT | 0 | 4 |
| C_invalid_missing | primary | V4 | ACCEPT | 10 | 7 |
| C_invalid_missing | primary | V4 | FLAG | 15 | 17 |
| C_invalid_missing | primary | V4 | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch | V1 | ACCEPT | 9 | 4 |
| C_invalid_missing | including_no_patch | V1 | FLAG | 16 | 60 |
| C_invalid_missing | including_no_patch | V1 | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch | V2 | ACCEPT | 24 | 12 |
| C_invalid_missing | including_no_patch | V2 | FLAG | 1 | 12 |
| C_invalid_missing | including_no_patch | V2 | REJECT | 0 | 42 |
| C_invalid_missing | including_no_patch | V3 | ACCEPT | 9 | 4 |
| C_invalid_missing | including_no_patch | V3 | FLAG | 16 | 18 |
| C_invalid_missing | including_no_patch | V3 | REJECT | 0 | 44 |
| C_invalid_missing | including_no_patch | V4 | ACCEPT | 10 | 7 |
| C_invalid_missing | including_no_patch | V4 | FLAG | 15 | 17 |
| C_invalid_missing | including_no_patch | V4 | REJECT | 0 | 42 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V1 | ACCEPT | 9 | 4 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V1 | FLAG | 16 | 61 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V1 | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V2 | ACCEPT | 24 | 12 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V2 | FLAG | 1 | 12 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V2 | REJECT | 0 | 43 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V3 | ACCEPT | 9 | 4 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V3 | FLAG | 16 | 18 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V3 | REJECT | 0 | 45 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V4 | ACCEPT | 10 | 7 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V4 | FLAG | 15 | 17 |
| C_invalid_missing | including_no_patch_and_provider_blocked | V4 | REJECT | 0 | 43 |
| C_invalid_missing | excluding_T4 | V1 | ACCEPT | 9 | 4 |
| C_invalid_missing | excluding_T4 | V1 | FLAG | 16 | 20 |
| C_invalid_missing | excluding_T4 | V1 | REJECT | 0 | 2 |
| C_invalid_missing | excluding_T4 | V2 | ACCEPT | 24 | 12 |
| C_invalid_missing | excluding_T4 | V2 | FLAG | 1 | 12 |
| C_invalid_missing | excluding_T4 | V2 | REJECT | 0 | 2 |
| C_invalid_missing | excluding_T4 | V3 | ACCEPT | 9 | 4 |
| C_invalid_missing | excluding_T4 | V3 | FLAG | 16 | 18 |
| C_invalid_missing | excluding_T4 | V3 | REJECT | 0 | 4 |
| C_invalid_missing | excluding_T4 | V4 | ACCEPT | 10 | 7 |
| C_invalid_missing | excluding_T4 | V4 | FLAG | 15 | 17 |
| C_invalid_missing | excluding_T4 | V4 | REJECT | 0 | 2 |
| C_invalid_missing | excluding_T4_and_T3_name | V1 | ACCEPT | 9 | 4 |
| C_invalid_missing | excluding_T4_and_T3_name | V1 | FLAG | 14 | 19 |
| C_invalid_missing | excluding_T4_and_T3_name | V1 | REJECT | 0 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | V2 | ACCEPT | 22 | 12 |
| C_invalid_missing | excluding_T4_and_T3_name | V2 | FLAG | 1 | 10 |
| C_invalid_missing | excluding_T4_and_T3_name | V2 | REJECT | 0 | 2 |
| C_invalid_missing | excluding_T4_and_T3_name | V3 | ACCEPT | 9 | 4 |
| C_invalid_missing | excluding_T4_and_T3_name | V3 | FLAG | 14 | 17 |
| C_invalid_missing | excluding_T4_and_T3_name | V3 | REJECT | 0 | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | V4 | ACCEPT | 10 | 7 |
| C_invalid_missing | excluding_T4_and_T3_name | V4 | FLAG | 13 | 15 |
| C_invalid_missing | excluding_T4_and_T3_name | V4 | REJECT | 0 | 2 |

## Exploratory repositories

| accounting | cohort | repository | decision | correct | wrong |
| --- | --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_excluded | primary | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_excluded | primary | astropy__astropy | REJECT | 0 | 0 |
| S_invalid_excluded | primary | django__django | ACCEPT | 2 | 0 |
| S_invalid_excluded | primary | django__django | FLAG | 6 | 8 |
| S_invalid_excluded | primary | django__django | REJECT | 0 | 3 |
| S_invalid_excluded | primary | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_excluded | primary | matplotlib__matplotlib | FLAG | 6 | 5 |
| S_invalid_excluded | primary | matplotlib__matplotlib | REJECT | 0 | 1 |
| S_invalid_excluded | primary | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_excluded | primary | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_excluded | primary | pydata__xarray | REJECT | 0 | 0 |
| S_invalid_excluded | primary | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_excluded | primary | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_excluded | primary | pylint-dev__pylint | REJECT | 0 | 0 |
| S_invalid_excluded | primary | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_excluded | primary | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_excluded | primary | pytest-dev__pytest | REJECT | 0 | 0 |
| S_invalid_excluded | primary | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_excluded | primary | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_excluded | primary | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| S_invalid_excluded | primary | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_excluded | primary | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_excluded | primary | sphinx-doc__sphinx | REJECT | 0 | 0 |
| S_invalid_excluded | primary | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_excluded | primary | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_excluded | primary | sympy__sympy | REJECT | 0 | 0 |
| S_invalid_excluded | including_no_patch | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_excluded | including_no_patch | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_excluded | including_no_patch | astropy__astropy | REJECT | 0 | 1 |
| S_invalid_excluded | including_no_patch | django__django | ACCEPT | 2 | 0 |
| S_invalid_excluded | including_no_patch | django__django | FLAG | 6 | 8 |
| S_invalid_excluded | including_no_patch | django__django | REJECT | 0 | 15 |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib | FLAG | 6 | 5 |
| S_invalid_excluded | including_no_patch | matplotlib__matplotlib | REJECT | 0 | 8 |
| S_invalid_excluded | including_no_patch | mwaskom__seaborn | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch | mwaskom__seaborn | FLAG | 0 | 0 |
| S_invalid_excluded | including_no_patch | mwaskom__seaborn | REJECT | 0 | 1 |
| S_invalid_excluded | including_no_patch | pallets__flask | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch | pallets__flask | FLAG | 0 | 0 |
| S_invalid_excluded | including_no_patch | pallets__flask | REJECT | 0 | 1 |
| S_invalid_excluded | including_no_patch | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_excluded | including_no_patch | pydata__xarray | REJECT | 0 | 4 |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_excluded | including_no_patch | pylint-dev__pylint | REJECT | 0 | 5 |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_excluded | including_no_patch | pytest-dev__pytest | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_excluded | including_no_patch | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_excluded | including_no_patch | scikit-learn__scikit-learn | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_excluded | including_no_patch | sphinx-doc__sphinx | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_excluded | including_no_patch | sympy__sympy | REJECT | 0 | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy | REJECT | 0 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django | ACCEPT | 2 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django | FLAG | 6 | 8 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | django__django | REJECT | 0 | 16 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib | FLAG | 6 | 5 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib | REJECT | 0 | 8 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | mwaskom__seaborn | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | mwaskom__seaborn | FLAG | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | mwaskom__seaborn | REJECT | 0 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pallets__flask | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pallets__flask | FLAG | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pallets__flask | REJECT | 0 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray | REJECT | 0 | 4 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint | REJECT | 0 | 5 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | REJECT | 0 | 2 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy | REJECT | 0 | 3 |
| S_invalid_excluded | excluding_T4 | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_excluded | excluding_T4 | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_excluded | excluding_T4 | astropy__astropy | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | django__django | ACCEPT | 2 | 0 |
| S_invalid_excluded | excluding_T4 | django__django | FLAG | 6 | 8 |
| S_invalid_excluded | excluding_T4 | django__django | REJECT | 0 | 3 |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib | FLAG | 6 | 5 |
| S_invalid_excluded | excluding_T4 | matplotlib__matplotlib | REJECT | 0 | 1 |
| S_invalid_excluded | excluding_T4 | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_excluded | excluding_T4 | pydata__xarray | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_excluded | excluding_T4 | pylint-dev__pylint | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_excluded | excluding_T4 | pytest-dev__pytest | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_excluded | excluding_T4 | sphinx-doc__sphinx | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4 | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_excluded | excluding_T4 | sympy__sympy | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django | ACCEPT | 2 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django | FLAG | 5 | 7 |
| S_invalid_excluded | excluding_T4_and_T3_name | django__django | REJECT | 0 | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib | FLAG | 5 | 5 |
| S_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx | REJECT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy | REJECT | 0 | 0 |
| S_invalid_missing | primary | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_missing | primary | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_missing | primary | astropy__astropy | REJECT | 0 | 0 |
| S_invalid_missing | primary | django__django | ACCEPT | 2 | 0 |
| S_invalid_missing | primary | django__django | FLAG | 6 | 8 |
| S_invalid_missing | primary | django__django | REJECT | 0 | 3 |
| S_invalid_missing | primary | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_missing | primary | matplotlib__matplotlib | FLAG | 6 | 5 |
| S_invalid_missing | primary | matplotlib__matplotlib | REJECT | 0 | 1 |
| S_invalid_missing | primary | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_missing | primary | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_missing | primary | pydata__xarray | REJECT | 0 | 0 |
| S_invalid_missing | primary | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_missing | primary | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_missing | primary | pylint-dev__pylint | REJECT | 0 | 0 |
| S_invalid_missing | primary | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_missing | primary | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_missing | primary | pytest-dev__pytest | REJECT | 0 | 0 |
| S_invalid_missing | primary | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_missing | primary | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_missing | primary | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| S_invalid_missing | primary | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_missing | primary | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_missing | primary | sphinx-doc__sphinx | REJECT | 0 | 0 |
| S_invalid_missing | primary | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_missing | primary | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_missing | primary | sympy__sympy | REJECT | 0 | 0 |
| S_invalid_missing | including_no_patch | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_missing | including_no_patch | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_missing | including_no_patch | astropy__astropy | REJECT | 0 | 1 |
| S_invalid_missing | including_no_patch | django__django | ACCEPT | 2 | 0 |
| S_invalid_missing | including_no_patch | django__django | FLAG | 6 | 8 |
| S_invalid_missing | including_no_patch | django__django | REJECT | 0 | 15 |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib | FLAG | 6 | 5 |
| S_invalid_missing | including_no_patch | matplotlib__matplotlib | REJECT | 0 | 8 |
| S_invalid_missing | including_no_patch | mwaskom__seaborn | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch | mwaskom__seaborn | FLAG | 0 | 0 |
| S_invalid_missing | including_no_patch | mwaskom__seaborn | REJECT | 0 | 1 |
| S_invalid_missing | including_no_patch | pallets__flask | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch | pallets__flask | FLAG | 0 | 0 |
| S_invalid_missing | including_no_patch | pallets__flask | REJECT | 0 | 1 |
| S_invalid_missing | including_no_patch | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_missing | including_no_patch | pydata__xarray | REJECT | 0 | 4 |
| S_invalid_missing | including_no_patch | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_missing | including_no_patch | pylint-dev__pylint | REJECT | 0 | 5 |
| S_invalid_missing | including_no_patch | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_missing | including_no_patch | pytest-dev__pytest | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_missing | including_no_patch | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_missing | including_no_patch | scikit-learn__scikit-learn | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_missing | including_no_patch | sphinx-doc__sphinx | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_missing | including_no_patch | sympy__sympy | REJECT | 0 | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy | REJECT | 0 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django | ACCEPT | 2 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django | FLAG | 6 | 8 |
| S_invalid_missing | including_no_patch_and_provider_blocked | django__django | REJECT | 0 | 16 |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib | FLAG | 6 | 5 |
| S_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib | REJECT | 0 | 8 |
| S_invalid_missing | including_no_patch_and_provider_blocked | mwaskom__seaborn | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | mwaskom__seaborn | FLAG | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | mwaskom__seaborn | REJECT | 0 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pallets__flask | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pallets__flask | FLAG | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pallets__flask | REJECT | 0 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray | REJECT | 0 | 4 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint | REJECT | 0 | 5 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | REJECT | 0 | 2 |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy | REJECT | 0 | 3 |
| S_invalid_missing | excluding_T4 | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_missing | excluding_T4 | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_missing | excluding_T4 | astropy__astropy | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4 | django__django | ACCEPT | 2 | 0 |
| S_invalid_missing | excluding_T4 | django__django | FLAG | 6 | 8 |
| S_invalid_missing | excluding_T4 | django__django | REJECT | 0 | 3 |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib | FLAG | 6 | 5 |
| S_invalid_missing | excluding_T4 | matplotlib__matplotlib | REJECT | 0 | 1 |
| S_invalid_missing | excluding_T4 | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4 | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_missing | excluding_T4 | pydata__xarray | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_missing | excluding_T4 | pylint-dev__pylint | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_missing | excluding_T4 | pytest-dev__pytest | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4 | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_missing | excluding_T4 | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_missing | excluding_T4 | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_missing | excluding_T4 | sphinx-doc__sphinx | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4 | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4 | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_missing | excluding_T4 | sympy__sympy | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy | ACCEPT | 0 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy | FLAG | 1 | 2 |
| S_invalid_missing | excluding_T4_and_T3_name | astropy__astropy | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | django__django | ACCEPT | 2 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | django__django | FLAG | 5 | 7 |
| S_invalid_missing | excluding_T4_and_T3_name | django__django | REJECT | 0 | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib | FLAG | 5 | 5 |
| S_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | pydata__xarray | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | pydata__xarray | FLAG | 0 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | pydata__xarray | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint | FLAG | 1 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest | FLAG | 5 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx | FLAG | 0 | 3 |
| S_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx | REJECT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy | ACCEPT | 0 | 0 |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy | FLAG | 1 | 1 |
| S_invalid_missing | excluding_T4_and_T3_name | sympy__sympy | REJECT | 0 | 0 |
| C_invalid_excluded | primary | astropy__astropy | ACCEPT | 1 | 1 |
| C_invalid_excluded | primary | astropy__astropy | FLAG | 0 | 2 |
| C_invalid_excluded | primary | astropy__astropy | REJECT | 0 | 0 |
| C_invalid_excluded | primary | django__django | ACCEPT | 5 | 1 |
| C_invalid_excluded | primary | django__django | FLAG | 3 | 7 |
| C_invalid_excluded | primary | django__django | REJECT | 0 | 3 |
| C_invalid_excluded | primary | matplotlib__matplotlib | ACCEPT | 4 | 0 |
| C_invalid_excluded | primary | matplotlib__matplotlib | FLAG | 2 | 5 |
| C_invalid_excluded | primary | matplotlib__matplotlib | REJECT | 0 | 1 |
| C_invalid_excluded | primary | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_excluded | primary | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_excluded | primary | pydata__xarray | REJECT | 0 | 0 |
| C_invalid_excluded | primary | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_excluded | primary | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_excluded | primary | pylint-dev__pylint | REJECT | 0 | 0 |
| C_invalid_excluded | primary | pytest-dev__pytest | ACCEPT | 3 | 0 |
| C_invalid_excluded | primary | pytest-dev__pytest | FLAG | 2 | 0 |
| C_invalid_excluded | primary | pytest-dev__pytest | REJECT | 0 | 0 |
| C_invalid_excluded | primary | scikit-learn__scikit-learn | ACCEPT | 3 | 0 |
| C_invalid_excluded | primary | scikit-learn__scikit-learn | FLAG | 0 | 0 |
| C_invalid_excluded | primary | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| C_invalid_excluded | primary | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_excluded | primary | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_excluded | primary | sphinx-doc__sphinx | REJECT | 0 | 0 |
| C_invalid_excluded | primary | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_excluded | primary | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_excluded | primary | sympy__sympy | REJECT | 0 | 0 |
| C_invalid_excluded | including_no_patch | astropy__astropy | ACCEPT | 1 | 1 |
| C_invalid_excluded | including_no_patch | astropy__astropy | FLAG | 0 | 2 |
| C_invalid_excluded | including_no_patch | astropy__astropy | REJECT | 0 | 1 |
| C_invalid_excluded | including_no_patch | django__django | ACCEPT | 5 | 1 |
| C_invalid_excluded | including_no_patch | django__django | FLAG | 3 | 7 |
| C_invalid_excluded | including_no_patch | django__django | REJECT | 0 | 15 |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib | ACCEPT | 4 | 0 |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib | FLAG | 2 | 5 |
| C_invalid_excluded | including_no_patch | matplotlib__matplotlib | REJECT | 0 | 8 |
| C_invalid_excluded | including_no_patch | mwaskom__seaborn | ACCEPT | 0 | 0 |
| C_invalid_excluded | including_no_patch | mwaskom__seaborn | FLAG | 0 | 0 |
| C_invalid_excluded | including_no_patch | mwaskom__seaborn | REJECT | 0 | 1 |
| C_invalid_excluded | including_no_patch | pallets__flask | ACCEPT | 0 | 0 |
| C_invalid_excluded | including_no_patch | pallets__flask | FLAG | 0 | 0 |
| C_invalid_excluded | including_no_patch | pallets__flask | REJECT | 0 | 1 |
| C_invalid_excluded | including_no_patch | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_excluded | including_no_patch | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_excluded | including_no_patch | pydata__xarray | REJECT | 0 | 4 |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_excluded | including_no_patch | pylint-dev__pylint | REJECT | 0 | 5 |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest | ACCEPT | 3 | 0 |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest | FLAG | 2 | 0 |
| C_invalid_excluded | including_no_patch | pytest-dev__pytest | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch | scikit-learn__scikit-learn | ACCEPT | 3 | 0 |
| C_invalid_excluded | including_no_patch | scikit-learn__scikit-learn | FLAG | 0 | 0 |
| C_invalid_excluded | including_no_patch | scikit-learn__scikit-learn | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_excluded | including_no_patch | sphinx-doc__sphinx | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_excluded | including_no_patch | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_excluded | including_no_patch | sympy__sympy | REJECT | 0 | 3 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy | ACCEPT | 1 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy | FLAG | 0 | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | astropy__astropy | REJECT | 0 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django | ACCEPT | 5 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django | FLAG | 3 | 7 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | django__django | REJECT | 0 | 16 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib | ACCEPT | 4 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib | FLAG | 2 | 5 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | matplotlib__matplotlib | REJECT | 0 | 8 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | mwaskom__seaborn | ACCEPT | 0 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | mwaskom__seaborn | FLAG | 0 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | mwaskom__seaborn | REJECT | 0 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pallets__flask | ACCEPT | 0 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pallets__flask | FLAG | 0 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pallets__flask | REJECT | 0 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pydata__xarray | REJECT | 0 | 4 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pylint-dev__pylint | REJECT | 0 | 5 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest | ACCEPT | 3 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest | FLAG | 2 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | pytest-dev__pytest | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | ACCEPT | 3 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | FLAG | 0 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | REJECT | 0 | 2 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | sympy__sympy | REJECT | 0 | 3 |
| C_invalid_excluded | excluding_T4 | astropy__astropy | ACCEPT | 1 | 1 |
| C_invalid_excluded | excluding_T4 | astropy__astropy | FLAG | 0 | 2 |
| C_invalid_excluded | excluding_T4 | astropy__astropy | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4 | django__django | ACCEPT | 5 | 1 |
| C_invalid_excluded | excluding_T4 | django__django | FLAG | 3 | 7 |
| C_invalid_excluded | excluding_T4 | django__django | REJECT | 0 | 3 |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib | ACCEPT | 4 | 0 |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib | FLAG | 2 | 5 |
| C_invalid_excluded | excluding_T4 | matplotlib__matplotlib | REJECT | 0 | 1 |
| C_invalid_excluded | excluding_T4 | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_excluded | excluding_T4 | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_excluded | excluding_T4 | pydata__xarray | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_excluded | excluding_T4 | pylint-dev__pylint | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest | ACCEPT | 3 | 0 |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest | FLAG | 2 | 0 |
| C_invalid_excluded | excluding_T4 | pytest-dev__pytest | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn | ACCEPT | 3 | 0 |
| C_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn | FLAG | 0 | 0 |
| C_invalid_excluded | excluding_T4 | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_excluded | excluding_T4 | sphinx-doc__sphinx | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4 | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_excluded | excluding_T4 | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_excluded | excluding_T4 | sympy__sympy | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy | ACCEPT | 1 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy | FLAG | 0 | 2 |
| C_invalid_excluded | excluding_T4_and_T3_name | astropy__astropy | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django | ACCEPT | 5 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django | FLAG | 2 | 6 |
| C_invalid_excluded | excluding_T4_and_T3_name | django__django | REJECT | 0 | 3 |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib | ACCEPT | 4 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib | FLAG | 1 | 5 |
| C_invalid_excluded | excluding_T4_and_T3_name | matplotlib__matplotlib | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | pydata__xarray | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | pylint-dev__pylint | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest | ACCEPT | 3 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest | FLAG | 2 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | pytest-dev__pytest | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn | ACCEPT | 3 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn | FLAG | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_excluded | excluding_T4_and_T3_name | sphinx-doc__sphinx | REJECT | 0 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_excluded | excluding_T4_and_T3_name | sympy__sympy | REJECT | 0 | 0 |
| C_invalid_missing | primary | astropy__astropy | ACCEPT | 0 | 1 |
| C_invalid_missing | primary | astropy__astropy | FLAG | 1 | 2 |
| C_invalid_missing | primary | astropy__astropy | REJECT | 0 | 0 |
| C_invalid_missing | primary | django__django | ACCEPT | 4 | 1 |
| C_invalid_missing | primary | django__django | FLAG | 4 | 7 |
| C_invalid_missing | primary | django__django | REJECT | 0 | 3 |
| C_invalid_missing | primary | matplotlib__matplotlib | ACCEPT | 3 | 0 |
| C_invalid_missing | primary | matplotlib__matplotlib | FLAG | 3 | 5 |
| C_invalid_missing | primary | matplotlib__matplotlib | REJECT | 0 | 1 |
| C_invalid_missing | primary | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_missing | primary | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_missing | primary | pydata__xarray | REJECT | 0 | 0 |
| C_invalid_missing | primary | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_missing | primary | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_missing | primary | pylint-dev__pylint | REJECT | 0 | 0 |
| C_invalid_missing | primary | pytest-dev__pytest | ACCEPT | 0 | 0 |
| C_invalid_missing | primary | pytest-dev__pytest | FLAG | 5 | 0 |
| C_invalid_missing | primary | pytest-dev__pytest | REJECT | 0 | 0 |
| C_invalid_missing | primary | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| C_invalid_missing | primary | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| C_invalid_missing | primary | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| C_invalid_missing | primary | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_missing | primary | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_missing | primary | sphinx-doc__sphinx | REJECT | 0 | 0 |
| C_invalid_missing | primary | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_missing | primary | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_missing | primary | sympy__sympy | REJECT | 0 | 0 |
| C_invalid_missing | including_no_patch | astropy__astropy | ACCEPT | 0 | 1 |
| C_invalid_missing | including_no_patch | astropy__astropy | FLAG | 1 | 2 |
| C_invalid_missing | including_no_patch | astropy__astropy | REJECT | 0 | 1 |
| C_invalid_missing | including_no_patch | django__django | ACCEPT | 4 | 1 |
| C_invalid_missing | including_no_patch | django__django | FLAG | 4 | 7 |
| C_invalid_missing | including_no_patch | django__django | REJECT | 0 | 15 |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib | ACCEPT | 3 | 0 |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib | FLAG | 3 | 5 |
| C_invalid_missing | including_no_patch | matplotlib__matplotlib | REJECT | 0 | 8 |
| C_invalid_missing | including_no_patch | mwaskom__seaborn | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch | mwaskom__seaborn | FLAG | 0 | 0 |
| C_invalid_missing | including_no_patch | mwaskom__seaborn | REJECT | 0 | 1 |
| C_invalid_missing | including_no_patch | pallets__flask | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch | pallets__flask | FLAG | 0 | 0 |
| C_invalid_missing | including_no_patch | pallets__flask | REJECT | 0 | 1 |
| C_invalid_missing | including_no_patch | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_missing | including_no_patch | pydata__xarray | REJECT | 0 | 4 |
| C_invalid_missing | including_no_patch | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_missing | including_no_patch | pylint-dev__pylint | REJECT | 0 | 5 |
| C_invalid_missing | including_no_patch | pytest-dev__pytest | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch | pytest-dev__pytest | FLAG | 5 | 0 |
| C_invalid_missing | including_no_patch | pytest-dev__pytest | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| C_invalid_missing | including_no_patch | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| C_invalid_missing | including_no_patch | scikit-learn__scikit-learn | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_missing | including_no_patch | sphinx-doc__sphinx | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_missing | including_no_patch | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_missing | including_no_patch | sympy__sympy | REJECT | 0 | 3 |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy | ACCEPT | 0 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy | FLAG | 1 | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | astropy__astropy | REJECT | 0 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django | ACCEPT | 4 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django | FLAG | 4 | 7 |
| C_invalid_missing | including_no_patch_and_provider_blocked | django__django | REJECT | 0 | 16 |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib | ACCEPT | 3 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib | FLAG | 3 | 5 |
| C_invalid_missing | including_no_patch_and_provider_blocked | matplotlib__matplotlib | REJECT | 0 | 8 |
| C_invalid_missing | including_no_patch_and_provider_blocked | mwaskom__seaborn | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | mwaskom__seaborn | FLAG | 0 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | mwaskom__seaborn | REJECT | 0 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pallets__flask | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pallets__flask | FLAG | 0 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pallets__flask | REJECT | 0 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pydata__xarray | REJECT | 0 | 4 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pylint-dev__pylint | REJECT | 0 | 5 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest | ACCEPT | 0 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest | FLAG | 5 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | pytest-dev__pytest | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | scikit-learn__scikit-learn | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | sphinx-doc__sphinx | REJECT | 0 | 2 |
| C_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_missing | including_no_patch_and_provider_blocked | sympy__sympy | REJECT | 0 | 3 |
| C_invalid_missing | excluding_T4 | astropy__astropy | ACCEPT | 0 | 1 |
| C_invalid_missing | excluding_T4 | astropy__astropy | FLAG | 1 | 2 |
| C_invalid_missing | excluding_T4 | astropy__astropy | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4 | django__django | ACCEPT | 4 | 1 |
| C_invalid_missing | excluding_T4 | django__django | FLAG | 4 | 7 |
| C_invalid_missing | excluding_T4 | django__django | REJECT | 0 | 3 |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib | ACCEPT | 3 | 0 |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib | FLAG | 3 | 5 |
| C_invalid_missing | excluding_T4 | matplotlib__matplotlib | REJECT | 0 | 1 |
| C_invalid_missing | excluding_T4 | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_missing | excluding_T4 | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_missing | excluding_T4 | pydata__xarray | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_missing | excluding_T4 | pylint-dev__pylint | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest | ACCEPT | 0 | 0 |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest | FLAG | 5 | 0 |
| C_invalid_missing | excluding_T4 | pytest-dev__pytest | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4 | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| C_invalid_missing | excluding_T4 | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| C_invalid_missing | excluding_T4 | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_missing | excluding_T4 | sphinx-doc__sphinx | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4 | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_missing | excluding_T4 | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_missing | excluding_T4 | sympy__sympy | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy | ACCEPT | 0 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy | FLAG | 1 | 2 |
| C_invalid_missing | excluding_T4_and_T3_name | astropy__astropy | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | django__django | ACCEPT | 4 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | django__django | FLAG | 3 | 6 |
| C_invalid_missing | excluding_T4_and_T3_name | django__django | REJECT | 0 | 3 |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib | ACCEPT | 3 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib | FLAG | 2 | 5 |
| C_invalid_missing | excluding_T4_and_T3_name | matplotlib__matplotlib | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | pydata__xarray | ACCEPT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | pydata__xarray | FLAG | 0 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | pydata__xarray | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint | ACCEPT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint | FLAG | 1 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | pylint-dev__pylint | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest | ACCEPT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest | FLAG | 5 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | pytest-dev__pytest | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn | ACCEPT | 2 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn | FLAG | 1 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | scikit-learn__scikit-learn | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx | ACCEPT | 0 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx | FLAG | 0 | 2 |
| C_invalid_missing | excluding_T4_and_T3_name | sphinx-doc__sphinx | REJECT | 0 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | sympy__sympy | ACCEPT | 0 | 1 |
| C_invalid_missing | excluding_T4_and_T3_name | sympy__sympy | FLAG | 1 | 0 |
| C_invalid_missing | excluding_T4_and_T3_name | sympy__sympy | REJECT | 0 | 0 |

## Exploratory cost

| accounting | cohort | total_usd | correct_ACCEPT | cost_per_correct_ACCEPT_usd | median_task_usd |
| --- | --- | --- | --- | --- | --- |
| S_invalid_excluded | primary | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_excluded | including_no_patch | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_excluded | including_no_patch_and_provider_blocked | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_excluded | excluding_T4 | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_excluded | excluding_T4_and_T3_name | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_missing | primary | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_missing | including_no_patch | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_missing | including_no_patch_and_provider_blocked | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_missing | excluding_T4 | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| S_invalid_missing | excluding_T4_and_T3_name | 17.889181 | 4 | 4.47229524 | 0.19913612 |
| C_invalid_excluded | primary | 17.889181 | 16 | 1.11807381 | 0.19913612 |
| C_invalid_excluded | including_no_patch | 17.889181 | 16 | 1.11807381 | 0.19913612 |
| C_invalid_excluded | including_no_patch_and_provider_blocked | 17.889181 | 16 | 1.11807381 | 0.19913612 |
| C_invalid_excluded | excluding_T4 | 17.889181 | 16 | 1.11807381 | 0.19913612 |
| C_invalid_excluded | excluding_T4_and_T3_name | 17.889181 | 16 | 1.11807381 | 0.19913612 |
| C_invalid_missing | primary | 17.889181 | 9 | 1.98768677 | 0.19913612 |
| C_invalid_missing | including_no_patch | 17.889181 | 9 | 1.98768677 | 0.19913612 |
| C_invalid_missing | including_no_patch_and_provider_blocked | 17.889181 | 9 | 1.98768677 | 0.19913612 |
| C_invalid_missing | excluding_T4 | 17.889181 | 9 | 1.98768677 | 0.19913612 |
| C_invalid_missing | excluding_T4_and_T3_name | 17.889181 | 9 | 1.98768677 | 0.19913612 |
