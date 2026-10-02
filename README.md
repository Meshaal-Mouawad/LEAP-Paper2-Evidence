# From Source Linkage to Explanation Fidelity

## JSS research artifact

This repository is the research-artifact release accompanying the manuscript:

**From Source Linkage to Explanation Fidelity: An Executable Audit of Enterprise KPI Knowledge Publication**

Author: **Meshaal Obaid Mouawad**
Department of Electrical and Computer Engineering, Mississippi State University
ORCID: 0000-0002-1152-8324

This repository is prepared for submission to the **Journal of Systems and Software (JSS)**. It contains the frozen manuscript identity and the complete reproducibility/evidence archive supporting the reported results.

## Repository structure

- `manuscript/` — final JSS manuscript PDF.
- `Supplementary_Evidence_JSS_FINAL.zip` — exact supplementary archive submitted with the manuscript.
- `supplement/` — browseable extraction of that exact supplementary archive.
- `RELEASE_IDENTITY.txt` — SHA-256 identities for the frozen submission artifacts.

The extracted `supplement/` directory is intentionally preserved byte-for-byte from the submitted supplementary archive. Internal protocol filenames and historical revision labels are retained as provenance and are not separate manuscript versions.

## Reported study

The study evaluates four bounded publication obligations:

1. source-role accuracy;
2. condition disclosure;
3. representation-disagreement preservation;
4. review-authority consistency.

The reported LEAP audit localizes three systematic generator defect classes and one correctly operating conflict-routing mechanism. The repository also includes within-system persistence/input-sensitivity analyses, checker-validation controls, and a bounded FastAPI/OpenAPI transferability pilot.

## Reproduction

From `supplement/`, run:

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

The final release was rechecked with all ten commands succeeding and all 32 expected checker outcomes matching their declared labels: 30 binary PASS/FAIL controls and two N/A applicability controls.

## Scope

This artifact supports the bounded claims in the manuscript. The LEAP corpus is an audit of one software system, not a population sample of documentation generators. The external FastAPI/OpenAPI pilot demonstrates bounded procedural transfer of directly applicable checks and does not establish external defect prevalence or universal applicability of all four obligations.
