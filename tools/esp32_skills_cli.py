#!/usr/bin/env python3
"""One entry point for every checker in this repository.

The tools are separate scripts on purpose: each one is readable on its own and
importable from a test. This wrapper exists so a single binary can carry all of
them, which is what the Windows and Linux builds ship.

The imports below are deliberately static, not `importlib.import_module(name)`.
PyInstaller finds modules by reading the bytecode, and a name that only exists
as a string is a module it will not bundle - the executable then starts, prints
its help, and dies with ModuleNotFoundError on the first real command.

    esp32-skills pincheck --soc esp32 --assign "12=relay,34=button"
    esp32-skills airtime --sf 12 --payload 20
    esp32-skills --list
"""

from __future__ import annotations

import sys

import airtime
import flash_layout
import i2c_address_check
import modbus_frame
import modbus_map_check
import mqtt_topic_check
import panic_decode
import partition_check
import pincheck
import power_budget

TOOLS = {
    "pincheck": (pincheck, "Is this GPIO allowed to do this job on this SoC?"),
    "partition": (partition_check, "Does this partition table fit the flash and support OTA?"),
    "power": (power_budget, "How long does this duty cycle last on this battery?"),
    "panic": (panic_decode, "Which addr2line command turns this crash dump into file:line?"),
    "airtime": (airtime, "Does this LoRa payload fit the duty cycle at this spreading factor?"),
    "modbus-map": (modbus_map_check, "Does this register map overlap itself or lie about its types?"),
    "modbus-frame": (modbus_frame, "Is this RTU frame valid, and does the 3.5 character gap fit?"),
    "mqtt-topic": (mqtt_topic_check, "Is this topic legal, and does the filter match it?"),
    "flash-layout": (flash_layout, "Do these images overlap, and do they fit the flash?"),
    "i2c": (i2c_address_check, "Do two devices share an address, or use a reserved one?"),
}


def usage() -> str:
    lines = ["esp32-skills <command> [options]", "", "Commands:"]
    width = max(len(name) for name in TOOLS)
    for name, (_, description) in TOOLS.items():
        lines.append("  %-*s  %s" % (width, name, description))
    lines.append("")
    lines.append("Run 'esp32-skills <command> --help' for the options of one tool.")
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0] in ("-h", "--help", "help"):
        print(usage())
        return 0 if argv else 2

    if argv[0] in ("-l", "--list", "list"):
        for name, (_, description) in TOOLS.items():
            print("%-14s %s" % (name, description))
        return 0

    if argv[0] in ("-V", "--version", "version"):
        print("esp32-skills 1.0")
        return 0

    command = argv[0]
    if command not in TOOLS:
        print("unknown command %r\n" % command, file=sys.stderr)
        print(usage(), file=sys.stderr)
        return 2

    module = TOOLS[command][0]
    return module.main(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
