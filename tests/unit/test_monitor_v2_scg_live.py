"""Synthetic monitoring evidence only; no benchmark or harness imports."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts/monitor_v2_scg_live.py"
SPEC = importlib.util.spec_from_file_location("standalone_live_monitor", MODULE_PATH)
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


def arm(status="EXECUTED", signal="NOT_AVAILABLE", selected=1):
    return {"execution_status": status, "signal": signal, "selected": selected,
            "completeness": "COMPLETE", "calls": [],
            "selection": {"selection_status": "SELECTED", "graph_status": "complete"}}


class MonitoringEvidenceTests(unittest.TestCase):
    def test_distinguishes_three_not_available_causes_without_graph_inference(self):
        empty = monitor.explain_arm(arm("ZERO_SELECTION", selected=0))
        unavailable = arm("UNAVAILABLE_SELECTION", signal=None, selected=None)
        unavailable["selection"]["selection_status"] = "NO_RESOLVED_SEEDS"
        unavailable = monitor.explain_arm(unavailable)
        executed = monitor.explain_arm(arm())
        self.assertIn("ZERO_SELECTION", empty["reason_groups"])
        self.assertIn("UNAVAILABLE_SELECTION", unavailable["reason_groups"])
        self.assertEqual(unavailable["selection_status"], "NO_RESOLVED_SEEDS")
        self.assertIn("NO_NATIVE_COUNTED_EXECUTIONS", executed["reason_groups"])
        self.assertNotIn("GRAPH_OR_MAPPING_DIAGNOSTICS_RECORDED", empty["reason_groups"])

    def test_parameter_raw_coverage_does_not_promote_native_verdict(self):
        row = arm()
        row["outcomes"] = {"a.py::test_a": "NOT_RUN"}
        row["initial_calls"] = 1
        row["calls"] = [{"patched": False, "requested": ["a.py::test_a"], "run": {
            "requested_tests": ["a.py::test_a"], "timed_out": False, "evidence_complete": True,
            "results": [{"test_id": "a.py::test_a", "status": "not_run"}],
            "raw_results": [{"test_id": "a.py::test_a[one]", "status": "passed"},
                            {"test_id": "a.py::test_a[two]", "status": "skipped"}],
            "raw_id_map": {"a.py::test_a[one]": ["a.py::test_a"],
                           "a.py::test_a[two]": ["a.py::test_a"]}}}]
        explained = monitor.explain_arm(row)
        phase = explained["phases"][0]
        self.assertEqual((phase["raw_concrete_cases"], phase["mapped_selected_count"],
                          phase["admitted_selected_status_count"]), (2, 1, 0))
        self.assertEqual(explained["native_counted_outcomes"], 0)
        self.assertEqual(explained["signal"], "NOT_AVAILABLE")
        self.assertIn("RECORDED_PARAMETER_FAMILY_ADMISSION_GAP", explained["reason_groups"])

    def test_incomplete_original_and_fail_with_gaps_stay_native(self):
        row = arm(signal="INCOMPLETE")
        row.update(original_signal="PASS", completeness="INCOMPLETE_CONFIRMED",
                   incompleteness=["patched: a.py::test_a: timeout"])
        row["calls"] = [{"patched": True, "run": {
            "timed_out": True, "evidence_complete": False,
            "infrastructure_errors": ["runner batch 1 exit 4"]}}]
        result = monitor.explain_arm(row)
        self.assertEqual((result["original_signal"], result["signal"]), ("PASS", "INCOMPLETE"))
        self.assertEqual(result["incompleteness"], row["incompleteness"])
        self.assertTrue({"TIMEOUT", "RUNNER_ERROR", "INCOMPLETE_CAPTURE"} <= set(result["reason_groups"]))
        row["signal"] = "FAIL"
        row["outcomes"] = {"a": "REGRESSION", "b": "ERROR", "c": "TIMEOUT"}
        result = monitor.explain_arm(row)
        self.assertEqual(result["signal"], "FAIL")
        self.assertEqual(result["native_counted_outcomes"], 2)

    def test_snapshot_handles_live_partial_files_and_flags_arm_disagreement(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task = root / "tasks" / "task-a"
            task.mkdir(parents=True)
            pair = {"instance_id": "task-a", "arms": {"v2": arm(signal="PASS"),
                    "scg": arm("ZERO_SELECTION", selected=0)}}
            (task / "paired.json").write_text(json.dumps(pair))
            for name, row in pair["arms"].items():
                (task / name).mkdir()
                data = dict(row)
                if name == "v2":
                    data["signal"] = "FAIL"
                (task / name / "paired_arm.json").write_text(json.dumps(data))
            partial = root / "tasks" / "writing"
            partial.mkdir()
            (partial / "paired.json").write_text('{"arms":')
            snapshot = monitor.snapshot(root)
            self.assertEqual((snapshot["paired_files"], snapshot["arm_files"]), (2, 2))
            self.assertEqual(len(snapshot["records"]), 1)
            self.assertEqual(len(snapshot["warnings"]), 1)
            row = snapshot["records"][0]["arms"]["v2"]
            self.assertEqual(row["signal"], "PASS")
            self.assertIn("ARM_RECORD_CONSISTENCY_WARNING", row["reason_groups"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                monitor.main(["--results", str(root), "--summary"])
            self.assertIn("Tasks: 2/83 (2.41%) | Arms: 2/166", output.getvalue())
            self.assertIn("ZERO_SELECTION", output.getvalue())

    def test_display_bounds_lists_and_retains_exact_reasons_on_request(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            monitor.show_items("Exact reasons", ["first", "second", "third"], 1)
        self.assertIn("2 more", output.getvalue())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            monitor.show_items("Exact reasons", ["first", "second", "third"], 0)
        self.assertIn("third", output.getvalue())
        self.assertNotIn("more", output.getvalue())


if __name__ == "__main__":
    unittest.main()
