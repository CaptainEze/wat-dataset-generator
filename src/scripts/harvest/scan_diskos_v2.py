"""
Scan the FORCE / DISKOS text dataset for crude oil wax data (version 2).

Run:  python scan_diskos_v2.py "Norway - Diskos reports.csv"
Send back: diskos_wax_pages.csv  and  the column list printed at the start.

Needs pandas:  pip install pandas
"""
import sys
import pandas as pd

src = sys.argv[1]
out = "diskos_wax_pages.csv"

# 1. Show the columns first, so we know what the file contains.
head = pd.read_csv(src, nrows=5, dtype=str, on_bad_lines="skip", engine="python")
print("COLUMNS:", list(head.columns))
print(head.iloc[0].to_dict() if len(head) else "no rows")

cols = list(head.columns)
text_col = next((c for c in cols if c.lower() in ("content", "text", "page_text")), cols[-1])
# Find the column that says whether a page is real text or gibberish.
class_col = next((c for c in cols if any(k in c.lower() for k in
                  ("class", "label", "gibberish", "quality", "is_text", "real"))), None)
print("text column:", text_col, "| classification column:", class_col)

wax = (r"wax appearance|wax precipitation|wax dissolution|"
       r"\bWAT\b|\bWDT\b|cloud point|pour point")
second = r"pour point|wax content|density|viscosity|specific gravity|API"

first = True
kept = 0
for chunk in pd.read_csv(src, chunksize=50_000, dtype=str,
                         on_bad_lines="skip", engine="python"):
    txt = chunk[text_col].fillna("")
    mask = txt.str.contains(wax, case=False, regex=True) & \
           txt.str.contains(second, case=False, regex=True)
    hit = chunk[mask]
    if class_col is not None and len(hit):
        # Drop pages the file marks as gibberish. Keeps anything not clearly bad.
        bad = hit[class_col].fillna("").str.lower().str.contains("gibberish|bad|false|0|noise")
        hit = hit[~bad]
    if len(hit):
        hit.to_csv(out, mode="w" if first else "a", header=first, index=False)
        first = False
        kept += len(hit)
    print(f"pages kept so far: {kept}", end="\r")

print(f"\nDone. {kept} pages written to {out}")
