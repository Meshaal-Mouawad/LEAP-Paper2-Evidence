# Reviewer evidence supplement — Paper 2 JSS R5.1

This archive reproduces the results in **From Source Linkage to Explanation Fidelity: An Executable Audit of Enterprise KPI Knowledge Publication**.

## 1. Checker validation and chronology
`method/AUDIT_PROTOCOL_R5.md` records the rule-development chronology, the two earlier false-pass behaviors, and the final heading-only regression closed in R5.1 before the release rerun.

`method/audit_rules.py` contains the shared released predicates. Expected labels and rationales are frozen separately in `method/CHECKER_CONTROL_ORACLE.csv` and `method/ARTIFACT_MUTATION_ORACLE.csv`. `method/validate_audit_rules.py` executes 18 rule fixtures. `method/validate_mutated_artifacts.py` executes 14 artifact-derived controls: five unchanged baselines, eight substitutions of extracted inputs, and one document-level HTML mutation reparsed through the production adapter. `method/verify_control_oracles.py` independently compares emitted outcomes with the predeclared oracle tables. Across all 32 expected outcomes, the released checker must match every label. The 30 binary controls report misses and false alarms; the N/A controls verify applicability handling. These controls validate specified implementation behavior, not population-level diagnostic accuracy.

## 2. Current LEAP corpus
`primary/artifact_28/dossiers/` contains the complete 28 rendered dossier pages used for the current-build audit. `primary/audit/` contains the deterministic scanner output, guard inventory, lineage findings, defect-class summary, compact dossier-by-obligation matrix, and root-cause source excerpts.

## 3. Earlier LEAP state
`historical/dossiers/` contains the separately archived 18-dossier build. It is treated as temporal persistence of shared project cases, not independent replication. `historical/audit/` contains the reproduced audit outputs using the repaired shared guard/routing/authority predicates.

## 4. LEAP input-sensitivity checks
`robustness/` contains the scenario and challenge configurations. They reproduce the lineage and authority defects; their eligible zero guards are communicated correctly, so they do **not** reproduce the guard-binding defect.

## 5. External FastAPI/OpenAPI transferability pilot
`external_fastapi/` contains:

- four official FastAPI tutorial source files frozen from `fastapi/fastapi` commit `33d411dbc3236275dd64d200bfe18d5d60a49b2e`;
- upstream Git blob identities and local SHA-256 identities;
- OpenAPI descriptions generated with FastAPI 0.128.2 / Pydantic 2.13.4;
- source-to-generated role/name and constraint comparisons;
- two role/name negative controls;
- direct checklist results and separately labeled lifecycle-status analogues;
- runtime validation outcomes;
- a rerunnable `generate_and_audit.py` and requirements file.

Direct external result after checker repair: **7 applicable checks, 7 passes, 0 failures, 9 N/A cells**. Two deprecation-status analogues also pass. Representation-disagreement and exact review-authority checks are N/A in this selected external corpus and are not relabeled as passes.

## 6. Detailed cases
`detailed_cases/` retains the Yield and Gross Margin source files and public-source hash verification.

## 7. Study-boundary record
`method/COMPANION_RESULT_OVERLAP.md` states which frozen technical observations are reused from the companion LEAP study and which results are specific to Paper 2.

## 8. Reproduction
From the supplement root, run:

```bash
python method/validate_audit_rules.py
python method/validate_mutated_artifacts.py
python method/verify_control_oracles.py
python primary/audit/audit_primary_r3.py
python historical/audit/audit_historical_r3.py historical/dossiers historical/audit
python robustness/audit/audit_replication_r3.py robustness/scenarios robustness/audit scenarios
python robustness/audit/audit_replication_r3.py robustness/challenge robustness/audit challenge
python external_fastapi/generate_and_audit.py
python verification/verify_r5_evidence.py
python verification/verify_release_evidence.py
```

The inherited `r3` suffix on some LEAP audit script names records provenance. R5.1 retains the validated shared checker, closes the final heading-only false pass, and regenerates all affected outputs rather than silently preserving the earlier predicate defect.
