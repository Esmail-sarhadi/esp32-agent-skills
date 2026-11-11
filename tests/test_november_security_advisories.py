"""Regression contracts for November 2026 ESP-TEE, lwIP DNS and BLE Mesh advisories."""

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def read(path):
    return path.read_text(encoding="utf-8")


def skill(slug):
    return read(SKILLS / slug / "SKILL.md")


class NovemberSecurityAdvisoryTests(unittest.TestCase):
    def test_tee_skill_has_complete_engineering_contract(self):
        text = skill("esp32-tee-privilege-switch-boundary-audit")
        for heading in (
            "## Purpose and decision boundary", "## Required inputs",
            "## Engineering model", "## Design and investigation sequence",
            "## Constraints and invariants", "## Failure analysis",
            "## Verification plan", "## Deliverables", "## Review checklist",
            "## References and source policy",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)
        self.assertGreater(len(text), 3000)
        self.assertGreaterEqual(len(text.splitlines()), 40)
        self.assertLessEqual(len(text.splitlines()), 140)
        self.assertIn("name: esp32-tee-privilege-switch-boundary-audit", text)

    def test_tee_advisory_version_scope_and_branch_fixes_are_explicit(self):
        text = skill("esp32-tee-privilege-switch-boundary-audit")
        for token in (
            "GHSA-49x8-xqjg-2pjg", "CVE-2026-113780", "Critical severity (CVSS 9.3)",
            "ESP32-C5", "ESP32-C6", "ESP32-C61", "ESP32-H2",
            "v5.5.5", "v6.0.3", "v6.1", "v5.5.6", "v6.0.4", "v6.1.1",
            "acb7d99", "773761a", "b85a7b0", "dabd37f",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tee_pointer_is_validated_before_both_context_save_paths(self):
        text = skill("esp32-tee-privilege-switch-boundary-audit")
        for token in (
            "user ecall path", "interrupt entry path", "before any store",
            "overflow-safe range arithmetic", "entire frame",
            "TEE-exclusive memory", "fail closed",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tee_threat_model_does_not_claim_remote_exploitability(self):
        text = skill("esp32-tee-privilege-switch-boundary-audit")
        self.assertIn("local code execution in the REE", text)
        self.assertIn("not, by itself, a remote network entry point", text)
        self.assertIn("ESP-TEE component and secure-service trap path are present and reachable", text)
        self.assertIn("There is no runtime workaround", text)

    def test_dns_skill_has_complete_engineering_contract(self):
        text = skill("esp32-lwip-dns-cache-multi-address-bounds")
        for heading in (
            "## Purpose and decision boundary", "## Required inputs",
            "## Engineering model", "## Design and investigation sequence",
            "## Constraints and invariants", "## Failure analysis",
            "## Verification plan", "## Deliverables", "## Review checklist",
            "## References and source policy",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)
        self.assertGreater(len(text), 3000)
        self.assertGreaterEqual(len(text.splitlines()), 40)
        self.assertLessEqual(len(text.splitlines()), 140)

    def test_dns_advisory_preconditions_and_release_matrix_are_version_scoped(self):
        text = skill("esp32-lwip-dns-cache-multi-address-bounds")
        for token in (
            "GHSA-ch63-jxm5-vmvf", "CVE-2026-113783", "High severity (CVSS 7.4)",
            "CONFIG_LWIP_DNS_MAX_HOST_IP greater than one",
            "v5.2.3 through v5.2.8", "v5.3.2 through v5.3.6",
            "v5.4.0 through v5.4.4", "v5.5.0 through v5.5.5",
            "v6.0.0 through v6.0.2", "v5.5.6", "v6.0.3",
            "v5.2 branch has reached end of life",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_dns_cache_hit_and_single_address_buffer_contract_are_distinct(self):
        text = skill("esp32-lwip-dns-cache-multi-address-bounds")
        for token in (
            "first DNS resolution", "later lookup served from the cache",
            "dns_gethostbyname()", "dns_gethostbyname_addrtype()",
            "single ip_addr_t output buffer", "explicit caller capacity",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_dns_stack_protection_is_not_misrepresented_as_a_fix(self):
        text = skill("esp32-lwip-dns-cache-multi-address-bounds")
        self.assertIn("Stack smashing protection detects some corruptions but does not prevent the out-of-bounds write", text)
        self.assertIn("it is not a fix", text)
        self.assertIn("Keep CONFIG_LWIP_DNS_MAX_HOST_IP at one", text)

    def test_ble_mesh_advisory_is_scoped_to_bluedroid_and_gatt_bearers(self):
        text = skill("esp32-ble-malformed-packet-hardening")
        for token in (
            "GHSA-rjvf-fxv5-x87j", "CVE-2026-113781",
            "CONFIG_BT_BLUEDROID_ENABLED", "PB-GATT", "GATT Proxy",
            "NimBLE does not use this path", "v6.1+", "negative ATT error",
            "unsigned 16-bit length",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_advisory_triage_covers_tee_dns_ble_mesh_and_thread_border_router(self):
        text = skill("esp32-security-advisory-version-triage")
        for token in (
            "GHSA-49x8-xqjg-2pjg", "GHSA-ch63-jxm5-vmvf",
            "GHSA-rjvf-fxv5-x87j", "GHSA-c26h-gm53-qg83",
            "CONFIG_LWIP_DNS_MAX_HOST_IP", "CONFIG_OPENTHREAD_BORDER_ROUTER",
            "v6.0.4", "v6.1.1",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_manifests_and_readme_catalog_register_both_new_skills(self):
        manifest = read(ROOT / "agent.yaml")
        readme = read(ROOT / "README.md")
        for slug in (
            "esp32-tee-privilege-switch-boundary-audit",
            "esp32-lwip-dns-cache-multi-address-bounds",
        ):
            with self.subTest(slug=slug):
                self.assertIn("  - " + slug, manifest)
                self.assertIn("| `" + slug + "` |", readme)
        self.assertIn('version: "1.7.0"', manifest)
        self.assertIn("659 skills", manifest)

    def test_research_records_issue_19415_and_current_ecosystem_limits(self):
        text = read(ROOT / "docs" / "research" / "field-issue-patterns.md")
        for token in (
            "ESP-IDF #19415", "2026-11-11", "PlatformIO platform-espressif32 v8.0.0",
            "Arduino-ESP32 #13096", "GHSA-49x8-xqjg-2pjg",
            "GHSA-ch63-jxm5-vmvf", "No Google search-volume",
            "not a maintainer-confirmed regression",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
