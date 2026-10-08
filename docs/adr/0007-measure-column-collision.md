# ADR-007: Measure names must not collide with same-table column names

- Status: accepted — 2026-10-08
- Applies to: `pbi-skills.md` §10, `validate.py` collision check,
  fixture `broken-measure-collision`

## Context

`MarketingAnalytics` defined measure `'Conversions'` on table `DailySpend`,
which already has a `Conversions` column. Desktop refused to open the project:

> `The 'Conversions' measure cannot be created because a column with the same
> name already exists.` (`PFE_XL_MEASURE_COLUMN_ALREADY_EXIST`)

Model-wide measure uniqueness (already enforced) does not cover this: the
collision is per-table, measure-vs-column.

## Decision

Two rules, both enforced by the validator (case-insensitive):
1. Measure names unique across the whole model (existing rule).
2. No measure may share a name with any column **in its own table**.
Fix pattern: qualify the measure (`Total Conversions`), never rename the
source column (M `sourceColumn` bindings depend on it).

## Consequences

- Audit past projects on every new rule: Sales/Inventory/HR/Finance had no
  collisions (their measures are all qualified: `Total Quantity`, `Avg Unit
  Cost`); only Marketing's bare `Conversions` tripped it.
