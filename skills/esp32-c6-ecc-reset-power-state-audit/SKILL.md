---
name: esp32-c6-ecc-reset-power-state-audit
description: Use when ESP32-C6 Secure Boot V2 ECDSA verification fails after esp_restart() or a panic/watchdog reset following hardware ECC use; qualify reset class, ECC power-domain state and recovery evidence.
license: MIT
version: "1.0.0"
---

# ESP32-C6 ECC reset power-state audit

## Purpose and decision boundary

Investigate a narrowly scoped reset-path failure: after an application performs a hardware ECC operation, a CPU-level software reset may leave the ESP32-C6 ECC memory power state unsuitable for the ROM's next Secure Boot V2 ECDSA verification. This is not a general secure-boot provisioning guide and is not evidence that all C6 revisions or other SoCs are affected.

Treat the issue report as a strong, device-tested C6 observation, not yet as a vendor-confirmed defect. The upstream issue was open and assigned for investigation on 2026-11-16.

## Required inputs

Collect the exact ESP32-C6 ordering code and silicon revision; module and board; ROM build string; ESP-IDF commit and component revisions; bootloader and application hashes; Secure Boot V2 mode (CONFIG_SECURE_BOOT_V2_ENABLED); ECDSA scheme (CONFIG_SECURE_SIGNED_APPS_ECDSA_V2_SCHEME); flash-encryption mode; eFuse state; sdkconfig; hardware-ECC configuration; the exact PSA/mbedTLS operations before reset; reset reason; and the complete ROM boot log.

For the reported reproduction, the tuple was ESP32-C6 QFN32 revision v0.2 on ESP32-C6-DevKitM-1, ROM esp32c6-20220919, ESP-IDF v6.1 commit fff9895, Secure Boot V2, ECDSA P-256 signed apps, release-mode flash encryption and CONFIG_MBEDTLS_HARDWARE_ECC enabled.

## Engineering model

### Failure signature and reported mechanism

The reported sequence imports a P-256 public key with psa_import_key(), verifies a SHA-256 ECDSA signature with psa_verify_hash(), then calls esp_restart(). The ECC driver calls ecc_ll_power_down(), which sets PCR_ECC_MEM_PD and clears PCR_ECC_MEM_FORCE_PU.

The report traces esp_system_reset_modules_on_exit() as clearing PCR_ECC_MEM_FORCE_PD without restoring the ECC memory reset state. esp_restart_noos() then performs a CPU-level software reset that does not reset those PCR bits. ROM ets_ecdsa_verify consequently runs with ECC memory still powered down and prints “Valid secure boot key blocks: 0” / “Signature Check Failed”.

This register-path explanation is the reporter's source analysis. The issue had not yet received a public maintainer root-cause confirmation at the time of this review.

### Investigation sequence

1. Freeze the full target/version tuple and preserve the signed bootloader, application ELF, map file, boot log and reset reason.
2. Confirm that Secure Boot V2 ECDSA P-256 and release flash encryption are actually enabled; do not infer them from a project label.
3. Record every hardware ECC operation before the failing reset, including PSA key import, signature verification and any direct ECC HAL use.
4. Compare a cold power-on, USB-Serial-JTAG reset, ordinary esp_restart(), panic/watchdog reset and a reset that is known to reset the system power-control registers.
5. Reproduce on a disposable C6 board only. Secure Boot eFuse programming is irreversible; never burn production eFuses to test a suspected reset bug.
6. Inspect the exact C6 reset-module code and ECC power-control register definitions from the matching ESP-IDF commit. Do not copy register names or bit masks to another target.
7. Re-check the upstream issue and release notes for a vendor patch before selecting a production mitigation.

## Constraints and invariants

- ROM signature verification must succeed on every supported reset path, not only after power-on.
- Do not weaken Secure Boot, flash encryption, signature checks or watchdogs to make the reset appear successful.
- Do not modify eFuses, secure-boot key blocks or flash-encryption state as a diagnostic shortcut.
- Do not generalize the C6 observation to C5, C61, H2, H21 or P4. The reporter noted similar source patterns on some of those targets but explicitly tested only C6.
- A software reset that fails before the application starts is a boot-chain failure; an application task cannot recover it after the fact.
- Keep ROM logs and reset-class evidence separate from application-level log messages.

## Failure analysis

| Observation | Interpretation | Next check |
|---|---|---|
| Failure only after hardware ECC plus esp_restart() | Consistent with the reported C6 path | Compare PCR state and matching reset code |
| Cold power-on succeeds | Does not disprove a retained-state reset defect | Repeat after ECC and software reset |
| USB-Serial-JTAG reset succeeds | Indicates reset class changes the retained state | Record reset reason and compare reset domains |
| Failure without any ECC operation | Not the reported trigger | Investigate signature, eFuse, flash and image integrity independently |

A reporter-verified application workaround wraps esp_rom_software_reset_cpu with an IRAM linker wrapper that restores the C6 ECC memory power-control bits before calling the ROM reset. This is a low-level, target-specific workaround, not a supported cross-target recipe. Do not ship it without review against the exact register definitions, ROM reset path and an Espressif-provided fix or explicit engineering approval.

## Verification plan

- **Static:** verify the exact C6 register definitions, reset function and ECC power-down path at the pinned commit.
- **Host:** test reset-state decision logic and log classification; host tests cannot validate PCR retention or ROM behavior.
- **Build:** compile the exact Secure Boot V2 ECDSA configuration and preserve bootloader/application hashes.
- **Hardware:** on a sacrificial C6 revision-v0.2 board, run ECC then each reset class repeatedly; require ROM signature verification success and record reset reason, ROM log and PCR state where safely observable.
- **Release:** repeat with the final signed and encrypted production-equivalent image. A successful build or one successful reboot is not qualification.

## Deliverables

Return the exact target and firmware tuple, reset-class matrix, ECC operations performed, raw ROM logs, register/source evidence, confidence level, upstream fix status, any workaround approval and the remaining hardware-only tests.

## Review checklist

- [ ] Secure Boot and flash-encryption configuration is recorded, not assumed.
- [ ] eFuse operations were restricted to an approved disposable test device.
- [ ] The failing and successful reset classes were compared.
- [ ] C6-only evidence was not generalized to another SoC.
- [ ] The reporter workaround is labelled as invasive and unverified outside its exact board.
- [ ] No integrity or watchdog protection was disabled.
- [ ] Final signed-image reset testing is still required on hardware.

## References and source policy

- Primary issue: https://github.com/espressif/esp-idf/issues/19421
- ESP-IDF system restart implementation: https://github.com/espressif/esp-idf/tree/v6.1/components/esp_system
- ESP-IDF security and bootloader documentation: https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32c6/security/
- Use the exact silicon datasheet and technical reference manual for the selected C6 revision. An open issue is evidence of a reported condition, not proof that every release is affected.
