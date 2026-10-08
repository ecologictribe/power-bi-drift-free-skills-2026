"""Spec-driven PBIP generator. Usage: python build_from_spec.py spec/<domain>.json [outDir]
Implements pbi-skills.md + pbir-visuals.md generically: any LLM (or human) writes
a spec file, this emits a drift-free project. Proof output goes to a scratch dir
(default .quarantine/spec_proof/<Project>/) — never over the blessed projects.
"""
import json
import os
import shutil
import sys
import uuid

T = "\t"
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json"
GOOD_SETTINGS = {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                 "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                 "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}

def w_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")

def w_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def qname(name):
    return name if all(c.isalnum() or c == '_' for c in name) else f"'{name}'"

def proj_ref(e, p, kind):
    if kind == "column":
        return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
                "queryRef": f"{e}.{p}", "nativeQueryRef": p, "active": True}
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
            "queryRef": f"{e}.{p}", "nativeQueryRef": p}

def build(spec_path, out_root):
    spec = json.load(open(spec_path, encoding='utf-8'))
    project, data = spec["project"], spec["dataDir"]
    sem, rep = f"{project}.SemanticModel", f"{project}.Report"
    R = lambda *p: os.path.join(out_root, *p)

    w_json(R(f"{project}.pbip"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": rep}}],
        "settings": {"enableAutoRecovery": True}})
    w_json(R(sem, "definition.pbism"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0", "settings": {}})
    for itype in ("SemanticModel", "Report"):
        w_json(R(sem if itype == "SemanticModel" else rep, ".platform"), {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": itype, "displayName": project},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}})

    w_text(R(sem, "definition", "database.tmdl"),
           f"database {project}\n{T}compatibilityLevel: 1702\n{T}compatibilityMode: powerBI\n")
    w_text(R(sem, "definition", "model.tmdl"),
           f"model Model\n{T}culture: en-US\n{T}defaultPowerBIDataSourceVersion: powerBI_V3\n"
           f"{T}sourceQueryCulture: en-US\n{T}discourageImplicitMeasures: true\n\n" +
           "".join(f"ref table {t['name']}\n" for t in spec["tables"]))

    rels = []
    for r in spec["relationships"]:
        rels.append(
            f"relationship {r['id']}\n{T}fromColumn: {r['from']}\n{T}toColumn: {r['to']}\n"
            f"{T}crossFilteringBehavior: oneDirection\n{T}fromCardinality: many\n"
            f"{T}toCardinality: one\n{T}isActive: {'true' if r.get('active', True) else 'false'}")
    w_text(R(sem, "definition", "relationships.tmdl"), "\n\n".join(rels) + "\n")

    for t in spec["tables"]:
        parts = [f"table {t['name']}", ""]
        for m in t.get("measures", []):
            parts += [f"{T}/// {m['desc']}",
                      f"{T}measure '{m['name']}' = ```", f"{T}{T}{m['expr']}",
                      f"{T}\t```", f"{T}{T}formatString: {m['format']}", ""]
        for c in t["columns"]:
            parts += [f"{T}column {qname(c['name'])}", f"{T}{T}dataType: {c['type']}",
                      f"{T}{T}sourceColumn: {c['source']}", f"{T}{T}summarizeBy: none"]
            if c.get("key"):
                parts.append(f"{T}{T}isKey")
        for h in t.get("hierarchies", []):
            parts += ["", f"{T}hierarchy '{h['name']}'"]
            for lv in h["levels"]:
                parts += [f"{T}{T}level {lv['level']}", f"{T}{T}{T}column: {lv['column']}"]
        pc, mt = t["partition"]["columns"], t["partition"]["mtypes"]
        pairs = ", ".join(f'{{"{c}", {m}}}' for c, m in zip(pc, mt))
        parts += ["", f"{T}partition {t['name']} = m", f"{T}{T}mode: import",
                  f"{T}{T}source =", f"{T}{T}{T}let",
                  f"{T}{T}{T}{T}Source = Csv.Document(File.Contents(\"{data}/{t['file']}\"), "
                  f"[Delimiter=\",\", Columns={len(pc)}, Encoding=65001, QuoteStyle=QuoteStyle.None]),",
                  f"{T}{T}{T}{T}#\"Promoted Headers\" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                  f"{T}{T}{T}{T}#\"Changed Type\" = Table.TransformColumnTypes(#\"Promoted Headers\", {{{pairs}}})",
                  f"{T}{T}{T}in", f"{T}{T}{T}{T}#\"Changed Type\"",
                  f"{T}{T}annotation PBI_ResultType = Table", ""]
        w_text(R(sem, "definition", "tables", f"{t['name']}.tmdl"), "\n".join(parts))

    w_json(R(rep, "definition.pbir"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{sem}"}}})
    w_json(R(rep, "definition", "version.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})
    w_json(R(rep, "definition", "report.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY26SU02",
            "reportVersionAtImport": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
            "type": "SharedResources"}},
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
            "items": [{"name": "CY26SU02", "path": "BaseThemes/CY26SU02.json", "type": "BaseTheme"}]}],
        "settings": GOOD_SETTINGS})
    w_text(R(rep, "StaticResources", "SharedResources", "BaseThemes", "CY26SU02.json"),
           json.dumps({"name": "CY26SU02",
            "dataColors": ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7", "#744EC2", "#D9B300", "#D9B300"],
            "background": "#FFFFFF", "foreground": "#252423", "tableAccent": "#118DFF"}, indent=2) + "\n")

    pages_dir = R(rep, "definition", "pages")
    if os.path.isdir(pages_dir):
        shutil.rmtree(pages_dir)
    order = []
    for pg in spec["report"]["pages"]:
        order.append(pg["id"])
        w_json(os.path.join(pages_dir, pg["id"], "page.json"), {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
            "name": pg["id"], "displayName": pg["name"], "displayOption": "FitToPage",
            "height": 720, "width": 1280})
        for vs in pg["visuals"]:
            qs = {}
            for role, projs in vs["query"].items():
                out = []
                for p in projs:
                    if "column" in p:
                        out.append(proj_ref(p["column"][0], p["column"][1], "column"))
                    else:
                        out.append(proj_ref(p["measure"][0], p["measure"][1], "measure"))
                qs[role] = {"projections": out}
            x, y, w, h, o = vs["pos"]
            v = {"$schema": VC, "name": vs["id"],
                 "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": o},
                 "visual": {"visualType": vs["type"], "query": {"queryState": qs}}}
            if "sort" in vs:
                s = vs["sort"]
                kind = "Column" if s["kind"] == "column" else "Measure"
                v["visual"]["query"]["sortDefinition"] = {"sort": [{
                    "field": {kind: {"Expression": {"SourceRef": {"Entity": s["entity"]}},
                                     "Property": s["prop"]}},
                    "direction": s["direction"]}]}
            if vs["type"] != "slicer":
                v["visual"]["drillFilterOtherVisuals"] = True
            v["visual"]["visualContainerObjects"] = {"title": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}}}}]}
            w_json(os.path.join(pages_dir, pg["id"], "visuals", vs["id"], "visual.json"), v)
    w_json(os.path.join(pages_dir, "pages.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": order, "activePageName": order[0]})
    n = sum(len(p["visuals"]) for p in spec["report"]["pages"])
    print(f"Built {project} from spec: {len(order)} pages, {n} visuals -> {out_root}")

if __name__ == "__main__":
    sp = sys.argv[1]
    proj = json.load(open(sp, encoding='utf-8'))["project"]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".quarantine", "spec_proof", proj)
    # SAFETY (ADR-008): the output root must be this repo root (blessed trees)
    # or a scratch dir beneath it — never .git, never outside the repo.
    # Only definition/pages/ is ever wiped; the output root itself is untouched.
    root = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.abspath(out)
    if dest == os.path.join(root, ".git") or not dest.startswith(root + os.sep) and dest != root:
        sys.exit(f"refusing to build into {out!r}")
    build(sp, out)
