# Modbus TCP Engineering Dossier

## Scope and architecture

Modbus TCP transports Modbus application protocol messages over a TCP byte stream. The MBAP header carries a transaction identifier, protocol identifier, length and unit identifier. TCP preserves byte order but not application message boundaries: one read may contain a partial ADU, exactly one ADU, or multiple ADUs.

Do not assume one socket read equals one Modbus request. Accumulate bytes until the MBAP header is complete, validate the protocol identifier and declared length, then extract exactly one ADU and retain trailing bytes for the next frame. Bound the receive buffer and reject impossible lengths before allocation.

## Request validation

- Check transaction ID correlation for every outstanding request.
- Require protocol identifier zero for standard Modbus TCP.
- Validate MBAP length against the minimum and maximum accepted ADU.
- Validate function code and quantity against the function-specific limits.
- Validate unit identifier according to the downstream server/gateway topology.
- Return the correct Modbus exception for a validly framed but unsupported request.
- Close or quarantine peers that repeatedly send malformed or oversized frames.

## TCP lifecycle

Use finite connect, read and write deadlines. A peer may disconnect between header and payload. Reconnect logic must not leak sockets or block the fieldbus task. Use one connection owner or explicit synchronization; never allow two tasks to interleave bytes on one stream.

For an RTU-to-TCP gateway, map transaction IDs to downstream serial transactions, preserve unit IDs, and enforce a bounded queue. TCP retransmission does not create deterministic RTU timing. A serial timeout must be translated into a documented gateway error policy.

## Security boundary

Traditional Modbus TCP has no built-in authentication or encryption. Keep it on a controlled network, restrict client addresses and write ranges, and use a VPN, firewall or secure gateway where remote access is required. Do not expose arbitrary register writes directly to the public internet.

## Regression matrix

| Case | Expected behavior |
|---|---|
| Header split across TCP reads | Parser waits for complete header |
| Payload split across reads | Parser waits for declared length |
| Two ADUs in one read | Both parsed independently |
| Invalid protocol ID/length | Rejected without overread |
| Peer closes mid-frame | Bounded cleanup; no stale buffer |
| Slow downstream RTU slave | Queue bounded; timeout reported |
| Duplicate transaction ID | Defined correlation policy |

## Sources

- Modbus Organization specifications: https://www.modbus.org/specs.php
- Modbus Application Protocol Specification V1.1b3: https://www.modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf
- ESP-Modbus component: https://github.com/espressif/esp-modbus

## Evidence boundary

This dossier describes protocol framing and engineering checks. It does not claim interoperability with every vendor's register map. Device-specific address conventions, data types and timing must come from the vendor's current register documentation.
