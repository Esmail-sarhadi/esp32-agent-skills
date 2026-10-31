import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "pincheck.py")


def run(*args):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        capture_output=True,
        text=True,
        check=False,
    )


class PinCheckTest(unittest.TestCase):
    def test_flash_pin_is_an_error(self):
        result = run("--soc", "esp32", "--assign", "6=led")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SPI flash", result.stdout)

    def test_safe_pin_exits_zero(self):
        result = run("--soc", "esp32", "--assign", "32=led")
        self.assertEqual(result.returncode, 0)
        self.assertIn("no constraint found", result.stdout)

    def test_input_only_pin_warns(self):
        result = run("--soc", "esp32", "--assign", "34=button")
        self.assertEqual(result.returncode, 0)
        self.assertIn("input-only", result.stdout)

    def test_strapping_pin_warns(self):
        result = run("--soc", "esp32", "--assign", "12=relay")
        self.assertIn("strapping pin", result.stdout)

    def test_duplicate_pin_is_an_error(self):
        result = run("--soc", "esp32", "--assign", "25=a,25=b")
        self.assertEqual(result.returncode, 1)
        self.assertIn("assigned twice", result.stdout)

    def test_pin_out_of_range_is_an_error(self):
        result = run("--soc", "esp32c3", "--assign", "40=led")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not exist", result.stdout)

    def test_json_output(self):
        result = run("--soc", "esp32", "--assign", "6=led", "--json")
        data = json.loads(result.stdout)
        self.assertEqual(data["errors"], 1)
        self.assertEqual(data["pins"][0]["pin"], 6)

    def test_unknown_soc_is_rejected(self):
        result = run("--soc", "esp8266", "--assign", "4=led")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown SoC", result.stderr)

    def test_file_input(self):
        path = os.path.join(ROOT, "examples", "pinmap.txt")
        result = run("--soc", "esp32", "--file", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("status_led", result.stdout)


if __name__ == "__main__":
    unittest.main()
