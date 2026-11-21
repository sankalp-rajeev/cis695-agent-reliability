"""Per-requirement V4 with in-memory generators and sandboxes."""

import hashlib
import json
from contextlib import contextmanager, nullcontext
from dataclasses import replace
from types import SimpleNamespace

import pytest
import yaml
from jinja2 import Environment, meta

from reliability import e2e_models
from reliability.provider_spend import ProviderLedger
from reliability.umgpt import ACTIVE
from reliability.umgpt_spend import BudgetCap
from reliability.verifier.decision import SignalOutcome
from reliability.verifier.reproduction import (
    evaluate_frozen,
    signal_before_patch,
    signal_from_reproduction,
)
from reliability.verifier.reproduction_freeze import (
    ASSERTION_RETURNCODE,
    MANIFEST,
    REQUIREMENTS_PATH,
    TIMEOUT_RETURNCODE,
    FrozenSuite,
    GenerationOutcome,
    PerRequirementSetup,
    ReproductionConfigError,
    ReproductionSetup,
    freeze_requirements,
    freeze_tests,
    parse_requirements,
    repro_path,
)
from reliability.verifier.run_v1_4_1 import DEFAULT_VERIFIER_CONFIG, default_reproduction_setup
from reliability.verifier.task_specs import ROOT

ISSUE = "Correct the behavior described in this issue."
IID = "demo__repo-1"
PATCH = "synthetic patched-tree marker"
ASSERT = ASSERTION_RETURNCODE


def requirement_json(count):
    return json.dumps(
        {
            "requirements": [
                {"id": f"R{i}", "text": f"Behavior {i} with input and expected result"}
                for i in range(1, count + 1)
            ]
        }
    ).encode()


@pytest.fixture
def setup():
    config = DEFAULT_VERIFIER_CONFIG.with_name("v1_5.yaml")
    study = default_reproduction_setup(verifier_config=config)
    assert isinstance(study, PerRequirementSetup)
    return study


class Sandbox:
    def __init__(self, statuses):
        self.files = {}
        self.statuses = {path: iter(status) for path, status in statuses.items()}

    def write_file(self, path, data):
        self.files[path] = data

    def sha256(self, path):
        return "sha256:" + hashlib.sha256(self.files[path]).hexdigest()

    def run_test(self, path, timeout_s):
        return next(self.statuses[path]), "synthetic run"

    def set_patched(self, patched):
        assert patched


class Generator:
    def __init__(self, files, *, check=lambda: None):
        self.files = files
        self.check = check

    def generate(self, issue_text, instance_id):
        assert (issue_text, instance_id) == (ISSUE, IID)
        self.check()
        return GenerationOutcome(
            self.files,
            "Submitted",
            2,
            0.02,
            input_tokens=100,
            output_tokens=20,
            cached_input_tokens=10,
        )


def path(requirement, pass_number=None):
    suffix = "" if pass_number is None else f"_p{pass_number}"
    return f"v4_repro/test_repro_{requirement}{suffix}.py"


@pytest.mark.parametrize(
    "filename,variables",
    [
        ("v4_requirements.yaml", {"task"}),
        ("v4_tests_per_requirement.yaml", {"task", "requirements"}),
    ],
)
def test_prompt_placeholders_and_isolation(filename, variables):
    text = (ROOT / "configs/agent" / filename).read_text()
    data = yaml.safe_load(text)
    env = Environment()
    assert meta.find_undeclared_variables(env.parse(data["agent"]["system_template"])) == set()
    assert (
        meta.find_undeclared_variables(env.parse(data["agent"]["instance_template"])) == variables
    )
    for forbidden in ("FAIL_TO_PASS", "PASS_TO_PASS", "hints_text", "test_patch", "model_patch"):
        assert forbidden.casefold() not in text.casefold()
    assert data["environment"]["run_args"] == [
        "--rm",
        "--network",
        "none",
        "--tmpfs",
        "/opt/miniconda3/pkgs",
        "--tmpfs",
        "/root/.cache/pip",
    ]


@pytest.mark.parametrize(
    "raw",
    [
        b"bad JSON",
        b"[]",
        b'{"requirements":[]}',
        b'{"requirements":[{"id":"R2","text":"x"}]}',
        b'{"requirements":[{"id":"R1","text":" "}]}',
        b'{"requirements":[{"id":"R1","text":false}]}',
        b'{"requirements":[{"id":"R1","text":"a"},{"id":"R1","text":"b"}]}',
    ],
)
def test_requirements_validation(raw):
    with pytest.raises(ValueError):
        parse_requirements(raw)


@pytest.mark.parametrize("files", [{}, {REQUIREMENTS_PATH: b'{"requirements":[]}'}])
def test_unavailable_requirements_skips_tests_without_retry(tmp_path, setup, files):
    requested = []

    def generate(request):
        requested.append(request.name)
        return Generator(files)

    suite = freeze_requirements(
        ISSUE,
        IID,
        setup=setup,
        directory=tmp_path,
        generator_for=generate,
        base_sandbox=lambda iid: pytest.fail("screening without valid requirements"),
    )
    signal = signal_before_patch(suite, setup)
    assert requested == ["requirements"]
    assert signal.outcome is SignalOutcome.NOT_AVAILABLE
    assert signal.findings["absence_reason"] == "REQUIREMENTS_UNAVAILABLE"
    assert signal.findings["generation_totals"]["input_tokens"] == 100
    assert not (tmp_path / "requirements.json").exists()


def test_freeze_order_isolation_truncation_and_ignore_unknown_ids(tmp_path, setup):
    events = []
    requirements_path = tmp_path / "requirements.json"
    first_pass_marker = b"FIRST_PASS_BYTES"

    def generate(request):
        if request.pass_number is None:
            assert not requirements_path.exists()
            return Generator(
                {REQUIREMENTS_PATH: requirement_json(5)},
                check=lambda: events.append("requirements"),
            )
        assert parse_requirements(requirements_path.read_bytes()) == request.requirements
        assert [item.id for item in request.requirements] == ["R1", "R2", "R3", "R4"]
        rendered = request.prompt_variables["requirements"]
        assert len(rendered.splitlines()) == 4 and first_pass_marker.decode() not in rendered
        assert "R5: " not in rendered
        marker = first_pass_marker if request.pass_number == 1 else b"SECOND_PASS_BYTES"
        return Generator(
            {path("R1"): marker, path("R5"): b"ignored"}, check=lambda: events.append(request.name)
        )

    def base(iid):
        events.append("screen")
        assert events == ["requirements", "pass_1", "pass_2", "screen"]
        assert (tmp_path / "tests/test_repro_R1_p1.py").read_bytes() == first_pass_marker
        assert (tmp_path / "tests/test_repro_R1_p2.py").read_bytes() == b"SECOND_PASS_BYTES"
        return nullcontext(Sandbox({path("R1", n): [ASSERT, ASSERT] for n in (1, 2)}))

    suite = freeze_requirements(
        ISSUE, IID, setup=setup, directory=tmp_path, generator_for=generate, base_sandbox=base
    )
    assert suite.requirements_truncated_from == 5
    assert [test.pass_number for test in suite.kept] == [1, 2]
    assert {test.requirement_id for test in suite.kept} == {"R1"}
    assert len(suite.ignored) == 2
    assert FrozenSuite.read(tmp_path) == suite
    assert suite.as_dict()["generation_totals"] == {
        "cost_usd": 0.06,
        "input_tokens": 300,
        "output_tokens": 60,
        "cached_input_tokens": 30,
    }
    assert (
        freeze_requirements(
            ISSUE,
            IID,
            setup=setup,
            directory=tmp_path,
            generator_for=lambda request: pytest.fail("cached suite regenerated"),
            base_sandbox=base,
        )
        == suite
    )
    requirements_path.write_bytes(requirement_json(3))
    with pytest.raises(ReproductionConfigError, match="frozen requirement list changed"):
        FrozenSuite.read(tmp_path)


@pytest.mark.parametrize(
    "passes,patch_results,count,expected,outcome,reason",
    [
        (2, {1: [0, 0], 2: [0, 0]}, 1, "PASS", SignalOutcome.PASS, None),
        (2, {1: [0, 0], 2: [0, ASSERT]}, 1, "PASS", SignalOutcome.PASS, None),
        (2, {1: [0, 0], 2: [ASSERT, ASSERT]}, 1, "FAIL_SINGLE", SignalOutcome.FAIL, None),
        (
            2,
            {1: [ASSERT, ASSERT], 2: [ASSERT, ASSERT]},
            2,
            "FAIL_CONFIRMED",
            SignalOutcome.FAIL,
            None,
        ),
        (
            2,
            {1: [1, 1], 2: [TIMEOUT_RETURNCODE, TIMEOUT_RETURNCODE]},
            1,
            "NO_RESULT",
            SignalOutcome.NOT_AVAILABLE,
            "NO_RESULT",
        ),
        (2, {1: [0, 0]}, 2, "PASS", SignalOutcome.NOT_AVAILABLE, "UNCOVERED"),
        (2, {}, 1, "UNCOVERED", SignalOutcome.NOT_AVAILABLE, "UNCOVERED"),
        (1, {1: [ASSERT, ASSERT]}, 1, "FAIL_SINGLE", SignalOutcome.FAIL, None),
    ],
)
def test_requirement_verdicts_and_signal_mapping(
    tmp_path, setup, passes, patch_results, count, expected, outcome, reason
):
    setup = replace(setup, passes=passes)

    def generator_for(request):
        if request.pass_number is None:
            return Generator({REQUIREMENTS_PATH: requirement_json(count)})
        files = {path("R1"): b"test me"} if request.pass_number in patch_results else {}
        # R2's file passes on the base and is discarded during screening.
        if count > 1:
            files[path("R2")] = b"screened out"
        return Generator(files)

    base_results = {path("R1", n): [ASSERT, ASSERT] for n in patch_results}
    base_results.update({path("R2", n): [0, 0] for n in range(1, passes + 1)})
    suite = freeze_requirements(
        ISSUE,
        IID,
        setup=setup,
        directory=tmp_path,
        generator_for=generator_for,
        base_sandbox=lambda iid: nullcontext(Sandbox(base_results)),
    )
    signal = signal_before_patch(suite, setup)
    if signal is None:
        sandbox = Sandbox({path("R1", n): results for n, results in patch_results.items()})
        patched = evaluate_frozen(suite, PATCH, sandbox, setup)
        signal = signal_from_reproduction(suite, patched, setup)

    assert signal.outcome is outcome
    assert signal.findings["requirement_verdicts"]["R1"] == expected
    assert signal.findings["full_pass"] == (outcome is SignalOutcome.PASS)
    assert signal.findings.get("absence_reason") == reason
    assert sum(signal.findings["verdict_counts"].values()) == count
    if count > 1:
        assert signal.findings["uncovered_ids"] == ["R2"]
    for test in signal.findings["kept_tests"]:
        assert test["requirement_id"] == "R1"
        assert test["pass"] in patch_results
        assert test["sha256"] == test["patched"]["sha256"]
        assert all(run["returncode"] == ASSERT for run in test["base_runs"])
        assert [run["returncode"] for run in test["patched"]["runs"]] == patch_results[test["pass"]]


def test_explicit_legacy_config_uses_the_original_setup_and_freeze(tmp_path):
    config = tmp_path / "legacy.yaml"
    config.write_text(DEFAULT_VERIFIER_CONFIG.read_text() + "\nv1_5:\n  v4_design: legacy\n")
    setup = default_reproduction_setup(verifier_config=config)
    assert type(setup) is ReproductionSetup and setup == default_reproduction_setup()
    events = []
    suite = freeze_tests(
        ISSUE,
        IID,
        setup=setup,
        cache_dir=tmp_path,
        generator=Generator({repro_path(1): b"test me"}, check=lambda: events.append("legacy")),
        base_sandbox=lambda iid: nullcontext(Sandbox({repro_path(1): [ASSERT, ASSERT]})),
    )
    assert events == ["legacy"]
    assert "requirements" not in suite.as_dict()
    assert "pass" not in suite.kept[0].as_dict()
    patched = evaluate_frozen(suite, PATCH, Sandbox({repro_path(1): [0, 0]}), setup)
    assert signal_from_reproduction(suite, patched, setup).outcome is SignalOutcome.PASS


@pytest.mark.parametrize("run_cap", [0.07, 0.05])
def test_e2e_fresh_calls_frozen_before_patch_and_run_cap_is_aggregate(
    tmp_path, monkeypatch, setup, run_cap
):
    ledger = ProviderLedger(
        tmp_path / "ledger.json",
        provider="deepseek",
        job="test",
        total_usd=run_cap,
        job_usd=run_cap,
    )
    folder = tmp_path / "v4"
    events, conversations, readouts = [], [], []

    @contextmanager
    def pristine(task, where, experiment, *, patch_text="", agent=False):
        if agent:
            events.append(where.parent.name)
            assert not patch_text
            yield SimpleNamespace(phase=where.parent.name)
        elif patch_text:
            events.append("patched")
            assert patch_text == PATCH
            suite = FrozenSuite.read(folder)
            assert (folder / MANIFEST).is_file() and len(suite.kept) == 2
            for test in suite.kept:
                assert suite.bytes_of(test) == str(test.pass_number).encode()
            yield Sandbox({path("R1", n): [0, 0] for n in (1, 2)})
        else:
            events.append("screen")
            yield Sandbox({path("R1", n): [ASSERT, ASSERT] for n in (1, 2)})

    class Agent:
        n_calls = 1
        cost = 0.02

        def __init__(self, env, steps, cap):
            self.env = env
            self.messages = []
            assert cap == setup.budget.generator_max_cost_usd
            assert steps == (40 if env.phase == "requirements" else 80)

        def run(self, issue, **variables):
            assert issue == ISSUE
            conversations.append((self, variables))
            runtime = ACTIVE.get()
            call = ledger.reserve(
                0.02, task=IID, task_cap=runtime.task_cap, stage=runtime.stage, model_id="fake"
            )
            ledger.settle(call, 0.02, input_tokens=100, output_tokens=20, cached_input_tokens=0)
            if self.env.phase == "requirements":
                assert not variables
            else:
                assert variables == {
                    "requirements": "R1: Behavior 1 with input and expected result"
                }
                assert (folder / "requirements.json").is_file()
            return {"exit_status": "Submitted"}

    def read_out(env, budget, *, paths):
        readouts.append(paths)
        if env.phase == "requirements":
            return {REQUIREMENTS_PATH: requirement_json(1)}, ()
        return {path("R1"): env.phase[-1].encode()}, ()

    monkeypatch.setattr(e2e_models, "pristine", pristine)
    monkeypatch.setattr(e2e_models, "attached_environment", lambda container, config: container)
    monkeypatch.setattr(
        e2e_models,
        "configured_agent",
        lambda config, model, env, steps, cost, timeout: Agent(env, steps, cost),
    )
    monkeypatch.setattr(e2e_models, "_read_out", read_out)
    monkeypatch.setattr(e2e_models, "ContainerSandbox", lambda container: container)
    task = SimpleNamespace(instance_id=IID)
    integrity = SimpleNamespace(findings={"patch_applies": True})

    def run():
        return e2e_models.run_v4(
            task,
            PATCH,
            integrity,
            setup,
            tmp_path / "unused_model.yaml",
            {},
            ledger,
            folder,
            "test",
            ISSUE,
        )

    if run_cap == 0.07:
        signal = run()
        assert signal.outcome is SignalOutcome.PASS
        assert signal.findings["generation_totals"]["cost_usd"] == pytest.approx(0.06)
        assert readouts == [{REQUIREMENTS_PATH}, {path("R1")}, {path("R1")}]
        assert events == ["requirements", "pass_1", "pass_2", "screen", "patched"]
    else:
        with pytest.raises(BudgetCap) as exc:
            run()
        assert exc.value.paid_calls == 2
        assert events == ["requirements", "pass_1", "pass_2"]
    assert len({id(agent) for agent, _ in conversations}) == 3
    assert [row["stage"] for row in ledger.snapshot()["calls"]] == (
        ["V4_requirements", "V4_pass_1", "V4_pass_2"][: (3 if run_cap == 0.07 else 2)]
    )
    for name in ("requirements", "pass_1", "pass_2"):
        assert (folder / name / "generation_usage.json").is_file()
