#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from logbook_export import export

LOGBOOK_DIR = Path("/var/lib/avnav/logbuch")
OUTPUT_DIR = ROOT.parent / "export-test"

START = datetime(2026, 1, 1).date()
END = datetime(2035, 12, 31).date()

files = export(
    logbook_dir=LOGBOOK_DIR,
    output_dir=OUTPUT_DIR,
    start_date=START,
    end_date=END,
    formats=("markdown", "html"),
    title="Digitales Logbuch (Test)",
)

print()
print("Erzeugte Dateien:")
for f in files:
    print(" -", f)

print()
print("Fertig.")
