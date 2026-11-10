"""Regression contracts for the November 2026 issue-driven skill wave.

Four independent checks per skill: metadata/size, required engineering structure,
topic-specific source traceability, and safety/evidence requirements.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
ISSUE_SKILLS = [
    "esp32-psram-stack-flash-boundary",
    "esp32-flash-cache-disabled-isr-audit",
    "esp32-wear-leveling-page-boundary-integrity",
    "esp32-esp-timer-isr-task-race-audit",
    "esp32-tls-nonblocking-select-recovery",
    "esp32-c5-psram-crypto-alignment-qualification",
    "esp32-c5-reset-psram-ota-rollback-interaction",
    "esp32-wifi-eap-tls-reauth-starvation",
    "esp32-espnow-tx-queue-ownership",
    "esp32-sdmmc-host-lifecycle-lock-order",
    "esp32-rgb-panel-bounce-buffer-recovery",
    "esp32-security-advisory-version-triage"
]

SOURCE_HINTS = {
    "esp32-psram-stack-flash-boundary": "external-ram.html",
    "esp32-flash-cache-disabled-isr-audit": "fatal-errors.html",
    "esp32-wear-leveling-page-boundary-integrity": "19403",
    "esp32-esp-timer-isr-task-race-audit": "19400",
    "esp32-tls-nonblocking-select-recovery": "19378",
    "esp32-c5-psram-crypto-alignment-qualification": "AR2025-008",
    "esp32-c5-reset-psram-ota-rollback-interaction": "AR2025-008",
    "esp32-wifi-eap-tls-reauth-starvation": "19409",
    "esp32-espnow-tx-queue-ownership": "19405",
    "esp32-sdmmc-host-lifecycle-lock-order": "19402",
    "esp32-rgb-panel-bounce-buffer-recovery": "19395",
    "esp32-security-advisory-version-triage": "security/advisories",
}

def read_skill(slug):
    return (SKILLS / slug / "SKILL.md").read_text(encoding="utf-8")

class NovemberIssueWaveQualityTests(unittest.TestCase):
    def assert_contract(self, slug, contract):
        text = read_skill(slug)
        if contract == "metadata":
            match = re.match(r"^---\\n(.*?)\\n---\\n", text, re.S)
            self.assertIsNotNone(match, slug)
            self.assertIn("name: " + slug, match.group(1))
            self.assertIn("description: Use when ", match.group(1))
            self.assertIn("license: MIT", match.group(1))
            self.assertGreaterEqual(len(text), 3000, slug)
            self.assertGreaterEqual(len(text.splitlines()), 40, slug)
            self.assertLessEqual(len(text.splitlines()), 120, slug)
            self.assertTrue((SKILLS / slug / "LICENSE.txt").is_file(), slug)
        elif contract == "structure":
            for heading in ("## Purpose and decision boundary", "## Required inputs",
                            "## Engineering model", "## Constraints and invariants",
                            "## Failure analysis", "## Verification plan",
                            "## Deliverables", "## Review checklist",
                            "## References and source policy"):
                with self.subTest(slug=slug, heading=heading):
                    self.assertIn(heading, text)
        elif contract == "source":
            self.assertIn(SOURCE_HINTS[slug], text, slug)
            self.assertIn("Primary topic reference:", text, slug)
            self.assertIn("unknown", text.lower(), slug)
            self.assertIn("affected", text.lower(), slug)
        elif contract == "safety":
            for phrase in ("Never disable brownout detection",
                           "Never treat an ESP32 as a safety-rated controller",
                           "A successful build does not prove",
                           "pass/fail"):
                with self.subTest(slug=slug, phrase=phrase):
                    self.assertIn(phrase.lower(), text.lower())

for _slug in ISSUE_SKILLS:
    for _contract in ("metadata", "structure", "source", "safety"):
        def _test(self, slug=_slug, contract=_contract):
            self.assert_contract(slug, contract)
        _test.__name__ = "test_%s_%s" % (_slug.replace("-", "_"), _contract)
        setattr(NovemberIssueWaveQualityTests, _test.__name__, _test)

if __name__ == "__main__":
    unittest.main()
