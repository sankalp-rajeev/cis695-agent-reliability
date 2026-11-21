"""Pinned, pristine-verified environments for repair and V4 generation."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from reliability.agent.runner import (AgentOutcome, MiniSweAgentBackend, _commands_from,
    _serialisable, _split_submission, _step_limit_reached, _sum_tokens, _termination_for)
from reliability.agent.records import Termination
from reliability.agent.freeze import freeze_patch
from reliability.paid_models import model_options, paid_stage
from reliability.provider_errors import ProviderTransientError
from reliability.umgpt import ACTIVE
from reliability.umgpt_spend import BudgetCap
from reliability.verifier.guarded_v2 import FrozenContainer
from reliability.verifier.record import SignalAbsence, SignalKind, SignalRecord
from reliability.verifier.reproduction import ContainerSandbox, evaluate_frozen, signal_before_patch, signal_from_reproduction
from reliability.verifier.reproduction_freeze import (
    GenerationOutcome, GenerationRequest, PerRequirementSetup, ReproductionConfigError, _read_out, _sha256,
    freeze_requirements, freeze_tests, sum_generation_usage,
)
from reliability.verifier.reproduction_reuse import GENERATOR_OVERRIDE, V4ReuseError
from reliability.verifier.reproduction_v1_4 import RecordingGenerator
from reliability.verifier.source_integrity import SourceIntegrityError
from reliability.verifier.task_specs import ROOT, write


class AgentContainer(FrozenContainer):
    def run_args(self):
        args = super().run_args()
        index = args.index(self.image)
        args[index:index] = ['--tmpfs', '/opt/miniconda3/pkgs', '--tmpfs', '/root/.cache/pip']
        return args


@contextmanager
def pristine(task, folder, experiment, *, patch_text='', agent=False):
    folder.mkdir(parents=True, exist_ok=True)
    cls = AgentContainer if agent else FrozenContainer
    with cls(task.instance_id, patch_text, image=task.image_id, experiment_id=experiment,
             source_spec=task.source, source_receipt_path=folder / 'pristine_source_receipt.json') as container:
        if container.source_integrity.get('status') != 'VERIFIED':
            raise ValueError('A fresh VERIFIED pristine receipt is required')
        write(folder / 'pristine_generated_inputs.json', container.generated_snapshot())
        if agent:
            from reliability.agent.isolation import assert_network_none
            assert_network_none(container.name)
        yield container


def attached_environment(container, config):
    from minisweagent.environments.docker import DockerEnvironment

    class AttachedEnvironment(DockerEnvironment):
        # Reuse the scaffold's command execution and submission handling. Its
        # constructor invokes this override, so it cannot pull or start an image.
        def _start_container(self):
            self.container_id = container.name

        def cleanup(self):
            # The pristine context owns the container lifecycle.
            pass

    allowed = {k: config[k] for k in ('cwd', 'env', 'timeout', 'interpreter') if k in config}
    return AttachedEnvironment(image=container.image, **allowed)


def configured_agent(config, model_path, env, steps, cost, timeout):
    from minisweagent.agents.default import DefaultAgent
    from minisweagent.models import get_model
    model_config = yaml.safe_load(Path(model_path).read_text())
    options = {**config.get('model', {}), **model_options(model_path), 'model_name': model_config['model_id']}
    model = get_model(model_config['model_id'], options)
    agent = dict(config['agent'], step_limit=steps, cost_limit=cost)
    return DefaultAgent(model, env, **agent, wall_time_limit_seconds=timeout)


@dataclass
class PinnedBackend(MiniSweAgentBackend):
    task_spec: object = None
    model_config_path: Path | None = None

    def run(self, task, workdir, limits):
        config = yaml.safe_load(Path(self.agent_config_path).read_text())
        config['environment']['timeout'] = limits.per_command_timeout_s
        with pristine(self.task_spec, workdir / 'agent_environment', self.experiment_id, agent=True) as container:
            env = attached_environment(container, config['environment'])
            agent = configured_agent(config, self.model_config_path, env, limits.max_steps,
                                      limits.max_cost_usd, limits.per_task_timeout_s)
            try:
                result = agent.run(task.problem_statement)
                status, submission = result.get('exit_status', ''), result.get('submission', '') or ''
            except SourceIntegrityError:
                raise
            except ProviderTransientError as exc:
                write(workdir / 'agent_absence.json', {
                    'reason': 'AGENT_INFRA:' + exc.error_type, 'infrastructure': True})
                (workdir / 'trajectory.jsonl').write_text(''.join(
                    json.dumps(_serialisable(m)) + '\n' for m in agent.messages))
                # The submit prompt extracts a git diff from /testbed. On an
                # exhausted query there may be no patch.txt (or a stale one),
                # so extract the current tracked working-tree diff directly.
                diff = env.execute({'command': 'git diff --'})
                if diff['returncode'] != 0:
                    # Leave the task unfinished; a failed extraction is never
                    # evidence that the working tree has no changes.
                    raise
                freeze_patch(workdir / 'patch.diff', diff['output'].encode('utf-8'))
                raise
            except Exception as exc:
                status, submission = type(exc).__name__, ''
            claim, patch = _split_submission(submission)
            termination = _termination_for(status, False, step_limit_reached=_step_limit_reached(agent, limits.max_steps))
            runtime = ACTIVE.get()
            if runtime and runtime.halt and runtime.halt['termination'] in ('AUTH_ERROR', 'BUDGET_CAP'):
                termination = Termination(runtime.halt['termination'])
            return AgentOutcome(claim, patch, termination, commands_run=_commands_from(agent.messages),
                tokens_in=_sum_tokens(agent.messages, 'prompt_tokens'), tokens_out=_sum_tokens(agent.messages, 'completion_tokens'),
                api_cost_usd=float(getattr(agent, 'cost', 0.0)),
                trajectory=tuple(_serialisable(m) for m in agent.messages))


@dataclass
class PinnedGenerator:
    task: object
    setup: object
    config_path: Path
    folder: Path
    experiment: str
    request: GenerationRequest | None = None

    def generate(self, issue_text, instance_id):
        if (disabled := GENERATOR_OVERRIDE.get()) is not None:
            return disabled.generate(issue_text, instance_id)
        if instance_id != self.task.instance_id:
            raise ValueError('Generator task identity mismatch')
        budget = self.setup.budget
        steps = budget.generator_max_steps
        if self.request is None:
            config = yaml.safe_load((ROOT / self.setup.prompt_path).read_text())
            variables, readout = {}, {}
        else:
            requirements_call = self.request.pass_number is None
            prompt, expected = self.setup.prompts[0 if requirements_call else 1]
            raw = (ROOT / prompt).read_bytes()
            if _sha256(raw) != expected:
                raise ValueError('Pinned V4 prompt changed: ' + prompt)
            config = yaml.safe_load(raw)
            steps = self.setup.requirements_max_steps if requirements_call else self.setup.tests_max_steps
            variables, readout = self.request.prompt_variables, {'paths': self.request.paths}
        config['environment']['timeout'] = budget.per_command_timeout_s
        with pristine(self.task, self.folder / 'generator', self.experiment, agent=True) as container:
            env = attached_environment(container, config['environment'])
            agent = configured_agent(config, self.config_path, env, steps,
                                      budget.generator_max_cost_usd, budget.generator_timeout_s)
            try:
                termination = agent.run(issue_text, **variables).get('exit_status', '') or 'unknown'
            except SourceIntegrityError:
                raise
            except ProviderTransientError:
                # The model query already exhausted the scaffold's retries.
                # Do not screen an incomplete suite as generated evidence.
                raise
            except Exception as exc:
                if self.request is not None and isinstance(exc, BudgetCap):
                    raise
                termination = type(exc).__name__
            finally:
                trajectory = tuple(_serialisable(m) for m in agent.messages)
                path = self.folder / 'generator/generation_trajectory.jsonl'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(''.join(json.dumps(message) + '\n' for message in trajectory),
                                encoding='utf-8')
            files, ignored = _read_out(env, budget, **readout)
            return GenerationOutcome(files, termination, n_steps=int(getattr(agent, 'n_calls', 0)),
                cost_usd=float(getattr(agent, 'cost', 0.0)), ignored=ignored,
                trajectory=trajectory)


def _generation_ledger_calls(ledger, instance_id, stages):
    return [call for call in ledger.account_calls(ledger.snapshot())
            if call['job'] == ledger.job and call['task'] == instance_id and call['stage'] in stages]


@dataclass
class MeteredGenerator:
    generator: PinnedGenerator
    model_config: dict
    ledger: object

    def generate(self, issue_text, instance_id):
        if (disabled := GENERATOR_OVERRIDE.get()) is not None:
            return disabled.generate(issue_text, instance_id)
        name = self.generator.request.name
        stage = f'V4_{name}'
        cap = self.generator.setup.budget.generator_max_cost_usd
        try:
            with paid_stage(self.model_config, self.ledger, instance_id, stage, cap, allow_partial=True):
                outcome = self.generator.generate(issue_text, instance_id)
        finally:
            calls = _generation_ledger_calls(self.ledger, instance_id, {stage})
            usage = sum_generation_usage(calls)
            write(self.generator.folder / 'generation_usage.json',
                  {'call': name, 'stage': stage, 'provider_requests': len(calls), **usage})
        return replace(outcome, **usage)


def run_reused_v4(task, patch_text, integrity, setup, suite, folder, experiment):
    if suite is None:
        signal = SignalRecord.absent(SignalKind.REPRODUCTION, SignalAbsence.NOTHING_TO_CHECK, 'NO_FROZEN_V4')
        signal.findings['absence_reason'] = 'NO_FROZEN_V4'
        return signal
    if (early := signal_before_patch(suite, setup)) is not None:
        return early
    if task is None or not integrity.findings.get('patch_applies', True):
        return SignalRecord.absent(SignalKind.REPRODUCTION, SignalAbsence.NOTHING_TO_CHECK,
                                   'no task spec or patch does not apply')
    started = time.monotonic()
    with pristine(task, folder / 'patched', experiment, patch_text=patch_text) as container:
        container.set_patched(True)
        try:
            patched = evaluate_frozen(suite, patch_text, ContainerSandbox(container), setup)
        except (OSError, ReproductionConfigError) as exc:
            raise V4ReuseError(task.instance_id, 'reused frozen test could not be read or verified') from exc
    if any(test.verdict == 'not_in_place' for test in patched):
        raise V4ReuseError(task.instance_id, 'reused frozen test or runner SHA-256 mismatch in patched tree')
    return signal_from_reproduction(suite, patched, setup, duration_s=time.monotonic() - started)


def run_v4(task, patch_text, integrity, setup, model_path, model_config, ledger, folder, experiment, issue_text):
    if (disabled := GENERATOR_OVERRIDE.get()) is not None:
        return disabled.generate(issue_text, getattr(task, 'instance_id', '<no task spec>'))
    if task is None:
        return SignalRecord.absent(SignalKind.REPRODUCTION, SignalAbsence.ERROR, 'NO_TASK_SPEC')
    if not patch_text.strip() or not integrity.findings.get('patch_applies', True):
        return SignalRecord.absent(SignalKind.REPRODUCTION, SignalAbsence.NOTHING_TO_CHECK, 'patch empty or does not apply')
    started, source_errors = time.monotonic(), []

    @contextmanager
    def base(_iid):
        try:
            with pristine(task, folder / 'screen', experiment) as container:
                yield ContainerSandbox(container)
        except SourceIntegrityError as exc:
            # The frozen screen helper catches Exception. Retain its typed
            # error here and rethrow immediately after it returns.
            source_errors.append(exc)
            raise

    def finish(suite):
        if source_errors:
            raise source_errors[0]
        early = signal_before_patch(suite, setup, duration_s=time.monotonic() - started)
        if early is not None:
            return early
        with pristine(task, folder / 'patched', experiment, patch_text=patch_text) as container:
            container.set_patched(True)
            patched = evaluate_frozen(suite, patch_text, ContainerSandbox(container), setup)
        return signal_from_reproduction(suite, patched, setup, duration_s=time.monotonic() - started)

    if isinstance(setup, PerRequirementSetup):
        def generator_for(request):
            generator = PinnedGenerator(task, setup, model_path, folder / request.name, experiment, request)
            return MeteredGenerator(generator, model_config, ledger)

        try:
            suite = freeze_requirements(issue_text, task.instance_id, setup=setup, directory=folder,
                                        generator_for=generator_for, base_sandbox=base)
        except BudgetCap as exc:
            stages = {'V4_requirements', *(f'V4_pass_{number}' for number in range(1, setup.passes + 1))}
            exc.paid_calls = sum(call['state'] == 'reserved' or call.get('reservation_retained', False)
                                 or call.get('input_tokens') is not None
                                 for call in _generation_ledger_calls(ledger, task.instance_id, stages))
            raise
        return finish(suite)

    with paid_stage(model_config, ledger, task.instance_id, 'V4', setup.budget.generator_max_cost_usd):
        generator = RecordingGenerator(PinnedGenerator(task, setup, model_path, folder, experiment), setup,
                                        folder / 'generation_evidence.v1_4_1.json')
        suite = freeze_tests(issue_text, task.instance_id, setup=setup, cache_dir=folder / 'cache',
                             generator=generator, base_sandbox=base)
        return finish(suite)
