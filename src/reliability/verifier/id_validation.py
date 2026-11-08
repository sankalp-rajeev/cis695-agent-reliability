"""Label-blind AST validation and identity expansion, without source execution."""

from __future__ import annotations

import ast
import configparser
import fnmatch
import shlex
import tomllib
from dataclasses import asdict, dataclass, replace
from pathlib import PurePosixPath

from reliability.verifier.selection import RepoTree

_FUNCTION = (ast.FunctionDef, ast.AsyncFunctionDef)
_TESTCASE_ROOTS = {"unittest.TestCase", "unittest.case.TestCase"}


@dataclass(frozen=True)
class IDValidation:
    selected_id: str
    category: str
    runnable_ids: tuple[str, ...] = ()
    reason: str = ""
    owner: str = ""
    owner_is_testcase: bool = False
    decorators: tuple[str, ...] = ()
    expanded: bool = False
    stage: str = "static"
    message: str = ""
    # Native expansion members are retained even when another member is invalid.
    invalid_instances: tuple[tuple[str, str], ...] = ()
    static_reason: str = ""
    native_disagrees: bool = False
    owner_instances: tuple[str, ...] = ()
    unavailable: bool = False
    failure_status: str = ""
    elapsed_s: float = 0.0
    collector_fallback: bool = False
    collector_failure_status: str = ""
    collector_message: str = ""
    module_skip_reason: str = ""
    module_skip_instances: tuple[tuple[str, str], ...] = ()

    @property
    def valid(self):
        return bool(self.runnable_ids) and not self.reason

    def to_dict(self):
        data = asdict(self)
        data["runnable_ids"] = list(self.runnable_ids)
        data["decorators"] = list(self.decorators)
        data["invalid_instances"] = [list(pair) for pair in self.invalid_instances]
        data["owner_instances"] = list(self.owner_instances)
        data['module_skip_instances'] = [list(pair) for pair in self.module_skip_instances]
        return {
            **data,
            "valid": self.valid,
            "validation_status": ("MODULE_SKIPPED" if self.module_skip_reason else "VALID") if self.valid
            else (self.failure_status or "COLLECTION_ERROR")
            if self.unavailable
            else "INVALID_ID",
            "expansion_count": len(self.owner_instances or self.runnable_ids)
            if self.expanded
            else 0,
        }


@dataclass
class SourceTree:
    sources: dict[str, str]

    def list_files(self):
        return tuple(sorted(self.sources))

    def read_text(self, path):
        return self.sources.get(path, "")


class StaticIndex:
    """Resolve imports, unittest ancestry and effective C3 method owners by AST."""

    def __init__(self, tree: RepoTree, runner: str, *, parse_cache=None):
        self.runner = runner
        parse_cache = {} if parse_cache is None else parse_cache
        self.tree = tree
        self.modules, self.classes, self.aliases, self.parse_errors = {}, {}, {}, {}
        self.files = set(tree.list_files())
        for path in sorted(self.files):
            if not path.endswith(".py"):
                continue
            module = self.module_name(path)
            try:
                text = tree.read_text(path)
                cached = parse_cache.get(path)
                if cached is not None and cached[0] == text:
                    parsed = cached[1]
                else:
                    parsed = ast.parse(text, filename=path)
                    parse_cache[path] = (text, parsed)
            except (SyntaxError, ValueError) as exc:
                self.parse_errors[path] = str(exc)
                continue
            self.modules[module] = (path, parsed)
        test_roots = {m.split(".")[1] for m in self.modules if m.startswith("tests.")}

        def canonical(name):
            if runner == "django" and name.split(".")[0] in test_roots:
                return "tests." + name
            return name

        def imports(node):
            for child in ast.iter_child_nodes(node):
                if not isinstance(child, (*_FUNCTION, ast.ClassDef)):
                    yield child
                    yield from imports(child)

        for module, (path, parsed) in self.modules.items():
            aliases = self.aliases.setdefault(module, {})
            package = module if path.endswith("/__init__.py") else module.rpartition(".")[0]
            for node in imports(parsed):
                if isinstance(node, ast.ImportFrom):
                    prefix = (
                        ".".join(package.split(".")[: len(package.split(".")) - node.level + 1])
                        if node.level
                        else ""
                    )
                    target = ".".join(v for v in (prefix, node.module) if v)
                    for alias in node.names:
                        aliases[alias.asname or alias.name] = canonical(target + "." + alias.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        aliases[alias.asname or alias.name.split(".")[0]] = canonical(
                            alias.name if alias.asname else alias.name.split(".")[0]
                        )
            self._classes(module, path, parsed.body)
        self.bases = {
            key: tuple(self.resolve(module, ast.unparse(b)) for b in node.bases)
            for key, (module, _, node) in self.classes.items()
        }
        self._mros = {}
        self._subclasses = {}

    @staticmethod
    def module_name(path):
        name = path[:-3].replace("/", ".")
        return name.removesuffix(".__init__")

    def _classes(self, module, path, body, scope=""):
        for node in body:
            if isinstance(node, ast.ClassDef):
                key = module + "." + scope + node.name
                self.classes[key] = (module, path, node)
                self._classes(module, path, node.body, scope + node.name + ".")

    def resolve(self, module, name):
        head, _, tail = name.partition(".")
        value = self.aliases[module].get(head, module + "." + head)
        value += "." + tail if tail else ""
        seen = set()
        while value not in seen and len(seen) < 30:
            if value in self.classes or value in _TESTCASE_ROOTS:
                break
            seen.add(value)
            parts = value.split(".")
            replacement = None
            for i in range(len(parts) - 1, 0, -1):
                target = self.aliases.get(".".join(parts[:i]), {}).get(parts[i])
                if target:
                    replacement = ".".join([target] + parts[i + 1 :])
                    break
            if replacement is None:
                break
            value = replacement
        return value

    def mro(self, key, active=()):
        if key in self._mros:
            return self._mros[key]
        if key in active:
            raise ValueError("cyclic class ancestry: " + key)
        bases = self.bases.get(key, ())
        seqs = [list(self.mro(b, active + (key,))) for b in bases] + [list(bases)]
        result = [key]
        while any(seqs):
            seqs = [s for s in seqs if s]
            head = next((s[0] for s in seqs if all(s[0] not in t[1:] for t in seqs)), None)
            if head is None:
                raise ValueError("unresolved C3 MRO: " + key)
            result.append(head)
            for seq in seqs:
                if seq[0] == head:
                    seq.pop(0)
        self._mros[key] = tuple(result)
        return self._mros[key]

    def is_testcase(self, key):
        return bool(_TESTCASE_ROOTS.intersection(self.mro(key)))

    @staticmethod
    def named(body, name):
        for node in reversed(body):
            if getattr(node, "name", None) == name:
                return node
            targets = (
                node.targets
                if isinstance(node, ast.Assign)
                else [node.target]
                if isinstance(node, ast.AnnAssign)
                else ()
            )
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                return node
        return None

    def member(self, key, name):
        for parent in self.mro(key):
            if parent in self.classes:
                node = self.named(self.classes[parent][2].body, name)
                if node is not None:
                    return parent, node
        return "", None

    def pytest_patterns(self, path, option="python_classes"):
        defaults = ("Test",) if option == "python_classes" else ("test",)
        # pytest searches from the selected path toward the repo root. At each
        # level these files have the same precedence as its native config loader.
        for folder in (PurePosixPath(path).parent, *PurePosixPath(path).parent.parents):
            for filename in ("pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"):
                candidate = str(folder / filename)
                if candidate not in self.files:
                    continue
                try:
                    text = self.tree.read_text(candidate)
                    if filename == "pyproject.toml":
                        settings = (
                            tomllib.loads(text).get("tool", {}).get("pytest", {}).get("ini_options")
                        )
                        if settings is None:
                            continue
                        value = settings.get(option, defaults)
                        return tuple(shlex.split(value) if isinstance(value, str) else value)
                    parser = configparser.ConfigParser(interpolation=None)
                    parser.read_string(text)
                    section = "tool:pytest" if filename == "setup.cfg" else "pytest"
                    if filename not in ("pytest.ini", ".pytest.ini") and not parser.has_section(
                        section
                    ):
                        continue
                    return (
                        tuple(shlex.split(parser.get(section, option)))
                        if parser.has_option(section, option)
                        else defaults
                    )
                except (ValueError, configparser.Error):
                    return defaults  # malformed configuration is diagnosed natively
        return defaults

    @staticmethod
    def matches(name, patterns):
        return any(
            fnmatch.fnmatchcase(name, pattern)
            if any(c in pattern for c in "*?[")
            else name.startswith(pattern)
            for pattern in patterns
        )

    def runnable_owner(self, key):
        testcase = self.is_testcase(key)
        if self.runner == "django":
            return testcase
        if self.runner == "sympy":
            return True  # prediction only; SymPy identities require native receipts
        _, path, node = self.classes[key]
        _, test_flag = self.member(key, "__test__")
        if (
            isinstance(test_flag, (ast.Assign, ast.AnnAssign))
            and isinstance(test_flag.value, ast.Constant)
            and test_flag.value.value is False
        ):
            return False
        if testcase:
            return True
        if not self.matches(node.name, self.pytest_patterns(path)):
            return False
        return self.member(key, "__init__")[1] is None

    def concrete_subclasses(self, owner, name):
        cache_key = (owner, name)
        if cache_key not in self._subclasses:
            values = []
            definition_owner = self.member(owner, name)[0]
            for key, (module, path, _) in self.classes.items():
                try:
                    if (
                        key != owner
                        and owner in self.mro(key)
                        and self.runnable_owner(key)
                        and self.member(key, name)[0] == definition_owner
                    ):
                        scope = key[len(module) + 1 :].replace(".", "::")
                        values.append(path + "::" + scope + "::" + name)
                except ValueError:
                    # Unrelated invalid class definitions are native collector concerns.
                    continue
            self._subclasses[cache_key] = tuple(sorted(values))
        return self._subclasses[cache_key]

    def classify(self, selected_id):
        parts = selected_id.split("::")
        path = parts[0]
        if (
            PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or len(parts) < 2
            or path not in self.files
        ):
            return IDValidation(selected_id, "not_found", reason="not_found")
        if path in self.parse_errors:
            return IDValidation(
                selected_id,
                "not_found",
                reason="source_parse_error",
                message=self.parse_errors[path],
            )
        module = self.module_name(path)
        if module not in self.modules:
            return IDValidation(selected_id, "not_found", reason="not_found")
        name = parts[-1].split("[", 1)[0]
        owner, node = "", None
        selected_class = ".".join([module] + parts[1:-1]) if len(parts) > 2 else ""
        try:
            if selected_class in self.classes:
                owner, node = self.member(selected_class, name)
            elif len(parts) == 2:
                node = self.named(self.modules[module][1].body, name)
            if node is None:
                # A nested helper cannot be resolved as a method by the runner.
                body = (
                    self.classes[selected_class][2].body
                    if selected_class in self.classes
                    else self.modules[module][1].body
                )
                nested = any(
                    isinstance(n, _FUNCTION) and n.name == name
                    for parent in body
                    if isinstance(parent, _FUNCTION)
                    for n in ast.walk(parent)
                    if n is not parent
                )
                return IDValidation(
                    selected_id,
                    "helper" if nested else "not_found",
                    reason="nested_helper" if nested else "not_found",
                )
            decorators = tuple(ast.unparse(d) for d in getattr(node, "decorator_list", ()))
            testcase = bool(selected_class and self.is_testcase(selected_class))
        except ValueError as exc:
            return IDValidation(
                selected_id, "not_found", reason="unresolved_ancestry", message=str(exc)
            )
        result = IDValidation(
            selected_id,
            "runnable_test",
            owner=owner,
            owner_is_testcase=testcase,
            decorators=decorators,
        )
        if any(
            d.split("(")[0].rsplit(".", 1)[-1] in ("property", "cached_property")
            for d in decorators
        ):
            return replace(result, category="property", reason="property")
        if not isinstance(node, _FUNCTION):
            return replace(result, category="helper", reason="non_callable_attribute")
        if not (
            name.startswith("test")
            if self.runner == "django"
            else self.matches(name, self.pytest_patterns(path, "python_functions"))
        ):
            return replace(result, category="helper", reason="helper")
        if owner and not self.runnable_owner(selected_class):
            identities = self.concrete_subclasses(selected_class, name)
            return replace(
                result,
                category="non_runnable_owner_method",
                expanded=True,
                runnable_ids=identities,
                reason="" if identities else "no_runnable_owner",
            )
        if not owner and self.runner == "django":
            return replace(
                result,
                category="decorated_callable" if decorators else "plain_function",
                reason="plain_function",
            )
        return replace(
            result,
            category="decorated_callable" if decorators else "runnable_test",
            runnable_ids=(selected_id,),
        )

    def validate(self, selected):
        return tuple(self.classify(label) for label in selected)


# A parse failure or unresolved ancestry is not proof that an identity is invalid.
STATIC_INVALID_REASONS = frozenset(
    {
        "not_found",
        "property",
        "plain_function",
        "helper",
        "nested_helper",
        "non_callable_attribute",
        "no_runnable_owner",
    }
)


def native_failure_status(observed):
    """Require an explicit successful receipt before absence can prove invalidity."""
    status = observed.get("collection_status")
    reason = observed.get("reason", "")
    if (status == 'MODULE_SKIPPED' and observed.get('module_skip_reason','').strip()
        and observed.get('completed') is True and observed.get('returncode',0) in (0,5)):
        return ''
    if status == "NOT_REACHED":
        return "NOT_REACHED"
    if status == "RUNNER_UNAVAILABLE" or reason == "runner_unavailable":
        return "RUNNER_UNAVAILABLE"
    if (
        status == "COLLECTION_ERROR"
        or observed.get("returncode", 0) != 0
        or reason in ("native_load_error", "collection_timeout", "native_identity_mismatch")
    ):
        return "COLLECTION_ERROR"
    if observed.get("completed") is not True:
        return "COLLECTION_ERROR"
    return ""


def merge_native(static, native):
    """INVALID_ID needs static rejection AND completed native absence."""
    output = []
    for item in static:
        concrete, invalid, messages, failures, skips = [], [], [], [], []
        selected = native.get(item.selected_id, {})
        direct = selected.get('ids') and not native_failure_status(selected)
        members = (item.selected_id,) if direct or selected.get('collection_status') == 'MODULE_SKIPPED' else (item.runnable_ids if item.valid else (item.selected_id,))
        for tid in members:
            observed = native.get(tid, {})
            ids = observed.get("ids", ())
            failure = native_failure_status(observed)
            if (not failure and observed.get('collection_status') == 'MODULE_SKIPPED'
                and observed.get('module_skip_reason')):
                skips.append((tid,observed['module_skip_reason']))
                concrete.append(tid)
                continue
            if any(
                node != tid and not ("[" not in tid and node.startswith(tid + "[")) for node in ids
            ):
                failure = "COLLECTION_ERROR"
                observed = {
                    "reason": "native_identity_mismatch",
                    "message": "Collector returned an identity outside the selected instance",
                }
            if failure or observed.get("reason") or not ids:
                reason = observed.get("reason") or (
                    "collection_error" if failure else "native_not_found"
                )
                invalid.append((tid, reason))
                if failure:
                    failures.append(failure)
                if observed.get("message"):
                    messages.append(tid + ": " + observed["message"])
            else:
                concrete.extend(ids)
        static_proof = not item.valid and item.reason in STATIC_INVALID_REASONS
        failure_status = (
            "RUNNER_UNAVAILABLE"
            if "RUNNER_UNAVAILABLE" in failures
            else "NOT_REACHED"
            if "NOT_REACHED" in failures
            else "COLLECTION_ERROR"
            if failures
            else ""
        )
        if invalid and not failure_status and not static_proof:
            failure_status = 'COLLECTION_ERROR'
            messages.append('Static/native disagreement: native absence alone is not INVALID_ID')
        unavailable = bool(failure_status)
        if unavailable:
            reason = failure_status.lower()
        elif invalid:
            reason = (
                item.reason
                if static_proof
                else "invalid_expansion"
                if item.expanded
                else invalid[0][1]
            )
        else:
            reason = ""
        output.append(
            replace(
                item,
                runnable_ids=tuple(dict.fromkeys(concrete)),
                expanded=item.expanded and item.valid,
                reason=reason,
                unavailable=unavailable,
                failure_status=failure_status if unavailable else "",
                elapsed_s=max((native.get(t, {}).get("elapsed_s", 0.0) for t in (item.runnable_ids or (item.selected_id,))), default=0.0),
                stage="native",
                message="\n".join(messages),
                invalid_instances=tuple(invalid),
                static_reason=item.reason,
                native_disagrees=item.valid != (not invalid and bool(concrete)),
                owner_instances=item.runnable_ids if item.expanded else (),
                module_skip_reason='; '.join(dict.fromkeys(reason for _,reason in skips)),
                module_skip_instances=tuple(skips),
            )
        )
    return tuple(output)
