---
name: esp32-lora-and-lorawan
description: Use when an ESP32 drives a LoRa radio - the module never answers on SPI, DIO0 never fires, the join request is never accepted, or the gateway hears nothing. Covers SX127x wiring, airtime and duty cycle, and join failures.
---

# LoRa and LoRaWAN on ESP32

The radio is a separate chip on SPI. Almost every failure is one of three things:
the wiring, the interrupt line, or the duty cycle.

## Wiring the SX127x

- 3.3 V only. The module draws up to 120 mA during transmit at +20 dBm; a weak
  regulator browns out the ESP32 on every packet, which looks like a crash.
- SPI mode 0, up to 10 MHz. Long wires at 10 MHz give intermittent NOP answers.
- **DIO0 must be connected.** Polling the register works for a test and fails in
  production: you will miss the TxDone window and the driver will hang waiting.
- RESET must be a real GPIO. Tying it high leaves the chip in an undefined state
  after a brownout.

## Airtime is the design constraint

A 20 byte payload at SF12/125 kHz occupies the channel for about 1.5 seconds. In
the EU868 band the legal duty cycle is 1 %, so that packet may be sent once every
150 seconds. Any design that reports every 30 seconds must use a lower spreading
factor, a shorter payload, or a different band.

Work out the airtime before choosing the interval, not after the gateway starts
dropping frames.

## Join failures

| What you see | What it means |
|---|---|
| join accept never arrives | wrong region/plan, or the gateway is on another sub-band |
| joins once, then never again | nonces lost on reset - the counter restarted |
| works near the gateway only | antenna mismatch, or the module is inside a metal box |
| accepted, then all uplinks fail | duty cycle limiter on the network server |
| RSSI good, SNR negative | interference, not distance - check the channel plan |

## Antenna and ground

The module needs a ground plane under it and a keepout around the antenna. A
quarter-wave wire soldered to the pad and folded against the PCB loses most of
its efficiency, and no amount of software gain fixes it.

## When it is not LoRaWAN

Point-to-point LoRa has no join, no duty-cycle limiter and no server: the two
ends must share frequency, spreading factor, bandwidth and sync word. A mismatch
in any one of them is silence, and the radio will happily report a successful
transmit.
