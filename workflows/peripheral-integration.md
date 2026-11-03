# Workflow: ESP32 Peripheral Integration

1. Read the exact component datasheet and the matching repository skill.
2. Confirm voltage, current, logic levels, pin capabilities and board routing.
3. Check bus electrical requirements: I2C pull-ups, SPI mode/frequency,
   UART baud/levels, RS485 termination/bias or CAN transceiver topology.
4. Confirm driver/API compatibility with the project's pinned ESP-IDF or
   Arduino-ESP32 version.
5. Implement bounded initialization, explicit timeouts and recoverable error
   handling.
6. Validate malformed responses, disconnects, missing devices and bus faults.
7. Run relevant checker, unit/integration tests and build.
8. Verify with the actual component and board; record measured conditions.

Do not infer electrical compatibility from a library example or a successful
compile.
