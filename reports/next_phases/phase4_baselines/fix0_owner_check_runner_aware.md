# Runner-aware owner-rule recheck

Re-ran the AST-only stored-base-archive owner inventory after replacing the
owner rule. The regenerated `fix0_owner_check.csv` is byte-identical to its
committed predecessor: **all 476 non-TestCase-owner task/labels are Django**
(952 tree slots), with **0 pytest and 0 SymPy** in this inventory. Since Django
uses unittest loading, the runner-aware rule yields the same **2,347 inherited
identities** and **10 labels without a runnable owner**. No classification,
subclass list or per-label count changed; see `fix0_owner_check_runner_aware.csv`.

This inventory is scoped to the prior three missing-argument signatures;
it does not claim that all frozen selections lack pytest class methods.
No Docker, benchmark source execution, outcomes or correctness labels were used.
