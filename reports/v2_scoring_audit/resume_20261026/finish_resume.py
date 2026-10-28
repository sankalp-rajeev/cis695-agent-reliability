"""Post-hoc metrics and report; never change diagnostic/scoring outputs."""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('analysis_resume',OUT/'analyze_resume.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
run=a.run


def ratio(n,d):return n/d if d else None


def main():
    assert (OUT/'diagnostics_frozen_before_labels.json').exists()
    assert json.loads((OUT/'parser_tests.json').read_text())['returncode']==0
    # Only headline correctness labels are accessed, after diagnosis is frozen.
    # No gold patch, grader log or official test list is ever read by this resume.
    with (run.ROOT/'docs/results_100.csv').open() as f:
        rows={r['instance_id']:r for r in csv.DictReader(f) if r['instance_id'] in run.INPUTS}
    assert len(rows)==8
    labels={iid:('right' if r['oracle']=='resolved' else 'wrong') for iid,r in rows.items()}
    assert all(r['oracle'] in {'resolved','unresolved'} for r in rows.values())
    run.save(OUT/'posthoc_metric_labels.json',{
        'labels':labels,'source':'docs/results_100.csv: oracle field only',
        'purpose':'Post-hoc metric grouping only; diagnosis, selections, parser and scoring outputs already frozen',
        'gold_or_official_test_lists_read':False,
        'diagnostic_freeze_sha256':run.sha((OUT/'diagnostics_frozen_before_labels.json').read_bytes())})
    comparison=list(csv.DictReader((OUT/'old_vs_fixed.csv').open()))
    detailed=json.loads((OUT/'parser_comparison.json').read_text())
    stability=list(csv.DictReader((OUT/'regression_reruns.csv').open()))
    coverage=list(csv.DictReader((OUT/'selected_coverage.csv').open()))
    subset=sorted(detailed)
    usable=sorted(iid for iid,d in detailed.items() if d['usable'])
    originals={r['instance_id']:r['original_study_v2'] for r in comparison}
    versions={'committed_original_same_new_raw_subset':originals,
              'old_parser_replay_same_raw':{iid:d['old']['v2_label'] for iid,d in detailed.items()},
              'proposed_parser_replay_same_raw':{iid:d['fixed']['v2_label'] for iid,d in detailed.items()}}
    metrics=[]
    for population,ids in [('paired_new_raw_subset',subset),('same_subset_raw_complete_usable_only',usable)]:
        for version,outcomes in versions.items():
            right=[iid for iid in ids if labels[iid]=='right']
            wrong=[iid for iid in ids if labels[iid]=='wrong']
            failures=[iid for iid in ids if outcomes[iid]=='FAIL']
            wrong_fail=[iid for iid in failures if labels[iid]=='wrong']
            false_positive=[iid for iid in failures if labels[iid]=='right']
            usable_right=[iid for iid in right if iid in usable]
            usable_wrong=[iid for iid in wrong if iid in usable]
            precision=ratio(len(wrong_fail),len(failures))
            metrics.append({'population':population,'version':version,'subset_size':len(ids),'subset_ids':ids,
                'right_count':len(right),'wrong_count':len(wrong),
                **{v:sum(outcomes[iid]==v for iid in ids) for v in ('PASS','FAIL','NOT_AVAILABLE')},
                'raw_usable_count':sum(iid in usable for iid in ids),
                'FAIL_precision_wrong_numerator':len(wrong_fail),'FAIL_precision_FAIL_denominator':len(failures),
                'FAIL_precision':precision,'false_positive_numerator':len(false_positive),
                'all_right_denominator':len(right),'FPR_over_all_right_in_population':ratio(len(false_positive),len(right)),
                'usable_false_positive_numerator':sum(iid in usable for iid in false_positive),
                'usable_right_denominator':len(usable_right),
                'FPR_over_usable_right':ratio(sum(iid in usable for iid in false_positive),len(usable_right)),
                'wrong_detected_numerator':len(wrong_fail),'all_wrong_denominator':len(wrong),
                'wrong_detection_rate':ratio(len(wrong_fail),len(wrong)),
                'usable_wrong_denominator':len(usable_wrong),
                'population_wrong_base_rate':ratio(len(wrong),len(ids)),
                'requested_global_wrong_numerator':14,'requested_global_patch_denominator':83,
                'requested_global_wrong_rate':14/83,
                'FAIL_precision_minus_global_base_rate':precision-14/83 if precision is not None else None,
                'usable_definition':run.PROTOCOL['usable_v2_exact_user_definition'],
                'limitation':'Targeted, incomplete sample; new rerun replay is not historical rescoring or an all-83 correction'})
    a.write_csv('metrics_before_after.csv',metrics)
    per_repo=[]
    for version,outcomes in versions.items():
        for repo in sorted({rows[iid]['repo'] for iid in subset}):
            for label in ('right','wrong'):
                ids=[iid for iid in subset if rows[iid]['repo']==repo and labels[iid]==label]
                per_repo.append({'version':version,'repo':repo,'correctness':label,'count':len(ids),
                    'raw_usable':sum(iid in usable for iid in ids),
                    **{v:sum(outcomes[iid]==v for iid in ids) for v in ('PASS','FAIL','NOT_AVAILABLE')},
                    'population':'same three paired new-raw patches; no result imputed for five blocked targets'})
    a.write_csv('metrics_by_repo.csv',per_repo)
    run.save(OUT/'raw_evidence_subset.json',{
        'new_paired_raw_size':len(subset),'new_paired_raw_ids':subset,
        'raw_complete_usable_size':len(usable),'raw_complete_usable_ids':usable,
        'historical_raw_rescoring_size':0,'historical_raw_rescoring_ids':[],
        'historical_reason':'The existing 83-row risk screen found no sufficient historical paired pre-parser raw evidence. Parsed baseline caches and aggregate regression records are not valid raw rescoring inputs. New observations cannot retroactively repair historical outcomes.',
        'authorized_targets_blocked':sorted(set(run.INPUTS)-set(subset)),
        'outside_authorized_targets_rerun':0,
        'same_subset_original_ids':subset})
    attempts=[]
    batch_processes=0
    for phase in ('phase2','phase3'):
        for path in (OUT/phase).rglob('attempt.json'):
            r=json.loads(path.read_text());r['phase']=phase
            attempts.append(r)
            batch_processes+=sum(e['event']=='start' for e in a.read_events(path.parent))
    counts=Counter(r['diagnostic_label'] for r in stability)
    missing=[r for r in coverage if r['base_recorded_outcome']=='False' or r['patched_recorded_outcome']=='False']
    original_targets=Counter(originals.values())
    # Preserve sources, protocol, selections and all previous audit files.
    run.verify_frozen()
    for path,digest in json.loads((OUT/'raw_collection.sha256.json').read_text()).items():
        assert run.sha((OUT/path).read_bytes())==digest,path
    completion={'status':'partial: all feasible authorized execution complete; five local images missing',
        'target_count':8,'initial_patch_pairs_completed':len(subset),
        'initial_full_selection_passes':sum(r['phase']=='phase2' for r in attempts),
        'individual_confirmation_attempts':sum(r['phase']=='phase3' for r in attempts),
        'concrete_confirmation_candidates':len(stability),'runner_subprocesses':batch_processes,
        'timeout_attempts':sum(r['driver_state']=='timeout' for r in attempts),
        'stable_candidates':sum(r['stability']=='STABLE' for r in stability),
        'flaky_candidates':sum(r['stability']=='FLAKY' for r in stability),
        'candidate_labels':dict(counts),'new_raw_rescoring_subset_size':len(subset),
        'historical_raw_rescoring_subset_size':0,'raw_complete_usable_subset_size':len(usable),
        'parser_unit_tests':4,'parser_unit_tests_passed':True,
        'old_vs_fixed_verdict_changes':sum(d['old']['v2_label']!=d['fixed']['v2_label'] for d in detailed.values()),
        'production_and_old_artifact_hashes_unchanged':True,
        'oracle_usage':'headline correctness labels for post-hoc metrics after frozen diagnostics only',
        'gold_grader_official_tests_read':False,'network_pull_build_install':False,
        'selector_callgraph_work':False,'commits':0,
        'utc':run.datetime.now(run.timezone.utc).isoformat()}
    run.save(OUT/'completion.json',completion)
    lines=['# Frozen V2 scoring audit — resumed execution','',
      '[confirmed] The saved `../protocol.json` and frozen inputs were verified by SHA-256 and used unchanged. Previous audit files and production code are preserved. New files are confined to this resume directory. No selector/call-graph work, network, image pull/build, dependency installation, model, agent or commit occurred.','',
      '[confirmed] **Three of eight authorized pairs ran; five are blocked by missing local frozen images.** Docker is reachable. Missing images: django-12209, django-13297, django-14140, django-14631 and sphinx-10435. They were not replaced or downloaded and their missing rerun results were not relabeled NOT_AVAILABLE. The original eight labels remain '+str(dict(original_targets))+'.','',
      '| Phase | Result |','|---|---|',
      '| 2 | [confirmed] Six full-selection passes, one base and one patched per available patch; raw bytes and batch events persisted before parsing |',
      '| 3 | [confirmed] Five concrete candidates; 30 additional individual attempts, three per tree/test; every candidate has four observations per tree |',
      '| 4 | [confirmed] Old and unchanged proposed parser applied offline to identical Phase-2 logs with identical confirmation evidence |',
      '| 5 | [confirmed] Four actual-format parser tests pass; three new paired-raw replays; zero valid historical raw re-scores |',
      '| 6 | [confirmed] Matched three-patch metrics and matched one-patch usable metrics; no corrected all-83 estimate |','',
      '## Paired observations','',
      '| Patch | Raw-covered selected IDs, base/patch | Old parsed IDs, base/patch | Proposed parsed IDs, base/patch | Committed / old replay / proposed replay | Usable |',
      '|---|---|---|---|---|---|']
    for iid in subset:
        d=detailed[iid];o=d['old'];f=d['fixed'];n=len(run.INPUTS[iid]['selected_tests'])
        lines.append(f"| {iid} | {d['base_raw_coverage']}/{n}; {d['patched_raw_coverage']}/{n} | {o['base_parsed_selected']}; {o['patched_parsed_selected']} | {f['base_parsed_selected']}; {f['patched_parsed_selected']} | {originals[iid]} / {o['v2_label']} / {f['v2_label']} | {d['usable']} |")
    lines += ['',
      '[confirmed] The proposal empirically fixes admission of 26 parameter families for pylint-6528 and 13 for pylint-7277, on each tree. It changes zero patch verdicts. The copied proposal is not applied to production. Its family-level aggregation can still conceal different failing concrete cases when a family fails on both trees [inferred limitation, not demonstrated here]. No Django raw format was observed, so Django parser tests and suffix/multiline-ID hypotheses remain unresolved.','',
      '## Stability and diagnosis','',
      '| Patch/test | Base initial + repeats | Patched initial + repeats | Classification |','|---|---|---|---|']
    for r in stability:
        lines.append(f"| {r['instance_id']} / `{r['raw_test_id']}` | {r['base_initial_outcome']} + {r['base_repeat_outcomes']} | {r['patched_initial_outcome']} + {r['patched_repeat_outcomes']} | [confirmed] {r['stability']}; {r['diagnostic_label']} |")
    lines += ['',
      '[confirmed] There is one stable real regression: pytest `TestPaste.test_create_new_paste`. The old test at `testing/test_pastebin.py:131` expects a Python lexer; the candidate sends `lexer=text`. Base passes 4/4 observations and patched fails 4/4. Its headline post-hoc label is right, so this is a V2 existing-test design limit in this environment, not a parser bug. [inferred] It is consistent with the historical false positive, but absent historical raw logs and image digests prevent proving historical causation.','',
      '[confirmed] In each pylint case, `TestCallbackOptions.test_generate_toml_config` and `test_generate_toml_config_disable_symbolic_names` fail on both trees 4/4 times; observed logs report TOMLKitError from adding a table to a dotted key. The base-failure rule excludes these four observed failures. No initially differing case was omitted from confirmation selection. Zero candidates are flaky; no timeout occurred.','',
      '[unresolved] These observed pre-existing failures do not establish why the headline wrong pylint patches passed the historical verifier. No official/gold failing-test list was used to diagnose them. Django-13297 remains UNKNOWN because its image is missing. Do not equate evidence of baseline absorption with proof that it absorbed the official failing test.','',
      '## Denominators, missing outcomes and metrics','',
      '[confirmed] Usable V2 means: **'+run.PROTOCOL['usable_v2_exact_user_definition']+'** The parser-independent raw coverage flag was fixed before comparison. Missing IDs and process-level timeouts do not manufacture per-test outcomes. Completed responsible batches and concrete emitted outcomes are required for selected families. ERROR/SKIP are recorded outcomes; at least one concrete PASS/FAIL/SKIP must have run per tree. Only pylint-7277 qualifies.','',
      '[confirmed] Missing on both trees:']
    lines += [f"- `{r['instance_id']}`: `{r['selected_id']}`" for r in missing]
    lines += ['',
      '[confirmed] Pytest reports its three missing IDs as not found; pylint-6528 reports a not-found selection too. No missing ID is assigned a raw PASS. Partial aggregate PASS is nevertheless allowed by the unchanged production scoring rule, as demonstrated by pylint-6528. This establishes incomplete-evidence PASS, not an individual missing test being classified PASS.','',
      '| Population/version | Patches (right/wrong) | PASS / FAIL / NOT_AVAILABLE | FAIL precision, wrong/FAIL | FPR, FAIL-right/all-right | FPR on usable right |',
      '|---|---|---|---|---|---|']
    for r in metrics:
        precision=f"{r['FAIL_precision_wrong_numerator']}/{r['FAIL_precision_FAIL_denominator']}"
        fpr=f"{r['false_positive_numerator']}/{r['all_right_denominator']}"
        usable_fpr=f"{r['usable_false_positive_numerator']}/{r['usable_right_denominator']}"
        lines.append(f"| {r['population']} / {r['version']} | {r['subset_size']} ({r['right_count']}/{r['wrong_count']}) | {r['PASS']} / {r['FAIL']} / {r['NOT_AVAILABLE']} | {precision} | {fpr} | {usable_fpr} |")
    lines += ['',
      '[confirmed] All three versions on the matched new-raw subset yield PASS=2, FAIL=1, NOT_AVAILABLE=0. Proposed FAIL precision is **0/1 = 0%**, versus the requested global wrong-patch base rate **14/83 = 16.8675%** and this targeted subset\'s own wrong-patch rate **2/3 = 66.6667%**. False-positive rate over the subset\'s right patches is **1/1 = 100%**. On the single usable patch, FAIL precision is **0/0 undefined**, usable-right FPR is **0/0 undefined**, and wrong detection is **0/1**. These deliberately selected, incomplete observations cannot estimate global precision lift or a corrected global false-positive rate.','',
      '[confirmed] Historical valid raw re-scoring subset: **0 patches, []**. New paired-raw replay subset: **3**, explicitly listed in `raw_evidence_subset.json`; original committed metrics are shown on those identical three IDs beside both replays. The existing 83-row screen provides parsed/aggregate records, not qualifying paired historical raw logs. All 75 non-target patches remain unexecuted. Do not replace historical study outcomes with new-environment replays.','',
      '## Environment and practical limits','',
      '[confirmed] All observed images run Python 3.9.20; pylint runner is pytest 7.4.4 and pytest-5809 raw headers identify pytest 4.6.6.dev9+g8aba863a6. Current image IDs/RepoDigests, observed commits, patch hashes, frozen selections, batch exits and durations are recorded in `environment_sanity.csv` and raw preflight files. Full-pass and individual timeouts are 300 s; initial pair budget 600 s. All observed initial pairs complete well within budget.','',
      '[unresolved] Historical image digest, historical runner version and independently recorded historical base commit are absent from frozen inputs. Current HEAD was recorded and frozen candidate applicability checked, but historical identity is not proved. STABLE describes four repeated observations per side in the current image, not demonstrated equivalence to the original study environment.','',
      '[inferred] This evidence does not support strengthening V2 into a correctness gate: one stable old-test regression occurs on a right patch, two wrong patches still receive PASS, and only one replay meets the predeclared raw-completeness requirement. This is an interpretation of the fixed protocol, not a policy or selector change.','',
      '[confirmed] Preservation checks passed for all prior audit files, production sources, frozen inputs and newly captured raw logs. Commands are in `commands.jsonl`, raw logs/events in `phase2/` and `phase3/`, and offline parser checks in `parser_tests.stderr`. Execution stopped after the authorized audit; five missing images remain the only execution blocker.','']
    (OUT/'report.md').write_text('\n'.join(lines))
    output_manifest={str(p.relative_to(OUT)):run.sha(p.read_bytes()) for p in OUT.rglob('*') if p.is_file()}
    run.save(OUT/'outputs.sha256.json',output_manifest)
    print(json.dumps(completion,indent=2))


if __name__=='__main__':main()
