# Paper 2 R5.1 audit protocol

## Purpose
R5.1 retains the R5 study design and closes one bounded heading-only false-pass exposed during final independent checker validation.

The evidence roles remain:

1. **Current LEAP defect localization** — complete 28-dossier frozen publication build.
2. **Within-LEAP persistence/input sensitivity** — earlier 18-dossier build plus scenario/challenge configurations; not external replication.
3. **External transferability pilot** — four official FastAPI tutorial sources passed through the independently developed FastAPI/OpenAPI generator.
4. **Checker validation** — controlled positive/negative fixtures plus in-memory mutations of actual archived LEAP/FastAPI artifacts.

## Development chronology
An earlier research version used a post-hoc 11-row manual condition adjudication. The retained R3 protocol records replacement of that table with deterministic rules. Subsequent negative-control testing identified two implementation defects in the R4 checker:

- the FastAPI query source-role cell was assigned PASS without evaluating the published location/name against source expectations;
- the LEAP guard checker could accept an empty denominator and could treat the presence of the `Zero-Division Guard:` heading as sufficient even when safeguard prose contradicted the existence of handling.

R5 repaired those defects before rerunning the reported analyses; R5.1 additionally rejects heading-only safeguard text. The manual condition-adjudication table remains excluded from the released evidence.

## Shared released rule implementation
`audit_rules.py` is imported by the primary, historical, robustness, external, and validation workflows where the corresponding rule applies. It implements:

- explicit source-role/name comparison;
- nonempty denominator and guarded-variable binding;
- affirmative zero/non-positive safeguard semantics with contradictory-text rejection;
- conflict-routing checks;
- review-authority/certification checks.

## Checker-validation controls
`validate_audit_rules.py` contains 18 predeclared rule fixtures. They include:

- correct and substituted role/name examples;
- benign and defective comment-role mappings;
- correct guard disclosure;
- missing and wrong denominators;
- contradictory or explicitly disabled safeguard prose;
- correct non-positive disclosure and zero-only loss of non-positive semantics;
- preserved and suppressed conflict routing;
- unresolved clean/certified authority states;
- benign N/A controls.

`validate_mutated_artifacts.py` contains 14 artifact-derived controls: five unchanged baselines, eight substitutions of extracted inputs, and one document-level HTML mutation that replaces the safeguard sentence with a second `Zero-Division Guard:` heading and reparses the page through the production HTML adapter. Frozen source/evidence files are not modified on disk.

Expected outcomes and rationales are frozen in `CHECKER_CONTROL_ORACLE.csv` and `ARTIFACT_MUTATION_ORACLE.csv`, separate from checker output. `verify_control_oracles.py` compares those predeclared oracle tables with the emitted validation results. Across the 32 outcomes, all expected labels must match. The 30 binary PASS/FAIL controls report misses and false alarms; two additional fixtures verify N/A handling. These controls validate specified checker behavior and are not population-level sensitivity/specificity estimates.

## LEAP checklist
The four literature-grounded obligations are:

- source-role accuracy;
- condition disclosure;
- representation-disagreement preservation;
- review-authority consistency.

Repeated page occurrences are manifestations of generator/template defects, not independent scientific defects or prevalence estimates.

## External applicability rules
- Source-role accuracy compares source-declared parameter/request-body location and name with generated OpenAPI location/name.
- Condition disclosure compares source-declared validation constraints with generated OpenAPI constraints and runtime enforcement.
- Disagreement preservation is N/A when no unresolved explicit conflict exists.
- Review-authority consistency is N/A because the selected FastAPI examples expose no human review state.
- Deprecation propagation is a separately labeled lifecycle-status analogue, not a direct review-authority pass.

## Interpretation boundaries
- The earlier LEAP build is persistence evidence, not independent replication.
- Scenario/challenge configurations reproduce lineage and authority defects but not the guard-binding defect.
- The FastAPI pilot demonstrates procedural transfer for directly applicable role/condition checks; it does not estimate FastAPI defect prevalence or externally validate LEAP-specific review-authority semantics.
- Checker validation establishes behavior on specified controls, not general diagnostic accuracy.
