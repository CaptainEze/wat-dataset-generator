"""Load the real data used for calibration and evaluation."""
import numpy as np, pandas as pd, os
from modules.measurement import map_method
from modules.paths import MASTER, NOAA_POOL, LOCAL_POOL

def usable_rows(path=MASTER):
    """Usable master rows (tier not P, X or D, WAT present) with one density basis: API at 15 C.
    Density-only rows are corrected to 15 C with 0.7 kg/m3 per K (assumption) before conversion."""
    d = pd.read_csv(path)
    u = d[~d.tier.isin(["P", "X", "D"]) & d.wat_c.notna()].copy()
    T = u.density_T_c.fillna(15)
    rho15 = u.density_kg_m3 + 0.7 * (T - 15)
    u["api15"] = u.api.where(u.api.notna(), 141.5 / (rho15 / 999.0) - 131.5)
    u["api_source"] = np.where(u.api.notna(), "reported", "from_density")
    u["gap"] = u.wat_c - u.pour_c
    u["screen_flag"] = (u.gap > 40) | (u.gap < 0)
    u["benamara"] = u.source.fillna("").str.contains("Benamara")
    u["tierC"] = u.tier.eq("C")
    return u.reset_index(drop=True)


def labelled(include_benamara=False, include_tierC=False, screened=False):
    u = usable_rows()
    u = u.dropna(subset=["api15", "pour_c", "wax_wt_pct", "wat_c"])
    if not include_benamara: u = u[~u.benamara]
    if not include_tierC: u = u[~u.tierC]
    if screened: u = u[~u.screen_flag]
    u = u.copy(); u["meas_method"] = u.wat_method.map(map_method)
    # unknown methods: DSC is the most common in the set; recorded as an assumption
    u["method_known"] = u.meas_method.notna()
    u["meas_method"] = u.meas_method.fillna("DSC")
    return u.reset_index(drop=True)

def unlabelled():
    from modules.inputs import load_pool
    p = load_pool(NOAA_POOL, LOCAL_POOL)
    p = p.dropna(subset=["api15", "pour_c", "wax_wt_pct"])
    p = p[~p.pour_censored & p.wax_wt_pct.between(0.2, 45) & p.api15.between(8, 75)]
    return p.reset_index(drop=True)
