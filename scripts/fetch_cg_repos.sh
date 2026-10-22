#!/usr/bin/env bash
# Fetch public base repositories and archive exact task commits. No repo code runs.
# Run this yourself on a host with network access. Do not run through a sandbox
# network override. --plan-only reads cached metadata and writes pending records.
set -euo pipefail

CG_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CG_REPO_ROOT="${CG_REPO_ROOT:-$HOME/cg_repos}"
CG_PYTHON="${CG_PYTHON:-$CG_PROJECT_ROOT/.venv/bin/python}"
CG_DATASET_ARROW="${CG_DATASET_ARROW:-$HOME/.cache/huggingface/datasets/SWE-bench___swe-bench_verified/default/0.0.0/78f471bf655a3137b2e8a75af1501690ec009ec3/swe-bench_verified-test.arrow}"
CG_PLAN_ONLY=0
case "${1:-}" in
  --plan-only) CG_PLAN_ONLY=1; shift ;;
  --help|-h)
    cat <<'HELP'
Usage: bash scripts/fetch_cg_repos.sh [--plan-only]

Defaults: clone cache ~/cg_repos; cached SWE-bench Verified Arrow; project venv.
Overrides: CG_REPO_ROOT, CG_DATASET_ARROW, CG_PYTHON.

Clones all 12 cached benchmark repos once, using --filter=blob:none --no-checkout.
The 83 non-empty headline tasks span 11 repos; requests has no headline archives.
Verifies exact task commits; writes git-archive tar files under the external cache;
marks managed clones read-only only after every archive succeeds; records heads,
commits, archive hashes and input/code hashes in reports/callgraph_selection/inputs.json.

No source extraction/import/install/test execution, graph construction, Docker,
selectors, gold comparisons, project git staging/committing/pushing, or study writes.
--plan-only does no network access and does not create the external clone cache.
HELP
    exit 0 ;;
esac
if (( $# )); then
  echo 'Unexpected arguments. Use --help.' >&2
  exit 2
fi
export PYTHONDONTWRITEBYTECODE=1
export GIT_TERMINAL_PROMPT=0
export GIT_OPTIONAL_LOCKS=0
unset PYTHONPATH

"$CG_PYTHON" -B - "$CG_PROJECT_ROOT" "$CG_DATASET_ARROW" "$CG_REPO_ROOT" "$CG_PLAN_ONLY" <<'PY'
import csv, hashlib, json, re, subprocess, sys
from collections import Counter
from pathlib import Path
import pyarrow
import pyarrow.ipc as ipc

project, arrow, cache = (Path(s).expanduser().resolve() for s in sys.argv[1:4])
plan_only = sys.argv[4] == '1'
out = project / 'reports/callgraph_selection'
if cache == project or project in cache.parents or cache == Path('/'):
    raise SystemExit('CG_REPO_ROOT must be a dedicated directory outside the project.')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def git_read(*args):
    return subprocess.check_output(
        ['git', '--no-optional-locks', '-C', str(project), *args], text=True).strip()

design = out / 'design.md'
design_commit = git_read('log', '-1', '--format=%H', '--', 'reports/callgraph_selection/design.md')
registered = subprocess.check_output([
    'git', '--no-optional-locks', '-C', str(project), 'show',
    design_commit + ':reports/callgraph_selection/design.md'])
if registered != design.read_bytes():
    raise SystemExit('Working design differs from its committed pre-registration.')
cohort_path = project / 'reports/v2_diagnostic/patches.csv'
with cohort_path.open(newline='') as stream:
    # Membership is already frozen. Project identities only; never inspect labels.
    cohort = [{k: row[k] for k in ('instance_id', 'source_run')}
              for row in csv.DictReader(stream)]
if len(cohort) != 83 or len({r['instance_id'] for r in cohort}) != 83:
    raise SystemExit('Expected exactly 83 unique frozen headline task identities.')
with arrow.open('rb') as stream:
    # Only the public execution metadata is materialized into Python objects.
    metadata = ipc.open_stream(stream).read_all().select(['instance_id', 'repo', 'base_commit'])
if metadata.num_rows != 500:
    raise SystemExit('Expected the existing 500-task SWE-bench Verified cache.')
lookup = {row['instance_id']: row for row in metadata.to_pylist()}
if len(lookup) != 500:
    raise SystemExit('Duplicate IDs in cached benchmark metadata.')
repo_names = sorted({row['repo'] for row in lookup.values()})
if len(repo_names) != 12:
    raise SystemExit('Expected 12 benchmark repositories; review cache before fetching.')
for repo in repo_names:
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise SystemExit('Unsafe repository identifier.')
    if any(part in ('.', '..') for part in repo.split('/')):
        raise SystemExit('Unsafe repository component.')
tasks = []
for member in cohort:
    entry = lookup[member['instance_id']]
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', entry['instance_id']):
        raise SystemExit('Unsafe instance identifier.')
    if not re.fullmatch(r'[0-9a-f]{40}', entry['base_commit']):
        raise SystemExit('Expected full base commit SHA.')
    repo_path = cache / entry['repo'].replace('/', '__')
    tasks.append({**member, 'repo': entry['repo'], 'base_commit': entry['base_commit'],
                  'repo_path': str(repo_path), 'base_commit_exists': None,
                  'commit_verification_status': 'pending_user_fetch',
                  'archive_path': str(cache / 'task_archives' / (entry['instance_id'] + '.tar')),
                  'archive_sha256': None, 'archive_status': 'not_created',
                  'patch_status': 'not_reconstructed_fetch_stop',
                  'graph_status': 'not_attempted_fetch_stop'})
counts = Counter(t['repo'] for t in tasks)
repositories = [{'repo': repo, 'repo_path': str(cache / repo.replace('/', '__')),
                 'url': 'https://github.com/' + repo + '.git', 'head': None,
                 'clone_status': 'pending_user_fetch', 'headline_tasks': counts[repo],
                 'read_only': None} for repo in repo_names]
code_paths = [project / 'scripts/fetch_cg_repos.sh', design,
              project / 'src/reliability/verifier/patch.py',
              project / 'src/reliability/verifier/selection.py']
plan = {'stage': 'base_acquisition', 'status': 'plan_only' if plan_only else 'fetch_pending',
        'design_commit': design_commit, 'cache_root': str(cache),
        'population_tasks': len(tasks), 'headline_repositories': len(counts),
        'clone_repositories': len(repo_names), 'repositories': repositories, 'tasks': tasks,
        'metadata_columns_used': ['instance_id', 'repo', 'base_commit'],
        'cohort_columns_used': ['instance_id', 'source_run'],
        'input_sha256': {str(p): digest(p) for p in (arrow, cohort_path, design)},
        'code_sha256': {str(p): digest(p) for p in code_paths},
        'pyarrow_version': pyarrow.__version__, 'network_attempted_by_script': False,
        'tests_executed': False, 'graphs_constructed': 0,
        'note': '83 headline tasks span 11 repos. The 12th clone is psf/requests; '
                'it has no headline task archive. No oracle fields or gold patches are used.'}
out.mkdir(parents=True, exist_ok=True)
(out / 'inputs.json').write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n')
if not plan_only:
    cache.mkdir(parents=True, exist_ok=True)
    (cache / '.cg_fetch_plan.json').write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n')
    with (cache / '.cg_repositories.tsv').open('w') as stream:
        for repo in repositories:
            stream.write('\t'.join((repo['repo'], repo['url'], repo['repo_path'])) + '\n')
    with (cache / '.cg_tasks.tsv').open('w') as stream:
        for task in tasks:
            stream.write('\t'.join((task['instance_id'], task['repo_path'],
                                    task['base_commit'], task['archive_path'])) + '\n')
print(f"Prepared {len(tasks)} task commits across {len(counts)} headline repos; {len(repo_names)} clones planned.")
PY

if (( CG_PLAN_ONLY )); then
  echo 'Plan only: no network, clones, archives, or external-cache writes performed.'
  exit 0
fi

CG_REPO_ROOT="$("$CG_PYTHON" -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["cache_root"])' "$CG_PROJECT_ROOT/reports/callgraph_selection/inputs.json")"
command -v flock >/dev/null || { echo 'flock is required for acquisition locking.' >&2; exit 1; }
exec 9>"$CG_REPO_ROOT/.cg_fetch.lock"
flock -n 9 || { echo 'Another acquisition is using this cache.' >&2; exit 1; }
mkdir -p -- "$CG_REPO_ROOT/task_archives" "$CG_REPO_ROOT/.cg_metadata"
CG_ARCHIVE_TMP=''
trap 'if [[ -n "$CG_ARCHIVE_TMP" ]]; then rm -f -- "$CG_ARCHIVE_TMP"; fi' EXIT

cg_git() {
  git -c core.fsmonitor=false -c core.hooksPath=/dev/null "$@"
}

while IFS=$'\t' read -r cg_repo cg_url cg_path; do
  if [[ -L "$cg_path" ]]; then
    echo "Refusing a symlink as a managed clone: $cg_path" >&2
    exit 1
  fi
  if [[ ! -e "$cg_path" ]]; then
    cg_git clone --filter=blob:none --no-checkout -- "$cg_url" "$cg_path"
    printf '%s\n' "$cg_repo" > "$cg_path/.cg_fetch_repository"
  fi
  if [[ ! -f "$cg_path/.cg_fetch_repository" ]] || [[ "$(cat -- "$cg_path/.cg_fetch_repository")" != "$cg_repo" ]]; then
    echo "Refusing to reuse an unmanaged directory: $cg_path" >&2
    exit 1
  fi
  if [[ "$(cg_git -C "$cg_path" config --get remote.origin.url)" != "$cg_url" ]]; then
    echo "Origin mismatch in $cg_path" >&2
    exit 1
  fi
  cg_git -C "$cg_path" rev-parse --verify 'HEAD^{commit}' > "$CG_REPO_ROOT/.cg_metadata/${cg_repo//\//__}.head"
done < "$CG_REPO_ROOT/.cg_repositories.tsv"

while IFS=$'\t' read -r cg_instance cg_path cg_base cg_archive; do
  # No shallow clone: historical commits should normally already be present.
  # If a commit is absent, request only that exact SHA from the same origin.
  if ! GIT_NO_LAZY_FETCH=1 cg_git -C "$cg_path" cat-file -e "${cg_base}^{commit}" 2>/dev/null; then
    cg_git -C "$cg_path" fetch --filter=blob:none origin "$cg_base"
  fi
  cg_actual="$(GIT_NO_LAZY_FETCH=1 cg_git -C "$cg_path" rev-parse --verify "${cg_base}^{commit}")"
  [[ "$cg_actual" == "$cg_base" ]] || { echo "Commit mismatch: $cg_instance" >&2; exit 1; }
  printf '%s\n' "$cg_actual" > "$CG_REPO_ROOT/.cg_metadata/$cg_instance.commit"
  CG_ARCHIVE_TMP="$(mktemp "$CG_REPO_ROOT/task_archives/.${cg_instance}.XXXXXX.tar")"
  # Promisor blobs may be fetched here by Git. No worktree is checked out and
  # no repository code is run. All required blobs are hydrated before chmod.
  cg_git -C "$cg_path" archive --format=tar --prefix=testbed/ --output="$CG_ARCHIVE_TMP" "$cg_base"
  [[ "$(cg_git get-tar-commit-id < "$CG_ARCHIVE_TMP")" == "$cg_base" ]] || {
    echo "Archive commit mismatch: $cg_instance" >&2; exit 1;
  }
  if [[ -e "$cg_archive" ]]; then
    cmp -s -- "$CG_ARCHIVE_TMP" "$cg_archive" || {
      echo "Existing archive differs; refusing to overwrite: $cg_instance" >&2; exit 1;
    }
    rm -f -- "$CG_ARCHIVE_TMP"
  else
    mv -- "$CG_ARCHIVE_TMP" "$cg_archive"
  fi
  CG_ARCHIVE_TMP=''
  echo "Archived $cg_instance at $cg_base"
done < "$CG_REPO_ROOT/.cg_tasks.tsv"

# All commit/blob/archive work is complete. Freeze only our managed clones,
# not the user's home, the cache parent, archives, or any other repository.
while IFS=$'\t' read -r cg_repo cg_url cg_path; do
  chmod -R a-w -- "$cg_path"
done < "$CG_REPO_ROOT/.cg_repositories.tsv"

"$CG_PYTHON" -B - "$CG_PROJECT_ROOT" "$CG_REPO_ROOT" <<'PY'
import csv, hashlib, json, sys
from pathlib import Path
project, cache = map(Path, sys.argv[1:3])
plan = json.loads((cache / '.cg_fetch_plan.json').read_text())
def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
for repo in plan['repositories']:
    repo['head'] = (cache / '.cg_metadata' / (repo['repo'].replace('/', '__') + '.head')).read_text().strip()
    repo['clone_status'] = 'available'
    repo['read_only'] = all(not (p.stat().st_mode & 0o222)
                            for p in [Path(repo['repo_path']), *Path(repo['repo_path']).rglob('*')]
                            if not p.is_symlink())
    if not repo['read_only']:
        raise SystemExit('Managed clone still has writable entries.')
for task in plan['tasks']:
    actual = (cache / '.cg_metadata' / (task['instance_id'] + '.commit')).read_text().strip()
    if actual != task['base_commit']:
        raise SystemExit('Recorded task commit mismatch.')
    task.update(base_commit_exists=True, commit_verification_status='verified',
                archive_sha256=digest(Path(task['archive_path'])), archive_status='created_and_commit_verified',
                graph_status='not_attempted_fetch_only')
for path, expected in {**plan['input_sha256'], **plan['code_sha256']}.items():
    if digest(Path(path)) != expected:
        raise SystemExit('Code/input changed during acquisition: ' + path)
plan.update(status='archives_ready_no_graphs_built', network_attempted_by_script=True)
(project / 'reports/callgraph_selection/inputs.json').write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n')
inventory = project / 'reports/callgraph_selection/base_feasibility.csv'
if inventory.is_file():
    with inventory.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    tasks = {t['instance_id']: t for t in plan['tasks']}
    for row in rows:
        task = tasks[row['instance_id']]
        row.update(source_kind='local_partial_clone_archive', source_path=task['repo_path'],
                   source_status='verified_base_commit_and_archive',
                   reason='Archive ready; graph construction has not run.',
                   graph_status='not_attempted_fetch_only')
    with inventory.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
print('Recorded 12 repo HEADs and 83 verified base commits/archive hashes; clones are read-only.')
PY
echo 'Acquisition complete. Archives remain outside the project; no graph/selector/test/oracle was run.'
