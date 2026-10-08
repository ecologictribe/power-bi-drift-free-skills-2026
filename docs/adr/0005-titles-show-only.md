# ADR-005: Visual titles are show-only (no `titleText`)

- Status: accepted — 2026-10-08
- Applies to: `pbir-visuals.md` §3, `validate.py` visuals check, fixture `broken-title-text`

## Context

Custom titles were emitted as `titleText` inside
`visualContainerObjects.title[].properties`. The `visualContainer/2.7.0` schema
rejected it as an additional property on all 22 visuals.

## Decision

Title objects carry only `show: true`; Desktop auto-titles from bound fields and
users rename in Desktop afterwards. Custom title text is intentionally omitted
until a schema version documents a valid property for it.

## Consequences

- Cosmetic control is sacrificed for schema validity — a deliberate trade the
  validator enforces.
- If a future schema adds a title-text property, this ADR is the place to record
  the version-gated change.
