# ESP32 Agent Skills

**Fourteen skills and four checkers that stop AI coding agents from writing ESP32 firmware that compiles and then kills the board.**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](tools/pincheck.py)
[![CI](https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/workflows/test.yml/badge.svg)](https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/workflows/test.yml)

**[Read this on a page instead of a README →](https://esmail-sarhadi.github.io/esp32-agent-skills/)**

![ESP32 Agent Skills](docs/assets/poster.jpg)

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

**Claude Code**

```bash
cp -r skills/* ~/.claude/skills/
```

**Cursor / other agents that read project rules**

Point the rule file at the skill you need, or paste its body into `.cursorrules`:

```markdown
When writing ESP32 firmware, follow skills/esp32-pin-safety/SKILL.md before
choosing any GPIO number. Never invent a pin number.
```

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
| `esp32-field-gotchas` | A hundred and ten failures people actually hit — brownout, dead I2C, garbled UART, watchdog resets — indexed by symptom, each linked to the Stack Overflow thread where the cause was found. |

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

All four use the standard library only. All four exit non-zero on an error, so
they drop straight into CI or a pre-flash hook.

| Tool | Answers |
|---|---|
| `tools/pincheck.py` | Is this GPIO allowed to do this job on this SoC? |
| `tools/partition_check.py` | Does this partition table fit the flash and support OTA? |
| `tools/power_budget.py` | How long does this duty cycle actually last on this battery? |
| `tools/panic_decode.py` | Which `addr2line` command turns this crash dump into file:line? |

### Data and examples

| Path | What it is |
|---|---|
| `data/esp32-pins.json` | Machine-readable pin constraints for `esp32`, `esp32s3`, `esp32c3`. |
| `examples/pinmap.txt` | A realistic pin map with the mistakes agents actually make. |
| `examples/partitions-ota-4mb.csv` | A correct 4 MB OTA layout. |
| `examples/partitions-broken.csv` | The same layout with misalignment, overlap and overflow. |
| `examples/panic-log.txt` | A real `LoadProhibited` dump with a four frame backtrace. |
| `tests/` | 30 unit tests covering all four tools. |

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

## Roadmap

- [ ] ESP32-C6 and ESP32-H2 pin maps
- [ ] `--board` profiles for common dev boards (DevKitC, WROVER-KIT, M5Stack)
- [ ] Reusable GitHub Action that runs all four checkers on every PR
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
- **A failure we have not written down.** `esp32-field-gotchas` has a hundred and ten
  entries, each with a link to the thread where it was solved. If you have one
  that is not there, send it with the symptom and the fix.

Every skill has to survive `python -m unittest discover -s tests`, and every
rule that can be expressed as code has to compile - `examples/compiled` is built
in CI for exactly that reason.

## License

MIT — see [LICENSE](LICENSE).
