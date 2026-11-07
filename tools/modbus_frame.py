#!/usr/bin/env python3
"""Modbus RTU frames: build them, check them, and time the gaps between them.

Two things go wrong in every Modbus RTU integration, and neither is visible in
the code that "works on the bench":

1. The CRC is computed over the wrong bytes, or the frame carries a byte count
   that does not match the data. The slave answers nothing, and the master
   reports a timeout rather than a format error.
2. The inter-frame gap is measured with a millisecond timer. At 9600 baud 3.5
   characters is 3.65 ms, which a 1 ms tick can just about see; at 115200 it is
   0.3 ms, which it cannot. Frames then merge and the slave drops both.

This tool does the arithmetic and the encoding, so a plan can state the real
numbers instead of "about 4 ms".

Usage:
    python tools/modbus_frame.py --build read --slave 1 --start 0 --count 10
    python tools/modbus_frame.py --check "11 03 00 6B 00 03 76 87"
    python tools/modbus_frame.py --timing --baud 115200
    python tools/modbus_frame.py --build read --slave 1 --start 0 --count 10 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

EXCEPTIONS = {
    1: "illegal function",
    2: "illegal data address",
    3: "illegal data value",
    4: "slave device failure",
    5: "acknowledge",
    6: "slave device busy",
    8: "memory parity error",
    10: "gateway path unavailable",
    11: "gateway target device failed to respond",
}

FUNCTION_NAMES = {
    1: "read coils",
    2: "read discrete inputs",
    3: "read holding registers",
    4: "read input registers",
    5: "write single coil",
    6: "write single register",
    15: "write multiple coils",
    16: "write multiple registers",
}


def crc16(data: bytes) -> int:
    """Modbus CRC-16: polynomial 0xA001, initial value 0xFFFF, no reflection."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def with_crc(pdu: bytes) -> bytes:
    """Append the CRC low byte first, which is the order on the wire."""
    value = crc16(pdu)
    return pdu + bytes([value & 0xFF, (value >> 8) & 0xFF])


def build_read(slave: int, start: int, count: int, function: int = 3) -> bytes:
    if not 1 <= slave <= 247:
        raise ValueError("slave address must be 1-247; 0 is broadcast and cannot be read")
    if function not in (1, 2, 3, 4):
        raise ValueError("read functions are 1, 2, 3 and 4")
    if count < 1 or count > 125:
        raise ValueError("read one to 125 registers or coils per request")
    if start < 0 or start > 0xFFFF:
        raise ValueError("start address must be 0-65535")
    if start + count - 1 > 0xFFFF:
        raise ValueError("the request runs past address 65535")
    pdu = bytes([slave, function,
                 (start >> 8) & 0xFF, start & 0xFF,
                 (count >> 8) & 0xFF, count & 0xFF])
    return with_crc(pdu)


def build_write_single(slave: int, address: int, value: int, function: int = 6) -> bytes:
    if not 1 <= slave <= 247:
        raise ValueError("slave address must be 1-247")
    if function not in (5, 6):
        raise ValueError("single writes are function 5 (coil) and 6 (register)")
    if not 0 <= value <= 0xFFFF:
        raise ValueError("value must be 0-65535")
    pdu = bytes([slave, function,
                 (address >> 8) & 0xFF, address & 0xFF,
                 (value >> 8) & 0xFF, value & 0xFF])
    return with_crc(pdu)


def parse_frame(frame: bytes) -> dict:
    """Validate a frame and describe it. Raises ValueError when it is not valid."""
    if len(frame) < 4:
        raise ValueError("a frame is at least 4 bytes: address, function, CRC")
    body, received = frame[:-2], frame[-2] | (frame[-1] << 8)
    expected = crc16(body)
    if received != expected:
        raise ValueError("CRC mismatch: frame says 0x%04X, the bytes give 0x%04X"
                         % (received, expected))

    slave, function = frame[0], frame[1]
    result = {
        "slave": slave,
        "function": function,
        "function_name": FUNCTION_NAMES.get(function & 0x7F, "unknown"),
        "bytes": len(frame),
        "crc": "0x%04X" % expected,
    }

    if function & 0x80:
        code = frame[2] if len(frame) > 4 else None
        result["exception"] = {"code": code, "name": EXCEPTIONS.get(code, "unknown")}
        return result

    if function in (1, 2, 3, 4) and len(frame) > 5:
        count = frame[2]
        result["byte_count"] = count
        result["payload_bytes"] = len(frame) - 5
        result["payload_matches_count"] = (count == len(frame) - 5)
        return result

    if function in (5, 6, 15, 16) and len(frame) >= 8:
        result["echoed"] = True
        return result

    return result


def char_time_ms(baud: int, bits: int = 11) -> float:
    """One character on the wire: start + 8 data + parity + stop, 11 bits typical."""
    if baud <= 0:
        raise ValueError("baud must be positive")
    return bits * 1000.0 / baud


def gap_ms(baud: int, bits: int = 11, chars: float = 3.5) -> float:
    """The silence that ends a frame. 3.5 characters per the Modbus spec."""
    return char_time_ms(baud, bits) * chars


def timing(baud: int, bits: int = 11) -> dict:
    one = char_time_ms(baud, bits)
    return {
        "baud": baud,
        "bits_per_char": bits,
        "char_ms": one,
        "gap_ms": one * 3.5,
        "gap_fits_1ms_tick": (one * 3.5) >= 1.0,
        "max_frame_ms_256": one * 256,
        "frames_per_second_8_byte": 1000.0 / (one * 8 + one * 3.5),
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Build, check and time Modbus RTU frames.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", choices=("read", "write"), help="build a request frame")
    group.add_argument("--check", help="validate a frame given as hex bytes")
    group.add_argument("--timing", action="store_true", help="character and gap timing")
    parser.add_argument("--slave", type=lambda s: int(s, 0), default=1)
    parser.add_argument("--function", type=int, default=3)
    parser.add_argument("--start", type=lambda s: int(s, 0), default=0)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--address", type=lambda s: int(s, 0), default=0)
    parser.add_argument("--value", type=lambda s: int(s, 0), default=0)
    parser.add_argument("--baud", type=lambda s: int(s, 0), default=9600)
    parser.add_argument("--bits", type=int, default=11, help="bits per character")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.build == "read":
            frame = build_read(args.slave, args.start, args.count, args.function)
        elif args.build == "write":
            frame = build_write_single(args.slave, args.address, args.value, args.function)
        else:
            frame = None

        if args.timing:
            result = timing(args.baud, args.bits)
            if args.json:
                print(json.dumps(result, indent=2))
                return 0
            print("at %d baud, %d bits per character" % (args.baud, args.bits))
            print("")
            print("  one character   %6.3f ms" % result["char_ms"])
            print("  frame gap       %6.3f ms  (3.5 characters)" % result["gap_ms"])
            print("  256 byte frame  %6.1f ms" % result["max_frame_ms_256"])
            print("  throughput      %6.1f eight-byte transactions per second"
                  % result["frames_per_second_8_byte"])
            print("")
            if not result["gap_fits_1ms_tick"]:
                print("  the gap is below a 1 ms tick: a software timer cannot measure it, "
                      "use the UART idle detection")
            return 0

        if frame is not None:
            parsed = parse_frame(frame)
            parsed["hex"] = " ".join("%02X" % b for b in frame)
            if args.json:
                print(json.dumps(parsed, indent=2))
                return 0
            print("%s" % parsed["hex"])
            print("")
            print("  slave     %d" % parsed["slave"])
            print("  function  %d (%s)" % (parsed["function"], parsed["function_name"]))
            print("  bytes     %d" % parsed["bytes"])
            print("  crc       %s" % parsed["crc"])
            return 0

        raw = bytes(int(token, 16) for token in args.check.replace(",", " ").split())
        parsed = parse_frame(raw)
        if args.json:
            print(json.dumps(parsed, indent=2))
            return 0
        print("valid frame, %d bytes" % parsed["bytes"])
        print("  slave     %d" % parsed["slave"])
        print("  function  %d (%s)" % (parsed["function"], parsed["function_name"]))
        if "exception" in parsed:
            print("  exception %s - %s" % (parsed["exception"]["code"], parsed["exception"]["name"]))
        if "byte_count" in parsed:
            print("  byte count %d, %s" % (parsed["byte_count"],
                                           "matches" if parsed["payload_matches_count"]
                                           else "does NOT match the data"))
        return 0
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
