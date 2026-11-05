"""Tests for thermo_wat.py. Run:  python3 -I test_thermo.py  (from this folder)
Prints a comparison table for each published example and asserts loose bounds.
All 'published' numbers are typed from the sources named next to them."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import math
import numpy as np
import thermo_wat as tw

K0 = 273.15
results = []

def rep(name, calc, ref, note=""):
    results.append((name, calc, ref, note))
    print(f"{name:58s} calc={calc:8.2f}  ref={ref if isinstance(ref,str) else f'{ref:8.2f}'}  {note}")

print("== T1 pure n-alkane melting points: Coutinho 2006 eq 2 vs Broadhurst 1962 Table 2 (K) ==")
broad = {10: 243.5, 12: 263.6, 14: 279.0, 16: 291.3, 18: 301.3, 20: 309.8}
for n_, Tm in broad.items():
    c = float(tw.coutinho_Tm(n_))
    rep(f"Tm n-C{n_} Coutinho", c, Tm)
    assert abs(c - Tm) < 10.0  # smooth fit; even C10-C20 real values sit above it
# Broadhurst eq for n>=44 vs Zhou 2026 Table 4 cooling-DSC precipitation T (C)
for n_, Tc in {44: 86.00, 48: 90.50, 50: 92.20}.items():
    rep(f"Tm n-C{n_} Broadhurst eq (C) vs Zhou cooling DSC", float(tw.broadhurst_Tm(n_)) - K0, Tc, "cooling peak is a little below melting")
    rep(f"Tm n-C{n_} Coutinho eq (C) vs Zhou cooling DSC", float(tw.coutinho_Tm(n_)) - K0, Tc)

print("\n== T2 binary solubility, Zhou et al. 2026 Processes 14:1207 Tables 1,4,5 ==")
# (i) reproduce the paper's ideal-solution calc with its own Table 4 parameters
# nC38: Tw = 79.00 C, Hw = 96633 J/mol, Ttr = 76.00 C, Htr = 7768 J/mol (two-term eq 2)
def x_ideal_two_term(T, Tw, Hw, Ttr, Htr):
    lnx = -(Hw / tw.R) * (1 / T - 1 / Tw)
    if T < Ttr:
        lnx += -(Htr / tw.R) * (1 / T - 1 / Ttr)
    return math.exp(lnx)
for (T_c, x_meas, x_calc_pub) in [(40.22, 1.26, 1.17), (46.04, 2.62, 2.43), (53.09, 5.69, 5.68)]:
    xc = 100 * x_ideal_two_term(T_c + K0, 79.00 + K0, 96633, 76.00 + K0, 7768)
    rep(f"nC38/heptane x(mol%) at {T_c} C, paper params", xc, x_calc_pub, f"(measured {x_meas})")
# nC50 single term with total enthalpy 142287 J/mol and Tw = 92.20 C
for (T_c, x_meas, x_calc_pub) in [(57.52, 0.73, 0.73), (64.06, 1.99, 2.00), (68.16, 3.41, 3.68)]:
    xc = 100 * math.exp(-(142287 / tw.R) * (1 / (T_c + K0) - 1 / (92.20 + K0)))
    rep(f"nC50/heptane x(mol%) at {T_c} C, paper params", xc, x_calc_pub, f"(measured {x_meas})")
# (ii) predict the saturation temperature with the module's Coutinho properties
for n_, x, Tmeas in [(38, 0.0126, 40.22), (38, 0.0569, 53.09), (50, 0.0073, 57.52), (50, 0.0341, 68.16)]:
    T = tw.wat_multisolid([n_], [x]) - K0
    rep(f"nC{n_}/heptane x={x}: saturation T (C), Coutinho props", T, Tmeas)
    assert abs(T - Tmeas) < 10  # ideal liquid + Coutinho total enthalpy over-predicts; see notes

print("\n== T3 Dauphin et al. 1999 synthetic waxes in n-C10 (compositions from Bhangale 2007 Tables 6.1-6.3) ==")
nA = list(range(18, 37))
sysA = [0.029981,0.025723,0.022065,0.018946,0.016246,0.013939,0.01196,0.01026,0.008812,0.007555,0.006513,0.005561,0.004769,0.004101,0.00351,0.003024,0.002589,0.001889,0.001904]
sysB = [0.033915,0.029102,0.024961,0.021427,0.018372,0.015766,0.013528,0.011604,0,0,0,0.006288,0.005405,0.004631,0.003972,0.003411,0.002922,0.002508,0.002153]
sysC = [0.037241,0.031958,0.027418,0.023527,0.020185,0.017317,0.014858,0,0,0,0,0,0.00593,0.005086,0.00437,0.003745,0.003209,0.002754,0.002368]
meas = {"A": 308.75, "B": 309.65, "C": 310.37}
pub_ped = {"A": 314.6, "B": 315.2, "C": 315.6}      # Bhangale 2007, Pedersen model (PR EOS liquid, ideal SS, Won props)
pub_won = {"A": 308.9, "B": 310.42, "C": 311.2}     # Bhangale 2007 Table 6.4, Won model
for key, z in (("A", sysA), ("B", sysB), ("C", sysC)):
    z = np.array(z)
    ms = tw.wat_multisolid(nA, z)
    ss_c = tw.wat_ideal_solid_solution(nA, z, props="coutinho")
    # Pedersen-type: ideal SS with Won Tf/dHf on n-alkane M and Pedersen dCp
    ss_w = tw.wat_ideal_solid_solution(nA, z, props="won", use_dcp=True)
    ss_w0 = tw.wat_ideal_solid_solution(nA, z, props="won", use_dcp=False)
    rep(f"Sys {key} multisolid, Coutinho props", ms, meas[key], "measured")
    rep(f"Sys {key} ideal SS, Coutinho props", ss_c, meas[key], "measured")
    rep(f"Sys {key} ideal SS, Won props + Pedersen dCp", ss_w, pub_ped[key], "Bhangale Pedersen-model result")
    rep(f"Sys {key} ideal SS, Won props, no dCp", ss_w0, pub_ped[key], "Bhangale Pedersen-model result")
    assert 290 < ms < 320 and 290 < ss_c < 330

print("\n== T4 Java 'Crude A', Kurniawan et al. 2013 Sci Contrib Oil Gas 36(2) Table 2 ==")
nJ = list(range(20, 49))
molpct = [0.558,0.549,0.542,0.536,0.531,0.527,0.524,0.406,0.314,0.244,0.190,0.147,0.115,0.089,0.070,0.054,0.043,0.033,0.026,0.020,0.016,0.013,0.010,0.008,0.006,0.005,0.004,0.003,0.002]
wtpct = [1.109,1.146,1.185,1.225,1.266,1.308,1.352,1.087,0.873,0.702,0.564,0.453,0.364,0.293,0.235,0.189,0.152,0.122,0.098,0.079,0.063,0.051,0.041,0.033,0.026,0.021,0.017,0.014,0.011]
xJ = np.array(molpct) / 100
for props in ("coutinho", "won"):
    rep(f"Crude A multisolid, {props} props, paper mol% (C)", tw.wat_multisolid(nJ, xJ, props) - K0, 38.0, "DSC 38 C; Coutinho model 40 C")
    rep(f"Crude A ideal SS, {props} props, paper mol% (C)", tw.wat_ideal_solid_solution(nJ, xJ, props) - K0, 38.0, "DSC 38 C; Coutinho model 40 C")
# mol% column implies M_oil = x*M/w ; check and recompute with stated 162.9 g/mol
impl = np.array(molpct) * tw.mw_nalkane(nJ) / np.array(wtpct)
print(f"   implied oil molar mass from table: {impl.mean():.1f} g/mol (paper states 162.9-163)")
x163 = tw.wt_to_mole(np.array(wtpct) / 100, tw.mw_nalkane(nJ), 162.9)
rep("Crude A multisolid, Coutinho, wt% with M_oil=162.9 (C)", tw.wat_multisolid(nJ, x163) - K0, 38.0)
rep("Crude A ideal SS, Coutinho, wt% with M_oil=162.9 (C)", tw.wat_ideal_solid_solution(nJ, x163) - K0, 38.0)
T = np.arange(250.0, 320.0, 1.0)
S, W = tw.solid_curve_ideal_ss(nJ, x163, T, M_inert=150.0)
print("   ideal SS solid wt% at -20 C:", round(float(np.interp(253.15, T, W)), 2), "(paper: 13.86 wt% at -20 C, total n-paraffin 14.08)")

print("\n== T5 Shariatrad et al. 2022 ACS Omega quaternary C11+C14+C16+C18 WDT (Table 1) ==")
rows = [(0.3114,0.2224,0.4124,0.0538,275.8),(0.0752,0.5791,0.2404,0.1052,276.8),(0.1830,0.2340,0.3401,0.2429,282.4),
        (0.2439,0.2927,0.2195,0.2439,283.1),(0.1250,0.2001,0.2714,0.4035,287.3),(0.0636,0.2920,0.0796,0.5648,293.5)]
nq = [11, 14, 16, 18]; Mq = tw.mw_nalkane(nq)
errs_ms, errs_ss = [], []
for r in rows:
    w = np.array(r[:4]); x = (w / Mq) / np.sum(w / Mq)
    ms = tw.wat_multisolid(nq, x); ss = tw.wat_ideal_solid_solution(nq, x)
    errs_ms.append(ms - r[4]); errs_ss.append(ss - r[4])
    rep(f"quaternary w={r[:4]} multisolid", ms, r[4], f"ideal SS {ss:.1f}")
print(f"   mean error multisolid {np.mean(errs_ms):+.2f} K, ideal SS {np.mean(errs_ss):+.2f} K (paper best model AAD 0.8 K)")

print("\n== T6 Pedersen-style crude from bulk data (b) ==")
for rho, M, wax in [(0.83, 200, 5.0), (0.85, 230, 10.0), (0.87, 260, 15.0)]:
    out = {}
    for abc in ("pedersen1991", "pedersen1995", "ji2004", "neqsim_code"):
        out[abc] = tw.pedersen_wat(rho, M, None, abc=abc) - K0
    tuned = tw.pedersen_wat(rho, M, wax) - K0
    print(f"   rho={rho} M={M}: untuned WAT C {', '.join(f'{k}={v:.1f}' for k,v in out.items())}; tuned to wax {wax}% -> {tuned:.1f} C")
    assert -40 < tuned < 90

print("\n== T7 distribution builder (c) ==")
n, w, x = tw.build_nparaffin_distribution(12.0, 27.0, 5.0, 210.0)
mean = np.sum(n * w) / np.sum(w); sd = math.sqrt(np.sum(w * (n - mean) ** 2) / np.sum(w))
print(f"   sum w = {100*w.sum():.3f} wt%, mean CN = {mean:.2f}, sd = {sd:.2f}, sum x = {x.sum():.4f}")
assert abs(100 * w.sum() - 12.0) < 1e-6 and abs(mean - 27.0) < 0.6 and abs(sd - 5.0) < 0.6
for wax in (2, 5, 10, 20):
    print(f"   wax {wax:2d} wt%, mean C25, sd 5, M 220: WAT multisolid {tw.wat_from_bulk(wax,25,5,220)-K0:5.1f} C, ideal SS {tw.wat_from_bulk(wax,25,5,220,model='ideal_ss')-K0:5.1f} C")
for mc in (22, 26, 30, 34):
    print(f"   wax 10 wt%, mean C{mc}, sd 5, M 220: WAT multisolid {tw.wat_from_bulk(10,mc,5,220)-K0:5.1f} C, ideal SS {tw.wat_from_bulk(10,mc,5,220,model='ideal_ss')-K0:5.1f} C")

print("\n== T8 bracket factor f = (WAT_meas - WAT_ms)/(WAT_ss - WAT_ms), Coutinho props ==")
cases = [("Dauphin A", nA, np.array(sysA), meas["A"]), ("Dauphin B", nA, np.array(sysB), meas["B"]),
         ("Dauphin C", nA, np.array(sysC), meas["C"]), ("Java crude A (M 162.9)", nJ, x163, 38.0 + K0)]
for r in rows:
    w_ = np.array(r[:4]); cases.append((f"quaternary WDT {r[4]}", nq, (w_ / Mq) / np.sum(w_ / Mq), r[4]))
fs = []
for name, nn, zz, Tm_ in cases:
    _, ms, ss = tw.wat_bracket(nn, zz)
    f = (Tm_ - ms) / (ss - ms); fs.append(f)
    print(f"   {name:28s} ms={ms:7.2f} ss={ss:7.2f} meas={Tm_:7.2f} f={f:5.2f}")
fs = np.array(fs)
print(f"   f mean {fs.mean():.2f}, sd {fs.std(ddof=1):.2f}, n={len(fs)}; module default BRACKET_F={tw.BRACKET_F}")
errs = []
for name, nn, zz, Tm_ in cases:
    errs.append(tw.wat_bracket(nn, zz)[0] - Tm_)
print(f"   bracket model error with default f: mean {np.mean(errs):+.2f} K, MAE {np.mean(np.abs(errs)):.2f} K, max {np.max(np.abs(errs)):.2f} K (in-sample)")
print("\n== T9 round trip for builder (c): Java Crude A summarised as wax 14.08 wt%, mean C26.16, sd 4.84 (from its own GC table), n_min 20 ==")
for shape in ("gamma", "normal", "exponential"):
    n9, w9, x9 = tw.build_nparaffin_distribution(14.08, 26.16, 4.84, 162.9, n_min=20, shape=shape)
    b, ms, ss = tw.wat_bracket(n9, x9)
    print(f"   {shape:11s}: multisolid {ms-K0:5.1f} C, ideal SS {ss-K0:5.1f} C, bracket {b-K0:5.1f} C (measured DSC 38.0 C; from full GC table bracket {tw.wat_bracket(nJ, x163)[0]-K0:.1f} C)")
for cut in (1e-4, 1e-3, 1e-2, 5e-2):
    n9, w9, x9 = tw.build_nparaffin_distribution(14.08, 26.16, 4.84, 162.9, n_min=20, cutoff_wt_pct=cut)
    print(f"   gamma, tail cutoff {cut:g} wt%: n_max {int(n9.max())}, bracket WAT {tw.wat_bracket(n9, x9)[0]-K0:5.1f} C")
print("\nALL TESTS PASSED")
