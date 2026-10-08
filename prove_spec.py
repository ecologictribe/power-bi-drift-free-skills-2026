"""Proves spec-built output semantically equals the blessed project tree.
Ignores random IDs (.platform logicalIds, page/visual folder names, name fields).
Usage: python prove_spec.py <BlessedRoot> <ProofRoot> <Project>
Exit 0 = equivalent.
"""
import glob
import json
import os
import re
import sys

VC_POS = ("x", "y", "width", "height")
fails = []


def check(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    if not cond:
        fails.append(msg)


def norm(txt):
    return "\n".join(ln for ln in txt.splitlines() if ln.strip())


def tables(root, sem):
    out = {}
    for f in glob.glob(os.path.join(root, sem, "definition", "tables", "*.tmdl")):
        t = os.path.splitext(os.path.basename(f))[0]
        txt = norm(open(f, encoding='utf-8').read())
        out[t] = {
            "measures": sorted(re.findall(r"measure '([^']+)' = ```\s+(.+?)\s+```\s+formatString: (.+)", txt, re.S)),
            "columns": sorted(re.findall(r"^\tcolumn (.+)\n\t\tdataType: (\S+)\n\t\tsourceColumn: (.+)", txt, re.M)),
            "hier": re.findall(r"hierarchy '([^']+)'|level (\S+)\s+column: (\S+)", txt),
            "mpath": re.findall(r'File\.Contents\("([^"]+)"', txt),
            "mpairs": re.findall(r'\{"([^"]+)", ([^}]+)\}', txt)}
    return out


def rels(root, sem):
    txt = norm(open(os.path.join(root, sem, "definition", "relationships.tmdl"), encoding='utf-8').read())
    return sorted(re.findall(
        r"fromColumn: (\S+)\n\ttoColumn: (\S+)\n\tcrossFilteringBehavior: (\S+)\n"
        r"\tfromCardinality: (\S+)\n\ttoCardinality: (\S+)\n\tisActive: (\S+)", txt))


def visuals(root, rep):
    out = {}
    pages = json.load(open(os.path.join(root, rep, "definition", "pages", "pages.json"), encoding='utf-8'))
    for pid in pages["pageOrder"]:
        pg = json.load(open(os.path.join(root, rep, "definition", "pages", pid, "page.json"), encoding='utf-8'))
        vs = []
        for vf in glob.glob(os.path.join(root, rep, "definition", "pages", pid, "visuals", "*", "visual.json")):
            v = json.load(open(vf, encoding='utf-8'))
            qs = {}
            for role, packs in v["visual"].get("query", {}).get("queryState", {}).items():
                items = []
                for p in packs.get("projections", []):
                    fld = p["field"]
                    if "Column" in fld:
                        items.append(("C", fld["Column"]["Expression"]["SourceRef"]["Entity"],
                                      fld["Column"]["Property"]))
                    else:
                        items.append(("M", fld["Measure"]["Expression"]["SourceRef"]["Entity"],
                                      fld["Measure"]["Property"]))
                qs[role] = sorted(items)
            sd = v["visual"].get("query", {}).get("sortDefinition", {}).get("sort", [])
            srt = sorted(
                (list(s["field"])[0],
                 s["field"][list(s["field"])[0]]["Expression"]["SourceRef"].get("Entity"),
                 s["field"][list(s["field"])[0]]["Property"], s["direction"]) for s in sd)
            vs.append((v["visual"]["visualType"],
                       tuple(v["position"][k] for k in VC_POS),
                       sorted(qs.items()), srt,
                       v["visual"].get("drillFilterOtherVisuals")))
        out[pg["displayName"]] = sorted(vs, key=repr)
    order = [json.load(open(os.path.join(root, rep, "definition", "pages", p, "page.json"),
                            encoding='utf-8'))["displayName"] for p in pages["pageOrder"]]
    return order, out


def main(blessed, proof, project):
    sem, rep = f"{project}.SemanticModel", f"{project}.Report"
    bt, pt = tables(blessed, sem), tables(proof, sem)
    check(set(bt) == set(pt), f"same tables {sorted(bt)}")
    for t in bt:
        check(bt[t] == pt.get(t), f"table {t} identical")
    check(rels(blessed, sem) == rels(proof, sem), "relationships identical")

    border, bv = visuals(blessed, rep)
    porder, pv = visuals(proof, rep)
    check(border == porder, f"same page order {border}")
    if bv != pv:
        for pg in border:
            for a, c in zip(bv.get(pg, []), pv.get(pg, [])):
                if a != c:
                    print("DIFF PAGE:", pg)
                    print("  BLESSED:", json.dumps(a))
                    print("  PROOF:  ", json.dumps(c))
    check(bv == pv, "all visuals identical (type/position/query/sort/drill)")

    b = json.load(open(os.path.join(blessed, rep, "definition", "report.json"), encoding='utf-8'))
    p = json.load(open(os.path.join(proof, rep, "definition", "report.json"), encoding='utf-8'))
    b.pop("$schema", None)
    p.pop("$schema", None)
    check(b == p, "definition/report.json identical")

    print("EQUIVALENCE:", "PROVEN" if not fails else f"FAILED: {fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
