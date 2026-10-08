# ADR-002: Every visual projection requires `nativeQueryRef`

- Status: accepted — 2026-10-08
- Applies to: `pbir-visuals.md` §1, `validate.py` visuals check, fixture `broken-native-queryref`

## Context

Hand-written `visual.json` projections carried only `queryRef` (`Table.Field`).
The report opened, but Desktop silently dropped all 22 visuals on save — empty
pages with no error pointing at the cause.

## Decision

Every projection carries both `queryRef` (`<Table>.<Field>`, internal) and
`nativeQueryRef` (bare field name, display label), matching exactly what Desktop
itself writes. Column projections also carry `"active": true`; measure
projections omit it.

## Consequences

- The absence of an error message is itself a failure mode: the validator must
  assert presence of fields Desktop needs but does not demand loudly.
- Reference rule: when in doubt, diff against a Desktop-saved file, not against
  third-party templates.
