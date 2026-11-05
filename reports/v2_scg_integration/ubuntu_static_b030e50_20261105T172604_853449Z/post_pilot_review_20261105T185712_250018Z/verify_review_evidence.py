"""Read-only verification of saved diagnostics; never imports benchmark code."""
import collections
import hashlib
import json
import pathlib
import subprocess
import tarfile

D = pathlib.Path(__file__).resolve().parent
P = D.parent
F = P / 'paired_frozen'
E = P / 'pilot_20261105T183041_929325Z'
REVIEW = pathlib.Path('/home/sankalp/projects/cis695-v2-scg-paired-review-b030e50')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def write(name, value):
    (D / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


before = read(D / 'protected_inputs_before.json')
errors = []
protected_counts = {}
for label, root in [('frozen', F), ('pilot', E)]:
    actual = {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()}
    expected = before[label + '_files']
    protected_counts[label] = len(actual)
    if actual != expected:
        errors.append({'protected_tree_drift': label,
                       'changed_or_missing': [k for k, v in expected.items() if actual.get(k) != v],
                       'added': sorted(actual.keys() - expected.keys())})
assert sha(F / 'protocol.json') == before['protocol_sha256']
assert sha(E / 'results/results.json') == before['pilot_results_sha256']
assert sha(pathlib.Path(before['plan_path'])) == before['plan_sha256']
sealed_counts = {}
for label, root, name in [('frozen', F, 'artifact_hashes.json'), ('pilot', E, 'evidence_sha256.json')]:
    hashes = read(root / name)
    sealed_counts[label] = len(hashes)
    for rel, expected in hashes.items():
        if sha(root / rel) != expected:
            errors.append({'sealed_artifact_mismatch': str(root / rel)})

tasks = read(F / 'tasks.json')
assert len(tasks) == len({t['instance_id'] for t in tasks}) == 83
task_rows = read(D / 'parameter_exposure_tasks.json')
by_task = {r['instance_id']: r for r in task_rows}
id_rows = read(D / 'parameter_exposure_ids.json')
by_arm = collections.defaultdict(list)
for row in id_rows:
    by_arm[row['instance_id'], row['arm']].append(row)
archive_results = []
all_selected_counts = collections.Counter()
parameterized_ids = collections.Counter()
probe_results = []
evidence_file_count = 0
for task in tasks:
    iid = task['instance_id']
    summary = by_task[iid]
    assert task['runner']['name'] == summary['runner']
    for arm in ['v2', 'scg']:
        selected = read(F / task['selections'][arm])['tests']
        s = summary['arms'][arm]
        assert s['selected_count'] == (None if selected is None else len(selected))
        assert s['selection_unavailable'] == (selected is None)
        all_selected_counts[arm] += len(selected or [])
        parameterized_ids[arm] += sum('[' in tid for tid in selected or [])
        if task['runner']['name'] == 'pytest':
            assert [r['test_id'] for r in by_arm[iid, arm]] == (selected or [])
            exposed = [r['test_id'] for r in by_arm[iid, arm] if r['static_parameterization_evidence']]
            assert exposed == s['exposed_ids']
    archive = pathlib.Path('/home/sankalp/cg_repos/task_archives') / (iid + '.tar')
    digest = sha(archive)
    assert digest == task['base_archive_sha256']
    needed = {}
    def add_evidence(e):
        if 'path' in e and 'sha256' in e:
            assert e['path'] not in needed or needed[e['path']] == e['sha256']
            needed[e['path']] = e['sha256']
        for helper in e.get('helper_chain', []):
            add_evidence(helper)
    for arm in ['v2', 'scg']:
        for row in by_arm[iid, arm]:
            for evidence in row['static_parameterization_evidence']:
                add_evidence(evidence)
    pf = D / 'import_probes' / (iid + '.json')
    if pf.exists():
        config = read(D / 'import_probes' / (iid + '.configuration.json'))
        needed.update(config['source_sha256'])
        needed.update({v['archive_path']: v['sha256'] for v in config['modules'].values() if v.get('archive_path')})
    with tarfile.open(archive) as tar:
        members = {(m.name[2:] if m.name.startswith('./') else m.name): m
                   for m in tar.getmembers() if m.isfile()}
        for rel, expected in needed.items():
            member = members.get(rel) or members['testbed/' + rel]
            data = tar.extractfile(member).read()
            assert hashlib.sha256(data).hexdigest() == expected, (iid, rel)
    evidence_file_count += len(needed)
    archive_results.append({'instance_id': iid, 'archive': str(archive), 'sha256': digest,
                            'matches_frozen': True, 'diagnostic_evidence_source_files_verified': len(needed)})
    if pf.exists():
        obj = read(pf)
        probe = obj['probe']
        assert obj['image_id'] == task['image_binding']['host_image_id']
        assert obj['returncode'] == 0 and obj['mounts'] == []
        assert obj['working_dir'] == '/testbed' and obj['network_mode'] == 'none'
        assert not obj['candidate_patch_applied']
        assert probe['benchmark_files_before'] == probe['benchmark_files_after']
        assert not probe['benchmark_file_changes']
        assert not probe['test_execution_or_collection_invoked']
        assert not probe['benchmark_test_modules_intentionally_imported']
        assert probe['source_sha256'] == config['source_sha256'] and probe['source_hashes_match']
        modules = {k: v for k, v in probe['modules'].items() if v.get('expected_archive_path')}
        assert all(v['origin_is_expected_testbed_path'] and v['source_bytes_match_archive'] for v in modules.values())
        probe_results.append({'instance_id': iid, 'image_id': obj['image_id'], 'python': probe['python'],
                              'sys_path': probe['runner_entry_sys_path'], 'modules': modules,
                              'editable_install_files': probe['path_and_editable_install_files'],
                              'distributions': probe['distributions'],
                              'project_module_hash_matches': len(modules),
                              'common_source_file_hash_matches': len(config['source_sha256']),
                              'benchmark_files_unchanged': len(probe['benchmark_files_before']),
                              'scope_limit': probe['scope_limit']})

worktrees = {}
for label, root in [('original', P.parents[2]), ('review', REVIEW),
                    ('scg', pathlib.Path('/home/sankalp/projects/cis695-callgraph-typeprop'))]:
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    status = subprocess.check_output(['git', '-C', str(root), 'status', '--short'], text=True)
    worktrees[label] = {'path': str(root), 'commit': head, 'status': status}
assert worktrees['review']['commit'] == 'b030e508d849926b9a2260c70e1091adebfee993'
assert not worktrees['review']['status'] and not worktrees['scg']['status']
assert not errors, errors
write('archive_and_static_evidence_recheck.json', archive_results)
write('import_provenance_verified_summary.json', {'tasks': probe_results,
      'project_module_hash_matches': sum(r['project_module_hash_matches'] for r in probe_results),
      'common_source_file_hash_matches': sum(r['common_source_file_hash_matches'] for r in probe_results),
      'retrospective_proof_of_pilot_imports': False,
      'test_collection_or_execution_in_this_review': False})
result = {'protected_files_checked': protected_counts, 'sealed_artifacts_checked': sealed_counts,
          'protocol_sha256': before['protocol_sha256'], 'pilot_results_sha256': before['pilot_results_sha256'],
          'pilot_plan_sha256': before['plan_sha256'], 'protected_file_drift': errors,
          'archives_verified': len(archive_results), 'diagnostic_source_file_references_verified': evidence_file_count,
          'all_selected_id_counts': dict(all_selected_counts), 'explicit_bracket_parameter_ids': dict(parameterized_ids),
          'static_scan_ids_reconciled': len(id_rows), 'static_scan_tasks_reconciled': len(task_rows),
          'worktrees': worktrees, 'benchmark_tests_executed_by_this_utility': 0}
write('final_integrity_verification.json', result)
print(json.dumps(result, indent=2))
