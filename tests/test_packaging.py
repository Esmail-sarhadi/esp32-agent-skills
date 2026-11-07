"""The packaging layer: manifests, schema and the installer.

The repository is only useful to an agent if it can be installed and if the
manifests tell the truth about what is inside. These tests hold the two
together: every count in ``agent.yaml`` and the plugin manifests is compared
against the directory listing, and ``gen_manifest.py --check`` is run the way
CI runs it.
"""

import io
import json
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
TOOLS = os.path.join(ROOT, "tools")
PLUGIN = os.path.join(ROOT, ".claude-plugin")
SCHEMA = os.path.join(ROOT, "schemas", "skill.schema.json")

sys.path.insert(0, TOOLS)

import gen_manifest  # noqa: E402
import validate_skills  # noqa: E402


def skill_dirs():
    return sorted(name for name in os.listdir(SKILLS)
                  if os.path.isfile(os.path.join(SKILLS, name, "SKILL.md")))


def load(path):
    with io.open(path, encoding="utf-8") as handle:
        return json.load(handle)


def read(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


class ManifestTest(unittest.TestCase):
    """agent.yaml, plugin.json and marketplace.json against the tree."""

    def test_agent_yaml_lists_every_skill_and_nothing_else(self):
        text = read(os.path.join(ROOT, "agent.yaml"))
        listed = re.findall(r"^  - (esp32-[a-z0-9-]+)$", text, re.M)
        self.assertEqual(sorted(listed), skill_dirs())

    def test_agent_yaml_lists_all_specialist_roles(self):
        text = read(os.path.join(ROOT, "agent.yaml"))
        listed = re.findall(r"^  - agents/([a-z0-9-]+)\.md$", text, re.M)
        expected = sorted(name[:-3] for name in os.listdir(os.path.join(ROOT, "agents"))
                          if name.endswith(".md") and name.lower() != "readme.md")
        self.assertEqual(listed, expected)

    def test_agent_yaml_lists_all_workflows(self):
        text = read(os.path.join(ROOT, "agent.yaml"))
        listed = re.findall(r"^  - workflows/([a-z0-9-]+)\.md$", text, re.M)
        expected = sorted(name[:-3] for name in os.listdir(os.path.join(ROOT, "workflows"))
                          if name.endswith(".md"))
        self.assertEqual(listed, expected)

    def test_agent_yaml_version_matches_the_version_file(self):
        text = read(os.path.join(ROOT, "agent.yaml"))
        version = read(os.path.join(ROOT, "VERSION")).strip()
        self.assertIn('version: "%s"' % version, text)

    def test_plugin_json_is_valid_and_names_the_repository(self):
        payload = load(os.path.join(PLUGIN, "plugin.json"))
        self.assertEqual(payload["name"], "esp32-agent-skills")
        self.assertEqual(payload["license"], "MIT")
        self.assertIn("github.com/Esmail-sarhadi/esp32-agent-skills",
                      payload["repository"])

    def test_plugin_json_version_matches_the_version_file(self):
        payload = load(os.path.join(PLUGIN, "plugin.json"))
        version = read(os.path.join(ROOT, "VERSION")).strip()
        self.assertEqual(payload["version"], version)

    def test_marketplace_points_at_the_repository_root(self):
        payload = load(os.path.join(PLUGIN, "marketplace.json"))
        self.assertEqual(payload["name"], "esp32-agent-skills")
        self.assertEqual(len(payload["plugins"]), 1)
        self.assertEqual(payload["plugins"][0]["source"], "./")
        self.assertEqual(payload["plugins"][0]["name"], "esp32-agent-skills")

    def test_marketplace_version_matches_the_plugin(self):
        plugin = load(os.path.join(PLUGIN, "plugin.json"))
        marketplace = load(os.path.join(PLUGIN, "marketplace.json"))
        self.assertEqual(marketplace["plugins"][0]["version"], plugin["version"])

    def test_counts_in_the_descriptions_come_from_the_tree(self):
        """A description that says '101 skills' must be reading 101 directories."""
        plugin = load(os.path.join(PLUGIN, "plugin.json"))
        expected = "%d ESP32 firmware skills and %d checkers" % (
            len(skill_dirs()), len(gen_manifest.collect_tools()))
        self.assertIn(expected, plugin["description"])

    def test_manifests_are_in_sync_with_the_tree(self):
        result = subprocess.run(
            [sys.executable, os.path.join(TOOLS, "gen_manifest.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0,
                         "gen_manifest --check failed:\n%s%s" % (result.stdout, result.stderr))

    def test_generator_is_deterministic(self):
        first = [(path, content) for path, content in gen_manifest.targets()]
        second = [(path, content) for path, content in gen_manifest.targets()]
        self.assertEqual(first, second)


class SchemaTest(unittest.TestCase):
    """The schema file and the validator must describe the same contract."""

    def test_schema_is_valid_json_with_the_expected_required_keys(self):
        schema = load(SCHEMA)
        self.assertEqual(schema["type"], "object")
        self.assertEqual(sorted(schema["required"]), sorted(validate_skills.REQUIRED))

    def test_schema_forbids_unknown_keys_like_the_validator_does(self):
        schema = load(SCHEMA)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(sorted(schema["properties"]), sorted(validate_skills.ALLOWED))

    def test_schema_name_pattern_matches_the_validator(self):
        schema = load(SCHEMA)
        self.assertEqual(schema["properties"]["name"]["pattern"],
                         validate_skills.NAME_RE.pattern)

    def test_schema_description_prefix_matches_the_validator(self):
        schema = load(SCHEMA)
        self.assertEqual(schema["properties"]["description"]["pattern"],
                         "^" + validate_skills.DESCRIPTION_PREFIX + " ")


class CorpusValidityTest(unittest.TestCase):
    """Every skill passes the validator, and the validator is not vacuous."""

    def test_every_skill_passes_the_validator(self):
        problems = validate_skills.validate_all()
        self.assertEqual(problems, [], "\n".join(problems))

    def test_every_skill_declares_the_mit_license(self):
        for name in skill_dirs():
            fields = gen_manifest.parse_frontmatter(
                read(os.path.join(SKILLS, name, "SKILL.md")))
            self.assertEqual(fields.get("license"), "MIT", name)

    def test_every_skill_ships_a_license_file(self):
        for name in skill_dirs():
            path = os.path.join(SKILLS, name, "LICENSE.txt")
            self.assertTrue(os.path.isfile(path), "%s has no LICENSE.txt" % name)

    def test_validator_rejects_a_description_that_does_not_start_with_use_when(self):
        """A guard against the validator quietly accepting everything."""
        problems = validate_skills.validate_skill("esp32-can-twai")
        self.assertEqual(problems, [])
        fields, _ = validate_skills.parse_frontmatter(
            read(os.path.join(SKILLS, "esp32-can-twai", "SKILL.md")))
        self.assertTrue(fields["description"].startswith("Use when"))


class InstallerTest(unittest.TestCase):
    """The installer lists exactly the skills, and copies without deleting."""

    def test_shell_installer_lists_every_skill(self):
        script = os.path.join(ROOT, "install.sh")
        bash = shutil_which("bash")
        if bash is None:
            self.skipTest("bash is not available")
        result = subprocess.run([bash, script, "--list"], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(result.stdout.split()), skill_dirs())

    def test_shell_installer_dry_run_reports_every_skill(self):
        script = os.path.join(ROOT, "install.sh")
        bash = shutil_which("bash")
        if bash is None:
            self.skipTest("bash is not available")
        result = subprocess.run([bash, script, "--dry-run", "--target", "/tmp/esp32-skills-test"],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("%d skill(s) would be installed" % len(skill_dirs()), result.stdout)


def shutil_which(name):
    from shutil import which
    return which(name)


if __name__ == "__main__":
    unittest.main()
