"""The oracle layer: SWE-bench's own verdict on a frozen patch (Phase 8).

This is the only part of the pipeline permitted to read ground truth, and it is
deliberately the last thing to run. The ordering guard in `runner.py` enforces
that: the oracle cannot execute for a task until both the repair record and the
verification record already exist on disk, so neither the agent's claim nor the
verifier's decision can have been influenced by knowing the answer.
"""
