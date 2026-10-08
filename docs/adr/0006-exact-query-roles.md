# ADR-006: Exact query roles per visual type

- Status: accepted — 2026-10-08
- Applies to: `pbir-visuals.md` §2, `validate.py` visuals check,
  fixtures `broken-combo-series`, `broken-slicer-filters`

## Context

Two role mistakes survived the first visual pass: a combo chart used `Series`
for its second axis (combos require `Y2`, a measure — `Series` is a column
legend role), and a slicer carried an empty `Filters` key (slicers accept
`Values` only). Both produce invalid visuals Desktop cannot bind.

## Decision

Roles are fixed per visual type and asserted by the validator:
`cardVisual→Data`, cartesian/pie/donut→`Category+Y` (+`Series` legend only on
cartesian), `lineStackedColumnComboChart→Category+Y+Y2`, `tableEx/slicer→Values`
with no `Filters` key. `chart→drillFilterOtherVisuals: true` (slicers omit it).

## Consequences

- Role tables live in one place (`pbir-visuals.md` §2); new visual types must
  extend the table and the validator together.
