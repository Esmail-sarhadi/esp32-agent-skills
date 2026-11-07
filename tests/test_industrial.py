"""The industrial wave: new skills, the RTU frame tool, and the register-map checker.

Three jobs here.

The first is the shape of the twenty-two skills added in this round. They are the
ones that touch real hardware in a cabinet, so they are held to a slightly
stricter rule than the rest: a symptom table and an explicit constraint are
required, not optional.

The second is `tools/modbus_frame.py`. Its CRC is pinned to two frames published
in Modbus documentation, which is the only way to know an implementation of that
algorithm is right - a CRC that is wrong in the same way on both ends still
"works" on the bench and fails on the third device.

The third is the register-map checker that came in with the merge: every way a
CSV map can be wrong, one test each.
"""

import io
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import modbus_frame  # noqa: E402
import modbus_map_check  # noqa: E402

SKILLS_DIR = os.path.join(ROOT, "skills")
TOOL = os.path.join(ROOT, "tools", "modbus_frame.py")
MAP_TOOL = os.path.join(ROOT, "tools", "modbus_map_check.py")

INDUSTRIAL = [
    "esp32-enc28j60-ethernet",
    "esp32-rs485-isolated-transceivers",
    "esp32-sx127x-lora",
    "esp32-nrf24l01",
    "esp32-rfm69-subghz",
    "esp32-ads1115-external-adc",
    "esp32-ads1256-precision-adc",
    "esp32-mcp4725-analog-output",
    "esp32-4-20ma-transmitter",
    "esp32-vfd-modbus-control",
    "esp32-poe-power",
    "esp32-surge-and-tvs-protection",
    "esp32-isolated-digital-input",
    "esp32-din-rail-power",
    "esp32-energy-meter-modbus",
    "esp32-iec-60870-5-104",
    "esp32-snmp-agent",
    "esp32-sparkplug-b-mqtt",
    "esp32-canopen-basics",
    "esp32-modbus-rtu-slave",
    "esp32-modbus-rtu-tcp-gateway",
    "esp32-wifi-enterprise-eap",
]


def read_skill(name):
    with io.open(os.path.join(SKILLS_DIR, name, "SKILL.md"), encoding="utf-8") as handle:
        return handle.read()


# ---------------------------------------------------------------------------
# The industrial skills: a symptom table and a hard constraint
# ---------------------------------------------------------------------------

class IndustrialSkillTest(unittest.TestCase):
    """Field-facing skills have to be usable when something is already broken."""


def _make_symptom_test(name):
    def test(self):
        text = read_skill(name)
        self.assertIn("## Symptom table", text,
                      "%s must map symptoms to causes; that is what an agent needs at 2am" % name)
        rows = [line for line in text.splitlines() if line.startswith("| ") and "|" in line[2:]]
        self.assertGreaterEqual(len(rows), 4, "%s has a symptom table with too few rows" % name)

    test.__name__ = "test_%s_has_a_symptom_table" % name.replace("-", "_")
    return test


def _make_constraint_test(name):
    def test(self):
        text = read_skill(name).lower()
        hard_words = ("never", "must", "cannot", "not optional", "mandatory", "forbidden")
        found = [word for word in hard_words if word in text]
        self.assertTrue(found, "%s states no hard constraint, only description" % name)

    test.__name__ = "test_%s_states_a_hard_constraint" % name.replace("-", "_")
    return test


for _name in INDUSTRIAL:
    setattr(IndustrialSkillTest, "test_%s_has_a_symptom_table" % _name.replace("-", "_"),
            _make_symptom_test(_name))
    setattr(IndustrialSkillTest, "test_%s_states_a_hard_constraint" % _name.replace("-", "_"),
            _make_constraint_test(_name))


# ---------------------------------------------------------------------------
# Modbus RTU frames
# ---------------------------------------------------------------------------

class CrcTest(unittest.TestCase):
    def test_the_published_read_request_vector(self):
        # 01 03 0000 000A is the example frame in every Modbus RTU tutorial.
        frame = modbus_frame.build_read(1, 0, 10)
        self.assertEqual(frame.hex(" ").upper(), "01 03 00 00 00 0A C5 CD")

    def test_the_second_published_vector(self):
        # 11 03 006B 0003 with CRC 76 87, the other frame everybody quotes.
        frame = modbus_frame.build_read(0x11, 0x6B, 3)
        self.assertEqual(frame.hex(" ").upper(), "11 03 00 6B 00 03 76 87")

    def test_crc_of_the_two_vectors_directly(self):
        self.assertEqual(modbus_frame.crc16(bytes.fromhex("01030000000A")), 0xCDC5)
        self.assertEqual(modbus_frame.crc16(bytes.fromhex("1103006B0003")), 0x8776)

    def test_the_crc_goes_low_byte_first(self):
        frame = modbus_frame.build_read(1, 0, 10)
        value = modbus_frame.crc16(frame[:-2])
        self.assertEqual(frame[-2], value & 0xFF)
        self.assertEqual(frame[-1], (value >> 8) & 0xFF)

    def test_a_single_bit_change_breaks_the_crc(self):
        frame = bytearray(modbus_frame.build_read(1, 0, 10))
        frame[4] ^= 0x01
        with self.assertRaises(ValueError):
            modbus_frame.parse_frame(bytes(frame))


class BuildTest(unittest.TestCase):
    def test_a_read_request_is_eight_bytes(self):
        self.assertEqual(len(modbus_frame.build_read(1, 0, 1)), 8)

    def test_function_one_reads_coils(self):
        self.assertEqual(modbus_frame.build_read(1, 0, 1, function=1)[1], 1)

    def test_a_write_single_register_frame(self):
        frame = modbus_frame.build_write_single(1, 1, 3)
        self.assertEqual(frame[:6].hex(" ").upper(), "01 06 00 01 00 03")

    def test_slave_zero_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.build_read(0, 0, 1)

    def test_slave_248_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.build_read(248, 0, 1)

    def test_zero_registers_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.build_read(1, 0, 0)

    def test_more_than_125_registers_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.build_read(1, 0, 126)

    def test_a_request_past_the_address_space_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.build_read(1, 0xFFFF, 2)

    def test_a_write_function_in_a_read_request_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.build_read(1, 0, 1, function=6)

    def test_a_value_above_16_bits_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.build_write_single(1, 0, 0x10000)

    def test_the_last_valid_address_is_accepted(self):
        self.assertEqual(len(modbus_frame.build_read(1, 0xFFFF, 1)), 8)


class ParseTest(unittest.TestCase):
    def test_a_valid_request_parses(self):
        parsed = modbus_frame.parse_frame(modbus_frame.build_read(17, 0x6B, 3))
        self.assertEqual(parsed["slave"], 17)
        self.assertEqual(parsed["function"], 3)
        self.assertEqual(parsed["bytes"], 8)

    def test_the_function_name_is_resolved(self):
        parsed = modbus_frame.parse_frame(modbus_frame.build_read(1, 0, 1))
        self.assertEqual(parsed["function_name"], "read holding registers")

    def test_a_response_byte_count_is_checked(self):
        body = bytes([1, 3, 4, 0x00, 0x0A, 0x00, 0x0B])
        parsed = modbus_frame.parse_frame(modbus_frame.with_crc(body))
        self.assertEqual(parsed["byte_count"], 4)
        self.assertTrue(parsed["payload_matches_count"])

    def test_a_short_response_is_flagged(self):
        body = bytes([1, 3, 4, 0x00, 0x0A])
        parsed = modbus_frame.parse_frame(modbus_frame.with_crc(body))
        self.assertFalse(parsed["payload_matches_count"])

    def test_an_exception_response_is_decoded(self):
        body = bytes([1, 0x83, 0x02])
        parsed = modbus_frame.parse_frame(modbus_frame.with_crc(body))
        self.assertEqual(parsed["exception"]["code"], 2)
        self.assertEqual(parsed["exception"]["name"], "illegal data address")

    def test_a_gateway_timeout_exception_is_named(self):
        body = bytes([1, 0x83, 0x0B])
        parsed = modbus_frame.parse_frame(modbus_frame.with_crc(body))
        self.assertIn("failed to respond", parsed["exception"]["name"])

    def test_a_three_byte_frame_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.parse_frame(b"\x01\x03\x00")

    def test_a_bad_crc_names_both_values(self):
        frame = bytearray(modbus_frame.build_read(1, 0, 1))
        frame[-1] ^= 0xFF
        with self.assertRaises(ValueError) as caught:
            modbus_frame.parse_frame(bytes(frame))
        self.assertIn("CRC mismatch", str(caught.exception))


class TimingTest(unittest.TestCase):
    def test_one_character_at_9600_is_about_1_15_ms(self):
        self.assertAlmostEqual(modbus_frame.char_time_ms(9600), 1.1458, places=3)

    def test_one_character_at_115200_is_about_0_095_ms(self):
        self.assertAlmostEqual(modbus_frame.char_time_ms(115200), 0.0955, places=3)

    def test_the_gap_is_three_and_a_half_characters(self):
        self.assertAlmostEqual(modbus_frame.gap_ms(9600), 4.0104, places=3)

    def test_the_gap_at_115200_is_below_a_millisecond(self):
        self.assertFalse(modbus_frame.timing(115200)["gap_fits_1ms_tick"])

    def test_the_gap_at_9600_is_above_a_millisecond(self):
        self.assertTrue(modbus_frame.timing(9600)["gap_fits_1ms_tick"])

    def test_a_wider_frame_bits_per_char_slows_everything(self):
        self.assertGreater(modbus_frame.char_time_ms(9600, bits=12),
                           modbus_frame.char_time_ms(9600, bits=11))

    def test_zero_baud_is_rejected(self):
        with self.assertRaises(ValueError):
            modbus_frame.char_time_ms(0)

    def test_throughput_drops_with_baud(self):
        self.assertLess(modbus_frame.timing(115200)["frames_per_second_8_byte"],
                        modbus_frame.timing(9600)["frames_per_second_8_byte"] * 1000)


class CommandLineTest(unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run([sys.executable, TOOL, *args],
                              capture_output=True, text=True, check=False)

    def test_building_a_frame_prints_it(self):
        result = self.run_tool("--build", "read", "--slave", "1", "--start", "0", "--count", "10")
        self.assertEqual(result.returncode, 0)
        self.assertIn("C5 CD", result.stdout)

    def test_hex_arguments_are_accepted(self):
        result = self.run_tool("--build", "read", "--slave", "0x11", "--start", "0x6B", "--count", "3")
        self.assertEqual(result.returncode, 0)
        self.assertIn("76 87", result.stdout)

    def test_checking_a_good_frame_exits_zero(self):
        result = self.run_tool("--check", "11 03 00 6B 00 03 76 87")
        self.assertEqual(result.returncode, 0)
        self.assertIn("valid frame", result.stdout)

    def test_checking_a_bad_frame_exits_one(self):
        result = self.run_tool("--check", "11 03 00 6B 00 03 76 88")
        self.assertEqual(result.returncode, 1)
        self.assertIn("CRC mismatch", result.stderr)

    def test_timing_json_has_the_gap(self):
        result = self.run_tool("--timing", "--baud", "19200", "--json")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gap_ms", result.stdout)

    def test_an_invalid_slave_exits_one(self):
        result = self.run_tool("--build", "read", "--slave", "0", "--count", "1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("broadcast", result.stderr)


# ---------------------------------------------------------------------------
# The register-map checker
# ---------------------------------------------------------------------------

HEADER = "name,table,address,type,access,scale,unit,description\n"


def map_findings(text):
    handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
    handle.write(HEADER + text)
    handle.close()
    try:
        rows = modbus_map_check.parse_map(handle.name)
    finally:
        os.unlink(handle.name)
    return modbus_map_check.check(rows)


def messages(findings):
    return " | ".join(f["message"] for f in findings)


class RegisterMapTest(unittest.TestCase):
    def test_a_clean_map_has_no_errors(self):
        findings, errors = map_findings(
            "status,holding,0x0000,U16,R,1,1,status bitfield\n"
            "temp,input,0x0010,I16,R,0.1,degC,tenths of a degree\n")
        self.assertEqual(errors, 0, messages(findings))

    def test_the_shipped_example_is_clean(self):
        rows = modbus_map_check.parse_map(os.path.join(ROOT, "examples", "modbus-register-map.csv"))
        findings, errors = modbus_map_check.check(rows)
        self.assertEqual(errors, 0, messages(findings))

    def test_a_duplicate_name_is_an_error(self):
        findings, errors = map_findings(
            "status,holding,0x0000,U16,R,1,1,a\n"
            "Status,holding,0x0001,U16,R,1,1,b\n")
        self.assertEqual(errors, 1)
        self.assertIn("duplicate point name", messages(findings))

    def test_an_unknown_table_is_an_error(self):
        findings, errors = map_findings("x,register,0x0000,U16,R,1,1,a\n")
        self.assertEqual(errors, 1)
        self.assertIn("table must be one of", messages(findings))

    def test_an_unknown_type_is_an_error(self):
        findings, errors = map_findings("x,holding,0x0000,FLOAT,R,1,1,a\n")
        self.assertEqual(errors, 1)
        self.assertIn("unsupported type", messages(findings))

    def test_an_unknown_access_is_an_error(self):
        findings, errors = map_findings("x,holding,0x0000,U16,X,1,1,a\n")
        self.assertEqual(errors, 1)
        self.assertIn("access must be", messages(findings))

    def test_a_zero_scale_is_an_error(self):
        findings, errors = map_findings("x,holding,0x0000,U16,R,0,1,a\n")
        self.assertEqual(errors, 1)
        self.assertIn("scale must be", messages(findings))

    def test_a_non_numeric_scale_is_an_error(self):
        findings, errors = map_findings("x,holding,0x0000,U16,R,abc,1,a\n")
        self.assertEqual(errors, 1)

    def test_a_missing_unit_is_an_error(self):
        findings, errors = map_findings("x,holding,0x0000,U16,R,1,,a\n")
        self.assertEqual(errors, 1)
        self.assertIn("unit is required", messages(findings))

    def test_an_empty_description_is_only_a_warning(self):
        findings, errors = map_findings("x,holding,0x0000,U16,R,1,1,\n")
        self.assertEqual(errors, 0)
        self.assertIn("description is empty", messages(findings))

    def test_a_coil_table_must_use_bool(self):
        findings, errors = map_findings("x,coil,0x0001,U16,RW,1,1,a\n")
        self.assertEqual(errors, 1)
        self.assertIn("must use BOOL", messages(findings))

    def test_bool_in_a_register_table_is_a_warning(self):
        findings, errors = map_findings("x,holding,0x0001,BOOL,RW,1,1,a\n")
        self.assertEqual(errors, 0)
        self.assertIn("vendor-specific", messages(findings))

    def test_a_32_bit_value_overlapping_the_next_point_is_an_error(self):
        findings, errors = map_findings(
            "energy,holding,0x0020,U32,R,1,kWh,a\n"
            "status,holding,0x0021,U16,R,1,1,b\n")
        self.assertEqual(errors, 1)
        self.assertIn("overlaps", messages(findings))

    def test_a_32_bit_value_with_room_is_fine(self):
        findings, errors = map_findings(
            "energy,holding,0x0020,U32,R,1,kWh,a\n"
            "status,holding,0x0022,U16,R,1,1,b\n")
        self.assertEqual(errors, 0, messages(findings))

    def test_a_value_past_the_address_space_is_an_error(self):
        findings, errors = map_findings("energy,holding,0xFFFF,U32,R,1,kWh,a\n")
        self.assertEqual(errors, 1)
        self.assertIn("outside the 16-bit", messages(findings))

    def test_a_non_numeric_address_is_an_error(self):
        findings, errors = map_findings("x,holding,start,U16,R,1,1,a\n")
        self.assertEqual(errors, 1)
        self.assertIn("decimal or 0x-prefixed", messages(findings))

    def test_a_decimal_address_is_accepted(self):
        findings, errors = map_findings("x,holding,16,U16,R,1,1,a\n")
        self.assertEqual(errors, 0, messages(findings))

    def test_a_missing_column_is_rejected_at_parse_time(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        handle.write("name,table,address\nx,holding,0\n")
        handle.close()
        try:
            with self.assertRaises(ValueError):
                modbus_map_check.parse_map(handle.name)
        finally:
            os.unlink(handle.name)

    def test_a_header_only_file_is_rejected(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        handle.write(HEADER)
        handle.close()
        try:
            with self.assertRaises(ValueError):
                modbus_map_check.parse_map(handle.name)
        finally:
            os.unlink(handle.name)

    def test_every_finding_carries_a_line_number(self):
        findings, _ = map_findings("x,holding,0x0000,U16,X,1,1,a\n")
        self.assertTrue(all(f.get("line") for f in findings))

    def test_the_error_count_matches_the_error_findings(self):
        findings, errors = map_findings(
            "a,holding,0x0000,U16,R,0,1,x\n"
            "b,holding,0x0001,U16,X,1,1,y\n")
        self.assertEqual(errors, sum(1 for f in findings if f["severity"] == modbus_map_check.ERROR))

    def test_the_broken_example_fails(self):
        rows = modbus_map_check.parse_map(os.path.join(ROOT, "examples", "modbus-register-map-broken.csv"))
        _, errors = modbus_map_check.check(rows)
        self.assertGreater(errors, 0)

    def test_the_command_line_exits_one_on_the_broken_example(self):
        result = subprocess.run([sys.executable, MAP_TOOL, "--file",
                                 os.path.join(ROOT, "examples", "modbus-register-map-broken.csv")],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
