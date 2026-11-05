"""Scan TotalEnergies-format assay xlsx files: whole-crude properties plus WAT / wax label check.
Usage: python3 -I scan_totalenergies_assays.py <folder_with_xlsx> <out.csv>"""
import openpyxl, glob, hashlib, re, csv, sys, os
folder,outp=sys.argv[1],sys.argv[2]
seen={}; uniq=[]
for f in sorted(glob.glob(os.path.join(folder,"*.xlsx"))):
    h=hashlib.md5(open(f,"rb").read()).hexdigest()
    if h in seen: continue
    seen[h]=f; uniq.append(f)
keys=["file","Name","Traded Crude","Origin","Sample Date","Density @ 15°C (g/cc)","API Gravity","Total Sulphur (% wt)","Pour Point (°C)","Viscosity @ 20°C (cSt)","Viscosity @ 40°C (cSt)","Total Acid Number (mgKOH/g)"]
txt={"file","Name","Traded Crude","Origin","Sample Date"}
rows=[]; wat_hits=[]; wax_whole=[]
for f in uniq:
    wb=openpyxl.load_workbook(f,data_only=True); ws=wb["Summary"]; d={"file":os.path.basename(f)[9:]}
    for row in ws.iter_rows(min_row=1,max_row=30,values_only=True):
        if row[1] in ("Name:","Traded Crude:","Origin:","Sample Date:"): d[str(row[1]).strip(":")]=row[2]
        lab=row[12] if len(row)>12 else None
        if isinstance(lab,str) and row[16] is not None: d[lab.strip()]=row[16]
        if isinstance(lab,str) and re.search("wax",lab,re.I): wax_whole.append((d["file"],lab,row[16]))
    for w in wb.worksheets:
        for r in w.iter_rows():
            for c in r:
                if isinstance(c.value,str) and re.search(r"\bWAT\b|wax appear|appearance temp",c.value,re.I): wat_hits.append((d["file"],w.title,c.coordinate,c.value[:60]))
    rows.append(d)
def fmt(k,v):
    if v is None: return ""
    if k in txt: return v
    try: return round(float(v),4)
    except: return ""
with open(outp,"w",newline="") as fh:
    w=csv.writer(fh); w.writerow(keys)
    for d in rows: w.writerow([fmt(k,d.get(k)) for k in keys])
print(len(uniq),"unique assays; WAT-like labels:",len(wat_hits),wat_hits[:5],"; whole-crude wax fields:",len(wax_whole))
