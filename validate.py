"""Shared PBIP validator. Usage: python validate.py <ProjectName>
Checks the full skill contract (pbi-skills.md + pbir-visuals.md) for any
generated project. Exit 0 = all green, 1 = failures.
"""
import glob
import json
import os
import re
import sys

VALID_SETTINGS = {'useStylableVisualContainerHeader', 'exportDataMode',
                  'defaultDrillFilterOtherVisuals', 'allowChangeFilterTypes',
                  'useEnhancedTooltips', 'useDefaultAggregateDisplayName'}

def main(project):
    sem, rep = f"{project}.SemanticModel", f"{project}.Report"
    fails = []

    def check(cond, msg):
        print(('PASS ' if cond else 'FAIL ') + msg)
        if not cond:
            fails.append(msg)

    if not os.path.isfile(f"{project}.pbip"):
        print(f"FAIL no {project}.pbip"); return 1

    def find_data_dirs():
        out, d = [], os.path.abspath(os.getcwd())
        while True:
            out += [os.path.join(d, x) for x in glob.glob(os.path.join(d, "data*"))
                    if os.path.isdir(os.path.join(d, x))]
            nd = os.path.dirname(d)
            if nd == d:
                break
            d = nd
        return out

    data_dirs = find_data_dirs()
    csvs = [os.path.basename(f) for d in data_dirs for f in glob.glob(f"{d}/*.csv")]

    files = glob.glob(f"{sem}/**/*", recursive=True) + \
        glob.glob(f"{rep}/**/*", recursive=True) + [f"{project}.pbip"]
    bom = [f for f in files if os.path.isfile(f) and open(f, 'rb').read(3) == b'\xef\xbb\xbf']
    check(not bom, f"UTF-8 no-BOM ({len(files)} files)")

    jfiles = glob.glob(f"{rep}/**/*.json", recursive=True) + \
        [f"{project}.pbip", f"{sem}/definition.pbism", f"{rep}/definition.pbir"]
    ok = True
    for f in jfiles:
        try:
            json.load(open(f, encoding='utf-8'))
        except Exception as e:  # noqa: BLE001
            ok = False; fails.append(f"JSON parse: {f}: {e}")
    check(ok, f"all {len(jfiles)} JSON parse")

    tmdls = glob.glob(f"{sem}/definition/**/*.tmdl", recursive=True)
    check(tmdls, "TMDL files exist")
    check(all(not [ln for ln in open(f, encoding='utf-8').read().splitlines()
                  if ln.startswith(' ') and ln.strip()] for f in tmdls), "TMDL tabs-only")
    txt = "".join(open(f, encoding='utf-8').read() for f in tmdls)
    check("VARCHAR" not in txt and "DATETIME2" not in txt and "singleDirection" not in txt,
          "TOM types + oneDirection (no singleDirection)")
    check("crossFilteringBehavior: oneDirection" in txt, "relationships oneDirection present")
    rel = open(f"{sem}/definition/relationships.tmdl", encoding='utf-8').read()
    check("///" not in rel, "no /// on relationships")

    tables = glob.glob(f"{sem}/definition/tables/*.tmdl")
    m_ok = True
    for f in tables:
        paths = re.findall(r"File\.Contents\(\"([^\"]+)\"", open(f, encoding='utf-8').read())
        if len(paths) != 1 or "\\" in paths[0] or not paths[0].endswith(".csv"):
            m_ok = False; fails.append(f"M path: {f} -> {paths}")
        csv = paths[0].split("/")[-1] if paths else ""
        if csv not in csvs:
            m_ok = False; fails.append(f"M path CSV not in repo data: {csv}")
    check(m_ok, "M paths forward-slash + CSVs exist")

    ms = [m for f in tables for m in re.findall(r"measure '([^']+)'", open(f, encoding='utf-8').read())]
    check(len(ms) == len(set(ms)) and ms, f"measures unique ({len(ms)})")
    coll = []
    for f in tables:
        txt = open(f, encoding='utf-8').read()
        cols = {c.strip("'").lower() for c in re.findall(r"^\tcolumn (.+)$", txt, re.M)}
        for m in re.findall(r"^\tmeasure '([^']+)'", txt, re.M):
            if m.lower() in cols:
                coll.append(f"{os.path.basename(f)}: measure '{m}' collides with column")
    check(not coll, "no measure/column name collisions")
    for c in coll[:5]:
        print("  -", c)
    check(json.load(open(f"{sem}/definition.pbism", encoding='utf-8')).get("version") == "4.0", "pbism 4.0")
    check(json.load(open(f"{rep}/definition.pbir", encoding='utf-8'))["datasetReference"]
          == {"byPath": {"path": f"../{sem}"}}, "pbir byPath")

    settings = json.load(open(f"{rep}/definition/report.json", encoding='utf-8'))["settings"]
    check(set(settings) <= VALID_SETTINGS, "report settings keys")
    check(settings.get("exportDataMode") == "AllowSummarized", "exportDataMode const")

    n, bad = 0, []
    for f in glob.glob(f"{rep}/definition/pages/*/visuals/*/visual.json"):
        v = json.load(open(f, encoding='utf-8'))
        qs = v["visual"].get("query", {}).get("queryState", {})
        if "Filters" in qs:
            bad.append(f"{f}: Filters role")
        for role, packs in qs.items():
            for p in packs.get("projections", []):
                n += 1
                if "nativeQueryRef" not in p:
                    bad.append(f"{f}: no nativeQueryRef")
        if v["visual"].get("visualType") == "lineStackedColumnComboChart" and "Y2" not in qs:
            bad.append(f"{f}: combo no Y2")
        if "titleText" in json.dumps(v):
            bad.append(f"{f}: titleText present")
    check(not bad, f"visuals conform ({n} projections)")
    for b in bad[:5]:
        print("  -", b)

    pages = json.load(open(f"{rep}/definition/pages/pages.json", encoding='utf-8'))
    pg_ok = set(pages["pageOrder"]) == {d for d in os.listdir(f"{rep}/definition/pages") if d != "pages.json"}
    disp_ok = True
    for pid in pages["pageOrder"]:
        pg = json.load(open(f"{rep}/definition/pages/{pid}/page.json", encoding='utf-8'))
        if pg.get("displayOption") != "FitToPage":
            disp_ok = False; fails.append(f"page {pid} displayOption")
    check(pg_ok and disp_ok, "pages FitToPage + order matches folders")

    print("RESULT:", "ALL GREEN" if not fails else f"{len(fails)} FAILURES")
    return 0 if not fails else 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate.py <ProjectName>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
