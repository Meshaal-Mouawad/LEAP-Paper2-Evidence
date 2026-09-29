# Yield case evidence map

## Artifact identity

- Source: `../cases/control_no_conflict_yield.py`
- Source SHA-256: `bcbe6f52920321e544374308ebcf180a12875b8752c2420c94aa036291195930`
- Published dossier: `../cases/ethylene_production_yield.html`
- Dossier SHA-256: `0a217434501cbc54b35da7b46d8306ff3f472b5d7258da9471c5c36b14ae1f55`

## Source evidence

The source contains the declared percentage formula and the executable guard:

```python
def calculate_ethylene_yield_pct(ethylene_produced_tons: float,
                                 feedstock_input_tons: float) -> float:
    """Calculates ethylene production yield as a percentage of feedstock input."""
    if feedstock_input_tons <= 0:
        return 0.0
    return (ethylene_produced_tons / feedstock_input_tons) * 100.0
```

## Published evidence

The dossier displays status `Validated` and exposes the source in its Developer Lineage Breakdown. For the function docstring it publishes:

> Output alias: maps this expression to a in the result set.

The same role text is repeated twice in the one dossier. The dossier also displays the ratio as the Formal Formula, while the source context separately shows the non-positive-input guard.

Relevant raw HTML locations in the archived dossier:

- line 126 / 131: `Validated` status.
- lines 233–235: `Formal Formula` field and the ratio-only MathJax expression.
- line 303: `Verified Logic Mapping` describes the ratio as the `certified calculation expression`.
- line 272: first Developer Lineage Breakdown, including the docstring role text and guard lines.
- line 287: complete captured source.
- line 295: repeated Developer Lineage Breakdown.

## Paper 2 finding

The linked source statement is a Python function docstring. The published lineage text labels it as a result-set alias. Source linkage is present; the semantic role is wrong. The source also contains a branch condition that changes executable behavior for non-positive feedstock.

## Formal publication field and its stated role

The `Mathematical Formulation` section contains the `Formal Formula` label at line 233. Line 235 displays:

```latex
\mathrm{Ethylene\,Production\,Yield} = \left(\frac{\mathrm{Ethylene\,Produced}}{\mathrm{Feedstock\,Input}}\right) \times 100
```

The second list item in `Verified Logic Mapping` at line 303 states:

> Second, it presents the certified calculation expression (Ethylene Yield % = (Ethylene Produced (tons) / Feedstock Input (tons)) * 100) in the formal MathJax formula shown above.

This is the displayed field examined in the condition-preservation finding. Source lines 17–18 implement the non-positive-input guard; HTML line 287 retains that source. The condition is absent from the formal ratio field, not from the entire dossier. `yield_dossier_excerpt.txt` includes the exact raw HTML lines, with their original line numbers.
