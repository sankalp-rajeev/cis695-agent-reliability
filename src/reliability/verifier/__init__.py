"""Execution-grounded verification of frozen patches.

Operates on the patch and repository alone. Test selection must not consult
`PASS_TO_PASS`; the overlap between the selected set and `PASS_TO_PASS` is
measured after the fact as analysis only. See Phase 5.1 and 5.3.
"""
