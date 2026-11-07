# Workflow: ESP32 Board Bring-up

1. Identify exact SoC/module, board revision, schematic, flash/PSRAM and USB
   interface.
2. Inspect power rails, reset/boot circuitry and strapping pins before flashing.
3. Confirm the board profile exists in `data/esp32-pins.json`; do not guess
   pin capabilities for an unsupported target.
4. Record framework/toolchain versions and build the smallest known-good image.
5. Validate serial console, reset reason, boot log and basic GPIO without
   attaching hazardous loads.
6. Add peripherals one at a time; check voltage, pull-ups, termination and
   shared-bus conflicts.
7. Run relevant checkers and capture a board-specific baseline.
8. Record measured results, instrument, wiring, ambient conditions and known
   limitations.

Exit criteria: repeatable clean boot, known pin map, verified power baseline,
documented peripheral inventory and reproducible build instructions.
