"""Physics layer: n-paraffin description -> solid wax curve -> 'true' WAT.

Engine: agents/thermo/thermo_wat.py (Coutinho 2006 n-alkane properties; multisolid with ideal
liquid gives a lower bound, one ideal solid solution gives an upper bound; real waxes sit in
between, WAT = WAT_ms + f (WAT_ss - WAT_ms), f fitted on 10 published systems: mean 0.55, sd 0.23).
The solid curve of the bracket model is taken as the multisolid curve shifted up in temperature
by f (WAT_ss - WAT_ms) (ASSUMPTION).

To make sampling and calibration fast, a lookup table is precomputed over the latent grid
(n-paraffin wt%, mass-mean carbon number, spread, oil molar mass) storing WAT_ms, WAT_ss and the
temperature at which the multisolid solid fraction reaches each of several thresholds.
"""
import numpy as np
from itertools import product
from modules import thermo as tw

THRESH = np.array([0.003, 0.005, 0.01, 0.02, 0.05, 0.1, 0.16, 0.2, 0.3, 0.43, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.0])
GRID = dict(
    npw=np.round(np.geomspace(0.2, 40, 16), 4),   # n-paraffin wt% of oil
    mcn=np.arange(18, 47, 2.0),                    # mass-mean carbon number of the n-paraffin block
    spr=np.array([2.5, 3.5, 5.0, 6.5, 8.0, 10.0]),  # mass SD of carbon number
    M=np.array([120, 160, 200, 250, 320, 420.0]),   # oil number-average molar mass g/mol
)
T_GRID = np.arange(-70.0, 110.01, 0.5) + 273.15

def oil_molar_mass(api):
    """Cragoe (1929) M = 6084/(API - 5.9). FROM MEMORY, low confidence; clipped to 120-450.
    Used only to convert n-paraffin mass fractions to mole fractions; a latent multiplier is applied."""
    api = np.asarray(api, float)
    return np.clip(6084.0 / np.maximum(api - 5.9, 5.0), 120, 450)

def _thr_temps(Tg, S):
    """temperatures (C) at which solid wt% S first reaches each THRESH, scanning hot to cold"""
    out = np.full(len(THRESH), np.nan)
    Th = Tg[::-1] - 273.15; s = S[::-1]
    for k, thr in enumerate(THRESH):
        j = np.argmax(s >= thr)
        if s[j] < thr: continue
        if j == 0: out[k] = Th[0]; continue
        t0, t1, s0, s1 = Th[j-1], Th[j], s[j-1], s[j]
        out[k] = t0 + (thr - s0) * (t1 - t0) / (s1 - s0)
    return out

def sim_point(npw, mcn, spr, M, n_min=15):
    try:
        n, w, x = tw.build_nparaffin_distribution(npw, mcn, spr, M, n_min=n_min, n_max=100)
        ms = tw.wat_multisolid(n, x)
        ss = tw.wat_ideal_solid_solution(n, x)
        _, Sw = tw.solid_curve_multisolid(n, x, T_GRID, M_inert=M)
        return np.r_[ms - 273.15, ss - 273.15, _thr_temps(T_GRID, Sw)]
    except Exception:
        return np.full(2 + len(THRESH), np.nan)

def build_table(path, n_jobs=2):
    from joblib import Parallel, delayed
    keys = list(product(GRID["npw"], GRID["mcn"], GRID["spr"], GRID["M"]))
    res = Parallel(n_jobs=n_jobs, batch_size=64)(delayed(sim_point)(*k) for k in keys)
    arr = np.array(res).reshape(len(GRID["npw"]), len(GRID["mcn"]), len(GRID["spr"]), len(GRID["M"]), -1)
    np.savez_compressed(path, arr=arr, thresh=THRESH, **GRID)
    return arr

class Table:
    def __init__(self, path):
        from scipy.interpolate import RegularGridInterpolator
        z = np.load(path)
        self.arr = z["arr"]; self.thresh = z["thresh"]
        axes = (np.log(z["npw"]), z["mcn"], z["spr"], np.log(z["M"]))
        self.lim = [(a.min(), a.max()) for a in axes]
        self.f = RegularGridInterpolator(axes, self.arr, bounds_error=False, fill_value=None)
    def query(self, npw, mcn, spr, M):
        X = np.c_[np.log(npw), mcn, spr, np.log(M)]
        for i, (lo, hi) in enumerate(self.lim): X[:, i] = np.clip(X[:, i], lo, hi)
        return self.f(X)   # columns: wat_ms, wat_ss, T at each threshold (multisolid curve)

def solid_temp(q, frac_bracket, thr):
    """Temperature (C) where the bracket-model solid fraction reaches thr wt% (array per row)."""
    ms, ss = q[:, 0], q[:, 1]
    shift = frac_bracket * (ss - ms)
    T = np.empty(len(q))
    lt = np.log(THRESH)
    for i in range(len(q)):
        row = q[i, 2:]
        ok = np.isfinite(row)
        T[i] = np.interp(np.log(thr[i]), lt[ok], row[ok]) if ok.sum() > 1 else np.nan
    return T + shift
