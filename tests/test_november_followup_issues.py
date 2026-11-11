"""Evidence contracts for the November 2026 AES-GCM, OTA, PSRAM and EAP-TLS reports."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def skill(slug):
    return (SKILLS / slug / "SKILL.md").read_text(encoding="utf-8")


class NovemberFollowupIssueTests(unittest.TestCase):
    def test_aes_gcm_skill_has_the_complete_engineering_contract(self):
        text = skill("esp32-aes-gcm-multipart-stream-integrity")
        for heading in (
            "## Purpose and decision boundary", "## Required inputs",
            "## Engineering model", "## Constraints and invariants",
            "## Failure analysis", "## Verification plan", "## Deliverables",
            "## Review checklist", "## References and source policy",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)
        self.assertGreaterEqual(len(text.splitlines()), 40)
        self.assertLessEqual(len(text.splitlines()), 120)

    def test_aes_gcm_scope_is_tied_to_v55_hardware_aes_configuration(self):
        text = skill("esp32-aes-gcm-multipart-stream-integrity")
        for token in ("release/v5.5", "v5.5.x", "CONFIG_MBEDTLS_HARDWARE_AES",
                      "ESP32-C6", "classic ESP32", "#19406"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_aes_gcm_stream_state_covers_ctr_and_ghash_partial_blocks(self):
        text = skill("esp32-aes-gcm-multipart-stream-integrity")
        for token in ("counter offset", "unused keystream bytes", "partial GHASH block",
                      "nc_off", "stream", "GHASH zero-pads"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_aes_gcm_authentication_gates_plaintext_consumption(self):
        text = skill("esp32-aes-gcm-multipart-stream-integrity")
        self.assertIn("Do not release, execute, install or persist decrypted plaintext", text)
        self.assertIn("final tag verification succeeds", text)
        self.assertIn("discard it on authentication failure", text)

    def test_aes_gcm_fix_commits_are_explicit_and_branch_scoped(self):
        text = skill("esp32-aes-gcm-multipart-stream-integrity")
        for commit in ("e6ac065424", "8767271843", "613469ffe7"):
            with self.subTest(commit=commit):
                self.assertIn(commit, text)
        self.assertIn("do not assume", text.lower())

    def test_ota_confirmation_requires_state_and_boot_partition_readback(self):
        text = skill("ota-pending-verify-rollback-qualification")
        for token in ("esp_ota_get_state_partition", "ESP_OTA_IMG_VALID",
                      "esp_ota_get_boot_partition", "ESP_OK"):
            with self.subTest(token=token):
                self.assertIn(token, text)
        self.assertIn("do not accept a later ESP_OK by itself", text)

    def test_ota_retry_report_is_bound_to_the_reported_c6_sdk_tuple(self):
        text = skill("ota-pending-verify-rollback-qualification")
        for token in ("#19413", "ESP32-C6", "v6.0.1", "de1e5035b5"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_psram_once_control_is_kept_out_of_external_ram(self):
        text = skill("psram-capability-allocation-audit")
        for token in ("pthread_once_t", "once_control", "internal DRAM",
                      "ESP32-S3", "PSRAM"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_psram_spurious_cas_failure_is_not_treated_as_completed_init(self):
        text = skill("psram-capability-allocation-audit")
        for token in ("#19411", "esp_cpu_compare_and_set", "spurious",
                      "initializer", "external_ram_cas_lock"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_eap_tls_duplicate_fragment_is_a_distinct_reassembly_case(self):
        text = skill("esp32-wifi-eap-tls-reauth-starvation")
        for token in ("#19408", "duplicate", "reassembly", "424-byte",
                      "1408-byte", "WIFI_REASON_802_1X_AUTH_FAILED"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_eap_tls_driver_stall_and_fragment_failure_are_not_assumed_same_cause(self):
        text = skill("esp32-wifi-eap-tls-reauth-starvation")
        for token in ("#19409", "887 ms", "not established", "wpa2_post"):
            with self.subTest(token=token):
                self.assertIn(token, text)
