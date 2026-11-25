"""scripts/build_report_v1_5.py: placeholder filling, README block, number scanner, figures, determinism."""

import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("build_report_v1_5", ROOT / "scripts" / "build_report_v1_5.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_report_v1_5"] = mod
    spec.loader.exec_module(mod)
    return mod


BR = _load()


def test_render_fills_and_rejects_missing():
    assert BR.render("a {{x}} b {{ y }}", {"x": "1", "y": "2"}) == "a 1 b 2"
    with pytest.raises(KeyError):
        BR.render("a {{missing}}", {})


def test_fill_readme_block():
    text = "head\n<!-- results:start -->\nold\n<!-- results:end -->\ntail\n"
    out = BR.fill_block(text, "NEW")
    assert out == "head\n<!-- results:start -->\nNEW\n<!-- results:end -->\ntail\n"
    assert BR.fill_block(out, "NEW") == out
    with pytest.raises(ValueError):
        BR.fill_block("no markers", "x")


def test_formatters():
    assert BR.pct(0.845) == "84.5%" and BR.pct(None) == "n/a"
    r = {"k": 49, "n": 58, "value": 49 / 58, "ci": [0.731, 0.916]}
    assert BR.ci(r) == "84.5% [73.1%, 91.6%]"
    assert BR.kn(r) == "49/58"


def test_scanner_finds_typed_statistics():
    assert BR.typed_numbers("precision was 84.5% overall")
    assert BR.typed_numbers("| a | 12 | b |")
    assert BR.typed_numbers("we saw 17 pairs")
    assert BR.typed_numbers("about 5% more")
    assert BR.typed_numbers("Claude Sonnet 4 accepted 12 patches")
    assert BR.typed_numbers("a 90% CI")


def test_scanner_allows_protocol_constants_and_identifiers():
    ok = ("seed 20261126 with 10,000 resamples on 200 tasks: 92 dev and 108 test (60 and 48).",
          "Rules R1, R3b, H1/H2, RQ5, A1–A8, B15, V1–V4, S1–S3, v1.5, v1.4.1, swebench 5.0.2, gpt-4.1-mini.",
          "Built on 25 Nov 2026 for CIS 695, Fall 2026; PLAN §11; the 500-task plan.",
          "`scripts/x_v1_5.py --seed 7`", "{{pooled_precision}}", "[link](reports/b1/x2.md)",
          "## 7. Results", "1. first item", "```\nrun 123\n```", "<!-- results:start -->",
          "Claude Sonnet 4 and Gemini 2.5 Flash, with Wilson 95% CIs and a 95% CI.")
    for text in ok:
        assert BR.typed_numbers(text) == [], text


def test_template_and_static_readme_have_no_typed_statistics():
    template = (ROOT / "reports/study_v1_5/report_template.md").read_text(encoding="utf-8")
    assert BR.typed_numbers(template) == []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    static = BR.fill_block(readme, "")
    assert BR.typed_numbers(static) == []


def test_svg_is_deterministic():
    pts = [("a", 0.4, (0.3, 0.5), 0.8, (0.6, 0.9)), ("b", 0.2, (0.1, 0.3), 0.7, (0.5, 0.85))]
    one, two = BR.svg_points(pts, "t"), BR.svg_points(pts, "t")
    assert one == two and one.startswith("<svg") and "<text" in one
    bars = [("frozen", 0.845, 0.06), ("V2 forced PASS", 0.707, 0.179)]
    assert BR.svg_bars(bars, "t") == BR.svg_bars(bars, "t")


def test_build_twice_is_identical_and_matches_results(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text((ROOT / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
    out1, out2 = tmp_path / "r1.md", tmp_path / "r2.md"
    BR.build(report_out=out1, readme=readme, figures=tmp_path / "f1")
    first_readme = readme.read_bytes()
    BR.build(report_out=out2, readme=readme, figures=tmp_path / "f2")
    assert out1.read_bytes() == out2.read_bytes()
    assert readme.read_bytes() == first_readme
    assert (tmp_path / "f1/fig1_precision_vs_base.svg").read_bytes() == (tmp_path / "f2/fig1_precision_vs_base.svg").read_bytes()
    final = json.loads((ROOT / "reports/study_v1_5/results/results_final.json").read_text())
    pooled = final["scopes"]["headline (batch, minus headline exclusions)"]["policies"]["frozen"]["pooled"]
    text = out1.read_text(encoding="utf-8")
    assert BR.ci(pooled["accept_precision"]) in text and BR.ci(pooled["base_rate"]) in text
    assert "{{" not in text and "}}" not in text
