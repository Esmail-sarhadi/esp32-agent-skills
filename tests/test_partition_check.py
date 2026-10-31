import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "partition_check.py")
GOOD = os.path.join(ROOT, "examples", "partitions-ota-4mb.csv")
BROKEN = os.path.join(ROOT, "examples", "partitions-broken.csv")


def run(*args):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        capture_output=True,
        text=True,
        check=False,
    )


class PartitionCheckTest(unittest.TestCase):
    def test_valid_ota_layout_passes(self):
        result = run("--file", GOOD, "--flash", "4MB", "--ota")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("app0", result.stdout)
        self.assertIn("app1", result.stdout)

    def test_broken_layout_fails(self):
        result = run("--file", BROKEN, "--flash", "4MB", "--ota")
        self.assertEqual(result.returncode, 1)

    def test_alignment_is_enforced(self):
        result = run("--file", BROKEN, "--flash", "4MB", "--ota")
        self.assertIn("aligned to 0x10000", result.stdout)

    def test_overlap_is_detected(self):
        result = run("--file", BROKEN, "--flash", "4MB", "--ota")
        self.assertIn("overlaps", result.stdout)

    def test_overflowing_flash_is_detected(self):
        result = run("--file", BROKEN, "--flash", "4MB", "--ota")
        self.assertIn("past the end of 4MB", result.stdout)

    def test_ota_requires_two_equal_slots(self):
        result = run("--file", BROKEN, "--flash", "4MB", "--ota")
        self.assertIn("do not have the same size", result.stdout)

    def test_json_output(self):
        result = run("--file", GOOD, "--flash", "4MB", "--ota", "--json")
        data = json.loads(result.stdout)
        self.assertEqual(data["errors"], 0)
        self.assertEqual(data["flash"], 4 * 1024 * 1024)
        self.assertEqual(data["partitions"][0]["name"], "nvs")

    def test_unreadable_size_is_rejected(self):
        result = run("--file", GOOD, "--flash", "big")
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read size", result.stderr)


if __name__ == "__main__":
    unittest.main()
