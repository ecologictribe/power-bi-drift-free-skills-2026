# Power BI Projects (PBIP) — Sales & Inventory Analytics

Source-controlled Power BI Project (`.pbip`) builds with TMDL semantic models and
PBIR reports, generated under strict skill contracts so they open, refresh, and
render in Power BI Desktop without serialization errors.

## Projects

| Project | Data | Model | Report |
|---|---|---|---|
| `SalesAnalytics` | `data/` — Orders, Customers, Products, Dates (2023–2024) | 4 tables, 10 measures, 3 relationships | 3 pages / 22 visuals |
| `InventoryAnalytics` | `data_inventory/` — Transactions, Products, Warehouses, Suppliers, Dates | 5 tables, 9 measures, 4 relationships | 3 pages / 22 visuals |

Report pages cover KPI cards, line/bar/donut/pie/combo charts, slicers, and detail
tables per project domain.

## Prerequisites

- Power BI Desktop (tested on v2.157, Aug 2026) with preview features on:
  **Store semantic model using TMDL format**, **Power BI enhanced report format (PBIR)**
- Python 3.11+ with `pandas`, `numpy` (data generators and validators only)

## Quickstart (first open)

A fresh `.pbip` carries metadata only — one manual refresh is expected, not a bug:

1. Close Power BI Desktop if it is already running (it caches definitions).
2. Open `<Project>.pbip` (e.g. `SalesAnalytics.pbip`).
3. When prompted, **Refresh** to load the local CSVs (connections are anonymous
   `File.Contents` reads; no credentials needed).
4. Verify relationships loaded, then browse the three report pages.

## Repository layout

```
prompt.md                        # build brief: template + worked example + acceptance gate
pbip-project-builder/
  pbi-skills.md                  # normative: project shell, TMDL, report shell
  pbir-visuals.md                # normative: all visual.json rules
build_sales_pbip.py              # SalesAnalytics generator (UTF-8 no-BOM, tab TMDL)
build_inventory_pbip.py          # InventoryAnalytics generator
generate→ / data/…              # sales CSVs (+ generate_sales_data.py)
data_inventory/…                 # inventory CSVs (+ generate_inventory_data.py)
validate.py                      # shared validator: python validate.py <ProjectName>
.quarantine/                     # retired superseded scripts (gitignored)
```

## Skills & prompt

- `prompt.md` is the entry point: reusable brief template, worked SalesAnalytics
  example, and the acceptance gate. On any conflict, the skill files override it.
- `pbi-skills.md` owns encodings, `pbism 4.0`, `byPath`, TOM types, indentation,
  TMDL relationship enums, report folder hierarchy, and report settings.
- `pbir-visuals.md` owns field bindings (`nativeQueryRef`), query roles per visual
  type, combo `Y2`, slicer shape, `FitToPage` pages, and regeneration hygiene.

## Validation

```powershell
python validate.py SalesAnalytics
python validate.py InventoryAnalytics
```

Exit 0 with `RESULT: ALL GREEN` means the skill contract holds (TMDL, PBIR shell,
41 visual projections per project, page consistency). Both projects must stay green
before any commit.

## Regenerating

```powershell
python data/generate_sales_data.py
python data_inventory/generate_inventory_data.py
python build_sales_pbip.py
python build_inventory_pbip.py
```

Generators wipe `definition/pages/` before rewriting (IDs are re-randomized) and
write UTF-8 without BOM.

## Git & remote

Machine-local Desktop artifacts (`.pbi/`, `*.abf`, trace zips) are gitignored —
see `.gitignore`. After Desktop opens a project cleanly and saves it, commit that
Desktop-normalized state as the new baseline so writer-vs-Desktop drift disappears.

## License

MIT — see [LICENSE](LICENSE).
