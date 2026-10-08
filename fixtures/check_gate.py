"""Runs the full gate: real projects must pass, every fixture must fail."""
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

fails = []
for proj in ("SalesAnalytics", "InventoryAnalytics"):
    r = subprocess.run([sys.executable, "validate.py", proj], cwd=ROOT, capture_output=True, text=True)
    print(f"[{proj}] exit={r.returncode}")
    if r.returncode != 0:
        fails.append(proj)

base = os.path.join(ROOT, "fixtures")
for d in sorted(glob.glob(os.path.join(base, "broken-*"))):
    proj = glob.glob(os.path.join(d, "*.pbip"))[0]
    proj = os.path.splitext(os.path.basename(proj))[0]
    r = subprocess.run([sys.executable, os.path.join(ROOT, "validate.py"), proj],
                       cwd=d, capture_output=True, text=True)
    tag = "OK-fails" if r.returncode != 0 else "UNEXPECTED-PASS"
    print(f"[{os.path.basename(d)}] exit={r.returncode} {tag}")
    if r.returncode == 0:
        fails.append(os.path.basename(d))

print("GATE:", "GREEN" if not fails else f"RED: {fails}")
sys.exit(0 if not fails else 1)
