# BLE numbers worth memorising

## Link parameters

| Parameter | Unit | Range | Notes |
|---|---|---|---|
| Connection interval | 1.25 ms | 7.5 ms - 4 s | 6 to 3200 units |
| Slave latency | intervals | 0 - 499 | the peripheral may skip this many events |
| Supervision timeout | 10 ms | 100 ms - 32 s | 10 to 3200 units |
| ATT MTU | bytes | 23 - 517 | 23 is the default; 247 is the usual negotiated value |

## The timeout inequality

A connection is only valid if the supervision timeout is longer than the worst
case the two sides agreed to:

```
timeout > (1 + slave_latency) x connection_interval x 2
```

With a 50 ms interval and latency 4, the timeout must exceed 500 ms. A client that
asks for 4 s with latency 3 needs more than 400 ms - and a client that asks for
a 4 s interval with a 4 s timeout is asking for a link that cannot stay up.

Validate in the connection-update callback. Accepting whatever the phone proposes
is how a link drops every time the CPU is busy.

## Payload

| MTU | Notification payload |
|---|---|
| 23 (default) | 20 bytes |
| 100 | 97 bytes |
| 247 | 244 bytes |
| 517 | 514 bytes |

A characteristic defined with a 512-byte value still sends 20 bytes per
notification until the MTU is exchanged.

## Advertising

| Field | Limit |
|---|---|
| Legacy advertising PDU | 31 bytes of payload, split between flags, UUIDs and name |
| Scan response | another 31 bytes |
| Extended advertising | up to 255 bytes per PDU, and multiple PDUs |

A 128-bit service UUID costs 16 of the 31 bytes. Two of them plus a name leaves no
room for manufacturer data - which is why extended advertising exists.

## Current draw, roughly

| State | Order of magnitude |
|---|---|
| Advertising, 100 ms interval | hundreds of µA to a few mA |
| Connected, idle, 1 s interval | tens of µA to ~1 mA |
| Connected, streaming notifications | several mA |
| Peak during a connection event | ~10-20 mA above the average |

The peak, not the average, decides whether a coin cell browns out.
