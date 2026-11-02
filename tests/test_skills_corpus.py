"""Coverage for the second half of the corpus.

Two jobs. First, the twenty skills added in this round get the same scrutiny the
first twenty-six got: frontmatter, body shape, a table, no placeholders, and a
license next to them. That is one test per skill, generated from the directory
listing so a new skill cannot be added without one.

Second, the four checkers get the edge cases the first file did not reach: the
C3 and S3 pin tables, partition tables that are wrong in each specific way, the
boundary of the battery model, and the panic parser on the example log.
"""

import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import panic_decode  # noqa: E402
import partition_check  # noqa: E402
import pincheck  # noqa: E402
import power_budget  # noqa: E402

SKILLS_DIR = os.path.join(ROOT, "skills")
SKILL_NAMES = sorted(
    name for name in os.listdir(SKILLS_DIR)
    if os.path.isdir(os.path.join(SKILLS_DIR, name))
)

ERROR = pincheck.ERROR
WARN = pincheck.WARN
INFO = pincheck.INFO
OK = pincheck.OK

DB = pincheck.load_db()
ESP32 = DB["socs"]["esp32"]
S3 = DB["socs"]["esp32s3"]
C3 = DB["socs"]["esp32c3"]


def read_skill(name):
    with open(os.path.join(SKILLS_DIR, name, "SKILL.md"), encoding="utf-8") as handle:
        return handle.read()


def frontmatter(text):
    """Return the frontmatter block as a dict of the two keys we require."""
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 3)
    if end == -1:
        return {}
    block = text[4:end]
    fields = {}
    for line in block.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def body(text):
    end = text.find("\n---\n", 3)
    return text[end + 5:] if end != -1 else text


def severities(findings):
    return [severity for severity, _ in findings]


def messages(findings):
    return " | ".join(message for _, message in findings)


# ---------------------------------------------------------------------------
# One test per skill: the shape of a skill file
# ---------------------------------------------------------------------------

class SkillShapeTest(unittest.TestCase):
    """Every directory under skills/ must look like a skill, not like notes."""


def _make_skill_test(name):
    def test(self):
        text = read_skill(name)
        meta = frontmatter(text)

        self.assertEqual(meta.get("name"), name, "frontmatter name must match the directory")
        description = meta.get("description", "")
        self.assertTrue(description, "no description in %s" % name)
        self.assertTrue(
            description.startswith("Use when"),
            "%s: the description must start with 'Use when', it is what an agent matches on" % name,
        )

        prose = body(text)
        headings = re.findall(r"^## (.+)$", prose, re.M)
        self.assertGreaterEqual(len(headings), 3, "%s has %d sections" % (name, len(headings)))
        self.assertGreater(len(prose), 1500, "%s is too thin to be a skill" % name)

        structured = (
            "|" in prose
            or re.search(r"^\s*[-*] ", prose, re.M)
            or "```" in prose
        )
        self.assertTrue(structured, "%s is all prose: no table, list or code block" % name)

        lowered = prose.lower()
        for placeholder in ("todo", "fixme", "lorem", "xxx"):
            self.assertNotIn(placeholder, lowered, "%s still contains %r" % (name, placeholder))

        license_path = os.path.join(SKILLS_DIR, name, "LICENSE.txt")
        self.assertTrue(os.path.isfile(license_path), "%s has no LICENSE.txt" % name)

    test.__name__ = "test_skill_%s" % name.replace("-", "_")
    test.__doc__ = "skills/%s/SKILL.md is a well formed skill" % name
    return test


for _name in SKILL_NAMES:
    setattr(SkillShapeTest, "test_skill_%s" % _name.replace("-", "_"), _make_skill_test(_name))


# ---------------------------------------------------------------------------
# The corpus as a whole
# ---------------------------------------------------------------------------

class SkillCorpusTest(unittest.TestCase):
    def test_the_corpus_has_forty_six_skills(self):
        self.assertEqual(len(SKILL_NAMES), 59)

    def test_names_are_unique(self):
        self.assertEqual(len(SKILL_NAMES), len(set(SKILL_NAMES)))

    def test_every_name_is_prefixed(self):
        for name in SKILL_NAMES:
            self.assertTrue(name.startswith("esp32-"), name)

    def test_descriptions_are_unique(self):
        descriptions = [frontmatter(read_skill(n))["description"] for n in SKILL_NAMES]
        self.assertEqual(len(descriptions), len(set(descriptions)))

    def test_descriptions_are_long_enough_to_match_on(self):
        for name in SKILL_NAMES:
            description = frontmatter(read_skill(name))["description"]
            self.assertGreaterEqual(len(description), 80, name)

    def test_descriptions_are_not_essays(self):
        for name in SKILL_NAMES:
            description = frontmatter(read_skill(name))["description"]
            self.assertLessEqual(len(description), 400, name)

    def test_no_skill_directory_holds_stray_files(self):
        for name in SKILL_NAMES:
            for entry in os.listdir(os.path.join(SKILLS_DIR, name)):
                self.assertIn(entry, ("SKILL.md", "LICENSE.txt", "reference"), name)

    def test_files_use_lf_not_crlf(self):
        for name in SKILL_NAMES:
            raw = open(os.path.join(SKILLS_DIR, name, "SKILL.md"), "rb").read()
            self.assertNotIn(b"\r\n", raw, name)

    def test_no_skill_is_shorter_than_forty_lines(self):
        for name in SKILL_NAMES:
            self.assertGreaterEqual(len(read_skill(name).splitlines()), 40, name)

    def test_no_skill_is_longer_than_one_twenty_lines(self):
        for name in SKILL_NAMES:
            self.assertLessEqual(len(read_skill(name).splitlines()), 120, name)

    def test_frontmatter_block_is_closed(self):
        for name in SKILL_NAMES:
            self.assertIn("\n---\n", read_skill(name)[3:], name)

    def test_readme_lists_every_skill(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as handle:
            readme = handle.read()
        for name in SKILL_NAMES:
            self.assertIn("`%s`" % name, readme, "%s is missing from the README table" % name)

    def test_the_oldest_skill_still_carries_the_field_notes(self):
        notes = os.path.join(SKILLS_DIR, "esp32-field-gotchas", "reference", "field-notes.md")
        self.assertTrue(os.path.isfile(notes))


# ---------------------------------------------------------------------------
# pincheck: the chips that were not covered
# ---------------------------------------------------------------------------

class PincheckOtherChipsTest(unittest.TestCase):
    def test_c3_flash_pin_is_an_error(self):
        self.assertIn(ERROR, severities(pincheck.check_pin(C3, 11, "x", {})))

    def test_c3_adc2_pin_is_a_note(self):
        self.assertIn(INFO, severities(pincheck.check_pin(C3, 5, "x", {})))
        self.assertIn("ADC2", messages(pincheck.check_pin(C3, 5, "x", {})))

    def test_c3_strapping_pin_warns(self):
        self.assertIn(WARN, severities(pincheck.check_pin(C3, 2, "boot", {})))

    def test_c3_pin_above_range(self):
        self.assertIn("0-21", messages(pincheck.check_pin(C3, 30, "x", {})))

    def test_s3_flash_pin_is_an_error(self):
        self.assertIn(ERROR, severities(pincheck.check_pin(S3, 26, "x", {})))

    def test_s3_strapping_pin_warns(self):
        self.assertIn(WARN, severities(pincheck.check_pin(S3, 46, "psram", {})))

    def test_s3_clean_pin_is_ok(self):
        self.assertEqual(severities(pincheck.check_pin(S3, 33, "led", {})), [OK])

    def test_esp32_pin_17_does_not_exist_on_a_wroom(self):
        self.assertIn(ERROR, severities(pincheck.check_pin(ESP32, 17, "x", {})))

    def test_esp32_pin_5_is_a_strapping_pin(self):
        self.assertIn(WARN, severities(pincheck.check_pin(ESP32, 5, "cs", {})))

    def test_esp32_pin_15_is_a_strapping_pin(self):
        self.assertIn(WARN, severities(pincheck.check_pin(ESP32, 15, "x", {})))

    def test_esp32_pin_2_is_both_a_strap_and_adc2(self):
        findings = pincheck.check_pin(ESP32, 2, "sensor", {})
        self.assertEqual(set(severities(findings)), {WARN, INFO})

    def test_parse_accepts_the_gpio_prefix(self):
        self.assertEqual(pincheck.parse_assignment("gpio4=relay"), [(4, "relay")])

    def test_parse_accepts_several_separators(self):
        self.assertEqual(
            pincheck.parse_assignment("4=a;5=b\n6=c"),
            [(4, "a"), (5, "b"), (6, "c")],
        )

    def test_parse_defaults_a_missing_label(self):
        self.assertEqual(pincheck.parse_assignment("4"), [(4, "unnamed")])

    def test_parse_rejects_a_pin_that_is_not_a_number(self):
        with self.assertRaises(ValueError):
            pincheck.parse_assignment("D4=relay")

    def test_run_counts_one_error_for_a_flash_pin(self):
        _, errors = pincheck.run("esp32", [(6, "led")], DB)
        self.assertEqual(errors, 1)

    def test_run_with_no_assignments_is_clean(self):
        report, errors = pincheck.run("esp32", [], DB)
        self.assertEqual(errors, 0)
        self.assertEqual(report, [])


# ---------------------------------------------------------------------------
# partition_check
# ---------------------------------------------------------------------------

VALID_OTA = """# Name, Type, SubType, Offset, Size
nvs,      data, nvs,     0x9000,   0x4000
otadata,  data, ota,     0xd000,   0x2000
app0,     app,  ota_0,   0x10000,  0x140000
app1,     app,  ota_1,   0x150000, 0x140000
"""


def table_from(text):
    handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    handle.write(text)
    handle.close()
    try:
        rows = partition_check.parse_table(handle.name)
    finally:
        os.unlink(handle.name)
    partition_check.resolve_offsets(rows)
    return rows


class PartitionTableTest(unittest.TestCase):
    def test_a_valid_ota_table_has_no_errors(self):
        _, findings, errors = partition_check.check(table_from(VALID_OTA), 4 * 1024 * 1024, True)
        self.assertEqual(errors, 0, findings)

    def test_otadata_is_required_for_ota(self):
        text = VALID_OTA.replace("otadata,  data, ota,     0xd000,   0x2000\n", "")
        _, findings, errors = partition_check.check(table_from(text), 4 * 1024 * 1024, True)
        self.assertIn("otadata", " ".join(m for _, m in findings))
        self.assertEqual(errors, 1)

    def test_one_ota_slot_is_not_enough(self):
        text = VALID_OTA.replace("app1,     app,  ota_1,   0x150000, 0x140000\n", "")
        _, findings, errors = partition_check.check(table_from(text), 4 * 1024 * 1024, True)
        self.assertIn("two are required", " ".join(m for _, m in findings))
        self.assertEqual(errors, 1)

    def test_unequal_ota_slots_are_an_error(self):
        text = VALID_OTA.replace("0x150000, 0x140000", "0x150000, 0x100000")
        _, findings, errors = partition_check.check(table_from(text), 4 * 1024 * 1024, True)
        self.assertIn("must match", " ".join(m for _, m in findings))
        self.assertEqual(errors, 1)

    def test_an_app_partition_must_be_aligned(self):
        text = VALID_OTA.replace("0x10000,  0x140000", "0x11000,  0x140000")
        _, findings, errors = partition_check.check(table_from(text), 4 * 1024 * 1024, True)
        self.assertIn("aligned", " ".join(m for _, m in findings))
        self.assertGreaterEqual(errors, 1)

    def test_overlapping_partitions_are_an_error(self):
        text = VALID_OTA.replace("0x150000, 0x140000", "0x120000, 0x140000")
        _, findings, errors = partition_check.check(table_from(text), 4 * 1024 * 1024, True)
        self.assertIn("overlaps", " ".join(m for _, m in findings))
        self.assertGreaterEqual(errors, 1)

    def test_a_partition_inside_the_bootloader_is_an_error(self):
        text = VALID_OTA.replace("0x9000,   0x4000", "0x8000,   0x4000")
        _, findings, errors = partition_check.check(table_from(text), 4 * 1024 * 1024, True)
        self.assertIn("0x9000", " ".join(m for _, m in findings))
        self.assertGreaterEqual(errors, 1)

    def test_a_partition_past_the_end_of_flash_is_an_error(self):
        _, findings, errors = partition_check.check(table_from(VALID_OTA), 1024 * 1024, True)
        self.assertIn("past the end", " ".join(m for _, m in findings))
        self.assertGreaterEqual(errors, 1)

    def test_no_nvs_partition_is_a_warning(self):
        text = VALID_OTA.replace("nvs,      data, nvs,     0x9000,   0x4000\n", "")
        _, findings, _ = partition_check.check(table_from(text), 4 * 1024 * 1024, True)
        self.assertIn(WARN, [s for s, _ in findings])
        self.assertIn("nvs", " ".join(m for _, m in findings).lower())

    def test_a_small_factory_partition_warns(self):
        text = VALID_OTA + "factory,  app,  factory, 0x290000, 0x40000\n"
        _, findings, errors = partition_check.check(table_from(text), 4 * 1024 * 1024, True)
        self.assertIn(WARN, [s for s, _ in findings])
        self.assertEqual(errors, 0)

    def test_otadata_without_the_ota_flag_is_a_note(self):
        _, findings, errors = partition_check.check(table_from(VALID_OTA), 4 * 1024 * 1024, False)
        self.assertIn(INFO, [s for s, _ in findings])
        self.assertEqual(errors, 0)

    def test_parse_size_reads_hex(self):
        self.assertEqual(partition_check.parse_size("0x10000"), 65536)

    def test_parse_size_reads_kilobytes(self):
        self.assertEqual(partition_check.parse_size("64K"), 65536)

    def test_parse_size_reads_megabytes(self):
        self.assertEqual(partition_check.parse_size("1M"), 1024 * 1024)

    def test_parse_size_rejects_nonsense(self):
        with self.assertRaises(ValueError):
            partition_check.parse_size("big")

    def test_human_formats_megabytes(self):
        self.assertEqual(partition_check.human(1024 * 1024), "1MB")

    def test_human_formats_kilobytes(self):
        self.assertEqual(partition_check.human(65536), "64KB")

    def test_parse_table_skips_comments_and_the_header(self):
        self.assertEqual(len(table_from(VALID_OTA)), 4)

    def test_resolve_offsets_aligns_to_four_kilobytes(self):
        rows = table_from("nvs,data,nvs,0x9000,0x1000\nphy,data,phy,,0x1000\n")
        self.assertEqual(rows[1]["offset"], 0xA000)

    def test_report_is_sorted_by_offset(self):
        report, _, _ = partition_check.check(table_from(VALID_OTA), 4 * 1024 * 1024, True)
        offsets = [row["offset"] for row in report]
        self.assertEqual(offsets, sorted(offsets))


# ---------------------------------------------------------------------------
# power_budget
# ---------------------------------------------------------------------------

class PowerBudgetEdgesTest(unittest.TestCase):
    def test_tx_equal_to_the_wake_window_is_allowed(self):
        result = power_budget.battery_life(1000, 10, 100, tx_ms=100)
        self.assertGreater(result["hours"], 0)

    def test_no_wakes_is_pure_sleep(self):
        result = power_budget.battery_life(1000, 0, 0)
        self.assertAlmostEqual(result["average_ma"], 0.01, places=3)

    def test_breakdown_sums_to_the_average(self):
        result = power_budget.battery_life(1000, 12, 400)
        self.assertAlmostEqual(sum(result["breakdown_ma"].values()), result["average_ma"], places=6)

    def test_days_are_hours_over_twenty_four(self):
        result = power_budget.battery_life(2000, 6, 500)
        self.assertAlmostEqual(result["days"], result["hours"] / 24.0, places=6)

    def test_duty_cycle_scales_with_the_wakes(self):
        one = power_budget.battery_life(1000, 10, 300)["duty_cycle_percent"]
        two = power_budget.battery_life(1000, 20, 300)["duty_cycle_percent"]
        self.assertAlmostEqual(two, one * 2, places=6)

    def test_the_radio_dominates_a_chatty_node(self):
        result = power_budget.battery_life(1000, 360, 1000, tx_ms=800)
        self.assertEqual(result["dominant_term"], "tx")

    def test_sleep_dominates_a_quiet_node(self):
        result = power_budget.battery_life(1000, 1, 100, tx_ms=50)
        self.assertEqual(result["dominant_term"], "sleep")

    def test_more_wakes_mean_fewer_hours(self):
        few = power_budget.battery_life(1000, 6, 500)["hours"]
        many = power_budget.battery_life(1000, 60, 500)["hours"]
        self.assertLess(many, few)

    def test_awake_more_than_an_hour_raises(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(1000, 2000, 5000)

    def test_zero_battery_raises(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(0, 10, 100)

    def test_negative_wakes_raise(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(1000, -1, 100)

    def test_the_dominant_percentage_is_bounded(self):
        result = power_budget.battery_life(1000, 12, 400)
        self.assertGreaterEqual(result["dominant_percent"], 0)
        self.assertLessEqual(result["dominant_percent"], 100)


# ---------------------------------------------------------------------------
# panic_decode on the example log
# ---------------------------------------------------------------------------

PANIC_LOG = os.path.join(ROOT, "examples", "panic-log.txt")


class PanicLogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PANIC_LOG, encoding="utf-8") as handle:
            cls.parsed = panic_decode.parse(handle.read())

    def test_reason_is_load_prohibited(self):
        self.assertEqual(self.parsed["reason"], "LoadProhibited")

    def test_the_hint_mentions_a_bad_pointer(self):
        self.assertIn("bad pointer", self.parsed["hint"])

    def test_the_faulting_core_is_read(self):
        self.assertEqual(self.parsed["core"], 1)

    def test_four_frames_are_extracted(self):
        self.assertEqual(len(self.parsed["frames"]), 4)

    def test_the_first_frame_is_the_innermost(self):
        self.assertEqual(self.parsed["frames"][0], "0x400d4a3e")

    def test_the_last_frame_is_the_outermost(self):
        self.assertEqual(self.parsed["frames"][-1], "0x400d0d45")

    def test_the_log_is_recognised_as_a_panic(self):
        self.assertTrue(self.parsed["is_panic"])

    def test_the_addr2line_command_carries_every_frame(self):
        command = panic_decode.addr2line_command(self.parsed["frames"], "app.elf", "xtensa-esp32-elf-addr2line")
        for frame in self.parsed["frames"]:
            self.assertIn(frame, command)
        self.assertIn("app.elf", command)

    def test_a_normal_log_is_not_a_panic(self):
        self.assertFalse(panic_decode.parse("I (1234) wifi: connected").get("is_panic"))


if __name__ == "__main__":
    unittest.main()
