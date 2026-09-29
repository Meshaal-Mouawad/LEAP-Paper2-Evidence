# Gross Margin case evidence map

## Artifact identity

- Source: `../cases/conflict_formula_margin.py`
- Source SHA-256: `78cfb5e20447f19d36c1b25adcdf3d5542edc09199194f97bddabb6963067ef1`
- Published dossier: `../cases/gross_margin_percentage.html`
- Dossier SHA-256: `83b4dcc240818a783156c38bb3cc7572ad2a2796a2a5c2fe8b69115b9d0cd479`

## Source evidence

```python
def calculate_gross_margin_pct(revenue, cost):
    # CONFLICT: business formula specifies (Revenue - Cost) / Revenue * 100
    # but implementation divides revenue by cost instead — operator conflict
    if cost == 0:
        return 0.0
    return (revenue / cost) * 100
```

Declared representation:

`D = 100(R-C)/R`

Executable positive-domain representation:

`I = 100R/C`

For `R>0` and `C>0`:

`I-D = 100(1 + (R-C)^2/(RC)) >= 100`.

## Published evidence

The archived dossier simultaneously contains:

- `Needs Review`
- `Verified Logic Mapping`
- `LEAP certifies the KPI definition...`
- `certified calculation expression`
- `Print Certified Dossier`

Relevant raw HTML locations:

- line 126 / 131: `Needs Review` status.
- line 284: Developer Lineage Breakdown with declared/executable conflict and cost guard.
- line 299: complete source excerpt.
- lines 314-315: `Verified Logic Mapping` and certification-oriented prose.
- line 323: current status `Needs Review`.
- line 419: `Print Certified Dossier` action.

## Paper 2 finding

The declared and executable representations remain mathematically incompatible throughout the strictly positive domain. The same published dossier combines an unresolved review state with certification-oriented language. Paper 2 analyzes that juxtaposition as a publication-level review-authority problem.
