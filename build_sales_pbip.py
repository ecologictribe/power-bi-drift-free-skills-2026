"""Builds SalesAnalytics PBIP project (TMDL + PBIR) from ./data CSVs.
Writes UTF-8 without BOM, tabs for TMDL, forward-slash M paths.
Run: python build_sales_pbip.py
"""
import json
import os
import secrets
import uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = "SalesAnalytics"
DATA_DIR_FWD = "D:/power_new/data"  # exact local data folder, forward slashes
SEM = f"{PROJECT}.SemanticModel"
REP = f"{PROJECT}.Report"

def hex20():
    return secrets.token_hex(10)

def w_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")

def w_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # utf-8 without BOM: plain "utf-8" (not utf-8-sig), \n newlines
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def col_block(col, dtype, source=None, extra=None):
    tab = "\t"
    s = f"{tab}column {col if ' ' not in col and '.' not in col else repr(col).replace(chr(34), chr(39))}\n" if False else None
    # Build column header with quoting when needed
    name = col if all(c.isalnum() or c == '_' for c in col) else f"'{col}'"
    lines = [f"{tab}column {name}", f"{tab}{tab}dataType: {dtype}"]
    if source:
        lines.append(f"{tab}{tab}sourceColumn: {source}")
    lines.append(f"{tab}{tab}summarizeBy: none")
    if extra:
        for e in extra:
            lines.append(f"{tab}{tab}{e}")
    return "\n".join(lines)

def measure_block(name, expr, fmt, desc):
    tab = "\t"
    # multi-line DAX wrapped in ``` blocks per TMDL guidance
    lines = [
        f"{tab}/// {desc}",
        f"{tab}measure '{name}' = ```",
        f"{tab}{tab}{expr}",
        f"{tab}\t```",
        f"{tab}{tab}formatString: {fmt}",
    ]
    return "\n".join(lines)

# ---------- 1. .pbip ----------
w_json(os.path.join(ROOT, f"{PROJECT}.pbip"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0",
    "artifacts": [{"report": {"path": REP}}],
    "settings": {"enableAutoRecovery": True},
})

# ---------- 2. SemanticModel ----------
w_json(os.path.join(ROOT, SEM, "definition.pbism"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.0",
    "settings": {},
})
for item_type, disp in [("SemanticModel", PROJECT), ("Report", PROJECT)]:
    folder = SEM if item_type == "SemanticModel" else REP
    w_json(os.path.join(ROOT, folder, ".platform"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": item_type, "displayName": disp},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())},
    })

T = "\t"
w_text(os.path.join(ROOT, SEM, "definition", "database.tmdl"),
f"""database {PROJECT}
{T}compatibilityLevel: 1702
{T}compatibilityMode: powerBI
""")

w_text(os.path.join(ROOT, SEM, "definition", "model.tmdl"),
f"""model Model
{T}culture: en-US
{T}defaultPowerBIDataSourceVersion: powerBI_V3
{T}sourceQueryCulture: en-US
{T}discourageImplicitMeasures: true

ref table Orders
ref table Customers
ref table Products
ref table Dates
""")

# Relationships: forest, all active, no /// comments (forbidden on relationships)
w_text(os.path.join(ROOT, SEM, "definition", "relationships.tmdl"),
f"""relationship c9a4e2f1b3d54a6f9e8d1234567890ab
{T}fromColumn: Orders.CustomerID
{T}toColumn: Customers.CustomerID
{T}crossFilteringBehavior: oneDirection
{T}fromCardinality: many
{T}toCardinality: one
{T}isActive: true

relationship d4b5f6a7c8e94b0a1f2d3456789abcdef0
{T}fromColumn: Orders.ProductID
{T}toColumn: Products.ProductID
{T}crossFilteringBehavior: oneDirection
{T}fromCardinality: many
{T}toCardinality: one
{T}isActive: true

relationship e5c6a7b8d9f04c1b2a3e456789abcdef12
{T}fromColumn: Orders.OrderDate
{T}toColumn: Dates.Date
{T}crossFilteringBehavior: oneDirection
{T}fromCardinality: many
{T}toCardinality: one
{T}isActive: true
""")

def m_csv(filename, columns, types):
    cols = ", ".join([f'"{c}"' for c in columns])
    type_pairs = ", ".join([f'{{"{c}", {t}}}' for c, t in zip(columns, types)])
    return (
f"""{T}partition {filename.replace('.csv','')} = m
{T}{T}mode: import
{T}{T}source =
{T}{T}{T}let
{T}{T}{T}{T}// Load local CSV from project data folder
{T}{T}{T}{T}Source = Csv.Document(File.Contents("{DATA_DIR_FWD}/{filename}"), [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.None]),
{T}{T}{T}{T}#"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
{T}{T}{T}{T}#"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{type_pairs}}})
{T}{T}{T}in
{T}{T}{T}{T}#"Changed Type"
{T}{T}annotation PBI_ResultType = Table"""
    )

orders_cols = ["OrderID","CustomerID","ProductID","OrderDate","Quantity","Amount","Cost","Status"]
orders_mtypes = ["Int64.Type","Int64.Type","Int64.Type","type datetime","Int64.Type","type number","type number","type text"]
orders_tmdl = f"""table Orders

{measure_block('Total Sales', 'SUM(Orders[Amount])', '$#,##0.00', 'Total sales amount across all orders.')}
{measure_block('Total Cost', 'SUM(Orders[Cost])', '$#,##0.00', 'Total cost across all orders.')}
{measure_block('Total Profit', '[Total Sales] - [Total Cost]', '$#,##0.00', 'Total profit (sales minus cost).')}
{measure_block('Profit Margin %', 'DIVIDE([Total Profit], [Total Sales], 0)', '0.00%', 'Profit margin as share of sales.')}
{measure_block('Total Quantity', 'SUM(Orders[Quantity])', '#,##0', 'Total units sold.')}
{measure_block('Order Count', 'COUNTROWS(Orders)', '#,##0', 'Number of order rows.')}
{measure_block('Avg Order Value', 'DIVIDE([Total Sales], [Order Count], 0)', '$#,##0.00', 'Average sales per order.')}
{measure_block('Completed Sales', 'CALCULATE([Total Sales], Orders[Status] = "Completed")', '$#,##0.00', 'Sales for completed orders only.')}

{col_block('OrderID','int64','OrderID')}
{col_block('CustomerID','int64','CustomerID')}
{col_block('ProductID','int64','ProductID')}
{col_block('OrderDate','dateTime','OrderDate')}
{col_block('Quantity','int64','Quantity')}
{col_block('Amount','decimal','Amount')}
{col_block('Cost','decimal','Cost')}
{col_block('Status','string','Status')}

{m_csv('Orders.csv', orders_cols, orders_mtypes)}
"""
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Orders.tmdl"), orders_tmdl)

cust_cols = ["CustomerID","CustomerName","Region","Segment","City"]
cust_mtypes = ["Int64.Type","type text","type text","type text","type text"]
cust_tmdl = f"""table Customers

{T}/// Number of customers.
{T}measure 'Customer Count' = ```
{T}{T}DISTINCTCOUNT(Customers[CustomerID])
{T}\t```
{T}{T}formatString: #,##0

{col_block('CustomerID','int64','CustomerID',['isKey'])}
{col_block('CustomerName','string','CustomerName')}
{col_block('Region','string','Region')}
{col_block('Segment','string','Segment')}
{col_block('City','string','City')}

{m_csv('Customers.csv', cust_cols, cust_mtypes)}
"""
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Customers.tmdl"), cust_tmdl)

prod_cols = ["ProductID","ProductName","Category","SubCategory","UnitPrice","Cost"]
prod_mtypes = ["Int64.Type","type text","type text","type text","type number","type number"]
prod_tmdl = f"""table Products

{T}/// Number of products.
{T}measure 'Product Count' = ```
{T}{T}DISTINCTCOUNT(Products[ProductID])
{T}\t```
{T}{T}formatString: #,##0

{col_block('ProductID','int64','ProductID',['isKey'])}
{col_block('ProductName','string','ProductName')}
{col_block('Category','string','Category')}
{col_block('SubCategory','string','SubCategory')}
{col_block('UnitPrice','decimal','UnitPrice')}
{col_block('Cost','decimal','Cost')}

{m_csv('Products.csv', prod_cols, prod_mtypes)}
"""
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Products.tmdl"), prod_tmdl)

dates_cols = ["Date","Year","Quarter","Month","MonthName","DayOfWeek","DayOfMonth","WeekOfYear","IsWeekend"]
dates_mtypes = ["type datetime","Int64.Type","Int64.Type","Int64.Type","type text","type text","Int64.Type","Int64.Type","type logical"]
dates_tmdl = f"""table Dates

{col_block('Date','dateTime','Date',['isKey'])}
{col_block('Year','int64','Year')}
{col_block('Quarter','int64','Quarter')}
{col_block('Month','int64','Month')}
{col_block('MonthName','string','MonthName')}
{col_block('DayOfWeek','string','DayOfWeek')}
{col_block('DayOfMonth','int64','DayOfMonth')}
{col_block('WeekOfYear','int64','WeekOfYear')}
{col_block('IsWeekend','boolean','IsWeekend')}

{m_csv('Dates.csv', dates_cols, dates_mtypes)}
"""
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Dates.tmdl"), dates_tmdl)

# ---------- 3. Report ----------
w_json(os.path.join(ROOT, REP, "definition.pbir"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0",
    "datasetReference": {"byPath": {"path": f"../{SEM}"}},
})
w_json(os.path.join(ROOT, REP, "definition", "version.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "version": "2.0.0",
})
w_json(os.path.join(ROOT, REP, "definition", "report.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json",
    "themeCollection": {
        "baseTheme": {
            "name": "CY26SU02",
            "reportVersionAtImport": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
            "type": "SharedResources",
        }
    },
    "resourcePackages": [{
        "name": "SharedResources",
        "type": "SharedResources",
        "items": [{"name": "CY26SU02", "path": "BaseThemes/CY26SU02.json", "type": "BaseTheme"}],
    }],
    "settings": {
        "useStylableVisualContainerHeader": True,
        "exportDataMode": "AllowSummarized",
        "defaultDrillFilterOtherVisuals": True,
        "allowChangeFilterTypes": True,
        "useEnhancedTooltips": True,
        "useDefaultAggregateDisplayName": True,
    },
})
w_text(os.path.join(ROOT, REP, "StaticResources", "SharedResources", "BaseThemes", "CY26SU02.json"),
json.dumps({"name": "CY26SU02",
 "dataColors": ["#118DFF","#12239E","#E66C37","#6B007B","#E044A7","#744EC2","#D9B300","#D9B300"],
 "background": "#FFFFFF", "foreground": "#252423", "tableAccent": "#118DFF"}, indent=2) + "\n")

VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"

def col_ref(entity, prop):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
            "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop, "active": True}

def meas_ref(entity, prop):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
            "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}

def visual(name, vtype, x, y, w, h, order, query_state, title=None, sort=None, extra_visual=None, drill=True):
    v = {"$schema": VC, "name": name,
         "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": order},
         "visual": {"visualType": vtype, "query": {"queryState": query_state}}}
    if sort:
        v["visual"]["query"]["sortDefinition"] = sort
    if extra_visual:
        v["visual"].update(extra_visual)
    if drill and vtype != "slicer":
        v["visual"]["drillFilterOtherVisuals"] = True
    if title:
        # NOTE: visualContainer/2.7.0 title properties accept ONLY show (plus
        # container-owned props). titleText is rejected as additionalProperty,
        # so custom text is intentionally omitted — Desktop auto-titles from fields.
        v["visual"]["visualContainerObjects"] = {
            "title": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}}}}]}
    return v

def card(title, measure, x, y, w=290, h=140, order=1000):
    return visual(hex20(), "cardVisual", x, y, w, h, order,
                 {"Data": {"projections": [meas_ref("Orders", measure)]}}, title=title)

page1 = "1e5d5184e440013f0a1e"; page2 = "1e130b0d3d73243f0b39"; page3 = "e7d7a9eed58fff691b5e"
pages = [(page1, "Sales Overview"), (page2, "Products & Customers"), (page3, "Trends & Details")]

# Page 1 visuals
p1_visuals = [
    card("Total Sales", "Total Sales", 20, 20, 295, 140, 1000),
    card("Total Profit", "Total Profit", 325, 20, 295, 140, 2000),
    card("Order Count", "Order Count", 630, 20, 295, 140, 3000),
    card("Avg Order Value", "Avg Order Value", 935, 20, 295, 140, 4000),
    visual(hex20(), "lineChart", 20, 180, 620, 300, 5000,
           {"Category": {"projections": [col_ref("Dates", "MonthName")]},
            "Y": {"projections": [meas_ref("Orders", "Total Sales")]}},
           title="Sales by Month"),
    visual(hex20(), "clusteredBarChart", 650, 180, 600, 300, 6000,
           {"Category": {"projections": [col_ref("Products", "Category")]},
            "Y": {"projections": [meas_ref("Orders", "Total Sales")]}},
           title="Sales by Category",
           sort={"sort": [{"field": meas_ref("Orders", "Total Sales")["field"], "direction": "Descending"}]}),
    visual(hex20(), "donutChart", 20, 500, 400, 200, 7000,
           {"Category": {"projections": [col_ref("Customers", "Region")]},
            "Y": {"projections": [meas_ref("Orders", "Total Sales")]}},
           title="Sales by Region"),
    visual(hex20(), "clusteredColumnChart", 430, 500, 400, 200, 8000,
           {"Category": {"projections": [col_ref("Orders", "Status")]},
            "Y": {"projections": [meas_ref("Orders", "Order Count")]}},
           title="Orders by Status"),
    visual(hex20(), "tableEx", 840, 500, 410, 200, 9000,
           {"Values": {"projections": [col_ref("Products", "Category"),
                                       meas_ref("Orders", "Total Sales"),
                                       meas_ref("Orders", "Total Profit"),
                                       meas_ref("Orders", "Profit Margin %")]}},
           title="Category Performance"),
]
# Page 2 visuals
p2_visuals = [
    visual(hex20(), "slicer", 20, 20, 300, 140, 1000,
           {"Values": {"projections": [col_ref("Products", "Category")]}},
           title="Category Slicer"),
    visual(hex20(), "slicer", 330, 20, 300, 140, 2000,
           {"Values": {"projections": [col_ref("Customers", "Region")]}},
           title="Region Slicer"),
    card("Profit Margin %", "Profit Margin %", 640, 20, 295, 140, 3000),
    card("Customer Count", "Customer Count", 945, 20, 285, 140, 4000),
    visual(hex20(), "clusteredBarChart", 20, 180, 610, 300, 5000,
           {"Category": {"projections": [col_ref("Products", "SubCategory")]},
            "Y": {"projections": [meas_ref("Orders", "Total Sales")]}},
           title="Sales by SubCategory",
           sort={"sort": [{"field": meas_ref("Orders", "Total Sales")["field"], "direction": "Descending"}]}),
    visual(hex20(), "pieChart", 640, 180, 610, 300, 6000,
           {"Category": {"projections": [col_ref("Customers", "Segment")]},
            "Y": {"projections": [meas_ref("Orders", "Total Sales")]}},
           title="Sales by Segment"),
    visual(hex20(), "tableEx", 20, 500, 1230, 200, 7000,
           {"Values": {"projections": [col_ref("Products", "ProductName"),
                                       col_ref("Products", "Category"),
                                       meas_ref("Orders", "Total Quantity"),
                                       meas_ref("Orders", "Total Sales"),
                                       meas_ref("Orders", "Total Profit")]}},
           title="Product Details"),
]
# Page 3 visuals
p3_visuals = [
    visual(hex20(), "slicer", 20, 20, 300, 120, 1000,
           {"Values": {"projections": [col_ref("Dates", "Year")]}},
           title="Year Slicer"),
    card("Completed Sales", "Completed Sales", 330, 20, 300, 120, 2000),
    card("Total Quantity", "Total Quantity", 640, 20, 300, 120, 3000),
    card("Total Cost", "Total Cost", 950, 20, 300, 120, 4000),
    visual(hex20(), "lineStackedColumnComboChart", 20, 160, 1230, 300, 5000,
           {"Category": {"projections": [col_ref("Dates", "Month")]},
            "Y": {"projections": [meas_ref("Orders", "Total Sales")]},
            "Y2": {"projections": [meas_ref("Orders", "Total Profit")]}},
           title="Monthly Sales vs Profit"),
    visual(hex20(), "tableEx", 20, 480, 1230, 220, 6000,
           {"Values": {"projections": [col_ref("Dates", "Date"),
                                       col_ref("Customers", "CustomerName"),
                                       col_ref("Products", "ProductName"),
                                       meas_ref("Orders", "Total Sales"),
                                       col_ref("Orders", "Status")]}},
           title="Order Details"),
]

all_pages = [(page1, "Sales Overview", p1_visuals), (page2, "Products & Customers", p2_visuals), (page3, "Trends & Details", p3_visuals)]

# Wipe stale pages (visual IDs are random per run; never leave orphan folders).
import shutil
_pages_dir = os.path.join(ROOT, REP, "definition", "pages")
if os.path.isdir(_pages_dir):
    shutil.rmtree(_pages_dir)

w_json(os.path.join(ROOT, REP, "definition", "pages", "pages.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [page1, page2, page3],
    "activePageName": page1,
})
for pid, dname, visuals in all_pages:
    w_json(os.path.join(ROOT, REP, "definition", "pages", pid, "page.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": pid, "displayName": dname, "displayOption": "FitToPage", "height": 720, "width": 1280,
    })
    for v in visuals:
        vdir = os.path.join(ROOT, REP, "definition", "pages", pid, "visuals", v["name"])
        w_json(os.path.join(vdir, "visual.json"), v)

print(f"Built {PROJECT}: {len(all_pages)} pages, {sum(len(v) for _,_,v in all_pages)} visuals")
