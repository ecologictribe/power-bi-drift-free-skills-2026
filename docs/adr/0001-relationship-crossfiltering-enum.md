# ADR-001: Relationship `crossFilteringBehavior` must be `oneDirection`

- Status: accepted — 2026-10-08
- Applies to: `pbi-skills.md` §7, `validate.py` TMDL check, fixture `broken-rel-enum`

## Context

Generated `relationships.tmdl` used `crossFilteringBehavior: singleDirection`
(a natural-English guess). Power BI Desktop v2.157 refused to open the project:

> `InvalidValueFormat ... Failed to convert the value 'singleDirection' to the
> expected type CrossFilteringBehavior!`

## Decision

Use exact TOM enum spellings (case-sensitive camelCase): `oneDirection` or
`bothDirections`, with `fromCardinality: many` / `toCardinality: one` for
fact-to-dimension joins. Never invent enum prose.

## Consequences

- Validator rejects any other spelling before Desktop is involved.
- Lesson generalized: every TMDL enum (not just this one) must be copied from TOM
  vocabulary, never guessed. See ADR-004 for the JSON-side equivalent.
