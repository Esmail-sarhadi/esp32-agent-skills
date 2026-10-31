import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "power_budget.py")


def run(*args):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        capture_output=True,
        text=True,
        check=False,
    )


class PowerBudgetTest(unittest.TestCase):
    def test_known_duty_cycle(self):
        # 12 wakes/hour * 2000 ms = 0.667% duty; 240 mA for 250 ms per wake,
        # 80 mA while idle, 10 uA asleep -> 0.677 mA average.
        result = run("--battery", "3000", "--wakes-per-hour", "12",
                     "--wake-ms", "2000", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertAlmostEqual(data["average_ma"], 0.6767, places=3)
        self.assertAlmostEqual(data["days"], 184.7, places=1)
        self.assertAlmostEqual(data["duty_cycle_percent"], 0.6667, places=3)

    def test_breakdown_sums_to_average(self):
        result = run("--battery", "2000", "--wakes-per-hour", "60",
                     "--wake-ms", "800", "--json")
        data = json.loads(result.stdout)
        total = sum(data["breakdown_ma"].values())
        self.assertAlmostEqual(total, data["average_ma"], places=9)

    def test_dominant_term_is_reported(self):
        result = run("--battery", "3000", "--wakes-per-hour", "12",
                     "--wake-ms", "2000", "--json")
        data = json.loads(result.stdout)
        self.assertIn(data["dominant_term"], ("sleep", "idle", "tx"))
        self.assertGreaterEqual(data["dominant_percent"], 33.0)

    def test_tx_longer_than_wake_is_rejected(self):
        result = run("--battery", "3000", "--wakes-per-hour", "10",
                     "--wake-ms", "100", "--tx-ms", "500")
        self.assertEqual(result.returncode, 2)
        self.assertIn("tx_ms cannot exceed wake_ms", result.stderr)

    def test_more_than_full_duty_is_rejected(self):
        result = run("--battery", "3000", "--wakes-per-hour", "60",
                     "--wake-ms", "70000")
        self.assertEqual(result.returncode, 2)
        self.assertIn("awake more than 100%", result.stderr)

    def test_human_output_mentions_life(self):
        result = run("--battery", "3000", "--wakes-per-hour", "12", "--wake-ms", "2000")
        self.assertIn("battery life", result.stdout)
        self.assertIn("dominant term", result.stdout)


if __name__ == "__main__":
    unittest.main()
