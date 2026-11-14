# Probe stopped: AUTH_ERROR

Date: 2026-11-14 (America/Phoenix). Branch: `feature/umgpt-routing`.

The first and only live verification request was `openai/gpt-4.1-mini` at
`https://api.toolkit.umgpt.umich.edu/v1/chat/completions`. UM returned HTTP 401:

```json
{"status":"failure","message":"Portkey Error: Invalid API Key. Error Code: 03","error":{"message":"Portkey Error: Invalid API Key. Error Code: 03","code":"03"}}
```

The key was read from the existing ignored `.env`; there was no inherited
`UMGPT_API_KEY` override. No credential was printed or rewritten. Authentication
failures are not retried because backoff cannot repair a rejected credential.

No candidate passed. `gpt-4.1` and `gpt-4o-mini` were not attempted. Both new model
configs remain unverified (no `verified:` block). No probe task, 10-task pilot, or larger
run was launched. No served model, fingerprint, usage, or task measurement exists.
The failed live attempt did not persist rate-limit headers; their presence/values
are unknown. Mocked tests now cover their capture on errors.

Ledger: `runs/umgpt_spend_ledger.json`; one settled HTTP rejection, $0.00 estimated
spend, no outstanding reservation. No provider billing amount was returned.
Sanitized evidence: `runs/umgpt_probe/verification.json` and the committed report.

**One decision needed:** supply a valid UM Toolkit credential in the local ignored
`.env` and authorize resuming paid verification/probing. Do not paste the key into
chat. Preserve the spend ledger and this failed attempt when resuming.

Separately, historical `pilot_15` trajectories are absent from the accessible
projects/archive; its token-based comparison cannot be calculated from this host.
