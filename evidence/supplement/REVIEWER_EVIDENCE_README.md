# Paper 2 reviewer evidence supplement

This supplement gives a direct path from the manuscript to the evidence used for the survey, meeting-series, and two central source-linked cases.

## S1 - Survey (N=60)

- `SURVEY_INSTRUMENT.md` - questionnaire wording, response options, and the three items analyzed in Paper 2.
- `survey_profile_N60.csv` - role and enterprise-system experience counts.
- `survey_counts_N60.csv` - the three Paper 2 distributions; every distribution totals N=60.
- `survey_instrument_recovered.csv` - machine-readable version of the retained instrument fields.

## S2 - Meeting archive

- `MEETING_ARCHIVE_METHOD.md` - inclusion rule, recorded fields, duration calculation, and phase assignment.
- `meeting_duration_log.csv` - all 60 completed dated meeting records.
- `meeting_phase_definition.csv` - exact meeting-number/date boundaries for the four archived phases.

## S3 - Yield case

- `YIELD_CASE_EVIDENCE.md` - direct evidence map and raw HTML line locators.
- `yield_source_excerpt.txt`
- `yield_dossier_excerpt.txt`
- Full files: `../cases/control_no_conflict_yield.py` and `../cases/ethylene_production_yield.html`.

## S4 - Gross Margin case

- `MARGIN_CASE_EVIDENCE.md` - direct evidence map and raw HTML line locators.
- `margin_source_excerpt.txt`
- `margin_dossier_excerpt.txt`
- `gross_margin_proof.md`
- Full files: `../cases/conflict_formula_margin.py` and `../cases/gross_margin_percentage.html`.

## S5 - Artifact identity

- `case_evidence_manifest.csv` - SHA-256 values, source archive identity, and original archive member paths.
- `../cases/CASE_SOURCE_MANIFEST.json` - machine-readable case manifest.

The four case artifacts are preserved byte-for-byte from the identified companion technical archive.

## S6 - Reproduction and package layout

From the supplement root, run:

```sh
python -m pip install -r verification/requirements.txt
python verification/verify_evidence.py --root .
```

To repeat comparison against the original companion ZIP, add:

```sh
python verification/verify_evidence.py --root . --source-archive "/path/to/JSS_Submtion 2.zip"
```

The script checks arithmetic, all 60 recorded meeting intervals, archived phase boundaries, the mathematical identity, source/HTML evidence, and relative case paths. It does not infer original recruitment procedures or timestamp capture meaning. Verification results and file hashes are written as JSON.

The layout is the same in the full revision and reviewer supplement: notes and counts are in `evidence/supplement/`; preserved source and HTML files are in `evidence/cases/`. Relative `../cases/` references in these notes therefore resolve in every delivered package.
