"""Verify a sealed E2E source and copy its frozen V4 evidence without execution."""

import hashlib
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from reliability.verifier.reproduction_freeze import MANIFEST, REPRO_DIR, FrozenSuite
from reliability.verifier.source_integrity import SourceIntegrityError
from reliability.verifier.task_specs import require_hash

RECORD = "verification_record.full-v1.4.1.json"


class V4ReuseError(SourceIntegrityError):
    def __init__(self, location, reason):
        super().__init__({"mismatches": [{"path": str(location), "reason": reason}]})


class DisabledGenerator:
    def __init__(self):
        self.calls = 0

    def generate(self, issue_text, instance_id):
        self.calls += 1
        raise V4ReuseError(instance_id, "generator called during frozen V4 reuse")


GENERATOR_OVERRIDE: ContextVar[DisabledGenerator | None] = ContextVar("v4_generator_override", default=None)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _settings(identity):
    design = identity.get("design", "legacy")
    if design == "per_requirement":
        return design, identity["passes"], identity["max_requirements"], identity["prompts"]
    if design == "legacy":
        return design, 1, None, {identity["prompt_path"]: identity["prompt_sha256"]}
    raise ValueError("Invalid V4 design")


class V4Reuse:
    def __init__(self, root: Path, setup, model_config_sha256: str):
        self.root = root.resolve()
        self.generator = DisabledGenerator()
        seal = self.root / "seal.json"
        if not seal.is_file() or seal.is_symlink():
            raise ValueError("V4 source run must have a seal.json")
        raw = seal.read_bytes()
        self.seal_sha256 = _sha256(raw)
        self.files = json.loads(raw).get("files_sha256")
        if not isinstance(self.files, dict) or "header.json" not in self.files:
            raise ValueError("Invalid source run seal inventory")
        paths = list(self.root.rglob("*"))
        if any(path.is_symlink() for path in paths):
            raise ValueError("Source run seal contains a symlink")
        inventory = {path.relative_to(self.root).as_posix() for path in paths
                     if path.is_file() and path != seal}
        if inventory != self.files.keys():
            raise ValueError("Source run files do not match the seal inventory")
        for name, digest in self.files.items():
            require_hash(self.root / name, digest)
        header = json.loads(self._read("header.json"))
        self.settings = _settings(setup.identity())
        try:
            source_settings = _settings(header["generator"])
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("Source run header is missing its V4 settings") from exc
        if (source_settings != self.settings or header.get("generator_config_sha256") != model_config_sha256):
            raise ValueError("Source and destination V4 settings differ")

    @contextmanager
    def prohibit_generation(self):
        token = GENERATOR_OVERRIDE.set(self.generator)
        try:
            yield
        finally:
            GENERATOR_OVERRIDE.reset(token)

    def _read(self, name: str) -> bytes:
        path = self.root / name
        if name not in self.files or path.resolve() != path or not path.is_file():
            raise ValueError("V4 source file is absent from the verified seal: " + name)
        raw = path.read_bytes()
        if _sha256(raw) != self.files[name]:
            raise ValueError("V4 source file SHA-256 mismatch: " + name)
        return raw

    def load(self, instance_id: str, destination: Path) -> FrozenSuite | None:
        try:
            return self._load(instance_id, destination)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise V4ReuseError(instance_id, str(exc)) from exc

    def _load(self, iid: str, destination: Path) -> FrozenSuite | None:
        require_hash(self.root / "seal.json", self.seal_sha256)
        task = f"tasks/{iid}"
        folder = f"{task}/verification/v4"
        if self.settings[0] == "legacy":
            folder += f"/cache/{iid}"
        manifest = f"{folder}/{MANIFEST}"
        record_path = f"{task}/{RECORD}"
        findings = {}
        if record_path in self.files:
            record = json.loads(self._read(record_path))
            if record["instance_id"] != iid:
                raise ValueError("Source V4 record has a different instance ID")
            findings = record["reproduction"]["findings"]
        if manifest not in self.files:
            if "suite_sha256" in findings or (self.root / manifest).exists():
                raise ValueError("Source V4 record is missing its sealed freeze manifest")
            return None

        raw = self._read(manifest)
        data = json.loads(raw)
        if (data["instance_id"] != iid or _settings(data["identity"]) != self.settings
                or data["suite_sha256"] != findings.get("suite_sha256")
                or data["tests"] != findings.get("frozen")):
            raise ValueError("Source V4 freeze does not match its task record")

        files = {MANIFEST: raw}
        requirement_sha = data.get("requirements_sha256")
        if requirement_sha != findings.get("requirements_sha256"):
            raise ValueError("Source V4 requirement SHA-256 differs from its task record")
        if requirement_sha is not None:
            requirements = self._read(f"{folder}/requirements.json")
            if "sha256:" + _sha256(requirements) != requirement_sha:
                raise ValueError("Source V4 requirements SHA-256 mismatch")
            files["requirements.json"] = requirements
        elif f"{folder}/requirements.json" in self.files:
            raise ValueError("Unexpected unrecorded requirement list in source V4 freeze")

        for test in data["tests"]:
            if not test["kept"]:
                continue
            if self.settings[0] == "per_requirement":
                requirement, pass_number = test["requirement_id"], test["pass"]
                if (requirement not in {row["id"] for row in data["requirements"]}
                        or type(pass_number) is not int or not 1 <= pass_number <= self.settings[1]):
                    raise ValueError("Invalid kept V4 requirement or pass")
                name = f"test_repro_{requirement}_p{pass_number}.py"
            else:
                name = Path(test["path"]).name
                if not re.fullmatch(r"test_repro_[1-9][0-9]*\.py", name):
                    raise ValueError("Invalid kept legacy V4 test path")
            if test["path"] != f"{REPRO_DIR}/{name}" or f"tests/{name}" in files:
                raise ValueError("Invalid or duplicate kept V4 test path")
            content = self._read(f"{folder}/tests/{name}")
            if "sha256:" + _sha256(content) != test["sha256"] or len(content) != test["size_bytes"]:
                raise ValueError("Source V4 test SHA-256 or size mismatch: " + name)
            files[f"tests/{name}"] = content

        for name, content in files.items():
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(content)
        suite = FrozenSuite.read(destination)
        if suite.suite_sha256 != data["suite_sha256"]:
            raise ValueError("Source V4 suite SHA-256 mismatch")
        return suite
