# Modeling & DAX notes (the concepts under the TMDL syntax)

## Star schema and the forest rule

Both projects are star schemas: one fact table (`Orders`, `InventoryTransactions`)
surrounded by dimensions (`Customers`, `Products`, `Dates` / `Warehouses`,
`Suppliers`). Every relationship is fact(`many`) → dimension(`one`), single
direction, active. The active relationships must form a **forest**: at most one
active filter path between any two tables, otherwise Desktop fails with ambiguous
paths. InventoryAnalytics chains `Transactions → Products → Suppliers` — a second
direct `Transactions → Suppliers` link would close a loop and must stay inactive
(`isActive: false`, usable via `USERELATIONSHIP`) or be omitted.

## Filter context and the `CALCULATE` measures

Measures like `Completed Sales = CALCULATE([Total Sales], Orders[Status] = "Completed")`
work by *filter context*: `CALCULATE` evaluates the base measure under an added
filter. Slicers and cross-filtering do the same thing from visuals
(`drillFilterOtherVisuals`, page `visualInteractions`). One mental model covers
DAX, slicers, and interactions.

## Measure uniqueness and placement

Analysis Services requires measure names unique **across the whole model**, not
per table — hence all business measures live on the fact table with `formatString`
set (`$#,##0.00`, `#,##0`, `0.00%`). Dimension tables carry only their own
count measures (`Customer Count`, `Product Count`). Additionally, no measure may
share a name with a column **in its own table** (`PFE_XL_MEASURE_COLUMN_ALREADY_EXIST`
otherwise) — always qualify (`Total Conversions`, never bare `Conversions`).

## Power Query partitions

Each table has one `import`-mode M partition: `Csv.Document(File.Contents(...))`
→ `PromoteHeaders` → `TransformColumnTypes`. Types here are M types
(`Int64.Type`, `type number`, `type datetime`, `type text`, `type logical`);
the TMDL `dataType` is the separate TOM enum. Both layers must agree or refresh
breaks. Paths are absolute with forward slashes; a fresh `.pbip` holds metadata
only, so the first Desktop open always needs one manual refresh by design.
