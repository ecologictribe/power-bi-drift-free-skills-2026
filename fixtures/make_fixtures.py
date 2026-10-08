"""Builds the drift gallery: 7 minimal PBIP fixtures, each violating exactly ONE
skill rule so students see the precise validator/Desktop error per bug.
Run from repo root: python fixtures/make_fixtures.py
Regenerating wipes fixtures/broken-*/ (IDs are fixed, so reruns are stable).
"""
import json
import os
import shutil
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = "D:/power_new/data"
T = "\t"
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"

ORDERS_M = (
    f"{T}partition Orders = m\n{T}{T}mode: import\n{T}{T}source =\n{T}{T}{T}let\n"
    f"{T}{T}{T}{T}Source = Csv.Document(File.Contents(\"{DATA}/Orders.csv\"), [Delimiter=\",\", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),\n"
    f"{T}{T}{T}{T}#\"Promoted Headers\" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n"
    f"{T}{T}{T}{T}#\"Changed Type\" = Table.TransformColumnTypes(#\"Promoted Headers\", "
    f'{{\"OrderID\", Int64.Type}}, {{\"CustomerID\", Int64.Type}}, {{\"ProductID\", Int64.Type}}, '
    f'{{\"OrderDate\", type datetime}}, {{\"Quantity\", Int64.Type}}, {{\"Amount\", type number}}, '
    f'{{\"Cost\", type number}}, {{\"Status\", type text}}}})\n'
    f"{T}{T}{T}in\n{T}{T}{T}{T}#\"Changed Type\"\n{T}{T}annotation PBI_ResultType = Table")
CUST_M = (
    f"{T}partition Customers = m\n{T}{T}mode: import\n{T}{T}source =\n{T}{T}{T}let\n"
    f"{T}{T}{T}{T}Source = Csv.Document(File.Contents(\"{DATA}/Customers.csv\"), [Delimiter=\",\", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.None]),\n"
    f"{T}{T}{T}{T}#\"Promoted Headers\" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n"
    f"{T}{T}{T}{T}#\"Changed Type\" = Table.TransformColumnTypes(#\"Promoted Headers\", "
    f'{{\"CustomerID\", Int64.Type}}, {{\"CustomerName\", type text}}, {{\"Region\", type text}}, '
    f'{{\"Segment\", type text}}, {{\"City\", type text}}}})\n'
    f"{T}{T}{T}in\n{T}{T}{T}{T}#\"Changed Type\"\n{T}{T}annotation PBI_ResultType = Table")

ORDERS_T = f"""table Orders

{T}/// Total sales amount.
{T}measure 'Total Sales' = ```
{T}{T}SUM(Orders[Amount])
{T}\t```
{T}{T}formatString: $#,##0.00

{T}column OrderID
{T}{T}dataType: int64
{T}{T}sourceColumn: OrderID
{T}{T}summarizeBy: none
{T}column CustomerID
{T}{T}dataType: int64
{T}{T}sourceColumn: CustomerID
{T}{T}summarizeBy: none
{T}column Amount
{T}{T}dataType: decimal
{T}{T}sourceColumn: Amount
{T}{T}summarizeBy: none

{ORDERS_M}
"""
CUST_T = f"""table Customers

{T}column CustomerID
{T}{T}dataType: int64
{T}{T}sourceColumn: CustomerID
{T}{T}summarizeBy: none
{T}column Region
{T}{T}dataType: string
{T}{T}sourceColumn: Region
{T}{T}summarizeBy: none

{CUST_M}
"""

GOOD_SETTINGS = {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                 "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                 "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}
BAD_SETTINGS = {"filterPaneEnabled": True, "navContentPaneEnabled": True,
                "useStylableVisualContainerHeader": True, "exportDataMode": 1, "queryLimitOption": 3}

def w_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")

def w_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def cref(e, p, native=True):
    pr = {"field": {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
          "queryRef": f"{e}.{p}", "active": True}
    if native:
        pr["nativeQueryRef"] = p
    return pr

def mref(e, p, native=True):
    pr = {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
          "queryRef": f"{e}.{p}"}
    if native:
        pr["nativeQueryRef"] = p
    return pr

def bar(category_entity, category_col, native=True, title_props=None):
    title_props = title_props if title_props is not None else {
        "show": {"expr": {"Literal": {"Value": "true"}}}}
    return {"$schema": VC, "name": "a1b2c3d4e5f60718293a4",
            "position": {"x": 20, "y": 20, "z": 0, "width": 600, "height": 300, "tabOrder": 1000},
            "visual": {
                "visualType": "clusteredBarChart",
                "query": {"queryState": {
                    "Category": {"projections": [cref(category_entity, category_col, native)]},
                    "Y": {"projections": [mref("Orders", "Total Sales", native)]}}},
                "drillFilterOtherVisuals": True,
                "visualContainerObjects": {"title": [{"properties": title_props}]}}}

FIXTURES = {
    # slug: (ProjectName, mutation kwargs)
    "broken-rel-enum":      {"rel": "singleDirection"},
    "broken-native-queryref": {"native": False},
    "broken-display-option": {"display": 0},
    "broken-settings":      {"settings": "bad"},
    "broken-title-text":    {"title_text": True},
    "broken-combo-series":  {"combo": True},
    "broken-slicer-filters": {"slicer": True},
}

for slug, mut in FIXTURES.items():
    proj, sem, rep = "BrokenGallery", f"BrokenGallery.SemanticModel", "BrokenGallery.Report"
    base = os.path.join(ROOT, "fixtures", slug)
    if os.path.isdir(base):
        shutil.rmtree(base)

    w_json(os.path.join(base, f"{proj}.pbip"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": rep}}],
        "settings": {"enableAutoRecovery": True}})
    w_json(os.path.join(base, sem, "definition.pbism"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0", "settings": {}})
    for itype in ("SemanticModel", "Report"):
        w_json(os.path.join(base, sem if itype == "SemanticModel" else rep, ".platform"), {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": itype, "displayName": proj},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}})
    w_text(os.path.join(base, sem, "definition", "database.tmdl"),
           f"database {proj}\n{T}compatibilityLevel: 1702\n{T}compatibilityMode: powerBI\n")
    w_text(os.path.join(base, sem, "definition", "model.tmdl"),
           f"model Model\n{T}culture: en-US\n{T}defaultPowerBIDataSourceVersion: powerBI_V3\n"
           f"{T}sourceQueryCulture: en-US\n\nref table Orders\nref table Customers\n")
    w_text(os.path.join(base, sem, "definition", "relationships.tmdl"),
           f"relationship a1b2c3d4e5f60718293a4b5c6d7e8f9\n{T}fromColumn: Orders.CustomerID\n"
           f"{T}toColumn: Customers.CustomerID\n"
           f"{T}crossFilteringBehavior: {mut.get('rel', 'oneDirection')}\n"
           f"{T}fromCardinality: many\n{T}toCardinality: one\n{T}isActive: true\n")
    w_text(os.path.join(base, sem, "definition", "tables", "Orders.tmdl"), ORDERS_T)
    w_text(os.path.join(base, sem, "definition", "tables", "Customers.tmdl"), CUST_T)

    w_json(os.path.join(base, rep, "definition.pbir"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{sem}"}}})
    w_json(os.path.join(base, rep, "definition", "version.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})
    w_json(os.path.join(base, rep, "definition", "report.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY26SU02",
            "reportVersionAtImport": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
            "type": "SharedResources"}},
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
            "items": [{"name": "CY26SU02", "path": "BaseThemes/CY26SU02.json", "type": "BaseTheme"}]}],
        "settings": BAD_SETTINGS if mut.get("settings") == "bad" else GOOD_SETTINGS})
    w_text(os.path.join(base, rep, "StaticResources", "SharedResources", "BaseThemes", "CY26SU02.json"),
           json.dumps({"name": "CY26SU02"}, indent=2) + "\n")

    pid = "b1c2d3e4f506172839a4"
    w_json(os.path.join(base, rep, "definition", "pages", "pages.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [pid], "activePageName": pid})
    w_json(os.path.join(base, rep, "definition", "pages", pid, "page.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": pid, "displayName": "Gallery", "displayOption": mut.get("display", "FitToPage"),
        "height": 720, "width": 1280})

    if mut.get("combo"):
        v = {"$schema": VC, "name": "c1d2e3f4a506172839b5",
             "position": {"x": 20, "y": 20, "z": 0, "width": 600, "height": 300, "tabOrder": 1000},
             "visual": {"visualType": "lineStackedColumnComboChart",
                        "query": {"queryState": {
                            "Category": {"projections": [cref("Customers", "Region")]},
                            "Y": {"projections": [mref("Orders", "Total Sales")]},
                            "Series": {"projections": [cref("Customers", "Region")]}}},
                        "drillFilterOtherVisuals": True}}
    elif mut.get("slicer"):
        v = {"$schema": VC, "name": "c1d2e3f4a506172839b5",
             "position": {"x": 20, "y": 20, "z": 0, "width": 300, "height": 140, "tabOrder": 1000},
             "visual": {"visualType": "slicer",
                        "query": {"queryState": {
                            "Values": {"projections": [cref("Customers", "Region")]},
                            "Filters": {"projections": []}}}}}
    else:
        tp = ({"show": {"expr": {"Literal": {"Value": "true"}}},
               "titleText": {"expr": {"Literal": {"Value": "'Sales'"}}}}
              if mut.get("title_text") else None)
        v = bar("Customers", "Region", native=mut.get("native", True), title_props=tp)
    w_json(os.path.join(base, rep, "definition", "pages", pid, "visuals", v["name"], "visual.json"), v)
    print(f"built fixtures/{slug}")

print("done: 7 fixtures")
