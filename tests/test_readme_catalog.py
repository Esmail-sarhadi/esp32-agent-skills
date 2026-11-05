"""The README skills catalog is generated, not hand-maintained.

A corpus test already asserts that every skill name appears in README.md.
That test fails *after* someone adds a skill and forgets the table. These
tests go one step further: they prove the generator can detect that drift
itself, so CI can say "run the generator" instead of just going red.
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
TOOLS = os.path.join(ROOT, "tools")
README = os.path.join(ROOT, "README.md")
SCRIPT = os.path.join(TOOLS, "gen_readme_catalog.py")

sys.path.insert(0, TOOLS)

import gen_readme_catalog  # noqa: E402


def skill_dirs():
    return sorted(name for name in os.listdir(SKILLS)
                  if os.path.isfile(os.path.join(SKILLS, name, "SKILL.md")))


def run_check(cwd=ROOT):
    return subprocess.run([sys.executable, SCRIPT, "--check"],
                          cwd=cwd, text=True, capture_output=True, check=False)


class ReadmeCatalogTest(unittest.TestCase):

    def test_check_passes_on_the_current_tree(self):
        result = run_check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_skill_has_a_row(self):
        block = gen_readme_catalog.build_catalog()
        for name in skill_dirs():
            self.assertIn("| `%s` |" % name, block, name)

    def test_row_count_equals_skill_count(self):
        block = gen_readme_catalog.build_catalog()
        data_rows = [line for line in block.splitlines()
                     if line.startswith("| `")]
        self.assertEqual(len(data_rows), len(skill_dirs()))

    def test_markers_are_present_in_the_readme(self):
        with open(README, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn(gen_readme_catalog.START, text)
        self.assertIn(gen_readme_catalog.END, text)
        self.assertLess(text.index(gen_readme_catalog.START),
                        text.index(gen_readme_catalog.END))

    def test_generator_is_idempotent(self):
        before = gen_readme_catalog.read_readme()
        once = gen_readme_catalog.splice(before, gen_readme_catalog.build_catalog())
        twice = gen_readme_catalog.splice(once, gen_readme_catalog.build_catalog())
        self.assertEqual(once, twice)

    def test_a_missing_row_is_detected_as_drift(self):
        """This is the regression: the README rewrite dropped the whole table."""
        with open(README, encoding="utf-8") as handle:
            text = handle.read()
        start = text.index(gen_readme_catalog.START)
        end = text.index(gen_readme_catalog.END) + len(gen_readme_catalog.END)
        without_table = text[:start] + text[end:]
        restored = gen_readme_catalog.splice(
            without_table, gen_readme_catalog.build_catalog())
        self.assertNotEqual(restored, without_table)
        self.assertIn("| `%s` |" % skill_dirs()[0], restored)

    def test_a_changed_description_is_detected_as_drift(self):
        with open(README, encoding="utf-8") as handle:
            text = handle.read()
        name = skill_dirs()[0]
        stale = text.replace("| `%s` |" % name, "| `%s` | stale hand edit |" % name, 1)
        self.assertNotEqual(stale, text)
        # Regenerating the stale README must bring back the real description.
        self.assertEqual(
            gen_readme_catalog.splice(stale, gen_readme_catalog.build_catalog()),
            text,
        )

    def test_pipes_in_a_description_cannot_break_the_table(self):
        self.assertEqual(
            gen_readme_catalog.parse_description(
                "---\nname: x\ndescription: Use when a | b\nlicense: MIT\n---\nbody\n"),
            "A \\| b",
        )


if __name__ == "__main__":
    unittest.main()
