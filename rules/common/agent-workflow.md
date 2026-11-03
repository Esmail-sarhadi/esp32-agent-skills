# ESP32 Agent Workflow Rules

These rules are deliberately short. Load a task-specific skill from `skills/`
when the request matches; do not paste the entire corpus into every prompt.

## Before changing firmware

1. Identify the exact SoC, module, board revision, framework, framework version,
   and build target. Do not treat ESP32, ESP32-S2, S3, C3, C6, H2, C5 or P4 as
   interchangeable.
2. Read the matching skill and its references before proposing pin assignments,
   peripheral configuration, partition changes, power design or radio settings.
3. Inspect the actual project configuration and source. Never infer the active
   SDK version, pin map, flash size or partition table from a product name.
4. Separate facts from assumptions. Cite the datasheet, ESP-IDF documentation,
   driver source or issue that supports hardware-sensitive claims.

## Before flashing or deploying

1. Run the relevant repository checker(s) and the project's build.
2. Review partition offsets, flash capacity, boot mode pins, power budget and
   peripheral conflicts when relevant.
3. State what was tested in software and what still requires physical hardware.
4. Never claim a board was tested unless the exact board and test evidence are
   recorded.

## Engineering safety

- Never recommend disabling brownout detection as a substitute for fixing the
  supply, wiring or transient load.
- Do not drive a motor, heater, relay or other hazardous load directly from an
  MCU pin. Check driver ratings, isolation, flyback paths and fail-safe state.
- An ESP32 is not a safety-rated controller. Emergency stop and personnel
  protection require appropriately rated independent hardware.
- Do not invent GPIO capabilities. If the requested SoC is absent from the
  checked-in pin database, say that the database has no profile and stop.
- Do not put credentials, private keys or production tokens in source, logs or
  example configurations.

## Reporting

Report exact commands and outcomes. Distinguish passed, failed, skipped and
not-run checks. Label unresolved field reports as unresolved; never turn an
anecdote into a confirmed fix.
