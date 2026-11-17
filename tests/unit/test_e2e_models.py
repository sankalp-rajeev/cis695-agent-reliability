from contextlib import contextmanager
from types import SimpleNamespace

from reliability.e2e_models import PinnedBackend, PinnedGenerator, attached_environment
from reliability.verifier.run_v1_4_1 import default_reproduction_setup
from reliability.verifier.task_specs import ROOT


def test_attaching_scaffold_environment_cannot_launch_or_pull(monkeypatch):
    import minisweagent.environments.docker as docker
    def forbidden(*args, **kwargs):
        raise AssertionError('attaching an already verified container must not launch another one')
    monkeypatch.setattr(docker.subprocess, 'run', forbidden)
    monkeypatch.setattr(docker.subprocess, 'Popen', forbidden)
    container = SimpleNamespace(name='already_verified', image='sha256:' + 'a' * 64)
    env = attached_environment(container, {'cwd': '/testbed', 'timeout': 60})
    assert env.container_id == 'already_verified'
    assert env.config.image == container.image
    env.cleanup()


def test_primary_and_generator_take_explicit_configs_and_issue_only(tmp_path, monkeypatch):
    from reliability import e2e_models
    from reliability.agent.runner import AgentLimits
    seen = []
    @contextmanager
    def verified(task, folder, experiment, **kwargs):
        seen.append(('container', task.instance_id, kwargs))
        yield SimpleNamespace(name='verified', image='sha256:' + 'a' * 64)
    class Agent:
        messages, n_calls, cost = [], 1, .01
        def run(self, issue):
            seen.append(('issue', issue))
            return {'exit_status': 'Submitted', 'submission': 'FINAL_STATUS: UNRESOLVED\n<<<END_CLAIM>>>\npatch bytes'}
    def configure(config, model_path, env, steps, cost, timeout):
        seen.append(('config', model_path, steps, cost))
        return Agent()
    monkeypatch.setattr(e2e_models, 'pristine', verified)
    monkeypatch.setattr(e2e_models, 'attached_environment', lambda *a: object())
    monkeypatch.setattr(e2e_models, 'configured_agent', configure)
    monkeypatch.setattr(e2e_models, '_read_out', lambda *a: ({'v4_repro/test_repro_1.py': b'assert False'}, ()))
    spec = SimpleNamespace(instance_id='demo__repo-1')
    task = SimpleNamespace(instance_id=spec.instance_id, problem_statement='issue text only')
    primary = ROOT / 'configs/model/primary_umgpt.yaml'
    backend = PinnedBackend(model_id='openai/gpt-4.1-mini', task_spec=spec,
        model_config_path=primary, agent_config_path=ROOT / 'configs/agent/swebench_claim.yaml', experiment_id='mock')
    outcome = backend.run(task, tmp_path, AgentLimits())
    assert outcome.patch == b'patch bytes'
    generator = ROOT / 'configs/model/generator.yaml'
    setup = default_reproduction_setup(generator)
    generated = PinnedGenerator(spec, setup, generator, tmp_path, 'mock').generate(task.problem_statement, task.instance_id)
    assert generated.files == {'v4_repro/test_repro_1.py': b'assert False'}
    assert [r[1] for r in seen if r[0] == 'config'] == [primary, generator]
    assert [r[1] for r in seen if r[0] == 'issue'] == ['issue text only', 'issue text only']
    assert all(r[2] == {'agent': True} for r in seen if r[0] == 'container')
