# Protocol / Interface Dossier: Name

## Scope and compatibility

List SoC, framework, component/driver versions and known exclusions.

## Electrical layer

Voltage domains, common-mode range, drive strength, isolation, termination,
cable, shielding, grounding, ESD/surge protection and power sequencing.

## Wire protocol

Framing, byte order, checksums, addressing, timing, retries, sequence numbers,
flow control, maximum payload and error behavior.

## Firmware architecture

Driver ownership, task boundaries, ISR behavior, buffers, timeouts, state
machine, recovery and observability.

## Failure signatures

Map symptoms to likely electrical, protocol, driver, scheduler and application
causes. Include measurements that distinguish them.

## Verification

Buildable example, host tests, simulator/fuzzer, target test and HIL plan.

## Sources

Datasheet, official standard, vendor application note, upstream source and
versioned community cases.
