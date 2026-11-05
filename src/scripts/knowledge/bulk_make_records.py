"""Write models.jsonl, facts.jsonl and log.csv for the bulk agent, checking that
every python field runs and reproduces its stated check value.
python3 -I make_records.py"""
import csv, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bulk_relations as br

PETPROPY = 'https://github.com/EverJRamosI/petpropy (petpropy/oil/oil_viscosity.py)'
PVTCPP = 'https://github.com/zentechnologygroup/pvt-cpp (include/correlations/dead-oil-viscosity-impl.H)'
PYCHEMQT = 'https://github.com/jjgomera/pychemqt (lib/petro.py)'
API11 = 'https://github.com/m2b/API11_1VCF (API11_1VCF.Lib, Test/CTPLFromAPIDegFPsigTests.cs)'
INTECH = 'https://intechopen.com/chapters/40684'
ENFOQUE = 'https://www.redalyc.org/journal/5722/572261628002/572261628002.pdf'
VURUP = 'https://www.vurup.sk/na_stiahnutie/new-viscosity-correlations-dead-crude-oils/'
ALOMAIR = 'https://link.springer.com/content/pdf/10.1007/s13202-015-0184-8.pdf'

API_IN = {"name": "API gravity at 60 F", "unit": "deg API", "symbol": "API"}
TF_IN = {"name": "temperature", "unit": "F", "symbol": "T"}


def deadoil(id_, name, eq, py, coef, valid, fitted, acc, cit, doi, where, conf, notes, extra_urls, check):
    return dict(id=id_, name=name, target="viscosity", inputs=[API_IN, TF_IN], equation_text=eq, python=py,
                coefficients=coef, output_unit="cP (dynamic viscosity of gas-free oil at 1 atm)", validity=valid,
                fitted_on=fitted, reported_accuracy=acc, citation=cit, doi=doi, url=extra_urls,
                access="secondary_citation", where=where, confidence=conf, notes=notes, _check=check)


M = []
M.append(dict(id="api_from_sg", name="API gravity definition", target="density",
              inputs=[{"name": "specific gravity 60F/60F", "unit": "-", "symbol": "SG"}],
              equation_text="API = 141.5/SG - 131.5 ; SG = 141.5/(API + 131.5)", python="141.5/SG - 131.5",
              coefficients={"a": 141.5, "b": 131.5}, output_unit="deg API", validity={"SG": [0.6, 1.1]},
              fitted_on="definition", reported_accuracy="exact by definition",
              citation="API MPMS Chapter 11.1 (2004) / ASTM D1250-04; definition as coded in m2b/API11_1VCF Conversions.cs (SGtoAPI, APItoKgm3 with water density 999.016 kg/m3 at 60 F)",
              doi="", url=API11, access="secondary_citation", where="Conversions.cs APItoSG / SGtoAPI; densH20at60 = 999.016",
              confidence="high", notes="Density at 60 F (kg/m3) = SG x 999.016 in the 2004 standard. Check: SG 0.85 gives 34.97 API.",
              _check=({"SG": 0.85}, 34.97, 0.01)))
M.append(dict(id="api_mpms_11_1_2004_ctl_crude", name="API MPMS 11.1-2004 temperature correction (CTL), crude oil group",
              target="density",
              inputs=[API_IN, {"name": "observed temperature", "unit": "F", "symbol": "T"}],
              equation_text=("rho60 = 999.016*141.5/(API+131.5); A = (0.01374979547/2)*((K0/rho60 + K1)/rho60 + K2); "
                             "B = (2K0 + K1 rho60)/(K0 + (K1 + K2 rho60) rho60); rho* = rho60*(1 + (exp(A(1+0.8A)) - 1)/(1 + A(1+1.6A)B)); "
                             "alpha60 = K0/rho*^2 + K1/rho* + K2; T68 = T(ITS-90) converted to IPTS-68 with the 8-term polynomial in tau=t/630 (a = -0.148759, -0.267408, 1.080760, 1.269056, -4.089591, -1.871251, 7.438081, -3.536296); "
                             "dT = T68 - 60.0068749; CTL = exp(-alpha60 dT (1 + 0.8 alpha60 (dT + 0.01374979547))); rho_T = rho60 CTL. Crude oil: K0 = 341.0957, K1 = 0, K2 = 0"),
              python=("import math\nrho60 = 999.016*141.5/(API+131.5)\nK0 = 341.0957\nA = (0.01374979547/2.0)*(K0/rho60**2)\nB = 2.0\n"
                      "rs = rho60*(1 + (math.exp(A*(1+0.8*A)) - 1)/(1 + A*(1+1.6*A)*B))\na60 = K0/rs**2\n"
                      "tc = (T-32)/1.8; tau = tc/630.0\nc = [-0.148759,-0.267408,1.080760,1.269056,-4.089591,-1.871251,7.438081,-3.536296]\n"
                      "d = c[-1]\nfor ci in c[-2::-1]: d = ci + d*tau\n"
                      "t68 = (tc - d*tau)*1.8 + 32\ndT = t68 - 60.0068749\nreturn math.exp(-a60*dT*(1 + 0.8*a60*(dT + 0.01374979547)))"),
              coefficients={"K0": 341.0957, "K1": 0.0, "K2": 0.0, "delta60_F": 0.01374979547, "base_T60_IPTS68_F": 60.0068749},
              output_unit="CTL (dimensionless, V_T/V_60 = rho_60/rho_T inverse; rho_T = rho60*CTL)",
              validity={"API": [-10, 100], "T": [-58, 302]},
              fitted_on="API standard (crude oil density data behind the 1980 and 2004 tables)",
              reported_accuracy="Standard; implementation reproduces Section 11.1.6.1 Example 1 to 1e-12",
              citation="API (2004). Manual of Petroleum Measurement Standards Chapter 11.1, Temperature and Pressure Volume Correction Factors for Generalized Crude Oils, Refined Products, and Lubricating Oils (ASTM D1250-04 / IP 200/04). Equations as implemented in m2b/API11_1VCF.",
              doi="", url=API11, access="secondary_citation",
              where="Sections 11.1.2.2 Eq 16, 11.1.3.3 Eq 14, 11.1.6.1 Steps 2 to 5; Example 1 values in the repository test file",
              confidence="high",
              notes="Reproduces 11.1.6.1 Example 1 (17.785 API, -27.7 F): alpha60 0.000380407044 and CTL 1.033011591958 vs published 1.033011591958. Example 2 (-10 API, 301.93 F): CTL 0.938051116886 reproduced. Use to convert API to density at 15 C, 20 C or any T, and to invert observed density to API (bulk_relations.api_from_rho_at_T).",
              _check=({"API": 17.785, "T": -27.7}, 1.033011591958, 1e-9)))
M.append(dict(id="astm_d1250_1980_t54a_crude", name="ASTM D1250-80 / API 2540 Table 53A/54A form, crude oil, 15 C base",
              target="density",
              inputs=[{"name": "density at 15 C", "unit": "kg/m3", "symbol": "rho15"}, {"name": "temperature", "unit": "C", "symbol": "T"}],
              equation_text="alpha15 = K0/rho15^2 + K1/rho15 ; VCF = exp(-alpha15 dT (1 + 0.8 alpha15 dT)), dT = T - 15 ; crude oil K0 = 613.9723, K1 = 0",
              python="rho15*np.exp(-(613.9723/rho15**2)*(T-15)*(1+0.8*(613.9723/rho15**2)*(T-15)))",
              coefficients={"K0": 613.9723, "K1": 0.0}, output_unit="kg/m3 (density at T)",
              validity={"rho15": [610.5, 1075.0], "T": [-18, 150]},
              fitted_on="1980 Petroleum Measurement Tables, generalized crude oils",
              reported_accuracy="Standard; agrees with the 2004 procedure within 0.002 kg/m3 for rho15 = 850 at 20 C (this work)",
              citation="ASTM D1250-80 / API Standard 2540 / IP 200 (1980) Petroleum Measurement Tables, Tables 53A and 54A. K0 value as used in industrial code (e.g. github.com/Kandimus/tritonn density.h; iplus-framework MaterialPetroleum.cs)",
              doi="", url="https://github.com/Kandimus/tritonn/blob/master/src/tritonn/density.h", access="secondary_citation",
              where="K0[0] = 613.9723 for crude oil group; 2004 standard notes the 1980 crude constants", confidence="high",
              notes="Simple closed form for harmonising density measured at 20 C (or other T) to 15 C: iterate rho15 = rho_T / VCF(rho15, T). For rho15 = 850, rho20 = 846.38 (2004 procedure 846.38). Density at 15 C is about 0.35 to 0.45 kg/m3 above density at 60 F, and 3.2 to 4.1 kg/m3 above density at 20 C (API 15 to 55).",
              _check=({"rho15": 850.0, "T": 20.0}, 846.3838, 0.001)))
M.append(dict(id="walther_astm_d341", name="ASTM D341 Walther viscosity-temperature equation (with D341-09 low-viscosity terms)",
              target="viscosity",
              inputs=[{"name": "Walther intercept", "unit": "-", "symbol": "A"}, {"name": "Walther slope", "unit": "-", "symbol": "B"},
                      {"name": "temperature", "unit": "K", "symbol": "TK"}],
              equation_text=("log10 log10 Z = A - B log10 T (T in K or R); Z = v + 0.7 + exp(-1.47 - 1.84 v - 0.51 v^2); "
                             "inverse v = (Z - 0.7) - exp(-0.7487 - 3.295 (Z-0.7) + 0.6119 (Z-0.7)^2 - 0.3191 (Z-0.7)^3). "
                             "Two-point fit: B = (log log Z1 - log log Z2)/(log T2 - log T1); A = log log Z1 + B log T1. Classic Walther uses Z = v + 0.7 only."),
              python=("import math\nZ = 10**(10**(A - B*math.log10(TK)))\nz = Z - 0.7\nreturn z - math.exp(-0.7487 - 3.295*z + 0.6119*z**2 - 0.3191*z**3)"),
              coefficients={"c": 0.7, "e1": -1.47, "e2": -1.84, "e3": -0.51, "i1": -0.7487, "i2": -3.295, "i3": 0.6119, "i4": -0.3191},
              output_unit="cSt", validity={"v": [0.21, 1e7]},
              fitted_on="ASTM D341 (hydrocarbon liquids, Newtonian region)",
              reported_accuracy="API TDB 11A4.4 Example B reproduced (1.2006 vs 1.201 cSt). On 156 NOAA crude oils with 3+ viscosities above pour point + 5 C, predicting the middle point from the outer two: mean abs error 3.6 %, median 0.36 %, p90 12 % (this work).",
              citation="ASTM D341 Standard Practice for Viscosity-Temperature Charts for Liquid Petroleum Products; API Technical Data Book procedure 11A4.4. Equations as implemented in pychemqt viscoAPI().",
              doi="", url=PYCHEMQT, access="secondary_citation", where="pychemqt lib/petro.py viscoAPI, Example B of procedure 11A4.4",
              confidence="high",
              notes="Use only for kinematic viscosity in the Newtonian region (above WAT ideally, at least above pour point). A, B depend on whether T is in K or R, predictions do not. Test: v(32F)=1.644, v(104F)=0.925 cSt -> v(68F) = 1.2006 cSt (published 1.201). Python check uses A, B fitted to that example in K.",
              _check=None))
M.append(deadoil("mu_od_beal_standing", "Beal (1946) dead-oil viscosity, Standing equation",
                 "mu_od = (0.32 + 1.8e7/API^4.53) (360/(T + 200))^a ; a = 10^(0.43 + 8.33/API) ; T in F",
                 "(0.32 + 1.8e7/API**4.53)*(360.0/(T+200.0))**(10**(0.43+8.33/API))",
                 {"a1": 0.32, "a2": 1.8e7, "a3": 4.53, "b1": 0.43, "b2": 8.33}, {"API": [10.1, 52.5], "T": [100, 220]},
                 "California crude oils, chart at 100 and 200 F (Beal 1946); equation by Standing (1981)",
                 "Alomair 2016 heavy Kuwaiti test: AARD 6420 %, R2 0.04 (out of range). This work, 40 C: NOAA median APE 22.5 %, local pool 37.6 %",
                 "Beal, C. (1946). The viscosity of air, water, natural gas, crude oil and its associated gases at oil field temperatures and pressures (SPE Reprint Series No. 3, 114-127, 1970); equation in Standing, M.B. (1981) Volumetric and Phase Behavior of Oil Field Hydrocarbon Systems, 9th ed., SPE.",
                 "", f"{PVTCPP} ; {PETPROPY} ; {INTECH}", "pvt-cpp UodBeal; petpropy beal_muod; IntechOpen ch. 40684 Appendix A-1", "medium",
                 "Three secondary sources agree on coefficients. Note: petpropy and IntechOpen write T-260 or (T-460)+200 with T in Rankine, same thing.",
                 ({"API": 30.0, "T": 104.0}, 9.437, 0.01)))
M.append(deadoil("mu_od_beggs_robinson_1975", "Beggs and Robinson (1975) dead-oil viscosity",
                 "mu_od = 10^x - 1 ; x = y T^-1.163 ; y = 10^z ; z = 3.0324 - 0.02023 API ; T in F (equivalently x = T^-1.163 exp(6.9824 - 0.04658 API))",
                 "10**(10**(3.0324-0.02023*API)*T**-1.163) - 1",
                 {"z0": 3.0324, "z1": -0.02023, "texp": -1.163}, {"API": [16, 58], "T": [70, 295]},
                 "460 dead-oil viscosity measurements, 16 to 58 API, 70 to 295 F (IHS Harmony documentation)",
                 "Alomair 2016 heavy oils: AARD 76.8 %, worldwide R2 0.96. This work at 40 C: overpredicts, NOAA median APE 86 %, mean log10 bias +0.19; local pool +0.27",
                 "Beggs, H.D., and Robinson, J.R. (1975). Estimating the viscosity of crude oil systems. Journal of Petroleum Technology, 27(9), 1140-1141. SPE-5434-PA.",
                 "", f"{PVTCPP} ; {PETPROPY} ; https://github.com/yohanesnuwara/reservoir-engineering", "pvt-cpp UodBeggsRobinson; petpropy; yohanesnuwara notebook (exp form)", "high",
                 "Three code sources agree; the exp form reproduces the 10^ form within 0.02 %. PetroWiki and IHS documentation state it overpredicts below about 75 to 150 F, consistent with our +0.19 log10 bias at 104 F.",
                 ({"API": 30.0, "T": 104.0}, 14.9, 0.01)))
M.append(deadoil("mu_od_glaso_1980", "Glaso (1980) dead-oil viscosity",
                 "mu_od = 3.141e10 T^-3.444 (log10 API)^a ; a = 10.313 log10 T - 36.447 ; T in F",
                 "3.141e10*T**-3.444*np.log10(API)**(10.313*np.log10(T)-36.447)",
                 {"c": 3.141e10, "texp": -3.444, "a1": 10.313, "a0": -36.447}, {"API": [20.1, 48.1], "T": [50, 300]},
                 "not stated in the sources read; validity 20 to 48 API, 50 to 300 F, 0.6 to 39 cP (Alomair 2016 Table 7)",
                 "Alomair 2016: AARD 458.8 % on heavy oils (out of range). This work at 40 C: NOAA median APE 20.6 %, bias -0.09 log10; local pool median APE 24.3 %, bias -0.005",
                 "Glaso, O. (1980). Generalized pressure-volume-temperature correlations. Journal of Petroleum Technology, 32(5), 785-795. SPE-8016-PA.",
                 "", f"{PVTCPP} ; {PETPROPY} ; {INTECH} ; {ENFOQUE}", "pvt-cpp UodGlaso; IntechOpen A-3; Enfoque UTE eq 2-3", "high",
                 "Four sources agree. Among the best performers on our pools at 40 C.",
                 ({"API": 30.0, "T": 104.0}, 7.940, 0.01)))
M.append(deadoil("mu_od_ng_egbogah_1983", "Ng and Egbogah (1983) / Egbogah and Ng (1990) dead-oil viscosity without pour point (modified Beggs-Robinson)",
                 "log10 log10 (mu_od + 1) = 1.8653 - 0.025086 API - 0.5644 log10 T ; T in F",
                 "10**(10**(1.8653-0.025086*API-0.5644*np.log10(T))) - 1",
                 {"a": 1.8653, "b": -0.025086, "c": -0.5644}, {"API": [5, 58], "T": [59, 176]},
                 "API 5 to 58 (IHS Harmony documentation); data set size not read",
                 "This work at 40 C: NOAA median APE 20.3 %, bias -0.09 log10; local pool median APE 24.1 %, bias -0.008 (best on local pool)",
                 "Ng, J.T.H., and Egbogah, E.O. (1983). An improved temperature-viscosity correlation for crude oil systems. Petroleum Society of CIM Annual Technical Meeting, Banff, PETSOC-83-34-32; Egbogah, E.O., and Ng, J.T. (1990), journal version (details not verified).",
                 "", f"{PVTCPP} ; {PETPROPY} ; {PYCHEMQT} (crude.py, commented) ; https://github.com/yohanesnuwara/reservoir-engineering",
                 "pvt-cpp UodEgbogahNg (T range 15 to 80 C); petpropy egbogad_muod; pychemqt crude.py", "high",
                 "Four code sources agree (one notebook rounds 1.8653 to 1.863). The PAPER ALSO HAS A POUR-POINT VERSION (IHS Harmony documentation: pour point -50 to 15 C, API 5 to 58) that we could not read: equation is an image. Gap.",
                 ({"API": 30.0, "T": 104.0}, 7.761, 0.01)))
M.append(deadoil("mu_od_kartoatmodjo_schmidt_1994", "Kartoatmodjo and Schmidt (1994) dead-oil viscosity",
                 "mu_od = 16e8 T^-2.8177 (log10 API)^x ; x = 5.7526 log10 T - 26.9718 ; T in F",
                 "16e8*T**-2.8177*np.log10(API)**(5.7526*np.log10(T)-26.9718)",
                 {"c": 16e8, "texp": -2.8177, "x1": 5.7526, "x0": -26.9718}, {"API": [14.4, 59], "T": [80, 320]},
                 "large worldwide data bank; ranges 14.4 to 59 API, 80 to 320 F, 0.506 to 682 cP (pvt-cpp)",
                 "Alomair 2016: AARD 123 % heavy oils. This work at 40 C: NOAA median APE 20.0 % (best on NOAA), bias -0.07",
                 "Kartoatmodjo, T., and Schmidt, Z. (1994). Large data bank improves crude physical property correlations. Oil and Gas Journal, 92(27), 51-55.",
                 "", f"{PVTCPP} ; {PETPROPY} ; {INTECH}", "pvt-cpp UodKartoatmodjoSchmidt; IntechOpen A-5", "high", "Three sources agree.",
                 ({"API": 30.0, "T": 104.0}, 8.261, 0.01)))
M.append(deadoil("mu_od_petrosky_farshad_1995", "Petrosky and Farshad (1995) dead-oil viscosity, Gulf of Mexico",
                 "mu_od = 2.3511e7 T^-2.10255 (log10 API)^x ; x = 4.59388 log10 T - 22.82792 ; T in F",
                 "2.3511e7*T**-2.10255*np.log10(API)**(4.59388*np.log10(T)-22.82792)",
                 {"c": 2.3511e7, "texp": -2.10255, "x1": 4.59388, "x0": -22.82792}, {"API": [25.4, 46.1], "T": [114, 288]},
                 "Gulf of Mexico crude oils", "range 0.725 to 10.249 cP (pvt-cpp). Alomair 2016: AARD 125 %. This work at 40 C: NOAA median APE 26 %",
                 "Petrosky, G.E., and Farshad, F.F. (1995). Viscosity correlations for Gulf of Mexico crude oils. SPE Production Operations Symposium, SPE-29468-MS.",
                 "", PVTCPP, "pvt-cpp UodPetroskyFarshad", "medium", "Single secondary source (code).",
                 ({"API": 30.0, "T": 104.0}, 6.804, 0.01)))
M.append(deadoil("mu_od_de_ghetto_1995", "De Ghetto, Paone and Villa (1995) dead-oil viscosity, heavy and extra-heavy (modified Egbogah-Jack)",
                 "API <= 10: log10 log10(mu_od+1) = 1.90296 - 0.012619 API - 0.61748 log10 T ; 10 < API <= 22.3: log10 log10(mu_od+1) = 2.06492 - 0.0179 API - 0.70226 log10 T ; T in F",
                 "10**(10**(np.where(API<=10, 1.90296-0.012619*API-0.61748*np.log10(T), 2.06492-0.0179*API-0.70226*np.log10(T)))) - 1",
                 {"xh_a": 1.90296, "xh_b": -0.012619, "xh_c": -0.61748, "h_a": 2.06492, "h_b": -0.0179, "h_c": -0.70226},
                 {"API": [6, 22.3], "T": [131.4, 250.7]},
                 "Heavy and extra-heavy oils; dead-oil viscosity 7.7 to 1386.9 cP (IHS Harmony documentation)",
                 "This work: strongly overpredicts light oils at 40 C (out of range), NOAA bias +0.29 log10; use only for API < 22.3",
                 "De Ghetto, G., Paone, F., and Villa, M. (1995). Pressure-volume-temperature correlations for heavy and extra heavy oils. SPE International Heavy Oil Symposium, Calgary, SPE-30316-MS.",
                 "", f"{PVTCPP} ; https://www.ihsenergy.ca/support/documentation_ca/WellTest/content/html_files/reference_materials/calculations_correlations/oil_correlations.htm",
                 "pvt-cpp UodDeGhettoEtAl; IHS WellTest doc names 'modified Egbogah-Jack' and the two API classes", "medium",
                 "Coefficients from one code source; the IHS page confirms the two API classes and ranges but its equations are images.",
                 ({"API": 15.0, "T": 150.0}, br.mu_od_de_ghetto(15.0, 150.0), 1e-9)))
M.append(deadoil("mu_od_naseri_2005", "Naseri, Nikazar and Mousavi Dehghani (2005) dead-oil viscosity, Iranian oils",
                 "log10 mu_od = 11.2699 - 4.2699 log10 API - 2.052 log10 T ; T in F",
                 "10**(11.2699-4.2699*np.log10(API)-2.052*np.log10(T))",
                 {"a": 11.2699, "b": -4.2699, "c": -2.052}, {"API": [17, 44], "T": [105, 295]},
                 "Iranian crude oils; 17 to 44 API, 105 to 295 F, 0.75 to 54 cP (Alomair 2016 Table 7; pvt-cpp)",
                 "Alomair 2016: AARD 76 %, worldwide R2 0.27. This work at 40 C: NOAA median APE 28 %, bias -0.17",
                 "Naseri, A., Nikazar, M., and Mousavi Dehghani, S.A. (2005). A correlation approach for prediction of crude oil viscosities. Journal of Petroleum Science and Engineering (volume and pages not verified).",
                 "", f"{PVTCPP} ; {ENFOQUE} ; {VURUP}", "pvt-cpp UodNaseri; Enfoque UTE eq 5 (garbled but same digits); Sattarin 2007 A5 (garbled)",
                 "medium", "pvt-cpp and Enfoque UTE agree on 11.2699, 4.2699, 2.052; the Petroleum and Coal page text printed 11.699 and 4.298 (extraction garble).",
                 ({"API": 30.0, "T": 104.0}, 6.665, 0.01)))
M.append(deadoil("mu_od_labedi_1992", "Labedi (1992) dead-oil viscosity, light Libyan crudes",
                 "mu_od = 10^9.224 / (API^4.7013 T^0.6739) ; T in F (signs reconstructed from a garbled rendering)",
                 "10**9.224/(API**4.7013*T**0.6739)",
                 {"a": 9.224, "b": 4.7013, "c": 0.6739}, {"API": [32, 48], "T": [100, 306]},
                 "Libyan light crudes", "Alomair 2016: AARD 2884 % on heavy oils (out of range). This work at 40 C: NOAA median APE 21 %, local pool 25 %, bias near 0, which supports the sign reading",
                 "Labedi, R. (1992). Improved correlations for predicting the viscosity of light crudes. Journal of Petroleum Science and Engineering, 8(3), 221-234.",
                 "", INTECH, "IntechOpen ch. 40684 Appendix A-4 (superscripts and minus signs lost in extraction)", "low",
                 "Only one secondary rendering, with lost signs. Treat as unverified until the primary is read.",
                 ({"API": 40.0, "T": 104.0}, br.mu_od_labedi(40, 104), 1e-9)))
M.append(dict(id="pour_point_api_tdb_2b8", name="API Technical Data Book procedure 2B8.1 pour point of petroleum fractions",
              target="pour_point",
              inputs=[{"name": "specific gravity", "unit": "-", "symbol": "SG"}, {"name": "mean average boiling point", "unit": "R", "symbol": "Tb"},
                      {"name": "kinematic viscosity at 100 F", "unit": "cSt", "symbol": "v100"}],
              equation_text="PP(R) = 753 + 136 (1 - exp(-0.15 v100)) - 572 SG + 0.0512 v100 + 0.139 Tb (Eq 2B8.1-1) ; without viscosity: PP = 3.85e-8 Tb^5.49 10^-(0.712 Tb^0.315 + 0.133 SG) + 1.4 (Eq 2B8.1-2)",
              python="753 + 136*(1-np.exp(-0.15*v100)) - 572*SG + 0.0512*v100 + 0.139*Tb",
              coefficients={"c0": 753, "c1": 136, "k": -0.15, "cSG": -572, "cv": 0.0512, "cTb": 0.139},
              output_unit="R (subtract 459.67 for F)", validity={"SG": [0.8, 1.0], "Tb": [800, 1500], "v100": [2, 960]},
              fitted_on="petroleum fractions (API TDB)", reported_accuracy="not stated in the secondary source",
              citation="API (1997). Technical Data Book - Petroleum Refining, 6th ed., procedure 2B8.1 (origin of Eq 2B8.1-1 usually credited to Hu and Burns 1970, not verified). As implemented in pychemqt PourPoint().",
              doi="", url=PYCHEMQT, access="secondary_citation", where="pychemqt lib/petro.py PourPoint docstring example", confidence="medium",
              notes="Reproduces the documented example: SG 0.839, Tb 972 R, v100 3 cSt -> 457.6 R (published 458 R, about -1.4 C). For narrow fractions; applying to whole crudes needs Tb = MeABP of the crude, which is not measured in our data, so use only as a soft constraint.",
              _check=({"SG": 0.839, "Tb": 972.0, "v100": 3.0}, 458.0, 0.5)))
M.append(dict(id="mw_riazi_daubert_1980", name="Riazi and Daubert (1980) molecular weight from Tb and SG", target="other",
              inputs=[{"name": "mean average boiling point", "unit": "R", "symbol": "Tb"}, {"name": "specific gravity", "unit": "-", "symbol": "SG"}],
              equation_text="M = 4.5673e-5 Tb^2.1962 SG^-1.0164", python="4.5673e-5*Tb**2.1962*SG**-1.0164",
              coefficients={"a": 4.5673e-5, "b": 2.1962, "c": -1.0164}, output_unit="g/mol", validity={"Tb": [560, 1310], "M": [70, 300]},
              fitted_on="petroleum fractions", reported_accuracy="not stated in secondary source",
              citation="Riazi, M.R., and Daubert, T.E. (1980). Simplify property predictions. Hydrocarbon Processing, March 1980, 115-116. Coefficients and Ahmed (2016) Example 2.2 as in pychemqt prop_Riazi_Daubert_1980().",
              doi="", url=PYCHEMQT, access="secondary_citation", where="pychemqt lib/petro.py prop_Riazi_Daubert_1980 docstring", confidence="medium",
              notes="Reproduces Ahmed Example 2.2: Tb 198 F, SG 0.7365 -> 96.3 (published 96).",
              _check=({"Tb": 657.67, "SG": 0.7365}, 96.0, 0.5)))
M.append(dict(id="mw_riazi_daubert_1987_visc_sg", name="Riazi and Daubert (1987) molecular weight from kinematic viscosity at 100 F and SG", target="other",
              inputs=[{"name": "kinematic viscosity at 100 F", "unit": "cSt", "symbol": "v100"}, {"name": "specific gravity", "unit": "-", "symbol": "SG"}],
              equation_text="M = a v100^e SG^f exp(b v100 + c SG + d v100 SG) ; a = 1.51723e6, b = -0.195411, c = -9.63897, d = 0.16247, e = 0.56370, f = 6.89383",
              python="1.51723e6*v100**0.56370*SG**6.89383*np.exp(-0.195411*v100 - 9.63897*SG + 0.16247*v100*SG)",
              coefficients={"a": 1.51723e6, "b": -0.195411, "c": -9.63897, "d": 0.16247, "e": 0.56370, "f": 6.89383}, output_unit="g/mol",
              validity={"M": [200, 800], "v100": [2, 18000], "SG": [0.82, 1.08]},
              fitted_on="heavy petroleum fractions", reported_accuracy="not stated in secondary source",
              citation="Riazi, M.R., and Daubert, T.E. (1987). Characterization parameters for petroleum fractions. Ind. Eng. Chem. Res., 26(4), 755-759. Coefficients as tabulated in pychemqt (Table VII, v1-SG). Validity ranges as quoted by Gomez (1996) OGJ.",
              doi="10.1021/ie00064a023", url=PYCHEMQT + " ; https://www.ogj.com/home/article/17234322/new-equations-predict-boiling-point-from-viscosity-gravity",
              access="secondary_citation", where="pychemqt prop_Riazi_Daubert par['M']['v1-SG']", confidence="low",
              notes="No published worked example found; v100 = 10 cSt and SG 0.9 gives 281 g/mol (plausible). The exp argument structure follows pychemqt's code; unit of v1 assumed cSt. Verify against the primary paper before use.",
              _check=({"v100": 10.0, "SG": 0.9}, 280.64, 0.05)))
M.append(dict(id="mw_hirschler_astm_d2502", name="Hirschler (1946) equations behind ASTM D2502 (MW from viscosity at 100 F and 210 F)", target="other",
              inputs=[{"name": "kinematic viscosity at 100 F", "unit": "cSt", "symbol": "v100"}, {"name": "kinematic viscosity at 210 F", "unit": "cSt", "symbol": "v210"}],
              equation_text="H = 870 log10(log10(v + 0.6)) + 154 ; MW = 180 + S (H100 + 60) ; S = 4.146 - 1.733 log10(VSF - 145) ; VSF = H100 - H210",
              python=("H1 = 870*np.log10(np.log10(v100+0.6))+154\nH2 = 870*np.log10(np.log10(v210+0.6))+154\n"
                      "return 180 + (4.146 - 1.733*np.log10(H1-H2-145))*(H1+60)"),
              coefficients={"h1": 870, "h0": 154, "c": 0.6, "m0": 180, "s0": 4.146, "s1": -1.733, "vsf0": 145, "h60": 60}, output_unit="g/mol",
              validity={"MW": [250, 700]}, fitted_on="average petroleum fractions (lubricating oils)",
              reported_accuracy="D2502 chart precision: repeatability 3 g/mol, reproducibility 25 g/mol",
              citation="Hirschler, A.E. (1946). Molecular weight of petroleum oils from viscosity (journal details not verified). Equations as given by JAWChemist (2020) modelling the ASTM D2502 chart; worked example from ASTM D2502-92(2002) Section 5.3 (official preview).",
              doi="", url="https://jawchemist.blogspot.com/p/mw-calc-full.html ; https://cdn.standards.iteh.ai/samples/23092/b14826d85cdd4755a615c78135051b7e/ASTM-D2502-92-2002-.pdf",
              access="secondary_citation", where="JAWChemist Eq 1, 3, 4, 5; D2502 Section 5.3 example and Table 1", confidence="medium",
              notes="Reproduces D2502 example: v100 179, v210 9.72 cSt -> H100 461.1 (published 461) and MW 357.5 (chart 360, within reproducibility). Whole crudes contain light ends, so MW from this is only for heavy cuts.",
              _check=({"v100": 179.0, "v210": 9.72}, 360.0, 5.0)))
M.append(dict(id="visc_api_tdb_11a4_2", name="API TDB procedure 11A4.2 kinematic viscosity at 100 F and 210 F from Tb and Watson K", target="viscosity",
              inputs=[{"name": "mean average boiling point", "unit": "R", "symbol": "Tb"}, {"name": "Watson K", "unit": "-", "symbol": "Kw"}],
              equation_text=("v100 = 10^(-1.35579 + 8.16059e-4 Tb + 8.38505e-7 Tb^2) + 10^(A1 + A2 Kw) ; A1 = 34.931 - 8.84387e-2 Tb + 6.73513e-5 Tb^2 - 1.01394e-8 Tb^3 ; "
                             "A2 = -2.92649 + 6.98405e-3 Tb - 5.09947e-6 Tb^2 + 7.49378e-10 Tb^3 ; v210 = 10^(-1.92353 + 2.41071e-4 Tb + 0.5113 log10(Tb v100))"),
              python=("A1 = 34.931-8.84387e-2*Tb+6.73513e-5*Tb**2-1.01394e-8*Tb**3\nA2 = -2.92649+6.98405e-3*Tb-5.09947e-6*Tb**2+7.49378e-10*Tb**3\n"
                      "return 10**(-1.35579+8.16059e-4*Tb+8.38505e-7*Tb**2) + 10**(A1+A2*Kw)"),
              coefficients={"r0": -1.35579, "r1": 8.16059e-4, "r2": 8.38505e-7, "A1": [34.931, -8.84387e-2, 6.73513e-5, -1.01394e-8], "A2": [-2.92649, 6.98405e-3, -5.09947e-6, 7.49378e-10],
                            "v210": [-1.92353, 2.41071e-4, 0.5113]},
              output_unit="cSt (v100)", validity={"Tb": [800, 1600], "Kw": [10, 13]}, fitted_on="petroleum fractions",
              reported_accuracy="reproduces API TDB Examples A (5.94/1.88 cSt) and C (1.249 cSt)",
              citation="API (1997). Technical Data Book - Petroleum Refining, procedure 11A4.2, as implemented in pychemqt viscoAPI().",
              doi="", url=PYCHEMQT, access="secondary_citation", where="pychemqt lib/petro.py viscoAPI docstring Examples A, B, C", confidence="medium",
              notes="Combined with Kw = Tb^(1/3)/SG this can be inverted to get MeABP and Watson K from API and v100 (bulk_relations.tb_kw_from_api_v100): API 30, v100 10 cSt -> Tb 1114 R, Kw 11.83. Example A: Tb 598.7 F, Kw 11.87 -> 5.942 cSt (published 5.94).",
              _check=({"Tb": 1058.37, "Kw": 11.87}, 5.94, 0.006)))
M.append(dict(id="watson_k", name="Watson (UOP) characterisation factor", target="other",
              inputs=[{"name": "mean average boiling point", "unit": "R", "symbol": "Tb"}, {"name": "specific gravity", "unit": "-", "symbol": "SG"}],
              equation_text="Kw = Tb^(1/3) / SG", python="Tb**(1.0/3.0)/SG", coefficients={"exp": 1.0 / 3.0}, output_unit="-",
              validity={"Kw": [10, 13]}, fitted_on="definition", reported_accuracy="definition",
              citation="Watson, K.M., and co-workers (1930s), UOP characterisation factor (primary details not verified); as used in pychemqt and the API Technical Data Book.",
              doi="", url=PYCHEMQT, access="secondary_citation", where="pychemqt petro.py Kw usage", confidence="high",
              notes="Paraffinic crudes about 12 to 12.5, naphthenic about 11 to 11.5. Whole-crude Kw from API and viscosity via visc_api_tdb_11a4_2 inversion is a soft estimate. Check: Tb 1000 R, SG 0.85 -> 11.765.",
              _check=({"Tb": 1000.0, "SG": 0.85}, 11.765, 0.001)))


def run_py(code, inputs):
    env = {"np": np, "math": math}
    if "return" in code:
        args = ", ".join(inputs.keys())
        src = "def _f(" + args + "):\n" + "\n".join("    " + ln for ln in code.split("\n"))
        exec(src, env)
        return env["_f"](**inputs)
    return eval(code, env, dict(inputs))


# Walther check: fit A,B to Example B in K and evaluate at 68 F
A, B = br.walther_fit(1.644, 0.0, 0.925, 40.0)
for m in M:
    if m["id"] == "walther_astm_d341":
        m["_check"] = ({"A": A, "B": B, "TK": 293.15}, 1.201, 0.0006)
        m["coefficients"]["example_fit_A_K"] = A
        m["coefficients"]["example_fit_B_K"] = B

with open(os.path.join(HERE, "models.jsonl"), "w") as fh:
    for m in M:
        chk = m.pop("_check")
        if chk:
            got = float(run_py(m["python"], chk[0]))
            ok = abs(got - chk[1]) <= chk[2]
            print(("OK  " if ok else "BAD ") + m["id"], round(got, 6), chk[1])
            assert ok, m["id"]
        fh.write(json.dumps(m, ensure_ascii=False) + "\n")
print(len(M), "models")
