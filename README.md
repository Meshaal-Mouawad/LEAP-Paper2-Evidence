# LEAP Paper 2 — Explanation Fidelity Evidence

Research artifact for:

**From Source Linkage to Explanation Fidelity: Evidence-Preserving Responsibilities for Enterprise KPI Knowledge Publication**

This repository preserves the evidence used for the paper's descriptive survey results,
historical meeting-duration analysis, and two source-linked KPI case analyses.

## Contents

- `evidence/cases/` — preserved Yield and Gross Margin source and HTML artifacts.
- `evidence/supplement/` — survey counts and recovered instrument wording, participant-profile
  aggregates, meeting-duration log and phase definitions, case evidence maps, artifact manifests,
  focused excerpts, and the Gross Margin derivation.
- `verification/verify_evidence.py` — reproducibility checks for the reported arithmetic,
  symbolic Gross Margin result, case hashes, and evidence paths.
- `docs/REPRODUCIBILITY.md` — step-by-step verification instructions.

The repository contains no participant names, employee IDs, e-mail addresses, or respondent-level
answer matrix. Survey material is supplied as aggregate counts/profile counts. The meeting archive
contains the retained date/time/duration fields used in the published descriptive analysis.

## Reproduce the checks

```bash
python -m pip install -r verification/requirements.txt
python verification/verify_evidence.py --root .
```

The verification does not execute the archived KPI functions and does not contact any network
service or AI model.

## Evidence boundary

This repository supports the bounded claims in Paper 2. It does not convert the historical survey
or meeting records into a controlled intervention study, and it does not establish population-level
extraction accuracy for the companion LEAP software.

## Companion technical study

Paper 2 reuses two source-linked KPI artifacts from the companion LEAP technical study. The
publication-level explanation-fidelity analysis is distinct from the companion study's architecture
and implementation contribution.

## Citation

Citation metadata is provided in `CITATION.cff`.

## Version

Prepared for the 2026 Information and Software Technology submission package.
