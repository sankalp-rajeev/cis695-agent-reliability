# Fix 0 owner check (offline, base archives, AST only)

The three missing-argument signatures cover 2,550 selected tree slots across
1,275 task/label pairs in 10 tasks. Each CSV row represents one task/label/signature
and records both tree slots. Batch collateral is included.

| Exclusive category | Labels | Tree slots |
|---|---:|---:|
| Undecorated method on non-TestCase owner | 409 | 818 |
| Module-level function | 2 | 4 |
| Decorated function or method | 225 | 450 |
| Other (638 ordinary TestCase methods, one invalid nested-helper label) | 639 | 1,278 |

Decoration takes precedence in the category column. Independently, 476 labels
have non-TestCase owners (including 67 decorated methods); the CSV lists all
concrete TestCase subclasses inheriting each method unchanged and their counts.
Ten labels have no such subclass. The potential expansion is 2347 identities
(4694 tree instances), reported separately from original selected slots.
This is a diagnostic inventory; no IDs have been expanded or executed.

Class ancestry follows imports/re-exports and C3 method resolution across the
same archived repo. Overridden methods are excluded. Archived source is parsed,
never imported or executed; Docker calls: 0. Archive hashes are checked against
the frozen task metadata. See `fix0_owner_check_summary.json` for hashes and
`scripts/phase4_fix0_owner_check.py` for reproduction.
