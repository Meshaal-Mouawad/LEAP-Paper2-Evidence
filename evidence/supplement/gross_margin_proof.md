# Gross Margin algebra and boundary inputs

Declared representation:

`D = 100 (R - C) / R`

Executable positive-domain representation:

`I = 100 R / C`

For `R > 0` and `C > 0`:

`I - D = 100(R/C - (R-C)/R)`

`= 100(R/C + C/R - 1)`

`= 100(1 + (R-C)^2/(RC)) >= 100` percentage points.

Equality in the lower bound occurs at `R = C`; then `D = 0` and `I = 100`.

Boundary inputs preserved by the source:

- `R > 0, C = 0`: declaration gives 100%; implementation returns 0 through the `cost == 0` guard.
- `R = 0, C > 0`: declaration is undefined; implementation evaluates `100 * 0 / C = 0`.
