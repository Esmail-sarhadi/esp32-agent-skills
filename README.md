# ESP32 Agent Skills

**Two hundred and one skills and ten checkers for ESP32 and industrial embedded engineering, with a multi-harness agent toolkit.**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](tools/pincheck.py)
[![CI](https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/workflows/test.yml/badge.svg)](https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/workflows/test.yml)

**[Read this on a page instead of a README →](https://esmail-sarhadi.github.io/esp32-agent-skills/)**

![Agent Skill ESP32: build, connect, automate](docs/assets/banner.jpg)

---

## Watch it catch one

Same command twice: the first run exits 1 on a pin wired to the flash, the second
exits 0 after the pin is moved. The text is the real output of those two runs,
replayed line by line; the frame around it is drawn, not a screen recording.

![pincheck catching GPIO6, then passing GPIO25](docs/assets/demo.gif)

Swap `6` for `25` and the same command goes from `1 error(s) ... exit 1` to
`0 error(s) ... exit 0`. Nothing else changed.

## The problem

Ask any coding agent for an ESP32 sketch and you get something that compiles.
Then you flash it and one of four things happens:

| What the agent wrote | What happens on hardware |
|---|---|
| `#define LED 6` | `GPIO6` is wired to the SPI flash. The module never boots again. |
| `#define RELAY 34` | `GPIO34` is input-only. The relay never switches, and there is no error. |
| `#define RELAY 12` | `GPIO12` is a strapping pin. HIGH at reset selects 1.8 V flash and the board stays dark. |
| `analogRead(2)` + Wi-Fi | `GPIO2` is on ADC2. The reading is garbage as soon as the radio is on. |

None of these are logic errors, so no compiler and no unit test will catch them.
They live in the pin map, and the pin map is exactly what an agent invents from
memory.

This repository gives the agent that memory, and gives you a checker that
verifies the result in one command.

![Two readings of the same board: what the agent assumes, and what the silicon does](docs/assets/split.jpg)

## Expanded engineering coverage

The 100-skill expansion adds focused playbooks for SoC/board capability and pinmux planning, flash/PSRAM/stack/heap budgets, power and sleep analysis, Wi-Fi/BLE/radio reliability, Ethernet and industrial buses, sensor and display pipelines, OTA/security lifecycle, SBOM and reproducible builds, protocol fuzzing, fault injection and HIL fixture design.

Each new skill requires exact target/version context, evidence-backed review, a validation matrix and explicit hardware-only limitations. The expansion quality suite adds 400 independent unittest cases (four checks per skill) for frontmatter, required engineering sections, safety guardrails, and validation/evidence requirements:

```bash
python -m unittest tests.test_expanded_skill_quality
```

These tests validate skill-package quality; they do not claim that physical hardware behavior has been tested.

## Quickstart

```bash
git clone https://github.com/Esmail-sarhadi/esp32-agent-skills.git
cd esp32-agent-skills

python tools/pincheck.py --soc esp32 --assign "12=relay1,34=button,6=status_led"
```

```
ESP32 (classic, WROOM-32 / WROVER) - 3 pin(s) checked

  GPIO6   ERROR  status_led     GPIO6 is connected to the SPI flash, using it bricks the module
  GPIO12  WARN   relay1         GPIO12 is a strapping pin and must be LOW at boot on 3.3 V flash
                                modules, HIGH selects 1.8 V and the board will not boot; make sure
                                'relay1' cannot hold it there at reset
  GPIO34  WARN   button         GPIO34 is input-only: it cannot drive an output and has no internal
                                pull-up or pull-down, add an external resistor for 'button'
  GPIO12  INFO   relay1         GPIO12 is on ADC2, analogRead() returns garbage while Wi-Fi is active

  1 error(s), 2 warning(s), 1 note(s)
```

Exit code is `1` when there is at least one error, so it drops straight into CI or
a pre-flash hook. `--json` gives the same findings as machine-readable output.

Check a whole pin map from a file instead:

```bash
python tools/pincheck.py --soc esp32 --file examples/pinmap.txt
```

Check the partition table before you flash it:

```bash
python tools/partition_check.py --file examples/partitions-ota-4mb.csv --flash 4MB --ota
```

```
NAME           TYPE   SUBTYPE    OFFSET     SIZE
nvs            data   nvs        0x9000     20KB
otadata        data   ota        0xE000     8KB
app0           app    ota_0      0x10000    1280KB
app1           app    ota_1      0x150000   1280KB
spiffs         data   spiffs     0x290000   1408KB
coredump       data   coredump   0x3F0000   64KB

  INFO  4060KB of 4MB used (99.1%), 36KB free
```

And the one that matters before a battery-powered build:

```bash
python tools/power_budget.py --battery 3000 --wakes-per-hour 12 --wake-ms 2000
```

```
  duty cycle      0.67%
  average current 0.677 mA
  battery life    184.7 days (4433.9 hours)

  where the charge goes
    idle      0.467 mA   69.0%
    tx        0.200 mA   29.6%
    sleep     0.010 mA    1.5%

  dominant term: idle (69.0%), fix that one first
```

That last line is the point of the tool: it tells you which number to attack
instead of letting you guess.

## Install as an agent skill

The `skills/` directory follows the Agent Skills layout (`SKILL.md` with `name`
and `description` frontmatter), so the agent loads a skill only when the task
actually touches pins or power.

**Claude Code, as a plugin**

```bash
/plugin marketplace add Esmail-sarhadi/esp32-agent-skills
/plugin install esp32-agent-skills
```

The repository ships `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`,
so the skills arrive as a managed plugin instead of a directory you keep in sync by hand.

**Install into multiple harnesses**

```bash
./install.sh --harness claude       # ~/.claude/skills
./install.sh --harness codex        # ~/.agents/skills
./install.sh --harness opencode     # ~/.config/opencode/skills
./install.sh --harness all          # Claude + Codex + OpenCode
./install.sh --harness all --dry-run
```

PowerShell equivalents: `./install.ps1 -Harness codex` and
`./install.ps1 -Harness all -DryRun`. Both installers are idempotent and leave
existing skill folders untouched unless `--force` / `-Force` is supplied.
See [harnesses/README.md](harnesses/README.md) for supported locations and
capability boundaries.

**Rules, contexts and specialist agents**

- [Rules](rules/) provide short always-relevant engineering guardrails.
- [Contexts](contexts/embedded-engineering.md) explain how to use the knowledge base.
- [Specialist agent roles](agents/README.md) cover architecture, implementation,
  hardware review, validation, field-failure investigation and security.
- [Reusable workflows](workflows/) cover board bring-up, peripheral integration,
  field-failure triage and OTA release readiness.

`AGENTS.md` remains the repository entry point. Cursor has a native project rule
at `.cursor/rules/esp32-domain.mdc`; Gemini CLI has `GEMINI.md`. OpenCode and
Codex installation details are documented in the harness matrix.

**Any agent with shell access**

Let it call the checker directly — that is the whole point of shipping a binary
next to the prose:

```bash
python tools/pincheck.py --soc esp32 --assign "$(cat pinmap.txt)"
```

## What is inside

### Skills

| Skill | What it stops |
|---|---|
| `esp32-pin-safety` | Flash pins, input-only pins, strapping pins, ADC2 with Wi-Fi. |
| `esp32-power-and-boot` | Brownout, boot strap states, deep-sleep leakage — the "random reset" triage. |
| `esp32-i2c-bus` | Missing pull-ups, address conflicts, a bus that hangs mid-transfer. |
| `esp32-partitions-and-ota` | Misaligned app slots, overlapping regions, an OTA that silently rolls back. |
| `esp32-freertos` | Watchdog resets, stack overflow, ISR rules, shared data without a lock. |
| `esp32-modbus-rs485` | DE-pin timing, the 3.5 character gap, the CRC, the 40001 off-by-one. |
| `esp32-addressable-leds` | Power sizing, the 3.3 V data problem, GRB vs RGBW, refresh budget, flicker under Wi-Fi. |
| `esp32-gaming-rgb` | The OpenRGB SDK wire format, SignalRGB's real options, and what latency Wi-Fi cannot do. |
| `esp32-debugging` | Reading a panic dump, the exception decoder filter, core dumps, and telling a crash from a watchdog from a brownout. |
| `esp32-wifi-reliability` | Reconnect storms, power save as a latency setting, AP+STA, and what RSSI actually means. |
| `esp32-mqtt-and-cloud` | The 256 byte buffer that truncates payloads, keepalive and last will, TLS memory, why QoS 0 loses data. |
| `esp32-adc-and-sensors` | ADC1 vs ADC2, attenuation and the compressed top of the range, calibration, source impedance, averaging. |
| `esp32-pwm-and-timing` | LEDC's frequency/resolution trade-off, duty as a count not a percent, servo timing, the core 3.x API change. |
| `esp32-ble-gatt` | Connection parameters and the timeout inequality, MTU and the 20-byte default, notify vs indicate, and the bond that lives on the phone. |
| `esp32-memory-and-heap` | Internal SRAM vs PSRAM, `MALLOC_CAP_DMA`, the largest free block as the number that matters, stack sizing in bytes vs words. |
| `esp32-storage-and-filesystem` | NVS vs LittleFS vs FAT, commit and rename as the only atomic operations, wear, and mount failure as a decision. |
| `esp32-spi-and-devices` | Bus then device, one initialisation per host, chip select ownership, and why 40 MHz works on the bench and not in the box. |
| `esp32-can-twai` | Which chips have TWAI at all, the transceiver that is not optional, termination at both ends, and bus-off recovery. |
| `esp32-audio-i2s` | Master/slave roles, MCLK, DMA buffer counts, underruns as clicks, and why the pitch is wrong. |
| `esp32-camera-pipeline` | OV2640 limits, PSRAM framebuffers, init once with no de-init, and the camera plus Wi-Fi brownout. |
| `esp32-http-server` | Wildcard matching off by default, handler limits, never blocking the server task, and chunked responses. |
| `esp32-time-and-rtc` | SNTP is asynchronous, TZ strings with DST rules, RTC drift across sleep, and certificates that depend on the clock. |
| `esp32-security-and-provisioning` | Secure boot, flash encryption and NVS keys in the order that does not brick the board, and what a factory reset really erases. |
| `esp32-testing-and-ci` | Host tests, on-target Unity, size budgets and a build matrix that covers the chips the README claims. |
| `esp32-hardware-bringup` | Measure the rail before the firmware: current, strapping levels, the blink-first order, and reading a boot loop. |
| `esp32-field-gotchas` | A hundred and sixty failures people actually hit — brownout, dead I2C, garbled UART, watchdog resets, OTA that writes and boots nothing, cameras that brown out, ISRs that fault — indexed by symptom, each linked to the Stack Overflow thread where the cause was found. |
| `esp32-ethernet` | RMII clock on a strapping pin, the PHY address, and a link that never comes up. |
| `esp32-esp-now` | The channel that moves under you, the 250-byte frame limit, six encrypted peers, and LR that only one end speaks. |
| `esp32-lora-and-lorawan` | DIO0 that never fires, airtime against a 1 % duty cycle, and joins that fail after a reset. |
| `esp32-gps-and-nmea` | Baud, cold starts, valid time with no fix, and the checksum nobody validates. |
| `esp32-uart-and-serial` | UART0 and the bootloader, the 128-byte FIFO, DE timing on RS485, and logs that corrupt a protocol. |
| `esp32-watchdogs-and-timers` | Which of the three watchdogs reset you, and why feeding it from the wrong task tells you nothing. |
| `esp32-lvgl-and-displays` | SPI vs RGB panels, DMA buffers, tearing from the flush callback, and framebuffers in PSRAM. |
| `esp32-touch-and-input` | Baseline drift, water on the pad, no pull-ups on GPIO34-39, and strapping pins behind a button. |
| `esp32-actuators-and-relays` | Flyback diodes, inrush, SSR leakage, and servos on the wrong rail. |
| `esp32-multicore-and-ipc` | Core 0 belongs to the radio, priorities are absolute, and an ISR is not a task. |
| `esp32-nvs-and-config` | The 20 kB that fills up, encryption off by default, and a schema that needs migrating. |
| `esp32-json-and-payloads` | Capacity, streaming instead of String, float precision, and the cJSON leak on an early return. |
| `esp32-tls-and-certificates` | 40 kB per handshake, cert bundles, SNI, and a clock stuck in 1970. |
| `esp32-build-and-sdkconfig` | sdkconfig.defaults that is ignored, PlatformIO flags that are not Kconfig, and a binary that no longer fits. |
| `esp32-factory-test-and-calibration` | A rig that decides in seconds, per-unit identity, and calibration that survives a reflash. |
| `esp32-batch-provisioning` | SoftAP vs BLE, QR payloads phones reject, and batch flashing with unique serials. |
| `esp32-ota-server` | Version comparison, staged rollout, and a rollback that needs a trigger. |
| `esp32-battery-and-charging` | The charger is not a power path, the divider drains the cell, and the transmit peak browns out. |
| `esp32-sd-card-and-logging` | Mount failures, a power cut mid-write, and writes that block the control loop. |
| `esp32-emc-and-enclosure` | Antenna keepout, cables as antennas, and heat in a sealed box. |
| `esp32-w5500-ethernet` | SPI timing, socket exhaustion, link loss, and coexistence with Wi-Fi. |
| `esp32-ethernet-rmii-phy` | The 50 MHz clock on a strapping pin, PHY address straps, and link vs IP-layer diagnostics. |
| `esp32-modbus-tcp` | MBAP framing, transaction ids, and the session failures that look like wiring. |
| `esp32-can-fd-gateway` | TWAI vs an external CAN-FD controller, bus-off recovery, and isolation on a gateway. |
| `esp32-rs232-rs422` | MAX3232 charge pumps, full-duplex wiring, and a cable length that actually works. |
| `esp32-industrial-analog-io` | 4-20 mA shunts, 0-10 V dividers, and protection against a miswired field wire. |
| `esp32-pt100-pt1000-rtd` | Lead resistance, MAX31865 wiring, and calibration that survives a cable change. |
| `esp32-power-integrity` | Brownout at transmit, relay inrush, regulator heating, and the capacitor that fixes it. |
| `esp32-industrial-gateway-architecture` | Which protocol terminates where, and what a gateway must not pretend to be. |
| `esp32-secure-ota-production` | Signed images, anti-rollback, and a fleet rollout that can be stopped. |
| `esp32-serial-field-diagnostics` | Framing errors, FIFO overruns, boot-log interference and RS485 timeouts. |
| `esp32-i2c-recovery` | SDA stuck low, clock-pulse recovery, and a peripheral that powers off on its own. |
| `esp32-fault-injection-hil` | Fault injection, soak tests, and a rig that fails a device for the right reason. |
| `esp32-enc28j60-ethernet` | The 8 KB buffer, no auto-negotiation, and why a large transfer stalls while ping works. |
| `esp32-rs485-isolated-transceivers` | MAX3485 vs ISO3082 vs ADM2587E, termination, fail-safe bias, and what a TVS can actually clamp. |
| `esp32-sx127x-lora` | Register mode, DIO0 mapping, and the seven settings that must match on both ends. |
| `esp32-nrf24l01` | The 10 uF capacitor, pipe addresses, 32-byte payloads, and coexistence with Wi-Fi. |
| `esp32-rfm69-subghz` | W vs HW variants, the sync word, the FIFO threshold, and AES that decrypts to noise. |
| `esp32-ads1115-external-adc` | PGA ranges, the absolute-input trap, and single-ended vs differential. |
| `esp32-ads1256-precision-adc` | Reference, the 7.68 MHz clock, DRDY, and why 24 bits delivers 18. |
| `esp32-mcp4725-analog-output` | A DAC is not an analog output: buffer, gain, protection, and the EEPROM that remembers. |
| `esp32-4-20ma-transmitter` | The live zero, loop compliance, XTR116-class drivers, and isolation. |
| `esp32-vfd-modbus-control` | Control words, reference scaling, per-vendor register maps, and a stop that does not depend on Modbus. |
| `esp32-poe-power` | 802.3af/at classes, the signature resistor, and the isolation barrier. |
| `esp32-surge-and-tvs-protection` | Standoff vs clamping voltage, series impedance, and what a TVS cannot do. |
| `esp32-isolated-digital-input` | 24 V through an opto: resistor, reverse diode, wetting current, debounce. |
| `esp32-din-rail-power` | The 24 V rail, reverse protection, hold-up capacitance, and the dissipation arithmetic. |
| `esp32-energy-meter-modbus` | SDM120-class meters, float word order, and range validation in the parser. |
| `esp32-iec-60870-5-104` | APCI frame types, k/w windows, t1 to t3, and the ASDU fields a master will reject. |
| `esp32-snmp-agent` | GET and GETNEXT, BER long lengths, v3 engine state, and traps that survive a lost packet. |
| `esp32-sparkplug-b-mqtt` | Topic namespace, protobuf payloads, aliases, seq and bdSeq. |
| `esp32-canopen-basics` | Node-id COB-IDs, the pre-operational state, SDO vs PDO, heartbeat. |
| `esp32-modbus-rtu-slave` | Address range, 3.5 character timing, exception codes, and a map that matches the docs. |
| `esp32-modbus-rtu-tcp-gateway` | MBAP framing, unit-id mapping, transaction ids, and serialising the half-duplex side. |
| `esp32-wifi-enterprise-eap` | EAP-TLS vs PEAP, certificate validation, time sync, and the identity fields. |

| `esp32-modbus-security-and-mapping` | Register addressing, word order, scaling, write access and vendor map contracts. |
| `esp32-opc-ua-gateway` | OPC UA information models, certificates, quality and edge gateway boundaries. |
| `esp32-ethercat-gateway-boundary` | EtherCAT capability boundaries and safe northbound gateway architecture. |
| `esp32-cc1101-subghz` | CC1101 modem profiles, FIFO/IRQ handling and sub-GHz regulatory checks. |
| `esp32-sx126x-lora` | SX126x BUSY/DIO1 sequencing, RF switch and LoRa airtime. |
| `esp32-load-cells-hx711` | Load-cell mechanics, bridge wiring, calibration and drift. |
| `esp32-thermocouple-max31855` | Thermocouple wiring, cold-junction compensation and fault decoding. |
| `esp32-voltage-current-monitoring` | Shunt selection, INA219/INA226 calibration and transient sampling. |
| `esp32-dma-cache-psram` | DMA memory capabilities, cache ownership and PSRAM constraints. |
| `esp32-heap-forensics` | Heap leak vs retention, fragmentation, tracing and capability pools. |
| `esp32-wifi-roaming` | Multi-AP handoff, hysteresis, reconnect state machines and RF validation. |
| `esp32-max31865-rtd` | RTD wiring topology, reference resistor, linearization and MAX31865 faults. |
| `esp32-rmt-waveform-io` | Hardware-timed pulse generation/capture, symbol buffers and RMT API generations. |
| `esp32-mcpwm-power-stage` | Complementary PWM, dead time, hardware fault shutdown and motor power-stage safety. |
| `esp32-pcnt-encoder-feedback` | Pulse counting, quadrature direction, glitch filtering and counter overflow. |
| `esp32-sdmmc-card-lifecycle` | SDMMC/SPI selection, hot removal, power-loss logging and bounded storage latency. |
| `esp32-usb-otg-serial-jtag` | SoC-specific USB host/device/OTG and USB-Serial-JTAG capability boundaries. |
| `esp32-lwip-network-diagnostics` | DHCP, DNS, TCP stream framing, socket lifecycle and reconnect forensics. |
| `esp32-industrial-safety-interlocks` | Safe output states, interlocks, E-stop boundaries and restart inhibition. |
| `esp32-thermal-enclosure-derating` | Enclosure thermal budgets, hotspot measurements and temperature derating. |

### How a skill is laid out

Each skill is a directory, following the layout used by the official Anthropic
skill repository:

```
skills/esp32-pin-safety/
  SKILL.md          the rules, loaded when the task touches pins
  LICENSE.txt       so the directory can be copied out on its own
  reference/        the long tables, read only when needed
```

`SKILL.md` stays short on purpose: an agent loads it for every relevant task, so
it carries the decisions. The tables live in `reference/` and are pulled in only
when someone actually needs the full pin map.

The pin table is generated from `data/esp32-pins.json` by
`tools/render_pin_table.py`, and a test fails if the two drift apart.

### Tools

All ten use the standard library only. All ten exit non-zero on an error, so
they drop straight into CI or a pre-flash hook.

| Tool | Answers |
|---|---|
| `tools/pincheck.py` | Is this GPIO allowed to do this job on this SoC? |
| `tools/partition_check.py` | Does this partition table fit the flash and support OTA? |
| `tools/power_budget.py` | How long does this duty cycle actually last on this battery? |
| `tools/panic_decode.py` | Which `addr2line` command turns this crash dump into file:line? |
| `tools/airtime.py` | Does this LoRa payload fit the duty cycle at this spreading factor? |
| `tools/modbus_map_check.py` | Does this register map overlap itself or lie about its types? |
| `tools/modbus_frame.py` | Is this RTU frame valid, and does the 3.5 character gap fit your timer? |
| `tools/mqtt_topic_check.py` | Is this topic legal, and does the filter match the topic it is meant for? |
| `tools/flash_layout.py` | Do these images overlap, and do they fit the flash at these offsets? |
| `tools/i2c_address_check.py` | Do two devices share an address, or use one the spec reserves? |
| `tools/modbus_map_check.py` | Is this Modbus register map valid, non-overlapping and fully described? |

### Data and examples

| Path | What it is |
|---|---|
| `data/esp32-pins.json` | Machine-readable pin constraints for `esp32`, `esp32s3`, `esp32c3`. |
| `examples/pinmap.txt` | A realistic pin map with the mistakes agents actually make. |
| `examples/partitions-ota-4mb.csv` | A correct 4 MB OTA layout. |
| `examples/partitions-broken.csv` | The same layout with misalignment, overlap and overflow. |
| `examples/panic-log.txt` | A real `LoadProhibited` dump with a four frame backtrace. |
| `examples/modbus-register-map.csv` | Valid example register map with explicit offsets, types and scaling. |
| `examples/modbus-register-map-broken.csv` | Deliberately invalid map covering overlap, zero scale and coil type errors. |
| `tests/` | 559 unit tests: the ten tools, the pin and partition databases, one shape test per skill, and the packaging layer. |

## Verified on hardware

The pin database is not taken on trust. It was checked against a real module:

| Chip | Flash | Toolchain | Result |
|---|---|---|---|
| ESP32-D0WD-V3 rev 301, 2 cores | 4 MB | Arduino / ESP-IDF 5.5.5 | flashed, booted, serial read back |

```
=== board facts ===
chip        : ESP32-D0WD-V3 rev 301, 2 core(s)
cpu         : 240 MHz
flash       : 4 MB (4194304 bytes)
sdk         : v5.5.5
free heap   : 331072 bytes
=== end ===
```

Full boot log and the reproduction steps: [docs/hardware.md](docs/hardware.md).

## Every rule is compiled

A skill is advice, and advice that does not compile is worthless. So each rule in
`skills/` also exists as code that the compiler has to accept:

```bash
pio run -d examples/compiled
```

One sketch, one function per skill - PWM duty from the resolution, an ADC1-only
reading in calibrated millivolts, an I2C scan with a timeout, an ISR that hands
work to a task through a queue, the LED current shortfall, the partition
alignment check, the Modbus CRC, the reset reason switch. It is not meant to run;
it exists so that `ledcAttach`, `analogReadMilliVolts`, `Wire.setTimeOut` and the
rest are proven to exist with the signature the skills claim, on the core
version the README names.

CI runs it on every push. If an upstream core renames something, this job goes
red before a reader copies an API that no longer exists - which is exactly the
failure mode a skill library is supposed to prevent.

## On accuracy

The database encodes only constraints that are unambiguous across every module
variant, transcribed from the Espressif datasheets and the ESP-IDF GPIO
documentation. Board-specific quirks — the on-board LED on `GPIO2`, the USB
bridge on `GPIO1`/`GPIO3` — are deliberately excluded, because they differ per
board and a checker that cries wolf gets switched off.

If a constraint is wrong for your module, open an issue with the datasheet page
number and it gets fixed. That is the only way a database like this stays useful.

## Expanded engineering knowledge base

The repository now also maintains an evidence-oriented knowledge system in
[docs/knowledge-base/](docs/knowledge-base/README.md). It separates task skills,
field failures, protocol dossiers, test patterns and source confidence. The
initial casebook records both confirmed patterns and unresolved reports without
presenting open issues as solved.

New industrial and reliability skills in this expansion:
- `esp32-modbus-tcp` — MBAP framing, TCP stream parsing and RTU gateway behavior.
- `esp32-rs232-rs422` — serial physical-layer selection, wiring and protection.
- `esp32-industrial-analog-io` — 4–20 mA and 0–10 V analog front ends.
- `esp32-pt100-pt1000-rtd` — RTD wiring, excitation and calibration.
- `esp32-w5500-ethernet` — SPI Ethernet controller integration and diagnostics.
- `esp32-ethernet-rmii-phy` — MAC/PHY separation, RMII clock and PHY bring-up.
- `esp32-can-fd-gateway` — Classical CAN vs CAN-FD architecture and gateway safety.
- `esp32-i2c-recovery` — bounded bus recovery, stuck-line diagnosis and safe probing.
- `esp32-power-integrity` — brownout, regulator transients, battery sag and measurement.
- `esp32-secure-ota-production` — signed updates, rollback and power-fail resilience.
- `esp32-fault-injection-hil` — HIL fixtures, fault injection and soak-test design.
- `esp32-serial-field-diagnostics` — UART/RS485 capture, buffer and framing diagnostics.
- `esp32-industrial-gateway-architecture` — resilient multi-protocol gateway architecture.

See [the expansion roadmap](docs/knowledge-base/expansion-roadmap.md) for the
multi-release target of 300–500 skills, 2,000–3,000 field cases and a much larger
test/example corpus. These are targets, not current counts.

## Roadmap

- [ ] ESP32-C6 and ESP32-H2 pin maps
- [ ] `--board` profiles for common dev boards (DevKitC, WROVER-KIT, M5Stack)
- [ ] Reusable GitHub Action that runs all ten checkers on every PR
- [ ] Compile the examples against the previous Arduino core, not just the current one

## Contributing

The useful contributions here are not code, they are corrections and coverage:

- **A wrong constraint.** Open an issue with the datasheet page number. A rule
  that is wrong for your module is the most valuable bug report this repo can
  get, because it means someone else will hit it too.
- **A chip we do not cover.** `data/esp32-pins.json` has `esp32`, `esp32s3` and
  `esp32c3`. C6 and H2 are missing.
- **A skill from your domain.** CAN, BLE, camera, SD card, anything you fight
  with weekly. Copy the shape of an existing skill: a short `SKILL.md`, a
  `reference/` folder for the long tables, and a license so it can be copied out
  on its own.
- **A failure we have not written down.** `esp32-field-gotchas` has a hundred and sixty
  entries, each with a link to the thread where it was solved. If you have one
  that is not there, send it with the symptom and the fix.

Every skill has to survive `python -m unittest discover -s tests`, and every
rule that can be expressed as code has to compile - `examples/compiled` is built
in CI for exactly that reason.

## Binaries

Every tool is also available as one executable, so a machine without Python can
run the checkers:

```bash
python build.py            # dist/esp32-skills.pyz and dist/esp32-skills(.exe)
./dist/esp32-skills pincheck --soc esp32 --assign "6=led"
./dist/esp32-skills --list
```

Two artifacts come out of it. The `.pyz` is 25 kB and runs on any Python 3.8+
with no installation. The native executable is built with PyInstaller and is the
one to hand to someone who does not have Python at all.

PyInstaller cannot cross-compile, so `.github/workflows/release.yml` builds the
Windows and Linux binaries on their own runners and attaches both to a tag. The
build fails the release if the artifact does not run: the smoke test executes a
real command, not just `--list`, because a module that is imported dynamically is
exactly the thing PyInstaller leaves out.

## Where this is going

![Roadmap: 300 to 500 skills, 2,000 to 3,000 field cases, 1,500 to 2,500 tests](docs/assets/roadmap.jpg)

The numbers in that image are **targets, not counts**. Today the repository has
101 skills, 477 tests, 160 field notes and ten checkers; every figure in the
README is read from the repository itself.

## License

MIT — see [LICENSE](LICENSE).
