"""Builds models.jsonl (and checks every python field runs) for agents/thermo."""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
U = {
 "lira": "https://escholarship.org/content/qt9cb4w8ss/qt9cb4w8ss.pdf",
 "cout06": "https://scispace.com/pdf/reliable-wax-predictions-for-flow-assurance-2y02u640e4.pdf",
 "broad": "https://nvlpubs.nist.gov/nistpubs/jres/066/3/V66.N03.A05.pdf",
 "neq": "https://raw.githubusercontent.com/equinor/neqsim/master/src/main/java/neqsim/thermo/characterization/WaxCharacterise.java",
 "neqdoc": "https://equinor.github.io/neqsim/thermo/characterization/wax_characterization",
 "neqchar": "https://equinor.github.io/neqsim/pvtsimulation/fluid_characterization_mathematics",
 "bhang": "https://core.ac.uk/download/162577799.pdf",
 "hw": "https://core.ac.uk/download/287498089.pdf",
 "omega": "https://rcastoragev2.blob.core.windows.net/fac5385c3077144472cce8760da0bd29/ao1c07072.PMC9134231.pdf",
 "escobar": "https://www.redalyc.org/pdf/465/46519036003.pdf",
 "rob": "https://burjcdigital.urjc.es/bitstreams/49e877cc-f97e-43c1-9119-d7c433729b55/download",
 "johnsen": "https://arxiv.org/pdf/1807.08514",
 "zhou": "https://mdpi-res.com/d_attachment/processes/processes-14-01207/article_deploy/processes-14-01207.pdf",
 "chula": "https://cuir.car.chula.ac.th/bitstream/123456789/73565/7/Arm_yo_back_p.pdf",
 "jamali": "https://jogpt.pgu.ac.ir/article_226634_faa6a0d36cb2c33d9bb742d59617d392.pdf",
}
C = {
 "won86": "Won, K.W. (1986). Fluid Phase Equilibria, 30, 265-279 (title not verified).",
 "lira": "Lira-Galeana, C., Firoozabadi, A., Prausnitz, J.M. (1996). Thermodynamics of wax precipitation in petroleum mixtures. AIChE Journal (1996); read as preprint LBL-36816, Lawrence Berkeley Laboratory, 1995.",
 "ped91": "Pedersen, K.S., Skovborg, P., Ronningsen, H.P. (1991). Wax precipitation from North Sea crude oils. 4. Thermodynamic modeling. Energy & Fuels, 5, 924-932.",
 "ped95": "Pedersen, K.S. (1995). Prediction of cloud point temperatures and amount of wax precipitation. SPE Production & Facilities, 10(1).",
 "cout06": "Coutinho, J.A.P., Edmonds, B., Moorwood, T., Szczepanski, R., Zhang, X. (2006). Reliable wax predictions for flow assurance. Energy & Fuels (2006).",
 "broad": "Broadhurst, M.G. (1962). An analysis of the solid phase behavior of the normal paraffins. Journal of Research of the National Bureau of Standards, 66A(3).",
 "ji": "Ji, H.Y., Tohidi, B., Danesh, A., Todd, A.C. (2004). Wax phase equilibria: developing a thermodynamic model using a systematic approach. Fluid Phase Equilibria (as quoted by Ameri Mahabadian, Chapoy, Burgass, Tohidi, Heriot-Watt).",
 "hw": "Ameri Mahabadian, M., Chapoy, A., Burgass, R., Tohidi, B. Integrated wax-hydrate formation in real oil mixtures: what factors are important from thermodynamic modelling? (Heriot-Watt University, about 2016-2017).",
 "rob": "Robustillo, M.D., Martos, C., Espada, J.J., Coto, B. (2012). Assessment of different methods to determine the total wax content of crude oils. Energy & Fuels, 26, 6352-6357.",
 "escobar": "Escobar-Remolina, J.C.M., Barrios-Ortiz, W., Santoyo-Ramirez, G. (2009). Multi-solid model modified to predict paraffin precipitation in petroleum fluids at high temperatures and pressures. CT&F Ciencia, Tecnologia y Futuro, 3(5), 35-51.",
 "johnsen": "Johnsen, S.G. (2018). A general correlation between the temperature-dependent solubility and solute and solvent molar masses in binary n-alkane mixtures (review). arXiv:1807.08514.",
 "whitson": "Whitson, C.H. (1983). Characterizing hydrocarbon plus fractions. SPE Journal, 23(4), 683-694 (as given on the NeqSim fluid characterisation page).",
 "ped84": "Pedersen, K.S., Thomassen, P., Fredenslund, A. (1984). Ind. Eng. Chem. Process Des. Dev., 23(1), 163-170 (as given on the NeqSim page).",
 "omega": "Shariatrad, F., Javanmardi, J., Rasoolzadeh, A., Mohammadi, A.H. (2022). Experimental measurement and thermodynamic modeling of the WDT for a quaternary system of normal paraffins. ACS Omega, 7, 16928-16938.",
}

models = []
def M(**k):
    models.append(k)

# ---------------- pure n-alkane properties ----------------
M(id="won1986_Tf", name="Won melting temperature of wax-forming component", target="melting_point",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}],
  equation_text="T_i^f = 374.5 + 0.02617 M_i - 20172 / M_i", python="374.5 + 0.02617*M - 20172/M",
  coefficients={"a": 374.5, "b": 0.02617, "c": 20172}, output_unit="K", validity={"M": [100, 1000]},
  fitted_on="n-paraffins (Won 1986)", reported_accuracy="not stated in the secondary text", citation=C["won86"],
  doi="", url=U["lira"], access="secondary_citation",
  where="Lira-Galeana preprint Eq 8; same coefficients in NeqSim PedersenWaxModel and Bhangale 2007 Eq 4.15",
  confidence="high", notes="Read in three independent places with identical coefficients. Used by Pedersen 1991/1995 for every pseudo-component. Check: M=282.5 (n-C20) gives 310.5 K vs measured 309.8 K.",
  _test={"M": 282.55}, _expect=(310.5, 0.2))
M(id="won1986_dHf", name="Won enthalpy of fusion", target="enthalpy_fusion",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}, {"name": "melting temperature", "unit": "K", "symbol": "Tf"}],
  equation_text="dH_i^f = 0.1426 M_i T_i^f  (cal/mol)", python="0.1426*M*Tf*4.184",
  coefficients={"a": 0.1426}, output_unit="J/mol", validity={"M": [100, 1000]}, fitted_on="n-paraffins",
  reported_accuracy="not stated", citation=C["won86"], doi="", url=U["lira"], access="secondary_citation",
  where="Lira-Galeana preprint Eq 10; NeqSim calcHeatOfFusion (0.1426/0.238845 J); Bhangale Eq 4.14", confidence="high",
  notes="Original in cal/mol; python converts to J/mol. Lira-Galeana argue this is 2 to 3 times too large for non-normal components. Check: n-C20 gives 52.4 kJ/mol (measured total about 70 kJ/mol).",
  _test={"M": 282.55, "Tf": 310.5}, _expect=(52348, 50))
M(id="lira1996_Tf", name="Lira-Galeana melting temperature (P, N, A pseudo-components)", target="melting_point",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}],
  equation_text="T_i^f = 333.46 - 419.01 exp(-0.008546 M_i)", python="333.46 - 419.01*np.exp(-0.008546*M)",
  coefficients={"a": 333.46, "b": 419.01, "c": 0.008546}, output_unit="K", validity={"M": [80, 450]},
  fitted_on="API RP44 melting points of n-paraffins, alkylcyclohexanes and alkylbenzenes C6-C30", reported_accuracy="not stated",
  citation=C["lira"], doi="", url=U["lira"], access="full_text", where="Eq 9", confidence="medium",
  notes="Leading constant partly garbled in the OCR; 0.008546 also printed by Escobar-Remolina 2009. Not an n-paraffin correlation: it gives 296 K for M=282 against 310 K for n-C20, so do not use it for n-alkanes.",
  _test={"M": 282.55}, _expect=(296.0, 0.3))
M(id="lira1996_dHf", name="Lira-Galeana reduced enthalpy of fusion", target="enthalpy_fusion",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}, {"name": "melting temperature", "unit": "K", "symbol": "Tf"}],
  equation_text="dH_i^f = 0.05276 M_i T_i^f (cal/mol)", python="0.05276*M*Tf*4.184", coefficients={"a": 0.05276},
  output_unit="J/mol", validity={"M": [80, 900]}, fitted_on="Won slope reduced to match API RP44 melting entropies of P, N, A",
  reported_accuracy="not stated", citation=C["lira"], doi="", url=U["lira"], access="full_text", where="Eq 11",
  confidence="medium", notes="For use with lira1996_Tf in the multisolid model.", _test={"M": 282.55, "Tf": 296.0}, _expect=(18460, 30))
M(id="pedersen1991_dCp", name="Pedersen heat capacity difference liquid minus solid", target="other",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}, {"name": "temperature", "unit": "K", "symbol": "T"}],
  equation_text="dCp_i = 0.3033 M_i - 4.635e-4 M_i T  (cal/(mol K))", python="(0.3033*M - 4.635e-4*M*T)*4.184",
  coefficients={"alpha": 0.3033, "beta": -4.635e-4}, output_unit="J/(mol K)", validity={"T": [250, 350]},
  fitted_on="tuned on 17 North Sea crude oils (Pedersen et al. 1991)", reported_accuracy="not stated", citation=C["ped91"],
  doi="", url=U["lira"], access="secondary_citation", where="Lira-Galeana preprint Eq 12; NeqSim doc; Jamali 2025 Eq 24",
  confidence="high", notes="Used with the SLE term -(dCp/R)(Tf/T - 1 - ln(Tf/T)). In test_thermo T3 adding it lowers ideal-solid-solution WAT of the Dauphin systems by about 1.4 K.",
  _test={"M": 282.55, "T": 300.0}, _expect=(194.2, 0.5))
M(id="broadhurst1962_Tm", name="Broadhurst melting point of long n-paraffins", target="melting_point",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "n"}],
  equation_text="TM(K) = 414.3 (n - 1.5)/(n + 5.0)", python="414.3*(n-1.5)/(n+5.0)",
  coefficients={"T0": 414.3, "a": -1.5, "b": 5.0}, output_unit="K", validity={"n": [44, 100]},
  fitted_on="14 n-paraffins C44 and above (orthorhombic melting)", reported_accuracy="sd of TM 0.3 K; T0 uncertainty +-2.4 K",
  citation=C["broad"], doi="", url=U["broad"], access="full_text", where="abstract and Eq in text",
  confidence="high", notes="No odd/even split above C44. Below C20 melting points alternate (odd lower). Check: n=50 gives 365.3 K; Zhou 2026 cooling DSC 92.2 C.",
  _test={"n": 50}, _expect=(365.34, 0.05))
M(id="coutinho2006_Tm", name="Coutinho n-alkane melting temperature (Marano-Holder form)", target="melting_point",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "N"}],
  equation_text="Tm = 421.63 - 1936412 exp(-7.8945 (N - 1)^0.07194) K", python="421.63 - 1936412*np.exp(-7.8945*(N-1)**0.07194)",
  coefficients={"Tinf": 421.63, "dT0": 1936412, "beta": 7.8945, "gamma": 0.07194}, output_unit="K", validity={"N": [5, 100]},
  fitted_on="n-alkane melting data, built on Broadhurst 1962 with the Marano and Holder 1997 asymptotic approach (Coutinho 2001 BJChE text)",
  reported_accuracy="not stated", citation=C["cout06"], doi="10.1021/ef050082i", url=U["cout06"], access="full_text", where="Eq 2",
  confidence="high", notes="Smooth average of odd and even. Matches even n within 1 K above C18 but is 8.7 K low at n-C10 (Broadhurst 243.5 K). Matches Zhou 2026 DSC for C44-C50 within 0.4 K. Same form as Marano-Holder asymptotic correlation Y = Yinf - dY0 exp(-beta (n-n0)^gamma).",
  _test={"N": 20}, _expect=(309.54, 0.05))
M(id="coutinho2006_dH_total", name="Coutinho total melting enthalpy (orthorhombic solid)", target="enthalpy_fusion",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "N"}], equation_text="dHm = 3779.1 N - 12654 J/mol",
  python="3779.1*N - 12654", coefficients={"a": 3779.1, "b": -12654}, output_unit="J/mol", validity={"N": [8, 100]},
  fitted_on="n-alkane calorimetry (fusion plus solid-solid transitions)", reported_accuracy="not stated", citation=C["cout06"],
  doi="10.1021/ef050082i", url=U["cout06"], access="full_text", where="Eq 3", confidence="high",
  notes="Use alone (eq 4: dG = dHm(T/Tm - 1)) for n-paraffins with no rotator phase. For C8-C40 the rotator transition enthalpy is eq3 minus eq5.",
  _test={"N": 30}, _expect=(100719, 1))
M(id="coutinho2006_dHm_rotator", name="Coutinho fusion enthalpy from rotator phase, n-C8 to n-C40", target="enthalpy_fusion",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "N"}], equation_text="dHm = 3.55 N^3 - 237.6 N^2 + 7400 N - 34814 J/mol",
  python="3.55*N**3 - 237.6*N**2 + 7400*N - 34814", coefficients={"a3": 3.55, "a2": -237.6, "a1": 7400, "a0": -34814},
  output_unit="J/mol", validity={"N": [8, 40]}, fitted_on="n-alkanes C8-C40", reported_accuracy="not stated", citation=C["cout06"],
  doi="10.1021/ef050082i", url=U["cout06"], access="full_text", where="Eq 5", confidence="high",
  notes="The Mahidol thesis appendix prints the same polynomial (0.0036 N^3 - 0.2376 N^2 + 7.4 N - 34.814 kJ/mol for N>19), so it predates 2006 (Coutinho 1998 era).",
  _test={"N": 30}, _expect=(69196, 1))
M(id="coutinho2006_Ttr", name="Coutinho rotator to orthorhombic transition temperature", target="other",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "N"}], equation_text="Ttr = 420.42 - 134784 exp(-4.344 (N + 6.592)^0.14627) K",
  python="420.42 - 134784*np.exp(-4.344*(N+6.592)**0.14627)", coefficients={"Tinf": 420.42, "dT0": 134784, "beta": 4.344, "n0": -6.592, "gamma": 0.14627},
  output_unit="K", validity={"N": [8, 40]}, fitted_on="n-alkane transition data", reported_accuracy="not stated", citation=C["cout06"],
  doi="10.1021/ef050082i", url=U["cout06"], access="full_text", where="Eq 6", confidence="high",
  notes="Transition enthalpy dHtr = (eq 3) - (eq 5). Gibbs energy with transition: dG = dHm(T/Tm - 1) + dHtr(T/Ttr - 1) (eq 7). Check N=25 gives 319.6 K.",
  _test={"N": 25}, _expect=(319.6, 0.2))
M(id="coutinho_puniquac_rq", name="Predictive UNIQUAC structural parameters", target="other",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "N"}], equation_text="q_i = 0.1 N_i + 0.1141 ; r_i = 0.1 N_i + 0.0672",
  python="(0.1*N + 0.0672, 0.1*N + 0.1141)", coefficients={"r0": 0.0672, "q0": 0.1141, "slope": 0.1}, output_unit="(r, q)",
  validity={"N": [5, 100]}, fitted_on="n-alkanes", reported_accuracy="n/a", citation=C["cout06"], doi="10.1021/ef050082i", url=U["cout06"],
  access="full_text", where="Eqs 12-13", confidence="high", notes="Numerically confirmed by Shariatrad 2022 Table 5 (C11: r 1.1672, q 1.2141).",
  _test={"N": 11}, _expect=None)
M(id="coutinho_interaction_energies", name="Wilson / P-UNIQUAC solid interaction energies from sublimation enthalpy", target="other",
  inputs=[{"name": "sublimation enthalpy", "unit": "J/mol", "symbol": "dHsub"}, {"name": "temperature", "unit": "K", "symbol": "T"}],
  equation_text="lambda_ii = -1/3 (dHsub_i - R T) ; lambda_ij = R_ij min(lambda_ii, lambda_jj) (Wilson) ; lambda_ij = min(lambda_ii, lambda_jj) (P-UNIQUAC) ; R_ij = 1 - 8e-7 |dHsub_i - dHsub_j| ; dHsub = dHvap + dHm + dHtr at Tm",
  python="-(1.0/3.0)*(dHsub - 8.314462618*T)", coefficients={"Z_over_2_inverse": 1/3.0, "Rij_coef": 8e-7}, output_unit="J/mol",
  validity={}, fitted_on="Z = 6 orthorhombic coordination (Coutinho)", reported_accuracy="n/a", citation=C["cout06"], doi="10.1021/ef050082i",
  url=U["cout06"], access="full_text", where="Eqs 8-15", confidence="high",
  notes="dHvap from the PERT2 correlation (Morgan and Kobayashi 1994), not collected here, so P-UNIQUAC is not implemented in thermo_wat.py. NeqSim doc writes lambda_ii = -(2/Z)(dHsub - RT) with Z=10 in its code docs (different choice).",
  _test={"dHsub": 150000.0, "T": 300.0}, _expect=(-49168.6, 1))
M(id="pedersen1991_solubility_params", name="Pedersen liquid and solid solubility parameters (regular solution)", target="other",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "CN"}],
  equation_text="delta_L = 7.41 + 0.5914 (ln CN - ln 7) ; delta_S = 8.50 + 5.763 (ln CN - ln 7)  ((cal/cm3)^0.5)",
  python="(7.41 + 0.5914*(np.log(CN)-np.log(7)), 8.50 + 5.763*(np.log(CN)-np.log(7)))", coefficients={"a1": 0.5914, "a2": 5.763},
  output_unit="(cal/cm3)^0.5", validity={"CN": [7, 80]}, fitted_on="North Sea crude wax data (Pedersen 1991), used with Won regular-solution model",
  reported_accuracy="not stated", citation=C["ped91"], doi="", url=U["bhang"], access="secondary_citation",
  where="Bhangale 2007 Eqs 4.21-4.22; reproduces Shariatrad 2022 Table 5 values (C11: 7.6773 and 11.1048)", confidence="high",
  notes="Activity coefficient ln gamma_i = V_i (delta_i - delta_mix)^2 / (R T), delta_mix volume-fraction average (Won). Won 1986 originally tabulated delta to C40.",
  _test={"CN": 11}, _expect=None)
M(id="won_liquid_density_25C", name="Won molar volume density at 25 C", target="density",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}], equation_text="d25 = 0.8155 + 0.6272e-4 M - 13.06/M (g/cm3)",
  python="0.8155 + 0.6272e-4*M - 13.06/M", coefficients={"a": 0.8155, "b": 0.6272e-4, "c": 13.06}, output_unit="g/cm3", validity={"M": [100, 900]},
  fitted_on="n-paraffins", reported_accuracy="not stated", citation=C["won86"], doi="", url=U["bhang"],
  access="secondary_citation", where="Bhangale 2007 Eq 4.24", confidence="medium", notes="Gives molar volume V = M/d for regular solution terms. n-C20: 0.787.",
  _test={"M": 282.55}, _expect=(0.7865, 0.002))
M(id="johnsen_Tm", name="Simple n-alkane melting point", target="melting_point", inputs=[{"name": "carbon number", "unit": "-", "symbol": "N"}],
  equation_text="Tm(N) = 414.6/(1 + 6.86/N) - 273.15 (C)", python="414.6/(1+6.86/N) - 273.15", coefficients={"a": 414.6, "b": 6.86},
  output_unit="C", validity={"N": [10, 100]}, fitted_on="from Dollhopf et al. and Laux et al.", reported_accuracy="not stated", citation=C["johnsen"],
  doi="", url=U["johnsen"], access="full_text", where="Eq 5", confidence="medium", notes="No odd/even split. N=20 gives 35.6 C (n-C20 36.6 C).",
  _test={"N": 20}, _expect=(35.56, 0.05))
M(id="escobar2009_dCp", name="Escobar-Remolina refit of heat capacity difference", target="other",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}, {"name": "melting temperature", "unit": "K", "symbol": "Tf"}],
  equation_text="dCp_i = 0.2557 M_i - 4.4245e-4 M_i T_i^f (cal/(mol K)); also dH_f = 0.107834 M_i T_i^f; Tf = 370.12 + 0.002403 M_i ... - 15760.33/M_i ... 139.67 exp(... 0.008546 M_i) (garbled)",
  python="0.2557*M - 4.4245e-4*M*Tf", coefficients={"a": 0.2557, "b": -4.4245e-4, "hf": 0.107834}, output_unit="cal/(mol K)", validity={},
  fitted_on="Pedersen oils 1,10,11,12,15 plus synthetic mixtures; 13 Colombian crudes", reported_accuracy="WPT within 0.0-1.6 K for literature oils (Table 6)",
  citation=C["escobar"], doi="", url=U["escobar"], access="full_text", where="Eqs 11-13", confidence="low",
  notes="Equations garbled in extraction; only dCp reading is reasonably sure. Melting form cannot be rebuilt.", _test={"M": 300.0, "Tf": 320.0}, _expect=None)
M(id="mahidol_nalkane_polys", name="Cubic polynomials for n-alkane Tm, Ttr, dHm, dHtr (thesis appendix)", target="melting_point",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "Cn"}],
  equation_text="Tm = 0.0028Cn^3 - 0.3185Cn^2 + 13.559Cn + 143.15 (Cn>16); Ttr = 0.0038Cn^3 - 0.4126Cn^2 + 16.741Cn + 99.885 (Cn>16); dHm = 0.0036Cn^3 - 0.2376Cn^2 + 7.4Cn - 34.814 kJ/mol (Cn>19); dHtr = -0.0032Cn^3 + 0.2353Cn^2 - 3.912Cn + 25.261 kJ/mol (Cn>19)",
  python="0.0028*Cn**3 - 0.3185*Cn**2 + 13.559*Cn + 143.15", coefficients={}, output_unit="K", validity={"Cn": [17, 40]},
  fitted_on="unattributed (likely Coutinho 1998 data set)", reported_accuracy="none", citation="Mahidol University thesis (1998), Appendix A, wax-oil gel deposition (Chulalongkorn repository copy).",
  doi="", url=U["chula"], access="full_text", where="Appendix A eqs A.1-A.9", confidence="low",
  notes="OCR doubtful; the dHm polynomial equals Coutinho eq 5 in kJ. Tm(20) = 309.3 K. Use only as a cross-check.", _test={"Cn": 20}, _expect=(309.33, 0.05))
M(id="jamali_oddeven_Tf", name="Odd/even n-alkane melting and transition correlations (as used in recent EoS wax papers)", target="melting_point",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "Cn"}],
  equation_text="even C10<Cn<=C42: Tf = 0.0031Cn^3 - 0.3458Cn^2 + 14.277Cn + 137.73 ; odd: Tf = 0.0122Cn^2 - 2.0861Cn - 775.598/Cn + 76.2189 ln(Cn) + 156.9 ; Cn>42: 414.3 (Cn-1.5)/(Cn+5) ; Ttr odd = 0.0039Cn^3 - 0.4239Cn^2 + 17.28Cn - ln(Cn) + 95.4 ; Ttr even (C22-C42) = 0.0032Cn^3 - 0.3249Cn^2 + 12.78Cn + ln(Cn) + 154.19 ; hsum = 0.167 M Tf + 432.47 cal/mol (C9<Cn<=C33) split 0.74 fusion / 0.26 transition",
  python="0.0031*Cn**3 - 0.3458*Cn**2 + 14.277*Cn + 137.73", coefficients={}, output_unit="K", validity={"Cn": [10, 42]},
  fitted_on="not stated in extract", reported_accuracy="not stated", citation="Jamali, R., Izadpanah, A.A., Rahideh, H. (2025). Thermodynamic modeling of wax formation temperature in paraffinic systems using cubic plus chain EoS. J Oil Gas Petrochem Technol, 12(1), 1-17; same set in Shariatrad et al. 2022 ACS Omega.",
  doi="10.22034/jogpt.2025.490790.1132", url=U["jamali"], access="full_text", where="melting and transition equations (numbers not legible)", confidence="low",
  notes="Even-alkane polynomial at C20 gives 309.7 K (measured 309.8). Odd form and range assignments are garbled; verify before use. Origin probably Ghanaei et al. 2007 or Esmaeilzadeh group.",
  _test={"Cn": 20}, _expect=(309.7, 0.3))

# ---------------- SLE formulations ----------------
M(id="sle_general", name="Solid-liquid equilibrium of a crystallising component", target="WAT",
  inputs=[{"name": "temperature", "unit": "K", "symbol": "T"}, {"name": "melting temperature", "unit": "K", "symbol": "Tf"},
          {"name": "fusion enthalpy", "unit": "J/mol", "symbol": "dHf"}, {"name": "heat capacity difference", "unit": "J/(mol K)", "symbol": "dCp"}],
  equation_text="ln(x_i^S gamma_i^S / (x_i^L gamma_i^L)) = dH_f,i/(R T) (1 - T/T_f,i) - dCp_i/R (T_f,i/T - 1 - ln(T_f,i/T)) + dV_i (P - Pref)/(R T)",
  python="dHf/(8.314462618*T)*(1 - T/Tf) - dCp/8.314462618*(Tf/T - 1 - np.log(Tf/T))", coefficients={}, output_unit="ln K (dimensionless)",
  validity={}, fitted_on="thermodynamic identity", reported_accuracy="n/a", citation="NeqSim wax characterisation documentation (Equinor); same form in Lira-Galeana 1996 Eq 6 and Coutinho 2006 Eqs 4 and 7.",
  doi="", url=U["neqdoc"], access="full_text", where="Solid-liquid equilibrium section", confidence="high",
  notes="Add dHtr/(R T)(1 - T/Ttr) when T < Ttr (Coutinho eq 7). Returns ln K_i = ln(x_s/x_l) for ideal phases. Implemented as thermo_wat.ln_Kpure.",
  _test={"T": 300.0, "Tf": 330.0, "dHf": 60000.0, "dCp": 0.0}, _expect=(2.1866, 0.001))
M(id="multisolid_wat_ideal_liquid", name="Multisolid WAT (pure solids, ideal liquid)", target="WAT",
  inputs=[{"name": "n-alkane mole fraction in the oil", "unit": "-", "symbol": "z"}, {"name": "melting temperature", "unit": "K", "symbol": "Tf"},
          {"name": "melting enthalpy (total)", "unit": "J/mol", "symbol": "dH"}],
  equation_text="Stability (Lira-Galeana Eq 3): f_i(P,T,z) - f_i^S,pure(P,T) >= 0. With ideal liquid: component i can freeze as pure solid when ln z_i >= -dH_i/(R T)(1 - T/T_f,i). WAT = max over i of the T solving ln z_i = -dH_i/(R T)(1 - T/T_f,i).",
  python="1.0/(1.0/Tf - 8.314462618*np.log(z)/dH)", coefficients={}, output_unit="K", validity={},
  fitted_on="derived; Lira-Galeana used PR EOS for the liquid, Coutinho and Daridon 2001 an ideal liquid", reported_accuracy="this study, test_thermo T3-T5: under-predicts measured WAT by 3 to 9 K (mean -4.9 K)",
  citation=C["lira"], doi="", url=U["lira"], access="full_text", where="Eq 3 and algorithm section", confidence="high",
  notes="Closed form when dCp = 0 and no transition: T = 1/(1/Tf - R ln z / dH). Minimum inputs: carbon number (or M) and mole fraction of each n-paraffin. Implemented as thermo_wat.wat_multisolid. Check: z=0.0073, Tf=365.3 K, dH=176.3 kJ gives 336.8 K (63.6 C) for nC50 in heptane, measured 57.5 C (Zhou 2026).",
  _test={"z": 0.0073, "Tf": 365.31, "dH": 176301.0}, _expect=(336.76, 0.05))
M(id="ideal_solid_solution_wat", name="Ideal solid solution cloud point (Pedersen 1995 wax phase)", target="WAT",
  inputs=[{"name": "wax-former mole fractions", "unit": "-", "symbol": "z"}, {"name": "K values", "unit": "-", "symbol": "K"}],
  equation_text="K_i = x_i^S/x_i^L = exp[dH_f,i/(R T)(1 - T/T_f,i) - dCp_i/R(T_f,i/T - 1 - ln(T_f,i/T))] ; WAT is the T where sum_i z_i K_i(T) = 1 (non-formers K = 0) ; solid amount from sum_i z_i (K_i - 1)/(1 + S(K_i - 1)) = 0",
  python="float(np.sum(np.asarray(z)*np.asarray(K)))", coefficients={}, output_unit="sum z K (equals 1 at WAT)", validity={},
  fitted_on="derived from the SLE with gamma = 1 in both phases (Pedersen 1995: SRK liquid, ideal wax)", reported_accuracy="this study: over-predicts measured WAT by 3 to 9 K with Coutinho properties (Dauphin A-C +5.5 to +6.8 K, Java crude +6 K)",
  citation=C["ped95"], doi="", url="https://www.osti.gov/biblio/6897238", access="abstract_only", where="abstract (model statement); criterion derived here",
  confidence="medium", notes="Implemented as thermo_wat.wat_ideal_solid_solution and solid_curve_ideal_ss. Pedersen 1991 used a regular solution solid with the solubility parameters above; Pedersen 1995 switched to ideal solid. Erickson et al. 1993 also used an ideal solid solution of n-paraffins (not opened).",
  _test={"z": [0.5, 0.3], "K": [1.2, 1.0]}, _expect=(0.9, 1e-9))
M(id="won_regular_solution", name="Won regular-solution activity coefficient", target="other",
  inputs=[{"name": "molar volume", "unit": "cm3/mol", "symbol": "V"}, {"name": "solubility parameter", "unit": "(cal/cm3)^0.5", "symbol": "d"},
          {"name": "mixture solubility parameter", "unit": "(cal/cm3)^0.5", "symbol": "dm"}, {"name": "temperature", "unit": "K", "symbol": "T"}],
  equation_text="ln gamma_i = V_i (delta_i - delta_bar)^2 / (R T), delta_bar = sum phi_j delta_j (volume fractions)",
  python="V*(d-dm)**2/(1.987204*T)", coefficients={"R_cal": 1.987204}, output_unit="ln gamma", validity={},
  fitted_on="Won 1986", reported_accuracy="Bhangale 2007 Table 6.4: Won model WAT within 0.15-0.83 K of Dauphin systems A-C", citation=C["won86"],
  doi="", url=U["neqdoc"], access="secondary_citation", where="NeqSim doc Won model; Bhangale Eq 4.16", confidence="high",
  notes="R in cal/(mol K) because V delta^2 is in cal/mol. Applied to both liquid and solid with the Pedersen 1991 delta_L and delta_S.", _test={"V": 360.0, "d": 8.0, "dm": 7.6, "T": 300.0}, _expect=(0.0966, 0.001))
M(id="bracket_ms_ss", name="Bracket interpolation between multisolid and ideal-solid-solution WAT (this study)", target="WAT",
  inputs=[{"name": "multisolid WAT", "unit": "K", "symbol": "Tms"}, {"name": "ideal solid solution WAT", "unit": "K", "symbol": "Tss"}],
  equation_text="WAT = Tms + f (Tss - Tms), f = 0.47", python="Tms + 0.47*(Tss - Tms)", coefficients={"f": 0.47}, output_unit="K", validity={},
  fitted_on="this study, 10 systems with known n-alkane composition: Dauphin A, B, C; Kurniawan Java crude A; 6 Shariatrad quaternary mixtures; Coutinho properties", reported_accuracy="in-sample MAE 0.8 K, max 2.7 K; f mean 0.55 sd 0.23 (median about 0.47)",
  citation="This study (agents/thermo/test_thermo.py T8). Not a published model.", doi="", url="", access="full_text", where="test_output.txt T8",
  confidence="low", notes="ASSUMPTION. A cheap stand-in for a non-ideal solid solution model (Coutinho P-UNIQUAC lies between the two limits). Not validated on crude oils with measured n-paraffin GC except one.",
  _test={"Tms": 304.02, "Tss": 315.54}, _expect=(309.43, 0.01))

# ---------------- characterisation ----------------
M(id="pedersen_split_1991", name="Pedersen wax-forming fraction of each pseudo-component (1991 constants)", target="n_paraffin_dist",
  inputs=[{"name": "pseudo-component molar mass", "unit": "g/mol", "symbol": "M"}, {"name": "pseudo-component density", "unit": "g/cm3", "symbol": "rho"}],
  equation_text="z_i^S = z_i^tot [1 - (A + B M_i) ((rho_i - rho_i^P)/rho_i^P)^C], rho_i^P = 0.3915 + 0.0675 ln M_i ; A = 1.074, B = 6.584e-4, C = 0.1915",
  python="1 - (1.074 + 6.584e-4*M)*np.clip((rho-(0.3915+0.0675*np.log(M)))/(0.3915+0.0675*np.log(M)),0,None)**0.1915",
  coefficients={"A": 1.074, "B": 6.584e-4, "C": 0.1915}, output_unit="fraction of pseudo-component that can form wax", validity={"M": [200, 900]},
  fitted_on="North Sea oils wax precipitation data (Pedersen et al. 1991), SRK with Peneloux", reported_accuracy="not stated in secondary text",
  citation=C["ped91"], doi="", url=U["neq"], access="secondary_citation",
  where="NeqSim PedersenWaxModel: comment 'A = 1.074, B = 6.584e-4, C = 0.1915'; the active code uses B = 6.584e-6", confidence="medium",
  notes="Clip to [0,1]. Very sensitive to B: with 6.584e-4 heavy fractions (M 556) keep almost no wax; with 6.584e-6 about a quarter. In test_thermo T6 untuned WAT for rho 0.85, M 230 is 20 C (1991) vs 73 C (NeqSim code). Pc of wax part = Pc (rho^P/rho)^3.46 (NeqSim calcPCwax).",
  _test={"M": 282.0, "rho": 0.869}, _expect=(0.155, 0.01))
M(id="pedersen_split_1995", name="Pedersen wax-forming fraction (1995 constants)", target="n_paraffin_dist",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}, {"name": "density", "unit": "g/cm3", "symbol": "rho"}],
  equation_text="same form; A = 0.8824, B = 5.353e-4, C = 0.1144", python="1 - (0.8824 + 5.353e-4*M)*np.clip((rho-(0.3915+0.0675*np.log(M)))/(0.3915+0.0675*np.log(M)),0,None)**0.1144",
  coefficients={"A": 0.8824, "B": 5.353e-4, "C": 0.1144}, output_unit="fraction", validity={"M": [200, 900]}, fitted_on="many oil samples (Pedersen 1995)",
  reported_accuracy="not stated", citation=C["ped95"], doi="", url=U["bhang"], access="secondary_citation", where="Bhangale 2007 Table 4.2 (text attributes scheme to Pedersen 1995)",
  confidence="medium", notes="Bhangale re-tuned to Dauphin data: A 0.5903, B 5.70e-4, C 0.1354 (Table 6.7).", _test={"M": 282.0, "rho": 0.869}, _expect=None)
M(id="ji_split", name="Ji re-fit of Pedersen wax-forming fraction", target="n_paraffin_dist",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "M"}, {"name": "specific gravity", "unit": "-", "symbol": "SG"}, {"name": "n-paraffin SG", "unit": "-", "symbol": "SGnp"}],
  equation_text="x_P = 1 - (A + B Mw_np) ((SG_SCN - SG_np)/SG_np)^C ; A = 0.8133, B = 5.737e-4, C = 0.1281",
  python="1 - (0.8133 + 5.737e-4*M)*np.clip((SG-SGnp)/SGnp,0,None)**0.1281", coefficients={"A": 0.8133, "B": 5.737e-4, "C": 0.1281},
  output_unit="fraction", validity={}, fitted_on="WDT data (Ji 2004)", reported_accuracy="not stated", citation=C["ji"], doi="",
  url=U["hw"], access="secondary_citation", where="Eq 1 and text", confidence="medium", notes="Ji gives non-paraffinic part a fusion temperature 70 K lower than the n-alkane of same carbon number.",
  _test={"M": 282.0, "SG": 0.869, "SGnp": 0.772}, _expect=None)
M(id="riazi_alsahhaf_SG", name="Riazi and Al-Sahhaf SCN specific gravity", target="density",
  inputs=[{"name": "SCN molar mass", "unit": "g/mol", "symbol": "M"}], equation_text="SG_SCN = 1.07 - exp(3.56073 - 2.93886 Mw^0.1)",
  python="1.07 - np.exp(3.56073 - 2.93886*M**0.1)", coefficients={"a": 1.07, "b": 3.56073, "c": 2.93886}, output_unit="SG", validity={"M": [90, 700]},
  fitted_on="SCN data (Riazi and Al-Sahhaf)", reported_accuracy="not stated", citation="Riazi, M.R., Al-Sahhaf, T.A. SCN property correlations (as quoted by Ameri Mahabadian et al.; primary not opened).",
  doi="", url=U["hw"], access="secondary_citation", where="Eq 2", confidence="medium", notes="M=96 gives 0.730 (LTB98-1 SCN7 0.733).",
  _test={"M": 96.0}, _expect=(0.7297, 0.002))
M(id="ji_wax_from_Mw", name="Total wax (nC20+) from molar mass", target="wax_content",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "Mw"}], equation_text="Wt%(nC20+) = 0.070 x Mw - 8.3", python="0.070*Mw - 8.3",
  coefficients={"a": 0.070, "b": -8.3}, output_unit="wt%", validity={"Mw": [150, 400]}, fitted_on="paraffinic waxy crudes (Ji); Mw basis not stated",
  reported_accuracy="'good estimation for paraffinic waxy crudes', use with care", citation=C["ji"], doi="", url=U["hw"], access="secondary_citation",
  where="Eq 4", confidence="low", notes="Gives a negative value for the light LTB98-1 oil. Which Mw (dead oil probably) is not stated.", _test={"Mw": 250.0}, _expect=(9.2, 1e-6))
M(id="nparaffin_decay", name="Exponential decay of n-paraffin mass distribution", target="n_paraffin_dist",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "n"}, {"name": "reference carbon number", "unit": "-", "symbol": "n0"},
          {"name": "wt% at n0", "unit": "wt%", "symbol": "w0"}, {"name": "decay ratio", "unit": "-", "symbol": "aD"}],
  equation_text="aD = Wt nC(n+1) / Wt nC(n) for n > 20 (constant); general value 0.88 when no data", python="w0*aD**(n-n0)",
  coefficients={"aD_default": 0.88}, output_unit="wt%", validity={"n": [20, 90]}, fitted_on="Coutinho and Daridon 2001 (about 30 crudes); Ji 2004", reported_accuracy="n/a",
  citation=C["hw"], doi="", url=U["hw"], access="secondary_citation", where="Eq 3", confidence="medium",
  notes="Not valid below C20 (distribution may not decay there). Coutinho and Daridon 2005 call ratios above 0.9 'large' (slow decay). Kurniawan 2013 Java crude: 1.03 rising C20-C26, 0.80 falling C26+.",
  _test={"n": 30, "n0": 20, "w0": 1.0, "aD": 0.88}, _expect=(0.2785, 0.001))
M(id="pedersen_exponential_scn", name="Pedersen exponential plus-fraction distribution", target="n_paraffin_dist",
  inputs=[{"name": "carbon number", "unit": "-", "symbol": "n"}, {"name": "A", "unit": "-", "symbol": "A"}, {"name": "B", "unit": "-", "symbol": "B"}],
  equation_text="ln(z_n) = A + B n ; density rho_n = C1 + C2 ln(n) ; constraints sum z_n = z_+ and sum z_n M_n / sum z_n = M_+",
  python="np.exp(A + B*n)", coefficients={}, output_unit="mole fraction", validity={"n": [7, 80]}, fitted_on="North Sea oils (Pedersen 1984)", reported_accuracy="n/a",
  citation=C["ped84"], doi="", url=U["neqchar"], access="secondary_citation", where="Pedersen model section", confidence="medium",
  notes="Implemented in thermo_wat.pedersen_exponential_scn with M_n = 14n - 4 (assumption).", _test={"n": 20, "A": -1.0, "B": -0.2}, _expect=(0.006738, 1e-5))
M(id="whitson_gamma", name="Whitson three-parameter gamma distribution of C7+", target="n_paraffin_dist",
  inputs=[{"name": "molar mass", "unit": "g/mol", "symbol": "Mx"}, {"name": "alpha", "unit": "-", "symbol": "a"}, {"name": "eta", "unit": "g/mol", "symbol": "eta"}, {"name": "mean C7+ molar mass", "unit": "g/mol", "symbol": "Mp"}],
  equation_text="p(M) = (M - eta)^(alpha-1) exp(-(M - eta)/beta) / (beta^alpha Gamma(alpha)), beta = (M_C7+ - eta)/alpha ; z_i = z_C7+ [P0(MU) - P0(ML)]",
  python="(Mx-eta)**(a-1)*np.exp(-(Mx-eta)/((Mp-eta)/a))/(((Mp-eta)/a)**a*__import__('math').gamma(a))", coefficients={"eta_typical": 84.0},
  output_unit="probability density per g/mol", validity={}, fitted_on="Whitson 1983", reported_accuracy="n/a", citation=C["whitson"], doi="SPE-12233-PA",
  url=U["neqchar"], access="secondary_citation", where="Whitson gamma section", confidence="high",
  notes="Typical alpha 0.5-1 condensates, 1-2 black oils, 2-4 heavy oils; eta 84-90 (NeqSim). alpha=1 reduces to exponential.", _test={"Mx": 200.0, "a": 1.0, "eta": 84.0, "Mp": 200.0}, _expect=(0.003171, 1e-5))
M(id="robustillo2012_C20plus", name="C20+ (total wax) content from API gravity and pour point", target="wax_content",
  inputs=[{"name": "API gravity", "unit": "deg API", "symbol": "API"}, {"name": "pour point", "unit": "C", "symbol": "PP"}],
  equation_text="ln(C20+ WPC) = 2.0137 + 0.03344 PP - 229.65279/API^2  (reconstructed, see notes)", python="np.exp(2.0137 + 0.03344*PP - 229.65279/API**2)",
  coefficients={"a": 2.0137, "b": 0.03344, "c": 229.65279}, output_unit="wt% C20+ (DSC wax precipitation curve basis)", validity={"API": [10.7, 45], "PP": [-38, 39]},
  fitted_on="20 crude oils (North Sea, North and West Africa, Middle East, Asia, Mediterranean, South America); validated on 12 more", reported_accuracy="average absolute deviation 0.8 wt% (fit), 0.6 wt% (validation)",
  citation=C["rob"], doi="10.1021/ef301190s", url=U["rob"], access="full_text", where="Eq 6, Tables 4 and 5",
  confidence="medium", notes="Equation text was garbled; the form was rebuilt from the printed fragments (0.03344, 229.65279, ln, 2.0137, exponent 2) and then checked: it reproduces all 32 'calculated' values in Tables 4 and 5 to within 0.1 wt% (rounding). PP below -38 C is set to -38 C. C20+ here is the DSC-based n-paraffin-like wax, much lower than precipitation wax (2-10x).",
  _test={"API": 36.77, "PP": 24.0}, _expect=(14.1, 0.06))

def run(m):
    t = m.pop("_test"); e = m.pop("_expect")
    if t is None:
        return
    py = m["python"]
    env = {"np": np, **{k: (np.asarray(v) if isinstance(v, list) else v) for k, v in t.items()}}
    val = eval(py, env)
    if e is not None:
        v = float(val)
        if abs(v - e[0]) > e[1]: print("MISMATCH", m["id"], v, e)
    m["notes"] = m["notes"] + f" [python check: inputs {t} -> {np.round(val, 4).tolist() if hasattr(val, '__len__') else round(float(val), 4)}]"

with open(os.path.join(HERE, "models.jsonl"), "w", encoding="utf-8") as f:
    for m in models:
        run(m)
        for k in ["id","name","target","inputs","equation_text","python","coefficients","output_unit","validity","fitted_on","reported_accuracy","citation","doi","url","access","where","confidence","notes"]:
            m.setdefault(k, "")
        f.write(json.dumps(m, ensure_ascii=False) + "\n")
print(len(models), "models written")
