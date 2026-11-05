"""Registry of every extracted equation (all agents' models.jsonl) plus a small set of
bulk-input WAT correlations that can be applied directly to generated or real inputs.
These serve as cross-checks of the physics generator and as an alternative 'correlation' mode."""
import json, glob, os, numpy as np
from modules.paths import KNOWLEDGE

def load_registry():
    rows = []
    for f in sorted(glob.glob(os.path.join(KNOWLEDGE, "*", "models.jsonl"))):
        for line in open(f):
            line = line.strip()
            if not line: continue
            d = json.loads(line); d["agent"] = os.path.basename(os.path.dirname(f)); rows.append(d)
    return rows

# Bulk-input WAT correlations (inputs: wax wt%, pour C, API). Source ids refer to models.jsonl.
BULK_WAT = {
    # VNIIneft law for saturation (WAT) vs paraffin %, Russian practice; secondary citation; reads ~10 C high on master_v9
    "vniineft_tsat_paraffin": lambda wax, pour, api: 11.398 + 34.084 * np.log10(np.clip(wax, 0.1, None)),
    # Trebin 1980, ln form; secondary citation
    "trebin1980_tsat_paraffin": lambda wax, pour, api: 19.4574 * np.log(np.clip(wax, 0.1, None)) - 0.8117,
    # own fit on master_v9 (effects agent): WAT = pour + 26.508 - 0.498 wax
    "own_wat_from_pour_wax": lambda wax, pour, api: pour + 26.508 - 0.498 * wax,
    # own fit on master_v9 (effects agent), log wax
    "own_wat_vs_wax_log": lambda wax, pour, api: 11.20 * np.log(np.clip(wax, 0.1, None)) + 7.05,
    # correlations agent refit on master_v9: 17.48 + 17.39 log10(wax)
    "own_refit_log10_wax": lambda wax, pour, api: 17.48 + 17.39 * np.log10(np.clip(wax, 0.1, None)),
}
OWN_FITS = {"own_wat_from_pour_wax", "own_wat_vs_wax_log", "own_refit_log10_wax"}  # fitted on our data: do not use in evaluation

def apply_bulk(df, ids=None, exclude_own=True):
    ids = ids or [k for k in BULK_WAT if not (exclude_own and k in OWN_FITS)]
    return {k: BULK_WAT[k](df.wax_wt_pct.values, df.pour_c.values, df.api15.values) for k in ids}
