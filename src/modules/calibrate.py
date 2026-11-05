"""Calibrate the latent prior theta by maximum simulated likelihood.

Two data kinds:
  U  unlabelled real crudes with API, wax and pour point but no WAT (NOAA ADIOS + local pool):
     term log p(pour | API, wax, theta)                           <- the unsupervised part
  L  labelled real rows with API, wax, pour and a measured WAT (master v9, optionally restricted):
     term log p(pour, WAT | API, wax, method, theta)
Likelihoods are kernel estimates over K latent draws per crude (Gaussian kernels, sd 3 C),
with common random numbers so the objective is smooth for Nelder-Mead.
Use labelled=None for a WAT-free calibration (no leakage into any evaluation).
"""
import numpy as np, pandas as pd
from scipy.optimize import minimize
from modules.latent import THETA0, draw_latent, forward

KEYS = ["mu_cn", "b_api", "sd_cn", "m_fn", "k_fn", "g_lo", "g_hi"]
BOUNDS = dict(mu_cn=(19, 42), b_api=(-0.6, 0.4), sd_cn=(1.0, 8.0), m_fn=(0.05, 0.98), k_fn=(1.5, 40),
              g_lo=(0.2, 4.0), g_hi=(0.5, 10.0))

def _to_theta(x):
    th = dict(THETA0)
    for k, v in zip(KEYS, x):
        lo, hi = BOUNDS[k]; th[k] = lo + (hi - lo) / (1 + np.exp(-v))
    if th["g_hi"] < th["g_lo"] * 1.05: th["g_hi"] = th["g_lo"] * 1.05
    return th

def _to_x(th):
    out = []
    for k in KEYS:
        lo, hi = BOUNDS[k]; p = (th[k] - lo) / (hi - lo); p = min(max(p, 1e-3), 1 - 1e-3)
        out.append(np.log(p / (1 - p)))
    return np.array(out)

def _logmeanexp(a, axis=1):
    mx = np.max(a, axis=axis, keepdims=True)
    return (mx + np.log(np.mean(np.exp(a - mx), axis=axis, keepdims=True))).squeeze(axis)

def loglik(theta, table, U, L, K=120, seed=0, sp=3.0, sw=3.0):
    tot = 0.0; parts = {}
    if U is not None and len(U):
        rng = np.random.default_rng(seed)
        lat = draw_latent(rng, U.api15.values, U.wax_wt_pct.values, theta, K)
        sim = forward(table, lat, np.array(["DSC"] * len(U)), rng)
        z = -0.5 * ((sim["pour_raw"] - U.pour_c.values[:, None]) / sp) ** 2
        z = np.where(np.isfinite(z), z, -50)
        ll = _logmeanexp(z) - np.log(sp * np.sqrt(2 * np.pi)); parts["U"] = ll.mean(); tot += ll.sum()
    if L is not None and len(L):
        rng = np.random.default_rng(seed + 1)
        lat = draw_latent(rng, L.api15.values, L.wax_wt_pct.values, theta, K)
        sim = forward(table, lat, L.meas_method.values, rng)
        z = -0.5 * ((sim["pour_raw"] - L.pour_c.values[:, None]) / sp) ** 2 - 0.5 * ((sim["wat"] - L.wat_c.values[:, None]) / sw) ** 2
        z = np.where(np.isfinite(z), z, -50)
        ll = _logmeanexp(z) - np.log(sp * sw * 2 * np.pi); parts["L"] = ll.mean(); tot += ll.sum()
    return tot, parts

def fit(table, U, L=None, theta0=None, K=120, maxiter=300, seed=0):
    th0 = dict(theta0 or THETA0)
    f = lambda x: -loglik(_to_theta(x), table, U, L, K, seed)[0]
    r = minimize(f, _to_x(th0), method="Nelder-Mead", options=dict(maxiter=maxiter, xatol=1e-3, fatol=1e-2, adaptive=True))
    th = _to_theta(r.x)
    return th, -r.fun, loglik(th, table, U, L, K, seed)[1]

def posterior_predict(theta, table, df, K=400, seed=7, sp=3.0, use_pour=True):
    """Posterior predictive WAT for real crudes given API, wax, pour and method:
    latent draws weighted by agreement of simulated and observed pour point."""
    rng = np.random.default_rng(seed)
    lat = draw_latent(rng, df.api15.values, df.wax_wt_pct.values, theta, K)
    sim = forward(table, lat, df.meas_method.values, rng)
    if use_pour:
        z = -0.5 * ((sim["pour_raw"] - df.pour_c.values[:, None]) / sp) ** 2
        z = np.where(np.isfinite(z) & np.isfinite(sim["wat"]), z, -np.inf)
        w = np.exp(z - np.nanmax(z, axis=1, keepdims=True)); w = np.where(np.isfinite(w), w, 0)
    else:
        w = np.isfinite(sim["wat"]).astype(float)
    w = w / w.sum(1, keepdims=True)
    wat = np.where(np.isfinite(sim["wat"]), sim["wat"], 0)
    mean = (w * wat).sum(1); sd = np.sqrt((w * (wat - mean[:, None]) ** 2).sum(1))
    ess = 1 / (w ** 2).sum(1)
    return mean, sd, ess, sim, w


class Calibrator:
    """Wraps fit / loglik / posterior_predict. Global search (differential evolution) is the
    reliable option: Nelder-Mead stays near its starting point on this noisy objective."""
    def __init__(self, table, U, L=None, K=70, seed=0):
        self.table, self.U, self.L, self.K, self.seed = table, U, L, K, seed

    def fit_global(self, popsize=6, maxiter=30, de_seed=1):
        from scipy.optimize import differential_evolution
        f = lambda x: -loglik(_to_theta(x), self.table, self.U, self.L, self.K, self.seed)[0]
        r = differential_evolution(f, [(-4, 4)] * len(KEYS), popsize=popsize, maxiter=maxiter, tol=1e-4, seed=de_seed, polish=False)
        th = _to_theta(r.x)
        return th, loglik(th, self.table, self.U, self.L, K=200, seed=3)

    def predict(self, theta, df, K=500):
        return posterior_predict(theta, self.table, df, K=K)
