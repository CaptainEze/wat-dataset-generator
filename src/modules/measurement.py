"""Measurement layer: turns a solid-wax curve S(T) (wt% solid vs temperature, from the physics
layer) into the value a given laboratory method would report.

Principle (Coutinho and Daridon 2005; Hammami, Ratulowski and Coutinho 2003; Coutinho 2006):
a method reports WAT when the precipitated solid reaches its detection threshold, lowered further
by supercooling that grows with cooling rate. Offsets between methods therefore depend on how fast
the oil precipitates near the onset, which matches the observation that methods agree within
+/-3 C for fast-precipitating oils (Kruka, cited in Hammami et al. 2003).

Every number below carries the fact id from study/agents/effects/facts.jsonl it comes from.
"""
import numpy as np

# detection threshold in wt% solid (low, high) and supercooling slope in C per (C/min) (low, high),
# typical cooling rate C/min (low, high), repeatability SD in C
METHODS = {
  # CPM: crystals of 0.5-1 um, about 0.01-0.1 wt% (cd2005_cpm_crystal_size, hrc2003_detection_limits)
  "CPM":        dict(thr=(0.005, 0.05), k=(0.5, 1.5), rate=(0.3, 1.0), sd=1.0),
  # NIR/FTIR scattering: NIR sees crystallites < 55 nm (paso2009); DSC minus FTIR +0.45 C (own_dsc_minus_ftir_bouzas)
  "NIR":        dict(thr=(0.005, 0.05), k=(0.5, 1.5), rate=(0.3, 1.0), sd=1.0),
  "FTIR":       dict(thr=(0.05, 0.3), k=(0.5, 1.5), rate=(0.5, 1.0), sd=0.8),   # us6841779_ftir_repeat SD 0.76
  # DSC: 0.1-0.5 wt% (dsc_threshold_memory, low confidence); cooling-rate slope -0.64 to -3.3 C/(C/min) (ta429_*)
  "DSC":        dict(thr=(0.1, 0.5), k=(0.64, 3.3), rate=(0.5, 5.0), sd=1.0),
  "uDSC":       dict(thr=(0.05, 0.2), k=(0.64, 2.0), rate=(0.1, 1.0), sd=0.8),
  # light transmission / laser SDS / ASTM D8420: 0.16-0.43 wt% (coutinho2006_sds_threshold); repeatability 1.96 C (astm_d8420_repeatability)
  "D8420":      dict(thr=(0.16, 0.43), k=(0.3, 1.0), rate=(0.5, 1.0), sd=1.96 / 2.77),
  # viscometry: 0.3-1 wt% for a 2.5% deviation (cd2005_visc_needs_1pct)
  "viscometry": dict(thr=(0.3, 1.0), k=(0.5, 1.5), rate=(0.2, 1.0), sd=1.5),
  # filter plugging: about 1 wt% (coutinho2006_filter_threshold)
  "filter":     dict(thr=(0.8, 1.2), k=(0.5, 1.5), rate=(0.2, 1.0), sd=1.5),
  # ASTM D2500 cloud point: visual, light oils only (astm_d2500_scope); precision memory-based (low)
  "D2500":      dict(thr=(0.05, 0.3), k=(0.5, 1.0), rate=(0.5, 1.0), sd=2 / 2.77),
}
# Viscometry with previous thermal history kept reads 3.6 to 8.8 C lower (own_visc_kept_vs_erased_ans)
HISTORY_KEPT_SHIFT = (-8.8, -3.6)
# gel / pour point: Gulf of Mexico crude gelled at about 2 wt% solids (us6841779_gel_solids, 1-2 wt%);
# range widened to 1-5 wt% to cover pour point depression by natural inhibitors (assumption, calibrated later)
POUR_GEL_THRESHOLD = (1.0, 5.0)

def temp_at_solid(T_grid, S, thr):
    """Highest temperature at which solid fraction S (decreasing T grid order not required) >= thr."""
    T_grid = np.asarray(T_grid); S = np.asarray(S)
    idx = np.argsort(-T_grid); T = T_grid[idx]; s = S[idx]   # hot to cold
    above = np.where(s >= thr)[0]
    if len(above) == 0: return np.nan
    j = above[0]
    if j == 0: return T[0]
    # linear interpolation between j-1 (below thr) and j
    t0, t1, s0, s1 = T[j-1], T[j], s[j-1], s[j]
    return t0 + (thr - s0) * (t1 - t0) / (s1 - s0) if s1 != s0 else t1

def measure_wat(T_grid, S, method, rng, history_kept=False, rate=None, return_detail=False):
    m = METHODS[method]
    thr = rng.uniform(*m["thr"])
    r = rate if rate is not None else rng.uniform(*m["rate"])
    k = rng.uniform(*m["k"])
    t = temp_at_solid(T_grid, S, thr)
    wat = t - k * r + rng.normal(0, m["sd"])
    if history_kept and method == "viscometry":
        wat += rng.uniform(*HISTORY_KEPT_SHIFT)
    if return_detail:
        return wat, dict(threshold_wt=thr, cooling_rate=r, supercool_k=k, onset_at_threshold=t)
    return wat

def measure_pour(T_grid, S, rng, sd=1.5):
    """Pour point as the gel temperature: solid fraction reaches a gel threshold (assumption).
    ASTM D97 reports in 3 C steps: rounded accordingly."""
    thr = rng.uniform(*POUR_GEL_THRESHOLD)
    t = temp_at_solid(T_grid, S, thr) + rng.normal(0, sd)
    return 3 * np.round(t / 3), thr

def map_method(label):
    """Map a free-text master_v9 wat_method to a measurement-layer method (or None if unknown)."""
    s = str(label).lower()
    if "d8420" in s or "ip 389" in s or "ip389" in s or "light transmission" in s or "laser" in s: return "D8420"
    if "d2500" in s or "cloud point" in s: return "D2500"
    if "udsc" in s or "micro-dsc" in s or "microdsc" in s or "hp-udsc" in s: return "uDSC"
    if "dsc" in s or "calorimetr" in s: return "DSC"
    if "cpm" in s or "polari" in s or "microscop" in s or "plm" in s: return "CPM"
    if "nir" in s: return "NIR"
    if "ftir" in s or "ft-ir" in s: return "FTIR"
    if "visco" in s or "rheo" in s or "flow curve" in s: return "viscometry"
    if "filter" in s: return "filter"
    return None
