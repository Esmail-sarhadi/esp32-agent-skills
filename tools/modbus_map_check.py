#!/usr/bin/env python3
"""Validate a vendor-neutral Modbus register map CSV.

Required columns:
name,table,address,type,access,scale,unit,description

Supported types: BOOL, U16, I16, U32, I32, U64, I64, F32, F64.
Addresses are zero-based PDU offsets, not 3xxxx/4xxxx display references.
Exit code is 1 when an error is found.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from typing import Dict, List, Tuple

ERROR = "error"
WARN = "warn"
WIDTHS = {"BOOL": 1, "U16": 1, "I16": 1, "U32": 2, "I32": 2,
          "F32": 2, "U64": 4, "I64": 4, "F64": 4}
TABLES = {"holding", "input", "coil", "discrete"}
ACCESS = {"r", "w", "rw"}
REQUIRED = ("name", "table", "address", "type", "access", "scale", "unit", "description")


def parse_map(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        missing = [field for field in REQUIRED if field not in reader.fieldnames]
        if missing:
            raise ValueError("missing required columns: " + ", ".join(missing))
        rows = []
        for line, raw in enumerate(reader, 2):
            row = {key: (raw.get(key) or "").strip() for key in REQUIRED}
            if not any(row.values()):
                continue
            row["line"] = line
            rows.append(row)
    if not rows:
        raise ValueError("register map contains no data rows")
    return rows


def check(rows: List[dict]) -> Tuple[List[dict], int]:
    findings: List[dict] = []
    errors = 0
    occupied: Dict[Tuple[str, int], dict] = {}
    seen_names: Dict[str, dict] = {}

    def add(severity: str, row: dict, message: str) -> None:
        nonlocal errors
        findings.append({"severity": severity, "line": row.get("line"),
                         "name": row.get("name", ""), "message": message})
        if severity == ERROR:
            errors += 1

    for row in rows:
        name = row["name"]
        normalized_name = name.casefold()
        if normalized_name:
            if normalized_name in seen_names:
                add(ERROR, row, "duplicate point name also used on line %d" % seen_names[normalized_name]["line"])
            else:
                seen_names[normalized_name] = row
        table = row["table"].lower()
        dtype = row["type"].upper()
        access = row["access"].lower()
        try:
            address_text = row["address"].strip()
            address = int(address_text, 16) if address_text.lower().startswith("0x") else int(address_text, 10)
        except ValueError:
            add(ERROR, row, "address must be a decimal or 0x-prefixed zero-based offset")
            continue
        if not name:
            add(ERROR, row, "name is required")
        if table not in TABLES:
            add(ERROR, row, "table must be one of holding, input, coil, discrete")
        if dtype not in WIDTHS:
            add(ERROR, row, "unsupported type; use " + ", ".join(sorted(WIDTHS)))
            continue
        if access not in ACCESS:
            add(ERROR, row, "access must be R, W or RW")
        width = WIDTHS[dtype]
        limit = 65536 if table in ("holding", "input") else 65536
        if address < 0 or address + width > limit:
            add(ERROR, row, "address range is outside the 16-bit Modbus address space")
        try:
            scale = float(row["scale"])
            if not math.isfinite(scale) or scale == 0:
                raise ValueError()
        except ValueError:
            add(ERROR, row, "scale must be a finite non-zero number")
        if not row["unit"]:
            add(ERROR, row, "unit is required; use '1' for dimensionless values")
        if not row["description"]:
            add(WARN, row, "description is empty; add source and semantics")
        if table in ("coil", "discrete") and dtype != "BOOL":
            add(ERROR, row, "coil/discrete tables must use BOOL type")
        if table in ("holding", "input") and dtype == "BOOL":
            add(WARN, row, "BOOL in a register table is vendor-specific; document bit semantics")
        if table in TABLES and 0 <= address < limit and address + width <= limit:
            for offset in range(address, address + width):
                key = (table, offset)
                previous = occupied.get(key)
                if previous:
                    add(ERROR, row, "overlaps %s at %s offset %d" %
                        (previous["name"], table, offset))
                else:
                    occupied[key] = row
    return findings, errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, help="register map CSV")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)
    try:
        rows = parse_map(args.file)
        findings, errors = check(rows)
    except (OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"rows": len(rows), "errors": errors, "findings": findings}, indent=2))
    else:
        for item in findings:
            print("%s: line %s [%s]: %s" %
                  (item["severity"], item["line"], item["name"], item["message"]))
        print("%d register(s), %d error(s), %d warning(s)" %
              (len(rows), errors, sum(x["severity"] == WARN for x in findings)))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
