POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# django__django-16667  group=group1_false_accept  run=main_50_a
## ISSUE
SelectDateWidget can crash with OverflowError.
Description
	
Given a relatively common view like this:
from django import forms
from django.forms import SelectDateWidget
from django.http import HttpResponse
class ReproForm(forms.Form):
	 my_date = forms.DateField(widget=SelectDateWidget())
def repro_view(request):
	 form = ReproForm(request.GET) # for ease of reproducibility
	 if form.is_valid():
		 return HttpResponse("ok")
	 else:
		 return HttpResponse("not ok")
# urls.py
urlpatterns = [path('repro/', views.repro_view, name='repro')]
A user can trigger a server crash, reproducible by running locally and visiting ​http://127.0.0.1:8000/repro/?my_date_day=1&my_date_month=1&my_date_year=1234567821345678, which results in
[...] - ERROR - django.request: Internal Server Error: /repro/
Traceback (most recent call last):
[...]
 File "[...]/site-packages/django/forms/widgets.py", line 1160, in value_from_datadict
	date_value = datetime.date(int(y), int(m), int(d))
OverflowError: signed integer is greater than maximum
This can be triggered similarly for a post request.
The issue happens as part of the validation logic run in form.is_valid, specifically, when calling the SelectDateWidget.value_from_datadict, where the user-controlled value is converted into a date without guarding against a possible OverflowError.
Specifically, y, m and d are user controlled, and the code does this:
 date_value = datetime.date(int(y), int(m), int(d)) 
When large integers (larger than sys.maxsize) are supplied to date's constructor it will throw an OverflowError:
>>> import datetime, sys
>>> datetime.date(sys.maxsize+1, 3, 4)
Traceback (most recent call last):
 File "<stdin>", line 1, in <module>
OverflowError: Python int too large to convert to C long


## AGENT PATCH
diff --git a/django/forms/widgets.py b/django/forms/widgets.py
index 842b73e95c..f4bc74b7cd 100644
--- a/django/forms/widgets.py
+++ b/django/forms/widgets.py
@@ -1157,7 +1157,7 @@ class SelectDateWidget(Widget):
             input_format = formats.sanitize_strftime_format(input_format)
             try:
                 date_value = datetime.date(int(y), int(m), int(d))
-            except ValueError:
+            except (ValueError, OverflowError):
                 # Return pseudo-ISO dates with zeros for any unselected values,
                 # e.g. '2017-0-23'.
                 return "%s-%s-%s" % (y or 0, m or 0, d or 0)


## GOLD PATCH
diff --git a/django/forms/widgets.py b/django/forms/widgets.py
--- a/django/forms/widgets.py
+++ b/django/forms/widgets.py
@@ -1161,6 +1161,8 @@ def value_from_datadict(self, data, files, name):
                 # Return pseudo-ISO dates with zeros for any unselected values,
                 # e.g. '2017-0-23'.
                 return "%s-%s-%s" % (y or 0, m or 0, d or 0)
+            except OverflowError:
+                return "0-0-0"
             return date_value.strftime(input_format)
         return data.get(name)
 


## GOLD TEST_PATCH
diff --git a/tests/forms_tests/field_tests/test_datefield.py b/tests/forms_tests/field_tests/test_datefield.py
--- a/tests/forms_tests/field_tests/test_datefield.py
+++ b/tests/forms_tests/field_tests/test_datefield.py
@@ -1,3 +1,4 @@
+import sys
 from datetime import date, datetime
 
 from django.core.exceptions import ValidationError
@@ -36,6 +37,17 @@ def test_form_field(self):
         d = GetDate({"mydate_month": "1", "mydate_day": "1", "mydate_year": "2010"})
         self.assertIn('<label for="id_mydate_month">', d.as_p())
 
+        # Inputs raising an OverflowError.
+        e = GetDate(
+            {
+                "mydate_month": str(sys.maxsize + 1),
+                "mydate_day": "31",
+                "mydate_year": "2010",
+            }
+        )
+        self.assertIs(e.is_valid(), False)
+        self.assertEqual(e.errors, {"mydate": ["Enter a valid date."]})
+
     @translation.override("nl")
     def test_l10n_date_changed(self):
         """
@@ -149,6 +161,8 @@ def test_datefield_1(self):
             f.clean("200a-10-25")
         with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
             f.clean("25/10/06")
+        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
+            f.clean("0-0-0")
         with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
             f.clean(None)
 
diff --git a/tests/forms_tests/widget_tests/test_selectdatewidget.py b/tests/forms_tests/widget_tests/test_selectdatewidget.py
--- a/tests/forms_tests/widget_tests/test_selectdatewidget.py
+++ b/tests/forms_tests/widget_tests/test_selectdatewidget.py
@@ -1,3 +1,4 @@
+import sys
 from datetime import date
 
 from django.forms import DateField, Form, SelectDateWidget
@@ -610,6 +611,7 @@ def test_value_from_datadict(self):
             ((None, "12", "1"), None),
             (("2000", None, "1"), None),
             (("2000", "12", None), None),
+            ((str(sys.maxsize + 1), "12", "1"), "0-0-0"),
         ]
         for values, expected in tests:
             with self.subTest(values=values):


## V4 SOURCES
### test_repro_1.py
"""SelectDateWidget must not crash (OverflowError) on huge user-supplied
year/month/day integers; the form should simply be invalid."""
import datetime
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        USE_I18N=False,
        USE_TZ=False,
        INSTALLED_APPS=[],
        DATABASES={},
    )
django.setup()

from django import forms
from django.forms import SelectDateWidget


class ReproForm(forms.Form):
    my_date = forms.DateField(widget=SelectDateWidget())


def is_valid_without_crash(form):
    """Return form.is_valid() but turn any OverflowError into an AssertionError.

    On the buggy code the user-controlled integer overflows datetime.date,
    which must not propagate out of validation.
    """
    try:
        return form.is_valid()
    except OverflowError as exc:
        raise AssertionError(
            "SelectDateWidget.value_from_datadict leaked OverflowError: %r" % (exc,)
        )


# The exact reproducer from the issue (GET-style data).
data = {
    "my_date_day": "1",
    "my_date_month": "1",
    "my_date_year": "1234567821345678",
}
form = ReproForm(data)
assert is_valid_without_crash(form) is False, (
    "A date with an out-of-range year must make the form invalid, not valid."
)

# A normal, in-range date must still validate successfully.
good = {
    "my_date_day": "1",
    "my_date_month": "1",
    "my_date_year": "2020",
}
form_good = ReproForm(good)
assert is_valid_without_crash(form_good) is True, "A normal date must be valid."
assert form_good.cleaned_data["my_date"] == datetime.date(2020, 1, 1)

print("test_repro_1 passed")

### test_repro_2.py
"""POST-style submission with an oversized year must not crash validation."""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        USE_I18N=False,
        USE_TZ=False,
        INSTALLED_APPS=[],
        DATABASES={},
    )
django.setup()

from django import forms
from django.forms import SelectDateWidget


class ReproForm(forms.Form):
    my_date = forms.DateField(widget=SelectDateWidget())


def is_valid_without_crash(form):
    try:
        return form.is_valid()
    except OverflowError as exc:
        raise AssertionError(
            "OverflowError escaped form validation: %r" % (exc,)
        )


# POST data (dict) with a huge year, as described in the issue.
post_data = {
    "my_date_day": "1",
    "my_date_month": "1",
    "my_date_year": "1234567821345678",
}
form = ReproForm(post_data)
invalid = not is_valid_without_crash(form)
assert invalid, "An out-of-range year must yield an invalid form."

# The form must record a real validation error rather than blow up.
assert form.errors, "Expected a validation error for the out-of-range year."
assert "my_date" in form.errors, "The error must be attached to the my_date field."

print("test_repro_2 passed")

### test_repro_3.py
"""Boundary tests: integers just beyond the C long range must not crash
SelectDateWidget, for year, month and day positions alike."""
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        USE_I18N=False,
        USE_TZ=False,
        INSTALLED_APPS=[],
        DATABASES={},
    )
django.setup()

from django import forms
from django.forms import SelectDateWidget


class ReproForm(forms.Form):
    my_date = forms.DateField(widget=SelectDateWidget())


def is_valid_without_crash(form):
    try:
        return form.is_valid()
    except OverflowError as exc:
        raise AssertionError(
            "OverflowError escaped form validation: %r" % (exc,)
        )


huge = str(sys.maxsize + 1)
huge_negative = str(-(sys.maxsize + 1))

cases = [
    {"my_date_day": "1", "my_date_month": "1", "my_date_year": huge},
    {"my_date_day": "1", "my_date_month": huge, "my_date_year": "2020"},
    {"my_date_day": huge, "my_date_month": "1", "my_date_year": "2020"},
    {"my_date_day": "1", "my_date_month": "1", "my_date_year": huge_negative},
]

for case in cases:
    form = ReproForm(case)
    assert is_valid_without_crash(form) is False, (
        "Out-of-range component %r must make the form invalid." % (case,)
    )

print("test_repro_3 passed")

