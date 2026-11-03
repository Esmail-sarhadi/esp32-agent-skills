"""Four independent quality-contract checks per new skill: 400 unittest cases."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
NEW_SKILLS = ["esp32-board-capability-matrix","esp32-gpio-matrix-audit","esp32-peripheral-matrix-planner","esp32-pinmux-conflict-analysis","esp32-flash-psram-capacity","esp32-partition-ota-budget","esp32-iram-dram-budget","esp32-task-stack-budget","esp32-heap-fragmentation-forensics","esp32-dma-buffer-placement","esp32-psram-performance-tradeoffs","esp32-brownout-root-cause","esp32-power-rail-budget","esp32-deep-sleep-current-audit","esp32-light-sleep-wakeup-design","esp32-battery-state-estimation","esp32-charger-powerpath-review","esp32-thermal-derating-review","esp32-wifi-event-state-machine","esp32-wifi-roaming-policy","esp32-wifi-throughput-diagnostics","esp32-wifi-coexistence-analysis","esp32-wifi-enterprise-eap-review","esp32-wifi-provisioning-ux","esp32-ble-gatt-contract-review","esp32-ble-pairing-security","esp32-ble-throughput-latency","esp32-esp-now-reliability","esp32-ethernet-rmii-clock-review","esp32-ethernet-link-recovery","esp32-lora-link-budget","esp32-lorawan-device-lifecycle","esp32-subghz-regulatory-check","esp32-mqtt-session-recovery","esp32-mqtt-topic-acl-design","esp32-mqtt-payload-schema","esp32-tls-trust-anchor-rotation","esp32-http-client-resilience","esp32-dns-failure-diagnostics","esp32-ntp-time-bootstrap","esp32-rtc-drift-calibration","esp32-uart-framing-hardening","esp32-spi-signal-integrity","esp32-i2c-electrical-budget","esp32-i2c-multi-master-review","esp32-i2c-device-discovery","esp32-can-twai-bus-off-recovery","esp32-canopen-node-commissioning","esp32-modbus-register-contract","esp32-modbus-rtu-timing","esp32-modbus-tcp-hardening","esp32-rs485-termination-bias","esp32-rs485-direction-timing","esp32-opcua-gateway-boundary","esp32-canopen-safety-boundary","esp32-industrial-watchdog-policy","esp32-fail-safe-output-state","esp32-relay-inductive-load-review","esp32-motor-control-mcpwm-review","esp32-encoder-pcnt-validation","esp32-adc-calibration-linearity","esp32-dac-output-accuracy","esp32-touch-sensor-drift","esp32-load-cell-noise-budget","esp32-thermocouple-cold-junction","esp32-rtd-lead-compensation","esp32-pressure-sensor-compensation","esp32-imu-calibration-frame","esp32-sensor-fusion-timestamping","esp32-camera-framebuffer-budget","esp32-jpeg-streaming-backpressure","esp32-i2s-audio-clock-budget","esp32-audio-buffer-underrun","esp32-lvgl-rendering-budget","esp32-display-tearing-sync","esp32-usb-otg-role-review","esp32-usb-serial-jtag-debug","esp32-sd-card-filesystem-integrity","esp32-littlefs-wear-budget","esp32-nvs-schema-migration","esp32-configuration-transactionality","esp32-ota-image-compatibility","esp32-ota-power-loss-matrix","esp32-secure-boot-key-lifecycle","esp32-flash-encryption-production","esp32-anti-rollback-policy","esp32-device-identity-provisioning","esp32-secret-leakage-audit","esp32-firmware-sbom-generation","esp32-reproducible-firmware-build","esp32-firmware-provenance-attestation","esp32-dependency-vulnerability-triage","esp32-secure-debug-port-policy","esp32-threat-model-device-lifecycle","esp32-protocol-parser-fuzzing","esp32-modbus-conformance-testing","esp32-mqtt-conformance-testing","esp32-ble-gatt-regression","esp32-fault-injection-network","esp32-fault-injection-power"]

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
