# Paper 2 R3 audit protocol

This protocol fixes the audit rules before the R3 corpus rerun. It replaces the earlier post-hoc 11-row condition adjudication with a deterministic guard-disclosure check and reframes corpus outcomes as defect classes plus observed instances, not independent prevalence estimates.

## Literature-derived publication obligations

The four checks are a bounded synthesis of established obligations, not a claim of a complete, minimal, or mutually exclusive theory of explanation quality.

1. **Source-role fidelity.** Documentation and evidence models distinguish the role played by source statements and evidence items. Code-documentation equivalence requires documentation to describe behavior accurately and completely; SEPIO/ECO distinguish evidence/assertion types and provenance roles. Audit rule: comments, docstrings, and metadata must not be labeled as executable/query roles; SQL cast types must not be labeled as output aliases.
2. **Exceptional-guard disclosure.** Documentation-to-code equivalence requires reader-facing documentation to preserve behavior that changes under explicit execution conditions. Audit rule: an explicit zero/non-positive denominator guard is preserved only when the reader-facing safeguard identifies the guard and the denominator/guarded variable matches the displayed formula; a non-positive guard cannot be reduced to zero-only wording.
3. **Disagreement preservation.** Inconsistency-management research permits known disagreement to remain visible rather than being silently resolved, and evidence models can preserve supporting/refuting evidence. Audit rule: an explicitly marked source conflict/mismatch/inversion is preserved only when the dossier remains `Needs Review` and exposes a Review Queue.
4. **Authority-language consistency.** Evidence/provenance work distinguishes assertion/evidence roles and validation/governance state. Audit rule: a dossier carrying `Needs Review` fails when the same publication surface uses certification-oriented language that implies completed authority.

## Counting model

The primary scientific unit is a **defect class** or **working mechanism**, not each dossier occurrence. Dossier and condition counts are reported as repeated manifestations of a class.

- Lineage typing defect: one generator defect class; report affected dossiers and visible instances.
- Guard-to-safeguard binding defect: one generator defect class; report affected guards/dossiers.
- Authority-language template defect: one generator/template defect class; report affected unresolved dossiers.
- Conflict-routing mechanism: one working mechanism; report eligible dossiers that preserve disagreement through the review path.

## Deterministic condition scope

The R3 guard audit no longer uses a human-coded 11-row table. It scans explicit source-level zero/non-positive denominator guards only:

- `NULLIF(variable, 0)` denominator guards;
- conditional guards that compare a variable directly with zero (`==`, `=`, `<=`, `<`, `>=`, `>`), when the condition controls exceptional return/calculation behavior visible in the retained source context.

The earlier threshold-classification condition `index >= 1.0` is excluded from this denominator/exception-guard audit and remains part of the explicit conflict analysis. This yields ten guard instances in the primary 28-dossier build.

## Reproducibility boundary

All primary-corpus results must be reproduced from immutable dossier pages and deterministic scripts. Replication builds are reported separately and are not pooled into a prevalence estimate.
