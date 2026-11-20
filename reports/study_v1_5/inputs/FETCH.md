# Phase 2 patch fetch

The gate failed and acquisition stopped. Checked counts show observed coverage. Fetched counts include existing predictions with empty submissions. Missing entries returned an S3 HeadObject 404. Dashes indicate a set with zero checked keys.

| Priority | System | Set | Checked | Fetched | Empty (blank) | Empty (null) | Missing | Malformed |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `gpt-4.1-mini-2025-04-14` | Dev | 92/92 | 92 | 0 | 4 | 0 | 0 |
| 1 | `gpt-4.1-mini-2025-04-14` | Test | 108/108 | 108 | 0 | 3 | 0 | 0 |
| 2 | `claude-sonnet-4-20250514` | Dev | 92/92 | 0 | 0 | 0 | 92 | 0 |
| 2 | `claude-sonnet-4-20250514` | Test | 108/108 | 0 | 0 | 0 | 108 | 0 |
| 3 | `gpt-4.1-2025-04-14` | Dev | 49/92 | 0 | 0 | 0 | 49 | 0 |
| 3 | `gpt-4.1-2025-04-14` | Test | 0/108 | — | — | — | — | — |
| 4 | `gemini-2.5-flash` | Dev | 0/92 | — | — | — | — | — |
| 4 | `gemini-2.5-flash` | Test | 0/108 | — | — | — | — | — |
| 5 | `o4-mini-2025-04-16` | Dev | 0/92 | — | — | — | — | — |
| 5 | `o4-mini-2025-04-16` | Test | 0/108 | — | — | — | — | — |
| 6 | `qwen3-coder-480b-a35b-instruct` | Dev | 0/92 | — | — | — | — | — |
| 6 | `qwen3-coder-480b-a35b-instruct` | Test | 0/108 | — | — | — | — | — |

## Dropped systems

- `claude-sonnet-4-20250514`, Dev (92/92 checked, 92 missing, 0 malformed)
- `claude-sonnet-4-20250514`, Test (108/108 checked, 108 missing, 0 malformed)
- `gpt-4.1-2025-04-14`, Dev (49/92 checked, 49 missing, 0 malformed)

The running downloader finished Claude Sonnet 4 and checked part of GPT-4.1 before the gate failure was observed. The downloader now stops at the sixth combined missing or malformed prediction in either gate set.

Across all attempted keys, including reserves, 493 of 1,332 were checked and 222 were fetched. There were 0 blank, 8 null, 271 missing, and 0 malformed.

Priorities 4–6 and reference patch extraction were beyond the stop point.

## Malformed predictions

None among checked keys.
