# ESP32 Engineering Agents

These are role definitions for multi-step engineering tasks. They are
harness-neutral source documents, not claims that every harness supports native
subagents or delegation. A harness adapter may expose them as subagents where
supported; otherwise an agent can read the relevant role file as a focused
working brief.

## Roles

| Role | Use for |
|---|---|
| [ESP32 Architect](esp32-architect.md) | system boundaries, SoC/board selection, architecture decisions |
| [Firmware Implementer](firmware-implementer.md) | focused implementation after requirements and constraints are known |
| [Hardware Reviewer](hardware-reviewer.md) | pin, power, electrical interface and safety review |
| [Validation Engineer](validation-engineer.md) | build matrix, test strategy, fault injection and acceptance evidence |
| [Field Failure Investigator](field-failure-investigator.md) | incident triage, evidence grading and root-cause analysis |
| [Embedded Security Reviewer](embedded-security-reviewer.md) | OTA, provisioning, credentials, interfaces and threat review |

Use one role for a bounded task. For changes spanning hardware, firmware and
release validation, run the roles sequentially and reconcile disagreements
before implementation.
