"""Detect oracle data in agent-visible or verifier-input artifacts (Phase 8.3).

The gate this backs is non-negotiable: if ground truth reached the agent or the
verifier's selection step, the experiment measures nothing, and no other result
in the study survives it.

Two kinds of check, because either alone is insufficient:

**Field names.** `FAIL_TO_PASS`, `test_patch`, `hints_text` and friends appearing
in a prompt, a tool result, or a verifier input means oracle plumbing reached
somewhere it should not. The same words in the model's own message are
benchmark-awareness: counted, and not a failure, because nothing in the run
delivered them. A command the model itself issued to search the disk for one
of those names is recorded separately as an answer-key search, and is also
not a failure of this gate.

**Field content.** A leak does not have to carry its label. Gold patch text
pasted into a prompt, or a `FAIL_TO_PASS` test name appearing in a repository
that does not contain that test, is a leak whether or not the word
"FAIL_TO_PASS" appears anywhere. This check compares against the actual oracle
values for the instance, so it catches a leak that was laundered through
reformatting.

Two scoping decisions that matter for the result to mean anything:

- **The oracle's own outputs are out of scope.** `oracle_record.json` and the
  harness logs are *supposed* to contain `FAIL_TO_PASS` names and resolution
  status; that is what they are for. Scanning them would guarantee a hit and
  train the reader to ignore the audit. Scope is defined by an allowlist of
  agent-visible and verifier-input filenames rather than a denylist, so a new
  artifact is out of scope until someone adds it deliberately, instead of being
  scanned by accident and producing noise.

- **Scanning nothing is a failure, not a pass.** `audit()` returns
  `scanned_files == 0` as a hard failure. An audit that silently covered no
  files would exit clean and mean nothing, which is the same error as counting
  an unrun test as a pass.
"""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

#: Filenames that are agent-visible or feed the verifier. Everything else is out
#: of scope until added here on purpose.
IN_SCOPE = (
    "trajectory.jsonl",      # the full agent conversation, prompts included
    "generation_trajectory.jsonl",  # the V4 test generator's conversation
    "frozen.json",           # V4's freeze manifest: hashes and base-screen output
    "agent_output.txt",
    "submission_raw.txt",
    "repair_record.json",
    "patch.diff",
    "prompt.txt",
    "system_prompt.txt",
)

#: Verification records are in scope too, matched by pattern.
IN_SCOPE_PATTERNS = ("verification_record.*.json",)

#: Conversations, classified by who first said a name. The generator's is read
#: by exactly the same rules as the repair agent's.
TRAJECTORY_FILES = ("trajectory.jsonl", "generation_trajectory.jsonl")

#: V4's frozen tests are generator output and verifier input. They sit in a
#: `tests/` subdirectory of the generator's cache directory.
FROZEN_TESTS_DIR = "tests"
FROZEN_TEST_PATTERN = "test_repro_*.py"

#: Deliberately *not* scanned: these are the oracle's own output and are
#: supposed to contain ground truth. Listed explicitly so the exclusion is a
#: documented decision rather than an accident of the allowlist.
OUT_OF_SCOPE = (
    "oracle_record.json",
    "oracle_record.harness_original.json",
    "oracle_verdict.json",
    "harness.log",
    "predictions.jsonl",
)

#: Oracle column names. Any of these appearing in an in-scope file means oracle
#: plumbing reached somewhere it should not.
ORACLE_FIELD_NAMES = (
    "FAIL_TO_PASS",
    "PASS_TO_PASS",
    "test_patch",
    "hints_text",
    "eval_script",
    "environment_setup_commit",
    "golden_patch",
    "gold_patch",
)

#: Minimum length for a gold-patch line to be usable as a probe. Short lines
#: like `)` or `return` occur naturally in any repository and would produce
#: constant false positives.
MIN_PROBE_LENGTH = 24

#: How many distinctive lines to draw from each oracle text.
MAX_PROBES = 40

#: Conda's package cache. LLM containers mount an empty tmpfs here, so a
#: successful content read means the mask did not apply.
MASKED_CONDA_PKGS = "/opt/miniconda3/pkgs"
#: Newer copies that cannot be hidden without breaking conda or pip.
UNMASKABLE_PIP_VENDOR = "/pip/_vendor"
UNMASKABLE_CONDA_LIB = "/opt/miniconda3/lib"
UNMASKABLE_DIST_PACKAGES = "/usr/lib/python3/dist-packages"
#: The task image's own install at the base commit. Reading it is legitimate.
#: A `pip/_vendor` path under this tree is not: those still count.
LEGITIMATE_TESTBED_ENV = "/opt/miniconda3/envs/testbed"
#: Repository slug to import name, where they differ.
IMPORT_NAME_ALIASES = {"scikit-learn": "sklearn"}
#: First word of a command that only lists a path. `pip show` and `pip list`
#: are listing too. Anything else, including an unknown verb, is a read.
LISTING_VERBS = frozenset({"ls", "find", "stat", "du", "test", "[", "which"})


class Severity(str, Enum):
    """How much a finding implies.

    `CONFIRMED` means oracle content, or an oracle field name that was delivered
    to the model, was found where it cannot legitimately be. `REVIEW` means a
    match that has an innocent explanation worth ruling out by hand.
    `BENCHMARK_AWARENESS` means the model itself produced the field name — in
    its own reasoning, or in a command it issued to search the disk for one —
    and nothing delivered to it contained the name first. It is counted and it
    does not fail the gate: a model that remembers how SWE-bench is shaped is
    not a leak of this run's oracle. Only `CONFIRMED` fails the gate.
    """

    CONFIRMED = "confirmed"
    REVIEW = "review"
    BENCHMARK_AWARENESS = "benchmark-awareness"
    #: A newer-copy note that must not change pass/fail. Masked-cache reads
    #: stay `CONFIRMED`. This value is the unmaskable tier, listings, and
    #: compound commands whose output cannot be pinned on the masked cache.
    EXPOSED_COPY = "exposed-copy"


@dataclass(frozen=True, slots=True)
class Finding:
    severity: Severity
    kind: str
    path: str
    detail: str
    line_no: int | None = None

    def __str__(self) -> str:
        where = f":{self.line_no}" if self.line_no else ""
        return f"[{self.severity.value}] {self.kind} {self.path}{where}: {self.detail}"


@dataclass(frozen=True, slots=True)
class OracleProbes:
    """The values to search for, derived from one instance's oracle record."""

    instance_id: str
    patch_lines: tuple[str, ...] = ()
    test_patch_lines: tuple[str, ...] = ()
    fail_to_pass: tuple[str, ...] = ()
    hints_lines: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not (self.patch_lines or self.test_patch_lines
                    or self.fail_to_pass or self.hints_lines)


def _not_in_problem_statement(
    lines: tuple[str, ...], problem_statement: str
) -> tuple[str, ...]:
    """Drop probes the agent was legitimately given.

    A string that appears in the problem statement cannot distinguish a leak
    from the agent doing its job, so using it as a probe can only generate false
    positives. This matters most for `hints_text`, which is drawn from the same
    pull-request thread as the problem statement and frequently quotes it
    outright.
    """
    if not problem_statement:
        return lines
    return tuple(line for line in lines if line not in problem_statement)


@dataclass
class AuditResult:
    findings: list[Finding] = field(default_factory=list)
    scanned_files: int = 0
    scanned_tasks: int = 0
    content_checked_tasks: int = 0

    @property
    def confirmed(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.CONFIRMED]

    @property
    def review(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.REVIEW]

    @property
    def benchmark_awareness(self) -> list[Finding]:
        """Field names the model produced itself. Counted, and not a failure."""
        return [f for f in self.findings if f.severity is Severity.BENCHMARK_AWARENESS]

    @property
    def passed(self) -> bool:
        """An audit that scanned nothing has not passed.

        Same rule as NOT_RUN in Phase 5 and NOT_AVAILABLE in Phase 6: the
        absence of a check is never evidence of correctness, and an audit
        reporting clean over zero files is exactly that.
        """
        return self.scanned_files > 0 and not self.confirmed


def distinctive_lines(
    text: str, *, limit: int = MAX_PROBES, added_only: bool = False
) -> tuple[str, ...]:
    """Pull searchable lines out of a diff or a free-text field.

    Added and removed lines are stripped of their diff marker, because a leak
    would be reproduced as source, not as a diff. Lines shorter than
    `MIN_PROBE_LENGTH` are dropped: `)` and `return None` appear in every
    repository and would make every run look like a leak.

    `added_only` keeps lines the diff introduces. Context and removed lines
    are the file at the base commit; an agent that read the file will
    reproduce them, and that is not oracle content.
    """
    seen: list[str] = []
    for raw in text.splitlines():
        # Structural diff lines are not content and would only ever match
        # another diff, so they are dropped rather than stripped.
        if raw.startswith(("+++", "---", "@@", "diff --git", "index ")):
            continue
        if added_only:
            if not raw.startswith("+"):
                continue
            line = raw[1:].strip()
        else:
            line = (raw[1:] if raw[:1] in "+-" else raw).strip()
        if len(line) < MIN_PROBE_LENGTH:
            continue
        if line not in seen:
            seen.append(line)
        if len(seen) >= limit:
            break
    return tuple(seen)


def probes_from_oracle(record, problem_statement: str = "") -> OracleProbes:
    """Build probes from an `OracleRecord` from the dataset loader.

    Takes the loader's record rather than an instance id so this module never
    loads the dataset itself — the caller that already has oracle access passes
    it in, and nothing here acquires it.

    `problem_statement` is the agent-visible half, used to *subtract* probes
    rather than to search for anything. Without it the audit reports a leak
    every time an agent quotes the issue it was asked to fix.
    """
    return OracleProbes(
        instance_id=record.instance_id,
        patch_lines=_not_in_problem_statement(
            distinctive_lines(record.patch, added_only=True), problem_statement),
        test_patch_lines=_not_in_problem_statement(
            distinctive_lines(record.test_patch, added_only=True), problem_statement),
        fail_to_pass=tuple(record.fail_to_pass),
        hints_lines=_not_in_problem_statement(
            distinctive_lines(record.hints_text, limit=10), problem_statement),
    )


def without_base_lines(probes: OracleProbes, present: set[str]) -> OracleProbes:
    """Drop probes that already exist in the repository at the base commit.

    An added test-patch line can still be a docstring in another file. Finding
    it after the agent read that file is not evidence the test patch was shown.
    """
    if not present:
        return probes
    return OracleProbes(
        instance_id=probes.instance_id,
        patch_lines=tuple(line for line in probes.patch_lines if line not in present),
        test_patch_lines=tuple(
            line for line in probes.test_patch_lines if line not in present),
        fail_to_pass=probes.fail_to_pass,
        hints_lines=probes.hints_lines,
    )


def in_scope(path: Path) -> bool:
    if path.name in OUT_OF_SCOPE:
        return False
    if path.name in IN_SCOPE:
        return True
    return any(path.match(p) for p in IN_SCOPE_PATTERNS)


def scan_files(task_dir: Path) -> list[Path]:
    files = [p for p in task_dir.iterdir() if p.is_file() and in_scope(p)]
    frozen = task_dir / FROZEN_TESTS_DIR
    if (task_dir / "generation_trajectory.jsonl").is_file() and frozen.is_dir():
        files.extend(p for p in frozen.glob(FROZEN_TEST_PATTERN) if p.is_file())
    return sorted(files)


#: Output the verifier produces itself. It is a list of test node ids, and node
#: ids are named after tests: `test_patch_extractor_fit` is a scikit-learn test,
#: not the `test_patch` column. Nothing in it is dataset data, so it is not
#: scanned for field names at all. Content checks still read the whole file.
VERIFIER_OWN_OUTPUT_KEYS = ("selected_tests",)

_FIELD_TOKEN = {
    name: re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")
    for name in ORACLE_FIELD_NAMES
}


def _field_name_text(path: Path, text: str) -> str:
    """The text to search for field names, with our own output removed."""
    if not path.name.startswith("verification_record."):
        return text
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict):
        for key in VERIFIER_OWN_OUTPUT_KEYS:
            payload.pop(key, None)
        return json.dumps(payload, indent=2)
    return text


#: A command that looks for an oracle field on disk, as opposed to mentioning it.
_SEARCH_CMD = re.compile(r"(?<![A-Za-z0-9_])(?:find|grep|rg|ag)(?![A-Za-z0-9_])")
#: Repair-record fields the model wrote. A field name anywhere else in that
#: record was not the model's own words and stays a confirmed leak.
_MODEL_RECORD_KEYS = ("commands_run", "tests_run", "claim")


def _names_in(text: str) -> tuple[str, ...]:
    return tuple(name for name, token in _FIELD_TOKEN.items() if token.search(text))


def _confirmed_name(path: Path, name: str, line_no: int | None) -> Finding:
    return Finding(
        severity=Severity.CONFIRMED, kind="oracle-field-name", path=str(path),
        detail=f"{name!r} appears in an in-scope artifact", line_no=line_no,
    )


def _awareness(path: Path, name: str, *, search: bool, line_no: int | None) -> Finding:
    if search:
        return Finding(
            severity=Severity.BENCHMARK_AWARENESS, kind="answer-key-search",
            path=str(path), line_no=line_no,
            detail=(f"{name!r} is in a command the model issued to search the "
                    "disk for an oracle field; nothing delivered the name"),
        )
    return Finding(
        severity=Severity.BENCHMARK_AWARENESS, kind="benchmark-awareness",
        path=str(path), line_no=line_no,
        detail=(f"{name!r} is the model's own wording; nothing delivered the name"),
    )


def _scan_confirmed_lines(path: Path, text: str) -> list[Finding]:
    findings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for name in _names_in(line):
            findings.append(_confirmed_name(path, name, line_no))
    return findings


def _scan_trajectory_field_names(path: Path, text: str) -> list[Finding]:
    """Classify field names by the first message in the trajectory that has them.

    File order is the whole trajectory, not one turn. A name whose first
    appearance is the model's own message is benchmark-awareness, and a later
    tool result that merely echoes it is not a delivery. A name whose first
    appearance is a user, system, or tool message was handed to the model and
    stays confirmed, including when the model repeats it afterwards. A line
    that is not a message has no speaker, so its names stay confirmed.
    """
    parsed: list[tuple[int, str, dict | None]] = []
    findings: list[Finding] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        message: dict | None = None
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            loaded = None
        if isinstance(loaded, dict):
            message = loaded
        else:
            for name in _names_in(raw):
                findings.append(_confirmed_name(path, name, line_no))
            continue
        parsed.append((line_no, raw, message))

    first: dict[str, str] = {}
    for line_no, _raw, message in parsed:
        role = message.get("role")
        strings = _message_strings(message)
        calls = _message_strings(message.get("tool_calls"))
        for name in _names_in("\n".join(strings)):
            search = role == "assistant" and any(
                name in call and _SEARCH_CMD.search(call) for call in calls
            )
            if name not in first:
                first[name] = role if isinstance(role, str) else ""
            if first[name] == "assistant" and role == "assistant":
                findings.append(_awareness(path, name, search=search, line_no=line_no))
            elif first[name] == "assistant":
                continue
            else:
                findings.append(_confirmed_name(path, name, line_no))
    return findings


def _scan_repair_record_field_names(path: Path, text: str) -> list[Finding]:
    """The model's commands and claim are its own words. The rest of the record is not."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _scan_confirmed_lines(path, text)
    if not isinstance(payload, dict):
        return _scan_confirmed_lines(path, text)

    findings: list[Finding] = []
    for key in ("commands_run", "tests_run"):
        commands = payload.get(key) or ()
        if not isinstance(commands, list):
            continue
        for command in commands:
            if not isinstance(command, str):
                continue
            search = bool(_SEARCH_CMD.search(command))
            for name in _names_in(command):
                findings.append(_awareness(
                    path, name, search=search, line_no=_line_of(text, command[:80])))
    for name in _names_in("\n".join(_message_strings(payload.get("claim")))):
        findings.append(_awareness(path, name, search=False, line_no=None))

    rest = {k: v for k, v in payload.items() if k not in _MODEL_RECORD_KEYS}
    findings.extend(_scan_confirmed_lines(path, json.dumps(rest)))
    return findings


def _line_of(text: str, fragment: str) -> int | None:
    for line_no, line in enumerate(text.splitlines(), start=1):
        if fragment and fragment in line:
            return line_no
    return None


def scan_field_names(path: Path, text: str) -> list[Finding]:
    """Look for oracle column names in an agent-visible or verifier-input file.

    A name matches as a whole identifier, not as a substring of a longer one:
    `test_patch` inside `test_patch_extractor_fit` is a test's name. Boundaries
    are identifier characters, so `*test_patch*`, `"FAIL_TO_PASS"` and prose
    that names the column all still match.

    Where the name sits decides the severity. The model's own message is
    benchmark-awareness. A user, tool, or system message, a prompt, or a
    verifier record is confirmed: the name was somewhere it can shape a result.
    """
    text = _field_name_text(path, text)
    if path.name in TRAJECTORY_FILES:
        return _scan_trajectory_field_names(path, text)
    if path.name == "repair_record.json":
        return _scan_repair_record_field_names(path, text)
    return _scan_confirmed_lines(path, text)


def _message_strings(value: object) -> list[str]:
    """Every string in a message, decoded, including JSON carried inside a string.

    Tool-call arguments are a JSON document in a string field, so they are
    decoded a second time.
    """
    if isinstance(value, str):
        strings = [value]
        stripped = value.lstrip()
        if stripped[:1] in ("{", "["):
            try:
                strings.extend(_message_strings(json.loads(value)))
            except json.JSONDecodeError:
                pass
        return strings
    if isinstance(value, dict):
        return [s for v in value.values() for s in _message_strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _message_strings(v)]
    return []


def agent_authored_lines(task_dir: Path, probes: OracleProbes) -> frozenset[str]:
    """Added oracle lines whose first appearance, in the whole trajectory, is the model's own message.

    The walk is file order from the first message to the last. It is not
    reset per turn. A tool result that contains the line, followed later by
    the model restating it, is not agent-authored: the earlier tool message
    already showed the line to the model. Only a line that the assistant
    message contains before any user or tool message does is suppressed, so a
    later `git diff` of a fix the model wrote itself is not read as a leak.
    """
    path = next((task_dir / name for name in TRAJECTORY_FILES
                 if (task_dir / name).exists()), None)
    if path is None:
        return frozenset()
    probes_of_interest = probes.patch_lines + probes.test_patch_lines
    if not probes_of_interest:
        return frozenset()
    authored: set[str] = set()
    seen: set[str] = set()
    try:
        raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return frozenset()
    for raw in raw_lines:
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        # Decoded text, not the raw JSON line: a probe with a quote or a
        # backslash is stored escaped and never matches the raw line.
        text = "\n".join(_message_strings(message))
        for probe in probes_of_interest:
            if probe in seen or probe not in text:
                continue
            seen.add(probe)
            if role == "assistant":
                authored.add(probe)
    return frozenset(authored)


def scan_content(
    path: Path,
    text: str,
    probes: OracleProbes,
    agent_authored: frozenset[str] = frozenset(),
) -> list[Finding]:
    """Look for actual oracle values, which a leak need not have labelled."""
    findings = []

    # The gold patch and the test patch stay CONFIRMED, but only their added
    # lines, and not a line the agent wrote itself before any tool showed it
    # back. A one-line repair that matches the gold patch is the outcome under
    # test, not a leak, once the trajectory shows the model produced it.
    # `agent_authored` is that set. A line that arrives in a user or tool
    # message first — the prompt, or a fetched patch — is still confirmed.
    for label, lines, severity in (
        ("gold-patch", probes.patch_lines, Severity.CONFIRMED),
        ("test-patch", probes.test_patch_lines, Severity.CONFIRMED),
        ("hints-text", probes.hints_lines, Severity.REVIEW),
    ):
        for probe in lines:
            if probe in agent_authored:
                continue
            if probe in text:
                findings.append(Finding(
                    severity=severity,
                    kind=f"{label}-content",
                    path=str(path),
                    detail=f"oracle {label} line present: {probe[:60]!r}",
                ))
                break  # one hit per field is enough; the rest is noise

    # FAIL_TO_PASS names are reviewable rather than confirmed. Most are added by
    # the test patch and so cannot legitimately appear, but some already exist at
    # the base commit and an agent that read the test file would reproduce them
    # innocently. Failing on that would make the gate cry wolf; ignoring it would
    # miss a real leak, so it is surfaced for a human instead.
    for name in probes.fail_to_pass:
        symbol = _test_symbol(name)
        if symbol and re.search(rf"\b{re.escape(symbol)}\b", text):
            findings.append(Finding(
                severity=Severity.REVIEW,
                kind="fail-to-pass-name",
                path=str(path),
                detail=(f"FAIL_TO_PASS test {symbol!r} named in an in-scope "
                        "artifact; confirm it exists at the base commit"),
            ))
    return findings


def _test_symbol(node_id: str) -> str:
    """The test function name out of a pytest node id or a unittest path."""
    tail = node_id.split("::")[-1].split("[")[0].strip()
    return tail if tail.startswith("test") and len(tail) > 4 else ""


def import_name_for_instance(instance_id: str) -> str:
    """Import name for the repository named by a SWE-bench instance id.

    `org__repo-123` yields `repo`, hyphens become underscores, and
    `scikit-learn` is `sklearn`.
    """
    repo = instance_id.split("__", 1)[-1]
    repo = re.sub(r"-\d+$", "", repo)
    repo = IMPORT_NAME_ALIASES.get(repo, repo)
    return repo.replace("-", "_")


_ABS_PATH = re.compile(r"/[^\s'\"\\<>|;&]+")


def _command_verb(command: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    index = 0
    while index < len(tokens) and "=" in tokens[index] and not tokens[index].startswith(("/", "-")):
        index += 1
    if index >= len(tokens):
        return ""
    verb = Path(tokens[index]).name
    if verb == "pip" and index + 1 < len(tokens) and tokens[index + 1] in {"show", "list"}:
        return "pip-list"
    return verb


def _is_listing(command: str) -> bool:
    verb = _command_verb(command)
    return verb in LISTING_VERBS or verb == "pip-list"


def _is_listing_verb(verb: str) -> bool:
    return verb in LISTING_VERBS or verb == "pip-list"


#: A segment whose only effect is text it was given, or a directory change.
#: ``echo``, ``cd``, and ``true`` do not count as another producer of the
#: observation.
_NO_OP_VERBS = frozenset({"cd", "echo", "true"})
#: Stages that only narrow the previous stage. After a stage that names the
#: masked cache they are not a separate producer. A filter that itself names
#: the cache (``head /opt/miniconda3/pkgs/.../file.py``) is still a read.
_PIPELINE_FILTERS = frozenset({"head", "tail", "grep", "sort", "wc"})


def _split_command(command: str) -> list[list[str]]:
    """Split a command into segments, and each segment into pipeline stages.

    ``;``, ``&&``, ``||``, and newlines separate segments. ``|`` separates
    stages of one pipeline. Quotes and heredoc bodies stay in the segment
    that opened them.
    """
    segments: list[list[str]] = []
    stages: list[str] = []
    buf: list[str] = []
    # Heredocs opened so far in this segment. ``dest`` is ``"buf"`` until the
    # opening stage is flushed past a pipe, then the stage index.
    openings: list[dict[str, object]] = []
    i = 0
    n = len(command)

    def flush_stage() -> None:
        text = "".join(buf).strip()
        del buf[:]
        if not text and not any(item["dest"] == "buf" for item in openings):
            return
        index = len(stages)
        stages.append(text)
        for item in openings:
            if item["dest"] == "buf":
                item["dest"] = index

    def flush_segment() -> None:
        flush_stage()
        if stages:
            segments.append(list(stages))
            stages.clear()
        openings.clear()

    def read_heredoc(pos: int, delim: str, strip_tabs: bool) -> tuple[str, int]:
        start = pos
        if pos < n and command[pos] == "\n":
            pos += 1
        while pos < n:
            end = command.find("\n", pos)
            if end == -1:
                line = command[pos:]
                nxt = n
            else:
                line = command[pos:end]
                nxt = end + 1
            check = line.lstrip("\t") if strip_tabs else line
            if check == delim:
                return command[start:nxt], nxt
            pos = nxt
        return command[start:], n

    def consume_open_heredocs(pos: int) -> int:
        for item in openings:
            body, pos = read_heredoc(pos, str(item["delim"]), bool(item["strip"]))
            dest = item["dest"]
            if isinstance(dest, int):
                stages[dest] = stages[dest] + body
            else:
                buf.append(body)
        openings.clear()
        return pos

    while i < n:
        char = command[i]
        if char == "\\" and i + 1 < n:
            buf.append(char)
            buf.append(command[i + 1])
            i += 2
            continue
        if char == "'":
            buf.append(char)
            i += 1
            while i < n and command[i] != "'":
                buf.append(command[i])
                i += 1
            if i < n:
                buf.append(command[i])
                i += 1
            continue
        if char == '"':
            buf.append(char)
            i += 1
            while i < n and command[i] != '"':
                if command[i] == "\\" and i + 1 < n:
                    buf.append(command[i])
                    buf.append(command[i + 1])
                    i += 2
                    continue
                buf.append(command[i])
                i += 1
            if i < n:
                buf.append(command[i])
                i += 1
            continue
        if command.startswith("<<", i) and not command.startswith("<<<", i):
            j = i + 2
            strip_tabs = False
            if j < n and command[j] == "-":
                strip_tabs = True
                j += 1
            while j < n and command[j] in " \t":
                j += 1
            if j < n and command[j] in "\"'":
                quote = command[j]
                j += 1
                start = j
                while j < n and command[j] != quote:
                    j += 1
                delim = command[start:j]
                if j < n:
                    j += 1
            else:
                start = j
                while j < n and command[j] not in " \t\n|&;<>":
                    j += 1
                delim = command[start:j]
            buf.append(command[i:j])
            if delim:
                openings.append({"delim": delim, "strip": strip_tabs, "dest": "buf"})
            i = j
            continue
        if char == "\n":
            if openings:
                i = consume_open_heredocs(i)
                flush_segment()
                continue
            flush_segment()
            i += 1
            continue
        if char == ";":
            flush_segment()
            i += 1
            continue
        if char == "&" and i + 1 < n and command[i + 1] == "&":
            flush_segment()
            i += 2
            continue
        if char == "|" and i + 1 < n and command[i + 1] == "|":
            flush_segment()
            i += 2
            continue
        if char == "|":
            flush_stage()
            i += 1
            if i < n and command[i] == "&":
                i += 1
            continue
        buf.append(char)
        i += 1

    if openings:
        consume_open_heredocs(i)
    flush_segment()
    return segments


def _stage_names_masked(stage: str) -> bool:
    return any(_is_masked_path(path) for path in _ABS_PATH.findall(stage))


def _masked_cache_decision(command: str) -> str | None:
    # A masked-cache read fails only when a read-verb segment names
    # MASKED_CONDA_PKGS and the observation cannot have come from anywhere
    # else: every other output-producing segment also names that cache.
    # ``cd``, ``echo``, and ``true`` are not producers. ``head``, ``tail``,
    # ``grep``, ``sort``, and ``wc`` after a masked-path stage are filters of
    # that stage, not other producers. If another segment can plausibly
    # produce the output (``id``, ``umount``, ``pip cache list``,
    # ``python -c``, and anything else that does not name the cache), the
    # command is ``ambiguous`` and does not fail the audit.
    masked_read = False
    foreign = False
    touched = False
    for stages in _split_command(command):
        seen_masked = False
        for stage in stages:
            verb = _command_verb(stage)
            names_masked = _stage_names_masked(stage)
            if verb in _PIPELINE_FILTERS and seen_masked and not names_masked:
                continue
            if names_masked:
                seen_masked = True
                touched = True
                if _is_listing_verb(verb) or verb in _NO_OP_VERBS:
                    continue
                masked_read = True
                continue
            if verb in _NO_OP_VERBS or not verb:
                continue
            foreign = True
    if masked_read and not foreign:
        return "fail"
    if touched and foreign:
        return "ambiguous"
    return None


def _is_masked_path(path: str) -> bool:
    return path == MASKED_CONDA_PKGS or path.startswith(MASKED_CONDA_PKGS + "/")


def _is_pip_vendor(path: str, import_name: str) -> bool:
    needle = f"{UNMASKABLE_PIP_VENDOR}/{import_name}"
    return f"{needle}/" in path or path.rstrip("/").endswith(needle)


def _is_legitimate_testbed(path: str, import_name: str) -> bool:
    """The image's own base-commit install. Vendor copies under it still count."""
    if LEGITIMATE_TESTBED_ENV not in path or _is_pip_vendor(path, import_name):
        return False
    return re.search(
        rf"/site-packages/{re.escape(import_name)}(?:/|$)", path
    ) is not None


def _is_unmaskable(path: str, import_name: str) -> bool:
    if _is_pip_vendor(path, import_name):
        return True
    if path.startswith(UNMASKABLE_CONDA_LIB + "/") and LEGITIMATE_TESTBED_ENV not in path:
        if re.search(
            rf"/python[^/]*/site-packages/{re.escape(import_name)}(?:/|$)", path
        ):
            return True
    needle = f"{UNMASKABLE_DIST_PACKAGES}/{import_name}"
    return f"{needle}/" in path or path.rstrip("/").endswith(needle)


def _path_tier(path: str, import_name: str) -> str | None:
    """`masked`, `unmaskable`, or None when the path is not a newer copy."""
    if _is_masked_path(path):
        return "masked"
    if _is_legitimate_testbed(path, import_name):
        return None
    if _is_unmaskable(path, import_name):
        return "unmaskable"
    return None


def _observation(content: str) -> tuple[int | None, str]:
    code_match = re.search(r"<returncode>\s*(-?\d+)\s*</returncode>", content)
    output_match = re.search(r"<output>(.*?)</output>", content, re.DOTALL)
    code = int(code_match.group(1)) if code_match else None
    output = output_match.group(1).strip() if output_match else ""
    return code, output


def _bash_calls(message: dict) -> list[tuple[str, str]]:
    calls = message.get("tool_calls") or []
    found: list[tuple[str, str]] = []
    if not isinstance(calls, list):
        return found
    for index, call in enumerate(calls):
        if not isinstance(call, dict):
            continue
        function = call.get("function") or {}
        if not isinstance(function, dict) or function.get("name") != "bash":
            continue
        arguments = function.get("arguments")
        command = ""
        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                command = str(parsed.get("command") or "")
        elif isinstance(arguments, dict):
            command = str(arguments.get("command") or "")
        if command:
            found.append((str(call.get("id") or f"call-{index}"), command))
    return found


def scan_newer_copies(path: Path, text: str, instance_id: str) -> list[Finding]:
    """Newer-copy reads in one agent or V4-generator trajectory.

    A command counts only when its matching tool observation has returncode 0
    and, for a read, non-empty output. Listing verbs (`ls`, `find`, `stat`,
    `du`, `test`, `[`, `which`, and `pip show` / `pip list`) are recorded as
    `newer-copy-listing` and do not fail the audit. Any other verb, including
    one this list does not know, is a read.

    Masked-cache reads are decided per segment, not from the command's first
    word. See `_masked_cache_decision`. A read that survives that rule is a
    confirmed `newer-copy-path`. A compound command whose output could have
    come from another segment is `newer-copy-ambiguous` and does not fail.
    A read of an unmaskable copy is `newer-copy-path` with severity
    `exposed-copy` and detail `exposed_copy`, one per task, and is not a
    confirmed leak. The task's own install under `LEGITIMATE_TESTBED_ENV` is
    ignored, except `pip/_vendor` paths there.
    """
    import_name = import_name_for_instance(instance_id)
    pending: dict[str, str] = {}
    findings: list[Finding] = []
    exposed = False
    for raw in text.splitlines():
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        if role == "assistant":
            for call_id, command in _bash_calls(message):
                pending[call_id] = command
            continue
        if role != "tool":
            continue
        call_id = str(message.get("tool_call_id") or "")
        command = pending.pop(call_id, None)
        if command is None:
            continue
        code, output = _observation(str(message.get("content") or ""))
        if code != 0:
            continue
        tiers = {
            _path_tier(candidate, import_name)
            for candidate in _ABS_PATH.findall(command)
        }
        tiers.discard(None)
        if not tiers:
            continue
        # Tier (b), the unmaskable copy, still follows the whole command.
        # Only the masked cache is split into segments: a later `sed` is a
        # read even when the command starts with `ls`, and a masked path
        # beside `id` or `pip cache list` is not a confirmed read.
        decision = _masked_cache_decision(command) if "masked" in tiers else None
        listing = _is_listing(command)
        if decision == "fail" and output:
            findings.append(Finding(
                severity=Severity.CONFIRMED,
                kind="newer-copy-path",
                path=str(path),
                detail=f"masked package cache returned content: {command[:160]}",
            ))
        elif decision == "ambiguous" and output:
            findings.append(Finding(
                severity=Severity.EXPOSED_COPY,
                kind="newer-copy-ambiguous",
                path=str(path),
                detail=(
                    "masked path shares the command with another segment that "
                    f"can produce the output: {command[:160]}"
                ),
            ))
        elif listing:
            findings.append(Finding(
                severity=Severity.EXPOSED_COPY,
                kind="newer-copy-listing",
                path=str(path),
                detail=f"listing only: {command[:160]}",
            ))
        if listing:
            continue
        if not output:
            continue
        if "unmaskable" in tiers and not exposed:
            exposed = True
            findings.append(Finding(
                severity=Severity.EXPOSED_COPY,
                kind="newer-copy-path",
                path=str(path),
                detail=f"exposed_copy {instance_id}",
            ))
    return findings


def audit_task(
    task_dir: Path, probes: OracleProbes | None = None
) -> tuple[list[Finding], int]:
    """Audit one task directory. Returns its findings and how many files it read."""
    findings: list[Finding] = []
    files = scan_files(task_dir)
    authored = agent_authored_lines(task_dir, probes) if probes is not None else frozenset()

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(
                severity=Severity.CONFIRMED, kind="unreadable", path=str(path),
                detail=f"could not be scanned, so it cannot be cleared: {exc}",
            ))
            continue

        findings.extend(scan_field_names(path, text))
        if path.name in TRAJECTORY_FILES:
            findings.extend(scan_newer_copies(path, text, task_dir.name))
        if probes is not None and not probes.is_empty:
            findings.extend(scan_content(path, text, probes, authored))

    return findings, len(files)


def audit(
    task_dirs: list[Path], probes_by_instance: dict[str, OracleProbes] | None = None
) -> AuditResult:
    """Audit every task directory given.

    `probes_by_instance` is optional so the structural half can run without
    dataset access, but a caller that omits it gets `content_checked_tasks` of
    zero, and the gate script treats a partial audit as a failure rather than
    reporting it as clean.
    """
    probes_by_instance = probes_by_instance or {}
    result = AuditResult()

    for task_dir in task_dirs:
        probes = probes_by_instance.get(task_dir.name)
        findings, n_files = audit_task(task_dir, probes)

        result.findings.extend(findings)
        result.scanned_files += n_files
        result.scanned_tasks += 1
        if probes is not None and not probes.is_empty:
            result.content_checked_tasks += 1

    return result


def find_task_dirs(runs_root: Path) -> list[Path]:
    """Every agent-produced task directory under a runs root, and every V4 generator directory.

    A generator directory is `<exp>/_reproduction_cache/<instance_id>/`, named
    by instance like a task directory, so it gets the same oracle probes.

    Keyed on the presence of a repair record, which excludes the Phase 1 harness
    controls. Those legitimately contain gold patches — they exist to evaluate
    them — and scanning them would produce a guaranteed hit that trains the
    reader to ignore this audit.
    """
    # `runs/` holds many experiments (`*/tasks/...`). The runner and the
    # interim report pass one experiment directory (`tasks/...`). Both are roots.
    patterns = (
        "*/tasks/*/repair_record.json",
        "tasks/*/repair_record.json",
        "*/_reproduction_cache/*/generation_trajectory.jsonl",
        "_reproduction_cache/*/generation_trajectory.jsonl",
    )
    found: set[Path] = set()
    for pattern in patterns:
        found.update(path.parent for path in runs_root.glob(pattern))
    return sorted(found)


__all__ = [
    "ORACLE_FIELD_NAMES",
    "AuditResult",
    "Finding",
    "OracleProbes",
    "Severity",
    "agent_authored_lines",
    "audit",
    "audit_task",
    "distinctive_lines",
    "find_task_dirs",
    "in_scope",
    "probes_from_oracle",
    "without_base_lines",
]
