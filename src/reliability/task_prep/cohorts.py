"""Label-free, deterministic nested cohorts and stored status projection."""

from __future__ import annotations

import random
from collections import Counter, defaultdict

from reliability.task_prep.core import (
    FROZEN,
    ROOT,
    RULE,
    PreparationContainer,
    dataset_rows,
    eligibility,
    frozen_metadata,
    inspect_image,
    manifest_ids,
    write_new,
)
from reliability.verifier.admission_reference import JSONProjection
from reliability.verifier.container import image_for


def sample_additions(rows, fixed, pilot, excluded, n=200, seed=695):
    """Hamilton quotas for additions, weighted by the eligible Verified repo mix.

    Capacities respect fixed/pilot exclusions. Reallocate a saturated repo's
    quota proportionally among unsaturated repos; lexicographic ties are stable.
    """
    weights = Counter(r["repo"] for r in rows if r["instance_id"] not in excluded)
    pools = defaultdict(list)
    for row in rows:
        iid = row["instance_id"]
        if iid not in fixed | pilot | excluded:
            pools[row["repo"]].append(iid)
    needed = n - len(fixed)
    if needed < 0 or sum(map(len, pools.values())) < needed:
        raise ValueError("Insufficient eligible non-pilot population")
    quotas = {repo: 0 for repo in weights}
    left = needed
    while left:
        available = sorted(repo for repo in weights if quotas[repo] < len(pools[repo]))
        total = sum(weights[repo] for repo in available)
        shares = {repo: left * weights[repo] / total for repo in available}
        assigned = {
            repo: min(int(shares[repo]), len(pools[repo]) - quotas[repo]) for repo in available
        }
        for repo, count in assigned.items():
            quotas[repo] += count
            left -= count
        for repo in sorted(available, key=lambda repo: (-(shares[repo] % 1), repo)):
            if left and quotas[repo] < len(pools[repo]):
                quotas[repo] += 1
                left -= 1
    rng = random.Random(seed)
    selected = set(fixed)
    for repo in sorted(weights):
        selected.update(rng.sample(sorted(pools[repo]), quotas[repo]))
    return sorted(selected), quotas


def status_evidence(ids):
    root = FROZEN.parents[3] / "runs"
    # Reruns supersede original executions; no outcomes or patch content read.
    runs = ["main_50_a", "main_50_b", "main_2_rerun_mpl", "main_3_rerun_infra"]
    schema = {
        "instance_id": True,
        "termination": True,
        "patch": {"size_bytes": True},
        "infrastructure_error": True,
        "agent_error": True,
    }
    result = []
    for iid in ids:
        records = []
        for name in runs:
            path = root / name / "tasks" / iid / "repair_record.json"
            if path.is_file():
                records.append(
                    {
                        "source": str(path),
                        "fields": JSONProjection(path.read_text()).project(schema),
                    }
                )
        if not records:
            raise ValueError("Missing stored repair status: " + iid)
        final = records[-1]["fields"]
        if not iid.startswith("psf__requests-") and final.get("patch", {}).get("size_bytes") != 0:
            raise ValueError("Expected no final agent patch for " + iid)
        result.append(
            {
                "instance_id": iid,
                "records": records,
                "final": final,
                "exclusion_reason": RULE if iid.startswith("psf__requests-") else "NO_AGENT_PATCH",
            }
        )
    return result


def scan_local(rows):
    checks = []
    for row in sorted(rows, key=lambda r: r["instance_id"]):
        info = inspect_image(image_for(row["instance_id"]))
        if info is None:
            checks.append(
                {
                    "instance_id": row["instance_id"],
                    "status": "UNCHECKED",
                    "reason": "image_not_present",
                }
            )
            continue
        with PreparationContainer(
            row["instance_id"], "", image=info["Id"], experiment_id="task_prep_eligibility"
        ) as container:
            check = eligibility(container, row)
        checks.append(check)
        print(row["instance_id"], check["status"], flush=True)
    return checks


def build(cohort_dir, eligibility_path, status_path):
    rows, _ = dataset_rows()
    by_id = {r["instance_id"]: r for r in rows}
    main = set(manifest_ids(ROOT / "manifests/main_100.csv"))
    frozen = set(frozen_metadata())
    rest = sorted(main - frozen)
    if rest != sorted(manifest_ids(ROOT / "runs/main100_rest17.csv")) or len(rest) != 17:
        raise ValueError("Main/frozen/rest membership mismatch")
    write_new(status_path, status_evidence(rest))
    checks = scan_local(rows)
    lookup = {r["instance_id"]: r for r in checks}
    seven = {i for i in rest if i.startswith("psf__requests-")}
    if len(seven) != 7 or any(lookup[i]["status"] != RULE for i in seven):
        raise ValueError("STOP: automatic eligibility failed to flag all seven requests images")
    write_new(eligibility_path, {"rule": RULE, "tasks": checks})
    excluded = {i for i in by_id if i.startswith("psf__requests-")} | {
        c["instance_id"] for c in checks if c["status"] == RULE
    }
    fixed = main - excluded
    if len(fixed) != 93 or not frozen <= fixed:
        raise ValueError("STOP: unexpected main cohort eligibility")
    if any(lookup[i]["status"] != "ELIGIBLE" for i in fixed):
        raise ValueError("STOP: an available main image remains unchecked")
    pilot = set(manifest_ids(ROOT / "manifests/pilot.csv"))
    twohundred, quotas = sample_additions(rows, fixed, pilot, excluded)
    population = sorted(set(by_id) - excluded)
    rule = (
        "Start with the 93 main-study eligible tasks; add 107 with seed 695, Hamilton largest-remainder quotas "
        "weighted by the non-excluded Verified repo mix, capacity constrained after fixed and pilot exclusions; "
        "sample sorted IDs with random.Random(695), repos in sorted order."
    )
    for name, ids in [
        ("main100", sorted(fixed)),
        ("verified200", twohundred),
        ("verified500", population),
    ]:
        excluded_here = sorted(main & excluded) if name == "main100" else sorted(excluded)
        value = {
            "schema": "task_cohort/1",
            "cohort": name,
            "instance_ids": ids,
            "eligibility": {i: lookup[i]["status"] for i in ids},
            "excluded": [
                {
                    "instance_id": i,
                    "rule": RULE,
                    "evidence_status": lookup[i]["status"],
                    "reason": "observed unmaskable copy"
                    if lookup[i]["status"] == RULE
                    else "requests family precaution; check on pull",
                }
                for i in excluded_here
            ],
            "pilot_instances": sorted(set(ids) & pilot),
            "repo_counts": dict(sorted(Counter(by_id[i]["repo"] for i in ids).items())),
            "sampling_rule": rule
            if name == "verified200"
            else "fixed eligible main cohort"
            if name == "main100"
            else "all Verified IDs not known ineligible; unchecked images are rechecked on pull",
            "seed": 695 if name == "verified200" else None,
        }
        if name == "verified200":
            value["addition_repo_quotas"] = quotas
        write_new(cohort_dir / (name + ".json"), value)
    return checks
