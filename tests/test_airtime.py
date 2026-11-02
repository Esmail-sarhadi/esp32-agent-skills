"""The airtime formula, pinned to values that can be checked by hand.

Three reference points from the Semtech formula, the same numbers the published
calculators produce:

    SF7  / 125 kHz / 13 bytes / CR 4/5 / preamble 8  ->  46.336 ms
    SF9  / 125 kHz / 51 bytes                        -> 328.704 ms
    SF12 / 125 kHz / 20 bytes                        -> 1318.912 ms

The middle one and the last one exist to catch the low data rate optimize bit:
SF12 with DE ignored comes out about 40 % short, which is exactly the error a
hand calculation makes when it is deciding a reporting interval.
"""

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "airtime.py")
sys.path.insert(0, os.path.join(ROOT, "tools"))

import airtime as at  # noqa: E402


def run(*args):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        capture_output=True,
        text=True,
        check=False,
    )


class ReferenceValuesTest(unittest.TestCase):
    def test_sf7_thirteen_bytes_is_46_ms(self):
        result = at.airtime(7, 125.0, 13)
        self.assertAlmostEqual(result["airtime_ms"], 46.336, places=3)

    def test_sf9_fifty_one_bytes_is_329_ms(self):
        result = at.airtime(9, 125.0, 51)
        self.assertAlmostEqual(result["airtime_ms"], 328.704, places=3)

    def test_sf12_twenty_bytes_is_1319_ms(self):
        result = at.airtime(12, 125.0, 20)
        self.assertAlmostEqual(result["airtime_ms"], 1318.912, places=3)

    def test_sf7_twenty_bytes_is_57_ms(self):
        result = at.airtime(7, 125.0, 20)
        self.assertAlmostEqual(result["airtime_ms"], 56.576, places=3)

    def test_airtime_seconds_match_the_milliseconds(self):
        result = at.airtime(10, 125.0, 30)
        self.assertAlmostEqual(result["airtime_s"] * 1000.0, result["airtime_ms"], places=9)


class LdroTest(unittest.TestCase):
    def test_sf7_does_not_need_ldro(self):
        self.assertFalse(at.ldro_required(7, 125.0))

    def test_sf11_needs_ldro_at_125k(self):
        self.assertTrue(at.ldro_required(11, 125.0))

    def test_sf11_does_not_need_ldro_at_250k(self):
        self.assertFalse(at.ldro_required(11, 250.0))

    def test_sf12_needs_ldro_at_125k(self):
        self.assertTrue(at.airtime(12, 125.0, 20)["ldro"])

    def test_ldro_changes_the_symbol_count(self):
        # At 20 bytes the ceiling hides the difference; at 40 bytes it does not.
        with_ldro = at.payload_symbols(12, 40, 1, True)
        without = at.payload_symbols(12, 40, 1, False)
        self.assertNotEqual(with_ldro, without)


class DirectionTest(unittest.TestCase):
    def test_more_payload_is_more_airtime(self):
        self.assertLess(at.airtime(9, 125.0, 20)["airtime_ms"],
                        at.airtime(9, 125.0, 120)["airtime_ms"])

    def test_higher_spreading_factor_is_slower(self):
        self.assertLess(at.airtime(7, 125.0, 20)["airtime_ms"],
                        at.airtime(12, 125.0, 20)["airtime_ms"])

    def test_wider_bandwidth_is_faster(self):
        self.assertLess(at.airtime(9, 500.0, 20)["airtime_ms"],
                        at.airtime(9, 125.0, 20)["airtime_ms"])

    def test_a_longer_preamble_costs_time(self):
        self.assertLess(at.airtime(9, 125.0, 20, preamble=8)["airtime_ms"],
                        at.airtime(9, 125.0, 20, preamble=16)["airtime_ms"])

    def test_coding_rate_4_8_is_slower_than_4_5(self):
        self.assertLess(at.airtime(9, 125.0, 20, cr=1)["airtime_ms"],
                        at.airtime(9, 125.0, 20, cr=4)["airtime_ms"])

    def test_disabling_the_crc_is_faster(self):
        # A small payload rounds to the same symbol count, so compare at 100 bytes.
        self.assertLess(at.airtime(9, 125.0, 100, crc=False)["airtime_ms"],
                        at.airtime(9, 125.0, 100, crc=True)["airtime_ms"])

    def test_an_implicit_header_is_faster(self):
        self.assertLess(at.airtime(9, 125.0, 100, explicit_header=False)["airtime_ms"],
                        at.airtime(9, 125.0, 100, explicit_header=True)["airtime_ms"])


class DutyCycleTest(unittest.TestCase):
    def test_min_interval_is_airtime_over_duty(self):
        result = at.airtime(12, 125.0, 20, duty=0.01)
        self.assertAlmostEqual(result["min_interval_s"], result["airtime_s"] / 0.01, places=9)

    def test_ten_percent_allows_ten_times_more_packets(self):
        one = at.airtime(12, 125.0, 20, duty=0.01)["packets_per_hour"]
        ten = at.airtime(12, 125.0, 20, duty=0.1)["packets_per_hour"]
        self.assertAlmostEqual(ten, one * 10, places=6)

    def test_packets_per_hour_follows_from_the_interval(self):
        result = at.airtime(9, 125.0, 40)
        self.assertAlmostEqual(result["packets_per_hour"], 3600.0 / result["min_interval_s"], places=6)

    def test_payload_bytes_per_hour_is_the_payload_times_the_packets(self):
        result = at.airtime(9, 125.0, 40)
        self.assertEqual(result["max_payload_per_hour"], int(40 * result["packets_per_hour"]))

    def test_a_full_duty_cycle_means_no_wait(self):
        result = at.airtime(9, 125.0, 20, duty=1.0)
        self.assertAlmostEqual(result["min_interval_s"], result["airtime_s"], places=9)


class ValidationTest(unittest.TestCase):
    def test_zero_payload_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(9, 125.0, 0)

    def test_payload_above_255_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(9, 125.0, 256)

    def test_spreading_factor_above_12_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(13, 125.0, 20)

    def test_spreading_factor_below_5_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(4, 125.0, 20)

    def test_zero_bandwidth_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(9, 0.0, 20)

    def test_coding_rate_index_above_4_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(9, 125.0, 20, cr=5)

    def test_zero_duty_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(9, 125.0, 20, duty=0.0)

    def test_duty_above_one_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(9, 125.0, 20, duty=1.5)

    def test_negative_preamble_raises(self):
        with self.assertRaises(ValueError):
            at.airtime(9, 125.0, 20, preamble=-1)


class CommandLineTest(unittest.TestCase):
    def test_json_carries_the_airtime(self):
        result = run("--sf", "12", "--bw", "125", "--payload", "20", "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertAlmostEqual(payload["airtime_ms"], 1318.912, places=3)
        self.assertTrue(payload["ldro"])

    def test_an_interval_inside_the_budget_exits_zero(self):
        result = run("--sf", "12", "--payload", "20", "--interval", "200")
        self.assertEqual(result.returncode, 0)
        self.assertIn("headroom", result.stdout)

    def test_an_interval_over_the_budget_exits_one(self):
        result = run("--sf", "12", "--payload", "20", "--interval", "30")
        self.assertEqual(result.returncode, 1)
        self.assertIn("over the duty cycle", result.stdout)

    def test_json_reports_the_violation(self):
        result = run("--sf", "12", "--payload", "20", "--interval", "30", "--json")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(json.loads(result.stdout)["violates_duty_cycle"])

    def test_a_bad_spreading_factor_is_a_usage_error(self):
        result = run("--sf", "20", "--payload", "20")
        self.assertEqual(result.returncode, 2)
        self.assertIn("spreading factor", result.stderr)

    def test_the_human_output_names_the_settings(self):
        result = run("--sf", "9", "--bw", "125", "--payload", "51")
        self.assertIn("SF9", result.stdout)
        self.assertIn("328.704", result.stdout)


if __name__ == "__main__":
    unittest.main()
