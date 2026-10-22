POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# django__django-12209  group=group4_right_old_tests_fail  run=main_50_b
## ISSUE
Change in behaviour when saving a model instance with an explcit pk value if the pk field has a default
Description
	 
		(last modified by Reupen Shah)
	 
Consider the following model:
from uuid import uuid4
from django.db import models
class Sample(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid4)
	name = models.CharField(blank=True, max_length=100)
In Django 2.2 and earlier, the following commands would result in an INSERT followed by an UPDATE:
s0 = Sample.objects.create()
s1 = Sample(pk=s0.pk, name='Test 1')
s1.save()
However, in Django 3.0, this results in two INSERTs (naturally the second one fails). The behaviour also changes if default=uuid4 is removed from the id field.
This seems related to https://code.djangoproject.com/ticket/29260.
The change in behaviour also has the side effect of changing the behaviour of the loaddata management command when the fixture contains explicit pk values and the objects already exist (e.g. when loading the fixture multiple times).
Perhaps the intention was to only change the behaviour if an explicit pk value was not set on the model instance being saved? (At least, that would be more backwards-compatible behaviour...)


## AGENT PATCH
diff --git a/django/db/models/base.py b/django/db/models/base.py
index e3b14a41a0..094f82050e 100644
--- a/django/db/models/base.py
+++ b/django/db/models/base.py
@@ -16,7 +16,7 @@ from django.db import (
     connections, router, transaction,
 )
 from django.db.models import (
-    NOT_PROVIDED, ExpressionWrapper, IntegerField, Max, Value,
+    ExpressionWrapper, IntegerField, Max, Value,
 )
 from django.db.models.constants import LOOKUP_SEP
 from django.db.models.constraints import CheckConstraint, UniqueConstraint
@@ -847,14 +847,6 @@ class Model(metaclass=ModelBase):
         if not pk_set and (force_update or update_fields):
             raise ValueError("Cannot force an update in save() with no primary key.")
         updated = False
-        # Skip an UPDATE when adding an instance and primary key has a default.
-        if (
-            not force_insert and
-            self._state.adding and
-            self._meta.pk.default and
-            self._meta.pk.default is not NOT_PROVIDED
-        ):
-            force_insert = True
         # If possible, try an UPDATE. If that doesn't update anything, do an INSERT.
         if pk_set and not force_insert:
             base_qs = cls._base_manager.using(using)


## GOLD PATCH
diff --git a/django/db/models/base.py b/django/db/models/base.py
--- a/django/db/models/base.py
+++ b/django/db/models/base.py
@@ -849,6 +849,7 @@ def _save_table(self, raw=False, cls=None, force_insert=False,
         updated = False
         # Skip an UPDATE when adding an instance and primary key has a default.
         if (
+            not raw and
             not force_insert and
             self._state.adding and
             self._meta.pk.default and


## GOLD TEST_PATCH
diff --git a/tests/serializers/models/data.py b/tests/serializers/models/data.py
--- a/tests/serializers/models/data.py
+++ b/tests/serializers/models/data.py
@@ -4,6 +4,8 @@
 NULL values, where allowed.
 The basic idea is to have a model for each Django data type.
 """
+import uuid
+
 from django.contrib.contenttypes.fields import (
     GenericForeignKey, GenericRelation,
 )
@@ -257,6 +259,10 @@ class UUIDData(models.Model):
     data = models.UUIDField(primary_key=True)
 
 
+class UUIDDefaultData(models.Model):
+    data = models.UUIDField(primary_key=True, default=uuid.uuid4)
+
+
 class FKToUUID(models.Model):
     data = models.ForeignKey(UUIDData, models.CASCADE)
 
diff --git a/tests/serializers/test_data.py b/tests/serializers/test_data.py
--- a/tests/serializers/test_data.py
+++ b/tests/serializers/test_data.py
@@ -26,7 +26,7 @@
     ModifyingSaveData, NullBooleanData, O2OData, PositiveBigIntegerData,
     PositiveIntegerData, PositiveIntegerPKData, PositiveSmallIntegerData,
     PositiveSmallIntegerPKData, SlugData, SlugPKData, SmallData, SmallPKData,
-    Tag, TextData, TimeData, UniqueAnchor, UUIDData,
+    Tag, TextData, TimeData, UniqueAnchor, UUIDData, UUIDDefaultData,
 )
 from .tests import register_tests
 
@@ -351,6 +351,7 @@ def inherited_compare(testcase, pk, klass, data):
     # (pk_obj, 790, XMLPKData, "<foo></foo>"),
     (pk_obj, 791, UUIDData, uuid_obj),
     (fk_obj, 792, FKToUUID, uuid_obj),
+    (pk_obj, 793, UUIDDefaultData, uuid_obj),
 
     (data_obj, 800, AutoNowDateTimeData, datetime.datetime(2006, 6, 16, 10, 42, 37)),
     (data_obj, 810, ModifyingSaveData, 42),


## V4 SOURCES
### test_repro_1.py
"""
Regression test for ticket #31493.

Saving a model instance that has an explicit primary key value must not be
forced into an INSERT when the primary key field also has a default.  The
correct (Django <= 2.2) behaviour is to try an UPDATE first and only INSERT
when no matching row exists.

This script fails with AssertionError on the buggy code (the second save
raises IntegrityError because a duplicate INSERT is attempted) and exits 0
once the behaviour is fixed.
"""
import uuid

from django.conf import settings

settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        },
    },
    INSTALLED_APPS=[],
    USE_TZ=True,
)

import django

django.setup()

from django.db import connection, models
from django.db.utils import IntegrityError


class Sample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(blank=True, max_length=100)

    class Meta:
        app_label = 'repro'


with connection.schema_editor() as schema_editor:
    schema_editor.create_model(Sample)

s0 = Sample.objects.create(name='Original')
assert Sample.objects.count() == 1, 'setup failed: expected exactly one row'

# Reuse the existing primary key explicitly.  This must UPDATE the row.
s1 = Sample(pk=s0.pk, name='Test 1')
try:
    s1.save()
except IntegrityError as exc:
    raise AssertionError(
        'Saving a model instance with an explicit, already existing primary '
        'key raised IntegrityError (a duplicate INSERT was attempted) instead '
        'of updating the existing row: %r' % (exc,)
    )

assert Sample.objects.count() == 1, (
    'Saving with an explicit existing primary key inserted a duplicate row'
)
assert Sample.objects.get(pk=s0.pk).name == 'Test 1', (
    'The existing row was not updated with the new value'
)

print('OK: explicit primary key with a default updated the existing row')

### test_repro_2.py
"""
Regression test for ticket #31493 (loaddata side effect).

The ``loaddata`` management command deserializes fixture objects and saves
them with ``save_base(raw=True)``.  When a fixture contains an explicit
primary key for an object that already exists, the existing row must be
updated rather than a duplicate INSERT being attempted.

This script mimics that code path with Django's serializer deserializer (no
files are read).  It fails with AssertionError on the buggy code and exits 0
once the behaviour is fixed.
"""
import uuid

from django.conf import settings

settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        },
    },
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True,
)

import django

django.setup()

from django.core import serializers
from django.db import connection, models
from django.db.utils import IntegrityError


class Sample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(blank=True, max_length=100)

    class Meta:
        app_label = 'contenttypes'


with connection.schema_editor() as schema_editor:
    schema_editor.create_model(Sample)

s0 = Sample.objects.create(name='Original')
assert Sample.objects.count() == 1

# A fixture that reuses an already existing primary key, as loaddata would
# be given when loading the same fixture a second time.
fixture = (
    '[{"model": "%s.%s", "pk": "%s", "fields": {"name": "Test 1"}}]'
    % (Sample._meta.app_label, Sample._meta.model_name, s0.pk)
)

try:
    for deserialized_obj in serializers.deserialize('json', fixture):
        deserialized_obj.save()
except IntegrityError as exc:
    raise AssertionError(
        'Deserializing (as loaddata does) an object with an explicit, already '
        'existing primary key raised IntegrityError instead of updating the '
        'existing row: %r' % (exc,)
    )

assert Sample.objects.count() == 1, (
    'Loading a fixture with an explicit existing primary key inserted a '
    'duplicate row'
)
assert Sample.objects.get(pk=s0.pk).name == 'Test 1', (
    'The existing row was not updated while loading the fixture'
)

print('OK: deserializing an object with an explicit primary key updated the existing row')

### test_repro_3.py
"""
Regression test for ticket #31493 (update vs insert decision).

When a primary key field has a default:
  * a brand new object whose primary key was generated from the default must
    still be INSERTed (the optimisation from #29260), and
  * a new object that carries an explicit primary key value must take the
    normal UPDATE-then-INSERT path, including when ``update_fields`` is used.

This script fails with AssertionError on the buggy code (an explicit, already
existing primary key is force-inserted) and exits 0 once fixed.
"""
import uuid

from django.conf import settings

settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        },
    },
    INSTALLED_APPS=[],
    USE_TZ=True,
)

import django

django.setup()

from django.db import connection, models
from django.db.utils import IntegrityError


class Sample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(blank=True, max_length=100)

    class Meta:
        app_label = 'repro'


with connection.schema_editor() as schema_editor:
    schema_editor.create_model(Sample)

pk = uuid.uuid4()

# An explicit primary key that does not exist yet must be inserted.
Sample(pk=pk, name='First').save()
assert Sample.objects.count() == 1

# A different instance carrying the same explicit primary key must update the
# existing row, even when only some fields are saved.
try:
    Sample(pk=pk, name='Second').save(update_fields=['name'])
except IntegrityError as exc:
    raise AssertionError(
        'Saving a new instance with an explicit, existing primary key and '
        'update_fields raised IntegrityError instead of updating the row: %r'
        % (exc,)
    )

assert Sample.objects.count() == 1, (
    'Saving with an explicit existing primary key inserted a duplicate row'
)
assert Sample.objects.get(pk=pk).name == 'Second', (
    'The existing row was not updated'
)

# A full save of yet another instance with the same explicit primary key must
# also update the existing row.
Sample(pk=pk, name='Third').save()
assert Sample.objects.count() == 1
assert Sample.objects.get(pk=pk).name == 'Third'

# An object relying on the primary key default must still be inserted.
Sample(name='Auto').save()
assert Sample.objects.count() == 2
assert Sample.objects.filter(name='Auto').exists()

print('OK: explicit primary key save performed an UPDATE')

