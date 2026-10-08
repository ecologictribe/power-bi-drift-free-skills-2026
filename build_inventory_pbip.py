"""Builds InventoryAnalytics PBIP from ./data_inventory CSVs.
Follows pbip-project-builder/pbi-skills.md + pbir-visuals.md (no drift).
Run: python build_inventory_pbip.py
"""
import json
import os
import shutil
import uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = "InventoryAnalytics"
DATA_DIR_FWD = "D:/power_new/data_inventory"
SEM = f"{PROJECT}.SemanticModel"
REP = f"{PROJECT}.Report"

def w_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")

def w_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

T = "\t"

def col(name, dtype, source, extra=None):
    n = name if all(c.isalnum() or c == '_' for c in name) else f"'{name}'"
    lines = [f"{T}column {n}", f"{T}{T}dataType: {dtype}",
             f"{T}{T}sourceColumn: {source}", f"{T}{T}summarizeBy: none"]
    for e in (extra or []):
        lines.append(f"{T}{T}{e}")
    return "\n".join(lines)

def meas(name, expr, fmt, desc):
    return (f"{T}/// {desc}\n{T}measure '{name}' = ```\n{T}{T}{expr}\n{T}\t```\n"
            f"{T}{T}formatString: {fmt}")

def m_part(table, filename, columns, mtypes):
    pairs = ", ".join([f'{{"{c}", {t}}}' for c, t in zip(columns, mtypes)])
    return (
f"""{T}partition {table} = m
{T}{T}mode: import
{T}{T}source =
{T}{T}{T}let
{T}{T}{T}{T}Source = Csv.Document(File.Contents("{DATA_DIR_FWD}/{filename}"), [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.None]),
{T}{T}{T}{T}#"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
{T}{T}{T}{T}#"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{pairs}}})
{T}{T}{T}in
{T}{T}{T}{T}#"Changed Type"
{T}{T}annotation PBI_ResultType = Table""")

# ---------- .pbip ----------
w_json(os.path.join(ROOT, f"{PROJECT}.pbip"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0",
    "artifacts": [{"report": {"path": REP}}],
    "settings": {"enableAutoRecovery": True}})

# ---------- SemanticModel ----------
w_json(os.path.join(ROOT, SEM, "definition.pbism"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.0", "settings": {}})
for itype in ("SemanticModel", "Report"):
    folder = SEM if itype == "SemanticModel" else REP
    w_json(os.path.join(ROOT, folder, ".platform"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": itype, "displayName": PROJECT},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}})

w_text(os.path.join(ROOT, SEM, "definition", "database.tmdl"),
       f"database {PROJECT}\n{T}compatibilityLevel: 1702\n{T}compatibilityMode: powerBI\n")
w_text(os.path.join(ROOT, SEM, "definition", "model.tmdl"),
       f"model Model\n{T}culture: en-US\n{T}defaultPowerBIDataSourceVersion: powerBI_V3\n"
       f"{T}sourceQueryCulture: en-US\n{T}discourageImplicitMeasures: true\n\n"
       f"ref table InventoryTransactions\nref table Products\nref table Warehouses\n"
       f"ref table Suppliers\nref table Dates\n")

def rel(guid, frm, to):
    return (f"relationship {guid}\n{T}fromColumn: {frm}\n{T}toColumn: {to}\n"
            f"{T}crossFilteringBehavior: oneDirection\n{T}fromCardinality: many\n"
            f"{T}toCardinality: one\n{T}isActive: true")

w_text(os.path.join(ROOT, SEM, "definition", "relationships.tmdl"), "\n\n".join([
    rel("a1b2c3d4e5f647a8b9c0d1e2f3a4b5c6", "InventoryTransactions.ProductID", "Products.ProductID"),
    rel("b2c3d4e5f6a7a8b9c0d1e2f3a4b5c6d7", "InventoryTransactions.WarehouseID", "Warehouses.WarehouseID"),
    rel("c3d4e5f6a7b8a8b9c0d1e2f3a4b5c6d7e8", "InventoryTransactions.TransactionDate", "Dates.Date"),
    rel("d4e5f6a7b8c9a8b9c0d1e2f3a4b5c6d7e8f9", "Products.SupplierID", "Suppliers.SupplierID")]) + "\n")

txn_cols = ["TransactionID", "ProductID", "WarehouseID", "TransactionDate",
            "TransactionType", "Quantity", "UnitCost", "TotalValue"]
txn_mt = ["Int64.Type", "Int64.Type", "Int64.Type", "type datetime", "type text",
          "Int64.Type", "type number", "type number"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "InventoryTransactions.tmdl"),
f"""table InventoryTransactions

{meas('Total Quantity', 'SUM(InventoryTransactions[Quantity])', '#,##0', 'Net transacted units.')}
{meas('Total Value', 'SUM(InventoryTransactions[TotalValue])', '$#,##0.00', 'Total transacted value at cost.')}
{meas('Transaction Count', 'COUNTROWS(InventoryTransactions)', '#,##0', 'Number of transaction rows.')}
{meas('Units Purchased', 'CALCULATE(SUM(InventoryTransactions[Quantity]), InventoryTransactions[TransactionType] = "Purchase")', '#,##0', 'Units received via purchases.')}
{meas('Units Sold', 'CALCULATE(SUM(InventoryTransactions[Quantity]), InventoryTransactions[TransactionType] = "Sale")', '#,##0', 'Units moved via sales.')}
{meas('Avg Unit Cost', 'AVERAGE(InventoryTransactions[UnitCost])', '$#,##0.00', 'Average unit cost.')}

{col('TransactionID', 'int64', 'TransactionID')}
{col('ProductID', 'int64', 'ProductID')}
{col('WarehouseID', 'int64', 'WarehouseID')}
{col('TransactionDate', 'dateTime', 'TransactionDate')}
{col('TransactionType', 'string', 'TransactionType')}
{col('Quantity', 'int64', 'Quantity')}
{col('UnitCost', 'decimal', 'UnitCost')}
{col('TotalValue', 'decimal', 'TotalValue')}

{m_part('InventoryTransactions', 'InventoryTransactions.csv', txn_cols, txn_mt)}
""")

prod_cols = ["ProductID", "ProductName", "Category", "SubCategory", "SupplierID",
             "UnitCost", "UnitPrice", "ReorderLevel"]
prod_mt = ["Int64.Type", "type text", "type text", "type text", "Int64.Type",
           "type number", "type number", "Int64.Type"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Products.tmdl"),
f"""table Products

{meas('Product Count', 'DISTINCTCOUNT(Products[ProductID])', '#,##0', 'Number of products.')}

{col('ProductID', 'int64', 'ProductID', ['isKey'])}
{col('ProductName', 'string', 'ProductName')}
{col('Category', 'string', 'Category')}
{col('SubCategory', 'string', 'SubCategory')}
{col('SupplierID', 'int64', 'SupplierID')}
{col('UnitCost', 'decimal', 'UnitCost')}
{col('UnitPrice', 'decimal', 'UnitPrice')}
{col('ReorderLevel', 'int64', 'ReorderLevel')}

{m_part('Products', 'Products.csv', prod_cols, prod_mt)}
""")

wh_cols = ["WarehouseID", "WarehouseName", "Region", "City", "Capacity"]
wh_mt = ["Int64.Type", "type text", "type text", "type text", "Int64.Type"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Warehouses.tmdl"),
f"""table Warehouses

{meas('Warehouse Count', 'DISTINCTCOUNT(Warehouses[WarehouseID])', '#,##0', 'Number of warehouses.')}

{col('WarehouseID', 'int64', 'WarehouseID', ['isKey'])}
{col('WarehouseName', 'string', 'WarehouseName')}
{col('Region', 'string', 'Region')}
{col('City', 'string', 'City')}
{col('Capacity', 'int64', 'Capacity')}

{m_part('Warehouses', 'Warehouses.csv', wh_cols, wh_mt)}
""")

sup_cols = ["SupplierID", "SupplierName", "Country", "LeadTimeDays"]
sup_mt = ["Int64.Type", "type text", "type text", "Int64.Type"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Suppliers.tmdl"),
f"""table Suppliers

{meas('Supplier Count', 'DISTINCTCOUNT(Suppliers[SupplierID])', '#,##0', 'Number of suppliers.')}

{col('SupplierID', 'int64', 'SupplierID', ['isKey'])}
{col('SupplierName', 'string', 'SupplierName')}
{col('Country', 'string', 'Country')}
{col('LeadTimeDays', 'int64', 'LeadTimeDays')}

{m_part('Suppliers', 'Suppliers.csv', sup_cols, sup_mt)}
""")

d_cols = ["Date", "Year", "Quarter", "Month", "MonthName", "DayOfWeek",
          "DayOfMonth", "WeekOfYear", "IsWeekend"]
d_mt = ["type datetime", "Int64.Type", "Int64.Type", "Int64.Type", "type text",
        "type text", "Int64.Type", "Int64.Type", "type logical"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Dates.tmdl"),
"\n".join(["table Dates", "",
  col('Date', 'dateTime', 'Date', ['isKey']), col('Year', 'int64', 'Year'),
  col('Quarter', 'int64', 'Quarter'), col('Month', 'int64', 'Month'),
  col('MonthName', 'string', 'MonthName'), col('DayOfWeek', 'string', 'DayOfWeek'),
  col('DayOfMonth', 'int64', 'DayOfMonth'), col('WeekOfYear', 'int64', 'WeekOfYear'),
  col('IsWeekend', 'boolean', 'IsWeekend'), "",
  m_part('Dates', 'Dates.csv', d_cols, d_mt), ""]))

# ---------- Report ----------
w_json(os.path.join(ROOT, REP, "definition.pbir"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": f"../{SEM}"}}})
w_json(os.path.join(ROOT, REP, "definition", "version.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "version": "2.0.0"})
w_json(os.path.join(ROOT, REP, "definition", "report.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json",
    "themeCollection": {"baseTheme": {"name": "CY26SU02",
        "reportVersionAtImport": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
        "type": "SharedResources"}},
    "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
        "items": [{"name": "CY26SU02", "path": "BaseThemes/CY26SU02.json", "type": "BaseTheme"}]}],
    "settings": {"useStylableVisualContainerHeader": True,
        "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True,
        "allowChangeFilterTypes": True, "useEnhancedTooltips": True,
        "useDefaultAggregateDisplayName": True}})
w_text(os.path.join(ROOT, REP, "StaticResources", "SharedResources", "BaseThemes", "CY26SU02.json"),
       json.dumps({"name": "CY26SU02",
        "dataColors": ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7", "#744EC2", "#D9B300", "#D9B300"],
        "background": "#FFFFFF", "foreground": "#252423", "tableAccent": "#118DFF"}, indent=2) + "\n")

VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"
import secrets
hex20 = lambda: secrets.token_hex(10)

def cref(e, p):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
            "queryRef": f"{e}.{p}", "nativeQueryRef": p, "active": True}

def mref(e, p):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
            "queryRef": f"{e}.{p}", "nativeQueryRef": p}

FT = "InventoryTransactions"
def visual(name, vtype, x, y, w, h, order, qs, sort=None, drill=True):
    v = {"$schema": VC, "name": name,
         "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": order},
         "visual": {"visualType": vtype, "query": {"queryState": qs}}}
    if sort:
        v["visual"]["query"]["sortDefinition"] = sort
    if drill and vtype != "slicer":
        v["visual"]["drillFilterOtherVisuals"] = True
    v["visual"]["visualContainerObjects"] = {"title": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}}}}]}
    return v

def card(measure, entity, x, y, w=295, h=140, order=1000):
    return visual(hex20(), "cardVisual", x, y, w, h, order,
                 {"Data": {"projections": [mref(entity, measure)]}})

def desc_sort(entity, measure):
    return {"sort": [{"field": mref(entity, measure)["field"], "direction": "Descending"}]}

page1, page2, page3 = "a1b2c3d4e5f60718293a4", "b2c3d4e5f60718293a4b5", "c3d4e5f60718293a4b5c6"
p1 = [
    card("Total Value", FT, 20, 20, 295, 140, 1000),
    card("Total Quantity", FT, 325, 20, 295, 140, 2000),
    card("Transaction Count", FT, 630, 20, 295, 140, 3000),
    card("Avg Unit Cost", FT, 935, 20, 295, 140, 4000),
    visual(hex20(), "lineChart", 20, 180, 620, 300, 5000,
           {"Category": {"projections": [cref("Dates", "MonthName")]},
            "Y": {"projections": [mref(FT, "Total Quantity")]}}),
    visual(hex20(), "clusteredBarChart", 650, 180, 600, 300, 6000,
           {"Category": {"projections": [cref("Products", "Category")]},
            "Y": {"projections": [mref(FT, "Total Value")]}},
           sort=desc_sort(FT, "Total Value")),
    visual(hex20(), "donutChart", 20, 500, 400, 200, 7000,
           {"Category": {"projections": [cref("Warehouses", "WarehouseName")]},
            "Y": {"projections": [mref(FT, "Total Quantity")]}}),
    visual(hex20(), "clusteredColumnChart", 430, 500, 400, 200, 8000,
           {"Category": {"projections": [cref(FT, "TransactionType")]},
            "Y": {"projections": [mref(FT, "Transaction Count")]}}),
    visual(hex20(), "tableEx", 840, 500, 410, 200, 9000,
           {"Values": {"projections": [cref("Products", "Category"),
               mref(FT, "Units Purchased"), mref(FT, "Units Sold"), mref(FT, "Total Value")]}}),
]
p2 = [
    visual(hex20(), "slicer", 20, 20, 300, 140, 1000,
           {"Values": {"projections": [cref("Products", "Category")]}}, drill=False),
    visual(hex20(), "slicer", 330, 20, 300, 140, 2000,
           {"Values": {"projections": [cref("Warehouses", "Region")]}}, drill=False),
    card("Units Purchased", FT, 640, 20, 295, 140, 3000),
    card("Supplier Count", "Suppliers", 945, 20, 285, 140, 4000),
    visual(hex20(), "clusteredBarChart", 20, 180, 610, 300, 5000,
           {"Category": {"projections": [cref("Warehouses", "WarehouseName")]},
            "Y": {"projections": [mref(FT, "Total Value")]}},
           sort=desc_sort(FT, "Total Value")),
    visual(hex20(), "pieChart", 640, 180, 610, 300, 6000,
           {"Category": {"projections": [cref("Suppliers", "Country")]},
            "Y": {"projections": [mref(FT, "Total Quantity")]}}),
    visual(hex20(), "tableEx", 20, 500, 1230, 200, 7000,
           {"Values": {"projections": [cref("Products", "ProductName"),
               cref("Products", "Category"), mref(FT, "Total Quantity"),
               mref(FT, "Total Value"), cref("Products", "ReorderLevel")]}}),
]
p3 = [
    visual(hex20(), "slicer", 20, 20, 300, 120, 1000,
           {"Values": {"projections": [cref("Dates", "Year")]}}, drill=False),
    card("Units Sold", FT, 330, 20, 300, 120, 2000),
    card("Warehouse Count", "Warehouses", 640, 20, 300, 120, 3000),
    card("Product Count", "Products", 950, 20, 300, 120, 4000),
    visual(hex20(), "lineStackedColumnComboChart", 20, 160, 1230, 300, 5000,
           {"Category": {"projections": [cref("Dates", "Month")]},
            "Y": {"projections": [mref(FT, "Total Quantity")]},
            "Y2": {"projections": [mref(FT, "Total Value")]}}),
    visual(hex20(), "tableEx", 20, 480, 1230, 220, 6000,
           {"Values": {"projections": [cref("Dates", "Date"),
               cref("Products", "ProductName"), cref("Warehouses", "WarehouseName"),
               mref(FT, "Total Quantity"), cref(FT, "TransactionType")]}}),
]
all_pages = [(page1, "Stock Overview", p1), (page2, "Warehouse & Supplier", p2),
             (page3, "Trends & Details", p3)]

_pages = os.path.join(ROOT, REP, "definition", "pages")
if os.path.isdir(_pages):
    shutil.rmtree(_pages)
w_json(os.path.join(_pages, "pages.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [page1, page2, page3], "activePageName": page1})
for pid, dname, visuals in all_pages:
    w_json(os.path.join(_pages, pid, "page.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": pid, "displayName": dname, "displayOption": "FitToPage",
        "height": 720, "width": 1280})
    for v in visuals:
        w_json(os.path.join(_pages, pid, "visuals", v["name"], "visual.json"), v)

print(f"Built {PROJECT}: {len(all_pages)} pages, {sum(len(v) for _, _, v in all_pages)} visuals")
