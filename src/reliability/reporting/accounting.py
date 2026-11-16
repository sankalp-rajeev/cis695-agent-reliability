"""Pre-registered Policy S reporting; does not participate in V2 execution."""

from collections import Counter

VARIANTS = ("S_invalid_excluded", "S_invalid_missing", "C_invalid_excluded", "C_invalid_missing")
DEFAULT_ACCOUNTING = VARIANTS[0]


def report_accounting(outcomes, variant=DEFAULT_ACCOUNTING):
    if variant not in VARIANTS:
        raise ValueError("unknown reporting accounting: " + variant)
    counts = Counter(outcomes.values() if isinstance(outcomes, dict) else outcomes)
    excluded = counts["INVALID_ID"] if variant.endswith("_excluded") else 0
    denominator = sum(counts.values()) - excluded
    admitted = {"PASS", "PASSED", "FAIL", "FAILED", "XFAIL", "XPASS"}
    if variant.startswith("C_"):
        admitted.add("SKIPPED")
    observed = sum(n for status, n in counts.items() if status in admitted)
    failed = any(counts[s] for s in ("FAIL", "FAILED", "REGRESSION", "REGRESSION_ERROR"))
    return {
        "accounting": variant,
        "primary": variant == DEFAULT_ACCOUNTING,
        "label": "primary" if variant == DEFAULT_ACCOUNTING else "sensitivity: " + variant,
        "INVALID_ID": counts["INVALID_ID"],
        "denominator": denominator,
        "observed": observed,
        "missing": denominator - observed,
        "status": "FAIL"
        if failed
        else ("PASS" if denominator and observed == denominator else "INCOMPLETE"),
    }


def accounting_sensitivities(outcomes):
    return [report_accounting(outcomes, variant) for variant in VARIANTS]
