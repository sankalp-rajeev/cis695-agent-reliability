POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# matplotlib__matplotlib-23299  group=group1_false_accept  run=main_50_b
## ISSUE
[Bug]: get_backend() clears figures from Gcf.figs if they were created under rc_context
### Bug summary

calling `matplotlib.get_backend()` removes all figures from `Gcf` if the *first* figure in `Gcf.figs` was created in an `rc_context`.

### Code for reproduction

```python
import matplotlib.pyplot as plt
from matplotlib import get_backend, rc_context

# fig1 = plt.figure()  # <- UNCOMMENT THIS LINE AND IT WILL WORK
# plt.ion()            # <- ALTERNATIVELY, UNCOMMENT THIS LINE AND IT WILL ALSO WORK
with rc_context():
    fig2 = plt.figure()
before = f'{id(plt._pylab_helpers.Gcf)} {plt._pylab_helpers.Gcf.figs!r}'
get_backend()
after = f'{id(plt._pylab_helpers.Gcf)} {plt._pylab_helpers.Gcf.figs!r}'

assert before == after, '\n' + before + '\n' + after
```


### Actual outcome

```
---------------------------------------------------------------------------
AssertionError                            Traceback (most recent call last)
<ipython-input-1-fa4d099aa289> in <cell line: 11>()
      9 after = f'{id(plt._pylab_helpers.Gcf)} {plt._pylab_helpers.Gcf.figs!r}'
     10 
---> 11 assert before == after, '\n' + before + '\n' + after
     12 

AssertionError: 
94453354309744 OrderedDict([(1, <matplotlib.backends.backend_qt.FigureManagerQT object at 0x7fb33e26c220>)])
94453354309744 OrderedDict()
```

### Expected outcome

The figure should not be missing from `Gcf`.  Consequences of this are, e.g, `plt.close(fig2)` doesn't work because `Gcf.destroy_fig()` can't find it.

### Additional information

_No response_

### Operating system

Xubuntu

### Matplotlib Version

3.5.2

### Matplotlib Backend

QtAgg

### Python version

Python 3.10.4

### Jupyter version

n/a

### Installation

conda


## AGENT PATCH
diff --git a/lib/matplotlib/pyplot.py b/lib/matplotlib/pyplot.py
index e3c66ea67c..664d7a713f 100755
--- a/lib/matplotlib/pyplot.py
+++ b/lib/matplotlib/pyplot.py
@@ -222,6 +222,21 @@ def switch_backend(newbackend):
     global _backend_mod
     # make sure the init is pulled up so we can assign to it later
     import matplotlib.backends
+
+    if newbackend is rcsetup._auto_backend_sentinel and _backend_mod is not None:
+        # The backend has already been resolved (e.g. the auto sentinel was
+        # restored by `rc_context`); don't re-resolve it, as that would close
+        # all existing figures.  Just make sure rcParams is back in sync with
+        # the actual backend.
+        rcParams['backend'] = matplotlib.backends.backend
+        return
+
+    if getattr(matplotlib.backends, "backend", None) == newbackend:
+        # Switching to the backend that is already active; don't close all the
+        # figures.
+        rcParams['backend'] = newbackend
+        return
+
     close("all")
 
     if newbackend is rcsetup._auto_backend_sentinel:


## GOLD PATCH
diff --git a/lib/matplotlib/__init__.py b/lib/matplotlib/__init__.py
--- a/lib/matplotlib/__init__.py
+++ b/lib/matplotlib/__init__.py
@@ -1059,6 +1059,8 @@ def rc_context(rc=None, fname=None):
     """
     Return a context manager for temporarily changing rcParams.
 
+    The :rc:`backend` will not be reset by the context manager.
+
     Parameters
     ----------
     rc : dict
@@ -1087,7 +1089,8 @@ def rc_context(rc=None, fname=None):
              plt.plot(x, y)  # uses 'print.rc'
 
     """
-    orig = rcParams.copy()
+    orig = dict(rcParams.copy())
+    del orig['backend']
     try:
         if fname:
             rc_file(fname)


## GOLD TEST_PATCH
diff --git a/lib/matplotlib/tests/test_rcparams.py b/lib/matplotlib/tests/test_rcparams.py
--- a/lib/matplotlib/tests/test_rcparams.py
+++ b/lib/matplotlib/tests/test_rcparams.py
@@ -496,6 +496,13 @@ def test_keymaps():
         assert isinstance(mpl.rcParams[k], list)
 
 
+def test_no_backend_reset_rccontext():
+    assert mpl.rcParams['backend'] != 'module://aardvark'
+    with mpl.rc_context():
+        mpl.rcParams['backend'] = 'module://aardvark'
+    assert mpl.rcParams['backend'] == 'module://aardvark'
+
+
 def test_rcparams_reset_after_fail():
     # There was previously a bug that meant that if rc_context failed and
     # raised an exception due to issues in the supplied rc parameters, the


## V4 SOURCES
### test_repro_1.py
"""get_backend() must not clear figures created inside rc_context.

This is the direct reproduction from the bug report: make the first pyplot
figure inside an rc_context that starts while the backend is still the
unresolved "auto" sentinel, then call get_backend().
"""

import os

# Make this independent of any MPLBACKEND supplied by the calling environment:
# the bug only occurs when the backend is still unresolved.
os.environ.pop("MPLBACKEND", None)

import matplotlib
from matplotlib import _pylab_helpers, rcsetup

# Ensure the global backend is in the state where it still needs to be
# auto-resolved, regardless of any matplotlibrc/user configuration.
dict.__setitem__(
    matplotlib.rcParams, "backend", rcsetup._auto_backend_sentinel)

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import get_backend, rc_context  # noqa: E402


with rc_context():
    fig = plt.figure()

Gcf = _pylab_helpers.Gcf
before_keys = list(Gcf.figs)
assert fig.number in before_keys, (
    "precondition failed: the figure created in rc_context was not registered")
before_active = Gcf.get_active()

try:
    get_backend()
except Exception as exc:  # pragma: no cover - would be an unexpected failure
    raise AssertionError(f"get_backend() raised {exc!r}") from exc

after_keys = list(Gcf.figs)
assert fig.number in after_keys, (
    "get_backend() removed a figure created inside rc_context from "
    f"Gcf.figs: before={before_keys}, after={after_keys}")
assert Gcf.get_active() is before_active, (
    "get_backend() changed the active pyplot figure manager")

### test_repro_2.py
"""A figure created in rc_context must still be closeable after get_backend().

This reproduces the user-visible consequence noted in the report:
get_backend() must not make pyplot forget the figure, otherwise plt.close(fig)
cannot find it.
"""

import os

os.environ.pop("MPLBACKEND", None)

import matplotlib
from matplotlib import rcsetup

dict.__setitem__(
    matplotlib.rcParams, "backend", rcsetup._auto_backend_sentinel)

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import get_backend, rc_context  # noqa: E402


with rc_context({"figure.dpi": 100}):
    fig = plt.figure()

assert plt.fignum_exists(fig.number), "figure was not registered by pyplot"

get_backend()

# The figure must still be known to pyplot at this point.
assert plt.fignum_exists(fig.number), (
    "after get_backend(), plt.fignum_exists() says the figure created in "
    "rc_context is gone")

# ...and therefore close(fig) must actually remove it.
plt.close(fig)
assert not plt.fignum_exists(fig.number), (
    "plt.close(fig) did not close the figure created in rc_context")

### test_repro_3.py
"""The active figure must survive get_backend() when created in rc_context.

Nested rc_context blocks are used to make sure the restoration logic at each
level leaves the resolved backend in a coherent state.
"""

import os

os.environ.pop("MPLBACKEND", None)

import matplotlib
from matplotlib import rcsetup

dict.__setitem__(
    matplotlib.rcParams, "backend", rcsetup._auto_backend_sentinel)

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import get_backend, rc_context  # noqa: E402


with rc_context():
    with rc_context({"figure.dpi": 72}):
        fig = plt.figure()

assert plt.gcf() is fig, (
    "precondition failed: the figure created in rc_context is not current")

try:
    get_backend()
except Exception as exc:  # pragma: no cover - unexpected failure mode
    raise AssertionError(f"get_backend() raised {exc!r}") from exc

assert plt.gcf() is fig, (
    "get_backend() caused pyplot to forget the current figure created in "
    "rc_context")

# Calling it again must be equally harmless.
get_backend()
assert plt.gcf() is fig, (
    "repeated get_backend() calls lost the figure created in rc_context")

