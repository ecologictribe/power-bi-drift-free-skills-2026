---
name: pbir-visuals
description: Author valid Power BI Enhanced Report Format (PBIR) visuals that survive Desktop open/refresh/save without being dropped. Use when creating or editing visual.json files, choosing query roles per visual type, binding fields/measures, adding slicers, combo charts, cardVisual KPIs, tables, sorting, or titles in a .pbip Report definition.
---

# PBIR Visuals Authoring (drift-free)

Companion to the `pbip-project-builder` skill (project shell, TMDL model, encodings).
This file owns **everything inside `visual.json`** so generated reports render after
data refresh instead of opening as empty pages.

Target schemas (June 2026 Desktop): `visualContainer/2.7.0`, `page/2.1.0`,
`report/3.2.0`, `versionMetadata` content `2.0.0`, base theme `CY26SU02`.

## 1. Projection binding (REQUIRED — visuals vanish without this)

Every entry in `query.queryState.<Role>.projections` MUST carry BOTH refs:

```json
{
  "field": { "Column": { "Expression": { "SourceRef": { "Entity": "Products" } }, "Property": "Category" } },
  "queryRef": "Products.Category",
  "nativeQueryRef": "Category",
  "active": true
}
```

```json
{
  "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "Orders" } }, "Property": "Total Sales" } },
  "queryRef": "Orders.Total Sales",
  "nativeQueryRef": "Total Sales"
}
```

Rules:
- `queryRef` = `<Table>.<ColumnOrMeasure>` (exact TMDL names, case-sensitive).
- `nativeQueryRef` = bare property name. **Omitting it is the #1 cause of visuals
  being silently dropped on Desktop save** (found Oct 2026: 22 visuals, 0 rendered).
- Column projections include `"active": true`. Measure projections omit `active`
  (matches Desktop-written files).
- `Entity` MUST equal the TMDL `table` name exactly.

## 2. Query roles per visual type (exact names)

| visualType | Roles (queryState keys) |
|---|---|
| `cardVisual` (new card/KPI — always use this, never legacy `card`) | `Data` |
| `lineChart`, `clusteredBarChart`, `barChart`, `clusteredColumnChart`, `columnChart`, `pieChart`, `donutChart` | `Category` + `Y` (+ optional `Series` legend for cartesian charts) |
| `lineStackedColumnComboChart` | `Category` + `Y` (columns) + `Y2` (line). NEVER `Series` here. |
| `tableEx` | `Values` |
| `slicer` | `Values` ONLY. NEVER add a `Filters` key inside `queryState`. |
| `funnel` | `Category` + `Y` (sort `Category` by its order column ascending) |
| `gauge` | `Y` (actual measure) + `TargetValue` (target measure) |
| `kpi` | `Indicator` (measure) + `Goal` (measure) + `TrendLine` (date column) |
| `pivotTable` (matrix) | `Rows` + `Columns` (columns) + `Values` (measures) |
| `waterfallChart` | `Category` + `Y` (signed measure; negatives render as decreases) |

`Series` holds a **column** (legend split). `Y2` holds a **measure** (line axis).

## 3. Visual-level defaults

- Set `"drillFilterOtherVisuals": true` inside `visual` for every chart/card/table
  (Desktop writes it by default; slicers omit it).
- Titles: `visual.visualContainerObjects.title` accepts ONLY `show` under
  `visualContainer/2.7.0`. `titleText` is rejected as an additional property
  (validator flags it on every visual that carries it), so emit show-only and let
  Desktop auto-title from bound fields — rename in Desktop afterwards if needed:
```json
"visualContainerObjects": {
  "title": [{ "properties": {
    "show": { "expr": { "Literal": { "Value": "true" } } } } }]
}
```
- `sortDefinition` entries are `{ "field": <same field object>, "direction": "Descending" }`
  (no `queryRef` inside sort entries).
- `position` must fit the page (`x + width <= page width`, `y + height <= page height`,
  page is 1280x720). Unique `tabOrder` per visual. `z: 0`.
- Page/visual folder names: 20 lowercase hex chars. `pages.json` `pageOrder` MUST
  list exactly the existing page folders; `activePageName` = first page.

## 4. Page shell (`page.json`) — string enums only (render-killer if wrong)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
  "name": "<20-hex-id>",
  "displayName": "Sales Overview",
  "displayOption": "FitToPage",
  "width": 1280,
  "height": 720
}
```

Rules (verified against a real Desktop-saved report, Oct 2026):
- `displayOption` MUST be the string `"FitToPage"` (or `"FitToWidth"` / `"ActualSize"`).
  An integer (`0`, carried over from PBIR-Legacy) fails page parsing and **nothing
  on any page renders** — this was the blank-report bug.
- Page `$schema` MUST be `.../page/2.0.0/schema.json` (exactly what Desktop writes).
- Valid canvas: `1280x720` (default) or `1920x1080`. Every visual must satisfy
  `x + width <= page width`, `y + height <= page height`.
- `pages.json` (`pagesMetadata/1.0.0`) `pageOrder` MUST list exactly the existing page
  folders; `activePageName` = first page.

## 5. Regeneration hygiene

- Page IDs: fixed constants. Visual IDs: random per run is fine ONLY if the generator
  wipes `definition/pages/` before rewriting — otherwise orphan visual folders from
  prior runs linger and confuse Desktop/Git.
- After ANY report change: JSON-parse every file, assert BOM-free UTF-8,
  assert every projection has `nativeQueryRef`, assert no `Filters` role in slicers,
  assert combo charts carry `Y2`, assert `displayOption` is a string.

- Page IDs: fixed constants. Visual IDs: random per run is fine ONLY if the generator
  wipes `definition/pages/` before rewriting — otherwise orphan visual folders from
  prior runs linger and confuse Desktop/Git.
- After ANY visual.json change: JSON-parse every file, assert BOM-free UTF-8,
  assert every projection has `nativeQueryRef`, assert no `Filters` role in slicers,
  assert combo charts carry `Y2`.
- Close Power BI Desktop before replacing files (it does not watch the filesystem
  and rewrites definitions on save, which can mask generator bugs).
