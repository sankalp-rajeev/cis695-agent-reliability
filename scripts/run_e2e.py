#!/usr/bin/env python3
"""Serial repair → V1 → native selection → guarded V2 → V3 → V4 → decision.

Correctness evaluation is a separate operation after this run is sealed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from pathlib import Path

os.environ.setdefault('MSWEA_SILENT_STARTUP', '1')
os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')

import yaml

from reliability.agent.freeze import freeze_patch
from reliability.e2e_runner import git, run_batch, validate_mode
from reliability.env import assert_clean_interpreter
from reliability.provider_spend import ProviderLedger
from reliability.provider_errors import ProviderTransientError
from reliability.study_inputs import patch_digest, verification_source
from reliability.umgpt_spend import BudgetCap
from reliability.verifier.admission_reference import JSONProjection
from reliability.verifier.run_v1_4_1 import (
    DEFAULT_VERIFIER_CONFIG, default_reproduction_setup, load_v2_settings, verify_task,
)
from reliability.verifier.reproduction_reuse import V4Reuse
from reliability.verifier.source_integrity import SourceIntegrityError
from reliability.verifier.task_specs import ROOT, load_registries, require_hash, sha, write
from reliability.verifier.generic_health import rules_stamp


def manifest_ids(path):
    raw = path.read_text()
    if raw.lstrip().startswith('['):
        if raw.lstrip()[1:].lstrip().startswith(('"', ']')):
            ids = json.loads(raw)
        else:
            ids = [row['instance_id'] for row in JSONProjection(raw).project({'*': {'instance_id': True}})]
    elif raw.lstrip().startswith('{'):
        ids = JSONProjection(raw).project({'instance_ids': True})['instance_ids']
    elif raw.splitlines()[0].strip() == 'instance_id':
        reader = csv.DictReader(io.StringIO(raw))
        if reader.fieldnames != ['instance_id']:
            raise ValueError('Manifest must contain instance IDs only')
        ids = [row['instance_id'] for row in reader]
    else:
        ids = [line.strip() for line in raw.splitlines() if line.strip() and not line.startswith('#')]
    if not ids or len(ids) != len(set(ids)) or not all(isinstance(i, str) and
        re.fullmatch(r'[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+', i) for i in ids):
        raise ValueError('Manifest IDs must be nonempty, safe and unique')
    return ids


def frozen_inputs(root, ids):
    """Resolve supplied patch bytes and bind each one before starting the batch."""
    root = root.resolve()
    metadata = {}
    if (root / 'tasks.json').is_file():
        for row in JSONProjection((root / 'tasks.json').read_text()).project({'*': {
            'instance_id': True, 'patch_path': True, 'patch_sha256': True}}):
            metadata[row['instance_id']] = row
    result = {}
    for iid in ids:
        row = metadata.get(iid)
        if row:
            path = (root / row['patch_path']).resolve()
        else:
            candidates = [root / 'tasks' / iid / 'patch.diff', root / iid / 'patch.diff',
                          root / (iid + '.patch'), root / 'patches' / (iid + '.patch'),
                          root / 'patches' / (iid + '.diff')]
            path = next((p for p in candidates if p.is_file()), None)
            if path is None:
                raise ValueError('Missing supplied frozen patch: ' + iid)
            path = path.resolve()
        if not path.is_relative_to(root):
            raise ValueError('Frozen patch escapes supplied directory')
        if any(word in str(path).casefold() for word in ('oracle', 'grade', 'grader', 'label', 'gold', 'posthoc')):
            raise ValueError('Frozen patch has a forbidden input path')
        if row:
            require_hash(path, row['patch_sha256'])
        elif (path.parent / 'frozen_patch.json').is_file():
            proof = JSONProjection((path.parent / 'frozen_patch.json').read_text()).project({'sha256': True})
            require_hash(path, proof['sha256'].removeprefix('sha256:'))
        elif (path.parent / 'repair_record.json').is_file():
            proof = JSONProjection((path.parent / 'repair_record.json').read_text()).project({'patch': {'sha256': True}})
            require_hash(path, proof['patch']['sha256'].removeprefix('sha256:'))
        result[iid] = {'path': str(path), 'sha256': sha(path)}
    return result


def main(argv=None):
    assert_clean_interpreter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--task-specs', type=Path, nargs='+', required=True)
    parser.add_argument('--primary-config', type=Path, default=ROOT / 'configs/model/primary.yaml')
    parser.add_argument('--generator-config', type=Path, default=ROOT / 'configs/model/generator.yaml')
    parser.add_argument('--verifier-config', type=Path, default=DEFAULT_VERIFIER_CONFIG)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('pilot', 'audited'), required=True)
    parser.add_argument('--freeze-tag')
    parser.add_argument('--verify-only-from', type=Path)
    parser.add_argument('--reference-patches', action='store_true')
    parser.add_argument('--reuse-v4-from', type=Path)
    parser.add_argument('--skip-v4', action='store_true')
    parser.add_argument('--ledger-file', type=Path, default=ROOT / 'runs/provider_spend_ledger.json')
    parser.add_argument('--deepseek-cap-usd', type=float, default=4.0)
    parser.add_argument('--um-cap-usd', type=float, default=20.0)
    parser.add_argument('--um-job-cap-usd', type=float, default=3.0)
    args = parser.parse_args(argv)
    input_folder = args.verify_only_from.resolve() if args.verify_only_from is not None else None
    source_fields, origin_rows = verification_source(input_folder, args.reference_patches, ROOT)
    if args.reuse_v4_from is not None and (input_folder is None or args.skip_v4):
        raise ValueError('--reuse-v4-from requires verification-only mode with V4 enabled')
    validate_mode(args.mode, args.freeze_tag, args.verify_only_from, args.skip_v4)
    verifier_config = args.verifier_config.resolve()
    v2_settings = load_v2_settings(verifier_config)
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / 'runs').resolve()):
        raise ValueError('--output must be under runs/')
    ids = manifest_ids(args.manifest)
    supplied = frozen_inputs(input_folder, ids) if input_folder is not None else None
    if origin_rows is not None:
        for iid in ids:
            if supplied[iid]['sha256'] != patch_digest(origin_rows, iid):
                raise ValueError('Copied patch differs from the Phase 2 manifest for ' + iid)
    tasks, registries = load_registries(args.task_specs)
    primary_path, generator_path = args.primary_config.resolve(), args.generator_config.resolve()
    primary, generator = (yaml.safe_load(p.read_text()) for p in (primary_path, generator_path))
    for config, role in ((primary, 'primary'), (generator, 'generator')):
        if config.get('role') != role or config.get('verified', {}).get('status') != 'ok' or (
            config['verified'].get('model_id') != config.get('model_id')):
            raise ValueError('Model config role/verified identity mismatch')
        if config.get('provider') not in ('deepseek', 'umgpt'):
            raise ValueError('Unsupported paid provider')
    setup = default_reproduction_setup(generator_path, verifier_config=verifier_config)
    generator_digest = sha(generator_path)
    reuse = V4Reuse(args.reuse_v4_from, setup, generator_digest) if args.reuse_v4_from else None
    if reuse is not None and (output.is_relative_to(reuse.root) or reuse.root.is_relative_to(output)):
        raise ValueError('Reuse source and destination run directories must be separate')
    from reliability.paid_models import prices
    header = {'policy_version': 'v1.4.1-full', 'config_sha256': sha(verifier_config),
        'registry_sha256': registries, 'primary_config_sha256': sha(primary_path), 'generator_config_sha256': generator_digest,
        'manifest_sha256': sha(args.manifest), 'git_head': git('rev-parse', 'HEAD'),
        'git_dirty': bool(git('status', '--porcelain')), 'mode': args.mode, 'freeze_tag': args.freeze_tag,
        'skip_v4': args.skip_v4, 'verify_only_inputs': supplied, **source_fields,
        'ledger_file': str(args.ledger_file.resolve()), 'deepseek_cap_usd': args.deepseek_cap_usd,
        'um_cap_usd': args.um_cap_usd, 'um_job_cap_usd': args.um_job_cap_usd,
        'primary_prices': prices(primary), 'generator_prices': prices(generator),
        'generator': setup.identity(), 'parallelism': 1, 'patched_tree_drift_guard': 'weaker: no drift reference',
        'generic_exception_rules': rules_stamp()}
    if reuse is not None:
        header.update(reuse_v4_from=str(reuse.root), reuse_v4_seal_sha256=reuse.seal_sha256)
    ledgers = {}
    for config in (primary, generator):
        key = (config['provider'], config.get('account_id', 'default'))
        if key not in ledgers:
            cap = args.deepseek_cap_usd if key[0] == 'deepseek' else min(args.um_cap_usd, config.get('budget', {}).get('total_usd', args.um_cap_usd))
            ledgers[key] = ProviderLedger(args.ledger_file.resolve(), provider=key[0], account=key[1], job=str(output),
                total_usd=cap, job_usd=args.deepseek_cap_usd if key[0] == 'deepseek' else args.um_job_cap_usd)
    def ledger(config):
        return ledgers[(config['provider'], config.get('account_id', 'default'))]

    def agent_stage(iid, directory):
        supplied = header['verify_only_inputs']
        if supplied is not None:
            source = supplied[iid]
            require_hash(Path(source['path']), source['sha256'])
            freeze_patch(directory / 'patch.diff', Path(source['path']).read_bytes())
            return
        if iid not in tasks:
            write(directory / 'agent_absence.json', {'reason': 'NO_TASK_SPEC'})
            freeze_patch(directory / 'patch.diff', b'')
            return
        from reliability.agent.runner import AgentLimits, run_task
        from reliability.agent.records import RunRole
        from reliability.benchmark.loader import load_agent_task
        from reliability.benchmark.manifest import ManifestEntry
        from reliability.e2e_models import PinnedBackend
        from reliability.paid_models import paid_stage
        limits_config = yaml.safe_load((ROOT / 'configs/agent/mini_swe_agent.yaml').read_text())['limits']
        limits = AgentLimits(max_steps=primary['limits']['max_steps'],
            max_cost_usd=primary['limits']['max_cost_usd_per_task'],
            per_command_timeout_s=limits_config['per_command_timeout_s'],
            per_task_timeout_s=limits_config['per_task_timeout_s'])
        backend = PinnedBackend(model_id=primary['model_id'], agent_config_path=ROOT / 'configs/agent/swebench_claim.yaml',
            experiment_id=output.name, task_spec=tasks[iid], model_config_path=primary_path)
        try:
            with paid_stage(primary, ledger(primary), iid, 'agent', limits.max_cost_usd):
                # Supplying AgentTask avoids the legacy runner's paired-data loader.
                run_task(ManifestEntry(iid, tasks[iid].repo, 'unspecified', tasks[iid].base_commit), backend, output, experiment_id=output.name,
                    run_role=RunRole.PILOT if args.mode == 'pilot' else RunRole.MAIN,
                    manifest_hash=header['manifest_sha256'], limits=limits, agent_task=load_agent_task(iid))
        except (SourceIntegrityError, BudgetCap):
            raise
        except ProviderTransientError:
            # PinnedBackend captured the current diff and infrastructure receipt
            # before its container closed. Never replace it with an empty patch.
            if not (directory / 'patch.diff').exists():
                raise
        except Exception as exc:
            write(directory / 'agent_absence.json', {'reason': 'AGENT_EXCEPTION:' + type(exc).__name__})
            if not (directory / 'patch.diff').exists():
                freeze_patch(directory / 'patch.diff', b'')

    def verify_stage(iid, directory):
        folder = directory / 'verification/v4'
        reuse_evidence = None
        suite = None
        if reuse is not None:
            destination = folder / 'cache' / iid if reuse.settings[0] == 'legacy' else folder
            suite = reuse.load(iid, destination)
            reuse_evidence = {
                'reused_from': str(reuse.root),
                'requirements_sha256': suite.requirements_sha256 if suite is not None else None,
                'kept_test_sha256s': {test.path: test.sha256 for test in suite.kept} if suite is not None else {},
            }
            if suite is not None:
                reuse_evidence.update(suite_sha256=suite.suite_sha256,
                                      frozen=[test.as_dict() for test in suite.tests])

        def v4(instance_id, patch_text, integrity):
            if reuse is not None:
                from reliability.e2e_models import run_reused_v4
                return run_reused_v4(tasks.get(iid), patch_text, integrity, setup, suite, folder, output.name)
            if iid not in tasks:
                from reliability.verifier.run_v1_4_1 import absence
                from reliability.verifier.record import SignalKind
                return absence(SignalKind.REPRODUCTION, 'NO_TASK_SPEC')
            from reliability.benchmark.loader import load_agent_task
            from reliability.e2e_models import run_v4
            return run_v4(tasks.get(iid), patch_text, integrity, setup, generator_path, generator,
                          ledger(generator), directory / 'verification/v4', output.name,
                          load_agent_task(instance_id).problem_statement)
        options = {'v2_settings': v2_settings} if v2_settings else {}
        if reuse_evidence is not None:
            options['v4_reuse_evidence'] = reuse_evidence
        return verify_task(directory, instance_id=iid, task_spec=tasks.get(iid), experiment_id=output.name,
            skip_v4=args.skip_v4, provenance=json.loads((output / 'header.json').read_text()),
            v4_runner=v4, reproduction_setup=setup, **options)

    options = {'reuse_v4': reuse} if reuse is not None else {}
    status = run_batch(ids, output, header, agent_stage, verify_stage, ledgers=tuple(ledgers.values()), **options)
    print(json.dumps({'status': status, 'output': str(output)}))
    return 0 if status == 'COMPLETE' else 2


if __name__ == '__main__':
    raise SystemExit(main())
