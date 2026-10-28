"""Post-freeze report typography only; never reads or changes selector results."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    path = HERE / "report.md"
    original = path.read_bytes()
    text = original.decode()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("| PRIMARY_COMPLETE | SECONDARY_RESOLVED_PLUS_AMBIGUOUS | C3 |"):
            lines[index] = line.replace("Fixed six; secondary does not decide",
                                        "Frozen eligible NOT_AVAILABLE pool; secondary does not decide")
    text = "\n".join(lines) + "\n"
    text = text.replace("explicit completion line were verified before any successful-output hash or analysis.\n**No ranking",
                        "explicit completion line were verified before any successful-output hash or analysis.\n\n**No ranking")
    note = ("Report-only correction after the selector freeze: the secondary C3 row's denominator note now "
            "names its frozen eligible NOT_AVAILABLE pool, rather than incorrectly saying 'fixed six'. "
            "All counts, thresholds, criteria and decisions are unchanged. The correction source and original/final "
            "report hashes are recorded in `report_corrections.json`; frozen selector/code inputs are untouched.")
    if note not in text:
        text = text.replace("Every autonomous rerun is listed below;", note + "\n\nEvery autonomous rerun is listed below;", 1)
    command = "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/finalize_report.py"
    if command not in text:
        report_command = "env -u PYTHONPATH .venv/bin/python -B reports/callgraph_selection/phase2/run.py --stage report"
        text = text.replace(report_command, report_command + "\n" + command, 1)
    path.write_text(text)
    metadata = dict(scope="POST-FREEZE REPORT TYPOGRAPHY ONLY; no selector or criterion changes",
                    correction="Secondary C3 denominator note and Markdown paragraph separation",
                    source_sha256=digest(Path(__file__).read_bytes()),
                    frozen_selector_manifest_sha256=digest((HERE / "selector_freeze.json").read_bytes()),
                    original_report_sha256=digest(original), final_report_sha256=digest(path.read_bytes()))
    prior = HERE / "report_corrections.json"
    if prior.exists() and json.loads(prior.read_text())["final_report_sha256"] == digest(original):
        metadata["original_report_sha256"] = json.loads(prior.read_text())["original_report_sha256"]
    prior.write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
