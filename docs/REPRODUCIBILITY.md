# Reproducibility

## Requirements

- Python 3.10 or later
- SymPy (see `verification/requirements.txt`)

## Run

From the repository root:

```bash
python -m pip install -r verification/requirements.txt
python verification/verify_evidence.py --root .
```

The script checks:

1. N=60 survey category totals and percentages.
2. Survey role and enterprise-system-experience aggregates.
3. All 60 meeting intervals and archived phase summaries.
4. The 49-meeting post-baseline total and mean.
5. SHA-256 identities of the four preserved case artifacts.
6. Yield source/docstring/guard and dossier wording relationships.
7. Gross Margin declared/executable expressions and the positive-domain identity.
8. Relative evidence paths used by the case notes.

The script writes `verification/reproduced_results.json`.

## Optional original-archive comparison

If the original companion archive is available locally:

```bash
python verification/verify_evidence.py --root . --source-archive "/path/to/JSS_Submtion 2.zip"
```

This optional check confirms that the four preserved case files are byte-identical to their
original archive members.
