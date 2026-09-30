"""Parse the agent's structured final claim (Phase 3.2).

The agent is required to end with:

    FINAL_STATUS: RESOLVED | UNRESOLVED
    VALIDATION_EVIDENCE: <what it did to check>

The claim is a *measured quantity*, not a convenience. Phase 9.3 gates the pilot
on claim capture rate, and the whole research question is whether an agent's
self-assessment predicts a real repair. So an unreadable claim must surface as
`UNPARSEABLE` and never collapse into `UNRESOLVED`: silently defaulting would
invent an agent assertion that was never made, and would bias exactly the
quantity under study.

Three parsing decisions worth stating, because each could reasonably go the
other way:

1. **Formatting is forgiven; structure is not.** Markdown emphasis, backticks,
   and spacing around the marker are tolerated, because a model wrapping its
   answer in `**bold**` has still answered. But the literal `FINAL_STATUS` key
   and an exact status token are required. "I think it's resolved" is
   `UNPARSEABLE` - prose agreement is not a claim, and accepting it would let the
   parser infer intent the agent never committed to.

2. **Disagreement is unparseable, not last-wins.** A trajectory containing both
   `FINAL_STATUS: RESOLVED` and `FINAL_STATUS: UNRESOLVED` has no single claim.
   Taking the last one would fabricate a resolution to genuine ambiguity.
   Repeated *agreeing* markers are fine - models often restate their answer.

3. **Missing evidence does not void the status.** `VALIDATION_EVIDENCE` is
   recorded separately as `evidence`/`has_evidence` rather than downgrading a
   well-formed status to `UNPARSEABLE`. Status capture rate (Phase 9.3) and
   evidence quality are different measurements, and conflating them would make
   the 9.3 gate unreadable. A status without evidence is a complete claim that is
   poorly supported, which is itself a finding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

STATUS_MARKER = "FINAL_STATUS"
EVIDENCE_MARKER = "VALIDATION_EVIDENCE"


class ClaimStatus(str, Enum):
    """The agent's self-assessment, or an explicit failure to state one."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    UNPARSEABLE = "UNPARSEABLE"


class UnparseableReason(str, Enum):
    """Why a claim could not be read. Recorded so failures can be triaged."""

    MISSING = "missing"          # no FINAL_STATUS marker at all
    INVALID_VALUE = "invalid_value"  # marker present, value not a valid status
    AMBIGUOUS = "ambiguous"      # conflicting markers
    EMPTY_OUTPUT = "empty_output"
    # Set by the runner, never by the parser: the run ended before submission
    # (step or cost limit, timeout, throttling, error), so there was no final
    # output to read. Not a formatting failure.
    NEVER_FINISHED = "never_finished"


#: Tolerates markdown emphasis and backticks around the key, and `:` or `=`.
#: The key itself must appear literally; `final status` without the underscore
#: does not match, since that is prose rather than the required marker.
_STATUS_RE = re.compile(
    rf"[*_`\s]*{STATUS_MARKER}[*_`\s]*[:=][*_`\s]*([A-Za-z_]+)",
    re.IGNORECASE,
)

_EVIDENCE_RE = re.compile(
    rf"[*_`\s]*{EVIDENCE_MARKER}[*_`\s]*[:=][*_`\s]*(.*?)"
    rf"(?=\n\s*[*_`\s]*{STATUS_MARKER}[*_`\s]*[:=]|\Z)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class ParsedClaim:
    """The outcome of reading an agent's final output."""

    status: ClaimStatus
    evidence: str | None = None
    reason: UnparseableReason | None = None
    raw_status_tokens: tuple[str, ...] = ()

    @property
    def is_parseable(self) -> bool:
        return self.status is not ClaimStatus.UNPARSEABLE

    @property
    def has_evidence(self) -> bool:
        return bool(self.evidence and self.evidence.strip())


def _clean(text: str) -> str:
    """Strip trailing markdown noise from a captured span."""
    return text.strip().strip("*_`").strip()


def parse_claim(output: str | None) -> ParsedClaim:
    """Read the structured claim from an agent's final output.

    Never raises and never guesses: every path returns an explicit status, with
    `UNPARSEABLE` carrying a reason.
    """
    if output is None or not output.strip():
        return ParsedClaim(ClaimStatus.UNPARSEABLE, reason=UnparseableReason.EMPTY_OUTPUT)

    tokens = tuple(m.group(1).upper() for m in _STATUS_RE.finditer(output))

    evidence_match = _EVIDENCE_RE.search(output)
    evidence = _clean(evidence_match.group(1)) if evidence_match else None
    evidence = evidence or None

    if not tokens:
        return ParsedClaim(
            ClaimStatus.UNPARSEABLE,
            evidence=evidence,
            reason=UnparseableReason.MISSING,
        )

    valid = {ClaimStatus.RESOLVED.value, ClaimStatus.UNRESOLVED.value}
    distinct = set(tokens)

    if not distinct <= valid:
        return ParsedClaim(
            ClaimStatus.UNPARSEABLE,
            evidence=evidence,
            reason=UnparseableReason.INVALID_VALUE,
            raw_status_tokens=tokens,
        )

    if len(distinct) > 1:
        return ParsedClaim(
            ClaimStatus.UNPARSEABLE,
            evidence=evidence,
            reason=UnparseableReason.AMBIGUOUS,
            raw_status_tokens=tokens,
        )

    return ParsedClaim(
        ClaimStatus(distinct.pop()),
        evidence=evidence,
        raw_status_tokens=tokens,
    )
