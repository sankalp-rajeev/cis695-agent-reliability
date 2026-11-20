# Phase 2 patch fetch

Fetched counts include all existing submission objects. Blank and null submissions have zero-byte, read-only patch files.

| Priority | System | Set | Checked | Fetched | Empty (blank) | Empty (null) | Missing | Malformed |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `gpt-4.1-mini-2025-04-14` | Dev | 92/92 | 92 | 0 | 4 | 0 | 0 |
| 1 | `gpt-4.1-mini-2025-04-14` | Test | 108/108 | 108 | 0 | 3 | 0 | 0 |
| 2 | `claude-sonnet-4-20250514` | Dev | 92/92 | 92 | 0 | 0 | 0 | 0 |
| 2 | `claude-sonnet-4-20250514` | Test | 108/108 | 108 | 0 | 0 | 0 | 0 |
| 3 | `gpt-4.1-2025-04-14` | Dev | 92/92 | 92 | 2 | 0 | 0 | 0 |
| 3 | `gpt-4.1-2025-04-14` | Test | 108/108 | 108 | 6 | 0 | 0 | 0 |
| 4 | `gemini-2.5-flash` | Dev | 92/92 | 92 | 1 | 0 | 0 | 0 |
| 4 | `gemini-2.5-flash` | Test | 108/108 | 108 | 5 | 0 | 0 | 0 |
| 5 | `o4-mini-2025-04-16` | Dev | 92/92 | 92 | 0 | 0 | 0 | 0 |
| 5 | `o4-mini-2025-04-16` | Test | 108/108 | 108 | 3 | 0 | 0 | 0 |
| 6 | `qwen3-coder-480b-a35b-instruct` | Dev | 92/92 | 92 | 4 | 0 | 0 | 0 |
| 6 | `qwen3-coder-480b-a35b-instruct` | Test | 108/108 | 108 | 3 | 0 | 0 | 0 |

Gate passed. Each system had at most five missing plus malformed submissions in each gate set.

Across all attempted public keys including reserves, 1332 of 1,332 were checked and 1332 fetched. There were 26 blank, 8 null, 0 missing, and 0 malformed.

## Sonnet cross-check

222/222 fetched Claude Sonnet 4 submissions matched the raw patch SHA-256 in `all_preds.jsonl`.
Source SHA-256 `a869ab8aa7fb1ebf1b62a83e27e99a991fbf3306a494fc0abb114c61c785d94d`.

## Reference patches

Extracted 181 reference patches from the cached dataset for 51 development IDs and 130 test IDs.

## Malformed predictions

None among checked keys.
