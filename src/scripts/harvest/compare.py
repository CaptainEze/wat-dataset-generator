import pandas as pd, sys, glob, numpy as np
pd.set_option("display.width",250); pd.set_option("display.max_colwidth",80); pd.set_option("display.max_rows",300)
d=pd.read_csv("merged/wat_master_v2.csv").set_index("row_id")
f=["density_kg_m3","api","wax_wt_pct","pour_c","visc_cSt_40C","wat_c","wdt_c"]
tol={"density_kg_m3":1.5,"api":0.15,"wax_wt_pct":0.06,"pour_c":0.6,"visc_cSt_40C":0.06,"wat_c":0.25,"wdt_c":0.25}
rows=[]
for p in sorted(glob.glob("verify/V*_result.csv")):
    r=pd.read_csv(p)
    for _,x in r.iterrows():
        if x.status!="read": rows.append((x.row_id,"STATUS",x.status,"",p[-12:-11+0] if False else "")); continue
        m=d.loc[x.row_id]
        for c in f:
            a,b=m[c],pd.to_numeric(x[c],errors="coerce")
            if pd.isna(a) and pd.isna(b): continue
            if pd.isna(a)!=pd.isna(b): rows.append((x.row_id,c,a,b,"blank mismatch")); continue
            ok=abs(a-b)<=max(tol[c],abs(a)*0.002)
            rows.append((x.row_id,c,a,b,"ok" if ok else "MISMATCH"))
o=pd.DataFrame(rows,columns=["row_id","field","merged","checker","result"])
print(o.result.value_counts().to_dict())
print(o[~o.result.isin(["ok"])].to_string(index=False))
n=len(o[o.result.isin(["ok","MISMATCH","blank mismatch"])]); print("fields compared",n)
o.to_csv("verify/comparison.csv",index=False)
