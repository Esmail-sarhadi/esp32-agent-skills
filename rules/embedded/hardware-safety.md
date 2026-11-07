# Hardware-Sensitive ESP32 Rules

Apply this rule whenever work touches pins, power, clocks, RF, motors, analog
inputs, external buses, flash, boot or enclosure temperature.

- Confirm the exact chip variant and package. A family-level name is not enough
  to infer pin or peripheral availability.
- Treat board schematics and module datasheets as authoritative for board
  wiring; treat the SoC datasheet and errata as authoritative for silicon limits.
- Check strapping pins, flash/PSRAM connections, input-only pins, USB/JTAG use,
  ADC channel restrictions and peripheral matrix constraints for the target.
- Check voltage levels and absolute maximum ratings before connecting external
  signals. ESP32 GPIO is not 5 V tolerant unless the exact device documentation
  explicitly says otherwise.
- For I2C, verify pull-up voltage, bus capacitance, address collisions and
  recovery behavior. For SPI, verify mode, frequency, chip-select timing and
  signal integrity. For UART/RS485, verify transceiver direction, termination,
  biasing, common-mode range and isolation.
- For battery-powered designs, estimate average and peak current, radio bursts,
  regulator transient response, thermal dissipation and battery protection.
- For OTA, verify image compatibility, partition layout, rollback policy,
  signature/hash checks and power-loss behavior.
- For PWM or switching power stages, use hardware dead-time and fault shutdown
  where supported; do not rely on task scheduling for protection.
- State the limits of software-only validation. Electrical safety, EMC, RF
  compliance and thermal margin require appropriate instruments and physical
  tests.
