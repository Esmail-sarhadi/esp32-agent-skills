# Field issue research: recurring ESP32 failure patterns

Research date: 2026-11-07

## Scope and evidence standard

This expansion is based on recurring symptom clusters found in Espressif documentation, public ESP-IDF/Arduino-ESP32/ESPHome issue trackers and troubleshooting searches. Search result frequency is not a verified Google search-volume ranking. Public issue reports are treated as incident evidence for the reporter's exact hardware/software tuple, not as proof of a universal defect or confirmed root cause.

## Observed problem clusters

| Cluster | Recurring user-visible symptom | Engineering response added |
|---|---|---|
| Wi-Fi lifecycle | Authentication loops, disconnect reasons, link-up without IP/DNS, stale sessions | Reason-code forensics, credential recovery, event/IP lifecycle and provisioning recovery |
| Radio coexistence | BLE scan misses, Wi-Fi watchdogs, C6 Wi-Fi/802.15.4 starvation | Version-pinned coexistence regression matrix and long-duration RF soak |
| Power/reset | Brownout on RF or actuator events, ambiguous reset cause, unsafe outputs during reset | Rail transient measurement, reset classification and safe actuator defaults |
| Crash/memory | Guru Meditation, invalid backtrace, stack overflow, heap corruption | ELF-matched symbolication, stack watermark and allocation forensics |
| Storage/update | NVS no-free-pages, flash wear, OTA rollback, image/partition mismatch, power loss | Safe migration, write-rate budget, pending-verify qualification and fault injection |
| Low power | Immediate deep-sleep wake, missed timer wake, Wi-Fi latency after power save | Wake-source electrical review and measured latency/current qualification |
| Serial/fieldbus | Upload timeout, blank logs, UART overflow, RS485 truncation, Modbus timing and map errors | USB/UART path audit, direction timing, frame-gap validation and typed register mapping |
| Network security | TLS failure after sleep, SNI/time mismatch, DNS stale cache, MQTT duplicates | TLS time/SNI diagnostics, resolver lifecycle and idempotent MQTT session recovery |
| Peripheral reliability | I2C bus stuck, PSRAM/DMA capability mismatch, ADC2/Wi-Fi conflict, GPIO strap loading | Bus recovery, capability-aware allocation, target-specific ADC arbitration and boot strap audit |
| Engineering process | Regressions after SDK/controller updates, missing field evidence | Version bisect and minimal crash telemetry record |

## Primary sources consulted

### Espressif documentation
- Fatal errors, panic, watchdog, brownout, stack and heap checks: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/fatal-errors.html
- ESP-IDF error code reference: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/error-codes.html
- Wi-Fi programming guide: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html
- Radio coexistence: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/coexist.html
- NVS: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/nvs_flash.html
- OTA and rollback: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/ota.html
- Sleep modes: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/sleep_modes.html
- UART: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/uart.html
- ESP-Modbus protocol aspects: https://docs.espressif.com/projects/esp-modbus/en/main/esp32/modbus_protocol_aspects.html

### Public issue reports (reporter-specific evidence)
- ESP-IDF #19306: ESP32-C6 Wi-Fi/802.15.4 receive stall reported after BLE idle; workaround is reporter-verified, root-cause mechanism is explicitly a hypothesis: https://github.com/espressif/esp-idf/issues/19306
- ESP-IDF #18838: Wi-Fi/802.15.4 coexistence stuck while a frequency-switch poll appears to spin: https://github.com/espressif/esp-idf/issues/18838
- ESP-IDF #18931: BLE scan behavior regression reported under Wi-Fi coexistence: https://github.com/espressif/esp-idf/issues/18931
- ESP-IDF #6743: Wi-Fi task watchdog under load/coexistence: https://github.com/espressif/esp-idf/issues/6743
- ESP-IDF #18702: Wi-Fi authentication retry loop after AP password change: https://github.com/espressif/esp-idf/issues/18702
- ESP-IDF #13598: Wi-Fi transmit path blocked after a specific BLE scan/software reset sequence on classic ESP32: https://github.com/espressif/esp-idf/issues/13598
- ESPHome #19803: ESP32-S3 deep-sleep timer wake reliability report: https://github.com/esphome/esphome/issues/19803
- ESPHome #9850: immediate wake from configured deep-sleep pin: https://github.com/esphome/esphome/issues/9850
- ESPHome #17180: Modbus RTU device interoperability issue after inter-frame delay change: https://github.com/esphome/esphome/issues/17180
- Arduino-ESP32 #440: classic ESP32 ADC2/Wi-Fi limitation: https://github.com/espressif/arduino-esp32/issues/440
- Arduino-ESP32 troubleshooting: flashing timeout, boot mode, cable and serial path: https://github.com/espressif/arduino-esp32/blob/master/docs/en/troubleshooting.rst

## Interpretation and limits

- The search identifies recurring *problem classes*, not statistically validated query rankings or population incidence.
- Upstream issues can be open, version-specific, board-specific or unresolved. Their workaround must not be copied blindly.
- Skills instruct agents to freeze the target/version tuple, preserve raw evidence, isolate a reproducer, test competing hypotheses and separate host tests from hardware qualification.
- Hardware/RF/power/EMC and safety claims still require the actual board, instruments and applicable standards.
