"""Evidence contracts for November 18, 2026 reset, SMP, ADC and radio findings."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def read_skill(slug):
    return (SKILLS / slug / "SKILL.md").read_text(encoding="utf-8")


class NovemberRuntimeFindingTests(unittest.TestCase):
    def test_c6_ecc_skill_has_complete_engineering_contract(self):
        text = read_skill("esp32-c6-ecc-reset-power-state-audit")
        for heading in (
            "## Purpose and decision boundary", "## Required inputs",
            "## Engineering model", "## Constraints and invariants",
            "## Failure analysis", "## Verification plan", "## Deliverables",
            "## Review checklist", "## References and source policy",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)
        self.assertGreater(len(text), 3000)
        self.assertGreaterEqual(len(text.splitlines()), 40)
        self.assertLessEqual(len(text.splitlines()), 120)

    def test_c6_ecc_scope_is_bound_to_reported_rom_and_sdk_tuple(self):
        text = read_skill("esp32-c6-ecc-reset-power-state-audit")
        for token in (
            "issues/19421", "ESP32-C6", "revision v0.2", "esp32c6-20220919",
            "fff9895", "CONFIG_SECURE_BOOT_V2_ENABLED",
            "CONFIG_SECURE_SIGNED_APPS_ECDSA_V2_SCHEME",
            "CONFIG_MBEDTLS_HARDWARE_ECC",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_c6_ecc_failure_distinguishes_software_reset_from_power_on(self):
        text = read_skill("esp32-c6-ecc-reset-power-state-audit")
        for token in (
            "PCR_ECC_MEM_PD", "PCR_ECC_MEM_FORCE_PU",
            "esp_system_reset_modules_on_exit", "esp_restart_noos",
            "USB-Serial-JTAG reset", "power-on",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_c6_ecc_workaround_and_efuse_operations_are_safely_scoped(self):
        text = read_skill("esp32-c6-ecc-reset-power-state-audit")
        self.assertIn("linker wrapper", text)
        self.assertIn("not a supported cross-target recipe", text)
        self.assertIn("Secure Boot eFuse programming is irreversible", text)
        self.assertIn("Do not generalize", text)

    def test_s31_adc_phy_skill_has_complete_engineering_contract(self):
        text = read_skill("esp32-s31-adc-phy-lock-order-audit")
        for heading in (
            "## Purpose and decision boundary", "## Required inputs",
            "## Engineering model", "## Constraints and invariants",
            "## Failure analysis", "## Verification plan", "## Deliverables",
            "## Review checklist", "## References and source policy",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)
        self.assertGreater(len(text), 3000)
        self.assertGreaterEqual(len(text.splitlines()), 40)
        self.assertLessEqual(len(text.splitlines()), 120)

    def test_s31_adc_phy_trigger_and_commit_are_exact(self):
        text = read_skill("esp32-s31-adc-phy-lock-order-audit")
        for token in (
            "issues/19433", "ESP32-S31 Korvo-1", "f0114250e2",
            "9a97f6c54e", "WIFI_PS_MAX_MODEM", "A2DP",
            "ADC_ATTEN_DB_0", "5–15 minutes",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_s31_lock_cycle_keeps_closed_source_uncertainty_explicit(self):
        text = read_skill("esp32-s31-adc-phy-lock-order-audit")
        for token in (
            "rtc_spinlock", "regi2c", "REGI2C_WRITE_MASK",
            "temp_sensor_get_raw_value", "closed-source",
            "not a fully proven vendor root cause",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_s31_skill_does_not_recommend_disabling_watchdog_or_manipulating_locks(self):
        text = read_skill("esp32-s31-adc-phy-lock-order-audit")
        self.assertIn("Never acquire or release internal RTC/regi2c locks directly", text)
        self.assertIn("Do not disable the interrupt watchdog", text)
        self.assertIn("not vendor fixes", text)

    def test_multicore_skill_covers_cross_core_notification_pending_ready_list(self):
        text = read_skill("esp32-multicore-and-ipc")
        for token in (
            "#19450", "release/v5.5", "xPendingReadyList[xCurCoreID]",
            "xTaskResumeAll()", "vTaskNotifyGiveFromISR()",
            "49,994 µs", "#19451", "7266fdc", "19–20 per 2 s", "1,530 µs",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_multicore_skill_covers_ipc_stall_during_flash_read(self):
        text = read_skill("esp32-multicore-and-ipc")
        for token in (
            "#19456", "v6.3-dev", "v5.3", "v5.2.2",
            "esp_partition_read()", "esp_ipc_call(1, ...)",
            "1 kHz", "all timer callbacks stop", "#19457", "dfaa88f", "59,001 IPC calls", "Neither was merged",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_ota_power_loss_skill_covers_failed_erase_cleanup(self):
        text = read_skill("esp32-ota-power-loss-matrix")
        for token in (
            "#19439", "esp_ota_begin()", "ESP_ERR_OTA_ALREADY_IN_PROGRESS",
            "esp_partition_erase_range()", "dangerous write protection",
            "only after erase succeeds", "QEMU", "c1d1695", "multi-stage reset cases were not run",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_adc_skill_covers_s3_oneshot_pad_release_report_without_overclaiming(self):
        text = read_skill("esp32-adc-and-sensors")
        for token in (
            "#19442", "ESP32-S3 revision 2", "sar1_en_pad",
            "47 kΩ / 100 kΩ", "about 1 V",
            "suspected explanation", "not yet a confirmed vendor root cause",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)
        self.assertIn("universal supported API", text)

    def test_c6_802154_skill_covers_long_run_tx_done_assertion(self):
        text = read_skill("esp32-c6-wifi-ble-802154-coexistence")
        for token in (
            "#19425", "100 CSL children", "esp_ieee802154_transmit_done()",
            "s_transmit_psdu", "interrupt watchdog", "no standalone minimal reproducer",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)
        self.assertIn("Do not add blocking logs", text)

    def test_ble_backpressure_skill_covers_persistent_controller_failure_after_dma_oom(self):
        text = read_skill("esp32-ble-notification-backpressure")
        for token in (
            "#19461", "MALLOC_CAP_INTERNAL|MALLOC_CAP_DMA",
            "BLE_INIT: Malloc failed", "ble_gatts_notify_custom()",
            "roughly 40 KB", "no standalone example yet",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)
        self.assertIn("does not recover a controller", text)

    def test_manifests_catalog_and_version_register_the_two_new_skills(self):
        manifest = (ROOT / "agent.yaml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        plugin = (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        marketplace = (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(version, "1.8.0")
        for slug in (
            "esp32-c6-ecc-reset-power-state-audit",
            "esp32-s31-adc-phy-lock-order-audit",
        ):
            with self.subTest(slug=slug):
                self.assertIn("  - " + slug, manifest)
                self.assertIn(slug, readme)
        self.assertIn('"version": "1.8.0"', plugin)
        self.assertIn('"version": "1.8.0"', marketplace)
        self.assertIn("661 skills", manifest)


if __name__ == "__main__":
    unittest.main()
