# HX711 and Load-Cell Integration Dossier

## Measurement system

The HX711 is a precision 24-bit ADC intended for bridge sensors, but nominal bit depth is not equivalent to usable weight resolution. Noise, mechanical mounting, bridge excitation, creep, temperature drift, cable pickup and calibration dominate real-world performance.

## Bridge wiring and mechanics

Obtain excitation and signal wiring from the load-cell datasheet; wire colors are not standardized. Keep differential signal conductors paired and away from motor, relay and mains wiring. Use suitable shield termination for the installation. Mount the cell in its intended load direction and prevent side loading, binding or overload.

## HX711 configuration

Verify RATE selection, gain/channel selection, supply and data-ready behavior. Avoid blocking the main control task waiting for conversion; use a bounded wait or event-driven sampling. Treat missing data-ready and stuck output as sensor faults. Confirm that the selected library's timing and pin behavior match the board.

## Calibration and uncertainty

Tare only after the platform is mechanically stable. Calibrate across the intended operating range with traceable masses, and test linearity and eccentric loading. Store calibration coefficient, units, sensor identity, date and uncertainty. Recalibrate after mechanical changes or sensor replacement.

## Filtering and fault policy

Preserve raw ADC counts before filtering. Define filter delay and reject outliers without masking overload or disconnect. Detect open/short, saturation, implausible slew and drift. Represent invalid/stale readings separately from a valid numeric zero.

## Test matrix

| Test | Evidence |
|---|---|
| Multiple known masses | Span, linearity and residual error |
| Empty platform soak | Zero drift |
| Eccentric load | Corner error |
| Motor/relay switching | Coupled noise |
| Sensor disconnected | Explicit fault state |

## Sources

- Avia Semiconductor HX711 datasheet: https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf
- SparkFun load-cell amplifier hookup guide: https://learn.sparkfun.com/tutorials/load-cell-amplifier-hx711-breakout-hookup-guide

## Evidence boundary

Mechanical load paths and mounting are part of the instrument. A calibrated ADC reading does not prove the load cell is mechanically safe or that the complete weighing system meets legal metrology requirements.
