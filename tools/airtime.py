#!/usr/bin/env python3
"""Compute LoRa time on air, and the interval a duty cycle allows.

"Report every 30 seconds" and "use SF12 for range" are two decisions that
cannot both be true in the EU868 band. A 20 byte payload at SF12 occupies the
channel for 1.3 seconds, and the legal duty cycle is 1 %, so the earliest the
next packet may go out is about two minutes later.

The arithmetic is the Semtech formula (AN1200.13, section 4), the same one
behind every airtime calculator. Nothing here is estimated:

    Tsym    = 2^SF / BW
    Tpre    = (n_preamble + 4.25) * Tsym
    n_pay   = 8 + max(ceil((8*PL - 4*SF + 28 + 16*CRC - 20*IH) / (4*(SF - 2*DE))) * (CR + 4), 0)
    ToA     = Tpre + n_pay * Tsym

DE (low data rate optimize) is on when the symbol time exceeds 16 ms, which is
SF11 and SF12 at 125 kHz. It changes the denominator, so a calculator that
ignores it is wrong by about 40 % on exactly the settings people use for range.

Usage:
    python tools/airtime.py --sf 12 --bw 125 --payload 20
    python tools/airtime.py --sf 7 --bw 125 --payload 13 --interval 30
    python tools/airtime.py --sf 9 --bw 125 --payload 51 --duty 0.1 --json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Optional

SF_MIN, SF_MAX = 5, 12          # SX126x goes down to 5, SX127x stops at 6
PAYLOAD_MIN, PAYLOAD_MAX = 1, 255
BW_CHOICES = (7.8, 10.4, 15.6, 20.8, 31.25, 41.7, 62.5, 125.0, 250.0, 500.0)


def ldro_required(sf: int, bw_khz: float) -> bool:
    """Low data rate optimize is on when a symbol lasts longer than 16 ms."""
    return (2 ** sf) / (bw_khz * 1000.0) > 0.016


def payload_symbols(sf: int, payload: int, cr: int, ldro: bool,
                    explicit_header: bool = True, crc: bool = True) -> int:
    """Number of symbols the payload occupies, before the 8 symbol preamble gap.

    In the Semtech formula ``IH`` is 1 for *implicit* header, so an explicit
    header subtracts nothing and an implicit one subtracts 20 bits.
    """
    numerator = 8 * payload - 4 * sf + 28 + (16 if crc else 0) - (0 if explicit_header else 20)
    denominator = 4 * (sf - (2 if ldro else 0))
    steps = math.ceil(numerator / denominator)
    return 8 + max(steps, 0) * (cr + 4)


def airtime(sf: int, bw_khz: float, payload: int, cr: int = 1, preamble: int = 8,
            explicit_header: bool = True, crc: bool = True,
            duty: float = 0.01) -> dict:
    """Return the airtime breakdown and what the duty cycle allows.

    ``cr`` is the index, not the fraction: 1 is 4/5, 4 is 4/8. ``duty`` is a
    fraction of one, so 0.01 is the EU868 1 % band.
    """
    if not SF_MIN <= sf <= SF_MAX:
        raise ValueError("spreading factor must be between %d and %d" % (SF_MIN, SF_MAX))
    if bw_khz <= 0:
        raise ValueError("bandwidth must be positive")
    if not PAYLOAD_MIN <= payload <= PAYLOAD_MAX:
        raise ValueError("payload must be between %d and %d bytes" % (PAYLOAD_MIN, PAYLOAD_MAX))
    if not 1 <= cr <= 4:
        raise ValueError("coding rate index must be 1 (4/5) to 4 (4/8)")
    if preamble < 0:
        raise ValueError("preamble length cannot be negative")
    if not 0 < duty <= 1:
        raise ValueError("duty cycle must be a fraction greater than 0 and at most 1")

    ldro = ldro_required(sf, bw_khz)
    tsym = (2 ** sf) / (bw_khz * 1000.0)
    preamble_s = (preamble + 4.25) * tsym
    symbols = payload_symbols(sf, payload, cr, ldro, explicit_header, crc)
    payload_s = symbols * tsym
    total_s = preamble_s + payload_s

    min_interval_s = total_s / duty
    return {
        "sf": sf,
        "bw_khz": bw_khz,
        "payload": payload,
        "coding_rate": "4/%d" % (cr + 4),
        "preamble": preamble,
        "ldro": ldro,
        "symbol_ms": tsym * 1000.0,
        "preamble_ms": preamble_s * 1000.0,
        "payload_symbols": symbols,
        "payload_ms": payload_s * 1000.0,
        "airtime_ms": total_s * 1000.0,
        "airtime_s": total_s,
        "duty": duty,
        "min_interval_s": min_interval_s,
        "packets_per_hour": 3600.0 / min_interval_s if min_interval_s > 0 else float("inf"),
        "max_payload_per_hour": int(payload * 3600.0 / min_interval_s) if min_interval_s > 0 else 0,
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="LoRa time on air and duty cycle budget.")
    parser.add_argument("--sf", type=int, required=True, help="spreading factor 5-12")
    parser.add_argument("--bw", type=float, default=125.0, help="bandwidth in kHz (125, 250, 500)")
    parser.add_argument("--payload", type=int, required=True, help="application payload in bytes")
    parser.add_argument("--cr", type=int, default=1, help="coding rate index: 1=4/5 ... 4=4/8")
    parser.add_argument("--preamble", type=int, default=8, help="preamble symbols")
    parser.add_argument("--no-crc", action="store_true", help="payload CRC disabled")
    parser.add_argument("--implicit-header", action="store_true", help="implicit header mode")
    parser.add_argument("--duty", type=float, default=0.01,
                        help="duty cycle as a fraction: 0.01 is the EU868 1%% band")
    parser.add_argument("--interval", type=float, default=None,
                        help="planned seconds between packets, checked against the duty cycle")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = airtime(
            args.sf, args.bw, args.payload, args.cr, args.preamble,
            not args.implicit_header, not args.no_crc, args.duty,
        )
    except ValueError as exc:
        parser.error(str(exc))

    too_fast = args.interval is not None and args.interval < result["min_interval_s"]

    if args.json:
        payload = dict(result)
        payload["requested_interval_s"] = args.interval
        payload["violates_duty_cycle"] = too_fast
        print(json.dumps(payload, indent=2))
        return 1 if too_fast else 0

    print("SF%d / %g kHz / CR %s / %d bytes / preamble %d"
          % (result["sf"], result["bw_khz"], result["coding_rate"],
             result["payload"], result["preamble"]))
    print("")
    print("  symbol time   %8.3f ms   (low data rate optimize %s)"
          % (result["symbol_ms"], "on" if result["ldro"] else "off"))
    print("  preamble      %8.3f ms" % result["preamble_ms"])
    print("  payload       %8.3f ms   (%d symbols)"
          % (result["payload_ms"], result["payload_symbols"]))
    print("  airtime       %8.3f ms   (%.3f s)" % (result["airtime_ms"], result["airtime_s"]))
    print("")
    print("  at a %g%% duty cycle" % (result["duty"] * 100))
    print("    earliest next packet  %.1f s" % result["min_interval_s"])
    print("    ceiling               %.1f packets/hour, %d payload bytes/hour"
          % (result["packets_per_hour"], result["max_payload_per_hour"]))

    if args.interval is not None:
        print("")
        if too_fast:
            print("  every %.1f s is %.1fx over the duty cycle: the radio may send, "
                  "the network server will drop it" % (args.interval,
                                                       result["min_interval_s"] / args.interval))
            return 1
        print("  every %.1f s is inside the budget (%.1f s of headroom)"
              % (args.interval, args.interval - result["min_interval_s"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
