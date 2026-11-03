# ESP32 Agent Skills

Practical ESP32 and embedded-engineering knowledge for AI coding agents—plus command-line checks that catch hardware mistakes before you flash.

![ESP32 Agent Skills](docs/assets/banner.jpg)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/workflows/test.yml/badge.svg)](https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/workflows/test.yml)

## Why use it?

ESP32 firmware can compile and still fail on real hardware: a GPIO may be tied to flash, input-only, or affect boot; ADC2 readings can fail when Wi-Fi is active. The skills give agents reliable, task-specific guidance, while the checkers validate common constraints automatically.

![Pin checker catching an unsafe GPIO and then passing a corrected pin](docs/assets/demo.gif)

## Get started

Clone the repository and check a pin assignment:

```bash
git clone https://github.com/Esmail-sarhadi/esp32-agent-skills.git
cd esp32-agent-skills
python tools/pincheck.py --soc esp32 --assign "12=relay,34=button,25=led"
```

Install the skills for your agent:

```bash
./install.sh --harness claude   # or codex, opencode, all
```

For Claude Code, you can also install the plugin:

```text
/plugin marketplace add Esmail-sarhadi/esp32-agent-skills
/plugin install esp32-agent-skills
```

See [harness installation details](harnesses/README.md). Windows users can use `install.ps1`.

## What's included

- **Agent skills** for GPIO, power, FreeRTOS, Wi-Fi/BLE, storage, OTA, sensors, industrial protocols, security, debugging, and more.
- **Checkers** for pin assignments, partitions, power budgets, Modbus maps and frames, MQTT topics, flash layouts, I²C addresses, and other common engineering checks.
- **Engineering resources** including rules, contexts, specialist roles, workflows, examples, and a growing [knowledge base](docs/knowledge-base/README.md).

Browse the [`skills/`](skills/) directory or the [project site](https://esmail-sarhadi.github.io/esp32-agent-skills/) to explore the library.

## More checks

```bash
python tools/partition_check.py --file examples/partitions-ota-4mb.csv --flash 4MB --ota
python tools/power_budget.py --battery 3000 --wakes-per-hour 12 --wake-ms 2000
python -m unittest discover -s tests
```

The checks help catch configuration and design issues; they do not replace datasheet review or testing on your target hardware. See [hardware verification notes](docs/hardware.md).

## Contributing

Found an incorrect constraint or have a useful failure case, skill, or board to add? Please [open an issue](https://github.com/Esmail-sarhadi/esp32-agent-skills/issues) or submit a pull request. Include source references or hardware details when possible.

## License

[MIT](LICENSE)
