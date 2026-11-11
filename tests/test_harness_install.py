"""Regression tests for the multi-harness installer."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"


@unittest.skipUnless(shutil.which("bash"), "bash is required for install.sh tests")
class HarnessInstallerTests(unittest.TestCase):
    def run_installer(self, *args, home):
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            ["bash", str(INSTALLER), *args],
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_codex_installs_to_native_agents_skills_path(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            result = self.run_installer("--harness", "codex", home=home)
            self.assertEqual(result.returncode, 0, result.stderr)
            target = home / ".agents" / "skills"
            installed = list(target.glob("*/SKILL.md"))
            self.assertEqual(len(installed), 657)
            self.assertTrue((target / "esp32-pin-safety" / "SKILL.md").is_file())

    def test_second_install_is_idempotent_and_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            first = self.run_installer("--harness", "codex", home=home)
            self.assertEqual(first.returncode, 0, first.stderr)
            skill = home / ".agents" / "skills" / "esp32-pin-safety" / "SKILL.md"
            skill.write_text("user-edited\n", encoding="utf-8")
            second = self.run_installer("--harness", "codex", home=home)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("657 already present, left alone", second.stdout)
            self.assertEqual(skill.read_text(encoding="utf-8"), "user-edited\n")

    def test_force_replaces_existing_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            target = home / ".agents" / "skills" / "esp32-pin-safety"
            target.mkdir(parents=True)
            (target / "SKILL.md").write_text("stale\n", encoding="utf-8")
            result = self.run_installer("--harness", "codex", "--force", home=home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotEqual((target / "SKILL.md").read_text(encoding="utf-8"), "stale\n")

    def test_dry_run_does_not_create_target(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            result = self.run_installer("--harness", "opencode", "--dry-run", home=home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("657 skill(s) would be installed", result.stdout)
            self.assertFalse((home / ".config" / "opencode" / "skills").exists())

    def test_unknown_harness_fails_clearly(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_installer("--harness", "unknown", home=Path(temp))
            self.assertEqual(result.returncode, 2)
            self.assertIn("unsupported harness", result.stderr)


if __name__ == "__main__":
    unittest.main()
