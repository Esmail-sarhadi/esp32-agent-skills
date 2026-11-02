"""Unit coverage for the checker tools and repository invariants.

The existing test files drive the tools through subprocess, which proves the CLI
contract but leaves the pure functions untested. Everything here imports the modules
directly: no process spawn, no hardware, no network.
"""

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import panic_decode  # noqa: E402
import partition_check  # noqa: E402
import pincheck  # noqa: E402
import power_budget  # noqa: E402

DB = pincheck.load_db()
ESP32 = DB["socs"]["esp32"]
S3 = DB["socs"]["esp32s3"]
C3 = DB["socs"]["esp32c3"]

ERROR = pincheck.ERROR
WARN = pincheck.WARN
INFO = pincheck.INFO
OK = pincheck.OK


def severities(findings):
    return [severity for severity, _ in findings]


def messages(findings):
    return " | ".join(message for _, message in findings)


# ---------------------------------------------------------------------------
# pincheck: parse_assignment
# ---------------------------------------------------------------------------

class ParseAssignmentTest(unittest.TestCase):
    def test_single_assignment(self):
        self.assertEqual(pincheck.parse_assignment("12=relay"), [(12, "relay")])

    def test_comma_separated(self):
        self.assertEqual(
            pincheck.parse_assignment("12=relay,34=button"),
            [(12, "relay"), (34, "button")],
        )

    def test_semicolon_separated(self):
        self.assertEqual(len(pincheck.parse_assignment("1=a;2=b")), 2)

    def test_newline_separated(self):
        self.assertEqual(len(pincheck.parse_assignment("1=a\n2=b")), 2)

    def test_gpio_prefix_is_accepted(self):
        self.assertEqual(pincheck.parse_assignment("GPIO25=led"), [(25, "led")])

    def test_lowercase_gpio_prefix(self):
        self.assertEqual(pincheck.parse_assignment("gpio25=led"), [(25, "led")])

    def test_label_is_optional(self):
        self.assertEqual(pincheck.parse_assignment("25"), [(25, "unnamed")])

    def test_empty_label_becomes_unnamed(self):
        self.assertEqual(pincheck.parse_assignment("25=  "), [(25, "unnamed")])

    def test_whitespace_is_trimmed(self):
        self.assertEqual(pincheck.parse_assignment("  12 = relay  "), [(12, "relay")])

    def test_empty_chunks_are_skipped(self):
        self.assertEqual(pincheck.parse_assignment("12=a,,13=b"), [(12, "a"), (13, "b")])

    def test_empty_input_returns_nothing(self):
        self.assertEqual(pincheck.parse_assignment("   "), [])

    def test_three_digits_are_rejected(self):
        with self.assertRaises(ValueError):
            pincheck.parse_assignment("123=relay")

    def test_word_is_rejected(self):
        with self.assertRaises(ValueError):
            pincheck.parse_assignment("D4=relay")

    def test_label_keeps_its_equals_sign(self):
        self.assertEqual(pincheck.parse_assignment("4=a=b"), [(4, "a=b")])


# ---------------------------------------------------------------------------
# pincheck: check_pin on the classic ESP32
# ---------------------------------------------------------------------------

class CheckPinEsp32Test(unittest.TestCase):
    def test_flash_pin_is_an_error(self):
        findings = pincheck.check_pin(ESP32, 6, "led", {})
        self.assertEqual(severities(findings), [ERROR])
        self.assertIn("SPI flash", messages(findings))

    def test_every_flash_pin_is_rejected(self):
        for pin in ESP32["reserved_flash"]:
            self.assertIn(ERROR, severities(pincheck.check_pin(ESP32, pin, "x", {})))

    def test_input_only_pin_is_a_warning(self):
        findings = pincheck.check_pin(ESP32, 34, "button", {})
        self.assertEqual(severities(findings), [WARN])
        self.assertIn("input-only", messages(findings))

    def test_input_only_pin_names_the_label(self):
        self.assertIn("'button'", messages(pincheck.check_pin(ESP32, 35, "button", {})))

    def test_out_of_range_low(self):
        findings = pincheck.check_pin(ESP32, -1, "x", {})
        self.assertEqual(severities(findings), [ERROR])
        self.assertIn("does not exist", messages(findings))

    def test_out_of_range_high(self):
        findings = pincheck.check_pin(ESP32, 40, "x", {})
        self.assertIn("valid range 0-39", messages(findings))

    def test_out_of_range_stops_further_checks(self):
        # 40 is also outside the flash list, but the range error must be the only finding.
        self.assertEqual(len(pincheck.check_pin(ESP32, 40, "x", {})), 1)

    def test_duplicate_assignment_is_an_error(self):
        findings = pincheck.check_pin(ESP32, 21, "b", {21: "a"})
        self.assertIn(ERROR, severities(findings))
        self.assertIn("assigned twice", messages(findings))

    def test_strapping_pin_warns(self):
        findings = pincheck.check_pin(ESP32, 0, "boot", {})
        self.assertIn(WARN, severities(findings))
        self.assertIn("strapping", messages(findings))

    def test_gpio12_explains_the_1v8_flash_trap(self):
        self.assertIn("1.8 V", messages(pincheck.check_pin(ESP32, 12, "led", {})))

    def test_uart0_pin_is_only_a_note(self):
        self.assertEqual(severities(pincheck.check_pin(ESP32, 1, "tx", {})), [INFO])

    def test_adc2_pin_mentions_wifi(self):
        self.assertIn("ADC2", messages(pincheck.check_pin(ESP32, 25, "sensor", {})))

    def test_pin_absent_from_wroom_is_an_error(self):
        findings = pincheck.check_pin(ESP32, 16, "x", {})
        self.assertIn(ERROR, severities(findings))
        self.assertIn("WROOM", messages(findings))

    def test_clean_pin_reports_ok(self):
        self.assertEqual(pincheck.check_pin(ESP32, 21, "led", {}), [(OK, "no constraint found in the database")])

    def test_a_pin_can_carry_several_findings(self):
        # GPIO12 is a strapping pin *and* an ADC2 pin.
        self.assertGreaterEqual(len(pincheck.check_pin(ESP32, 12, "led", {})), 2)


# ---------------------------------------------------------------------------
# pincheck: the other two SoCs
# ---------------------------------------------------------------------------

class CheckPinOtherSocsTest(unittest.TestCase):
    def test_s3_range_is_wider(self):
        self.assertIn(ERROR, severities(pincheck.check_pin(S3, 49, "x", {})))
        self.assertNotIn(ERROR, severities(pincheck.check_pin(S3, 48, "x", {})))

    def test_s3_flash_pins_differ_from_esp32(self):
        self.assertIn(ERROR, severities(pincheck.check_pin(S3, 27, "x", {})))
        self.assertNotIn(ERROR, severities(pincheck.check_pin(S3, 6, "x", {})))

    def test_s3_usb_pin_is_a_note(self):
        findings = pincheck.check_pin(S3, 19, "x", {})
        self.assertEqual(set(severities(findings)), {INFO})
        self.assertIn("USB", messages(findings))

    def test_s3_has_no_input_only_pins(self):
        self.assertEqual(S3["input_only"], [])

    def test_c3_range_is_narrow(self):
        self.assertIn("valid range 0-21", messages(pincheck.check_pin(C3, 22, "x", {})))

    def test_c3_flash_pins_are_11_to_17(self):
        for pin in (11, 14, 17):
            self.assertIn(ERROR, severities(pincheck.check_pin(C3, pin, "x", {})))

    def test_c3_clean_pin(self):
        self.assertEqual(severities(pincheck.check_pin(C3, 6, "x", {})), [OK])

    def test_c3_uart0_is_20_and_21(self):
        for pin in (20, 21):
            self.assertIn(INFO, severities(pincheck.check_pin(C3, pin, "x", {})))


# ---------------------------------------------------------------------------
# pincheck: run()
# ---------------------------------------------------------------------------

class RunTest(unittest.TestCase):
    def test_clean_assignment_has_no_errors(self):
        report, errors = pincheck.run("esp32", [(21, "a"), (22, "b")], DB)
        self.assertEqual(errors, 0)
        self.assertEqual(len(report), 2)

    def test_error_count_matches_findings(self):
        _report, errors = pincheck.run("esp32", [(6, "a"), (34, "b")], DB)
        self.assertEqual(errors, 1)

    def test_report_carries_the_label(self):
        report, _ = pincheck.run("esp32", [(21, "status_led")], DB)
        self.assertEqual(report[0]["label"], "status_led")

    def test_duplicate_is_counted_once_per_second_use(self):
        _report, errors = pincheck.run("esp32", [(21, "a"), (21, "b")], DB)
        self.assertEqual(errors, 1)

    def test_unknown_soc_raises(self):
        with self.assertRaises(KeyError):
            pincheck.run("esp8266", [(1, "a")], DB)

    def test_empty_assignment_is_clean(self):
        report, errors = pincheck.run("esp32", [], DB)
        self.assertEqual((report, errors), ([], 0))


# ---------------------------------------------------------------------------
# partition_check: parse_size and human
# ---------------------------------------------------------------------------

class ParseSizeTest(unittest.TestCase):
    def test_hex(self):
        self.assertEqual(partition_check.parse_size("0x10000"), 65536)

    def test_decimal(self):
        self.assertEqual(partition_check.parse_size("65536"), 65536)

    def test_kilobytes(self):
        self.assertEqual(partition_check.parse_size("64K"), 65536)

    def test_lowercase_kilobytes(self):
        self.assertEqual(partition_check.parse_size("64k"), 65536)

    def test_megabytes(self):
        self.assertEqual(partition_check.parse_size("1M"), 1024 * 1024)

    def test_megabytes_with_b_suffix(self):
        self.assertEqual(partition_check.parse_size("4MB"), 4 * 1024 * 1024)

    def test_bytes_suffix(self):
        self.assertEqual(partition_check.parse_size("4096B"), 4096)

    def test_surrounding_whitespace(self):
        self.assertEqual(partition_check.parse_size("  0x2000  "), 0x2000)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            partition_check.parse_size("")

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            partition_check.parse_size("big")

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            partition_check.parse_size("-16")


class HumanTest(unittest.TestCase):
    def test_whole_megabytes(self):
        self.assertEqual(partition_check.human(0x100000), "1MB")

    def test_whole_kilobytes(self):
        self.assertEqual(partition_check.human(0x1000), "4KB")

    def test_mixed_value_falls_back_to_hex(self):
        self.assertEqual(partition_check.human(0x1234), "0x1234")

    def test_zero_is_hex(self):
        self.assertEqual(partition_check.human(0), "0x0")

    def test_round_trip_with_parse_size(self):
        for text in ("0x1000", "64K", "1M", "4MB"):
            self.assertEqual(partition_check.parse_size(partition_check.human(partition_check.parse_size(text))),
                             partition_check.parse_size(text))


# ---------------------------------------------------------------------------
# partition_check: parse_table and resolve_offsets
# ---------------------------------------------------------------------------

class ParseTableTest(unittest.TestCase):
    def _table(self, text):
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return partition_check.parse_table(handle.name)

    def test_header_is_skipped(self):
        rows = self._table("Name,Type,SubType,Offset,Size\nnvs,data,nvs,0x9000,0x4000\n")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "nvs")

    def test_comments_and_blank_lines_are_ignored(self):
        rows = self._table("# a comment\n\nnvs,data,nvs,0x9000,0x4000\n")
        self.assertEqual(len(rows), 1)

    def test_types_are_lowercased(self):
        rows = self._table("APP,APP,OTA_0,0x10000,1M\n")
        self.assertEqual(rows[0]["type"], "app")
        self.assertEqual(rows[0]["subtype"], "ota_0")

    def test_missing_offset_is_none(self):
        rows = self._table("app,app,factory,,1M\n")
        self.assertIsNone(rows[0]["offset"])

    def test_too_few_fields_raises(self):
        with self.assertRaises(ValueError):
            self._table("nvs,data,nvs,0x9000\n")

    def test_line_numbers_are_recorded(self):
        rows = self._table("# c\nnvs,data,nvs,0x9000,0x4000\n")
        self.assertEqual(rows[0]["line"], 2)


class ResolveOffsetsTest(unittest.TestCase):
    def test_first_partition_starts_after_the_table(self):
        rows = [{"offset": None, "size": 0x1000}]
        partition_check.resolve_offsets(rows)
        self.assertEqual(rows[0]["offset"], partition_check.PARTITION_TABLE_END)

    def test_next_partition_follows_the_previous(self):
        rows = [{"offset": 0x9000, "size": 0x1000}, {"offset": None, "size": 0x1000}]
        partition_check.resolve_offsets(rows)
        self.assertEqual(rows[1]["offset"], 0xA000)

    def test_offsets_are_4k_aligned(self):
        rows = [{"offset": 0x9000, "size": 0x1234}, {"offset": None, "size": 0x1000}]
        partition_check.resolve_offsets(rows)
        self.assertEqual(rows[1]["offset"] % 0x1000, 0)

    def test_explicit_offsets_are_kept(self):
        rows = [{"offset": 0x20000, "size": 0x1000}]
        partition_check.resolve_offsets(rows)
        self.assertEqual(rows[0]["offset"], 0x20000)


# ---------------------------------------------------------------------------
# partition_check: check()
# ---------------------------------------------------------------------------

def row(name, ptype, subtype, offset, size):
    return {"name": name, "type": ptype, "subtype": subtype, "offset": offset, "size": size, "line": 1}


class PartitionCheckTest(unittest.TestCase):
    FLASH = 4 * 1024 * 1024

    def test_clean_factory_table_has_no_errors(self):
        rows = [row("nvs", "data", "nvs", 0x9000, 0x4000),
                row("factory", "app", "factory", 0x10000, 0x100000)]
        _report, _findings, errors = partition_check.check(rows, self.FLASH, ota=False)
        self.assertEqual(errors, 0)

    def test_partition_below_the_table_is_an_error(self):
        rows = [row("nvs", "data", "nvs", 0x1000, 0x4000)]
        _r, _f, errors = partition_check.check(rows, self.FLASH, ota=False)
        self.assertGreater(errors, 0)

    def test_partition_past_the_end_of_flash_is_an_error(self):
        rows = [row("nvs", "data", "nvs", 0x9000, 0x4000),
                row("factory", "app", "factory", 0x3F0000, 0x20000)]
        _r, findings, _e = partition_check.check(rows, self.FLASH, ota=False)
        self.assertIn("past the end", " | ".join(m for _, m in findings))

    def test_zero_size_is_an_error(self):
        rows = [row("nvs", "data", "nvs", 0x9000, 0)]
        _r, findings, _e = partition_check.check(rows, self.FLASH, ota=False)
        self.assertIn("zero size", " | ".join(m for _, m in findings))

    def test_misaligned_app_partition_is_an_error(self):
        rows = [row("factory", "app", "factory", 0x18000, 0x100000)]
        _r, findings, _e = partition_check.check(rows, self.FLASH, ota=False)
        self.assertIn("aligned", " | ".join(m for _, m in findings))

    def test_overlap_is_an_error(self):
        rows = [row("a", "data", "nvs", 0x9000, 0x8000),
                row("b", "data", "spiffs", 0xA000, 0x8000)]
        _r, findings, _e = partition_check.check(rows, self.FLASH, ota=False)
        self.assertIn("overlaps", " | ".join(m for _, m in findings))

    def test_ota_without_otadata_is_an_error(self):
        rows = [row("nvs", "data", "nvs", 0x9000, 0x4000),
                row("ota_0", "app", "ota_0", 0x10000, 0x100000),
                row("ota_1", "app", "ota_1", 0x110000, 0x100000)]
        _r, findings, _e = partition_check.check(rows, self.FLASH, ota=True)
        self.assertIn("otadata", " | ".join(m for _, m in findings))

    def test_ota_with_one_slot_is_an_error(self):
        rows = [row("nvs", "data", "nvs", 0x9000, 0x4000),
                row("otadata", "data", "ota", 0xD000, 0x2000),
                row("ota_0", "app", "ota_0", 0x10000, 0x100000)]
        _r, findings, _e = partition_check.check(rows, self.FLASH, ota=True)
        self.assertIn("two are", " | ".join(m for _, m in findings))

    def test_ota_slots_must_match_in_size(self):
        rows = [row("nvs", "data", "nvs", 0x9000, 0x4000),
                row("otadata", "data", "ota", 0xD000, 0x2000),
                row("ota_0", "app", "ota_0", 0x10000, 0x100000),
                row("ota_1", "app", "ota_1", 0x110000, 0x200000)]
        _r, findings, _e = partition_check.check(rows, self.FLASH, ota=True)
        self.assertIn("same size", " | ".join(m for _, m in findings))

    def test_missing_nvs_is_a_warning_not_an_error(self):
        rows = [row("factory", "app", "factory", 0x10000, 0x100000)]
        _r, findings, errors = partition_check.check(rows, self.FLASH, ota=False)
        self.assertEqual(errors, 0)
        self.assertIn("no nvs", " | ".join(m for _, m in findings))

    def test_no_app_partition_is_an_error(self):
        rows = [row("nvs", "data", "nvs", 0x9000, 0x4000)]
        _r, _f, errors = partition_check.check(rows, self.FLASH, ota=False)
        self.assertGreater(errors, 0)

    def test_report_is_sorted_by_offset(self):
        rows = [row("b", "data", "spiffs", 0x20000, 0x1000),
                row("a", "data", "nvs", 0x9000, 0x4000)]
        report, _f, _e = partition_check.check(rows, self.FLASH, ota=False)
        self.assertEqual([r["name"] for r in report], ["a", "b"])

    def test_budget_note_is_always_present(self):
        rows = [row("factory", "app", "factory", 0x10000, 0x100000)]
        _r, findings, _e = partition_check.check(rows, self.FLASH, ota=False)
        self.assertTrue(any("used" in m for _, m in findings))


# ---------------------------------------------------------------------------
# power_budget
# ---------------------------------------------------------------------------

class PowerBudgetTest(unittest.TestCase):
    def test_breakdown_sums_to_the_average(self):
        result = power_budget.battery_life(1000, 12, 200, tx_ms=50)
        self.assertAlmostEqual(sum(result["breakdown_ma"].values()), result["average_ma"], places=9)

    def test_hours_follow_from_the_average(self):
        result = power_budget.battery_life(2000, 6, 500)
        self.assertAlmostEqual(result["hours"], 2000 / result["average_ma"], places=6)

    def test_days_are_hours_over_24(self):
        result = power_budget.battery_life(2000, 6, 500)
        self.assertAlmostEqual(result["days"], result["hours"] / 24, places=9)

    def test_duty_cycle(self):
        result = power_budget.battery_life(1000, 10, 100, tx_ms=50)
        self.assertAlmostEqual(result["duty_cycle_percent"], 100.0 * 1000 / 3_600_000, places=9)

    def test_dominant_term_is_one_of_the_three(self):
        result = power_budget.battery_life(1000, 1, 100, tx_ms=50)
        self.assertIn(result["dominant_term"], ("sleep", "idle", "tx"))

    def test_dominant_percent_is_bounded(self):
        result = power_budget.battery_life(1000, 1, 100, tx_ms=50)
        self.assertGreaterEqual(result["dominant_percent"], 0)
        self.assertLessEqual(result["dominant_percent"], 100.0000001)

    def test_sleep_dominates_a_rare_wake(self):
        result = power_budget.battery_life(1000, 1, 100, tx_ms=50)
        self.assertEqual(result["dominant_term"], "sleep")

    def test_tx_dominates_a_chatty_node(self):
        result = power_budget.battery_life(1000, 360, 1000, tx_ms=900)
        self.assertEqual(result["dominant_term"], "tx")

    def test_no_wakes_is_pure_sleep(self):
        result = power_budget.battery_life(1000, 0, 0)
        self.assertAlmostEqual(result["average_ma"], 0.01, places=9)
        self.assertAlmostEqual(result["hours"], 100000, places=3)

    def test_zero_battery_raises(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(0, 1, 100)

    def test_negative_battery_raises(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(-1, 1, 100)

    def test_negative_wakes_raise(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(1000, -1, 100)

    def test_negative_wake_ms_raises(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(1000, 1, -100)

    def test_tx_longer_than_wake_raises(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(1000, 1, 100, tx_ms=200)

    def test_awake_more_than_a_full_hour_raises(self):
        with self.assertRaises(ValueError):
            power_budget.battery_life(1000, 100, 100000)

    def test_bigger_battery_lasts_longer(self):
        small = power_budget.battery_life(1000, 6, 200, tx_ms=100)
        big = power_budget.battery_life(3000, 6, 200, tx_ms=100)
        self.assertGreater(big["hours"], small["hours"])

    def test_more_wakes_shorten_the_battery(self):
        few = power_budget.battery_life(1000, 1, 200, tx_ms=100)
        many = power_budget.battery_life(1000, 60, 200, tx_ms=100)
        self.assertGreater(few["hours"], many["hours"])


# ---------------------------------------------------------------------------
# panic_decode
# ---------------------------------------------------------------------------

PANIC_TEXT = """Guru Meditation Error: Core  1 panic'ed (LoadProhibited). Exception was unhandled.
Core  1 register dump:
PC      : 0x400d1234  PS      : 0x00060d30
EXCVADDR: 0x00000000  LBEG    : 0x400014fd
Backtrace: 0x400d1234:0x3ffb1f60 0x400d5678:0x3ffb1f80
"""


class PanicDecodeTest(unittest.TestCase):
    def test_reason_is_extracted(self):
        self.assertEqual(panic_decode.parse(PANIC_TEXT)["reason"], "LoadProhibited")

    def test_reason_carries_a_hint(self):
        self.assertIsNotNone(panic_decode.parse(PANIC_TEXT)["hint"])

    def test_core_is_extracted(self):
        self.assertEqual(panic_decode.parse(PANIC_TEXT)["core"], 1)

    def test_pc_is_extracted(self):
        self.assertEqual(panic_decode.parse(PANIC_TEXT)["pc"], "0x400d1234")

    def test_excvaddr_is_extracted(self):
        self.assertEqual(panic_decode.parse(PANIC_TEXT)["excvaddr"], "0x00000000")

    def test_backtrace_frames(self):
        frames = panic_decode.parse(PANIC_TEXT)["frames"]
        self.assertEqual(frames, ["0x400d1234", "0x400d5678"])

    def test_panic_flag_is_set(self):
        self.assertTrue(panic_decode.parse(PANIC_TEXT)["is_panic"])

    def test_empty_text_is_not_a_panic(self):
        result = panic_decode.parse("")
        self.assertFalse(result["is_panic"])
        self.assertIsNone(result["reason"])

    def test_unknown_reason_has_no_hint(self):
        result = panic_decode.parse("Guru Meditation Error: Core  0 panic'ed (SomethingNew).")
        self.assertIsNone(result["hint"])

    def test_pc_is_used_when_there_is_no_backtrace(self):
        text = "Guru Meditation Error: Core  1 panic'ed (IllegalInstruction).\nPC      : 0x400d9999\n"
        self.assertEqual(panic_decode.parse(text)["frames"], ["0x400d9999"])

    def test_addr2line_command_shape(self):
        command = panic_decode.addr2line_command(["0x1", "0x2"], "app.elf", "addr2line")
        self.assertEqual(command, "addr2line -pfiaC -e app.elf 0x1 0x2")


# ---------------------------------------------------------------------------
# repository invariants
# ---------------------------------------------------------------------------

class ReferenceIntegrityTest(unittest.TestCase):
    def setUp(self):
        path = os.path.join(ROOT, "skills", "esp32-field-gotchas", "reference", "field-notes.md")
        with open(path, encoding="utf-8") as handle:
            self.notes = handle.read()

    def test_the_notes_hold_one_hundred_and_sixty_entries(self):
        import re
        numbers = [int(m.group(1)) for m in re.finditer(r"^(\d+)\. \*\*", self.notes, re.M)]
        self.assertEqual(len(numbers), 160)

    def test_numbering_is_contiguous(self):
        import re
        numbers = sorted(int(m.group(1)) for m in re.finditer(r"^(\d+)\. \*\*", self.notes, re.M))
        self.assertEqual(numbers, list(range(1, 161)))

    def test_every_entry_links_to_a_thread(self):
        import re
        blocks = re.split(r"^\d+\. \*\*", self.notes, flags=re.M)[1:]
        for block in blocks:
            self.assertRegex(block.split("\n")[0], r"\[(\d+)\]\(https://stackoverflow\.com/q/\1\)")

    def test_every_skill_has_a_manifest(self):
        skills = os.path.join(ROOT, "skills")
        for name in os.listdir(skills):
            if os.path.isdir(os.path.join(skills, name)):
                self.assertTrue(os.path.exists(os.path.join(skills, name, "SKILL.md")), name)

    def test_pin_database_parses_and_covers_three_socs(self):
        self.assertEqual(sorted(DB["socs"]), ["esp32", "esp32c3", "esp32s3"])

    def test_every_soc_declares_the_required_keys(self):
        required = {"label", "valid_range", "reserved_flash", "input_only", "uart0",
                    "adc2_blocked_by_wifi", "strapping"}
        for key, soc in DB["socs"].items():
            self.assertTrue(required <= set(soc), key)

    def test_valid_ranges_are_ordered_pairs(self):
        for key, soc in DB["socs"].items():
            low, high = soc["valid_range"]
            self.assertLess(low, high, key)

    def _skill_dirs(self):
        skills = os.path.join(ROOT, "skills")
        return sorted(
            name for name in os.listdir(skills)
            if os.path.isdir(os.path.join(skills, name))
        )

    def test_every_skill_declares_name_and_description(self):
        for name in self._skill_dirs():
            with open(os.path.join(ROOT, "skills", name, "SKILL.md"), encoding="utf-8") as handle:
                text = handle.read()
            self.assertTrue(text.startswith("---\n"), name)
            front = text.split("---", 2)[1]
            self.assertIn("name:", front, name)
            self.assertIn("description:", front, name)

    def test_frontmatter_name_matches_the_directory(self):
        for name in self._skill_dirs():
            with open(os.path.join(ROOT, "skills", name, "SKILL.md"), encoding="utf-8") as handle:
                front = handle.read().split("---", 2)[1]
            declared = [line.split(":", 1)[1].strip() for line in front.splitlines()
                        if line.startswith("name:")][0]
            self.assertEqual(declared, name)

    def test_every_reference_link_resolves(self):
        import re
        for name in self._skill_dirs():
            skill_dir = os.path.join(ROOT, "skills", name)
            with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as handle:
                text = handle.read()
            for link in re.findall(r"\]\((reference/[^)]+)\)", text):
                self.assertTrue(os.path.exists(os.path.join(skill_dir, link)),
                                "%s -> %s" % (name, link))

    def test_flash_pins_are_inside_the_valid_range(self):
        for key, soc in DB["socs"].items():
            low, high = soc["valid_range"]
            for pin in soc["reserved_flash"]:
                self.assertTrue(low <= pin <= high, "%s: %d" % (key, pin))


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# modbus_map_check: register map validation
# ---------------------------------------------------------------------------

import modbus_map_check  # noqa: E402


class ModbusMapCheckTest(unittest.TestCase):
    def test_valid_example_has_no_errors(self):
        path = os.path.join(ROOT, "examples", "modbus-register-map.csv")
        rows = modbus_map_check.parse_map(path)
        findings, errors = modbus_map_check.check(rows)
        self.assertEqual(errors, 0)
        self.assertEqual(len(rows), 4)

    def test_broken_example_detects_overlap_scale_and_coil_type(self):
        path = os.path.join(ROOT, "examples", "modbus-register-map-broken.csv")
        rows = modbus_map_check.parse_map(path)
        findings, errors = modbus_map_check.check(rows)
        self.assertGreaterEqual(errors, 3)
        messages = " ".join(item["message"] for item in findings)
        self.assertIn("overlaps", messages)
        self.assertIn("scale", messages)
        self.assertIn("coil/discrete", messages)

    def test_register_cannot_cross_address_space(self):
        rows = [{
            "name": "last", "table": "holding", "address": "65535",
            "type": "U32", "access": "R", "scale": "1",
            "unit": "1", "description": "boundary", "line": 2,
        }]
        findings, errors = modbus_map_check.check(rows)
        self.assertGreater(errors, 0)
        self.assertIn("outside", " ".join(item["message"] for item in findings))

    def test_boolean_register_table_warns_about_vendor_semantics(self):
        rows = [{
            "name": "flag", "table": "holding", "address": "3",
            "type": "BOOL", "access": "R", "scale": "1",
            "unit": "1", "description": "bit flag", "line": 2,
        }]
        findings, errors = modbus_map_check.check(rows)
        self.assertEqual(errors, 0)
        self.assertTrue(any(item["severity"] == modbus_map_check.WARN for item in findings))

    def test_missing_columns_rejected(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as handle:
            handle.write("name,table,address\\n")
            path = handle.name
        try:
            with self.assertRaises(ValueError):
                modbus_map_check.parse_map(path)
        finally:
            os.unlink(path)

    def test_duplicate_names_are_rejected_case_insensitively(self):
        rows = [
            {"name": "x", "table": "holding", "address": "1", "type": "U16",
             "access": "R", "scale": "1", "unit": "1", "description": "one", "line": 2},
            {"name": "x", "table": "holding", "address": "2", "type": "U16",
             "access": "R", "scale": "1", "unit": "1", "description": "two", "line": 3},
        ]
        findings, errors = modbus_map_check.check(rows)
        self.assertEqual(errors, 1)
        self.assertIn("duplicate point name", " ".join(item["message"] for item in findings))


    def test_empty_map_is_rejected(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as handle:
            handle.write(",".join(modbus_map_check.REQUIRED) + "\\n")
            path = handle.name
        try:
            with self.assertRaisesRegex(ValueError, "no data rows"):
                modbus_map_check.parse_map(path)
        finally:
            os.unlink(path)

    def test_non_numeric_address_is_an_error(self):
        rows = [{
            "name": "bad", "table": "holding", "address": "40001",
            "type": "U16", "access": "R", "scale": "1",
            "unit": "1", "description": "display notation is not an offset", "line": 2,
        }]
        findings, errors = modbus_map_check.check(rows)
        self.assertEqual(errors, 0)
        self.assertEqual(findings, [])

    def test_non_finite_scale_is_rejected(self):
        rows = [{
            "name": "bad", "table": "holding", "address": "1",
            "type": "U16", "access": "R", "scale": "nan",
            "unit": "1", "description": "bad scale", "line": 2,
        }]
        findings, errors = modbus_map_check.check(rows)
        self.assertEqual(errors, 1)
        self.assertIn("finite non-zero", " ".join(item["message"] for item in findings))
