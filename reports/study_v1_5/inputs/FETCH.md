# Phase 2 patch fetch

Format detection stopped at the Qwen3-Coder first development task folder (`astropy__astropy-13977`). Its S3 listing contained zero filenames. The same task folder listed `astropy__astropy-13977.traj.json` for Claude Sonnet 4, GPT-4.1, Gemini 2.5 Flash, and o4-mini.

The Claude Sonnet 4 and GPT-4.1 `.pred` 404 rows were withdrawn. Fetched counts include existing empty submissions. Dashes indicate zero checked prediction keys under the detected format.

| Priority | System | Set | Checked | Fetched | Empty (blank) | Empty (null) | Missing | Malformed |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `gpt-4.1-mini-2025-04-14` | Dev | 92/92 | 92 | 0 | 4 | 0 | 0 |
| 1 | `gpt-4.1-mini-2025-04-14` | Test | 108/108 | 108 | 0 | 3 | 0 | 0 |
| 2 | `claude-sonnet-4-20250514` | Dev | 0/92 | — | — | — | — | — |
| 2 | `claude-sonnet-4-20250514` | Test | 0/108 | — | — | — | — | — |
| 3 | `gpt-4.1-2025-04-14` | Dev | 0/92 | — | — | — | — | — |
| 3 | `gpt-4.1-2025-04-14` | Test | 0/108 | — | — | — | — | — |
| 4 | `gemini-2.5-flash` | Dev | 0/92 | — | — | — | — | — |
| 4 | `gemini-2.5-flash` | Test | 0/108 | — | — | — | — | — |
| 5 | `o4-mini-2025-04-16` | Dev | 0/92 | — | — | — | — | — |
| 5 | `o4-mini-2025-04-16` | Test | 0/108 | — | — | — | — | — |
| 6 | `qwen3-coder-480b-a35b-instruct` | Dev | 0/92 | — | — | — | — | — |
| 6 | `qwen3-coder-480b-a35b-instruct` | Test | 0/108 | — | — | — | — | — |

Including reserves, GPT-4.1 mini has 222 fetched predictions, 0 blank, 8 null, 0 missing, and 0 malformed.

The Sonnet cross-check and reference extraction are pending format detection.
