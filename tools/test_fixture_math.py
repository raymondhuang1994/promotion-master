"""公开虚构输入的一致性；不能据此宣称生成报告的推论已经正确。"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def rows_with_header(path, first):
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[0] == first:
            result = []
            for item in lines[i + 2:]:
                if not item.startswith("|"):
                    break
                result.append([c.strip() for c in item.strip().strip("|").split("|")])
            return result
    raise ValueError("missing table " + first)


def percent(value):
    return float(value.rstrip("%")) / 100


class FixtureArithmeticTests(unittest.TestCase):
    def test_equipment_input_totals_and_comparison(self):
        source = ROOT / "evals/fixtures/service-equipment.md"
        holdings = rows_with_header(source, "企业")
        self.assertEqual(len(holdings), 8)
        weights = [percent(r[1]) for r in holdings]
        shares = [percent(r[4]) for r in holdings]
        self.assertAlmostEqual(sum(weights), 1)
        for row in holdings:
            self.assertAlmostEqual(percent(row[4]) + percent(row[5]), 1)
            self.assertLessEqual(percent(row[8]), percent(row[4]))
        # 第二张以“企业”为首列的比较表独立读取，避免把同表与自身比较。
        text = source.read_text(encoding="utf-8")
        comparison = text.split("| 企业 | 岚桥工业设备 ETF 权重 |", 1)[1]
        peer = []
        for line in comparison.splitlines()[2:]:
            if not line.startswith("|"):
                break
            peer.append(percent(line.strip().strip("|").split("|")[1].strip()))
        self.assertEqual(len(peer), len(weights))
        self.assertAlmostEqual(sum(peer), 1)
        self.assertAlmostEqual(sum(w * s for w, s in zip(weights, shares)), .4835)
        self.assertAlmostEqual(sum(w * s for w, s in zip(peer, shares)), .376)
        self.assertAlmostEqual(sum(min(a, b) for a, b in zip(weights, peer)), .76)
        self.assertAlmostEqual(sum(float(r[3]) for r in holdings), 520)
        self.assertAlmostEqual(sum(float(r[3]) * percent(r[4]) for r in holdings), 256)

    def test_credit_input_totals_and_rounded_statistics(self):
        source = ROOT / "evals/fixtures/short-credit.md"
        holdings = rows_with_header(source, "债券")
        self.assertEqual(len(holdings), 12)
        self.assertEqual(len({r[1] for r in holdings}), 11)
        weights = [percent(r[3]) for r in holdings]
        self.assertAlmostEqual(sum(weights), 1)
        for rating, expected in [("AA", .40), ("A", .43), ("BBB", .17)]:
            self.assertAlmostEqual(sum(percent(r[3]) for r in holdings if r[4] == rating), expected)
        duration = sum(percent(r[3]) * float(r[6]) for r in holdings)
        maturity = sum(percent(r[3]) * float(r[5]) for r in holdings)
        yield_rate = sum(percent(r[3]) * percent(r[7]) for r in holdings)
        self.assertAlmostEqual(duration, 1.091)
        self.assertAlmostEqual(maturity, 1.176)
        self.assertAlmostEqual(yield_rate, .03626)
        self.assertEqual(round(duration, 2), 1.09)
        self.assertEqual(round(maturity, 2), 1.18)
        self.assertEqual(round(yield_rate * 100, 2), 3.63)
        issuer_weights = {}
        for row in holdings:
            issuer_weights[row[1]] = issuer_weights.get(row[1], 0) + percent(row[3])
        self.assertAlmostEqual(max(issuer_weights.values()), .20)


if __name__ == "__main__":
    unittest.main()
