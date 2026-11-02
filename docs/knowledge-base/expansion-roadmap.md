# Expansion Roadmap: ESP32 Embedded Engineering Knowledge System

## Mission

Grow the repository from a set of promptable skills into a versioned, testable
engineering knowledge system for ESP32 and adjacent embedded/industrial systems.
The system should help an agent choose hardware, design interfaces, implement
firmware, diagnose field faults, verify fixes and prepare production releases.

## Target scale (multi-release, not current counts)

| Asset | Target | Quality gate |
|---|---:|---|
| Task skills | 300–500 | Unique trigger, actionable rules, version boundaries |
| Field-failure cases | 2,000–3,000 | Source, confidence grade, reproduction or explicit gap |
| Regression scenarios | 1,500–2,500 | Deterministic expected result; linked to a case or rule |
| Buildable examples | 300–500 | CI build with pinned toolchain and documented board |
| Protocol/component dossiers | 150–250 | Electrical + protocol + firmware integration |
| Automated checkers | 25–40 | CLI, machine-readable output, unit tests |
| SoC/board profiles | 20–30 | Datasheet-backed pin, power and peripheral constraints |
| Hardware-in-loop suites | 10–20 | Published fixture, wiring, measurements and limits |

Do not inflate counts with thin variants, duplicated skills, generated boilerplate,
or multiple test names for the same assertion. A case can be counted only when
its evidence metadata and acceptance gate are complete.

## Workstreams

### A. Silicon, modules and board profiles
- ESP32, S2, S3, C2, C3, C5, C6, C61, H2, P4 and future families as supported.
- Module-level flash/PSRAM/antenna variants and common development boards.
- GPIO matrix, strapping, USB/JTAG, ADC, touch, DAC, RMT, LEDC, MCPWM, SPI,
  I2C, UART, TWAI, SDMMC and DMA capability matrices.
- Board overlays must never be confused with SoC-level facts.

### B. Industrial communications
- Modbus RTU/TCP, RS232, RS422, RS485, CAN/TWAI, CAN-FD via external
  controllers, Ethernet RMII/SPI, W5500, ENC28J60, EtherCAT gateway boundaries.
- MQTT, OPC UA gateway patterns, HTTP/REST, WebSocket, BLE, ESP-NOW,
  LoRa/LoRaWAN, GNSS/NMEA and proprietary radio links.
- Include isolation, surge protection, grounding, termination, EMC and
  deterministic timing. Protocol knowledge must include the physical layer.

### C. Analog, instrumentation and motion
- 4–20 mA, 0–10 V, bridge sensors, thermocouples, RTD/PT100/PT1000,
  load cells, precision ADCs, DACs, current/voltage monitors and calibration.
- Stepper, servo, BLDC, relays, contactors, solenoids and safety interlocks.
- Include input protection, common-mode range, filtering, sampling, calibration
  traceability and failure-safe output states.

### D. Runtime, reliability and diagnostics
- FreeRTOS scheduling, SMP, watchdogs, stack, heap, PSRAM, DMA, race conditions,
  lock ordering, ISR latency, brownout, reset loops and power transitions.
- Wi-Fi roaming/reconnect, lwIP socket lifecycle, TLS memory, DNS, DHCP,
  captive portals and long-duration soak behavior.
- Crash decoding, core dumps, heap tracing, JTAG, logic analyzer and oscilloscope
  workflows.

### E. Storage, boot and lifecycle
- Partition layouts, secure boot, flash encryption, NVS migration, filesystem
  wear, SD logging, OTA A/B, signed images, rollback, anti-rollback and
  interrupted-update recovery.
- Factory provisioning, unique identity, calibration persistence, RMA and
  decommissioning.

### F. Toolchains and ecosystems
- ESP-IDF, Arduino-ESP32, PlatformIO, ESPHome, Zephyr interoperability,
  CMake, component manager, Kconfig, CI, reproducible builds and SBOM.
- Pin framework APIs to exact release ranges. Never merge examples from
  incompatible Arduino core generations without an explicit adapter.

### G. Validation and safety
- Host unit tests, fuzzing, static analysis, sanitizers where supported,
  protocol simulators, Wokwi, Unity on target, fault injection, HIL, EMC pre-scan,
  thermal/voltage corner testing and production burn-in.
- Document limits: software tests cannot prove isolation, surge immunity,
  thermal margins, radio compliance or safety certification.

## Delivery phases

| Phase | Deliverables | Exit condition |
|---|---|---|
| 0. Baseline | Inventory, evidence policy, branch/CI baseline | Existing claims reconciled |
| 1. Foundation | Knowledge taxonomy, templates, 33 new skills, first incident corpus | Skills shape tests and links pass |
| 2. Industrial core | 50–80 skills, 150 cases, 50 examples, 5 checkers | Protocol and hardware review |
| 3. Broad coverage | 150 skills, 500 cases, 300 scenarios | Versioned matrix and CI gates |
| 4. Scale | 300–500 skills, 2k–3k cases, 1.5k–2.5k tests | Deduplication and evidence audit |
| 5. Production | HIL fixtures, signed OTA, board profiles, release process | Reproducible release and field feedback loop |

## Release gates

- No skill without a unique task trigger and at least three meaningful sections.
- No incident marked solved without a credible source and a stated verification level.
- No universal pin/peripheral statement without a specific SoC/module boundary.
- No industrial interface guide without electrical limits and protection discussion.
- No example counted as buildable until CI compiles it with a pinned platform.
- No test counted as hardware verification unless it ran on the named hardware.
- Keep open bugs visible; never convert an open GitHub issue into a solved recipe.

## Next backlog

1. Add per-family capability data for C6/H2/P4 and board overlays.
2. Build reusable incident schema and search index.
3. Add Modbus TCP, RS232/RS422, 4–20 mA, RTD, W5500 and CAN-FD skills.
4. Add protocol simulators and fuzz harnesses.
5. Add CI build matrix for Arduino core 2.x/3.x and supported ESP-IDF releases.
6. Create HIL plans for power loss, brownout, bus contention, noisy links and OTA interruption.
