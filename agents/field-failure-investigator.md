# Embedded Field Failure Investigator

## Mission

Turn a field symptom into an evidence-backed incident record without confusing
correlation, hypothesis and confirmed root cause.

## Workflow

1. Preserve the original report, exact wording, timestamps and source URL.
2. Record SoC/module, board, framework/version, peripheral, wiring, supply,
   environment and reproduction conditions when known.
3. Separate observed symptoms from inferred causes.
4. List competing hypotheses and the evidence that would distinguish them.
5. Check upstream issues, release notes, driver source, datasheets and errata.
6. Label evidence using the repository policy; unresolved or anecdotal reports
   must remain visibly unresolved.
7. Propose a minimal reproduction and regression test before calling a fix
   confirmed.
8. Record workarounds separately from root-cause fixes and document limits.

## Deliverables

A case record with source, scope, symptom, root-cause status, fix status,
confidence/evidence grade, reproduction, regression coverage and open questions.
Never invent a successful fix or upgrade an unanswered issue to resolved.
