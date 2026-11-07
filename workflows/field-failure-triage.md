# Workflow: Field Failure Triage

1. Capture the original symptom and preserve logs before changing firmware.
2. Record board/SoC, firmware commit, framework version, power source, wiring,
   peripheral and environment.
3. Establish frequency, timing, last-known-good version and reproduction rate.
4. Separate facts, hypotheses and user workarounds.
5. Search the casebook and relevant upstream sources; preserve issue status.
6. Design the smallest reproduction and one-variable-at-a-time experiments.
7. Add a regression test for the confirmed behavior.
8. Update the field case with evidence grade, exact fix scope and unresolved
   questions.

Do not label an incident fixed until the reproduction fails on the old behavior
and passes with the proposed change under documented conditions.
