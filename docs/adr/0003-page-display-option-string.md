# ADR-003: Page `displayOption` is a string; page schema pinned to 2.0.0

- Status: accepted — 2026-10-08
- Applies to: `pbir-visuals.md` §4, `validate.py` pages check, fixture `broken-display-option`

## Context

Generated `page.json` used `"displayOption": 0` (integer, carried over from
PBIR-Legacy conventions). No visual on any page rendered. A real Desktop-saved
`page.json` showed the correct shape: `"displayOption": "FitToPage"` with schema
`.../page/2.0.0/schema.json`.

## Decision

`displayOption` must be `"FitToPage"` (or `"FitToWidth"` / `"ActualSize"`), and
the page `$schema` is pinned to `2.0.0` — exactly what Desktop writes, not newer
speculation.

## Consequences

- PBIR-Legacy habits (integer enums) are a recurring trap; every value ported
  from legacy format must be re-checked against a Desktop-saved PBIR sample.
- Canvas stays 1280×720 (default) with all visual positions bounded by it.
