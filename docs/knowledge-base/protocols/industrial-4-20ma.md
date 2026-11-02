# 4–20 mA and 0–10 V Industrial Analog Input Dossier

## Interface selection

A 4–20 mA loop is a current interface designed for robust transmission over industrial wiring. A 0–10 V input is a voltage interface and is more sensitive to ground offsets, cable resistance and coupled noise. Select the interface based on sensor output, cable length, installation environment and isolation requirements.

The ESP32 ADC is not an industrial input stage. Do not connect a field loop or 10 V signal directly to a GPIO. Design a protected analog front end with input current/voltage limits, filtering, appropriate common-mode handling and calibration.

## 4–20 mA conversion

A common measurement method uses a precision shunt resistor to convert loop current to voltage. Select resistance so the maximum loop current produces a voltage within the analog front end's allowed range while preserving loop compliance voltage. Calculate shunt dissipation at fault and overrange current; include tolerance and temperature coefficient.

For a 250 ohm shunt, 4 mA produces 1 V and 20 mA produces 5 V. That example is not safe to connect directly to an ESP32 ADC; it requires a suitable attenuator/buffer/protection stage and a check of the ADC input range and absolute maximum ratings. Choose shunt value and scaling from the complete circuit, not this example alone.

## Fault detection

A live-zero loop can distinguish normal zero-scale (4 mA) from some wiring faults, but exact underrange/overrange thresholds depend on the transmitter standard and device configuration. Define thresholds from the transmitter datasheet. Detect open loop, short, overrange, saturation and stale samples separately.

## 0–10 V front end

Use a precision divider or buffer designed for maximum input including expected transients, not merely nominal 10 V. Check divider loading, input impedance, resistor tolerance, protection leakage and RC settling. Add surge/transient protection appropriate to the field wiring environment. Consider galvanic isolation when the signal reference may differ materially from ESP32 ground.

## ADC and calibration

For ESP32 internal ADC, use the target-specific attenuation and calibration support. ADC characteristics vary by SoC family and board; do not assume identical range, linearity or calibration behavior across chips. For higher accuracy or channel count, use an external ADC with documented input range, reference, common-mode and isolation characteristics.

Calibrate the complete installed path at multiple points. Store calibration coefficients, units, channel identity, reference instrument and calibration date. Preserve raw ADC counts and engineering-unit values.

## Verification matrix

| Test | Required evidence |
|---|---|
| 4 mA / 12 mA / 20 mA | Scale and linearity |
| Open loop | Fault detection |
| Overrange current | Protection and saturation behavior |
| Input short | Safe state and diagnostics |
| Long cable / switching load | Noise and settling |
| Temperature variation | Drift and calibration stability |

## Sources

- ESP-IDF ADC calibration driver: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/adc/adc_calibration.html
- TI industrial analog input design resources: https://www.ti.com/solution/analog-input-module
- Analog Devices 4–20 mA current loop overview: https://www.analog.com/en/resources/analog-dialogue/articles/4-to-20-ma-current-loop.html

## Evidence boundary

Input protection, isolation, creepage/clearance and surge immunity are hardware certification topics. A software reading within range does not prove that the input survives industrial transients.
