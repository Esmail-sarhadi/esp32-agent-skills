---
name: esp32-s31-adc-phy-lock-order-audit
description: Use when ESP32-S31 firmware with Wi-Fi modem sleep and periodic ADC oneshot sampling hits an interrupt watchdog; investigate the reported ADC/PHY lock-order inversion without assuming it affects other SoCs.
license: MIT
version: "1.0.0"
---

# ESP32-S31 ADC and PHY lock-order audit

## Purpose and decision boundary

Use this playbook for a narrowly scoped ESP32-S31 failure in which periodic adc_oneshot_read() calls coincide with Wi-Fi PHY wake-up and an interrupt watchdog. The upstream report describes a possible lock-order inversion between ADC register access and PHY temperature tracking. It is not a generic ADC calibration guide and must not be generalized to ESP32-S3, C6 or other chips without independent evidence.

The reported issue is open. An Espressif maintainer acknowledged the analysis on 2026-11-16 and said a fix would be made, but no public fix commit or release mapping was available at this review.

## Required inputs

Capture the exact S31 module/board and revision, ESP-IDF commit, Arduino component version if used, sdkconfig, CPU affinity, ADC unit/channel/attenuation/bit width, sample rate, Wi-Fi power-save mode, Bluetooth host/profile, PHY calibration configuration, reset reason and complete dual-core panic trace.

The report used an ESP32-S31 Korvo-1 board with 16 MB flash and octal PSRAM, ESP-IDF release/v6.1 at f0114250e2 (2026-11-05), and Arduino-ESP32 4.0.0-rc1 as an IDF component. The same application ran for hours without the failure at 9a97f6c54e.

## Engineering model

### Reported trigger and lock sequence

The reported trigger combines a Wi-Fi STA using WIFI_PS_MAX_MODEM, a Bluedroid BR/EDR A2DP source, and repeated ADC1 oneshot reads at ADC_ATTEN_DB_0 on the other core several times per second. The interrupt watchdog occurred after 5–15 minutes in two reported runs.

The reporter decoded both cores as spinning in spinlock_acquire. The ADC path appears to hold rtc_spinlock and then request the regi2c lock through REGI2C_WRITE_MASK in adc_ll_weight_accumulator_bypass / adc_ll_set_cal_done. The Wi-Fi wake path appears to hold the regi2c lock in closed-source libphy, then call temp_sensor_get_raw_value(), which requests rtc_spinlock.

This is a plausible lock-order inversion, not a fully proven vendor root cause: the PHY implementation is closed source and the report infers its lock ownership from the call stack.

### Investigation sequence

1. Pin the exact S31 IDF commit and preserve the ELF/map file so both core traces can be decoded against the matching build.
2. Confirm that Wi-Fi modem sleep is enabled and identify the actual A2DP/BR/EDR host and controller configuration.
3. Run a controlled matrix: Wi-Fi without modem sleep; modem sleep without periodic ADC; ADC without Wi-Fi; Wi-Fi plus ADC without A2DP; and the full reported combination.
4. Keep ADC sampling on the reported core and rate for the reproduction. Change one variable at a time and record uptime to failure.
5. Decode both cores. A single-core stack or a generic WDT message is insufficient to establish a lock cycle.
6. Compare f0114250e2 with the reported non-reproducing baseline 9a97f6c54e; do not treat this comparison as proof of the exact fix.
7. Check the upstream issue for a reviewed commit and the first release containing it before removing mitigations.

## Constraints and invariants

- Never acquire or release internal RTC/regi2c locks directly from application code to work around a suspected driver lock cycle.
- Do not call ADC register-level routines from an ISR or while holding application spinlocks.
- Do not assume that moving the ADC task to another core removes the problem; the report already used the opposite core.
- Disabling Wi-Fi modem sleep or suspending ADC sampling can be useful isolation experiments, but they are not vendor fixes and may change power or measurement requirements.
- Do not disable the interrupt watchdog to hide the deadlock.
- Keep the S31 finding separate from the ESP32-S3 ADC sar1_en_pad report; they are different symptoms and different mechanisms.

## Failure analysis

| Observation | What it supports | What it does not prove |
|---|---|---|
| Both cores stop in the same spinlock acquisition path | A cross-core lock wait is plausible | Which closed-source path owns regi2c |
| Failure needs modem sleep plus periodic ADC | A timing interaction is likely | That all S31 ADC reads are unsafe |
| Removing ADC sampling avoids a reset in a short test | ADC participates in the trigger | A production-safe workaround |
| Same application survives on another commit | A revision-sensitive change is plausible | That the baseline is otherwise identical |

For diagnosis only, reduce the ADC polling rate or suspend the periodic sample during Wi-Fi wake windows, and compare with WIFI_PS_NONE. If the product cannot accept that behavior, evaluate an external ADC or wait for the vendor fix. Do not promise that either diagnostic change eliminates the underlying race.

## Verification plan

- **Static:** inspect the S31 ADC change that introduced regi2c writes and document lock acquisition order from available source.
- **Host:** test the application's sampling state machine and rate limiting; this cannot emulate the closed-source PHY or silicon locks.
- **Build:** compile the exact S31 target and component versions with the production power-save and Bluetooth settings.
- **Hardware:** run the full combination for substantially longer than the reported 5–15 minute window, repeat across cold boots, and retain both-core traces and uptime.
- **Regression:** after a vendor patch, verify ADC values, Wi-Fi reconnect/wake behavior, A2DP continuity, current consumption and watchdog health together.

## Deliverables

Provide the exact S31 version tuple, configuration matrix, sampling cadence, both-core panic trace, source-level lock-order hypothesis, confidence level, upstream fix commit and hardware soak results.

## Review checklist

- [ ] ESP32-S31 is confirmed; no family-wide claim is made.
- [ ] The exact f0114250e2 and comparison commit are recorded.
- [ ] Both cores are decoded with the matching ELF.
- [ ] The closed-source PHY lock ownership is labelled as inferred.
- [ ] Diagnostic workarounds are not described as vendor fixes.
- [ ] Power consumption and ADC accuracy are re-qualified after mitigation.
- [ ] A vendor-fixed build has passed a long hardware soak.

## References and source policy

- Primary issue: https://github.com/espressif/esp-idf/issues/19433
- S31 ESP-IDF source and release notes: https://github.com/espressif/esp-idf/tree/release/v6.1
- ESP-IDF ADC oneshot API: https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s31/api-reference/peripherals/adc_oneshot.html
- Treat issue stacks as reporter evidence; do not invent internals for the closed-source PHY library.
