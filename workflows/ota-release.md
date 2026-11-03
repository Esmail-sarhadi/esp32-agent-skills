# Workflow: ESP32 OTA Release Readiness

1. Identify target SoC, bootloader/partition layout and current deployed image.
2. Validate partition offsets, sizes, alignment and flash capacity.
3. Define image compatibility, signing/authentication and version policy.
4. Verify rollback and anti-rollback behavior against the product threat model.
5. Test interrupted download, interrupted flash, reset during boot and low
   power; confirm recovery behavior.
6. Confirm credentials and trust anchors are not embedded in public examples.
7. Build release artifacts reproducibly and retain checksums and provenance.
8. Test upgrade and downgrade policy on named hardware before production rollout.

A successful CI build does not prove OTA recovery, signature enforcement or
power-loss safety on hardware.
