# Drift gallery

Seven minimal PBIP projects, each violating **exactly one** skill rule. Run the
validator inside a fixture to see the precise failure; fix it to see green.
Rebuild all with `python fixtures/make_fixtures.py` (wipes and regenerates).

| Fixture | Violation | Validator failure | Skill rule | ADR |
|---|---|---|---|---|
| `broken-rel-enum` | `crossFilteringBehavior: singleDirection` | TOM types + oneDirection | `pbi-skills.md` §7 | ADR-001 |
| `broken-native-queryref` | projection without `nativeQueryRef` | visuals conform | `pbir-visuals.md` §1 | ADR-002 |
| `broken-display-option` | `displayOption: 0` (integer) | pages FitToPage | `pbir-visuals.md` §4 | ADR-003 |
| `broken-settings` | legacy settings keys + integer consts | settings keys, exportDataMode | `pbi-skills.md` §8 | ADR-004 |
| `broken-title-text` | `titleText` in title properties | visuals conform | `pbir-visuals.md` §3 | ADR-005 |
| `broken-combo-series` | combo uses `Series` instead of `Y2` | visuals conform | `pbir-visuals.md` §2 | ADR-006 |
| `broken-slicer-filters` | slicer with `Filters` role | visuals conform | `pbir-visuals.md` §2 | ADR-006 |

```powershell
cd fixtures/broken-rel-enum
python ..\..\validate.py BrokenGallery   # expect FAIL: oneDirection
```

`fixtures/check_gate.py` runs the whole gate: both real projects must pass,
all seven fixtures must fail.
