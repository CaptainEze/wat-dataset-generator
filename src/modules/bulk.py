"""
bulk_relations.py

Bulk crude oil property relations for the WAT synthetic-data generator.
Each function names its source. Run this file directly to execute the tests
against published worked examples:  python3 -I bulk_relations.py

Units are stated in every docstring. Temperatures: C unless the name says _F,
_R or _K. Kinematic viscosity: cSt (mm2/s). Dynamic viscosity: cP (mPa s).
Density: kg/m3. API gravity at 60 F.

Sources (details in models.jsonl):
  API MPMS Ch. 11.1 (2004) / ASTM D1250-04, crude oil group (K0=341.0957,K1=0,K2=0),
      equations as implemented in github.com/m2b/API11_1VCF, test values from
      the standard's Section 11.1.6.1 Examples 1 and 2.
  API 2540 / ASTM D1250-80 Table 53A/54A (15 C base, crude): K0=613.9723, K1=0.
  ASTM D341 / API TDB procedure 11A4.4 (Walther with low-viscosity terms),
      as implemented in pychemqt lib/petro.py viscoAPI(), test = Example B.
  API TDB 11A4.2 (v100, v210 from Tb and Watson K), test = Examples A and C.
  API TDB 2B8.1 pour point of petroleum fractions, test = pychemqt doc example.
  Riazi and Daubert (1980) M from Tb and SG, test = Ahmed Example 2.2.
  Dead-oil viscosity correlations (cP, T in F): Beal/Standing, Beggs and
      Robinson 1975, Glaso 1980, Ng and Egbogah 1983, Kartoatmodjo and Schmidt
      1994, Petrosky and Farshad 1995, De Ghetto et al. 1995, Naseri et al. 2005,
      Labedi 1992 (low confidence).
"""
import math
import numpy as np

# ---------------------------------------------------------------------------
# 1. Gravity and density
# ---------------------------------------------------------------------------
RHO_W60 = 999.016  # kg/m3, density of water at 60 F used by API MPMS 11.1-2004


def api_to_sg(api):
    """API gravity -> specific gravity 60F/60F.  SG = 141.5/(API+131.5)."""
    return 141.5 / (np.asarray(api, dtype=float) + 131.5)


def sg_to_api(sg):
    """Specific gravity 60F/60F -> API.  API = 141.5/SG - 131.5."""
    return 141.5 / np.asarray(sg, dtype=float) - 131.5


def api_to_rho60(api):
    """API -> density at 60 F in kg/m3 (API MPMS 11.1-2004, rho_w60 = 999.016)."""
    return api_to_sg(api) * RHO_W60


def rho60_to_api(rho60):
    return sg_to_api(np.asarray(rho60, dtype=float) / RHO_W60)


# --- API MPMS 11.1 (2004), crude oil commodity group -----------------------
_K_CRUDE_2004 = (341.0957, 0.0, 0.0)
_DELTA60 = 0.01374979547          # F, ITS-90 shift at 60 F
_BASE_T60_IPTS68 = 60.0068749     # F
_ITS90_A = (-0.148759, -0.267408, 1.080760, 1.269056, -4.089591,
            -1.871251, 7.438081, -3.536296)


def _its90_to_ipts68_C(tC):
    tau = tC / 630.0
    d = _ITS90_A[-1]
    for a in _ITS90_A[-2::-1]:
        d = a + d * tau
    d = d * tau
    return tC - d


def ctl_api2004(api60, t_F, k=_K_CRUDE_2004):
    """Correction for temperature on liquid, CTL = V_T / V_60, crude oil group,
    API MPMS 11.1-2004 (ASTM D1250-04). Input API at 60 F, observed T in F.
    Returns (CTL, alpha60 [1/F]). Density at T = rho60 * CTL."""
    k0, k1, k2 = k
    rho60 = api_to_rho60(api60)
    # Step 3: shift 60 F density to the IPTS-68 basis
    A = (_DELTA60 / 2.0) * ((k0 / rho60 + k1) / rho60 + k2)
    B = (2 * k0 + k1 * rho60) / (k0 + (k1 + k2 * rho60) * rho60)
    rho68 = rho60 * (1 + (math.exp(A * (1 + 0.8 * A)) - 1) / (1 + A * (1 + 1.6 * A) * B))
    # Step 4: alpha60
    alpha60 = k0 / rho68 ** 2 + k1 / rho68 + k2
    # Step 2: temperature to IPTS-68
    tC = (t_F - 32.0) / 1.8
    t68_F = _its90_to_ipts68_C(tC) * 1.8 + 32.0
    dT = t68_F - _BASE_T60_IPTS68
    ctl = math.exp(-alpha60 * dT * (1 + 0.8 * alpha60 * (dT + _DELTA60)))
    return ctl, alpha60


def rho_at_T_from_api(api60, t_C):
    """Density (kg/m3) at t_C of a crude with given API (60 F), API MPMS 11.1-2004."""
    ctl, _ = ctl_api2004(api60, t_C * 1.8 + 32.0)
    return api_to_rho60(api60) * ctl


def api_from_rho_at_T(rho_obs, t_C, tol=1e-9):
    """Invert API MPMS 11.1-2004 for crude oil: observed density (kg/m3) at t_C
    -> API at 60 F (fixed-point iteration, converges in < 10 steps)."""
    rho60 = float(rho_obs)
    for _ in range(100):
        ctl, _a = ctl_api2004(rho60_to_api(rho60), t_C * 1.8 + 32.0)
        new = rho_obs / ctl
        if abs(new - rho60) < tol:
            rho60 = new
            break
        rho60 = new
    return float(rho60_to_api(rho60))


def rho15_from_api(api60):
    """Density at 15 C (kg/m3) from API (60 F), via API MPMS 11.1-2004."""
    return float(rho_at_T_from_api(api60, 15.0))


def api_from_rho15(rho15):
    return api_from_rho_at_T(rho15, 15.0)


# --- ASTM D1250-80 / API 2540 Table 54A style, 15 C base, crude oils ---------
K0_CRUDE_1980_15C = 613.9723
K1_CRUDE_1980_15C = 0.0


def vcf_1980_15C(rho15, t_C):
    """VCF = V_T/V_15 for crude oil, 1980 tables, base 15 C.
    alpha15 = K0/rho15^2 + K1/rho15 (1/C); VCF = exp(-a dT (1 + 0.8 a dT))."""
    a15 = K0_CRUDE_1980_15C / rho15 ** 2 + K1_CRUDE_1980_15C / rho15
    dT = t_C - 15.0
    return math.exp(-a15 * dT * (1 + 0.8 * a15 * dT))


def rho_T_from_rho15_1980(rho15, t_C):
    return rho15 * vcf_1980_15C(rho15, t_C)


def rho15_from_rho_T_1980(rho_T, t_C, tol=1e-9):
    """Table 53A style inversion: density observed at t_C -> density at 15 C."""
    r = float(rho_T)
    for _ in range(100):
        new = rho_T / vcf_1980_15C(r, t_C)
        if abs(new - r) < tol:
            return new
        r = new
    return r


# ---------------------------------------------------------------------------
# 2. Viscosity-temperature: ASTM D341 / Walther
# ---------------------------------------------------------------------------
def _d341_Z(v, low_visc_terms=True):
    v = float(v)
    if low_visc_terms:
        return v + 0.7 + math.exp(-1.47 - 1.84 * v - 0.51 * v * v)
    return v + 0.7


def _d341_v(Z, low_visc_terms=True):
    if low_visc_terms:
        z = Z - 0.7
        return z - math.exp(-0.7487 - 3.295 * z + 0.6119 * z * z - 0.3191 * z ** 3)
    return Z - 0.7


def walther_fit(v1, T1_C, v2, T2_C, low_visc_terms=True):
    """Fit log10(log10(Z)) = A - B*log10(T_K) through two (T, v) points.
    v in cSt. Returns (A, B). With low_visc_terms=False, Z = v + 0.7 (classic
    Walther / ASTM D341 pre-2009); True adds the D341-09 low-viscosity terms
    (valid down to 0.21 cSt)."""
    T1, T2 = T1_C + 273.15, T2_C + 273.15
    y1 = math.log10(math.log10(_d341_Z(v1, low_visc_terms)))
    y2 = math.log10(math.log10(_d341_Z(v2, low_visc_terms)))
    B = (y1 - y2) / (math.log10(T2) - math.log10(T1))
    A = y1 + B * math.log10(T1)
    return A, B


def walther_visc(A, B, T_C, low_visc_terms=True):
    """Kinematic viscosity (cSt) at T_C from Walther constants A, B (T in K)."""
    Z = 10 ** (10 ** (A - B * math.log10(T_C + 273.15)))
    return _d341_v(Z, low_visc_terms)


def visc_at_T(v1, T1_C, v2, T2_C, T_C, low_visc_terms=True):
    """Interpolate / extrapolate kinematic viscosity to T_C from two points."""
    A, B = walther_fit(v1, T1_C, v2, T2_C, low_visc_terms)
    return walther_visc(A, B, T_C, low_visc_terms)


def dyn_to_kin(mu_cP, rho_kgm3):
    """cP -> cSt: nu = mu / (rho/1000)."""
    return mu_cP / (rho_kgm3 / 1000.0)


def kin_to_dyn(nu_cSt, rho_kgm3):
    return nu_cSt * (rho_kgm3 / 1000.0)


# ---------------------------------------------------------------------------
# 3. Dead-oil viscosity correlations. All return DYNAMIC viscosity in cP,
#    T in deg F, API at 60 F, for gas-free oil at atmospheric pressure.
# ---------------------------------------------------------------------------
def mu_od_beal(api, T_F):
    """Beal (1946) chart as fitted by Standing (1981). cP."""
    a = 10 ** (0.43 + 8.33 / api)
    return (0.32 + 1.8e7 / api ** 4.53) * (360.0 / (T_F + 200.0)) ** a


def mu_od_beggs_robinson(api, T_F):
    """Beggs and Robinson (1975). z = 3.0324 - 0.02023 API; y = 10^z;
    x = y T^-1.163; mu = 10^x - 1. cP. 16-58 API, 70-295 F."""
    z = 3.0324 - 0.02023 * api
    x = 10 ** z * T_F ** -1.163
    return 10 ** x - 1


def mu_od_glaso(api, T_F):
    """Glaso (1980). mu = 3.141e10 T^-3.444 (log API)^(10.313 log T - 36.447). cP."""
    return 3.141e10 * T_F ** -3.444 * math.log10(api) ** (10.313 * math.log10(T_F) - 36.447)


def mu_od_ng_egbogah(api, T_F):
    """Ng and Egbogah (1983) / Egbogah and Ng (1990), version without pour point:
    log10 log10(mu+1) = 1.8653 - 0.025086 API - 0.5644 log10 T. cP."""
    return 10 ** (10 ** (1.8653 - 0.025086 * api - 0.5644 * math.log10(T_F))) - 1


def mu_od_kartoatmodjo_schmidt(api, T_F):
    """Kartoatmodjo and Schmidt (1994). mu = 16e8 T^-2.8177 (log API)^(5.7526 log T - 26.9718). cP."""
    return 16e8 * T_F ** -2.8177 * math.log10(api) ** (5.7526 * math.log10(T_F) - 26.9718)


def mu_od_petrosky_farshad(api, T_F):
    """Petrosky and Farshad (1995). mu = 2.3511e7 T^-2.10255 (log API)^(4.59388 log T - 22.82792). cP."""
    return 2.3511e7 * T_F ** -2.10255 * math.log10(api) ** (4.59388 * math.log10(T_F) - 22.82792)


def mu_od_de_ghetto(api, T_F):
    """De Ghetto, Paone and Villa (1995), modified Egbogah-Jack. cP.
    API <= 10 (extra heavy): log log(mu+1) = 1.90296 - 0.012619 API - 0.61748 log T
    10 < API <= 22.3 (heavy): log log(mu+1) = 2.06492 - 0.0179 API - 0.70226 log T"""
    if api <= 10:
        a = 1.90296 - 0.012619 * api - 0.61748 * math.log10(T_F)
    else:
        a = 2.06492 - 0.0179 * api - 0.70226 * math.log10(T_F)
    return 10 ** (10 ** a) - 1


def mu_od_naseri(api, T_F):
    """Naseri, Nikazar and Mousavi Dehghani (2005), Iranian oils.
    log10 mu = 11.2699 - 4.2699 log10 API - 2.052 log10 T. cP."""
    return 10 ** (11.2699 - 4.2699 * math.log10(api) - 2.052 * math.log10(T_F))


def mu_od_labedi(api, T_F):
    """Labedi (1992) light Libyan crudes, as rendered (signs unconfirmed):
    mu = 10^9.224 / (API^4.7013 T^0.6739). cP. LOW CONFIDENCE."""
    return 10 ** 9.224 / (api ** 4.7013 * T_F ** 0.6739)


# ---------------------------------------------------------------------------
# 4. Petroleum-fraction characterisation (API Technical Data Book, Riazi)
#    NOTE: developed for narrow fractions, not whole crudes. Use only as soft
#    consistency checks for whole crude oils.
# ---------------------------------------------------------------------------
def C_to_R(tC):
    return (tC + 273.15) * 1.8


def R_to_C(tR):
    return tR / 1.8 - 273.15


def watson_k(Tb_R, sg):
    """Watson (UOP) characterisation factor Kw = Tb^(1/3)/SG, Tb = MeABP in R."""
    return Tb_R ** (1.0 / 3.0) / sg


def v100_v210_api_tdb(Tb_R, Kw):
    """API TDB procedure 11A4.2: kinematic viscosity (cSt) at 100 F and 210 F
    from mean average boiling point (R) and Watson K."""
    mu_ref = 10 ** (-1.35579 + 8.16059e-4 * Tb_R + 8.38505e-7 * Tb_R ** 2)
    A1 = 34.931 - 8.84387e-2 * Tb_R + 6.73513e-5 * Tb_R ** 2 - 1.01394e-8 * Tb_R ** 3
    A2 = -2.92649 + 6.98405e-3 * Tb_R - 5.09947e-6 * Tb_R ** 2 + 7.49378e-10 * Tb_R ** 3
    v100 = mu_ref + 10 ** (A1 + A2 * Kw)
    v210 = 10 ** (-1.92353 + 2.41071e-4 * Tb_R + 0.5113 * math.log10(Tb_R * v100))
    return v100, v210


def tb_kw_from_api_v100(api, v100, lo=500.0, hi=2000.0):
    """Invert API TDB 11A4.2 with Kw = Tb^(1/3)/SG: given API and v100 (cSt),
    solve for MeABP Tb (R) by bisection. Returns (Tb_R, Kw). Soft estimate."""
    sg = float(api_to_sg(api))
    f = lambda T: v100_v210_api_tdb(T, watson_k(T, sg))[0] - v100
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return float('nan'), float('nan')
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    Tb = 0.5 * (lo + hi)
    return Tb, watson_k(Tb, sg)


def pour_point_api_tdb(sg, Tb_R, v100=None):
    """API TDB procedure 2B8.1 pour point of petroleum fractions (R).
    With v100 (cSt): PP = 753 + 136(1 - exp(-0.15 v100)) - 572 SG + 0.0512 v100 + 0.139 Tb
    Without:         PP = 3.85e-8 Tb^5.49 10^-(0.712 Tb^0.315 + 0.133 SG) + 1.4
    Ranges: 0.8<=SG<=1, 800<=Tb<=1500 R, 2<=v100<=960 cSt."""
    if v100 is not None:
        return 753 + 136 * (1 - math.exp(-0.15 * v100)) - 572 * sg + 0.0512 * v100 + 0.139 * Tb_R
    return 3.85e-8 * Tb_R ** 5.49 * 10 ** -(0.712 * Tb_R ** 0.315 + 0.133 * sg) + 1.4


def mw_riazi_daubert_1980(Tb_R, sg):
    """Riazi and Daubert (1980): M = 4.5673e-5 Tb^2.1962 SG^-1.0164, Tb in R."""
    return 4.5673e-5 * Tb_R ** 2.1962 * sg ** -1.0164


def mw_riazi_daubert_1987_v100_sg(v100, sg):
    """Riazi and Daubert (1987) generalised form, M from kinematic viscosity at
    100 F (cSt) and SG: M = a v^e SG^f exp(b v + c SG + d v SG), coefficients
    as tabulated in pychemqt (Table VII). Intended for heavy fractions,
    roughly M 200-800. Medium confidence."""
    a, b, c, d, e, f = 1.51723e6, -0.195411, -9.63897, 0.16247, 0.56370, 6.89383
    return a * v100 ** e * sg ** f * math.exp(b * v100 + c * sg + d * v100 * sg)


def hirschler_H(v_cSt):
    """Hirschler (1946) viscosity function used by ASTM D2502 Table 1:
    H = 870 log10(log10(v + 0.6)) + 154, v in cSt."""
    return 870.0 * math.log10(math.log10(v_cSt + 0.6)) + 154.0


def mw_hirschler_d2502(v100, v210):
    """Mean relative molecular mass from kinematic viscosity at 100 F and 210 F
    (cSt), Hirschler (1946) equations behind the ASTM D2502 chart:
    MW = 180 + S (H100 + 60), S = 4.146 - 1.733 log10(VSF - 145), VSF = H100 - H210.
    D2502 scope: MW 250 to 700, average petroleum fractions (not whole crudes)."""
    H100, H210 = hirschler_H(v100), hirschler_H(v210)
    S = 4.146 - 1.733 * math.log10(H100 - H210 - 145.0)
    return 180.0 + S * (H100 + 60.0)


# ---------------------------------------------------------------------------
# Tests against published worked examples
# ---------------------------------------------------------------------------
def _close(a, b, rtol=None, atol=None):
    if atol is not None:
        return abs(a - b) <= atol
    return abs(a - b) <= rtol * abs(b)


def run_tests(verbose=True):
    res = []

    def chk(name, got, want, **kw):
        ok = _close(got, want, **kw)
        res.append((name, ok, got, want))
        if verbose:
            print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got:.10g}  published {want:.10g}")

    # API MPMS 11.1-2004 Section 11.1.6.1 Example 1: crude, 17.785 API, -27.7 F
    ctl, a60 = ctl_api2004(17.785, -27.7)
    chk("API11.1-2004 Ex1 alpha60", a60, 0.000380407044, rtol=1e-8)
    chk("API11.1-2004 Ex1 CTL", ctl, 1.033011591958, rtol=1e-9)
    # Example 2: crude group coefficients, -10 API, 301.93 F (CTL only)
    ctl2, a602 = ctl_api2004(-10.0, 301.93)
    chk("API11.1-2004 Ex2 alpha60", a602, 0.000251982006, rtol=1e-8)
    chk("API11.1-2004 Ex2 CTL", ctl2, 0.938051116886, rtol=1e-9)
    # Round trip density inversion
    r20 = rho_at_T_from_api(30.0, 20.0)
    chk("API11.1 inversion round trip (API 30 via rho20)", api_from_rho_at_T(r20, 20.0), 30.0, atol=1e-6)
    # 1980 vs 2004 consistency: rho15 -> rho20 for 850 kg/m3 (should agree within 0.1 kg/m3)
    api850 = api_from_rho15(850.0)
    chk("1980 Table54A vs 2004: rho20 of rho15=850", rho_T_from_rho15_1980(850.0, 20.0),
        rho_at_T_from_api(api850, 20.0), atol=0.1)

    # API TDB 11A4.4 Example B (ASTM D341 with low-viscosity terms):
    # 1.644 cSt at 32 F and 0.925 cSt at 104 F -> 1.201 cSt at 68 F
    v68 = visc_at_T(1.644, 0.0, 0.925, 40.0, 20.0)
    chk("API TDB 11A4.4 Ex B Walther v(68F)", v68, 1.201, atol=0.0006)
    # API TDB 11A4.2 Example A: Tb = 598.7 F, Kw = 11.87 -> v100 5.94, v210 1.88, v(140F) 3.57
    TbA = 598.7 + 459.67
    v100, v210 = v100_v210_api_tdb(TbA, 11.87)
    chk("API TDB 11A4.2 Ex A v100", v100, 5.94, atol=0.006)
    chk("API TDB 11A4.2 Ex A v210", v210, 1.88, atol=0.006)
    chk("API TDB 11A4.2 Ex A v140F (via D341)", visc_at_T(v100, 37.7778, v210, 98.8889, 60.0), 3.57, atol=0.006)
    # Example C: Tb = 382.1 F, Kw = 11.93 -> v100 1.249
    chk("API TDB 11A4.2 Ex C v100", v100_v210_api_tdb(382.1 + 459.67, 11.93)[0], 1.249, atol=0.0006)

    # API TDB 2B8.1 pour point example (pychemqt doc): SG 0.839, Tb 972 R, v100 3 cSt -> 458 R
    chk("API TDB 2B8.1 pour point", pour_point_api_tdb(0.839, 972.0, 3.0), 458.0, atol=0.5)
    # Riazi-Daubert 1980, Ahmed Example 2.2: Tb = 198 F, SG = 0.7365 -> M = 96
    chk("Riazi-Daubert 1980 M (Ahmed Ex 2.2)", mw_riazi_daubert_1980(198 + 459.67, 0.7365), 96.0, atol=0.5)

    # ASTM D2502 Section 5.3 worked example: v100 = 179 cSt, v210 = 9.72 cSt -> H = 461, MW = 360
    chk("ASTM D2502 Ex H(179 cSt)", hirschler_H(179.0), 461.0, atol=0.5)
    chk("ASTM D2502 Ex MW (Hirschler eqs vs chart, reproducibility 25)", mw_hirschler_d2502(179.0, 9.72), 360.0, atol=5.0)

    # Dead oil: Beggs-Robinson identity check with exp form x = T^-1.163 exp(6.9824 - 0.04658 API)
    chk("Beggs-Robinson log10 vs exp form (API 30, 150 F)", mu_od_beggs_robinson(30, 150),
        10 ** (150 ** -1.163 * math.exp(6.9824 - 0.04658 * 30)) - 1, rtol=2e-4)
    n_fail = sum(1 for r in res if not r[1])
    if verbose:
        print(f"{len(res) - n_fail}/{len(res)} tests passed")
    return n_fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
