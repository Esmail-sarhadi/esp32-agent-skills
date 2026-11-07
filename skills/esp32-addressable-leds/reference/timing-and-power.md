# Timing, current and wiring by LED type

## Protocol summary

| Type | Data protocol | Bits per LED | Colour order | Runs at |
|---|---|---|---|---|
| WS2812B | 800 kHz NRZ, no clock line | 24 | GRB | 5 V |
| WS2811 | 800 kHz NRZ | 24 | GRB | 5 V or 12 V |
| WS2815 | 800 kHz NRZ, backup data line | 24 | GRB | 12 V |
| SK6812 | 800 kHz NRZ | 32 | GRBW | 5 V |
| SK6812 RGBW | 800 kHz NRZ | 32 | GRBW | 5 V |
| APA102 | SPI, clock + data | 32 | BGR, with a 5-bit global brightness in the header | 5 V, 5 V logic |
| SK9822 | SPI, clock + data | 32 | BGR | 5 V, 5 V logic |

The two families behave differently in one important way: the 800 kHz parts have
**no clock line**, so a single late or early edge shifts every subsequent bit
and corrupts the rest of the strip. The SPI parts have a clock and tolerate
interrupts far better.

## Bit timing for the 800 kHz family

One bit is 1.25 µs:

| Symbol | High time | Low time |
|---|---|---|
| `0` | about 0.4 µs | about 0.85 µs |
| `1` | about 0.8 µs | about 0.45 µs |
| reset | low for at least 50 µs | |

These windows are tight enough that software bit-banging on a chip with Wi-Fi
enabled will fail. Use the RMT peripheral.

## Current and supply

- Full white is about **20 mA per colour channel**, so roughly 60 mA per
  RGB LED, and 80 mA for RGBW with the white channel on.
- Average current for real animations is far lower, but the supply has to
  survive the worst frame, not the average one.
- Size the supply as `N × 0.06 A × 1.2` for RGB strips. 150 LEDs needs about
  11 A, not 9 A.
- Inject power every 100-150 LEDs. Voltage drop along the strip is what turns
  the far end orange: the blue channel needs the most headroom and fades first.
- A 1000 µF electrolytic across 5 V near the first LED absorbs the power-up
  inrush. Without it, the ESP32 browns out and resets when the strip lights up.

## Refresh budget

| LEDs | Frame time | Practical maximum |
|---|---|---|
| 30 | 0.9 ms | over 200 fps |
| 60 | 1.8 ms | about 150 fps |
| 150 | 4.5 ms | about 60 fps with a reset gap |
| 300 | 9 ms | about 30-40 fps |
| 600 | 18 ms | about 20 fps |
| 1000 | 30 ms | about 15 fps |

Frame time is `LEDs × 24 bits × 1.25 µs`. Add the reset gap, and add the time
your animation code spends computing colours, which is rarely zero.

## Wiring checklist

1. Data from the ESP32 goes through a **330-470 Ω** series resistor into `DIN`
   of the first LED.
2. If the strip runs at 5 V, put a **74AHCT125** in the data line. The AHCT part
   accepts a 3.3 V input; the HC part does not.
3. Ground of the strip and ground of the ESP32 must be connected, even when the
   strip has its own supply.
4. Never feed the strip from the ESP32's `3V3` pin.
5. For long runs between controller and strip, prefer APA102/SK9822: the clock
   line makes them far more tolerant of cable length.
