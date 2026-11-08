# Fix 13 diagnosis: seven Astropy modules

Pristine frozen image `sha256:ba3d2b723b6698da914da64befdbf7a075799e65a970a56355b8f1ef1543c835`, base commit `5250b2442501e6c671c6b380536f1edb352602d1`. AST/source reads from the frozen base archive and pip/package-import checks only: no patch, collection or test bodies. [Package receipts](package_checks.json). No attempt-2 outcome/verdict file or labels were read.

| Module | Skip/importorskip location | Statement | Package check |
|---|---|---|---|
| astropy/io/misc/asdf/tags/unit/tests/test_quantity.py | astropy/io/misc/asdf/tags/unit/tests/test_quantity.py:5 (module level) | `pytest.importorskip("asdf")` | asdf absent; pip show and import both exit 1 |
| astropy/io/misc/asdf/tags/coordinates/tests/test_earthlocation.py | astropy/io/misc/asdf/tags/coordinates/tests/test_earthlocation.py:5 (module level) | `pytest.importorskip("asdf")` | asdf absent; pip show and import both exit 1 |
| astropy/io/misc/asdf/tags/coordinates/tests/test_skycoord.py | astropy/io/misc/asdf/tags/coordinates/tests/test_skycoord.py:9 (module level) | `pytest.importorskip("asdf")` | asdf absent; pip show and import both exit 1 |
| astropy/io/misc/asdf/tags/table/tests/test_table.py | astropy/io/misc/asdf/tags/table/tests/test_table.py:5 (module level) | `pytest.importorskip("asdf")` | asdf absent; pip show and import both exit 1 |
| astropy/io/misc/tests/test_parquet.py | astropy/io/misc/tests/test_parquet.py:28 (module level) | `pytest.importorskip("pyarrow")` | pyarrow absent; pip show and import both exit 1 |
| astropy/visualization/wcsaxes/tests/test_formatter_locator.py | astropy/visualization/wcsaxes/__init__.py:9 (parent package initialization) | `pytest.importorskip("matplotlib")` | matplotlib absent; pip show and import both exit 1 |
| astropy/visualization/wcsaxes/tests/test_wcsapi.py | astropy/visualization/wcsaxes/__init__.py:9 (parent package initialization) | `pytest.importorskip("matplotlib")` | matplotlib absent; pip show and import both exit 1 |

The WCSAxes test files have no local skip statement: importing their parent package executes its module-level importorskip before the test module is loaded. These are source-backed skip candidates; the executor will admit a module skip only when native collection records it with a reason. A missing dependency or static importorskip alone is not sufficient.
