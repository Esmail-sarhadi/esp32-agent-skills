#!/usr/bin/env python3
"""Estimate battery life for an ESP32 node from its duty cycle.

"3000 mAh battery, should last a year" is the sentence that turns into a
rewrite three weeks later. This turns the duty cycle into a number before the
board is built, and shows which term dominates so it is obvious what to fix.

The current figures are datasheet-typical values, not measurements. Override
them with the numbers from your own meter; the point of the tool is the
arithmetic and the breakdown, not the defaults.

Usage:
    python tools/power_budget.py --battery 3000 --wakes-per-hour 12 --wake-ms 2000
    python tools/power_budget.py --battery 2000 --wakes-per-hour 60 --wake-ms 800 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

# Datasheet-typical values for the classic ESP32. Replace with your own
# measurements when they disagree; the tool prints which term dominates.
DEFAULT_SLEEP_UA = 10.0        # deep sleep, module only
DEFAULT_ACTIVE_MA = 80.0       # awake but not transmitting
DEFAULT_TX_MA = 240.0          # 802.11b, 17 dBm, datasheet peak
DEFAULT_TX_MS = 250.0          # per wake, connecting and sending one packet


def battery_life(
    battery_mah: float,
    wakes_per_hour: float,
    wake_ms: float,
    sleep_ua: float = DEFAULT_SLEEP_UA,
    active_ma: float = DEFAULT_ACTIVE_MA,
    tx_ma: float = DEFAULT_TX_MA,
    tx_ms: float = DEFAULT_TX_MS,
) -> dict:
    """Return the average current and the resulting battery life."""
    if battery_mah <= 0:
        raise ValueError("battery capacity must be positive")
    if wakes_per_hour < 0 or wake_ms < 0 or tx_ms < 0:
        raise ValueError("durations and counts cannot be negative")
    if wake_ms > 0 and tx_ms > wake_ms:
        raise ValueError("tx_ms cannot exceed wake_ms, the radio cannot transmit while asleep")

    awake_ms_per_hour = wakes_per_hour * wake_ms
    if awake_ms_per_hour > 3_600_000:
        raise ValueError("the node is awake more than 100%% of the time, reduce wakes or wake_ms")

    tx_ms_per_hour = wakes_per_hour * min(tx_ms, wake_ms)
    idle_ms_per_hour = awake_ms_per_hour - tx_ms_per_hour
    sleep_ms_per_hour = 3_600_000 - awake_ms_per_hour

    sleep_ma = sleep_ua / 1000.0
    charge = (
        sleep_ma * sleep_ms_per_hour
        + active_ma * idle_ms_per_hour
        + tx_ma * tx_ms_per_hour
    ) / 3_600_000.0

    hours = battery_mah / charge if charge > 0 else float("inf")

    parts = {
        "sleep": sleep_ma * sleep_ms_per_hour / 3_600_000.0,
        "idle": active_ma * idle_ms_per_hour / 3_600_000.0,
        "tx": tx_ma * tx_ms_per_hour / 3_600_000.0,
    }
    dominant = max(parts, key=parts.get)

    return {
        "average_ma": charge,
        "hours": hours,
        "days": hours / 24.0,
        "duty_cycle_percent": 100.0 * awake_ms_per_hour / 3_600_000.0,
        "breakdown_ma": parts,
        "dominant_term": dominant,
        "dominant_percent": 100.0 * parts[dominant] / charge if charge > 0 else 0.0,
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate ESP32 battery life.")
    parser.add_argument("--battery", type=float, required=True, help="capacity in mAh")
    parser.add_argument("--wakes-per-hour", type=float, required=True)
    parser.add_argument("--wake-ms", type=float, required=True, help="awake time per wake")
    parser.add_argument("--sleep-ua", type=float, default=DEFAULT_SLEEP_UA)
    parser.add_argument("--active-ma", type=float, default=DEFAULT_ACTIVE_MA)
    parser.add_argument("--tx-ma", type=float, default=DEFAULT_TX_MA)
    parser.add_argument("--tx-ms", type=float, default=DEFAULT_TX_MS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = battery_life(
            args.battery, args.wakes_per_hour, args.wake_ms,
            args.sleep_ua, args.active_ma, args.tx_ma, args.tx_ms,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print("%.1f mAh battery, %g wake(s)/hour, %g ms awake each"
          % (args.battery, args.wakes_per_hour, args.wake_ms))
    print("")
    print("  duty cycle      %.2f%%" % result["duty_cycle_percent"])
    print("  average current %.3f mA" % result["average_ma"])
    print("  battery life    %.1f days (%.1f hours)" % (result["days"], result["hours"]))
    print("")
    print("  where the charge goes")
    for name, value in sorted(result["breakdown_ma"].items(), key=lambda kv: -kv[1]):
        share = 100.0 * value / result["average_ma"] if result["average_ma"] else 0.0
        print("    %-6s %8.3f mA  %5.1f%%" % (name, value, share))
    print("")
    print("  dominant term: %s (%.1f%%), fix that one first"
          % (result["dominant_term"], result["dominant_percent"]))
    print("  values are datasheet-typical, override them with your own measurements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
