# ADR-004: Report settings use const strings, minimal key set

- Status: accepted — 2026-10-08
- Applies to: `pbi-skills.md` §8, `validate.py` settings check, fixture `broken-settings`

## Context

Generated `report.json` settings used PBIR-Legacy shapes: `filterPaneEnabled`,
`navContentPaneEnabled` (rejected as additional properties) and integer
`exportDataMode: 1` / `queryLimitOption: 3` (failed const-type validation in
`report/3.2.0`). The schema validator listed every violation precisely.

## Decision

Emit only proven keys with const string values
(`exportDataMode: "AllowSummarized"` plus the Desktop-written boolean flags).
Rule of thumb: fewer settings keys — every key must exist in the schema version
declared in `$schema`.

## Consequences

- Same lesson as ADR-001 on the JSON side: never port legacy-typed values into a
  versioned schema without checking its consts.
- Validator pins the allowed key set, so future additions fail loudly.
