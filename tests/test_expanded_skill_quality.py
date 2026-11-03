"""Four independent quality-contract checks per new skill: 400 unittest cases."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
NEW_SKILLS = ["board-capability-matrix","gpio-matrix-audit","peripheral-matrix-planner","pinmux-conflict-analysis","flash-psram-capacity","partition-ota-budget","iram-dram-budget","task-stack-budget","heap-fragmentation-forensics","dma-buffer-placement","psram-performance-tradeoffs","brownout-root-cause","power-rail-budget","deep-sleep-current-audit","light-sleep-wakeup-design","battery-state-estimation","charger-powerpath-review","thermal-derating-review","wifi-event-state-machine","wifi-roaming-policy","wifi-throughput-diagnostics","wifi-coexistence-analysis","wifi-enterprise-eap-review","wifi-provisioning-ux","ble-gatt-contract-review","ble-pairing-security","ble-throughput-latency","esp-now-reliability","ethernet-rmii-clock-review","ethernet-link-recovery","lora-link-budget","lorawan-device-lifecycle","subghz-regulatory-check","mqtt-session-recovery","mqtt-topic-acl-design","mqtt-payload-schema","tls-trust-anchor-rotation","http-client-resilience","dns-failure-diagnostics","ntp-time-bootstrap","rtc-drift-calibration","uart-framing-hardening","spi-signal-integrity","i2c-electrical-budget","i2c-multi-master-review","i2c-device-discovery","can-twai-bus-off-recovery","canopen-node-commissioning","modbus-register-contract","modbus-rtu-timing","modbus-tcp-hardening","rs485-termination-bias","rs485-direction-timing","opcua-gateway-boundary","canopen-safety-boundary","industrial-watchdog-policy","fail-safe-output-state","relay-inductive-load-review","motor-control-mcpwm-review","encoder-pcnt-validation","adc-calibration-linearity","dac-output-accuracy","touch-sensor-drift","load-cell-noise-budget","thermocouple-cold-junction","rtd-lead-compensation","pressure-sensor-compensation","imu-calibration-frame","sensor-fusion-timestamping","camera-framebuffer-budget","jpeg-streaming-backpressure","i2s-audio-clock-budget","audio-buffer-underrun","lvgl-rendering-budget","display-tearing-sync","usb-otg-role-review","usb-serial-jtag-debug","sd-card-filesystem-integrity","littlefs-wear-budget","nvs-schema-migration","configuration-transactionality","ota-image-compatibility","ota-power-loss-matrix","secure-boot-key-lifecycle","flash-encryption-production","anti-rollback-policy","device-identity-provisioning","secret-leakage-audit","firmware-sbom-generation","reproducible-firmware-build","firmware-provenance-attestation","dependency-vulnerability-triage","secure-debug-port-policy","threat-model-device-lifecycle","protocol-parser-fuzzing","modbus-conformance-testing","mqtt-conformance-testing","ble-gatt-regression","fault-injection-network","fault-injection-power"]

def read_skill(skill_id):
    path = ROOT / "skills" / skill_id / "SKILL.md"
    return path, path.read_text(encoding="utf-8")

def make_test(skill_id, check):
    def test(self):
        path, content = read_skill(skill_id)
        if check == "frontmatter":
            self.assertTrue(content.startswith("---\n"), path)
            self.assertRegex(content, r"(?m)^name: " + re.escape(skill_id) + r"$")
            self.assertIn("description:", content.split("---", 2)[1])
        elif check == "engineering_sections":
            for heading in ("## Purpose", "## Required context", "## Procedure",
                            "## Domain checklist", "## Deliverable", "## References"):
                with self.subTest(heading=heading):
                    self.assertIn(heading, content)
            self.assertGreaterEqual(len(re.findall(r"(?m)^[0-9]+[.] ", content)), 8)
        elif check == "safety_contract":
            for phrase in ("Never invent GPIO capabilities",
                           "Never disable brownout detection",
                           "Never treat an ESP32 as a safety-rated controller",
                           "A successful build does not prove"):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, content)
        elif check == "validation_and_evidence":
            for phrase in ("## Validation matrix", "Static", "Host", "Build",
                           "Hardware", "docs.espressif.com", "technical-documents"):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, content)

    return test

class ExpandedSkillQualityTests(unittest.TestCase):
    pass

for _skill in NEW_SKILLS:
    for _check in ("frontmatter", "engineering_sections", "safety_contract",
                   "validation_and_evidence"):
        _name = "test_%s_%s" % (_skill.replace("-", "_"), _check)
        setattr(ExpandedSkillQualityTests, _name, make_test(_skill, _check))

if __name__ == "__main__":
    unittest.main()
