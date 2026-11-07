import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "panic_decode.py")
LOG = os.path.join(ROOT, "examples", "panic-log.txt")


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        capture_output=True,
        text=True,
        input=stdin,
        check=False,
    )


class PanicDecodeTest(unittest.TestCase):
    def test_reason_is_extracted(self):
        result = run("--file", LOG)
        self.assertEqual(result.returncode, 0)
        self.assertIn("LoadProhibited", result.stdout)
        self.assertIn("bad pointer", result.stdout)

    def test_core_is_extracted(self):
        result = run("--file", LOG, "--json")
        self.assertEqual(json.loads(result.stdout)["core"], 1)

    def test_frames_are_in_backtrace_order(self):
        result = run("--file", LOG, "--json")
        frames = json.loads(result.stdout)["frames"]
        self.assertEqual(len(frames), 4)
        self.assertEqual(frames[0], "0x400d4a3e")
        self.assertEqual(frames[-1], "0x400d0d45")

    def test_addr2line_command_contains_every_frame(self):
        result = run("--file", LOG, "--elf", "fw.elf", "--json")
        command = json.loads(result.stdout)["command"]
        self.assertIn("-e fw.elf", command)
        for frame in ("0x400d4a3e", "0x400d1f29", "0x400d0c81", "0x400d0d45"):
            self.assertIn(frame, command)

    def test_excvaddr_is_read_with_either_separator(self):
        text = "Guru Meditation Error: Core  1 panic'ed (StoreProhibited).\nEXCVADDR: 0x00000004\n"
        result = run("--json", stdin=text)
        self.assertEqual(json.loads(result.stdout)["excvaddr"], "0x00000004")

    def test_non_panic_input_is_rejected(self):
        result = run(stdin="hello world\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no panic found", result.stdout)

    def test_pc_is_used_when_there_is_no_backtrace(self):
        text = "Guru Meditation Error: Core  0 panic'ed (IllegalInstruction).\nPC      : 0x40081234  PS      : 0x00060d30\n"
        result = run("--json", stdin=text)
        self.assertEqual(json.loads(result.stdout)["frames"], ["0x40081234"])


if __name__ == "__main__":
    unittest.main()
