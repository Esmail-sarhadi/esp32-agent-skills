import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = os.path.join(ROOT, "tools", "render_pin_table.py")
REFERENCE = os.path.join(ROOT, "skills", "esp32-pin-safety", "reference", "pin-table.md")


class ReferenceTableTest(unittest.TestCase):
    """The reference table is generated, so a mismatch means someone edited it
    by hand instead of changing the JSON. That is the failure this catches."""

    def test_reference_file_matches_the_json(self):
        result = subprocess.run(
            [sys.executable, RENDER], capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(REFERENCE, "r", encoding="utf-8") as handle:
            committed = handle.read()
        self.assertEqual(
            result.stdout, committed,
            "reference/pin-table.md is stale; run: python tools/render_pin_table.py --write",
        )

    def test_reference_covers_every_pin_of_every_soc(self):
        with open(REFERENCE, "r", encoding="utf-8") as handle:
            text = handle.read()
        # 40 pins on the classic ESP32, 49 on the S3, 22 on the C3, plus headers
        rows = [line for line in text.splitlines() if line.startswith("| ") and "---" not in line]
        self.assertGreaterEqual(len(rows), 111 + 3)


if __name__ == "__main__":
    unittest.main()
