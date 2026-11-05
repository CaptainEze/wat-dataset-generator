import pandas as pd, numpy as np, glob
d=pd.read_csv("merged/wat_master_v2.csv")
d["verified"]="not_checked"
idx=d.set_index("row_id").index
def ix(r): return d.index[d.row_id==r][0]
# 1. densities found by checkers, with their temperature
fills={"R132":(886,80,"V3"),"R135":(827,40,"V3"),"R136":(790,40,"V3"),"R66":(921.8,40,"V4"),"R67":(891.6,40,"V4"),
       "R40":(890,np.nan,"V4"),"R68":(810,np.nan,"V4"),"R171":(868.8,15.56,"V5")}
for r,(v,t,vv) in fills.items():
    i=ix(r); d.at[i,"density_kg_m3"]=v; d.at[i,"density_T_c"]=t
    d.at[i,"notes"]=f"Density {v} kg/m3 added at verification ({vv}, single reading). "+str(d.at[i,"notes"])
# 2. tier changes
i=ix("R155"); d.at[i,"tier"]="P"; d.at[i,"notes"]="HELD at verification: the paper's 'waxing point' is not stated to be WAT and no method is given. "+str(d.at[i,"notes"])
i=ix("R171"); d.at[i,"tier"]="B-"; d.at[i,"notes"]="Downgraded from A- at verification: the 'Wax appearance 23.84' line has no stated unit or method in one of two readings. "+str(d.at[i,"notes"])
# 3. wax proxy rows (Oliveira 2018 = AP01-AP09 = harvest AMER-001..009)
ol=d.harvest_id.fillna("").isin([f"AMER-00{k}" for k in range(1,10)])
d.loc[ol,"wax_method"]="GC n-alkane sum C15-C44 (proxy for wax content)"
# 4. flags
def addf(r,f):
    i=ix(r); cur=d.at[i,"qc_flags"]; d.at[i,"qc_flags"]=(f if pd.isna(cur) or cur=="" else f"{cur};{f}")
for r in d.row_id[ol]: addf(r,"wax_proxy_GC_nalkanes")
addf("R154","pour_after_heat_treatment_80C"); addf("R154","density_printed_g/cm3_but_kg/m3")
addf("R155","held_wat_method_unconfirmed"); addf("R171","wat_unit_unlabelled")
addf("R158","pour_censored_below_-24")
for r in ["R132","R135","R136"]: addf(r,"WAT_cooling_rate_1K/min_chosen")
addf("R132","pour_51C_high")
# 5. verification status from comparison
cmp=pd.read_csv("verify/comparison.csv")
interp={"R157","R158","R160","R162","R163","R135","R136","R69","R154","R155","R171"}
fixed=set(fills)
checked=set(cmp.row_id)
for r in checked:
    i=ix(r)
    d.at[i,"verified"]="double_entry_interpretation" if r in interp else ("double_entry_filled" if r in fixed else "double_entry_agree")
# rows from V1 still running
v1=pd.read_csv("verify/V1_task.csv").row_id
for r in v1:
    if r not in checked: d.at[ix(r),"verified"]="check_pending"
d.to_csv("merged/wat_master_v3.csv",index=False)
print(d.verified.value_counts().to_dict())
print("rows",len(d),"| core3 now:",)
use=d[~d.tier.isin(["P","X","D"])&d.wat_c.notna()]
c3=use[(use.density_kg_m3.notna()|use.api.notna())&use.pour_c.notna()&use.wax_wt_pct.notna()]
print(len(c3),c3.oil_group.nunique(),"| core4",len(c3[c3.visc_cSt_40C.notna()]))
