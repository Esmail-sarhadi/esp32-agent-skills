# MAX31865 RTD Converter Dossier

## Measurement chain

The MAX31865 converts an RTD resistance ratio into a digital result. The measurement accuracy depends on RTD class, lead compensation, reference resistor tolerance and drift, excitation current, wiring, thermal gradients and calibration. The IC's nominal resolution is not the accuracy of the complete probe assembly.

## Wiring topology

Select 2-, 3- or 4-wire mode according to cable length and accuracy requirements. Follow the exact datasheet connection diagram for FORCE, RTDIN and reference pins. Do not assume a breakout's terminal labels match another vendor's board. Confirm whether the board is configured for PT100 or PT1000 and measure the reference resistor value if accuracy matters.

## Conversion and diagnostics

Read the RTD ratio and fault status using the documented SPI frame. Apply Callendar–Van Dusen coefficients appropriate to the RTD standard and temperature range. Check open/short, overvoltage and undervoltage fault flags before publishing a temperature. Preserve raw ratio and fault register in diagnostics.

## Self-heating and filtering

Excitation current creates sensor dissipation. Consider duty-cycling bias or conversion according to the device's supported operating sequence. Filtering reduces noise but adds latency; report both sample interval and filter response. Do not smooth away an open-circuit or saturation fault.

## Calibration and validation

Calibrate the installed chain at multiple traceable points. Record sensor serial/lot, wiring topology, reference resistor measured value, calibration coefficients, instrument uncertainty and date. Verify long-cable noise and switching interference in the final enclosure.

## Test matrix

| Test | Expected evidence |
|---|---|
| Precision resistor substitution | Resistance conversion error |
| Open/short sensor | Fault bits and invalid sample |
| Two/three/four-wire wiring | Lead compensation behavior |
| Thermal reference points | Error and uncertainty |
| Long cable near switching load | Noise and settling |

## Sources

- Analog Devices MAX31865 datasheet: https://www.analog.com/media/en/technical-documentation/data-sheets/max31865.pdf
- Analog Devices RTD measurement resources: https://www.analog.com/en/resources/technical-articles/rtd-measurement-system-design-essentials.html

## Evidence boundary

This dossier does not define the wiring for every breakout board. The component datasheet and board schematic take precedence; software calibration cannot correct a wrong topology or poor thermal installation.
