"""Input sampler: Gaussian copula over transformed bulk properties, fitted on real crudes
(NOAA ADIOS 1134 crudes + local pool 374 crudes). Pairwise-complete correlations; empirical
marginals with light smoothing. Returns physically screened vectors."""
import numpy as np, pandas as pd
from scipy import stats

VARS = ["api15", "log_visc40", "pour_c", "wax_wt_pct"]

def load_pool(noaa_csv, local_csv, include_condensate=True):
    n = pd.read_csv(noaa_csv)
    if not include_condensate:
        n = n[n.product_type != "Condensate"]
    n = pd.DataFrame({"api15": n.api, "visc40": n.visc40_cSt, "pour_c": n.pour_c,
                      "wax_wt_pct": n.wax_wt_pct, "src": "noaa", "name": n.name,
                      "pour_censored": n.pour_flag.fillna("").str.startswith("max")})
    l = pd.read_csv(local_csv)
    l = pd.DataFrame({"api15": l.api15, "visc40": l.visc40_cSt, "pour_c": l.pour_c,
                      "wax_wt_pct": l.wax_wt_pct, "src": "local:" + l.source.astype(str), "name": l["name"],
                      "pour_censored": False})
    p = pd.concat([n, l], ignore_index=True)
    p["log_visc40"] = np.log10(p.visc40.where(p.visc40 > 0))
    # light de-duplication: same name (lower) and same rounded API
    key = p["name"].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + "_" + p.api15.round(0).astype(str)
    p = p.loc[~key.duplicated()].reset_index(drop=True)
    return p

def _nearest_pd(c):
    w, v = np.linalg.eigh((c + c.T) / 2)
    w = np.clip(w, 1e-6, None)
    c2 = v @ np.diag(w) @ v.T
    d = np.sqrt(np.diag(c2)); return c2 / np.outer(d, d)

class InputSampler:
    def __init__(self, pool, vars=VARS, smooth=0.05, seed=0):
        self.vars = vars; self.rng = np.random.default_rng(seed)
        self.marg = {}
        Z = pd.DataFrame(index=pool.index)
        for v in vars:
            x = pool[v].dropna().values
            self.marg[v] = np.sort(x)
            # normal scores via ranks
            r = stats.rankdata(pool[v].dropna()) / (len(x) + 1)
            Z.loc[pool[v].dropna().index, v] = stats.norm.ppf(r)
        self.corr = _nearest_pd(Z[vars].astype(float).corr(min_periods=30).values)
        self.smooth = smooth
        self.n_pairs = {(a, b): int(Z[[a, b]].dropna().shape[0]) for a in vars for b in vars}

    def _inv(self, v, u):
        x = self.marg[v]; q = np.quantile(x, u)
        sd = np.std(x) * self.smooth
        return q + self.rng.normal(0, sd, size=len(u))

    def sample(self, n, max_tries=20):
        out = []
        for _ in range(max_tries):
            z = self.rng.multivariate_normal(np.zeros(len(self.vars)), self.corr, size=n * 2)
            u = stats.norm.cdf(z)
            df = pd.DataFrame({v: self._inv(v, u[:, i]) for i, v in enumerate(self.vars)})
            df = screen_inputs(df)
            out.append(df)
            if sum(len(o) for o in out) >= n: break
        return pd.concat(out, ignore_index=True).iloc[:n]

def screen_inputs(df):
    """Hard physical limits for dead crude oils at ambient pressure."""
    ok = (df.api15.between(8, 75) & df.wax_wt_pct.between(0.1, 45) & df.pour_c.between(-60, 55)
          & df.log_visc40.between(-0.5, 4.5))
    return df[ok].reset_index(drop=True)
