import pandas as pd, re, numpy as np
a=pd.read_csv("all_new_raw.csv",dtype=str); m=pd.read_csv("master_snapshot.csv",dtype=str)
num=["density_kg_m3","api","wax_wt_pct","pour_c","visc_cSt_40C","wat_c","wdt_c"]
for d in (a,m):
    for c in num: d[c]=pd.to_numeric(d[c],errors="coerce")
dec=[]  # decision log
def note(t): dec.append(t)

# ---- 1. drop duplicates across agents
drop={"REPO-018":"duplicate of MENA-070","REPO-019":"duplicate of MENA-071","REPO-020":"duplicate of MENA-072","REPO-021":"duplicate of MENA-073",
"APAC-010":"same values as METH-001 (Miri)","APAC-011":"same values as METH-002 (Angsi)","APAC-012":"same values as METH-003 (Penara)","APAC-013":"same values as METH-004 (Dulang)",
"BAL-008":"duplicate of AMER-017 (South Pelto FTIR, high pressure)","BAL-009":"duplicate of NSEA-004 (2/7-19R)","BAL-007":"duplicate of REPO-003 (Dagang heavy oil, same WAT and wax)"}
for k,v in drop.items(): note(f"DROP {k}: {v}")
# unify Uzen group names
a.loc[a.row_id.str.startswith("REPO-01"),"oil_group"]=a.oil_group
# ---- 2. upgrades of master tier C rows to primary source
up={"REPO-008":"R40","REPO-009":"R33","REPO-010":"R34","REPO-011":"R35"}
for hid,rid in up.items():
    s=a[a.row_id==hid].iloc[0]; i=m.index[m.row_id==rid][0]
    old=(m.at[i,"wax_wt_pct"],m.at[i,"api"],m.at[i,"wat_method"],m.at[i,"tier"])
    m.at[i,"wat_method"]=s.wat_method; m.at[i,"tier"]=s.tier; m.at[i,"source"]=s.source; m.at[i,"source_url"]=s.source_url
    if pd.notna(s.api): m.at[i,"api"]=s.api
    if hid!="REPO-008": m.at[i,"wax_wt_pct"]=np.nan
    m.at[i,"notes"]=f"UPGRADED from review-table tier C to primary source ({hid}). Previous values: wax {old[0]}, method {old[2]}, tier {old[3]}. "+str(s.notes)
    note(f"UPGRADE master {rid} from {hid}: tier {old[3]} -> {s.tier}; wax {old[0]} -> {m.at[i,'wax_wt_pct']}")
drop.update({k:"merged into master "+v for k,v in up.items()})
a=a[~a.row_id.isin(drop)].copy()

# ---- 3. specific edits
i=a.index[a.row_id=="NSEA-001"][0]
a.at[i,"wat_c"]=41.5; a.at[i,"density_kg_m3"]=838.0
a.at[i,"notes"]="Source prints WAT as a range 40-43 C; midpoint 41.5 entered by project rule (range kept here). "+re.sub(r"^Source prints WAT as a range 40-43 C; the lower bound is entered, not a midpoint\.\s*","",a.at[i,"notes"])
note("EDIT NSEA-001: WAT range 40-43 entered as midpoint 41.5")
kh=a.oil_group.str.contains("khalda|crude_?[a-d]$",case=False,na=False)|a.oil_name.str.contains("Khalda",na=False)
a.loc[kh,"tier"]="P"
a.loc[kh,"notes"]="HELD (tier P): another agent read this table twice and got inconsistent values; wax 37-41 wt% looks too high; Crude-B and Crude-C have identical WAT, wax and pour. Check against the PDF. "+a.loc[kh,"notes"].fillna("")
note(f"HOLD {kh.sum()} Khalda rows as tier P")
# 20 C densities recorded only in notes
fix={"REPO-001":855.4,"REPO-002":835.6,"REPO-003":940.86,"REPO-004":862.46,"REPO-005":868.32,"REPO-006":875.31,"REPO-007":879.3,"BAL-006":818.0}
for k,v in fix.items():
    n=a.loc[a.row_id==k,"notes"].iloc[0]
    assert str(v).rstrip("0").rstrip(".") in n.replace(",",""), (k,v)
    a.loc[a.row_id==k,"density_kg_m3"]=v
note("DENSITY from notes (20 C): "+", ".join(f"{k}={v}" for k,v in fix.items()))

# ---- 4. density temperature column
def dT(n):
    n=str(n)
    if re.search(r"\b20\s?(°|deg)?\s?C",n) and re.search(r"[Dd]ensity",n): return 20
    if re.search(r"\b15(\.6)?\s?(°|deg)?\s?C|60\s?F",n) and re.search(r"[Dd]ensity",n) and not re.search(r"not confirmed|temperature not stated",n): return 15
    return np.nan
a["density_T_c"]=a.notes.map(dT)
a.loc[a.density_kg_m3.isna(),"density_T_c"]=np.nan
a.loc[a.row_id=="NSEA-001","density_T_c"]=15
m["density_T_c"]=np.where(m.density_kg_m3.notna(),15,np.nan)

# ---- 5. ids, flags, columns
start=int(m.row_id.str[1:].astype(int).max())+1
a=a.reset_index(drop=True)
a["harvest_id"]=a.row_id
a["row_id"]=[f"R{start+j}" for j in range(len(a))]
m["harvest_id"]=""
for hid,rid in up.items(): m.loc[m.row_id==rid,"harvest_id"]=hid
d=pd.concat([m,a.drop(columns=["agent"])],ignore_index=True)
for c in num: d[c]=pd.to_numeric(d[c],errors="coerce")
def flags(r):
    f=[]
    if pd.notna(r.wat_c) and pd.notna(r.pour_c):
        g=r.wat_c-r.pour_c
        if g>40: f.append(f"plausibility:WAT-pour={g:.1f}")
        if g<0: f.append(f"plausibility:WAT-pour={g:.1f}")
    if pd.notna(r.density_kg_m3) and pd.isna(r.density_T_c): f.append("density_T_unknown")
    if pd.notna(r.density_T_c) and r.density_T_c!=15: f.append(f"density_at_{int(r.density_T_c)}C")
    if pd.isna(r.density_kg_m3) and pd.isna(r.api): f.append("no_density_or_api")
    if str(r.wat_method).startswith("other (rotational pour point tester"): f.append("method:torque_slope")
    if "censored" in str(r.notes).lower(): f.append("censored")
    if str(r.notes).startswith("HELD"): f.append("held_source_conflict")
    if "WAF-001" in str(r.harvest_id) : f.append("source_internally_inconsistent")
    return ";".join(f)
d["qc_flags"]=d.apply(flags,axis=1)
cols=["row_id","harvest_id","oil_group","oil_name","country_basin","density_kg_m3","density_T_c","api","wax_wt_pct","wax_method","pour_c","pour_method","visc_cSt_40C","wat_c","wat_method","wdt_c","tier","qc_flags","source","source_url","notes"]
d=d[cols]
d.to_csv("merged/wat_master_v2.csv",index=False)
# logs
L=[]
for ag in ["waf","nsea","mena","apac","amer","repos","methods","balance"]:
    l=pd.read_csv(f"{ag}/log.csv",dtype=str); l["agent"]=ag; L.append(l)
L=pd.concat(L,ignore_index=True); L.to_csv("merged/harvest_source_log_all.csv",index=False)
open("merged/merge_decisions.txt","w").write("\n".join(dec))
print(len(d),"rows;",d.oil_group.nunique(),"oil groups;",len(a),"new rows")
print(dec)
