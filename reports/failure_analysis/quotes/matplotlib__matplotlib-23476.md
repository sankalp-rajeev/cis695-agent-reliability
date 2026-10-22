POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# matplotlib__matplotlib-23476  group=group1_false_accept  run=main_50_b
## ISSUE
[Bug]: DPI of a figure is doubled after unpickling on M1 Mac
### Bug summary

When a figure is unpickled, it's dpi is doubled. This behaviour happens every time and if done in a loop it can cause an `OverflowError`.

### Code for reproduction

```python
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pickle
import platform

print(matplotlib.get_backend())
print('Matplotlib ver:', matplotlib.__version__)
print('Platform:', platform.platform())
print('System:', platform.system())
print('Release:', platform.release())
print('Python ver:', platform.python_version())


def dump_load_get_dpi(fig):
    with open('sinus.pickle','wb') as file:
        pickle.dump(fig, file)

    with open('sinus.pickle', 'rb') as blob:
        fig2 = pickle.load(blob)
    return fig2, fig2.dpi


def run():
    fig = plt.figure()
    x = np.linspace(0,2*np.pi)
    y = np.sin(x)

    for i in range(32):
        print(f'{i}: {fig.dpi}')
        fig, dpi = dump_load_get_dpi(fig)


if __name__ == '__main__':
    run()
```


### Actual outcome

```
MacOSX
Matplotlib ver: 3.5.2
Platform: macOS-12.4-arm64-arm-64bit
System: Darwin
Release: 21.5.0
Python ver: 3.9.12
0: 200.0
1: 400.0
2: 800.0
3: 1600.0
4: 3200.0
5: 6400.0
6: 12800.0
7: 25600.0
8: 51200.0
9: 102400.0
10: 204800.0
11: 409600.0
12: 819200.0
13: 1638400.0
14: 3276800.0
15: 6553600.0
16: 13107200.0
17: 26214400.0
18: 52428800.0
19: 104857600.0
20: 209715200.0
21: 419430400.0
Traceback (most recent call last):
  File "/Users/wsykala/projects/matplotlib/example.py", line 34, in <module>
    run()
  File "/Users/wsykala/projects/matplotlib/example.py", line 30, in run
    fig, dpi = dump_load_get_dpi(fig)
  File "/Users/wsykala/projects/matplotlib/example.py", line 20, in dump_load_get_dpi
    fig2 = pickle.load(blob)
  File "/Users/wsykala/miniconda3/envs/playground/lib/python3.9/site-packages/matplotlib/figure.py", line 2911, in __setstate__
    mgr = plt._backend_mod.new_figure_manager_given_figure(num, self)
  File "/Users/wsykala/miniconda3/envs/playground/lib/python3.9/site-packages/matplotlib/backend_bases.py", line 3499, in new_figure_manager_given_figure
    canvas = cls.FigureCanvas(figure)
  File "/Users/wsykala/miniconda3/envs/playground/lib/python3.9/site-packages/matplotlib/backends/backend_macosx.py", line 32, in __init__
    _macosx.FigureCanvas.__init__(self, width, height)
OverflowError: signed integer is greater than maximum
```

### Expected outcome

```
MacOSX
Matplotlib ver: 3.5.2
Platform: macOS-12.4-arm64-arm-64bit
System: Darwin
Release: 21.5.0
Python ver: 3.9.12
0: 200.0
1: 200.0
2: 200.0
3: 200.0
4: 200.0
5: 200.0
6: 200.0
7: 200.0
8: 200.0
9: 200.0
10: 200.0
11: 200.0
12: 200.0
13: 200.0
14: 200.0
15: 200.0
16: 200.0
17: 200.0
18: 200.0
19: 200.0
20: 200.0
21: 200.0
22: 200.0
```

### Additional information

This seems to happen only on M1 MacBooks and the version of python doesn't matter.

### Operating system

OS/X

### Matplotlib Version

3.5.2

### Matplotlib Backend

MacOSX

### Python version

3.9.12

### Jupyter version

_No response_

### Installation

pip


## AGENT PATCH
diff --git a/lib/matplotlib/backend_bases.py b/lib/matplotlib/backend_bases.py
index 9ae2982c62..409c7b0018 100755
--- a/lib/matplotlib/backend_bases.py
+++ b/lib/matplotlib/backend_bases.py
@@ -1653,7 +1653,8 @@ class FigureCanvasBase:
         self.toolbar = None  # NavigationToolbar2 will set me
         self._is_idle_drawing = False
         # We don't want to scale up the figure DPI more than once.
-        figure._original_dpi = figure.dpi
+        if getattr(figure, "_original_dpi", None) is None:
+            figure._original_dpi = figure.dpi
         self._device_pixel_ratio = 1
         super().__init__()  # Typically the GUI widget init (if any).
 
diff --git a/lib/matplotlib/figure.py b/lib/matplotlib/figure.py
index c55864243a..232e7367c7 100755
--- a/lib/matplotlib/figure.py
+++ b/lib/matplotlib/figure.py
@@ -2406,6 +2406,8 @@ class Figure(FigureBase):
         self.dpi_scale_trans = Affine2D().scale(dpi)
         # do not use property as it will trigger
         self._dpi = dpi
+        # We don't want to scale up the figure DPI more than once.
+        self._original_dpi = None
         self.bbox = TransformedBbox(self.bbox_inches, self.dpi_scale_trans)
         self.figbbox = self.bbox
         self.transFigure = BboxTransformTo(self.bbox)


## GOLD PATCH
diff --git a/lib/matplotlib/figure.py b/lib/matplotlib/figure.py
--- a/lib/matplotlib/figure.py
+++ b/lib/matplotlib/figure.py
@@ -3023,6 +3023,9 @@ def __getstate__(self):
         # Set cached renderer to None -- it can't be pickled.
         state["_cachedRenderer"] = None
 
+        # discard any changes to the dpi due to pixel ratio changes
+        state["_dpi"] = state.get('_original_dpi', state['_dpi'])
+
         # add version information to the state
         state['__mpl_version__'] = mpl.__version__
 


## GOLD TEST_PATCH
diff --git a/lib/matplotlib/tests/test_figure.py b/lib/matplotlib/tests/test_figure.py
--- a/lib/matplotlib/tests/test_figure.py
+++ b/lib/matplotlib/tests/test_figure.py
@@ -2,6 +2,7 @@
 from datetime import datetime
 import io
 from pathlib import Path
+import pickle
 import platform
 from threading import Timer
 from types import SimpleNamespace
@@ -1380,3 +1381,11 @@ def test_deepcopy():
 
     assert ax.get_xlim() == (1e-1, 1e2)
     assert fig2.axes[0].get_xlim() == (0, 1)
+
+
+def test_unpickle_with_device_pixel_ratio():
+    fig = Figure(dpi=42)
+    fig.canvas._set_device_pixel_ratio(7)
+    assert fig.dpi == 42*7
+    fig2 = pickle.loads(pickle.dumps(fig))
+    assert fig2.dpi == 42


## V4 SOURCES
### test_repro_1.py
"""Regression test: figure DPI must not double after pickling on high-DPI.

The issue reports that on an M1 Mac (device pixel ratio 2), repeatedly
pickling and unpickling a figure doubles its DPI each time.  The high-DPI
backend re-applies the device pixel ratio to the newly attached canvas; the
figure must remember the original (unscaled) DPI across pickling.
"""

import pickle

import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


def main():
    fig = Figure(figsize=(4, 3), dpi=100)
    fig.add_subplot(111)
    FigureCanvasAgg(fig)

    # Emulate a high-DPI display (for example, an Apple M1 Mac with a device
    # pixel ratio of 2).
    fig.canvas._set_device_pixel_ratio(2)
    assert fig.dpi == 200, f"initial scaled dpi is {fig.dpi}, expected 200"
    expected_dpi = fig.dpi

    for i in range(5):
        fig = pickle.loads(pickle.dumps(fig))
        # When the unpickled figure is attached to the high-DPI backend, that
        # backend applies its device pixel ratio, just as the MacOSX backend
        # does when it creates the window for the restored figure.
        fig.canvas._set_device_pixel_ratio(2)
        assert fig.dpi == expected_dpi, (
            f"after unpickling iteration {i}, dpi is {fig.dpi}; "
            f"expected it to stay {expected_dpi}")


if __name__ == "__main__":
    main()

### test_repro_2.py
"""Regression test for DPI doubling after unpickling with pyplot figures."""

import pickle

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


def main():
    fig = plt.figure(figsize=(4, 3), dpi=100)
    fig.canvas._set_device_pixel_ratio(2)
    assert fig.dpi == 200, f"initial scaled dpi is {fig.dpi}, expected 200"
    expected_dpi = fig.dpi

    for i in range(5):
        fig = pickle.loads(pickle.dumps(fig))
        # The MacOSX backend calls this when the window for the restored
        # figure is created.
        fig.canvas._set_device_pixel_ratio(2)
        assert fig.dpi == expected_dpi, (
            f"after unpickling iteration {i}, dpi is {fig.dpi}; "
            f"expected it to stay {expected_dpi}")

    plt.close("all")


if __name__ == "__main__":
    main()

### test_repro_3.py
"""Regression test for pickling a figure while a high-DPI scale is active.

This uses the same generic canvas-reattachment path that ``Figure.__setstate__``
uses during unpickling and then re-applies the device pixel ratio.
"""

import pickle

import matplotlib
matplotlib.use("Agg")

from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


def main():
    fig = Figure(figsize=(4, 3), dpi=100)
    canvas = FigureCanvasAgg(fig)
    canvas._set_device_pixel_ratio(2)
    assert fig.dpi == 200, f"initial scaled dpi is {fig.dpi}, expected 200"

    fig2 = pickle.loads(pickle.dumps(fig))
    # ``Figure.__setstate__`` uses ``FigureCanvasBase`` while restoring the
    # figure.  Verify that this did not destroy the recorded unscaled DPI.
    assert isinstance(fig2.canvas, FigureCanvasBase)
    fig2.canvas._set_device_pixel_ratio(2)
    assert fig2.dpi == 200, (
        f"dpi after unpickling and re-applying the device pixel ratio is "
        f"{fig2.dpi}; expected 200")


if __name__ == "__main__":
    main()

