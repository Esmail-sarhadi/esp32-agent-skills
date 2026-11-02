#!/usr/bin/env python3
"""Check a planned I2C address map before the boards are built.

Two devices at the same address is the most common I2C bring-up failure, and it
is invisible until both are soldered down. The second most common is picking an
address that is reserved, or one that a module already uses with a different
strap than the datasheet suggests.

This tool knows three things:

- the reserved ranges from the I2C specification (0000xxx and 1111xxx),
- the addresses that conflict across common parts, and
- the 10-bit address range, which is a different space entirely.

Usage:
    python tools/i2c_address_check.py 0x3C:oled 0x48:ads1115 0x68:rtc
    python tools/i2c_address_check.py 0x3C:oled 0x3C:other --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

# Parts that show up on the same bus far more often than they should.
KNOWN = {
    0x3C: "SSD1306 / SH1106 OLED (0x3C or 0x3D)",
    0x3D: "SSD1306 / SH1106 OLED (alternate)",
    0x48: "ADS1115 (ADDR=GND), LM75, TMP102, PCF8591",
    0x49: "ADS1115 (ADDR=VDD), LM75 (A0 high)",
    0x4A: "ADS1115 (ADDR=SDA)",
    0x4B: "ADS1115 (ADDR=SCL)",
    0x50: "AT24C32 EEPROM (also DS3231 module), 24LC256",
    0x57: "AT24C32 (A0/A1/A2 high), MAX30102",
    0x68: "DS3231 RTC, MPU-6050, DS1307",
    0x69: "MPU-6050 (AD0 high), ITG3200",
    0x76: "BME280, BMP280 (SDO low)",
    0x77: "BME280, BMP280 (SDO high)",
    0x40: "INA219, HTU21D, PCA9685",
    0x44: "SHT31, SGP30",
    0x23: "BH1750 (ADDR low), PCF8574",
    0x27: "PCF8574 (A0-A2 high), LCD backpack",
    0x20: "PCF8574 (all low), MCP23017",
    0x60: "MCP4725 (A0 low), Si7021",
    0x61: "MCP4725 (A0 high)",
}


def reserved(address: int) -> Optional[str]:
    """The I2C specification reserves 0000xxx and 1111xxx in the 7-bit space."""
    if not 0 <= address <= 0x7F:
        return "outside the 7-bit address space"
    if 0x00 <= address <= 0x07:
        return "reserved by the I2C specification (0000xxx)"
    if 0x78 <= address <= 0x7F:
        return "reserved for 10-bit addressing (1111xxx)"
    return None


def check(entries) -> dict:
    """entries: list of (address, label)."""
    problems = []
    notes = []
    seen = {}

    for address, label in entries:
        if address > 0x7F:
            notes.append("%s at 0x%X looks like a 10-bit address; it uses a different "
                         "addressing scheme and a second address byte" % (label, address))
            continue
        why = reserved(address)
        if why:
            problems.append("%s at 0x%02X is %s" % (label, address, why))
        if address in seen:
            problems.append("%s and %s share 0x%02X" % (seen[address], label, address))
        else:
            seen[address] = label

    for address in sorted(seen):
        if address in KNOWN:
            notes.append("0x%02X is commonly %s - check the strap on your module"
                         % (address, KNOWN[address]))

    return {
        "devices": len(entries),
        "unique": len(seen),
        "ok": not problems,
        "problems": problems,
        "notes": notes,
        "map": {("0x%02X" % a): seen[a] for a in sorted(seen)},
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Check an I2C address map.")
    parser.add_argument("entries", nargs="+", metavar="0xADDR:label")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    parsed = []
    for raw in args.entries:
        if ":" not in raw:
            parser.error("%r should look like 0x3C:oled" % raw)
        address_text, label = raw.split(":", 1)
        try:
            address = int(address_text, 0)
        except ValueError:
            parser.error("cannot read address %r" % address_text)
        parsed.append((address, label.strip() or "unnamed"))

    report = check(parsed)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    print("%d device(s), %d unique address(es)" % (report["devices"], report["unique"]))
    for address, label in sorted(report["map"].items()):
        print("  %s  %s" % (address, label))
    print("")
    for problem in report["problems"]:
        print("  ERROR  %s" % problem)
    for note in report["notes"]:
        print("  note   %s" % note)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
