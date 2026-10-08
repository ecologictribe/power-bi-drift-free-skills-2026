# Power BI Projects (PBIP) — Sales & Inventory Analytics

## The problem this repo solves

Public Power BI skills, tutorials, and AI-generated samples have **drifted**:
they teach TMDL/PBIR expressions from older Desktop releases that current
versions reject. Following them produces projects that fail to open, lose all
visuals on save, or render blank pages — with errors that never point at the
real cause (a wrong enum here, a missing field there).

This repo is the drift-free counterweight. Every skill rule was earned by
hitting the actual failure in Power BI Desktop v2.157 and fixing it against
Desktop-saved reference files:

| Symptom | Hidden cause | Rule |
|---|---|---|
| Project won't open (`InvalidValueFormat … CrossFilteringBehavior`) | `singleDirection` is not a TOM enum | `crossFilteringBehavior: oneDirection` |
| All 22 visuals silently dropped, empty pages | projections lacked `nativeQueryRef` | every projection carries `queryRef` + `nativeQueryRef` |
| Nothing on any page renders | `displayOption: 0` (legacy integer) | `displayOption: "FitToPage"`, page schema `2.0.0` |
| Schema validator rejects `report.json` | legacy settings keys + integer consts | minimal key set, `exportDataMode: "AllowSummarized"` |
| Every visual flagged (`titleText`) | `titleText` is not a 2.7.0 title property | show-only titles, Desktop auto-titles |
| Combo/slicer visuals unbindable | combo needs `Y2` (not `Series`); slicers take `Values` only | exact roles per visual type |
| Project won't open (measure/column clash) | measure `'Conversions'` on a table with a `Conversions` column | qualify measures (`Total Conversions`); validator asserts no collisions |

The guarantee is mechanical, not rhetorical: `python validate.py <Project>`
(or the full `fixtures/check_gate.py`, also enforced by CI) fails the build on
any of these. The `fixtures/` drift gallery lets students reproduce each failure
on purpose; `docs/adr/` records why each rule exists.

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

## Learning depth: drift gallery, ADRs, CI

- `fixtures/` — seven minimal broken projects, each violating exactly one rule
  (see `fixtures/README.md`). `python fixtures/check_gate.py` asserts both real
  projects pass and all fixtures fail.
- `docs/adr/` — six decision records capturing the symptom → evidence → rule for
  every hard-won fix, so the reasoning survives.
- `docs/modeling-dax.md` — star schema and forest rule, filter context behind the
  `CALCULATE` measures, model-wide measure uniqueness, M-vs-TOM types.
- `.github/workflows/validate.yml` — CI runs the full gate on every push/PR.

## Regenerating

```powershell
python data/generate_sales_data.py
python data_inventory/generate_inventory_data.py
python build_sales_pbip.py
python build_inventory_pbip.py
```

Generators wipe `definition/pages/` before rewriting (IDs are re-randomized) and
write UTF-8 without BOM.

## Spec-driven generation (LLM-agnostic)

`build_from_spec.py` + `spec/<domain>.json` is the generalized path: any agent
writes a declarative spec (tables, measures, relationships, pages/visuals), the
emitter produces the drift-free PBIP. `prove_spec.py` asserts semantic
equivalence with a blessed tree (proven on MarketingAnalytics: all tables,
relationships, 21 visuals, report shell identical modulo random IDs).

## Git & remote

Machine-local Desktop artifacts (`.pbi/`, `*.abf`, trace zips) are gitignored —
see `.gitignore`. After Desktop opens a project cleanly and saves it, commit that
Desktop-normalized state as the new baseline so writer-vs-Desktop drift disappears.

## License

MIT — see [LICENSE](LICENSE).
