# Power BI Project (.pbip) Build Prompt

You are acting as an expert Power BI Developer. Normative rules live in the skill
files — they override anything below on conflict:
- `pbip-project-builder/pbi-skills.md` (project shell, TMDL model, report shell)
- `pbip-project-builder/pbir-visuals.md` (all `visual.json` rules)

## A. Reusable brief (fill this in per project, no placeholders left blank)

- **Project Name**: `<e.g. SalesAnalytics>` → produces `<Project>.pbip`,
  `<Project>.SemanticModel/`, `<Project>.Report/`
- **Local Data Folder**: `<absolute path, e.g. D:/power_new/data/>` — Power Query M
  partitions reference these files with forward slashes (`/`)
- **Tables**: for each — table name, source CSV, columns with TOM types
  (`string | int64 | decimal | double | dateTime | boolean`), key measures with DAX
- **Relationships**: `Fact.Column → Dimension.Column` pairs (must form a forest:
  at most one active filter path between any two tables)
- **Report pages**: page names + visual list (type + bound fields per visual)

## B. Worked example (SalesAnalytics — the filled brief)

- **Project Name**: `SalesAnalytics` — **Data**: `D:/power_new/data/`
- **Tables**:
  1. `Orders` ← `Orders.csv` — `OrderID int64`, `CustomerID int64`,
     `ProductID int64`, `OrderDate dateTime`, `Quantity int64`,
     `Amount decimal`, `Cost decimal`, `Status string`
     Measures: `Total Sales = SUM(Orders[Amount])`, `Total Cost`, `Total Profit`,
     `Profit Margin %`, `Total Quantity`, `Order Count`, `Avg Order Value`,
     `Completed Sales` (all `$#,##0.00` / `#,##0` / `0.00%` formatted, unique model-wide)
  2. `Customers` ← `Customers.csv` — `CustomerID int64 (key)`, `CustomerName`,
     `Region`, `Segment`, `City` (all `string`) + `Customer Count`
  3. `Products` ← `Products.csv` — `ProductID int64 (key)`, `ProductName`,
     `Category`, `SubCategory` (all `string`), `UnitPrice decimal`, `Cost decimal`
     + `Product Count`
  4. `Dates` ← `Dates.csv` — `Date dateTime (key)`, `Year/Quarter/Month/
     DayOfMonth/WeekOfYear int64`, `MonthName/DayOfWeek string`, `IsWeekend boolean`
- **Relationships**: `Orders.CustomerID → Customers.CustomerID`,
  `Orders.ProductID → Products.ProductID`, `Orders.OrderDate → Dates.Date`
  (all `oneDirection`, `many → one`, `isActive: true`)
- **Report** (1280×720, `FitToPage`): *Sales Overview* (4 KPI cards, line, bar,
  donut, column, table), *Products & Customers* (2 slicers, 2 cards, bar, pie,
  table), *Trends & Details* (slicer, 3 cards, combo `Y+Y2`, table)

## C. Constraints & acceptance gate

- Generate strictly per the skill files (UTF-8 no-BOM, `pbism 4.0`,
  `byPath: ../<Project>.SemanticModel`, tab-indented TMDL, `nativeQueryRef`
  bindings, string `displayOption`, const report settings, show-only titles).
- Never leave orphan page/visual folders: wipe `definition/pages/` on regen if IDs
  are re-randomized; keep `pages.json` in sync with folders on disk.
- **Acceptance gate**: `python validate.py <ProjectName>` must print `RESULT: ALL GREEN`
  (exit 0 — TMDL + PBIR + visuals) before handoff.
- **Expected behavior (not a bug)**: a fresh `.pbip` carries metadata only, no cached
  data — Power BI Desktop always requires one manual data refresh on first open.
