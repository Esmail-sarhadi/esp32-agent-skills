# RS-485 Physical-Layer Engineering Dossier

## Electrical interface

RS-485 is a balanced differential physical layer, not a complete protocol. The transceiver determines logic thresholds, common-mode range, fail-safe behavior, slew rate, ESD rating and whether isolation is present. ESP32 GPIO pins must connect to a compatible transceiver logic interface, never directly to the differential bus.

Check the transceiver datasheet for supply voltage, receiver input thresholds, driver enable polarity, common-mode range, bus loading and protection ratings. A label marked A/B is not a reliable polarity convention across all vendors; use the transceiver truth table and device documentation.

## Topology and termination

Use a trunk/daisy-chain topology where practical. Avoid star wiring and long stubs at high data rates. Terminate only at the two physical ends of the main bus with a value matched to cable characteristic impedance, commonly near 120 ohms for typical twisted-pair cable. Do not add a terminator at every node.

Bias/failsafe design must be calculated for the complete network. Integrated fail-safe receivers behave differently from external bias resistors; multiple bias networks can overload the bus. Include receiver unit loads and cable length in the node-count budget.

## Reference, shield and isolation

A differential pair still has a finite common-mode range. Provide a suitable signal reference conductor where required by the transceiver and installation design. Do not casually bond isolated signal ground to chassis/PE at multiple points. Define shield termination based on EMC and system grounding requirements; this is installation-specific.

Use galvanic isolation and isolated power where ground potential differences or hazardous wiring justify them. Add TVS/surge protection selected for the bus environment and ensure protection capacitance does not destroy signal integrity.

## Half-duplex direction timing

DE/RE timing must include UART shift-register completion, transceiver enable/disable delays and the protocol's inter-frame gap. Waiting for the TX FIFO to empty is not necessarily the same as the final stop bit leaving the pin. Verify with a logic analyzer on TX and DE simultaneously.

Hardware auto-direction may be preferable when software-controlled RTS timing is not deterministic enough. A firmware delay is not a universal substitute for measurement.

## Field diagnostic sequence

1. Verify transceiver part number, supply and logic voltage.
2. Verify pair continuity, polarity and reference conductor.
3. Measure differential idle and active levels at both ends.
4. Confirm termination only at the bus ends.
5. Capture TX, RX and DE around the final byte.
6. Test one node, then add nodes incrementally.
7. Inject cable disconnect, missing node power and bus short under controlled conditions.

## Sources

- Analog Devices AN-960, RS-485/RS-422 circuit implementation: https://www.analog.com/media/en/technical-documentation/application-notes/AN-960.pdf
- TI RS-485 design guide: https://www.ti.com/lit/an/slla272d/slla272d.pdf
- ESP-IDF UART driver: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/uart.html
- ESP-IDF issue on RS485 direction timing: https://github.com/espressif/esp-idf/issues/15987

## Evidence boundary

Cable, grounding, shield and termination choices depend on the complete installation. This dossier is not a substitute for the transceiver datasheet, surge/EMC design review or site grounding specification.
