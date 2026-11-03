# ESP32 Agent Skills

A practical ESP32 engineering toolkit for AI coding agents: curated skills, hardware-aware guardrails, and command-line validation tools that catch mistakes before a board is flashed.

![ESP32 Agent Skills](docs/assets/banner.jpg)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/workflows/test.yml/badge.svg)](https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/workflows/test.yml)

[Read the project site →](https://esmail-sarhadi.github.io/esp32-agent-skills/)

## Why this exists

AI coding agents can write ESP32 firmware that compiles cleanly and still fails on hardware. The most common failures are not logic bugs; they are hardware constraints hidden in the pin map, boot settings, power budget, and protocol boundaries.

Examples:

- GPIO6 tied to SPI flash
- GPIO34 used as an output when it is input-only
- GPIO12 held high during reset on a 3.3 V flash board
- ADC2 readings failing while Wi‑Fi is active

This repository gives the agent the missing knowledge and gives the workflow a check that runs before flashing.

![Pin checker catching an unsafe GPIO and then passing a corrected pin](docs/assets/demo.gif)

## What is included

- Skills for ESP32 architecture, GPIO, power, memory, OTA, Wi‑Fi/BLE, Modbus, CAN, sensors, debugging, and industrial interfaces
- Hardware-focused validation tools for common failure modes
- Agent-installation support for multiple harnesses and plugins
- Example boards, test data, and engineering references

## Quick start

Clone and validate a pin map:

```bash
git clone https://github.com/Esmail-sarhadi/esp32-agent-skills.git
cd esp32-agent-skills
python tools/pincheck.py --soc esp32 --assign "12=relay,34=button,25=led"
```

Example output:

```text
ESP32 (classic, WROOM-32 / WROVER) - 3 pin(s) checked

  GPIO6   ERROR  status_led     GPIO6 is connected to the SPI flash, using it bricks the module
  GPIO12  WARN   relay1         GPIO12 is a strapping pin and must be LOW at boot on 3.3 V flash
                                modules, HIGH selects 1.8 V and the board will not boot
  GPIO34  WARN   button         GPIO34 is input-only: it cannot drive an output and has no internal
                                pull-up or pull-down

  1 error(s), 2 warning(s)
```

Check a partition layout:

```bash
python tools/partition_check.py --file examples/partitions-ota-4mb.csv --flash 4MB --ota
```

Check the power budget:

```bash
python tools/power_budget.py --battery 3000 --wakes-per-hour 12 --wake-ms 2000
```

## Install as an agent skill

This repository follows the skill layout used by agent toolchains, with content split between short operational guidance and longer reference material.

### Claude Code plugin

```bash
/plugin marketplace add Esmail-sarhadi/esp32-agent-skills
/plugin install esp32-agent-skills
```

### Local harness install

```bash
./install.sh --harness claude
./install.sh --harness codex
./install.sh --harness opencode
./install.sh --harness all
```

PowerShell variants are also provided:

```powershell
./install.ps1 -Harness codex
./install.ps1 -Harness all -DryRun
```

See [harnesses/README.md](harnesses/README.md) for supported locations and capability boundaries.

## Included tools

| Tool | Purpose |
|---|---|
| `tools/pincheck.py` | Validate GPIO usage against ESP32 SoC constraints |
| `tools/partition_check.py` | Check partition layout and OTA alignment |
| `tools/power_budget.py` | Estimate runtime and dominant current draw |
| `tools/panic_decode.py` | Decode crash dumps and backtraces |
| `tools/airtime.py` | Check LoRa airtime and duty-cycle feasibility |
| `tools/modbus_map_check.py` | Validate Modbus register maps |
| `tools/modbus_frame.py` | Validate RTU framing and timing |
| `tools/mqtt_topic_check.py` | Validate MQTT topic filters and naming |
| `tools/flash_layout.py` | Detect overlapping firmware or flash regions |
| `tools/i2c_address_check.py` | Detect duplicate or reserved I²C addresses |

## Repository structure

- `skills/` — agent-facing skills used by coding assistants
- `rules/` — reusable engineering guardrails
- `contexts/` — domain knowledge and usage context
- `agents/` — specialist role definitions for architecture, review, validation, and incident analysis
- `workflows/` — structured engineering workflows
- `examples/` — realistic broken and fixed examples
- `data/` — machine-readable hardware data
- `tests/` — validation suite for the tools and skill metadata

## Accuracy and verification

The pin database is grounded in ESP32 datasheets and the ESP-IDF documentation, and the repository includes checks that validate the rules against real hardware and compiler behavior.

The project also includes a hardware verification log and compiled examples:

- [docs/hardware.md](docs/hardware.md)
- [examples/compiled](examples/compiled)

## Contributing

High-value contributions include:

- correcting a hardware constraint with datasheet evidence
- adding a missing SoC or board profile
- submitting a real-world field failure with a fix
- proposing a new skill or reference for an uncovered domain

Open an issue or send a pull request with supporting evidence.

## License

MIT — see [LICENSE](LICENSE).
