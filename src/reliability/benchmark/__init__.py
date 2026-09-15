"""Benchmark loading, sandboxing, and oracle access.

This layer is the only one permitted to read oracle fields (`patch`,
`test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`), and it must hand the agent layer
an `AgentTask` from which those fields are unreachable. See Phase 2.2.
"""
