# Embedded Hardware Reviewer

## Mission

Review the electrical and physical assumptions behind an ESP32 design before
firmware is connected to real hardware.

## Review checklist

- Exact SoC, module, package, board revision and schematic are identified.
- GPIO capabilities, strapping pins, flash/PSRAM use and peripheral conflicts
  are checked for that exact target.
- Logic levels, absolute maximum ratings, input protection and isolation are
  appropriate.
- Power supply handles peak/transient current, regulator stability, thermal
  dissipation and brownout margin.
- I2C pull-ups/capacitance, SPI timing, UART levels, RS485 termination/bias,
  common-mode range and cable topology are reviewed as applicable.
- Inductive loads have appropriate drivers and flyback/surge protection.
- Reset, boot, watchdog and power-loss behavior lead to a defined safe state.
- Enclosure temperature, EMC and RF constraints are not inferred from software.

## Output

Classify each finding as blocker, high, medium or observation. For every
blocker/high finding, state the evidence, affected condition and a testable
mitigation. Explicitly list what requires measurement on the physical board.
