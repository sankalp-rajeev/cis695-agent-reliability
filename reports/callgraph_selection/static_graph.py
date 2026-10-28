"""Base-source AST graph, with conservative, explicit uncertainty.

This module receives only base source paths. It never imports benchmark modules,
reads candidate/oracle artifacts, traverses reachability, or selects tests.
"""
from __future__ import annotations

import ast
import hashlib
import time
from collections import Counter, defaultdict
from pathlib import Path

from reliability.verifier.integrity import is_test_file

LIMITS = dict(python_files=50_000, source_blob_bytes=2 * 1024**2,
              source_bytes=512 * 1024**2, ast_nodes=5_000_000,
              definitions=1_000_000, call_sites=2_000_000, seconds=600)


class ResourceLimit(Exception):
    pass


def expression(node):
    if isinstance(node, ast.Name):
        return ("name", node.id)
    if isinstance(node, ast.Attribute):
        return ("attr", expression(node.value), node.attr)
    return ("dynamic", type(node).__name__)


def dotted(expr):
    if expr[0] == "name":
        return expr[1]
    if expr[0] == "attr":
        return dotted(expr[1]) + "." + expr[2]
    return "<" + expr[1] + ">"


class Graph:
    def __init__(self):
        self.started = time.monotonic()
        self.nodes = {}
        self.scopes = {}
        self.modules = defaultdict(list)
        self.files = {}
        self.calls = []
        self.edges = []
        self.failures = []
        self.counts = Counter()
        self.base_digest = hashlib.sha256()
        self.status = "complete"

    def check(self):
        for name in ("python_files", "source_bytes", "ast_nodes", "definitions", "call_sites"):
            if self.counts[name] > LIMITS[name]:
                raise ResourceLimit(name)
        if time.monotonic() - self.started > LIMITS["seconds"]:
            raise ResourceLimit("seconds")

    def add_scope(self, ident, parent, kind, caller, path, module):
        self.scopes[ident] = dict(parent=parent, kind=kind, caller=caller,
                                  path=path, module=module, bindings=defaultdict(list),
                                  star_import=False, redirected=set())

    def add_node(self, path, qual, kind, line, col, parent, module, **extra):
        ident = f"{path}::{qual}::{kind}@{line}:{col}"
        self.nodes[ident] = dict(id=ident, path=path, qualname=qual, kind=kind,
                                 line=line, column=col, parent=parent, module=module, **extra)
        self.add_scope(ident, parent, kind, ident, path, module)
        return ident

    def build(self, root: Path):
        paths = sorted(p for p in root.rglob("*.py") if p.is_file() and not p.is_symlink())
        self.counts["python_files"] = len(paths)
        self.counts["source_bytes"] = sum(p.stat().st_size for p in paths)
        try:
            self.check()
            for source in paths:
                self.check()
                path = source.relative_to(root).as_posix()
                payload = source.read_bytes()
                self.base_digest.update(path.encode() + b"\0" + payload + b"\0")
                if len(payload) > LIMITS["source_blob_bytes"]:
                    self.failures.append(dict(path=path, reason="source_blob_over_2_MiB"))
                    self.files[path] = "omitted"
                    self.counts["omitted_files"] += 1
                    continue
                try:
                    tree = ast.parse(payload, filename=path)
                except (SyntaxError, UnicodeError, ValueError, RecursionError) as exc:
                    self.files[path] = "parse_failure"
                    self.counts["parse_failures"] += 1
                    self.failures.append(dict(path=path, reason=type(exc).__name__,
                                              line=getattr(exc, "lineno", None),
                                              message=str(exc)[:200]))
                    continue
                for index, node in enumerate(ast.walk(tree)):
                    self.counts["ast_nodes"] += 1
                    self.counts["definitions"] += isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    self.counts["call_sites"] += isinstance(node, ast.Call)
                    if index % 4096 == 0:
                        self.check()
                self.check()
                self.files[path] = "parsed"
                self.counts["parsed_files"] += 1
                self.index_tree(path, tree)
            self.resolve_calls()
        except ResourceLimit as exc:
            self.status = "resource_limited"
            self.failures.append(dict(reason="fixed_resource_limit", limit=str(exc)))
        if self.status == "complete" and self.failures:
            self.status = "partial"
        self.counts.update(Counter(edge["status"] + "_edges" for edge in self.edges))
        self.counts["nodes"] = len(self.nodes)
        self.counts["edge_records"] = len(self.edges)
        self.runtime = time.monotonic() - self.started
        return self

    def index_tree(self, path, tree, indexer=None):
        """Shared indexing; callers may reuse an already preflighted base AST."""
        parts = list(Path(path).with_suffix("").parts)
        if parts[0] in {"src", "lib"}:
            parts = parts[1:]
        package = parts[-1] == "__init__"
        if package:
            parts = parts[:-1]
        module = ".".join(parts)
        mid = self.add_node(path, "<module>", "module", 1, 0, None, module,
                            package=package, decorated=False, conditional=False)
        self.modules[module].append(mid)
        (indexer or Indexer)(self, mid).visit(tree)

    def resolve_calls(self):
        """Existing classification logic, shared by original and amended builds."""
        self.expand_imports()
        for index, call in enumerate(self.calls):
            if index % 4096 == 0:
                self.check()
            scope, line, col, expr, unsupported = call
            if unsupported:
                refs, reason = [], "unsupported_comprehension_lambda_or_annotation_scope"
            else:
                refs, reason = self.resolve(scope, expr)
            refs = list(dict.fromkeys(refs))
            targets = [value for kind, value in refs if kind == "node"]
            if len(refs) == 1 and len(targets) == 1 and not reason:
                target = self.nodes[targets[0]]
                if target["decorated"] or target["conditional"]:
                    reason = "decorated_or_conditional_definition"
                status = "ambiguous" if reason else "resolved"
            elif targets:
                status = "ambiguous"
                reason = reason or "multiple_or_uncertain_bindings"
            else:
                status = "unresolved"
                reason = reason or "module_or_external_not_callable_definition"
            self.edges.append(dict(caller=self.scopes[scope]["caller"],
                                   scope=scope, path=self.scopes[scope]["path"],
                                   line=line, column=col, expression=dotted(expr),
                                   status=status, targets=targets, reason=reason or "unique_static_binding"))

    def resolve(self, sid, expr, depth=0):
        if depth > 30:
            return [], "resolution_depth_limit"
        scope = self.scopes[sid]
        if expr[0] == "dynamic":
            return [], "dynamic_receiver_or_callable"
        if expr[0] == "name":
            name = expr[1]
            current = sid
            while current:
                here = self.scopes[current]
                if name in here["redirected"]:
                    return [], "global_or_nonlocal_binding"
                bindings = here["bindings"].get(name)
                if bindings:
                    # Unknown assignments/parameters stay visible alongside definitions.
                    return list(bindings), "uncertain_or_rebound_name" if any(k == "unknown" for k, _ in bindings) else ""
                if here["star_import"]:
                    return [], "star_import_may_bind_name"
                current = here["parent"]
                # A class namespace is not a closure for functions or nested classes.
                while current and self.scopes[current]["kind"] == "class":
                    current = self.scopes[current]["parent"]
            return [], "name_not_statically_bound_or_builtin"
        refs, reason = self.resolve(sid, expr[1], depth + 1)
        result = []
        for kind, value in refs:
            if kind == "module":
                members, why = self.module_member(value, expr[2])
                result.extend(members)
                reason = reason or why
            elif kind in {"node", "receiver"} and self.nodes[value]["kind"] == "class":
                cls = self.nodes[value]
                members = self.scopes[value]["bindings"].get(expr[2], [])
                result.extend(members)
                if cls["decorated"] or cls["conditional"]:
                    reason = reason or "uncertain_class_definition"
                if kind == "receiver" and (cls.get("bases") or
                        "__getattribute__" in self.scopes[value]["bindings"] or
                        "__getattr__" in self.scopes[value]["bindings"]):
                    reason = reason or "inheritance_or_dynamic_receiver_dispatch"
                if not members:
                    reason = reason or "attribute_or_inherited_member_not_resolved"
            else:
                reason = reason or "instance_or_external_attribute_not_resolved"
        if len(refs) > 1:
            reason = reason or "multiple_receiver_bindings"
        return result, reason

    def module_member(self, module, name):
        mids = self.modules.get(module, [])
        result = []
        reason = "module_identity_collision" if len(mids) > 1 else ""
        for mid in mids:
            result.extend(self.scopes[mid]["bindings"].get(name, []))
            if self.scopes[mid]["star_import"]:
                reason = reason or "star_import_may_bind_attribute"
        child = module + "." + name if module else name
        if child in self.modules:
            result.append(("module", child))
        if any(k == "unknown" for k, _ in result):
            reason = reason or "uncertain_or_rebound_attribute"
        return result, reason or ("" if result else "external_or_missing_module_attribute")

    def expand_imports(self):
        """Resolve explicit from-import references without executing imports.

        Cycle-safe expansion is a metadata operation, not call traversal.
        """
        def expand(ref, seen):
            kind, value = ref
            if kind != "import":
                return [ref]
            if ref in seen:
                return [("unknown", "cyclic_import")]
            if len(seen) > 30:
                return [("unknown", "import_expansion_depth_limit")]
            module, name = value.rsplit(":", 1)
            refs, reason = self.module_member(module, name)
            if reason:
                refs.append(("unknown", reason))
            return [item for sub in refs for item in expand(sub, seen | {ref})]
        expanded = {}
        for index, (sid, scope) in enumerate(self.scopes.items()):
            if index % 1024 == 0:
                self.check()
            expanded[sid] = {name: list(dict.fromkeys(item for ref in refs for item in expand(ref, set())))
                             for name, refs in scope["bindings"].items()}
        for sid, bindings in expanded.items():
            self.scopes[sid]["bindings"] = bindings


class Indexer(ast.NodeVisitor):
    def __init__(self, graph, scope):
        self.g = graph
        self.scope = scope
        self.conditional = 0
        self.unsupported = 0

    def bind(self, name, ref):
        self.g.scopes[self.scope]["bindings"][name].append(ref)

    def definition(self, node):
        scope = self.g.scopes[self.scope]
        parent = self.g.nodes[scope["caller"]]
        is_class = isinstance(node, ast.ClassDef)
        is_method = scope["kind"] == "class"
        test = is_test_file(scope["path"]) and node.name.startswith("test")
        kind = "class" if is_class else ("test_method" if test and is_method else
                    "test_function" if test else "method" if is_method else "function")
        qual = node.name if parent["kind"] == "module" else parent["qualname"] + "." + node.name
        decorators = [dotted(expression(d)) for d in node.decorator_list]
        # Even classmethod/staticmethod must be unshadowed builtins to be safe.
        custom = bool(decorators)  # Conservative even for possibly shadowed builtin decorators.
        ident = self.g.add_node(scope["path"], qual, kind, node.lineno, node.col_offset,
                                self.scope, scope["module"], decorated=custom,
                                decorators=decorators, conditional=bool(self.conditional),
                                bases=[dotted(expression(b)) for b in node.bases] if is_class else [])
        for deco in node.decorator_list:
            self.visit(deco)
        if is_class:
            for base in node.bases:
                self.visit(base)
            for keyword in node.keywords:
                self.visit(keyword.value)
                self.g.nodes[ident]["decorated"] = True  # metaclass/custom class creation
        else:
            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self.visit(default)
            args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            args += [a for a in (node.args.vararg, node.args.kwarg) if a]
            for arg in args:
                self.g.scopes[ident]["bindings"][arg.arg].append(("unknown", "parameter"))
                if arg.annotation:
                    self.annotation(arg.annotation)
            if node.returns:
                self.annotation(node.returns)
            positional = [*node.args.posonlyargs, *node.args.args]
            if is_method and positional and "staticmethod" not in decorators:
                first = positional[0].arg
                if first in {"self", "cls"}:
                    self.g.scopes[ident]["bindings"][first] = [("receiver", self.scope)]
        self.bind(node.name, ("node", ident))
        previous, conditional = self.scope, self.conditional
        self.scope, self.conditional = ident, 0
        for statement in node.body:
            self.visit(statement)
        self.scope, self.conditional = previous, conditional

    visit_FunctionDef = definition
    visit_AsyncFunctionDef = definition
    visit_ClassDef = definition

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)) and not self.unsupported:
            self.bind(node.id, ("unknown", "assignment_or_deletion"))

    def visit_AnnAssign(self, node):
        self.visit(node.target)
        self.annotation(node.annotation)
        if node.value:
            self.visit(node.value)

    def visit_Import(self, node):
        for alias in node.names:
            self.bind(alias.asname or alias.name.split(".")[0],
                      ("module", alias.name if alias.asname else alias.name.split(".")[0]))
            if self.conditional:
                self.bind(alias.asname or alias.name.split(".")[0], ("unknown", "conditional_import"))

    def visit_ImportFrom(self, node):
        scope = self.g.scopes[self.scope]
        mid = scope["caller"]
        while self.g.nodes[mid]["kind"] != "module":
            mid = self.g.nodes[mid]["parent"]
        package = scope["module"].split(".")
        if not self.g.nodes[mid]["package"]:
            package = package[:-1]
        if node.level:
            module = ".".join(package[:len(package) - node.level + 1])
            if node.module:
                module = module + "." + node.module if module else node.module
        else:
            module = node.module or ""
        for alias in node.names:
            if alias.name == "*":
                scope["star_import"] = True
                continue
            self.bind(alias.asname or alias.name, ("import", module + ":" + alias.name))
            if self.conditional:
                self.bind(alias.asname or alias.name, ("unknown", "conditional_import"))

    def visit_Call(self, node):
        self.g.calls.append((self.scope, node.lineno, node.col_offset,
                             expression(node.func), bool(self.unsupported)))
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.bind(node.name, ("unknown", "exception_binding"))
        self.generic_visit(node)

    def visit_Match(self, node):
        for part in ast.walk(node):
            if isinstance(part, (ast.MatchAs, ast.MatchStar)) and part.name:
                self.bind(part.name, ("unknown", "match_binding"))
            if isinstance(part, ast.MatchMapping) and part.rest:
                self.bind(part.rest, ("unknown", "match_binding"))
        self.conditional_visit(node)

    def visit_Global(self, node):
        self.g.scopes[self.scope]["redirected"].update(node.names)

    visit_Nonlocal = visit_Global

    def conditional_visit(self, node):
        self.conditional += 1
        self.generic_visit(node)
        self.conditional -= 1

    visit_If = conditional_visit
    visit_For = conditional_visit
    visit_AsyncFor = conditional_visit
    visit_While = conditional_visit
    visit_Try = conditional_visit
    visit_TryStar = conditional_visit
    visit_With = conditional_visit
    visit_AsyncWith = conditional_visit

    def unsupported_visit(self, node):
        self.unsupported += 1
        self.generic_visit(node)
        self.unsupported -= 1

    visit_Lambda = unsupported_visit
    visit_ListComp = unsupported_visit
    visit_DictComp = unsupported_visit
    visit_SetComp = unsupported_visit
    visit_GeneratorExp = unsupported_visit

    def annotation(self, node):
        # Visit the root as well: an annotation can itself be ast.Call.
        self.unsupported += 1
        self.visit(node)
        self.unsupported -= 1
