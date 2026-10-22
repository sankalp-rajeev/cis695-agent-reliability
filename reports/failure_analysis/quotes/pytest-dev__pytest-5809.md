POST-HOC ANALYSIS ONLY. Uses oracle fields (FAIL_TO_PASS, PASS_TO_PASS, gold patch, test_patch). Must never feed back into any run.

# pytest-dev__pytest-5809  group=group4_right_old_tests_fail  run=main_50_a
## ISSUE
Lexer "python3" in --pastebin feature causes HTTP errors
The `--pastebin` option currently submits the output of `pytest` to `bpaste.net` using `lexer=python3`: https://github.com/pytest-dev/pytest/blob/d47b9d04d4cf824150caef46c9c888779c1b3f58/src/_pytest/pastebin.py#L68-L73

For some `contents`, this will raise a "HTTP Error 400: Bad Request".

As an example:
~~~
>>> from urllib.request import urlopen
>>> with open("data.txt", "rb") as in_fh:
...     data = in_fh.read()
>>> url = "https://bpaste.net"
>>> urlopen(url, data=data)
HTTPError: Bad Request
~~~
with the attached [data.txt](https://github.com/pytest-dev/pytest/files/3561212/data.txt).

This is the underlying cause for the problems mentioned in #5764.

The call goes through fine if `lexer` is changed from `python3` to `text`. This would seem like the right thing to do in any case: the console output of a `pytest` run that is being uploaded is not Python code, but arbitrary text.



## AGENT PATCH
diff --git a/src/_pytest/pastebin.py b/src/_pytest/pastebin.py
index 41576a615..79b0d9d40 100644
--- a/src/_pytest/pastebin.py
+++ b/src/_pytest/pastebin.py
@@ -79,7 +79,7 @@ def create_new_paste(contents):
 
     params = {
         "code": contents,
-        "lexer": "python3" if sys.version_info[0] >= 3 else "python",
+        "lexer": "text",
         "expiry": "1week",
     }
     url = "https://bpaste.net"


## GOLD PATCH
diff --git a/src/_pytest/pastebin.py b/src/_pytest/pastebin.py
--- a/src/_pytest/pastebin.py
+++ b/src/_pytest/pastebin.py
@@ -77,11 +77,7 @@ def create_new_paste(contents):
         from urllib.request import urlopen
         from urllib.parse import urlencode
 
-    params = {
-        "code": contents,
-        "lexer": "python3" if sys.version_info[0] >= 3 else "python",
-        "expiry": "1week",
-    }
+    params = {"code": contents, "lexer": "text", "expiry": "1week"}
     url = "https://bpaste.net"
     response = urlopen(url, data=urlencode(params).encode("ascii")).read()
     m = re.search(r'href="/raw/(\w+)"', response.decode("utf-8"))


## GOLD TEST_PATCH
diff --git a/testing/test_pastebin.py b/testing/test_pastebin.py
--- a/testing/test_pastebin.py
+++ b/testing/test_pastebin.py
@@ -126,7 +126,7 @@ def test_create_new_paste(self, pastebin, mocked_urlopen):
         assert len(mocked_urlopen) == 1
         url, data = mocked_urlopen[0]
         assert type(data) is bytes
-        lexer = "python3" if sys.version_info[0] >= 3 else "python"
+        lexer = "text"
         assert url == "https://bpaste.net"
         assert "lexer=%s" % lexer in data.decode()
         assert "code=full-paste-contents" in data.decode()


## V4 SOURCES
### test_repro_1.py
"""Reproduction test: pastebin uploads must use lexer=text, not python3.

The issue reports that ``pytest --pastebin`` submits its console output to
bpaste.net with ``lexer=python3``, which can make the service return
``HTTP Error 400: Bad Request``.  Arbitrary pytest output should be submitted
as plain text.
"""
import urllib.request
from urllib.parse import parse_qs

from _pytest import pastebin


class DummyResponse(object):
    def read(self):
        return b'<a href="/raw/abc123">raw</a>'


captured = []


def fake_urlopen(url, data=None):
    captured.append((url, data))
    return DummyResponse()


original_urlopen = urllib.request.urlopen
urllib.request.urlopen = fake_urlopen
try:
    result = pastebin.create_new_paste(b"pytest session output: anything\n")
finally:
    urllib.request.urlopen = original_urlopen

assert result == "https://bpaste.net/show/abc123", result
assert len(captured) == 1, captured
url, data = captured[0]
assert url == "https://bpaste.net", url
assert isinstance(data, bytes), type(data)

params = parse_qs(data.decode("ascii"))
assert params.get("lexer") == ["text"], (
    "pastebin should submit arbitrary pytest output with lexer='text', got %r"
    % (params.get("lexer"),)
)

### test_repro_2.py
"""Reproduction test: no HTTP 400 when submitting arbitrary output.

This simulates bpaste.net's reported behaviour: requests using
``lexer=python3`` are rejected with ``HTTP Error 400: Bad Request``, while
requests using ``lexer=text`` are accepted.  The --pastebin feature must
therefore use the text lexer and complete successfully.
"""
import urllib.error
import urllib.request
from urllib.parse import parse_qs

from _pytest import pastebin


class DummyResponse(object):
    def read(self):
        return b'<a href="/raw/def456">raw</a>'


def fake_urlopen(url, data=None):
    params = parse_qs(data.decode("ascii"))
    lexer = params.get("lexer", [None])[0]
    if lexer != "text":
        raise urllib.error.HTTPError(url, 400, "Bad Request", None, None)
    return DummyResponse()


original_urlopen = urllib.request.urlopen
urllib.request.urlopen = fake_urlopen
try:
    try:
        result = pastebin.create_new_paste(b"arbitrary pytest output\n")
    except urllib.error.HTTPError as exc:
        raise AssertionError(
            "pastebin upload raised HTTP Error %s: %s; it should submit with "
            "lexer='text' instead" % (exc.code, exc.msg)
        ) from exc
finally:
    urllib.request.urlopen = original_urlopen

assert result == "https://bpaste.net/show/def456", result

### test_repro_3.py
"""Reproduction test: non-ASCII / arbitrary bytes are still accepted.

The problematic pytest output is arbitrary text, not Python source.  This
test uses output containing bytes that are not valid Python source characters
and checks that the request is submitted with the text lexer.
"""
import urllib.error
import urllib.request
from urllib.parse import parse_qs

from _pytest import pastebin


class DummyResponse(object):
    def read(self):
        return b'<a href="/raw/ghi789">raw</a>'


captured = []


def fake_urlopen(url, data=None):
    parsed = parse_qs(data.decode("ascii"))
    captured.append(parsed)
    lexer = parsed.get("lexer", [None])[0]
    if lexer != "text":
        raise urllib.error.HTTPError(url, 400, "Bad Request", None, None)
    return DummyResponse()


contents = b"F\xe2\x98\xba pytest output \xf0\x9f\x98\x80\n"
original_urlopen = urllib.request.urlopen
urllib.request.urlopen = fake_urlopen
try:
    try:
        result = pastebin.create_new_paste(contents)
    except urllib.error.HTTPError as exc:
        raise AssertionError(
            "pastebin rejected arbitrary output with HTTP %s: %s"
            % (exc.code, exc.msg)
        ) from exc
finally:
    urllib.request.urlopen = original_urlopen

assert result == "https://bpaste.net/show/ghi789", result
assert captured and captured[0].get("lexer") == ["text"], captured

