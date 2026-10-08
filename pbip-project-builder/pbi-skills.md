---
name: pbip-project-builder
description: Automates creating, validating, and refactoring Power BI Projects (.pbip), TMDL semantic models, and PBIR reports while preventing specification drift, encoding issues, and schema errors. Use when creating .pbip projects, writing TMDL files, setting up PBIR reports, or fixing Power BI Desktop serialization exceptions.
---

# Power BI Project (.pbip) Builder

Automates the generation and validation of fault-free Power BI Project (`.pbip`) structures compliant with Power BI Desktop (v2.157+) packaging specifications.

> Visuals companion: `pbir-visuals.md` (same folder) owns all `visual.json` rules —
> `nativeQueryRef` bindings, query roles per visual type, combo `Y2`, slicer shape.
> Apply both files together; the project shell here plus that file render end-to-end.

## When to Use

Use this skill when:
- Creating new `.pbip` projects from raw data, CSVs, or databases
- Writing or modularizing TMDL semantic model files (`.tmdl`)
- Structuring PBIR report definitions (`definition.pbir` and page/visual JSONs)
- Troubleshooting packaging exceptions such as `PBIProjectReadException`, `TmdlFormatException`, or `TmdlSerializationException`
- Configuring Git version control for Power BI project repositories

## Core Rules & Specification Drift Controls

### 1. File Encoding Standard
- **Rule**: ALL project files (`.pbip`, `.pbism`, `.pbir`, `.tmdl`, `.json`) MUST be saved in strict **UTF-8 without Byte Order Mark (BOM)**.
- **Why**: Power BI's internal `UTF8EncodingThrowOnBOM` class rejects files containing BOM bytes (`0xEF,0xBB,0xBF`).

### 2. Semantic Model Metadata (`definition.pbism`)
- **Rule**: Declare `"version": "4.0"` inside `<ProjectName>.SemanticModel/definition.pbism`.
- **Why**: Legacy `"version": "1.0"` or `definition.pbidataset` forces Desktop to expect legacy `model.bim` files, ignoring TMDL directory trees.

### 3. Dataset Path Reference (`definition.pbir`)
- **Rule**: The `datasetReference.byPath.path` attribute in `<ProjectName>.Report/definition.pbir` MUST use relative paths with forward slashes (e.g., `"../<ProjectName>.SemanticModel"`).
- **Why**: Absolute Windows drive paths trigger fatal `ByPathNotRelative` read exceptions.

### 4. Tabular Data Types in TMDL
- **Rule**: TMDL column data types MUST use Tabular Object Model (TOM) enumeration types:
  - `string` (not `VARCHAR` or `NVARCHAR`)
  - `int64` (not `INT`, `INTEGER`, or `BIGINT`)
  - `decimal` or `double` (not `FLOAT`, `MONEY`, or `REAL`)
  - `dateTime` (not `DATETIME2` or `DATE`)
  - `boolean` (not `BIT` or `BOOL`)

### 5. TMDL Indentation Syntax
- **Rule**: Use strictly uniform indentation (consistently 1 tab `\t` per nesting level or 4 spaces). NEVER mix tabs and spaces on adjacent lines.

### 7. TMDL Relationship Enums (`relationships.tmdl`)
- **Rule**: Use exact Tabular Object Model (TOM) enum spellings (case-sensitive, camelCase):
  - `crossFilteringBehavior: oneDirection` (NOT `singleDirection`) or `bothDirections`
  - `fromCardinality: many` / `toCardinality: one` (for fact-to-dimension joins)
  - `isActive: true`
- **Why**: Desktop `TmdlValue.ParseEnum` rejects `singleDirection` with `InvalidValueFormat ... Failed to convert the value 'singleDirection' to the expected type CrossFilteringBehavior!` (Power BI Desktop v2.157, Oct 2026). Correct template:
```tmdl
relationship <guid-or-name>
	fromColumn: Orders.CustomerID
	toColumn: Customers.CustomerID
	crossFilteringBehavior: oneDirection
	fromCardinality: many
	toCardinality: one
	isActive: true
```
- **Rule**: NEVER put `///` description lines above a `relationship` object (unsupported `description` property on relationships).

### 6. PBIR Report Folder Hierarchy
- **Rule**: PBIR reports require folder hierarchy:
  - `definition/pages/pages.json`
  - `definition/pages/<pageId>/page.json`
  - `definition/pages/<pageId>/visuals/<visualId>/visual.json`
- **Why**: Flattening visuals into root directories violates JSON schemas and prevents report rendering.

### 8. Report Settings (`definition/report.json`, schema `report/3.2.0`)
- **Rule**: `settings` MUST contain only schema-valid keys with const string values:
```json
"settings": {
  "useStylableVisualContainerHeader": true,
  "exportDataMode": "AllowSummarized",
  "defaultDrillFilterOtherVisuals": true,
  "allowChangeFilterTypes": true,
  "useEnhancedTooltips": true,
  "useDefaultAggregateDisplayName": true
}
```
- **Why**: `filterPaneEnabled` / `navContentPaneEnabled` are rejected as additional
  properties, and `exportDataMode: 1` / `queryLimitOption: 3` (PBIR-Legacy integers)
  fail const-type validation in `report/3.2.0` (validator errors, Oct 2026). When in
   doubt, emit fewer settings keys — every key must exist in the schema.

### 9. Hierarchies & relationship forest (`tables/*.tmdl`, `relationships.tmdl`)
- **Rule**: Hierarchies live inside the table, levels ordered coarse → fine, each
  `level` mapping to an existing `column:` in the same table:
```tmdl
	hierarchy 'Calendar'
		level Year
			column: Year
		level Quarter
			column: Quarter
		level Month
			column: Month
```
- **Rule**: Active relationships must form a **forest** — at most one active filter
  path between any two tables. A redundant path (e.g. two facts sharing two
  dimensions) fails Desktop with ambiguous-path errors: keep one `isActive: true`,
  mark the other `isActive: false` (still usable via `USERELATIONSHIP` in DAX).

### 10. Measure naming (uniqueness + no column collisions)
- **Rule**: Measure names must be unique across the **whole model** AND must not
  equal any column name **in their own table** (case-insensitive). Desktop fails
  the open with `PFE_XL_MEASURE_COLUMN_ALREADY_EXIST` otherwise.
- **Why**: A bare measure like `'Conversions'` on a table with a `Conversions`
  column collides; qualified names (`Total Conversions`) never do.
- **Fix pattern**: rename the measure, never the source column (M `sourceColumn`
  bindings depend on column names).

### 11. Safe regeneration (destructive-ops ban)
- **Rule**: Generators may delete **only** inside their own regenerable artifact
  dirs (`definition/pages/`). The output root itself is NEVER removed, and the
  entry point MUST refuse output paths that are `.git` or outside the repo root
  (see ADR-008 — a root wipe once destroyed the local `.git`).
- **Why**: Fixed page/visual IDs make reruns stable without root wipes; anything
  broader risks the repo itself.

## 5-Step Workflow for Building a PBIP Project

### Step 1: Initialize Root `.pbip` & Git Configuration
Create `<ProjectName>.pbip` at the repository root:
```json
{
  "version": "1.0",
  "artifacts": [
    { "report": { "path": "<ProjectName>.Report" } }
  ],
  "settings": { "enableAutoRecovery": true }
}