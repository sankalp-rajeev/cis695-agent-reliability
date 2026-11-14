# Fresh base-tree invocation comparison

Both invocations reproduce the same import-time `DeprecationWarning` followed by
`AttributeError: PyTestReporter._active_file`. Both exit with code 1, finish before
the cap, and report none of the 16 selected names. Both tracebacks are in stderr.
The harness command was executed literally, with no added environment variables
or Python flags. Each command used a separate fresh source-verified container.

| Property | Harness | Executor |
|---|---|---|
| Entry command | `bin/test -C --verbose sympy/physics/quantum/tests/test_printing.py` | `python /tmp/verifier_sympy_driver.py execute <module> <16 IDs>` |
| Working directory | `/testbed` | `/testbed` |
| Python executable | `/opt/miniconda3/envs/testbed/bin/python` | Same |
| Explicit Python `-W` flags | None | None |
| Native child Python flags | `-R -c` (runner-generated) | None |
| Inherited `PYTHONWARNINGS` / `PYTHONPATH` | Unset / unset | Unset / unset |
| Effective warning override | Native warning policy | Adapter sets `PYTHONWARNINGS=ignore::UserWarning,ignore::SyntaxWarning` and the corresponding interpreter filters; does not suppress `DeprecationWarning` |
| Cache | `-C` sets `SYMPY_USE_CACHE=no` | Same, set before initial import |
| Hash subprocess | Native default; sets a random `PYTHONHASHSEED` for the child | `--no-subprocess`; inherited seed remains unset to preserve exact-selection guards |
| Python path setup | `bin/test`, then `get_sympy.path_hack()` inserts `/testbed`; native child starts via `python -c` | Uploaded `/tmp` entry point, then inserts `/testbed` and `/testbed/bin` |
| Other inherited environment differences | Container hostname | Container hostname |

The inherited environment and baseline interpreter path were measured with a
separate `python -c` metadata probe. Entry-point changes, native child seed and
warning policies are established from the hashed checkout source and adapter
source. No instrumentation changed either command. The full baseline path,
exact executor argv, stream hashes and timing are in `invocation_comparison.json`.
No test outcome values were decoded for this comparison.
