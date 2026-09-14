# CIS 695 — Reliable LLM Agents for Automated Software Repair

Research pipeline for *Trust but Verify: Execution-Grounded Selective Validation of
LLM-Generated Software Repairs*.

The pipeline keeps three information layers strictly separated:

1. **Repair** — a fixed `mini-swe-agent` scaffold produces a candidate patch and an
   explicit `RESOLVED` / `UNRESOLVED` claim.
2. **Verification** — an oracle-blind verifier scores the frozen patch on patch
   integrity, regression tests, static/build checks, and independently generated
   reproduction tests, then emits `ACCEPT` / `FLAG` / `REJECT`.
3. **Oracle** — the official SWE-bench harness produces the research label only
   after the decisions above are frozen.

See `docs/` for the project overview, technical design, and literature review.

## Environment

```powershell
uv sync
.\.venv\Scripts\Activate.ps1
```
