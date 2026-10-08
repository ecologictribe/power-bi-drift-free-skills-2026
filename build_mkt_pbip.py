"""Builds MarketingAnalytics PBIP from ./data_mkt CSVs.
New: scatterChart (Category+X+Y+Size). Run: python build_mkt_pbip.py
"""
import json
import os
import shutil
import uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = "MarketingAnalytics"
DATA_DIR_FWD = "D:/power_new/data_mkt"
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
       f"ref table DailySpend\nref table Channels\nref table Campaigns\nref table Dates\n")

def rel(guid, frm, to):
    return (f"relationship {guid}\n{T}fromColumn: {frm}\n{T}toColumn: {to}\n"
            f"{T}crossFilteringBehavior: oneDirection\n{T}fromCardinality: many\n"
            f"{T}toCardinality: one\n{T}isActive: true")

w_text(os.path.join(ROOT, SEM, "definition", "relationships.tmdl"), "\n\n".join([
    rel("d1e2f3a4b5c60718293a4b5c6d7e8f9", "DailySpend.ChannelID", "Channels.ChannelID"),
    rel("e2f3a4b5c6d0718293a4b5c6d7e8f9a0", "DailySpend.CampaignID", "Campaigns.CampaignID"),
    rel("f3a4b5c6d7e018293a4b5c6d7e8f9a0b1", "DailySpend.SpendDate", "Dates.Date")]) + "\n")

sp_cols = ["SpendID", "ChannelID", "CampaignID", "SpendDate", "Spend", "Impressions",
           "Clicks", "Conversions", "Revenue"]
sp_mt = ["Int64.Type", "Int64.Type", "Int64.Type", "type datetime", "type number",
         "Int64.Type", "Int64.Type", "Int64.Type", "type number"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "DailySpend.tmdl"),
f"""table DailySpend

{meas('Total Spend', 'SUM(DailySpend[Spend])', '$#,##0.00', 'Total media spend.')}
{meas('Total Revenue', 'SUM(DailySpend[Revenue])', '$#,##0.00', 'Attributed revenue.')}
{meas('ROAS', 'DIVIDE([Total Revenue], [Total Spend], 0)', '0.00', 'Return on ad spend.')}
{meas('Total Conversions', 'SUM(DailySpend[Conversions])', '#,##0', 'Total conversions.')}
{meas('Total Clicks', 'SUM(DailySpend[Clicks])', '#,##0', 'Total clicks.')}
{meas('CTR', 'DIVIDE(SUM(DailySpend[Clicks]), SUM(DailySpend[Impressions]), 0)', '0.00%', 'Click-through rate.')}

{col('SpendID', 'int64', 'SpendID')}
{col('ChannelID', 'int64', 'ChannelID')}
{col('CampaignID', 'int64', 'CampaignID')}
{col('SpendDate', 'dateTime', 'SpendDate')}
{col('Spend', 'decimal', 'Spend')}
{col('Impressions', 'int64', 'Impressions')}
{col('Clicks', 'int64', 'Clicks')}
{col('Conversions', 'int64', 'Conversions')}
{col('Revenue', 'decimal', 'Revenue')}

{m_part('DailySpend', 'DailySpend.csv', sp_cols, sp_mt)}
""")

ch_cols = ["ChannelID", "Channel", "Category"]
ch_mt = ["Int64.Type", "type text", "type text"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Channels.tmdl"),
f"""table Channels

{meas('Channel Count', 'DISTINCTCOUNT(Channels[ChannelID])', '#,##0', 'Number of channels.')}

{col('ChannelID', 'int64', 'ChannelID', ['isKey'])}
{col('Channel', 'string', 'Channel')}
{col('Category', 'string', 'Category')}

{m_part('Channels', 'Channels.csv', ch_cols, ch_mt)}
""")

ca_cols = ["CampaignID", "CampaignName", "Channel", "Budget"]
ca_mt = ["Int64.Type", "type text", "type text", "type number"]
w_text(os.path.join(ROOT, SEM, "definition", "tables", "Campaigns.tmdl"),
f"""table Campaigns

{meas('Campaign Count', 'DISTINCTCOUNT(Campaigns[CampaignID])', '#,##0', 'Number of campaigns.')}

{col('CampaignID', 'int64', 'CampaignID', ['isKey'])}
{col('CampaignName', 'string', 'CampaignName')}
{col('Channel', 'string', 'Channel')}
{col('Budget', 'decimal', 'Budget')}

{m_part('Campaigns', 'Campaigns.csv', ca_cols, ca_mt)}
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
w_text(os.path.join(ROOT, REP, "StaticResources/SharedResources/BaseThemes/CY26SU02.json"),
       json.dumps({"name": "CY26SU02",
        "dataColors": ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7", "#744EC2", "#D9B300", "#D9B300"],
        "background": "#FFFFFF", "foreground": "#252423", "tableAccent": "#118DFF"}, indent=2) + "\n")

VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"
import secrets
hex20 = lambda: secrets.token_hex(10)
DS = "DailySpend"

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

page1, page2, page3 = "d0e1f2a3b4c5566778899", "e1f2a3b4c5d6677889900", "f2a3b4c5d6e7788990011"
p1 = [
    card("Total Spend", DS, 20, 20, 295, 140, 1000),
    card("Total Revenue", DS, 325, 20, 295, 140, 2000),
    card("ROAS", DS, 630, 20, 295, 140, 3000),
    card("Total Conversions", DS, 935, 20, 295, 140, 4000),
    visual(hex20(), "clusteredBarChart", 20, 180, 620, 300, 5000,
           {"Category": {"projections": [cref("Campaigns", "CampaignName")]},
            "Y": {"projections": [mref(DS, "ROAS")]}},
           sort={"sort": [{"field": mref(DS, "ROAS")["field"], "direction": "Descending"}]}),
    visual(hex20(), "donutChart", 650, 180, 600, 300, 6000,
           {"Category": {"projections": [cref("Channels", "Channel")]},
            "Y": {"projections": [mref(DS, "Total Revenue")]}}),
    visual(hex20(), "clusteredColumnChart", 20, 500, 610, 200, 7000,
           {"Category": {"projections": [cref("Dates", "MonthName")]},
            "Y": {"projections": [mref(DS, "Total Conversions")]}}),
    visual(hex20(), "tableEx", 640, 500, 620, 200, 8000,
           {"Values": {"projections": [cref("Channels", "Channel"), mref(DS, "Total Spend"),
               mref(DS, "Total Revenue"), mref(DS, "ROAS")]}}),
]
p2 = [
    visual(hex20(), "slicer", 20, 20, 300, 140, 1000,
           {"Values": {"projections": [cref("Channels", "Category")]}}, drill=False),
    visual(hex20(), "slicer", 330, 20, 300, 140, 2000,
           {"Values": {"projections": [cref("Campaigns", "CampaignName")]}}, drill=False),
    card("CTR", DS, 640, 20, 295, 140, 3000),
    card("Campaign Count", "Campaigns", 945, 20, 285, 140, 4000),
    visual(hex20(), "scatterChart", 20, 180, 610, 300, 5000,
           {"Category": {"projections": [cref("Campaigns", "CampaignName")]},
            "X": {"projections": [mref(DS, "Total Spend")]},
            "Y": {"projections": [mref(DS, "Total Revenue")]},
            "Size": {"projections": [mref(DS, "Total Conversions")]}}),
    visual(hex20(), "funnel", 640, 180, 610, 300, 6000,
           {"Category": {"projections": [cref("Channels", "Channel")]},
            "Y": {"projections": [mref(DS, "Total Conversions")]}}),
    visual(hex20(), "lineStackedColumnComboChart", 20, 500, 1230, 200, 7000,
           {"Category": {"projections": [cref("Dates", "Month")]},
            "Y": {"projections": [mref(DS, "Total Spend")]},
            "Y2": {"projections": [mref(DS, "Total Revenue")]}}),
]
p3 = [
    visual(hex20(), "slicer", 20, 20, 300, 120, 1000,
           {"Values": {"projections": [cref("Dates", "Year")]}}, drill=False),
    card("Total Clicks", DS, 330, 20, 300, 120, 2000),
    card("Channel Count", "Channels", 640, 20, 300, 120, 3000),
    card("CTR", DS, 950, 20, 300, 120, 4000),
    visual(hex20(), "lineChart", 20, 160, 1230, 300, 5000,
           {"Category": {"projections": [cref("Dates", "Month")]},
            "Y": {"projections": [mref(DS, "Total Conversions")]},
            "Series": {"projections": [cref("Dates", "Year")]}}),
    visual(hex20(), "tableEx", 20, 480, 1230, 220, 6000,
           {"Values": {"projections": [cref("Dates", "Date"), cref("Channels", "Channel"),
               cref("Campaigns", "CampaignName"), mref(DS, "Total Spend"), mref(DS, "Total Revenue")]}}),
]
all_pages = [(page1, "Marketing Overview", p1), (page2, "ROI Deep-Dive", p2), (page3, "Trends & Details", p3)]

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
