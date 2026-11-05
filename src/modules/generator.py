"""Generate synthetic WAT datapoints.

Modes
  forward   : API, viscosity and wax content drawn from the real-crude copula (inputs.InputSampler);
              hidden n-paraffin description drawn from the calibrated prior; pour point and WAT
              (true and as measured by a chosen method) computed by the physics + measurement layers.
  anchored  : start from REAL crudes that have API, wax and pour point but no WAT (NOAA ADIOS + local pool);
              hidden description drawn from the prior and re-weighted by agreement with the real pour point
              (importance resampling); WAT computed as above. Inputs are therefore real, WAT is simulated.
Every row carries provenance: mode, theta file, method, latent values, pool id and the importance ESS.

CLI:  python src/generate.py --mode forward --n 5000 --theta src/modules/params/theta_J.json --out data/synthetic/synth.csv
"""
import argparse, json, os, sys, numpy as np, pandas as pd
from modules.physics import Table
from modules.latent import draw_latent, forward as fwd, THETA0
from modules.inputs import load_pool, InputSampler
from modules.data import unlabelled
from modules.paths import LATENT_TABLE, NOAA_POOL, LOCAL_POOL
from modules import bulk as br

DEFAULT_MIX = {"DSC": 0.4, "CPM": 0.2, "viscometry": 0.15, "D8420": 0.1, "uDSC": 0.1, "NIR": 0.05}

def _density15(api):
    return np.array([br.rho15_from_api(a) for a in api])

def _methods(rng, n, mix):
    k = list(mix); p = np.array([mix[x] for x in k], float); p /= p.sum()
    return np.array(k)[rng.choice(len(k), n, p=p)]

def generate(mode="forward", n=1000, theta=None, method_mix=None, seed=0, table=None, K=200):
    rng = np.random.default_rng(seed)
    theta = theta or THETA0; mix = method_mix or DEFAULT_MIX
    tab = table or Table(LATENT_TABLE)
    if mode == "forward":
        pool = load_pool(NOAA_POOL, LOCAL_POOL)
        X = InputSampler(pool, seed=seed).sample(n)
        meth = _methods(rng, len(X), mix)
        lat = draw_latent(rng, X.api15.values, X.wax_wt_pct.values, theta, 1)
        sim = fwd(tab, lat, meth, rng)
        out = pd.DataFrame(dict(api15=X.api15, visc40_cSt=10 ** X.log_visc40, wax_wt_pct=X.wax_wt_pct,
                                pour_c=sim["pour"][:, 0], wat_c=sim["wat"][:, 0], wat_true_c=sim["true"][:, 0],
                                wat_method=meth, pool_id="", ess=np.nan))
        for k in ["mcn", "spr", "fn", "npw", "M", "fb", "gel"]: out["lat_" + k] = lat[k][:, 0]
    elif mode == "anchored":
        P = unlabelled()
        idx = rng.choice(len(P), n, replace=True)
        X = P.iloc[idx].reset_index(drop=True)
        meth = _methods(rng, len(X), mix)
        lat = draw_latent(rng, X.api15.values, X.wax_wt_pct.values, theta, K)
        sim = fwd(tab, lat, meth, rng)
        z = -0.5 * ((sim["pour_raw"] - X.pour_c.values[:, None]) / 3.0) ** 2
        z = np.where(np.isfinite(z) & np.isfinite(sim["wat"]), z, -np.inf)
        w = np.exp(z - z.max(1, keepdims=True)); w /= w.sum(1, keepdims=True)
        ess = 1 / (w ** 2).sum(1)
        pick = np.array([rng.choice(K, p=w[i]) for i in range(len(X))])
        r = np.arange(len(X))
        out = pd.DataFrame(dict(api15=X.api15, visc40_cSt=X.visc40, wax_wt_pct=X.wax_wt_pct, pour_c=X.pour_c,
                                wat_c=sim["wat"][r, pick], wat_true_c=sim["true"][r, pick], wat_method=meth,
                                pool_id=X.src.astype(str) + ":" + X["name"].astype(str), ess=ess))
        for k in ["mcn", "spr", "fn", "npw", "M", "fb", "gel"]: out["lat_" + k] = lat[k][r, pick]
    else:
        raise ValueError(mode)
    out.insert(0, "mode", mode)
    out["density15"] = _density15(out.api15.values)
    out = out[np.isfinite(out.wat_c)].reset_index(drop=True)
    out.insert(0, "synth_id", [f"S{mode[0].upper()}{seed}_{i:06d}" for i in range(len(out))])
    out["synthetic"] = True
    return out

class SyntheticGenerator:
    def __init__(self, theta_path=None, seed=0):
        self.theta_path = theta_path
        self.theta = json.load(open(theta_path))["theta"] if theta_path else None
        self.seed = seed
        self.table = Table(LATENT_TABLE)

    def run(self, mode="forward", n=1000, method=None, method_mix=None, seed=None):
        mix = {method: 1.0} if method else method_mix
        df = generate(mode, n, self.theta, mix, self.seed if seed is None else seed, table=self.table)
        df["theta_file"] = os.path.basename(self.theta_path) if self.theta_path else "THETA0"
        return df
