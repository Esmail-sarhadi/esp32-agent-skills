"""The three newest checkers, the dispatcher, and the build artifacts.

The tools here are the ones that catch mistakes before anything is soldered or
flashed: a topic the broker will accept but never match, two images written to
the same flash offset, and two I2C devices that share an address. Each one is
pure logic over a small input, so the tests are direct.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import esp32_skills_cli  # noqa: E402
import flash_layout  # noqa: E402
import i2c_address_check  # noqa: E402
import mqtt_topic_check  # noqa: E402


def run_tool(name, *args):
    return subprocess.run([sys.executable, os.path.join(TOOLS, name + ".py"), *args],
                          capture_output=True, text=True, check=False)


# ---------------------------------------------------------------------------
# MQTT topics
# ---------------------------------------------------------------------------

class MqttPublishTest(unittest.TestCase):
    def test_a_plain_topic_is_accepted(self):
        self.assertTrue(mqtt_topic_check.check_topic("plant/line1/temp")["ok"])

    def test_a_publish_topic_cannot_contain_plus(self):
        result = mqtt_topic_check.check_topic("plant/+/temp")
        self.assertFalse(result["ok"])
        self.assertIn("only legal in a subscription", " ".join(result["problems"]))

    def test_a_publish_topic_cannot_contain_hash(self):
        self.assertFalse(mqtt_topic_check.check_topic("plant/#")["ok"])

    def test_an_empty_topic_is_rejected(self):
        self.assertFalse(mqtt_topic_check.check_topic("")["ok"])

    def test_a_null_character_is_rejected(self):
        self.assertFalse(mqtt_topic_check.check_topic("a/\x00b")["ok"])

    def test_an_empty_level_is_only_a_note(self):
        result = mqtt_topic_check.check_topic("plant//temp")
        self.assertTrue(result["ok"])
        self.assertTrue(result["notes"])

    def test_a_reserved_dollar_topic_is_noted(self):
        result = mqtt_topic_check.check_topic("$SYS/broker/uptime")
        self.assertTrue(result["ok"])
        self.assertIn("reserved", " ".join(result["notes"]))


class MqttFilterTest(unittest.TestCase):
    def test_a_plus_level_is_a_valid_filter(self):
        self.assertTrue(mqtt_topic_check.check_topic("plant/+/temp", subscribe=True)["ok"])

    def test_a_partial_plus_is_rejected(self):
        result = mqtt_topic_check.check_topic("plant/temp+/x", subscribe=True)
        self.assertFalse(result["ok"])
        self.assertIn("entire level", " ".join(result["problems"]))

    def test_a_partial_hash_is_rejected(self):
        self.assertFalse(mqtt_topic_check.check_topic("plant/x#", subscribe=True)["ok"])

    def test_hash_must_be_the_last_level(self):
        result = mqtt_topic_check.check_topic("plant/#/temp", subscribe=True)
        self.assertFalse(result["ok"])
        self.assertIn("last level", " ".join(result["problems"]))

    def test_a_bare_hash_is_a_valid_filter(self):
        self.assertTrue(mqtt_topic_check.check_topic("#", subscribe=True)["ok"])

    def test_a_reserved_tree_filter_is_valid(self):
        self.assertTrue(mqtt_topic_check.check_topic("$SYS/#", subscribe=True)["ok"])


class MqttMatchTest(unittest.TestCase):
    def test_single_level_wildcard_matches_one_level(self):
        self.assertTrue(mqtt_topic_check.matches("plant/+/temp", "plant/line1/temp"))

    def test_single_level_wildcard_does_not_span_levels(self):
        self.assertFalse(mqtt_topic_check.matches("plant/+/temp", "plant/a/b/temp"))

    def test_multi_level_wildcard_matches_the_parent(self):
        self.assertTrue(mqtt_topic_check.matches("plant/#", "plant"))

    def test_multi_level_wildcard_matches_deeper(self):
        self.assertTrue(mqtt_topic_check.matches("plant/#", "plant/a/b"))

    def test_a_dollar_topic_needs_an_explicit_filter(self):
        self.assertFalse(mqtt_topic_check.matches("#", "$SYS/broker/uptime"))
        self.assertTrue(mqtt_topic_check.matches("$SYS/#", "$SYS/broker/uptime"))

    def test_an_exact_mismatch_does_not_match(self):
        self.assertFalse(mqtt_topic_check.matches("a/b", "a/c"))


class SparkplugTest(unittest.TestCase):
    def test_a_node_birth_is_valid(self):
        result = mqtt_topic_check.check_topic("spBv1.0/plant/NDATA/esp32-01")
        self.assertTrue(result["ok"])
        self.assertTrue(result["sparkplug"])

    def test_an_unknown_message_type_is_rejected(self):
        result = mqtt_topic_check.check_topic("spBv1.0/plant/NBOGUS/esp32-01")
        self.assertFalse(result["ok"])
        self.assertIn("not a Sparkplug message type", " ".join(result["problems"]))

    def test_a_device_message_needs_a_device_id(self):
        result = mqtt_topic_check.check_topic("spBv1.0/plant/DBIRTH/esp32-01")
        self.assertFalse(result["ok"])
        self.assertIn("fifth level", " ".join(result["problems"]))

    def test_a_device_message_with_an_id_is_valid(self):
        self.assertTrue(mqtt_topic_check.check_topic(
            "spBv1.0/plant/DBIRTH/esp32-01/sensor-3")["ok"])

    def test_too_many_levels_is_rejected(self):
        self.assertFalse(mqtt_topic_check.check_topic(
            "spBv1.0/plant/NDATA/node/device/extra")["ok"])


class MqttCommandLineTest(unittest.TestCase):
    def test_a_bad_publish_topic_exits_one(self):
        result = run_tool("mqtt_topic_check", "--topic", "a/+/b", "--publish")
        self.assertEqual(result.returncode, 1)

    def test_a_good_topic_exits_zero(self):
        self.assertEqual(run_tool("mqtt_topic_check", "--topic", "a/b").returncode, 0)

    def test_json_reports_the_problems(self):
        result = run_tool("mqtt_topic_check", "--topic", "a/#/b", "--subscribe", "--json")
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["problems"])

    def test_matches_is_reported(self):
        result = run_tool("mqtt_topic_check", "--topic", "a/+/c", "--subscribe",
                          "--matches", "a/b/c", "--json")
        self.assertTrue(json.loads(result.stdout)["matches"])


# ---------------------------------------------------------------------------
# Flash layout
# ---------------------------------------------------------------------------

class FlashLayoutTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.paths = {}
        for name, size in (("boot.bin", 0x7000), ("part.bin", 0x1000), ("app.bin", 0x20000)):
            path = os.path.join(self.tmp, name)
            with open(path, "wb") as handle:
                handle.write(b"\xE9" + b"\x00" * (size - 1))
            self.paths[name] = path

    def entries(self, *pairs):
        return [(offset, self.paths[name], os.path.getsize(self.paths[name]))
                for offset, name in pairs]

    def test_the_classic_layout_is_clean(self):
        report = flash_layout.layout(
            self.entries((0x1000, "boot.bin"), (0x8000, "part.bin"), (0x10000, "app.bin")),
            4 * 1024 * 1024)
        self.assertTrue(report["ok"], report["problems"])

    def test_overlapping_images_are_an_error(self):
        report = flash_layout.layout(
            self.entries((0x1000, "boot.bin"), (0x4000, "part.bin")), 4 * 1024 * 1024)
        self.assertFalse(report["ok"])
        self.assertIn("overlaps", " ".join(report["problems"]))

    def test_images_past_the_flash_are_an_error(self):
        report = flash_layout.layout(self.entries((0x10000, "app.bin")), 64 * 1024)
        self.assertFalse(report["ok"])
        self.assertIn("past the end", " ".join(report["problems"]))

    def test_a_missing_bootloader_offset_is_an_error(self):
        report = flash_layout.layout(
            self.entries((0x8000, "part.bin"), (0x10000, "app.bin")), 4 * 1024 * 1024)
        self.assertIn("0x1000", " ".join(report["problems"]))

    def test_a_missing_partition_table_is_an_error(self):
        report = flash_layout.layout(
            self.entries((0x1000, "boot.bin"), (0x10000, "app.bin")), 4 * 1024 * 1024)
        self.assertIn("0x8000", " ".join(report["problems"]))

    def test_a_merged_image_at_zero_skips_the_layout_checks(self):
        report = flash_layout.layout(self.entries((0, "app.bin")), 4 * 1024 * 1024)
        self.assertTrue(report["ok"])
        self.assertIn("merged", " ".join(report["notes"]))

    def test_a_misaligned_offset_is_a_note(self):
        report = flash_layout.layout(
            self.entries((0x1000, "boot.bin"), (0x8000, "part.bin"), (0x10800, "app.bin")),
            4 * 1024 * 1024)
        self.assertIn("4KB sector", " ".join(report["notes"]))

    def test_the_used_size_is_the_highest_end(self):
        report = flash_layout.layout(
            self.entries((0x1000, "boot.bin"), (0x10000, "app.bin")), 4 * 1024 * 1024)
        self.assertEqual(report["used"], 0x10000 + 0x20000)

    def test_parse_size_understands_megabytes(self):
        self.assertEqual(flash_layout.parse_size("4MB"), 4 * 1024 * 1024)

    def test_parse_size_understands_kilobytes(self):
        self.assertEqual(flash_layout.parse_size("4096K"), 4096 * 1024)

    def test_parse_size_understands_hex(self):
        self.assertEqual(flash_layout.parse_size("0x400000"), 4 * 1024 * 1024)

    def test_human_formats_a_size(self):
        self.assertEqual(flash_layout.human(1024 * 1024), "1.0MB")

    def test_the_command_line_fails_on_an_overlap(self):
        result = run_tool("flash_layout", "--flash", "4MB",
                          "0x1000", self.paths["boot.bin"], "0x4000", self.paths["part.bin"])
        self.assertEqual(result.returncode, 1)

    def test_the_command_line_passes_a_clean_layout(self):
        result = run_tool("flash_layout", "--flash", "4MB",
                          "0x1000", self.paths["boot.bin"],
                          "0x8000", self.paths["part.bin"],
                          "0x10000", self.paths["app.bin"])
        self.assertEqual(result.returncode, 0)


# ---------------------------------------------------------------------------
# I2C addresses
# ---------------------------------------------------------------------------

class I2cAddressTest(unittest.TestCase):
    def test_a_clean_map_passes(self):
        report = i2c_address_check.check([(0x3C, "oled"), (0x68, "rtc"), (0x48, "ads1115")])
        self.assertTrue(report["ok"], report["problems"])

    def test_two_devices_on_one_address_is_an_error(self):
        report = i2c_address_check.check([(0x3C, "oled"), (0x3C, "other")])
        self.assertFalse(report["ok"])
        self.assertIn("share", " ".join(report["problems"]))

    def test_the_reserved_low_range_is_rejected(self):
        report = i2c_address_check.check([(0x04, "x")])
        self.assertFalse(report["ok"])
        self.assertIn("reserved", " ".join(report["problems"]))

    def test_the_reserved_high_range_is_rejected(self):
        report = i2c_address_check.check([(0x78, "x")])
        self.assertFalse(report["ok"])

    def test_a_ten_bit_address_is_noted(self):
        report = i2c_address_check.check([(0x100, "big")])
        self.assertTrue(report["ok"])
        self.assertIn("10-bit", " ".join(report["notes"]))

    def test_a_known_part_is_named(self):
        report = i2c_address_check.check([(0x68, "rtc")])
        self.assertIn("DS3231", " ".join(report["notes"]))

    def test_the_unique_count_ignores_duplicates(self):
        report = i2c_address_check.check([(0x3C, "a"), (0x3C, "b"), (0x40, "c")])
        self.assertEqual(report["unique"], 2)

    def test_the_command_line_fails_on_a_duplicate(self):
        result = run_tool("i2c_address_check", "0x3C:oled", "0x3C:other")
        self.assertEqual(result.returncode, 1)

    def test_the_command_line_passes_a_clean_map(self):
        result = run_tool("i2c_address_check", "0x3C:oled", "0x68:rtc")
        self.assertEqual(result.returncode, 0)

    def test_json_has_the_map(self):
        result = run_tool("i2c_address_check", "0x3C:oled", "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["map"]["0x3C"], "oled")


# ---------------------------------------------------------------------------
# The dispatcher and the build
# ---------------------------------------------------------------------------

class DispatcherTest(unittest.TestCase):
    def test_every_tool_is_listed(self):
        self.assertEqual(len(esp32_skills_cli.TOOLS), 10)

    def test_list_prints_each_command(self):
        out = io.StringIO()
        old = sys.stdout
        sys.stdout = out
        try:
            code = esp32_skills_cli.main(["--list"])
        finally:
            sys.stdout = old
        self.assertEqual(code, 0)
        for name in ("pincheck", "airtime", "modbus-frame", "mqtt-topic", "i2c"):
            self.assertIn(name, out.getvalue())

    def test_an_unknown_command_exits_two(self):
        self.assertEqual(esp32_skills_cli.main(["nope"]), 2)

    def test_no_arguments_exits_two(self):
        self.assertEqual(esp32_skills_cli.main([]), 2)

    def test_a_known_command_is_dispatched(self):
        self.assertEqual(esp32_skills_cli.main(["airtime", "--sf", "7", "--payload", "13"]), 0)

    def test_the_version_flag_works(self):
        self.assertEqual(esp32_skills_cli.main(["--version"]), 0)

    def test_the_module_names_match_the_tool_files(self):
        for module, _ in esp32_skills_cli.TOOLS.values():
            self.assertTrue(os.path.isfile(os.path.join(TOOLS, module.__name__ + ".py")),
                            "%s has no file" % module.__name__)


class BuildArtifactTest(unittest.TestCase):
    """Only runs when dist/ exists; the release workflow builds it there."""

    def setUp(self):
        self.zipapp = os.path.join(ROOT, "dist", "esp32-skills.pyz")
        if not os.path.isfile(self.zipapp):
            self.skipTest("dist/ has not been built")

    def test_the_zipapp_lists_the_commands(self):
        result = subprocess.run([sys.executable, self.zipapp, "--list"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("pincheck", result.stdout)

    def test_the_zipapp_runs_a_real_tool(self):
        result = subprocess.run([sys.executable, self.zipapp, "airtime",
                                 "--sf", "7", "--payload", "13"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("46.336", result.stdout)

    def test_the_zipapp_reports_an_error_with_the_right_exit_code(self):
        result = subprocess.run([sys.executable, self.zipapp, "pincheck",
                                 "--soc", "esp32", "--assign", "6=led"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)

    def test_the_zipapp_carries_the_pin_database(self):
        result = subprocess.run([sys.executable, self.zipapp, "pincheck",
                                 "--soc", "esp32s3", "--assign", "27=led"],
                                capture_output=True, text=True, check=False)
        self.assertIn("flash", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
