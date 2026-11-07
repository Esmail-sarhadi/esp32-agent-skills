# board-facts

Prints what the chip reports about itself, so the pin profile in
`data/esp32-pins.json` can be checked against a real module.

```bash
cd examples/board-facts
pio run -t upload --upload-port COM6
```

Then read the port. `pio device monitor` refuses to run with a redirected stdin,
so a short script is the reliable way to capture the output:

```python
import serial, time
port = serial.Serial("COM6", 115200, timeout=1)
port.setDTR(False); port.setRTS(True); time.sleep(0.15)   # reset the board
port.setRTS(False)
start = time.time(); buf = ""
while time.time() - start < 9:
    chunk = port.read(256)
    if chunk: buf += chunk.decode("utf-8", "replace")
print(buf)
```

Expected output, captured from an ESP32-D0WD-V3 with 4 MB flash:

```
=== board facts ===
chip        : ESP32-D0WD-V3 rev 301, 2 core(s)
cpu         : 240 MHz
flash       : 4 MB (4194304 bytes)
sdk         : v5.5.5
free heap   : 331072 bytes
=== end ===
```

What to do with it:

- `chip` tells you which entry of `data/esp32-pins.json` applies. If it is not
  `ESP32-D0WD...`, run `pincheck.py --soc esp32s3` or `--soc esp32c3` instead.
- `flash` is the value to pass to `partition_check.py --flash`.
- `free heap` is the budget a TLS connection has to fit inside.
