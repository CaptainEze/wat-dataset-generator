"""Latent prior for the hidden n-paraffin description of a crude, and the forward simulator
(inputs + latent -> pour point, WAT by method). Parameters theta are calibrated in calibrate.py."""
import numpy as np
from modules.physics import oil_molar_mass, solid_temp
from modules.measurement import METHODS, HISTORY_KEPT_SHIFT

THETA0 = dict(mu_cn=27.0, b_api=-0.15, sd_cn=4.0,      # mass-mean carbon number ~ N(mu + b (API-35), sd)
              m_fn=0.45, k_fn=6.0,                     # n-paraffin share of measured wax ~ Beta(mean m_fn, conc k_fn)
              g_lo=1.0, g_hi=5.0,                      # pour point gel threshold, wt% solid, log-uniform
              sd_M=0.15)                               # lognormal multiplier on Cragoe molar mass
BRACKET = (0.55, 0.23)
REF_THR = 0.01   # wt% solid, reference (CPM-like) detection threshold
REF_RATE = 0.5   # C/min
MAX_DROP = 20.0  # C, beyond this the method is treated as not detecting a WAT   # thermo agent T8: f over 10 published systems (mean, sd)

def draw_latent(rng, api, wax, theta, n):
    """n latent draws per crude, vectorised over crudes (api, wax arrays of length m) -> arrays (m, n)."""
    api = np.asarray(api, float)[:, None]; wax = np.asarray(wax, float)[:, None]
    m = api.shape[0]
    mcn = np.clip(theta["mu_cn"] + theta["b_api"] * (api - 35) + theta["sd_cn"] * rng.standard_normal((m, n)), 18, 46)
    spr = rng.uniform(3.0, 8.0, (m, n))
    a = theta["m_fn"] * theta["k_fn"]; b = (1 - theta["m_fn"]) * theta["k_fn"]
    fn = rng.beta(max(a, 0.05), max(b, 0.05), (m, n))
    npw = np.clip(wax * fn, 0.2, 40)
    M = oil_molar_mass(api) * np.exp(theta["sd_M"] * rng.standard_normal((m, n)))
    fb = np.clip(rng.normal(*BRACKET, (m, n)), 0, 1)
    gel = np.exp(rng.uniform(np.log(theta["g_lo"]), np.log(theta["g_hi"]), (m, n)))
    return dict(mcn=mcn, spr=spr, fn=fn, npw=npw, M=M, fb=fb, gel=gel)

def forward(table, lat, method_idx, rng):
    """Simulate pour point and measured WAT for every latent draw.
    method_idx: array (m,) of method names. Returns dict of arrays (m, n)."""
    m, n = lat["mcn"].shape
    q = table.query(lat["npw"].ravel(), lat["mcn"].ravel(), lat["spr"].ravel(), np.clip(lat["M"].ravel(), 120, 420))
    fb = lat["fb"].ravel()
    true = q[:, 0] + fb * (q[:, 1] - q[:, 0])
    pour_raw = solid_temp(q, fb, lat["gel"].ravel()) + rng.normal(0, 1.5, m * n)
    pour = 3 * np.round(pour_raw / 3)
    meth = np.repeat(np.asarray(method_idx), n)
    thr = np.empty(m * n); k = np.empty(m * n); r = np.empty(m * n); sd = np.empty(m * n)
    for name, p in METHODS.items():
        s = meth == name
        if not s.any(): continue
        c = s.sum()
        thr[s] = np.exp(rng.uniform(np.log(p["thr"][0]), np.log(p["thr"][1]), c))
        k[s] = rng.uniform(*p["k"], c); r[s] = rng.uniform(*p["rate"], c); sd[s] = p["sd"]
    # The bracket WAT was fitted to measured WATs from sensitive methods (thermo agent T8), so it is the
    # reference. Method offsets are relative: the drop in temperature between the reference detection
    # threshold (REF_THR wt% solid, CPM-like) and the method threshold, plus supercooling relative to
    # a reference cooling rate of REF_RATE C/min.
    t_ref = solid_temp(q, fb, np.full(m * n, REF_THR))
    t_m = solid_temp(q, fb, thr)
    drop = t_ref - t_m
    wat = true - drop - k * (r - REF_RATE) + rng.normal(0, 1, m * n) * sd
    # A method that needs far more solid than the oil precipitates near onset reports no clear WAT.
    # Cap from Coutinho and Daridon 2005: method-dependent error "as much as 20 K" (fact cd2005_method_error_20K).
    wat = np.where(drop > MAX_DROP, np.nan, wat)
    rs = lambda a: a.reshape(m, n)
    return dict(true=rs(true), pour=rs(pour), wat=rs(wat), pour_raw=rs(pour_raw))
