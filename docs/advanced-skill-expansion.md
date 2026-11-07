# Advanced ESP32 Engineering Skills — v1.3.0

This expansion adds 400 focused engineering skills across 20 engineering domains.

| Domain | New skills |
|---|---:|
| Architecture | 20 |
| GPIO routing | 20 |
| RTOS concurrency | 20 |
| Memory performance | 20 |
| Power and thermal | 20 |
| Wi-Fi networking | 20 |
| BLE provisioning | 20 |
| RF radio | 20 |
| Industrial protocols | 20 |
| Sensors measurement | 20 |
| Control actuation | 20 |
| Storage persistence | 20 |
| Security identity | 20 |
| OTA fleet operations | 20 |
| Testing verification | 20 |
| Debugging reliability | 20 |
| USB display HMI | 20 |
| Media pipelines | 20 |
| Manufacturing | 20 |
| Build supply chain | 20 |
| **Total** | **400** |

## Quality contract

The tests/test_advanced_skill_quality.py file contains 400 individually addressable
unit tests—one per added skill. Each test checks frontmatter identity, routing
metadata, required engineering sections, minimum content, fault handling and
verification evidence. The full repository validator, manifest drift checks and
existing Python/PlatformIO CI remain authoritative for the complete corpus.

## Engineering boundary

These skills are engineering playbooks, not substitutes for datasheets, schematics,
protocol specifications, risk assessments or measured HIL evidence. A compile or
host test must never be reported as proof of hardware safety or regulatory compliance.

## Official reference entry points

- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/)
- [ESP-IDF API Reference](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/)
- [Espressif technical documents](https://www.espressif.com/en/support/documents/technical-documents)
- [ESP-IDF releases](https://github.com/espressif/esp-idf/releases)
