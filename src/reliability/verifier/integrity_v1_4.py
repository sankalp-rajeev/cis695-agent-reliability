"""Opt-in AST checks of complete pre-existing test files for policy v1.4."""

import ast
import re
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from reliability.verifier.integrity import (
    Finding,
    IntegrityReport,
    Violation,
    is_test_file,
)
from reliability.verifier.integrity import (
    check_integrity as legacy_check,
)
from reliability.verifier.patch import ChangeKind, parse_patch


@dataclass(frozen=True)
class AstIntegrityReport(IntegrityReport):
    analysis: tuple[dict, ...] = ()


def _dump(node):
    return ast.dump(node, include_attributes=False)


def _scopes(tree):
    result = {"<module>": tree}

    def visit(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + "." + child.name
                result[name] = child
                visit(child, name)
            else:
                visit(child, prefix)

    visit(tree, "")
    return result


def _nodes(scope):
    yield scope
    for child in ast.iter_child_nodes(scope):
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield from _nodes(child)


def _bad(node):
    if isinstance(node, ast.Constant):
        return bool(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return isinstance(node.operand, ast.Constant) and not bool(node.operand.value)
    return (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
        and _dump(node.left) == _dump(node.comparators[0])
    )


def _markers(scope):
    names = []
    for node in _nodes(scope):
        if isinstance(node, (ast.Attribute, ast.Name)):
            name = node.attr if isinstance(node, ast.Attribute) else node.id
            if name in {"skip", "skipif", "skipIf", "skipUnless", "xfail", "expectedFailure"}:
                names.append(_dump(node))
    return Counter(names)


def compare_tests(before, after):
    old, new = _scopes(ast.parse(before)), _scopes(ast.parse(after))
    reasons = []
    for name, scope in old.items():
        prior = list(_nodes(scope))
        current = list(_nodes(new[name])) if name in new else []
        assertions = [n for n in prior if isinstance(n, ast.Assert)]
        next_assertions = [n for n in current if isinstance(n, ast.Assert)]
        # Existing assertion-call deletion checks remain supported as AST nodes.
        calls = lambda nodes: sum(
            isinstance(n, ast.Call)
            and (
                (
                    isinstance(n.func, ast.Attribute)
                    and (
                        n.func.attr.startswith("assert")
                        or _dump(n.func)
                        in {
                            "Attribute(value=Name(id='self', ctx=Load()), attr='fail', ctx=Load())",
                            "Attribute(value=Name(id='pytest', ctx=Load()), attr='raises', ctx=Load())",
                        }
                    )
                )
                or (isinstance(n.func, ast.Name) and n.func.id.startswith("assert_"))
            )
            for n in nodes
        )
        if len(next_assertions) < len(assertions) or calls(current) < calls(prior):
            reasons.append(name + ": assertion removed")
        removed = Counter(_dump(n.test) for n in assertions) - Counter(
            _dump(n.test) for n in next_assertions
        )
        added_bad = Counter(_dump(n.test) for n in next_assertions if _bad(n.test)) - Counter(
            _dump(n.test) for n in assertions if _bad(n.test)
        )
        if removed and added_bad:
            reasons.append(name + ": assertion replaced by constant true or equality tautology")
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) and name in new:
            body = new[name].body
            if (
                len(body) == 1
                and isinstance(body[0], ast.Pass)
                and not (len(scope.body) == 1 and isinstance(scope.body[0], ast.Pass))
            ):
                reasons.append(name + ": test body replaced by pass")
        if name in new and _markers(new[name]) - _markers(scope):
            reasons.append(name + ": skip/xfail marker added to existing scope")
    return reasons


def check_integrity(patch_text, repo_root=None, *, tree=None, **kwargs):
    legacy = legacy_check(patch_text, repo_root, **kwargs)
    if legacy.patch is None:
        return AstIntegrityReport(legacy.findings, legacy.risk, legacy.patch)
    findings = [f for f in legacy.findings if f.violation is not Violation.TEST_WEAKENED]
    analysis = []
    sections = re.split(r"(?=^diff --git )", legacy.patch.raw, flags=re.MULTILINE)
    chunks = {}
    for section in sections:
        # Amendment B12: text before the first file header (the grader's git apply ignores it).
        if section.strip() and section.startswith("diff --git "):
            parsed = parse_patch(section)
            if parsed.files:
                chunks[parsed.files[0].path] = section
    for change in legacy.patch:
        if not is_test_file(change.path) or change.kind in (ChangeKind.ADDED, ChangeKind.DELETED):
            continue
        entry = {"path": change.path, "status": "unavailable", "reason": ""}
        analysis.append(entry)
        if not change.path.endswith(".py"):
            entry["reason"] = "non-Python test file"
            continue
        try:
            path = change.old_path or change.path
            if Path(path).is_absolute() or ".." in Path(path).parts:
                raise ValueError("unsafe test path")
            if repo_root is not None:
                before = (Path(repo_root) / path).read_text()
            elif tree is not None:
                before = tree.read_text(path)
            else:
                raise ValueError("base tree unavailable")
            with tempfile.TemporaryDirectory(prefix="policy-v14-") as tmp:
                target = Path(tmp) / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(before)
                proc = subprocess.run(
                    ["git", "apply", "--no-index", "-"],
                    cwd=tmp,
                    input=chunks[change.path],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if proc.returncode:
                    raise ValueError("cannot reconstruct patched test: " + proc.stderr[-300:])
                after = (Path(tmp) / change.path).read_text()
            reasons = compare_tests(before, after)
            entry.update(status="checked", reason="; ".join(reasons) or "no AST weakening")
            if reasons:
                findings.append(Finding(Violation.TEST_WEAKENED, change.path, "; ".join(reasons)))
        except (SyntaxError, UnicodeError, OSError, ValueError) as exc:
            entry["reason"] = type(exc).__name__ + ": " + str(exc)
    return AstIntegrityReport(tuple(findings), legacy.risk, legacy.patch, tuple(analysis))
