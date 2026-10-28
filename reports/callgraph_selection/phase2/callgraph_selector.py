"""Fixed bounded traversal and ranking, accepting only base graphs and candidates."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

from inputs import ROOT  # establishes the existing diagnostic/production import paths
from oracle_posthoc import canonical, family, match_test

DEPTHS = (1, 2, 3)
BUDGETS = (25, 50, 100, 250, 500)
VARIANTS = ("PRIMARY_RESOLVED_ONLY", "SECONDARY_RESOLVED_PLUS_AMBIGUOUS")


def module_from_path(path):
    parts = path[:-3].split("/")
    if parts[0] in {"src", "lib"}:
        parts = parts[1:]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


class Identities:
    """An index calling the existing normalizer; no second normalization rules."""
    def __init__(self, nodes, base_ids, repo):
        self.repo = repo
        self.base = defaultdict(set)
        self.definitions = defaultdict(list)
        self.methods = {}
        for raw in base_ids:
            key, method = canonical(raw, repo)
            if key is not None:
                self.base[key].add(raw)
        for node in nodes.values():
            if node["kind"] not in {"test_function", "test_method"}:
                continue
            raw = node["path"] + "::" + node["qualname"].replace(".", "::")
            key, method = canonical(raw, repo)
            if key in self.base:
                self.definitions[key].append(node["id"])
        self.test_definitions = {n for group in self.definitions.values() for n in group}
        self.emittable = {group[0]: min(self.base[key]) for key, group in self.definitions.items() if len(group) == 1}
        self.cache = {}

    def lookup(self, raw):
        if raw in self.cache:
            return self.cache[raw]
        key, method = canonical(raw, self.repo)
        matched_key = key
        if key is not None and key not in self.base and "[" in key:
            matched_key = family(key)
        definitions = self.definitions.get(matched_key, [])
        matched = False
        match_method = "unmatched"
        if matched_key in self.base:
            # The existing matcher checks exact identity / explicit parameter family;
            # empty changed={} cannot resolve a bare name from gold information.
            evidence = match_test(raw, sorted(self.base[matched_key]), self.repo, {})
            matched = bool(evidence["selected_ids"])
            match_method = evidence["match_method"]
        node = definitions[0] if matched and len(definitions) == 1 else None
        reason = ("unique_exact_base_definition" if node else "multiple_base_definitions" if len(definitions) > 1
                  else "base_identity_without_graph_definition" if matched else method if key is None
                  else "no_exact_base_identity")
        result = dict(node_id=node, canonical_id=key, normalization_method=method,
                      match_method=match_method, mapping_reason=reason)
        self.cache[raw] = result
        return result


@dataclass(frozen=True)
class Route:
    nodes: tuple[str, ...]
    edges: tuple[int, ...]


def callsite_id(edge, ordinal):
    return f"{edge['path']}:{edge['line']}:{edge['column']}:{edge['scope']}#{ordinal}"


class Traversal:
    def __init__(self, nodes, edges, variant):
        self.nodes, self.edges, self.variant = nodes, edges, variant
        self.reverse = defaultdict(list)
        self.edge_ids = [callsite_id(e, i) for i, e in enumerate(edges)]
        for index, edge in enumerate(edges):
            allowed = edge["status"] == "resolved" or (variant == VARIANTS[1] and edge["status"] == "ambiguous")
            if allowed:
                for target in sorted(set(edge["targets"])):
                    if target in nodes and edge["caller"] in nodes:
                        self.reverse[target].append((edge["caller"], index))
        self.cache = {}

    def route_key(self, route):
        return route.nodes, tuple(self.edge_ids[e] for e in route.edges)

    def from_seed(self, seed):
        if seed in self.cache:
            return self.cache[seed]
        shortest = {seed: Route((seed,), ())}
        frontier = {seed: shortest[seed]}
        for _ in DEPTHS:
            following = {}
            for callee, route in frontier.items():
                for caller, edge in self.reverse.get(callee, ()):
                    if caller in shortest:
                        continue
                    candidate = Route((caller, *route.nodes), (edge, *route.edges))
                    if caller not in following or self.route_key(candidate) < self.route_key(following[caller]):
                        following[caller] = candidate
            shortest.update(following)
            frontier = following
        self.cache[seed] = shortest
        return shortest

    def test_paths(self, seeds, tests):
        by_test = defaultdict(dict)
        fan_in = {}
        for seed in sorted(seeds):
            hits = {n: p for n, p in self.from_seed(seed).items() if n in tests and 1 <= len(p.edges) <= 3}
            fan_in[seed] = len(hits)
            for test, route in hits.items():
                by_test[test][seed] = route
        return by_test, fan_in

    def provenance(self, route):
        calls = []
        for position, index in enumerate(route.edges, 1):
            edge = self.edges[index]
            calls.append(dict(callsite_id=self.edge_ids[index], position=position, path=edge["path"],
                              line=edge["line"], column=edge["column"], caller=edge["caller"],
                              chosen_target=route.nodes[position], status=edge["status"],
                              candidate_targets=edge["targets"], reason=edge["reason"]))
        ambiguous = [c["position"] for c in calls if c["status"] == "ambiguous"]
        return dict(path_nodes=list(route.nodes), path_calls=calls, distance=len(route.edges),
                    uses_ambiguous_edge=bool(ambiguous), ambiguous_hop_count=len(ambiguous), ambiguous_hop_positions=ambiguous)


def features(raw, node, nodes, seed_modules, paths, fan_in, depth, primary_paths, position=None, identity=None):
    selected = {s: p for s, p in paths.get(node, {}).items() if len(p.edges) <= depth} if node else {}
    module = nodes[node]["module"] if node else module_from_path(raw.split("::", 1)[0])
    package = module.rpartition(".")[0]
    minimum = min((len(p.edges) for p in selected.values()), default=None)
    if node is None:
        score, direct, graph_status = None, None, "unmappable"
    else:
        score = sum((Fraction(1, (1 + fan_in[s]) * len(p.edges)) for s, p in selected.items()), Fraction(0))
        direct = sum(len(p.edges) == 1 for p in selected.values())
        graph_status = "reachable" if selected else "mapped_unreachable"
    only_resolved = None if node is None else any(len(p.edges) <= depth for p in primary_paths.get(node, {}).values())
    value = dict(test_id=raw, graph_node_id=node, original_v2_position=position, graph_status=graph_status,
                 specificity_score=float(score) if score is not None else None,
                 score_numerator=score.numerator if score is not None else None,
                 score_denominator=score.denominator if score is not None else None,
                 directly_called_seeds=direct, minimum_distance=minimum,
                 same_module=module in seed_modules,
                 same_package=package in {m.rpartition(".")[0] for m in seed_modules},
                 reachable_seed_count=len(selected) if node else None,
                 reachable_resolved_only_same_depth=only_resolved)
    if identity:
        value.update(identity)
    return value, selected, score


def rank_key(candidate, strategy):
    score = (Fraction(candidate["score_numerator"], candidate["score_denominator"])
             if candidate["score_numerator"] is not None else None)
    tail = candidate["graph_status"] != "reachable"
    # Shared tail: missing graph features remain missing, never imputed. Neither
    # mapped-unreachable nor unmappable gets a priority; only computable features apply.
    return (tail, -score if not tail else Fraction(0),
            -candidate["directly_called_seeds"] if not tail else 0,
            candidate["minimum_distance"] if not tail else 0,
            -int(candidate["same_module"]), -int(candidate["same_package"]),
            candidate["original_v2_position"] if strategy == "C" else candidate["test_id"],
            candidate["test_id"])


def rank_candidates(strategy, candidates):
    return list(candidates) if strategy == "A" else sorted(candidates, key=lambda row: rank_key(row, strategy))


def membership(rank):
    return [*([k for k in BUDGETS if rank <= k]), "ALL"]
