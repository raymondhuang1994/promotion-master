"""虚构教学样例的图表输入与披露数值必须能独立对上；不评判生成文案的措辞。"""
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExampleArithmeticTests(unittest.TestCase):
    def test_report_numbers_match_chart_inputs(self):
        path = ROOT / "shared/examples/make_figures.py"
        spec = importlib.util.spec_from_file_location("sample_figures", path)
        figures = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(figures)
        names, weights, groups = figures.example_weights()
        self.assertEqual(len(names), 30)
        self.assertEqual(len(groups), len(weights))
        self.assertAlmostEqual(sum(weights), 100)
        effective = round(1 / sum((w / sum(weights)) ** 2 for w in weights), 1)
        report = json.loads((ROOT / "shared/examples/polaris-mini.json").read_text(encoding="utf-8"))
        table = next(v for kind, v in report["content"] if kind == "t" and v["head"] == ["读法", "数字", "含义"])
        data = {row[0]: float(re.search(r"[\d.]+", row[1]).group()) for row in table["rows"]}
        self.assertAlmostEqual(data["前三大合计"], sum(weights[:3]))
        self.assertEqual(data["有效持股数"], effective)
        self.assertEqual(data["其余成分当日最大权重"], max(weights[3:]))

    def test_relative_tilt_units(self):
        path = ROOT / "shared/scripts/quant_tools.py"
        spec = importlib.util.spec_from_file_location("sample_quant", path)
        quant = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(quant)
        tilt = 48.6 - 33.19
        self.assertEqual(quant.tilt_value(tilt, 10), 1.54)
        self.assertEqual(quant.tilt_value(tilt, -10), -1.54)
        self.assertEqual(round(100 * .40 / tilt, 2), 2.60)


if __name__ == "__main__":
    unittest.main()
