"""POST-HOC ANALYSIS ONLY. Compact overview of extracted.json for classification."""
from __future__ import annotations

import json
from pathlib import Path

NOTICE = (
    "POST-HOC ANALYSIS ONLY. This file uses oracle fields (FAIL_TO_PASS, "
    "PASS_TO_PASS, gold patch, test_patch). It must never feed back into any run."
)

p = Path(__file__).parent / "extracted.json"
data = json.loads(p.read_text())
print(NOTICE)
print("jsonl:", data.get("local_swebench_verified_jsonl"))
print("dataset:", data.get("dataset_source"))
print()

tasks = list(data["tasks"])
if data.get("matplotlib_20676_original_leak_open"):
    tasks.append(data["matplotlib_20676_original_leak_open"])

for t in tasks:
    print("=" * 78)
    print(f"{t['instance_id']}  [{t['group']}]  run={t['source_run']}")
    print(f"missing: {t.get('missing_files')}")
    print(f"csv_disagreements: {t.get('csv_disagreements')}")
    csv = t.get("csv_row") or {}
    print(
        f"csv: decision={csv.get('verifier_decision')} oracle={csv.get('oracle')} "
        f"int={csv.get('integrity')} reg={csv.get('regression')} "
        f"stat={csv.get('static')} repro={csv.get('reproduction')} "
        f"source_run={csv.get('source_run')}"
    )
    ora = t.get("oracle_record") or {}
    print(
        f"oracle: outcome={ora.get('outcome')} resolved={ora.get('resolved')} "
        f"applied={ora.get('patch_applied')} report={ora.get('report_file')}"
    )
    print(f"  F2P fail ({len(ora.get('f2p_failure') or [])}): {ora.get('f2p_failure')}")
    print(f"  F2P ok   ({len(ora.get('f2p_success') or [])}): {ora.get('f2p_success')}")
    print(f"  P2P fail ({len(ora.get('p2p_failure') or [])}): {ora.get('p2p_failure')}")
    print(f"  P2P ok n={len(ora.get('p2p_success') or [])}")
    print(f"official F2P ({len(t.get('official_fail_to_pass') or [])}): {t.get('official_fail_to_pass')}")
    print(f"official P2P n={len(t.get('official_pass_to_pass') or [])}")
    sig = t.get("signals") or {}
    print(
        f"decision={sig.get('decision')} reasons={sig.get('reasons')} "
        f"policy={sig.get('policy_version')}"
    )
    integ = sig.get("integrity") or {}
    print(f"integrity: {integ.get('outcome')} absence={integ.get('absence')} detail={integ.get('detail')}")
    reg = sig.get("regression") or {}
    print(
        f"regression: {reg.get('outcome')} absence={reg.get('absence')} "
        f"detail={reg.get('detail')} findings={reg.get('findings')}"
    )
    st = sig.get("static") or {}
    print(f"static: {st.get('outcome')} absence={st.get('absence')} detail={st.get('detail')}")
    repro = sig.get("reproduction") or {}
    print(
        f"reproduction: {repro.get('outcome')} absence={repro.get('absence')} "
        f"detail={repro.get('detail')} n_frozen={repro.get('n_frozen')}"
    )
    print(f"  frozen_meta: {repro.get('frozen_meta')}")
    print(f"  patched: {repro.get('patched')}")
    print(f"n_selected={sig.get('n_selected')} convention={sig.get('selection_convention')} "
          f"runner={sig.get('selection_runner')}")
    selected = sig.get("selected_tests") or []
    print("selected:")
    for s in selected:
        print(f"  - {s}")
    cov = t.get("coverage") or {}
    print(
        f"coverage: selected={cov.get('n_selected')} p2p={cov.get('n_official_p2p')} "
        f"overlap_p2p={cov.get('n_overlap_p2p')} frac={cov.get('fraction_of_p2p')} "
        f"failing_in_v2={cov.get('failing_in_v2_selection')} "
        f"failing_f2p_in_v2={cov.get('failing_f2p_in_v2')} "
        f"failing_p2p_in_v2={cov.get('failing_p2p_in_v2')}"
    )
    print(f"risk: {sig.get('risk_features')}")
    v4 = t.get("v4_test_sources") or {}
    print(f"v4 files: {list(v4)}")
    issue = t.get("problem_statement") or ""
    print("--- ISSUE (first 2500 chars) ---")
    print(issue[:2500])
    if len(issue) > 2500:
        print(f"... [{len(issue)} chars total]")
    print("--- AGENT PATCH ---")
    print(t.get("agent_patch") or "")
    print("--- GOLD PATCH ---")
    print(t.get("gold_patch") or "")
    print("--- GOLD TEST_PATCH ---")
    print(t.get("gold_test_patch") or "")
    print("--- V4 SOURCES ---")
    for name, src in v4.items():
        print(f"===== {name} =====")
        print(src)
    hr = t.get("harness_report")
    if hr is None:
        print("harness_report: MISSING")
    else:
        keys = list(hr.keys()) if isinstance(hr, dict) else type(hr)
        print(f"harness_report keys: {keys}")
        if isinstance(hr, dict):
            tests = hr.get("tests") or hr.get("test_results") or {}
            if tests:
                print(f"  tests keys: {list(tests)[:20]}")
print("DONE")
