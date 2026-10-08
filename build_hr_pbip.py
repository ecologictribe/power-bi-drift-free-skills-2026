"""Builds HRAnalytics PBIP from ./data_hr CSVs.
New constructs vs sales/inventory: funnel, gauge, kpi, pivotTable visuals,
Dates hierarchy, one INACTIVE relationship (forest rule).
Run: python build_hr_pbip.py
"""
import json
import os
import shutil
import uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = "HRAnalytics"
DATA_DIR_FWD = "D:/power_new/data_hr"
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

w_json(os.path.join(ROOT, f"{PROJECT}.pbip"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": REP}}],
    "settings": {"enableAutoRecovery": True}})
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
       f"ref table Employees\nref table Recruitment\nref table Departments\nref table Dates\n")

def rel(guid, frm, to, active=True):
    return (f"relationship {guid}\n{T}fromColumn: {frm}\n{T}toColumn: {to}\n"
            f"{T}crossFilteringBehavior: oneDirection\n{T}fromCardinality: many\n"
            f"{T}toCardinality: one\n{T}isActive: {'true' if active else 'false'}")

# NOTE: Recruitment.ApplicationDate -> Dates.Date is INACTIVE: two facts sharing
# Departments AND Dates would otherwise create two active paths between
# Employees and Recruitment (ambiguous-path load failure). Use USERELATIONSHIP
# in DAX when that path is needed.
w_text(os.path.join(ROOT, SEM, "definition", "relationships.tmdl"), "\n\n".join([
    rel("e1f2a3b4c5d647e8f9a0b1c2d3e4f5a6", "Employees.DepartmentID", "Departments.DepartmentID"),
    rel("f2a3b4c5d6e7e8f9a0b1c2d3e4f5a6b7", "Employees.HireDate", "Dates.Date"),
    rel("a3b4c5d6e7f8e8f9a0b1c2d3e4f5a6b7c8", "Recruitment.DepartmentID", "Departments.DepartmentID"),
    rel("b4c5d6e7f8a9e8f9a0b1c2d3e4f5a6b7c8d9", "Recruitment.ApplicationDate", "Dates.Date", active=False)]) + "\n")

emp_cols = ["EmployeeID", "Gender", "Age", "DepartmentID", "JobLevel", "HireDate", "Salary", "Attrition"]
emp_mt = ["Int64.Type", "type text", "Int64.Type", "Int64.Type", "type text", "type datetime", "type number", "type text"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Employees.tmdl"),
f"""table Employees

{meas('Headcount', 'COUNTROWS(Employees)', '#,##0', 'Total employees.')}
{meas('Attrition Count', 'CALCULATE(COUNTROWS(Employees), Employees[Attrition] = "Yes")', '#,##0', 'Employees who left.')}
{meas('Attrition Rate', 'DIVIDE([Attrition Count], [Headcount], 0)', '0.00%', 'Share of headcount lost.')}
{meas('Avg Salary', 'AVERAGE(Employees[Salary])', '$#,##0.00', 'Average salary.')}
{meas('Headcount Target', '500', '#,##0', 'Workforce plan target (KPI goal).')}
{meas('Target Attrition Rate', '0.15', '0.00%', 'Tolerated attrition (gauge target).')}

{col('EmployeeID', 'int64', 'EmployeeID')}
{col('Gender', 'string', 'Gender')}
{col('Age', 'int64', 'Age')}
{col('DepartmentID', 'int64', 'DepartmentID')}
{col('JobLevel', 'string', 'JobLevel')}
{col('HireDate', 'dateTime', 'HireDate')}
{col('Salary', 'decimal', 'Salary')}
{col('Attrition', 'string', 'Attrition')}

{m_part('Employees', 'Employees.csv', emp_cols, emp_mt)}
""")

rec_cols = ["ApplicationID", "DepartmentID", "Stage", "StageOrder", "ApplicationDate"]
rec_mt = ["Int64.Type", "Int64.Type", "type text", "Int64.Type", "type datetime"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Recruitment.tmdl"),
f"""table Recruitment

{meas('Applications', 'COUNTROWS(Recruitment)', '#,##0', 'Stage-reached application rows (funnel counts).')}
{meas('Hires', 'CALCULATE(COUNTROWS(Recruitment), Recruitment[Stage] = "Hired")', '#,##0', 'Hired applications.')}
{meas('Hire Rate', 'DIVIDE([Hires], CALCULATE(COUNTROWS(Recruitment), Recruitment[Stage] = "Applied"), 0)', '0.00%', 'Hired share of applicants.')}

{col('ApplicationID', 'int64', 'ApplicationID')}
{col('DepartmentID', 'int64', 'DepartmentID')}
{col('Stage', 'string', 'Stage')}
{col('StageOrder', 'int64', 'StageOrder')}
{col('ApplicationDate', 'dateTime', 'ApplicationDate')}

{m_part('Recruitment', 'Recruitment.csv', rec_cols, rec_mt)}
""")

dept_cols = ["DepartmentID", "DeptName", "Location"]
dept_mt = ["Int64.Type", "type text", "type text"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Departments.tmdl"),
f"""table Departments

{meas('Dept Count', 'DISTINCTCOUNT(Departments[DepartmentID])', '#,##0', 'Number of departments.')}

{col('DepartmentID', 'int64', 'DepartmentID', ['isKey'])}
{col('DeptName', 'string', 'DeptName')}
{col('Location', 'string', 'Location')}

{m_part('Departments', 'Departments.csv', dept_cols, dept_mt)}
""")

d_cols = ["Date", "Year", "Quarter", "Month", "MonthName", "DayOfWeek", "DayOfMonth", "WeekOfYear", "IsWeekend"]
d_mt = ["type datetime", "Int64.Type", "Int64.Type", "Int64.Type", "type text", "type text", "Int64.Type", "Int64.Type", "type logical"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Dates.tmdl"),
"\n".join(["table Dates", "",
  col('Date', 'dateTime', 'Date', ['isKey']), col('Year', 'int64', 'Year'),
  col('Quarter', 'int64', 'Quarter'), col('Month', 'int64', 'Month'),
  col('MonthName', 'string', 'MonthName'), col('DayOfWeek', 'string', 'DayOfWeek'),
  col('DayOfMonth', 'int64', 'DayOfMonth'), col('WeekOfYear', 'int64', 'WeekOfYear'),
  col('IsWeekend', 'boolean', 'IsWeekend'), "",
  f"{T}hierarchy 'Calendar'",
  f"{T}{T}level Year", f"{T}{T}{T}column: Year",
  f"{T}{T}level Quarter", f"{T}{T}{T}column: Quarter",
  f"{T}{T}level Month", f"{T}{T}{T}column: Month", "",
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
    "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
        "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
        "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}})
w_text(os.path.join(ROOT, REP, "StaticResources", "SharedResources", "BaseThemes", "CY26SU02.json"),
       json.dumps({"name": "CY26SU02",
        "dataColors": ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7", "#744EC2", "#D9B300", "#D9B300"],
        "background": "#FFFFFF", "foreground": "#252423", "tableAccent": "#118DFF"}, indent=2) + "\n")

VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"
import secrets
hex20 = lambda: secrets.token_hex(10)
EMP = "Employees"

def cref(e, p):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
            "queryRef": f"{e}.{p}", "nativeQueryRef": p, "active": True}

def mref(e, p):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
            "queryRef": f"{e}.{p}", "nativeQueryRef": p}

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
    return visual(hex20(), "cardVisual", x, y, w, h, order, {"Data": {"projections": [mref(entity, measure)]}})

page1, page2, page3 = "d4e5f6a7b8c9012345678", "e5f6a7b8c9d0123456789", "f6a7b8c9d0e123456789a"
p1 = [
    card("Headcount", EMP, 20, 20, 295, 140, 1000),
    card("Attrition Rate", EMP, 325, 20, 295, 140, 2000),
    card("Avg Salary", EMP, 630, 20, 295, 140, 3000),
    card("Applications", "Recruitment", 935, 20, 295, 140, 4000),
    visual(hex20(), "clusteredBarChart", 20, 180, 620, 300, 5000,
           {"Category": {"projections": [cref("Departments", "DeptName")]},
            "Y": {"projections": [mref(EMP, "Headcount")]}},
           sort={"sort": [{"field": mref(EMP, "Headcount")["field"], "direction": "Descending"}]}),
    visual(hex20(), "donutChart", 650, 180, 600, 300, 6000,
           {"Category": {"projections": [cref(EMP, "Gender")]},
            "Y": {"projections": [mref(EMP, "Headcount")]}}),
    visual(hex20(), "clusteredColumnChart", 20, 500, 610, 200, 7000,
           {"Category": {"projections": [cref("Dates", "MonthName")]},
            "Y": {"projections": [mref("Recruitment", "Hires")]}}),
    visual(hex20(), "tableEx", 640, 500, 620, 200, 8000,
           {"Values": {"projections": [cref("Departments", "DeptName"), mref(EMP, "Headcount"),
               mref(EMP, "Attrition Count"), mref(EMP, "Avg Salary")]}}),
]
p2 = [
    visual(hex20(), "slicer", 20, 20, 300, 140, 1000,
           {"Values": {"projections": [cref(EMP, "Gender")]}}, drill=False),
    visual(hex20(), "slicer", 330, 20, 300, 140, 2000,
           {"Values": {"projections": [cref("Departments", "DeptName")]}}, drill=False),
    card("Hire Rate", "Recruitment", 640, 20, 295, 140, 3000),
    card("Dept Count", "Departments", 945, 20, 285, 140, 4000),
    visual(hex20(), "funnel", 20, 180, 400, 300, 5000,
           {"Category": {"projections": [cref("Recruitment", "Stage")]},
            "Y": {"projections": [mref("Recruitment", "Applications")]}},
           sort={"sort": [{"field": cref("Recruitment", "StageOrder")["field"], "direction": "Ascending"}]}),
    visual(hex20(), "gauge", 430, 180, 400, 300, 6000,
           {"Y": {"projections": [mref(EMP, "Attrition Rate")]},
            "TargetValue": {"projections": [mref(EMP, "Target Attrition Rate")]}}),
    visual(hex20(), "kpi", 840, 180, 410, 300, 7000,
           {"Indicator": {"projections": [mref(EMP, "Headcount")]},
            "Goal": {"projections": [mref(EMP, "Headcount Target")]},
            "TrendLine": {"projections": [cref("Dates", "Month")]}}),
    visual(hex20(), "pivotTable", 20, 500, 1230, 200, 8000,
           {"Rows": {"projections": [cref("Departments", "DeptName")]},
            "Columns": {"projections": [cref("Dates", "Year")]},
            "Values": {"projections": [mref(EMP, "Headcount")]}}),
]
p3 = [
    visual(hex20(), "slicer", 20, 20, 300, 120, 1000,
           {"Values": {"projections": [cref("Dates", "Year")]}}, drill=False),
    card("Hires", "Recruitment", 330, 20, 300, 120, 2000),
    card("Attrition Count", EMP, 640, 20, 300, 120, 3000),
    card("Avg Salary", EMP, 950, 20, 300, 120, 4000),
    visual(hex20(), "lineChart", 20, 160, 1230, 300, 5000,
           {"Category": {"projections": [cref("Dates", "Month")]},
            "Y": {"projections": [mref("Recruitment", "Hires")]},
            "Series": {"projections": [cref("Dates", "Year")]}}),
    visual(hex20(), "tableEx", 20, 480, 1230, 220, 6000,
           {"Values": {"projections": [cref(EMP, "JobLevel"), cref("Departments", "DeptName"),
               cref(EMP, "Gender"), mref(EMP, "Avg Salary"), cref(EMP, "Attrition")]}}),
]
all_pages = [(page1, "Workforce Overview", p1), (page2, "Hiring Funnel", p2), (page3, "Trends & Details", p3)]

_pages = os.path.join(ROOT, REP, "definition", "pages")
if os.path.isdir(_pages):
    shutil.rmtree(_pages)
w_json(os.path.join(_pages, "pages.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [page1, page2, page3], "activePageName": page1})
for pid, dname, visuals in all_pages:
    w_json(os.path.join(_pages, pid, "page.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": pid, "displayName": dname, "displayOption": "FitToPage", "height": 720, "width": 1280})
    for v in visuals:
        w_json(os.path.join(_pages, pid, "visuals", v["name"], "visual.json"), v)

print(f"Built {PROJECT}: {len(all_pages)} pages, {sum(len(v) for _, _, v in all_pages)} visuals")
