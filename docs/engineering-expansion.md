# Embedded Engineering Expansion (v1.2.0)

This change adds 100 skills to the existing 101-skill corpus.

## Added domains

- Board/SoC capability, pin multiplexing, flash/PSRAM, memory and DMA budgets
- Power integrity, brownout, battery, sleep and thermal analysis
- Wi-Fi, BLE, ESP-NOW, Ethernet, LoRa and network resilience
- UART, SPI, I2C, TWAI/CANopen, Modbus, RS-485 and OPC UA
- Sensors, camera, audio, display and USB integration
- NVS/filesystem integrity, OTA recovery, secure boot and flash encryption
- Device identity, threat modeling, secret review, SBOM and build provenance
- Protocol conformance/fuzzing, fault injection and HIL test design

## Quality suite

`tests/test_expanded_skill_quality.py` registers four independent unittest
methods for every new skill (frontmatter, engineering sections, safety contract,
validation/evidence). The intended suite size is 400 test cases.

Run the full repository suite with:

```bash
python -m unittest discover -s tests
```

These checks validate package structure and required engineering guidance.
They do not constitute silicon, electrical, RF, EMC, thermal, production
security or hardware-in-loop validation.

## Evidence and safety

Every skill requires exact target and version context, points to official
Espressif documentation and asks the agent to preserve evidence scope. Physical
claims must be checked against the applicable datasheet, errata, schematic and
measurements. An ESP32 is not a safety-rated controller.
