# Field Failure Casebook — Initial Research Set

This is a curated seed set, not a claim that every issue is independently
reproduced. Grades and statuses are deliberately conservative.

## FF-0001 — RS485 direction-control latency
- **Grade:** B; **status:** reported workaround / hardware redesign.
- **Scope:** ESP-IDF UART RS485 direction control; exact board and release must be captured per reproduction.
- **Symptom:** DE/RTS transition arrives too late and truncates or collides with a frame.
- **Finding:** ISR scheduling and flash-resident ISR latency can affect software-controlled direction timing.
- **Candidate mitigations:** measure DE against TX with a logic analyzer; evaluate IRAM ISR configuration where supported; use UART HAL/custom driver only with maintenance cost understood; prefer hardware auto-direction when timing margin is inadequate.
- **Do not assume:** enabling an IRAM option universally fixes every UART/SoC combination.
- **Source:** https://github.com/espressif/esp-idf/issues/15987

## FF-0002 — UART pins remain claimed after driver uninstall
- **Grade:** A/B; **status:** upstream fix reported for a specific IDF branch.
- **Scope:** ESP-IDF UART peripheral teardown followed by TWAI reuse of the same GPIOs.
- **Symptom:** second peripheral cannot reliably take over pins after UART uninstall.
- **Finding:** driver uninstall did not fully restore GPIO configuration in the affected version.
- **Mitigation:** use the documented release containing the upstream correction; on affected versions, explicitly reset the GPIOs after uninstall and verify pin matrix state before reassigning.
- **Regression:** initialize UART, uninstall, reset pins, initialize TWAI; verify both TX/RX and CAN signals with a logic analyzer.
- **Source:** https://github.com/espressif/esp-idf/issues/16990

## FF-0003 — RS485 half-duplex echo disappears
- **Grade:** B; **status:** version-specific behavior under investigation.
- **Scope:** ESP-IDF UART RS485 half-duplex and collision-detect modes; issue reported on IDF 6.0.1.
- **Symptom:** bytes transmitted by the local node are not available as RX echo.
- **Finding:** half-duplex RTS handling and RX FIFO reset around TX_DONE affect echo visibility.
- **Mitigation:** choose the intended mode explicitly; test `rs485tx_rx_en`, DTR/hardware direction options and collision-detect semantics on the exact release.
- **Do not assume:** loopback echo is guaranteed by every half-duplex mode.
- **Source:** https://github.com/espressif/esp-idf/issues/18712

## FF-0004 — ADC2 reads fail while Wi-Fi is active
- **Grade:** A for classic ESP32; **status:** documented silicon resource conflict.
- **Scope:** classic ESP32 ADC2; do not generalize pin numbers or behavior to all ESP32 families.
- **Symptom:** MQ/sensor ADC reads work without Wi-Fi and fail or return unusable values when Wi-Fi starts.
- **Finding:** ADC2 is shared with Wi-Fi on the classic target.
- **Mitigation:** use an ADC1-capable input on the exact module, or an external ADC; verify attenuation, range, calibration and input impedance.
- **Source:** https://stackoverflow.com/questions/74082200/mq-sensors-giving-0-value-when-using-wifi-h-esp32-but-works-fine-without-it

## FF-0005 — Wi-Fi startup triggers brownout after deep sleep
- **Grade:** B; **status:** common field pattern, root cause must be measured.
- **Symptom:** board wakes and runs, then brownout appears when radio transmission begins.
- **Likely causes:** supply transient response, cable/connector resistance, regulator headroom, battery impedance or peripheral inrush.
- **Diagnostic:** scope 3V3 at the module during radio startup; measure at the module pins, not only at the regulator; compare with peripherals disconnected.
- **Mitigation:** power source and regulator sized for peak current, low-impedance routing, local decoupling per reference design and controlled peripheral startup.
- **Unsafe workaround:** disabling brownout detection.
- **Source:** https://stackoverflow.com/questions/65762611/esp32-why-wifi-connection-causes-brownout-detector-was-triggered-after-deep-sl

## FF-0006 — HTTPClient heap appears not to return
- **Grade:** C; **status:** diagnostic caution, not a confirmed universal leak.
- **Scope:** Arduino-ESP32 HTTPClient/lwIP; behavior varies by core and IDF version.
- **Symptom:** free heap decreases after requests and later appears to recover.
- **Finding:** TCP TIME_WAIT, socket buffers, allocator fragmentation and internal-vs-PSRAM accounting can resemble a leak.
- **Diagnostic:** log free heap and largest free block by capability; run controlled request/idle cycles; compare after connection close and sufficient quiet time; capture heap trace before asserting leak.
- **Source:** https://github.com/espressif/arduino-esp32/issues/8804

## FF-0007 — WiFiClientSecure suspected leak on failed connection
- **Grade:** C; **status:** unverified report.
- **Symptom:** heap loss suspected after repeated TLS connection failures.
- **Finding:** issue discussion proposes cleanup of mbedTLS certificate/key state, but the report is not proof of a general leak or universal patch.
- **Action:** reproduce on the exact Arduino core/IDF version; measure internal heap and largest block; test success and failure paths; inspect cleanup ownership.
- **Source:** https://github.com/espressif/arduino-esp32/issues/3808

## FF-0008 — Repeated Wi-Fi cycles reported to reduce heap
- **Grade:** D; **status:** open/unresolved report.
- **Symptom:** heap decreases across connect/disconnect cycles; backtrace points into lwIP timer paths.
- **Action:** retain as an investigation lead only. Capture exact core, IDF, configuration, heap capability metrics and a minimal reproducer; do not call it solved.
- **Source:** https://github.com/espressif/arduino-esp32/issues/10664

## FF-0009 — Task watchdog caused by a busy task
- **Grade:** B; **status:** recurring pattern with task-specific diagnosis.
- **Symptom:** task watchdog triggers under loops, WebSocket load or callbacks.
- **Finding:** a high-priority task can starve idle/task scheduling when it spins or blocks incorrectly.
- **Mitigation:** use bounded work, queues, `vTaskDelayUntil()` for periodic jobs, yield where appropriate, and keep callbacks short. Check task priority and affinity before changing watchdog timeout.
- **Important:** one RTOS tick is not necessarily one millisecond.
- **Sources:** https://stackoverflow.com/questions/79114861/embedded-esp32-freertos-task-watchdog-got-triggered ; https://stackoverflow.com/questions/78614192/esp32-task-watchdog-triggered

## FF-0010 — W5500 network stack crash after DHCP
- **Grade:** D; **status:** community report, unresolved.
- **Scope:** ESP32-C6 + W5500 + socket.io report.
- **Symptom:** DHCP succeeds, then socket activity faults in tcpip/lwIP mailbox path.
- **Action:** distinguish SPI Ethernet driver from native Wi-Fi/lwIP ownership; record driver version, socket API, task context and mailbox configuration; reproduce with a minimal TCP client before adding socket.io.
- **Source:** https://www.reddit.com/r/esp32/comments/1icb73w/

## FF-0011 — RS485 noise and ghost timeouts
- **Grade:** B/C; **status:** field diagnosis pattern; installation-specific.
- **Symptom:** intermittent Modbus RTU timeouts or corrupted frames in multi-node installations.
- **Checks:** termination only at the two physical bus ends; daisy-chain topology; unique slave IDs; twisted pair; reference conductor and common-mode limits; transceiver loading; shield/PE policy; isolation where ground potential differs.
- **Important:** A/B labels are not consistently assigned across vendors. Confirm polarity from the transceiver datasheet or scope differential voltage.
- **Sources:** https://electronics.stackexchange.com/questions/12624/rs485-noise-problems-signal-ground-common-ground-isolation ; https://www.reddit.com/r/embedded/comments/1t2qtqw/rs485modbus_rtu_ghost_timeouts_losing_my_mind_here/

## FF-0012 — I2C bus stuck low / peripheral absent at boot
- **Grade:** A for recovery mechanisms documented in driver; **status:** target-specific validation required.
- **Symptom:** SDA or SCL remains low after peripheral power loss or interrupted transaction.
- **Finding:** I2C master drivers may include bus-clear/recovery behavior, but the exact API and behavior vary by IDF generation.
- **Mitigation:** use supported bus recovery, bounded transaction timeout, power sequencing and device probe; do not wait forever for a device that may be absent.
- **Regression:** hold SDA low, power-cycle slave independently and verify bounded recovery.
- **Sources:** https://github.com/espressif/esp-idf/blob/master/components/driver/i2c/i2c.c ; https://github.com/espressif/esp-idf/issues/18713

## FF-0013 — OTA boot loop from flashing the wrong image at the wrong offset
- **Grade:** C; **status:** project-specific report.
- **Symptom:** board boot loops after a firmware image is flashed manually.
- **Finding:** a factory/onboarding image and an OTA application image may have different intended offsets and partition assumptions.
- **Mitigation:** inspect the exact partition table and image type; use the project's documented factory flash command; erase only when data loss is acceptable; verify bootloader, partition table and app offsets as a set.
- **Do not generalize:** never prescribe 0x0 or any other offset without the board's flash layout.
- **Source:** https://www.reddit.com/r/esp32/comments/1uec1h8/esp32_stuck_in_a_boot_loop/

## FF-0014 — PlatformIO serial monitor appears blank
- **Grade:** B; **status:** configuration-specific workaround.
- **Symptom:** firmware runs but monitor shows no output or board resets when monitor opens.
- **Checks:** baud rate, RTS/DTR auto-control, native USB CDC configuration, selected upload/monitor port and USB-UART bridge.
- **Reported configuration:** `monitor_speed=115200`, `monitor_rts=0`, `monitor_dtr=0`; native USB targets may require USB mode/CDC-on-boot flags appropriate to the board and framework.
- **Source:** https://community.platformio.org/t/solved-esp32-serial-monitor-not-working/2858

## FF-0015 — LoRa board interrupt watchdog panic
- **Grade:** C; **status:** report-based diagnostic pattern.
- **Symptom:** interrupt watchdog panic during LoRa operation.
- **Likely class:** ISR takes too long, blocks, allocates, logs or performs protocol work instead of deferring it.
- **Mitigation:** keep ISR minimal; capture timestamp/status and notify a task; inspect decoded backtrace and test a minimal radio receive sketch.
- **Source:** https://stackoverflow.com/questions/77432728/lora-esp32-v2-board-core-1-paniced

## FF-0016 — RS485 UART ISR timing and IRAM placement
- **Grade:** B; **status:** issue-specific mitigation, hardware validation required.
- **Symptom:** direction timing changes under flash/cache/interrupt load.
- **Action:** measure DE, TX and RX simultaneously; check ISR placement and interrupt priority; validate IRAM-safe configuration on the exact SoC; consider hardware auto-direction if deterministic timing cannot be guaranteed.
- **Source:** https://github.com/espressif/esp-idf/issues/15987

## FF-0017 — Heap integrity corruption
- **Grade:** A; **status:** official diagnostic method.
- **Symptom:** crash in allocator or failure far from the original invalid write.
- **Mitigation:** enable heap poisoning/integrity checks, add `heap_caps_check_integrity_all()` around suspected operations, use heap tracing and JTAG watchpoints when available.
- **Caution:** diagnostic options change timing and memory use; reproduce with production configuration after fixing.
- **Source:** https://github.com/espressif/esp-idf/blob/master/docs/en/api-reference/system/heap_debug.rst

## FF-0018 — Panic, stack overflow and watchdog classification
- **Grade:** A; **status:** official diagnostic guidance.
- **Symptom:** reboot with panic text that is mistaken for a generic crash.
- **Mitigation:** preserve full boot log and ELF; decode backtrace against the exact ELF; distinguish interrupt/task watchdog, brownout, stack canary and memory access exceptions before changing code.
- **Source:** https://github.com/espressif/esp-idf/blob/master/docs/en/api-guides/fatal-errors.rst

## FF-0019 — I2C LCD initialization blocks forever when panel is absent
- **Grade:** A; **status:** upstream response documents a bounded-timeout correction.
- **Scope:** ESP-IDF 6, ESP32-S3 report, I2C LCD panel IO.
- **Symptom:** `esp_lcd_panel_init()` never returns when the panel is missing or the I2C transaction cannot complete.
- **Root cause:** the I2C LCD panel IO used an infinite transaction timeout by default.
- **Fix:** configure a positive `transaction_timeout_ms` in `esp_lcd_panel_io_i2c_config_t`; optionally probe the expected address first with the supported I2C master probe API. A probe is not a substitute for a timeout on the actual transaction.
- **Regression:** boot with panel connected, disconnected, SDA held low and panel power removed; each case must return within the configured bound and expose a useful error.
- **Source:** https://github.com/espressif/esp-idf/issues/18713

## FF-0020 — I2C master timeout race can dereference a null read buffer
- **Grade:** C; **status:** issue closed internally, public resolution unavailable.
- **Scope:** ESP-IDF development revision based on v5.4, classic ESP32-D0WD.
- **Symptom:** a timeout and ISR interleaving can lead to a null pointer read in the I2C ISR.
- **Reported mechanism:** the reporter identified a window where transaction indices are cleared before status is changed to timeout; the ISR can still take the READ branch and access an unallocated operation buffer.
- **Handling:** do not apply a copied source patch without reviewing the exact upstream revision. Check release notes and current driver source for the target release; preserve a minimal timeout stress reproducer and backtrace.
- **Regression:** repeatedly trigger short I2C timeouts while varying task/interrupt timing; require no panic, no stale transaction state and deterministic error return.
- **Source:** https://github.com/espressif/esp-idf/issues/15444

## FF-0021 — HTTPClient socket exhaustion after repeated requests in a FreeRTOS task
- **Grade:** B; **status:** maintainer stated the disconnect issue was fixed in Arduino-ESP32 3.0.0; separate heap observations need independent interpretation.
- **Scope:** Arduino-ESP32 2.0.14 report on ESP32 / ESP32-MINI-1 using HTTPClient in a task.
- **Symptom:** repeated requests eventually fail with socket error 105 although earlier requests succeed.
- **Root cause and fix:** the report identified a disconnect path that did not reliably stop the underlying client socket in a particular disconnected state. A maintainer stated this was fixed in core 3.0.0. Use a current supported core and verify socket reclamation in the application's exact lifecycle.
- **Important distinction:** the reporter also observed heap reduction per request; the socket fix does not by itself prove that every observed heap change was the same defect or that all memory was leaked.
- **Regression:** run hundreds of task-based requests with connection reuse both enabled and disabled; record socket failures, internal free heap and largest block after an idle reclamation interval.
- **Sources:** https://github.com/espressif/arduino-esp32/issues/8804

## FF-0022 — Repeated Wi-Fi connect/disconnect reports heap loss on Arduino core
- **Grade:** C; **status:** issue closed for lack of follow-up; not a universal fix confirmation.
- **Scope:** ESP32-S3 report with Arduino-ESP32 3.0.7 and 3.1.0-RC1; a Wokwi reproducer was supplied.
- **Symptom:** repeated station connect/disconnect cycles appeared to reduce free heap.
- **Evidence:** a commenter reported that an ESP-IDF-only variant did not show the same behavior, suggesting an Arduino network-layer lifecycle issue in the tested versions. Later comments requested testing newer core versions; the issue was closed after no further feedback, with a maintainer noting no leak in core 3.2.0.
- **Handling:** test the exact release and reproducer before assigning root cause. Measure internal heap and largest block, wait for TCP cleanup, and compare Arduino and ESP-IDF baselines.
- **Regression:** run repeated connect/disconnect cycles on the same board and AP; include an idle wait and assert memory reaches a stable plateau rather than assuming every immediate heap dip is a leak.
- **Source:** https://github.com/espressif/arduino-esp32/issues/10664

## FF-0023 — W5500 Matter device fails to reconnect after a long power-off interval
- **Grade:** D; **status:** closed as an older-version report without a published technical resolution.
- **Scope:** ESP32-WROOM-32UE, SPI W5500 and Arduino Matter report.
- **Symptom:** commissioning succeeds and short power cycles recover, but after a longer outage the device does not reappear in Home Assistant without recommissioning.
- **Handling:** do not assume the W5500 silicon is defective or that recommissioning is the correct recovery. Capture Ethernet link, DHCP lease, IP address, Matter fabric/node identity, endpoint state and reconnect logs across short and long outages. Compare cold boot with link flap and router restart.
- **Regression:** repeat power-off durations around the failure boundary and verify the same commissioned node reconnects without fabric reset.
- **Source:** https://github.com/espressif/arduino-esp32/issues/11621

## Casebook maintenance

New reports must use the template in `templates/field-failure.md`. Add cases
only after checking for duplicates by symptom, root cause and affected versions.
Open reports and closed issues without a public technical resolution remain
unresolved or anecdotal. This casebook is a starting point, not a substitute
for reading the linked upstream discussion.
