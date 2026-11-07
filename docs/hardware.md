# Verified on hardware

The pin database is not taken on trust. It was checked against a real module by
flashing a sketch that reports what the chip says about itself.

| Board | Chip | Flash | Toolchain | Result |
|---|---|---|---|---|
| ESP32 DevKit, CP210x bridge (COM6) | ESP32-D0WD-V3 rev 301, 2 cores | 4 MB | Arduino / ESP-IDF 5.5.5 | flashed, booted, serial read back |

## Serial output

```
rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
mode:DIO, clock div:2
=== board facts ===
chip        : ESP32-D0WD-V3 rev 301, 2 core(s)
cpu         : 240 MHz
flash       : 4 MB (4194304 bytes)
sdk         : v5.5.5
free heap   : 331072 bytes
=== end ===
```

## What this confirms for the database

- `data/esp32-pins.json` `esp32` entry is the right profile for this module:
  classic ESP32, valid range 0-39, 4 MB flash, so `GPIO6`-`GPIO11` really are
  the flash pins and the 4 MB partition layouts in
  `skills/esp32-partitions-and-ota/reference/partition-layouts.md` apply.
- `partition_check.py --flash 4MB` is the correct size to pass for this board.
- `331072` bytes of free heap at boot is the budget a TLS connection has to fit
  inside, which is the number `esp32-mqtt-and-cloud` warns about.

## Reproducing

```bash
pio run -t upload --upload-port COM6
python - <<'PY'
import serial, time
port = serial.Serial("COM6", 115200, timeout=1)
port.setDTR(False); port.setRTS(True); time.sleep(0.15)
port.setRTS(False)
start = time.time(); buf = ""
while time.time() - start < 9:
    chunk = port.read(256)
    if chunk: buf += chunk.decode("utf-8", "replace")
print(buf)
PY
```

`pio device monitor` refuses to run with redirected stdin, so a script that
talks to the port directly is the way to capture output in CI or in a tool.
