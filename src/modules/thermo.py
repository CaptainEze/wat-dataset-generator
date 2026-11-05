"""
thermo_wat.py : a small physics engine for wax appearance temperature (WAT)
and the solid (wax) fraction curve of a dead crude oil at atmospheric pressure.

Written for the WAT synthetic-data study (agents/thermo). Every correlation is
tagged SOURCE (copied from a paper, with where it was read) or ASSUMPTION
(a modelling choice made here, not taken from a paper). See models.jsonl in the
same folder for full citations.

Main entry points
-----------------
nalkane_props(n, props="coutinho")                 pure n-alkane Tm, dHm, Ttr, dHtr, dCp
wat_multisolid(n, z, ...)                          (a) multisolid, pure solids, ideal liquid
solid_curve_multisolid(n, z, T_grid, ...)          solid wt% vs T for (a)
wat_ideal_solid_solution(n, z, ...)                ideal solid solution (Pedersen 1995 style)
solid_curve_ideal_ss(n, z, T_grid, ...)            solid mole and wt% vs T
pedersen_wat(density_15C, M_oil, wax_wt_pct, ...)  (b) Pedersen-style crude model
build_nparaffin_distribution(wax_wt_pct, mean_cn, spread, M_oil, ...)   (c)
wat_from_bulk(wax_wt_pct, mean_cn, spread, M_oil, ...)  (c) + (a) or ideal SS

Units: temperature K inside, mole fractions, molar masses g/mol,
enthalpies J/mol, densities g/cm3 at 15 C unless stated.

General SLE relation used (SOURCE: standard form, as printed in the NeqSim
wax documentation and in Coutinho et al. 2006 Energy Fuels eqs 4 and 7,
pressure term dropped because we work at about 1 bar):

  ln(x_s*gamma_s / (x_l*gamma_l)) = (dHm/RT)(1 - T/Tm)
                                    + (dHtr/RT)(1 - T/Ttr)   [only if T < Ttr]
                                    - (dCp/R)(Tm/T - 1 - ln(Tm/T))   [optional]
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

R = 8.314462618  # J/(mol K)
CAL = 4.184      # J per cal (thermochemical)


# ---------------------------------------------------------------------------
# 1. Pure n-alkane properties
# ---------------------------------------------------------------------------

def mw_nalkane(n):
    """Molar mass of n-CnH(2n+2), g/mol (exact stoichiometry, 14.027n + 2.016)."""
    n = np.asarray(n, dtype=float)
    return 14.02658 * n + 2.01588


def coutinho_Tm(n):
    """SOURCE: Coutinho et al. 2006 Energy Fuels 20:1081, eq 2.
    Tm = 421.63 - 1936412*exp(-7.8945*(N-1)**0.07194)  [K]"""
    n = np.asarray(n, dtype=float)
    return 421.63 - 1936412.0 * np.exp(-7.8945 * (n - 1.0) ** 0.07194)


def coutinho_dH_total(n):
    """SOURCE: Coutinho et al. 2006 eq 3, melting enthalpy of the orthorhombic
    crystal (total heat, fusion plus transitions): dH = 3779.1 N - 12654 J/mol."""
    n = np.asarray(n, dtype=float)
    return 3779.1 * n - 12654.0


def coutinho_dHm_rotator(n):
    """SOURCE: Coutinho et al. 2006 eq 5, fusion enthalpy from the rotator phase,
    n-C8 to n-C40: dHm = 3.55N^3 - 237.6N^2 + 7400N - 34814 J/mol."""
    n = np.asarray(n, dtype=float)
    return 3.55 * n**3 - 237.6 * n**2 + 7400.0 * n - 34814.0


def coutinho_Ttr(n):
    """SOURCE: Coutinho et al. 2006 eq 6, rotator to orthorhombic transition:
    Ttr = 420.42 - 134784*exp(-4.344*(N+6.592)**0.14627) [K]."""
    n = np.asarray(n, dtype=float)
    return 420.42 - 134784.0 * np.exp(-4.344 * (n + 6.592) ** 0.14627)


def won_Tf(M):
    """SOURCE: Won 1986 (Fluid Phase Equilib 30:265), as printed in
    Lira-Galeana et al. LBL-36816 eq 8 and NeqSim WaxCharacterise.java:
    Tf = 374.5 + 0.02617 M - 20172/M [K]."""
    M = np.asarray(M, dtype=float)
    return 374.5 + 0.02617 * M - 20172.0 / M


def won_dHf(M, Tf):
    """SOURCE: Won 1986, dHf = 0.1426 M Tf [cal/mol]; returned in J/mol."""
    return 0.1426 * np.asarray(M, float) * np.asarray(Tf, float) * CAL


def lira_Tf(M):
    """SOURCE: Lira-Galeana et al. 1996 (preprint LBL-36816 eq 9):
    Tf = 333.46 - 419.01*exp(-0.008546 M) [K]. Fitted to paraffins,
    naphthenes and aromatics C6-C30 (API RP44). Leading constant was OCR-garbled
    in the preprint; 0.008546 is also printed in Escobar-Remolina 2009."""
    M = np.asarray(M, dtype=float)
    return 333.46 - 419.01 * np.exp(-0.008546 * M)


def lira_dHf(M, Tf):
    """SOURCE: Lira-Galeana et al. eq 11, dHf = 0.05276 M Tf [cal/mol] -> J/mol."""
    return 0.05276 * np.asarray(M, float) * np.asarray(Tf, float) * CAL


def pedersen_dCp(M, T):
    """SOURCE: Pedersen et al. 1991 (Energy Fuels 5:924), via Lira-Galeana eq 12
    and NeqSim: dCp = 0.3033 M - 4.635e-4 M T [cal/(mol K)]; returned J/(mol K)."""
    M = np.asarray(M, float)
    return (0.3033 * M - 4.635e-4 * M * T) * CAL


def broadhurst_Tm(n):
    """SOURCE: Broadhurst 1962 J Res NBS 66A:241, Tm = 414.3 (n-1.5)/(n+5.0) K,
    fitted to n >= 44 (orthorhombic melting)."""
    n = np.asarray(n, dtype=float)
    return 414.3 * (n - 1.5) / (n + 5.0)


@dataclass
class Props:
    Tm: np.ndarray
    dHm: np.ndarray
    Ttr: np.ndarray     # nan where no transition
    dHtr: np.ndarray    # 0 where no transition
    M: np.ndarray


def nalkane_props(n, props: str = "coutinho") -> Props:
    """Pure n-alkane melting and transition properties by carbon number n.

    props = "coutinho": Coutinho 2006 eqs 2, 3, 5, 6. For 8 <= N <= 40 the solid
        is taken to pass rotator -> orthorhombic at Ttr with dHtr = eq3 - eq5
        (SOURCE: the paper says the transition enthalpy "can be obtained from a
        difference between eqs 3 and 5"). Outside that range, dHm = eq 3 and no
        transition. Odd/even differences are not represented (smooth fit).
    props = "won": Won 1986 Tf(M), dHf(M) with no transition.
    props = "lira": Lira-Galeana 1996 Tf(M), dHf(M) with no transition.
    """
    n = np.atleast_1d(np.asarray(n, dtype=float))
    M = mw_nalkane(n)
    if props == "coutinho":
        Tm = coutinho_Tm(n)
        has_tr = (n >= 8) & (n <= 40)
        dHm = np.where(has_tr, coutinho_dHm_rotator(n), coutinho_dH_total(n))
        Ttr = np.where(has_tr, coutinho_Ttr(n), np.nan)
        dHtr = np.where(has_tr, coutinho_dH_total(n) - coutinho_dHm_rotator(n), 0.0)
        dHtr = np.clip(dHtr, 0.0, None)
    elif props == "won":
        Tm = won_Tf(M)
        dHm = won_dHf(M, Tm)
        Ttr = np.full_like(n, np.nan)
        dHtr = np.zeros_like(n)
    elif props == "lira":
        Tm = lira_Tf(M)
        dHm = lira_dHf(M, Tm)
        Ttr = np.full_like(n, np.nan)
        dHtr = np.zeros_like(n)
    else:
        raise ValueError(props)
    return Props(Tm=Tm, dHm=dHm, Ttr=Ttr, dHtr=dHtr, M=M)


def ln_Kpure(T, p: Props, use_dcp: bool = False):
    """ln of (pure subcooled liquid fugacity / pure solid fugacity) at T, i.e.
    the right-hand side of the SLE equation. Positive below Tm.
    Returns an array over components."""
    T = float(T)
    val = (p.dHm / (R * T)) * (1.0 - T / p.Tm)
    tr = np.where(np.isfinite(p.Ttr) & (T < np.nan_to_num(p.Ttr, nan=-1.0)),
                  (p.dHtr / (R * T)) * (1.0 - T / np.nan_to_num(p.Ttr, nan=1.0)), 0.0)
    val = val + tr
    if use_dcp:
        dcp = pedersen_dCp(p.M, T)
        val = val - (dcp / R) * (p.Tm / T - 1.0 - np.log(p.Tm / T))
    return val


def _bisect(f, lo, hi, tol=1e-6, it=200):
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return float("nan")
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if abs(hi - lo) < tol:
            break
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# 2a. Multisolid model (Lira-Galeana 1996 idea), ideal liquid
# ---------------------------------------------------------------------------

def saturation_T_pure_solid(z_i, p_i: Props, use_dcp=False, Tlo=150.0):
    """Temperature at which a pure solid of component i first appears from a
    liquid in which its mole fraction is z_i (ideal liquid, gamma_l = 1):
        ln z_i = -lnK_i(T)   (SOURCE: stability test f_i(z) - f_i,pure solid = 0,
        Lira-Galeana et al. eq 3, with ideal liquid as in Coutinho and Daridon 2001)
    """
    if z_i <= 0:
        return float("nan")
    f = lambda T: math.log(z_i) + float(ln_Kpure(T, p_i, use_dcp)[0])
    hi = float(p_i.Tm[0]) - 1e-9
    return _bisect(f, Tlo, hi)


def _subset(p: Props, idx):
    return Props(Tm=p.Tm[idx], dHm=p.dHm[idx], Ttr=p.Ttr[idx], dHtr=p.dHtr[idx], M=p.M[idx])


def wat_multisolid(n: Sequence[float], z: Sequence[float], props: str = "coutinho",
                   use_dcp: bool = False, return_all: bool = False):
    """(a) WAT of a mixture whose n-alkanes (carbon numbers n, mole fractions z in
    the whole liquid) may each freeze out as a pure solid. Everything that is not
    listed is an inert, non-crystallising liquid (mole fraction 1 - sum z).

    WAT = max_i T_i where ln z_i = -lnK_i(T_i).   Returns K.
    Inputs needed: n, z (whole-liquid mole fractions). No molar mass needed when z
    is already a mole fraction; use wt_to_mole() first if you have wt%.
    """
    n = np.asarray(n, float)
    z = np.asarray(z, float)
    p = nalkane_props(n, props)
    Ts = np.array([saturation_T_pure_solid(z[i], _subset(p, [i]), use_dcp) for i in range(len(n))])
    wat = np.nanmax(Ts)
    if return_all:
        return wat, Ts
    return wat


def solid_curve_multisolid(n, z, T_grid, props="coutinho", use_dcp=False, M_inert=None):
    """Multisolid flash with ideal liquid at each T (pure solids).
    For saturated components x_i = x_sat_i(T) = exp(-lnK_i); others x_i = z_i/L.
    Closure: L = sum_unsat z_i / (1 - sum_sat x_sat_i). Iterate set membership.
    Returns (solid mole fraction of feed, solid wt% of feed if M_inert given)."""
    n = np.asarray(n, float); z = np.asarray(z, float)
    p = nalkane_props(n, props)
    z_inert = 1.0 - z.sum()
    out_mol, out_wt = [], []
    for T in T_grid:
        xsat = np.exp(-ln_Kpure(T, p, use_dcp))
        sat = np.zeros(len(n), bool)
        for _ in range(len(n) + 2):
            denom = 1.0 - xsat[sat].sum()
            L = (z_inert + z[~sat].sum()) / denom
            new = sat | (z / L > xsat)
            # drop components that would have negative solid
            s = z - L * np.where(new, xsat, z / L)
            new = new & (s > 0)
            if np.array_equal(new, sat):
                break
            sat = new
        denom = 1.0 - xsat[sat].sum()
        L = (z_inert + z[~sat].sum()) / denom
        s = np.where(sat, z - L * xsat, 0.0)
        out_mol.append(s.sum())
        if M_inert is not None:
            mass_tot = (z * p.M).sum() + z_inert * M_inert
            out_wt.append(100.0 * (s * p.M).sum() / mass_tot)
    return np.array(out_mol), (np.array(out_wt) if M_inert is not None else None)


# ---------------------------------------------------------------------------
# 2b. Ideal solid solution (Pedersen 1995: ideal wax phase; Erickson 1993 idea)
# ---------------------------------------------------------------------------

def wat_ideal_solid_solution(n, z, props="coutinho", use_dcp=False, Tlo=150.0, p: Props | None = None):
    """WAT for one ideal solid solution containing all wax formers, ideal liquid.
    K_i = x_s/x_l = exp(lnK_i(T)).  First solid when  sum_i z_i K_i(T) = 1
    (solid-phase analogue of a bubble point; derived from the SLE relation).
    p may be passed directly (e.g. from pedersen_wat with M-based properties)."""
    z = np.asarray(z, float)
    if p is None:
        p = nalkane_props(np.asarray(n, float), props)
    f = lambda T: math.log(np.sum(z * np.exp(ln_Kpure(T, p, use_dcp))))
    return _bisect(f, Tlo, float(np.max(p.Tm)) + 50.0)


def solid_curve_ideal_ss(n, z, T_grid, props="coutinho", use_dcp=False, M_inert=None, p: Props | None = None):
    """Rachford-Rice style flash: sum z_i (K_i-1)/(1+S(K_i-1)) = 0, inert K=0.
    Returns solid mole fraction S of the feed and solid wt% (if M_inert given)."""
    z = np.asarray(z, float)
    if p is None:
        p = nalkane_props(np.asarray(n, float), props)
    z_inert = 1.0 - z.sum()
    zz = np.append(z, z_inert)
    S_list, W_list = [], []
    for T in T_grid:
        K = np.append(np.exp(ln_Kpure(T, p, use_dcp)), 0.0)
        g = lambda S: np.sum(zz * (K - 1.0) / (1.0 + S * (K - 1.0)))
        if np.sum(zz * K) <= 1.0:
            S = 0.0
        else:
            Kmax = K.max()
            hi = min(1.0, 1.0 / (1.0 - Kmax) if Kmax < 1 else 1.0) - 1e-12
            # S must keep all 1+S(K-1) > 0 ; K=0 => S<1
            S = _bisect(g, 0.0, 1.0 - 1e-12)
            if not np.isfinite(S):
                S = 1.0
        S_list.append(S)
        if M_inert is not None:
            xs = zz * K / (1.0 + S * (K - 1.0))
            Ms = np.append(p.M, M_inert)
            W_list.append(100.0 * S * np.sum(xs * Ms) / np.sum(zz * Ms))
    return np.array(S_list), (np.array(W_list) if M_inert is not None else None)


# ---------------------------------------------------------------------------
# 3. Characterisation helpers
# ---------------------------------------------------------------------------

def wt_to_mole(w_frac, M_i, M_oil):
    """Mass fraction of species i in the oil -> mole fraction, given the oil's
    number-average molar mass: x_i = w_i * M_oil / M_i."""
    return np.asarray(w_frac, float) * M_oil / np.asarray(M_i, float)


def rho_nparaffin_pedersen(M):
    """SOURCE: Pedersen (1991/1995), via NeqSim calcParaffinDensity and Bhangale
    2007 eq 4.29: rho_P = 0.3915 + 0.0675 ln M  [g/cm3]."""
    return 0.3915 + 0.0675 * np.log(np.asarray(M, float))


def sg_riazi_alsahhaf(M):
    """SOURCE: Riazi and Al-Sahhaf, as printed in Ameri Mahabadian et al.
    (Heriot-Watt) eq 2: SG = 1.07 - exp(3.56073 - 2.93886 M^0.1)."""
    return 1.07 - np.exp(3.56073 - 2.93886 * np.asarray(M, float) ** 0.1)


PEDERSEN_ABC = {
    # SOURCE: NeqSim PedersenWaxModel comment "A = 1.074, B = 6.584e-4, C = 0.1915"
    # (Pedersen et al. 1991). NeqSim code itself uses B = 6.584e-6.
    "pedersen1991": (1.074, 6.584e-4, 0.1915),
    "neqsim_code": (1.074, 6.584e-6, 0.1915),
    # SOURCE: Bhangale 2007 Table 4.2, attributed to Pedersen 1995.
    "pedersen1995": (0.8824, 5.353e-4, 0.1144),
    # SOURCE: Ji (Heriot-Watt) refit to WDT, quoted by Ameri Mahabadian et al.
    "ji2004": (0.8133, 5.737e-4, 0.1281),
}


def pedersen_wax_fraction(M, rho, abc="pedersen1991"):
    """SOURCE: Pedersen split of each pseudo-component into a wax-forming part:
    z_s/z = 1 - (A + B M) * ((rho - rho_P)/rho_P)^C, clipped to [0, 1]."""
    A, B, C = PEDERSEN_ABC[abc] if isinstance(abc, str) else abc
    M = np.asarray(M, float); rho = np.asarray(rho, float)
    rp = rho_nparaffin_pedersen(M)
    dev = np.clip((rho - rp) / rp, 0.0, None)
    frac = 1.0 - (A + B * M) * dev ** C
    return np.clip(frac, 0.0, 1.0)


def pedersen_exponential_scn(M_plus, n_start=7, n_max=80, Mn=None):
    """Pedersen exponential plus-fraction model, ln z_n = A + B n
    (SOURCE form: NeqSim fluid characterisation page; Pedersen et al. 1984).
    Solves A, B so that sum z_n = 1 and sum z_n M_n = M_plus.
    ASSUMPTION: M_n = 14 n - 4 g/mol (common SCN molar mass rule, not read in a
    source during this study; flagged)."""
    n = np.arange(n_start, n_max + 1, dtype=float)
    M = 14.0 * n - 4.0 if Mn is None else np.asarray(Mn, float)
    def mean_M(B):
        w = np.exp(B * n); w /= w.sum()
        return float((w * M).sum())
    B = _bisect(lambda b: mean_M(b) - M_plus, -3.0, -1e-6)
    if not np.isfinite(B):
        raise ValueError("M_plus outside reachable range for this n window")
    z = np.exp(B * n); z /= z.sum()
    return n, M, z, B


def pedersen_wat(density_15C: float, M_oil: float, wax_wt_pct: float | None = None,
                 n_start: int = 7, n_max: int = 80, abc="pedersen1991",
                 props: str = "won", use_dcp: bool = True, wax_min_n: int = 20,
                 return_details: bool = False):
    """(b) Pedersen-style WAT of a dead oil from bulk data.

    Steps (SOURCE unless marked):
    1. ASSUMPTION: treat the whole dead oil as a C7+ fluid with molar mass M_oil.
       SCN mole fractions from Pedersen's exponential model ln z_n = A + B n.
    2. ASSUMPTION: SCN densities rho_n = k * SG_RiaziAlSahhaf(M_n), with one
       factor k chosen so that the ideal-mixing density of the SCN set equals
       density_15C (Pedersen instead uses rho_n = C + D ln n; same role).
    3. SOURCE: wax-forming mole fraction of each SCN from the Pedersen split
       (A, B, C set `abc`), rho_P = 0.3915 + 0.0675 ln M.
    4. ASSUMPTION (optional tuning, used by several authors for wax content):
       if wax_wt_pct is given, scale all wax-forming fractions by one factor so
       that the wax-forming mass with n >= wax_min_n equals wax_wt_pct.
    5. SOURCE: ideal solid solution (Pedersen 1995), ideal liquid here
       (Pedersen used SRK for the liquid), Won Tf and dHf by M, Pedersen dCp.
    Returns WAT in K (and details dict if asked).
    """
    n, M, z, B = pedersen_exponential_scn(M_oil, n_start, n_max)
    sg0 = sg_riazi_alsahhaf(M)
    w = z * M / np.sum(z * M)
    k = 1.0 / (density_15C * np.sum(w / sg0))
    rho = k * sg0
    fr = pedersen_wax_fraction(M, rho, abc)
    z_wax = z * fr
    scale = 1.0
    if wax_wt_pct is not None:
        mass = np.sum(z * M)
        cur = 100.0 * np.sum((z_wax * M)[n >= wax_min_n]) / mass
        if cur > 0:
            scale = wax_wt_pct / cur
            z_wax = np.minimum(z_wax * scale, z)
    if props == "won":
        Tm = won_Tf(M); dHm = won_dHf(M, Tm)
    elif props == "lira":
        Tm = lira_Tf(M); dHm = lira_dHf(M, Tm)
    else:
        raise ValueError("pedersen_wat uses M-based properties: 'won' or 'lira'")
    p = Props(Tm=Tm, dHm=dHm, Ttr=np.full_like(Tm, np.nan), dHtr=np.zeros_like(Tm), M=M)
    wat = wat_ideal_solid_solution(None, z_wax, p=p, use_dcp=use_dcp)
    if return_details:
        return wat, dict(n=n, M=M, z=z, rho=rho, wax_frac=fr, z_wax=z_wax, B=B, k=k, scale=scale, props=p)
    return wat


def build_nparaffin_distribution(wax_wt_pct: float, mean_cn: float, spread: float,
                                 M_oil: float, n_min: int = 15, n_max: int = 90,
                                 shape: str = "gamma", cutoff_wt_pct: float = 0.01):
    """(c) Build an n-paraffin carbon-number distribution from three numbers.

    wax_wt_pct : total mass % of n-paraffins with n >= n_min in the oil.
                 ASSUMPTION: equated to the measured wax content. In reality
                 UOP 46 / acetone-precipitation wax contains iso- and cyclo-
                 paraffins and occluded oil, and HTGC n-paraffin C20+ is often
                 smaller (Robustillo et al. 2012: precipitation 2-10x DSC/HTGC).
                 Pass wax_wt_pct * f_n (f_n your n-paraffin share) if you want.
    mean_cn    : mass-weighted mean carbon number of that n-paraffin block.
    spread     : mass-weighted standard deviation of carbon number.
    M_oil      : number-average molar mass of the whole oil, g/mol, to turn mass
                 fractions into whole-oil mole fractions (x_i = w_i M_oil / M_i).
    shape      : "gamma"  ASSUMPTION: discretised gamma in (n - n_min + 0.5)
                          with the requested mean and spread; gives a rising
                          limb and an exponential-like tail, as seen in GC
                          (e.g. Kurniawan 2013: ratio 1.03 rising to C26, 0.80 after).
                 "exponential" SOURCE form: w_{n+1}/w_n = alpha constant for
                          n >= n_min (Coutinho & Daridon; Ameri Mahabadian
                          default alpha = 0.88). alpha set from mean_cn:
                          mean = n_min + alpha/(1-alpha); spread is ignored.
                 "normal" ASSUMPTION: Gaussian in n (light tail).
    cutoff_wt_pct : drop carbon numbers whose share falls below this (wt% of
                 oil) and renormalise. SOURCE for the default 0.01 wt%:
                 Kurniawan et al. 2013 stopped GC extrapolation when wt% < 0.01
                 (Coutinho 2001 BJChE kept paraffins above 0.05 wt%).
                 WAT is very sensitive to it because the first crystals come
                 from the heaviest traces: for the Java crude test, cutoff
                 1e-4 instead of 0.01 wt% raises bracket WAT by about 6 C.
    Returns n (array), mass fraction w_n (of whole oil), mole fraction x_n.
    """
    n = np.arange(n_min, n_max + 1, dtype=float)
    if shape == "gamma":
        mu = mean_cn - n_min + 0.5
        if mu <= 0 or spread <= 0:
            raise ValueError("mean_cn must exceed n_min and spread > 0")
        kshape = (mu / spread) ** 2
        theta = spread**2 / mu
        u = n - n_min + 0.5
        logw = (kshape - 1.0) * np.log(u) - u / theta
        w = np.exp(logw - logw.max())
    elif shape == "normal":
        w = np.exp(-0.5 * ((n - mean_cn) / spread) ** 2)
    elif shape == "exponential":
        a = (mean_cn - n_min) / (1.0 + (mean_cn - n_min))
        w = a ** (n - n_min)
    else:
        raise ValueError(shape)
    w = w / w.sum() * wax_wt_pct / 100.0
    keep = w * 100.0 >= cutoff_wt_pct
    n, w = n[keep], w[keep]
    w = w / w.sum() * wax_wt_pct / 100.0
    x = wt_to_mole(w, mw_nalkane(n), M_oil)
    return n, w, x


BRACKET_F = 0.47  # ASSUMPTION: median of f over 10 systems in test_thermo.py T8 (in-sample MAE 0.8 K)


def wat_bracket(n, z, f: float = BRACKET_F, props="coutinho", use_dcp=False):
    """ASSUMPTION (empirical, fitted here, not from a paper): the pure-solid
    multisolid model (ideal liquid) under-predicts measured WAT and the ideal
    solid solution over-predicts it (see test_thermo.py T3-T5), because real
    n-alkane waxes form non-ideal solid solutions (Coutinho's P-UNIQUAC sits in
    between). WAT_bracket = WAT_ms + f (WAT_ss - WAT_ms). f fitted in test T8.
    Returns (WAT_bracket, WAT_ms, WAT_ss) in K."""
    ms = wat_multisolid(n, z, props, use_dcp)
    ss = wat_ideal_solid_solution(n, z, props, use_dcp)
    return ms + f * (ss - ms), ms, ss


def wat_from_bulk(wax_wt_pct, mean_cn, spread, M_oil, model="multisolid", props="coutinho",
                  use_dcp=False, **kw):
    """Convenience: (c) then (a), the ideal solid solution, or the bracket.
    model in {"multisolid", "ideal_ss", "bracket"}. Returns WAT in K."""
    n, w, x = build_nparaffin_distribution(wax_wt_pct, mean_cn, spread, M_oil, **kw)
    if model == "multisolid":
        return wat_multisolid(n, x, props, use_dcp)
    if model == "ideal_ss":
        return wat_ideal_solid_solution(n, x, props, use_dcp)
    if model == "bracket":
        return wat_bracket(n, x, props=props, use_dcp=use_dcp)[0]
    raise ValueError(model)


if __name__ == "__main__":
    for nn in (20, 28, 36, 50):
        pp = nalkane_props([nn])
        print(nn, round(float(pp.Tm[0]), 2), round(float(pp.dHm[0])), pp.Ttr[0], round(float(pp.dHtr[0])))
    print("WAT 10 wt% wax, mean C26, sd 5, M=220:",
          round(wat_from_bulk(10, 26, 5, 220) - 273.15, 1), "C (multisolid)",
          round(wat_from_bulk(10, 26, 5, 220, model="ideal_ss") - 273.15, 1), "C (ideal SS)")
