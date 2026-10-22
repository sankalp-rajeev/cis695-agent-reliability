POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# django__django-13297  group=group1_false_accept  run=main_50_b
## ISSUE
TemplateView.get_context_data()'s kwargs returns SimpleLazyObjects that causes a crash when filtering.
Description
	
Example Code that works in 3.0, but not in 3.1:
class OfferView(TemplateView):
	template_name = "offers/offer.html"
	def get_context_data(self, **kwargs):
		offer_slug = kwargs.get("offer_slug", "")
		offer = get_object_or_404(Account, slug=offer_slug)
		return {"offer": offer, "offer_slug": offer_slug}
In order to make this work in 3.1, you have to explicitly convert the result of kwargs.get() to a string to get the SimpleLazyObject to resolve:
class OfferView(TemplateView):
	template_name = "offers/offer.html"
	def get_context_data(self, **kwargs):
		offer_slug = kwargs.get("offer_slug", "")
		offer = get_object_or_404(Account, slug=str(offer_slug))
		return {"offer": offer, "offer_slug": offer_slug}
The error generated if you don't is:
Error binding parameter 0 - probably unsupported type
from django/db/backends/sqlite3/operations.py, line 144, in _quote_params_for_last_executed_query
In both cases, the urls.py looks like:
path(
		"/offers/<slug:offer_slug>/",
		OfferView.as_view(),
		name="offer_view",
	),
When debugging, I found that offer_slug (coming in from kwargs.get) was of type 'SimpleLazyObject' in Django 3.1, and when I explicitly converted it to a string, get_object_or_404 behaved as expected.
This is using Python 3.7.8 with SQLite.


## AGENT PATCH
diff --git a/django/views/generic/base.py b/django/views/generic/base.py
index ea5baca08d..2462b46672 100644
--- a/django/views/generic/base.py
+++ b/django/views/generic/base.py
@@ -157,17 +157,19 @@ class TemplateResponseMixin:
 class TemplateView(TemplateResponseMixin, ContextMixin, View):
     """Render a template."""
     def get(self, request, *args, **kwargs):
-        # RemovedInDjango40Warning: when the deprecation ends, replace with:
-        #   context = self.get_context_data()
-        context_kwargs = _wrap_url_kwargs_with_deprecation_warning(kwargs)
-        context = self.get_context_data(**context_kwargs)
+        context = self.get_context_data(**kwargs)
+        # RemovedInDjango40Warning: when the deprecation ends, remove the
+        # _wrap_url_kwargs_with_deprecation_warning() call.
+        context = _wrap_url_kwargs_with_deprecation_warning(kwargs, context)
         return self.render_to_response(context)
 
 
 # RemovedInDjango40Warning
-def _wrap_url_kwargs_with_deprecation_warning(url_kwargs):
-    context_kwargs = {}
+def _wrap_url_kwargs_with_deprecation_warning(url_kwargs, context):
     for key, value in url_kwargs.items():
+        # Don't override values set by a subclass in get_context_data().
+        if context.get(key, value) is not value:
+            continue
         # Bind into function closure.
         @SimpleLazyObject
         def access_value(key=key, value=value):
@@ -178,8 +180,8 @@ def _wrap_url_kwargs_with_deprecation_warning(url_kwargs):
                 RemovedInDjango40Warning, stacklevel=2,
             )
             return value
-        context_kwargs[key] = access_value
-    return context_kwargs
+        context[key] = access_value
+    return context
 
 
 class RedirectView(View):


## GOLD PATCH
diff --git a/django/views/generic/base.py b/django/views/generic/base.py
--- a/django/views/generic/base.py
+++ b/django/views/generic/base.py
@@ -11,7 +11,7 @@
 from django.urls import reverse
 from django.utils.decorators import classonlymethod
 from django.utils.deprecation import RemovedInDjango40Warning
-from django.utils.functional import SimpleLazyObject
+from django.utils.functional import lazy
 
 logger = logging.getLogger('django.request')
 
@@ -169,7 +169,6 @@ def _wrap_url_kwargs_with_deprecation_warning(url_kwargs):
     context_kwargs = {}
     for key, value in url_kwargs.items():
         # Bind into function closure.
-        @SimpleLazyObject
         def access_value(key=key, value=value):
             warnings.warn(
                 'TemplateView passing URL kwargs to the context is '
@@ -178,7 +177,7 @@ def access_value(key=key, value=value):
                 RemovedInDjango40Warning, stacklevel=2,
             )
             return value
-        context_kwargs[key] = access_value
+        context_kwargs[key] = lazy(access_value, type(value))()
     return context_kwargs
 
 


## GOLD TEST_PATCH
diff --git a/tests/generic_views/test_base.py b/tests/generic_views/test_base.py
--- a/tests/generic_views/test_base.py
+++ b/tests/generic_views/test_base.py
@@ -3,7 +3,8 @@
 from django.core.exceptions import ImproperlyConfigured
 from django.http import HttpResponse
 from django.test import (
-    RequestFactory, SimpleTestCase, ignore_warnings, override_settings,
+    RequestFactory, SimpleTestCase, TestCase, ignore_warnings,
+    override_settings,
 )
 from django.test.utils import require_jinja2
 from django.urls import resolve
@@ -11,6 +12,7 @@
 from django.views.generic import RedirectView, TemplateView, View
 
 from . import views
+from .models import Artist
 
 
 class SimpleView(View):
@@ -571,7 +573,9 @@ def test_template_mixin_without_template(self):
 
 
 @override_settings(ROOT_URLCONF='generic_views.urls')
-class DeprecationTests(SimpleTestCase):
+class DeprecationTests(TestCase):
+    rf = RequestFactory()
+
     @ignore_warnings(category=RemovedInDjango40Warning)
     def test_template_params(self):
         """A generic template view passes kwargs as context."""
@@ -603,3 +607,17 @@ def test_template_params_warning(self):
             str(response.context['foo2'])
         self.assertEqual(response.context['key'], 'value')
         self.assertIsInstance(response.context['view'], View)
+
+    @ignore_warnings(category=RemovedInDjango40Warning)
+    def test_template_params_filtering(self):
+        class ArtistView(TemplateView):
+            template_name = 'generic_views/about.html'
+
+            def get_context_data(self, *, artist_name, **kwargs):
+                context = super().get_context_data(**kwargs)
+                artist = Artist.objects.get(name=artist_name)
+                return {**context, 'artist': artist}
+
+        artist = Artist.objects.create(name='Rene Magritte')
+        response = ArtistView.as_view()(self.rf.get('/'), artist_name=artist.name)
+        self.assertEqual(response.context_data['artist'], artist)


## V4 SOURCES
### test_repro_1.py
"""Reproduction: TemplateView URL kwargs must be usable directly in the ORM.

On Django 3.1, ``TemplateView.get()`` wraps URL kwargs in ``SimpleLazyObject``
objects (to emit a deprecation warning when they are read from the context).
Such a wrapper reaches ``get_context_data(**kwargs)`` and crashes when it is
passed as a query parameter because sqlite cannot bind it:

    django.db.utils.InterfaceError: Error binding parameter 0 -
    probably unsupported type.

The correct behaviour is that the URL kwargs received by ``get_context_data``
are plain values that can be used directly (without an explicit ``str()``) in
ORM lookups.  This script asserts that behaviour.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="repro",
    ALLOWED_HOSTS=["*"],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=True,
)
django.setup()

from django.db import connection, models
from django.http import HttpResponse
from django.test import RequestFactory
from django.views.generic import TemplateView


class Account(models.Model):
    slug = models.SlugField()

    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as schema_editor:
    schema_editor.create_model(Account)

Account.objects.create(slug="my-offer")


class OfferView(TemplateView):
    template_name = "offers/offer.html"

    def get_context_data(self, **kwargs):
        offer_slug = kwargs.get("offer_slug", "")
        # Must work without the explicit ``str(offer_slug)`` workaround.
        offer = Account.objects.get(slug=offer_slug)
        return {"offer": offer, "offer_slug": offer_slug}

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(context["offer"].slug)


request = RequestFactory().get("/offers/my-offer/")
try:
    response = OfferView.as_view()(request, offer_slug="my-offer")
except Exception as exc:
    raise AssertionError(
        "Using a TemplateView URL kwarg in an ORM lookup raised %s: %s"
        % (type(exc).__name__, exc)
    )

assert response.status_code == 200, response.status_code
assert response.content == b"my-offer", response.content
print("OK")

### test_repro_2.py
"""Reproduction through the full URL resolver and test client.

Exactly like the issue report: a URL pattern ``<slug:offer_slug>`` routes to a
``TemplateView`` whose ``get_context_data`` uses ``kwargs.get("offer_slug")``
directly as an ORM lookup argument.  On Django 3.1 the kwarg is a
``SimpleLazyObject`` and binding it fails; the correct behaviour is a normal
string kwarg that the ORM accepts.
"""
import sys
import types

import django
from django.conf import settings

# A dynamic URLconf so the script stays self-contained.
urlconf = types.ModuleType("repro_urls")
sys.modules["repro_urls"] = urlconf

settings.configure(
    DEBUG=True,
    SECRET_KEY="repro",
    ALLOWED_HOSTS=["*"],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    INSTALLED_APPS=["django.contrib.contenttypes"],
    ROOT_URLCONF="repro_urls",
    USE_TZ=True,
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [
                    (
                        "django.template.loaders.locmem.Loader",
                        {"offers/offer.html": "{{ offer.slug }}"},
                    )
                ]
            },
        }
    ],
)
django.setup()

from django.db import connection, models


class Account(models.Model):
    slug = models.SlugField()

    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as schema_editor:
    schema_editor.create_model(Account)

Account.objects.create(slug="my-offer")

from django.urls import path
from django.views.generic import TemplateView


class OfferView(TemplateView):
    template_name = "offers/offer.html"

    def get_context_data(self, **kwargs):
        offer_slug = kwargs.get("offer_slug", "")
        offer = Account.objects.get(slug=offer_slug)
        return {"offer": offer, "offer_slug": offer_slug}


urlconf.urlpatterns = [
    path("offers/<slug:offer_slug>/", OfferView.as_view(), name="offer_view")
]

from django.test import Client

client = Client()
try:
    response = client.get("/offers/my-offer/")
except Exception as exc:
    raise AssertionError(
        "GET /offers/my-offer/ raised %s: %s" % (type(exc).__name__, exc)
    )

assert response.status_code == 200, response.status_code
assert response.content == b"my-offer", response.content
print("OK")

### test_repro_3.py
"""Reproduction using ``get_object_or_404`` exactly as in the issue report.

``offer_slug = kwargs.get("offer_slug", "")`` is handed straight to
``get_object_or_404(Account, slug=offer_slug)``.  In Django 3.1 that value is a
``SimpleLazyObject`` which the database backend cannot bind, so the lookup
raises ``InterfaceError: Error binding parameter 0``.  The correct behaviour
is that the lookup succeeds without an explicit ``str()`` conversion.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="repro",
    ALLOWED_HOSTS=["*"],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    INSTALLED_APPS=["django.contrib.contenttypes"],
    USE_TZ=True,
)
django.setup()

from django.db import connection, models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.test import RequestFactory
from django.views.generic import TemplateView


class Account(models.Model):
    slug = models.SlugField()

    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as schema_editor:
    schema_editor.create_model(Account)

Account.objects.create(slug="my-offer")


class OfferView(TemplateView):
    template_name = "offers/offer.html"

    def get_context_data(self, **kwargs):
        offer_slug = kwargs.get("offer_slug", "")
        offer = get_object_or_404(Account, slug=offer_slug)
        return {"offer": offer, "offer_slug": offer_slug}

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(context["offer_slug"])


request = RequestFactory().get("/offers/my-offer/")
try:
    response = OfferView.as_view()(request, offer_slug="my-offer")
except Exception as exc:
    raise AssertionError(
        "get_object_or_404 with a URL kwarg raised %s: %s"
        % (type(exc).__name__, exc)
    )

assert response.status_code == 200, response.status_code
assert response.content == b"my-offer", response.content
print("OK")

