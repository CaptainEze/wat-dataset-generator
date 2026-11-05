"""Write facts.jsonl and log.csv for the bulk agent. python3 -I make_facts.py"""
import csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
NOAA = "https://github.com/NOAA-ORR-ERD/noaa-oil-data"
NOAA_CIT = "NOAA Office of Response and Restoration (2024). ADIOS Oil Library data (noaa-oil-data, data/oil), incl. Environment and Climate Change Canada Crude Oil and Petroleum Product Database and Jokuty et al. catalogue records; statistics computed in this work (agents/bulk/noaa_stats.py)"
LOCAL_CIT = "This work: agents/bulk/bulk_pool_clean.csv built from master_v9.csv and the harvest bulk pools (agents/bulk/build_pool.py)"
ROB = "Robustillo, M.D., Martos, C., Espada, J.J., and Coto, B. (2012). Assessment of different methods to determine the total wax content of crude oils. Energy and Fuels, 26, 6352-6357."
ROB_URL = "https://burjcdigital.urjc.es/bitstreams/49e877cc-f97e-43c1-9119-d7c433729b55/download"
F = []


def f(id_, subj, obj, rel, mag, lo, hi, unit, cond, n, cit, doi, url, access, where, conf, notes):
    F.append(dict(id=id_, subject=subj, object=obj, relation=rel, magnitude=mag, value_low=lo, value_high=hi, unit=unit,
                  conditions=cond, n_oils=n, citation=cit, doi=doi, url=url, access=access, where=where, confidence=conf, notes=notes))


# Density harmonisation
f("rho15_minus_rho60", "density_15C", "density_60F", "offset", "rho15 - rho60 = +0.35 to +0.45 kg/m3 (API 15 to 55)", 0.35, 0.45, "kg/m3",
  "API MPMS 11.1-2004 crude oil group, computed with bulk_relations.ctl_api2004", None,
  "API MPMS Ch. 11.1 (2004), computed in this work", "", "https://github.com/m2b/API11_1VCF", "secondary_citation", "bulk_relations.py", "high",
  "Density at 15 C and at 60 F (15.56 C) differ by under 0.5 kg/m3, so they can be pooled for ML, but convert API to density15 with the standard, not with SG x 1000.")
f("rho15_minus_rho20", "density_15C", "density_20C", "offset", "rho15 - rho20 = +3.2 (API 15) to +4.1 (API 55) kg/m3; 3.6 kg/m3 at API 35", 3.18, 4.06, "kg/m3",
  "API MPMS 11.1-2004 and 1980 Table 54A crude oil (K0 = 613.9723) agree within 0.002 kg/m3", None,
  "API MPMS Ch. 11.1 (2004) and ASTM D1250-80, computed in this work", "", "https://github.com/m2b/API11_1VCF", "secondary_citation", "bulk_relations.py", "high",
  "master_v9 has 76 rows with density at 20 C; correcting them shifts density by about -3.6 kg/m3 (about +0.7 API).")
f("alpha60_crude", "thermal_expansion_alpha60", "API", "increases", "alpha60 = 3.66e-4 (15 API), 4.73e-4 (35 API), 5.94e-4 (55 API) per F", 3.66e-4, 5.94e-4, "1/F",
  "alpha60 = 341.0957/rho60*^2, crude oil group", None, "API MPMS Ch. 11.1 (2004), computed", "", "https://github.com/m2b/API11_1VCF", "secondary_citation", "", "high", "")
# Viscosity
f("walther_interp_accuracy", "walther_interpolation", "viscosity", "range", "mean abs error 3.6 %, median 0.36 %, p90 12 % when predicting a middle temperature from two outer ones", 0.36, 12.0, "% abs error",
  "156 fresh crude oils with 3 or more kinematic viscosities, all above pour point + 5 C, ASTM D341 with low-viscosity terms", 156,
  NOAA_CIT, "", NOAA, "full_text", "this work", "high", "Supports converting visc at two temperatures to 40 C when 40 C lies between them; extrapolation is less safe.")
f("deadoil_corr_perf_noaa", "dead_oil_viscosity_correlations", "viscosity", "range",
  "at 40 C (104 F), API 15 to 55: median abs % error Kartoatmodjo 20.0, Ng-Egbogah 20.3, Glaso 20.6, Labedi 21.0, Beal 22.5, Petrosky 26.4, Naseri 27.9, Beggs-Robinson 85.7, De Ghetto 128.8; log10 bias Glaso -0.09, Ng-Egbogah -0.09, Beggs-Robinson +0.19",
  20.0, 128.8, "% median abs error", "NOAA fresh crudes with measured or interpolated visc40, converted to cP with density at 40 C", 293,
  NOAA_CIT, "", NOAA, "full_text", "this work", "high", "Scatter of all API-only correlations is about 0.29 log10 units (factor 2), so API alone fixes viscosity only to within a factor of about 2.")
f("deadoil_corr_perf_local", "dead_oil_viscosity_correlations", "viscosity", "range",
  "at 40 C: median abs % error Ng-Egbogah 24.1, Glaso 24.3, Kartoatmodjo 24.9, Labedi 24.9, Petrosky 26.8, Naseri 28.9, Beal 37.6, Beggs-Robinson 103, De Ghetto 163; log10 bias Ng-Egbogah -0.008, Glaso -0.005, residual sd 0.22 to 0.23",
  24.1, 163.0, "% median abs error", "local cleaned pool, API 15 to 55", 168, LOCAL_CIT, "", "", "full_text", "this work", "high",
  "Ng and Egbogah (or Glaso) at 104 F with a log-normal spread of sd 0.23 log10 is a reasonable generator for visc40 given API.")
f("beggs_robinson_low_T", "Beggs_Robinson_correlation", "viscosity", "threshold", "overpredicts below about 75 F (PetroWiki) or below about 100 to 150 F (IHS)", 75, 150, "F",
  "dead oil", None, "SPE PetroWiki, Oil viscosity page; IHS Harmony Enterprise documentation, Oil correlations", "", "https://petrowiki.spe.org/Oil_viscosity", "full_text",
  "Beggs and Robinson paragraph", "medium", "Our 104 F test confirms a +0.19 to +0.27 log10 bias.")
f("alomair_validity_table", "dead_oil_viscosity_correlations", "viscosity", "range",
  "AARD on 11.7 to 18.8 API Kuwaiti heavy oils: Standing 39.8 %, Naseri 76 %, Beggs-Robinson 76.8 %, Elsharkawy-Alikhan 99.5 %, Hossain 119 %, Kartoatmodjo 123 %, Petrosky 125 %, Glaso 459 %, Labedi 2884 %, Beal 6421 %",
  39.8, 6420.6, "% AARD", "heavy oils 20 to 160 C, 1.7 to 11322 cP", None,
  "Alomair, O., Jumaa, M., Alkoriem, A., and Hamed, M. (2016). Heavy oil viscosity and density prediction at normal and elevated temperatures. J. Petrol. Explor. Prod. Technol., 6, 253-263.",
  "10.1007/s13202-015-0184-8", "https://link.springer.com/content/pdf/10.1007/s13202-015-0184-8.pdf", "full_text", "Tables 7, 8, 10", "high",
  "Also lists validity ranges (API, T, cP) of each correlation; used in models.jsonl.")
# Joint distributions NOAA
f("noaa_api_dist", "API", "crude_population", "range", "median 34.4, p10 21.3, p90 45.1, mean 33.9, sd 9.7", 21.3, 45.1, "deg API", "fresh crude oils, condensates and tight oils", 1134,
  NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md NOAA section", "high", "")
f("noaa_pour_dist", "pour_point", "crude_population", "range", "median -12 C, p10 -43, p90 15.3, mean -12.7, sd 22.8", -43, 15.3, "C", "uncensored pour points", 1008,
  NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md", "high", "Population is skewed to low-wax oils compared with our WAT data (local median pour +2 C).")
f("noaa_wax_dist", "wax_content", "crude_population", "range", "median 4.8 wt%, p10 1.0, p90 10, mean 5.6, max 32", 1.0, 10.0, "wt%", "methods mixed, mostly Environment Canada and legacy ADIOS", 423,
  NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md", "high", "Local pool wax is higher: median 8.7, p90 28.4 wt% (WAT papers favour waxy oils).")
f("noaa_visc40_dist", "viscosity_40C", "crude_population", "range", "log10 visc40 median 0.78 (6.0 cSt), p10 0.18 (1.5 cSt), p90 1.96 (91 cSt)", 1.5, 91, "cSt", "measured or Walther-interpolated", 314,
  NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md", "high", "")
f("noaa_corr_wax_pour", "wax_content", "pour_point", "increases", "Spearman 0.49, Pearson 0.51; pour = -24.0 + 2.54 x wax, residual sd 19.4 C", 0.49, 0.51, "correlation",
  "NOAA fresh crudes", 395, NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md", "high", "Local pool: Spearman 0.69 (n 143), see local_pool_stats.md for the local linear fit.")
f("noaa_corr_api_wax", "API", "wax_content", "equals", "no monotonic relation: Spearman -0.01 (NOAA n 423), -0.02 (local n 155); wax peaks at 30 to 40 API (median 5.2 wt%) and falls below 20 API (2.5) and above 50 API (0.7)", -0.01, -0.01, "correlation",
  "NOAA and local pools", 423, NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md wax by API class", "high", "Generator should sample wax nearly independently of API, with a hump-shaped conditional median.")
f("noaa_corr_api_pour", "API", "pour_point", "equals", "near zero: Spearman 0.01 (NOAA n 1008), -0.05 (local n 287)", -0.02, 0.01, "correlation", "NOAA and local pools", 1008, NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md", "high", "")
f("noaa_corr_api_visc", "API", "viscosity_40C", "decreases", "Spearman -0.92 with log10 visc40; log10 visc40 = 3.323 - 0.0701 API, residual sd 0.363 (NOAA n 308); local pool 2.641 - 0.0526 API, sd 0.324 (n 176)", -0.92, -0.85, "correlation",
  "10 < API < 60", 308, NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md", "high", "")
f("noaa_corr_sulphur", "sulphur", "API", "decreases", "Spearman -0.67 with API (n 313); +0.64 with log10 visc40 (n 131); -0.20 with pour point; -0.23 with wax", -0.67, 0.64, "correlation", "NOAA", 313, NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md", "high", "")
f("noaa_corr_pour_visc", "viscosity_40C", "pour_point", "equals", "weak: Spearman 0.02 (NOAA n 292), 0.05 (local n 165)", 0.02, 0.02, "correlation", "", 292, NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md", "high",
  "Pour point and viscosity are nearly independent across crudes once API is not controlled.")
f("noaa_pour_by_wax", "wax_content", "pour_point", "range", "median pour by wax class: 0-2 wt% -30 C; 2-4 -15; 4-6 -6; 6-10 -6; 10-15 +12; 15-40 +30 C", -30, 30, "C", "NOAA", 395, NOAA_CIT, "", NOAA, "full_text", "local_pool_stats.md pour by wax class", "high",
  "p10 to p90 spread is about 40 to 60 C within each class.")
# Wax methods
f("wax_precip_vs_dsc", "wax_method_precipitation", "wax_content", "offset", "precipitation minus DSC = +2.2 to +20.5 wt%, median +8.5; precipitation/DSC ratio median 3.5 (1.8 to 14)", 2.2, 20.5, "wt%",
  "24 crudes, API 10.8 to 45, solvent precipitation vs DSC; HTGC and DSC agree (median difference 0.2 wt%, mean abs 1.3 wt%, 19 crudes)", 23, ROB, "10.1021/ef301190s", ROB_URL, "full_text", "Tables 1 to 3", "high",
  "Precipitation methods (UOP 46 type) trap oil in the solid. Wax values from different methods should carry a method flag or be harmonised before pooling.")
f("robustillo_c20_api_pp", "pour_point", "wax_content", "increases", "C20+ (DSC wax) correlated with API and pour point (Eq 6); tabulated outputs scale as exp(0.03344 x PP) at fixed API", 0.6, 0.8, "wt% average abs deviation",
  "API 10.7 to 42.6, PP -38 to 39 C; fit 20 crudes (delta 0.8 wt%), validation 12 crudes (delta 0.6 wt%)", 32, ROB, "10.1021/ef301190s", ROB_URL, "full_text", "Section 3.3 Eq 6, Tables 4 and 5", "medium",
  "Eq 6 text was garbled in extraction (visible constants 229.65279, 2.0137, 0.03344, a natural log). The exp(0.03344 PP) factor was inferred by us from the tabulated calculated values (ratio C/exp(0.03344 PP) is a smooth function of API only). Needs the primary PDF to finish.")
# Standards precision / validity
f("d2502_precision", "ASTM_D2502", "molecular_weight", "range", "repeatability 3 g/mol, reproducibility 25 g/mol; scope MW 250 to 700", 3, 25, "g/mol", "average petroleum fractions", None,
  "ASTM D2502-92(2002) Standard Test Method for Estimation of Molecular Weight of Petroleum Oils From Viscosity Measurements (official preview)", "",
  "https://cdn.standards.iteh.ai/samples/23092/b14826d85cdd4755a615c78135051b7e/ASTM-D2502-92-2002-.pdf", "full_text", "Sections 1.1, 6.1", "high", "")
f("riazi_daubert_visc_ranges", "Riazi_Daubert_viscosity_correlations", "molecular_weight", "range", "valid for M 200 to 800, v100 2 to 18000 cSt, v210 1 to 180 cSt, SG 0.82 to 1.08", 200, 800, "g/mol", "heavy fractions", None,
  "Gomez, J.V. (1996). New equations predict boiling point from viscosity, gravity. Oil and Gas Journal, 7 Oct 1996.", "",
  "https://www.ogj.com/home/article/17234322/new-equations-predict-boiling-point-from-viscosity-gravity", "full_text", "text", "medium",
  "Gomez's Newton-Raphson Tb from (v100, v210, SG) has about 1 % average error on 107 fractions; equations are images, not read.")
f("ec_ans_pour_censoring", "pour_point", "measurement", "threshold", "7 Alaska North Slope light samples (API 53 to 58) reported pour <= -28 C (censored)", -28, -28, "C", "local ans2 pool", 7,
  LOCAL_CIT, "", "", "full_text", "ans2/alaska_no_wat_samples.csv", "high", "Treat as upper bounds, not values.")

with open(os.path.join(HERE, "facts.jsonl"), "w") as fh:
    for x in F:
        fh.write(json.dumps(x, ensure_ascii=False) + "\n")
print(len(F), "facts")

LOG = [
    ("https://link.springer.com/content/pdf/10.1007/s13202-015-0184-8.pdf", "Alomair et al. Heavy oil viscosity and density prediction", 2016, "used", "validity and AARD tables; no equations"),
    ("https://petrowiki.spe.org/Oil_viscosity", "PetroWiki Oil viscosity", "", "used", "qualitative notes and references; equations not in page text"),
    ("https://www.vurup.sk/na_stiahnutie/new-viscosity-correlations-dead-crude-oils/", "Sattarin et al. New viscosity correlations for dead crude oils (Petroleum and Coal 49(2))", 2007, "used", "equations garbled; used only to cross-check Naseri and ranges"),
    ("https://distantreader.org/stacks/journals/ijcpe/ijcpe-290.pdf", "Abdulmajeed. New viscosity correlation for Iraqi oil fields", 2014, "no_content", "equations lost in extraction"),
    ("https://journal.su.edu.ly/index.php/susj/article/download/2800/2266/5151", "Arwini. Assessment of oil viscosity correlations for Libyan crudes", 2024, "no_content", "names only"),
    ("https://www.ihsenergy.ca/support/documentation_ca/Harmony_Enterprise/latest/content/html_files/ref_materials/calculations/oil_correlations.htm", "IHS Harmony Enterprise oil correlations", "", "used", "ranges and descriptions; equations are images"),
    ("https://www.ihsenergy.ca/support/documentation_ca/WellTest/content/html_files/reference_materials/calculations_correlations/oil_correlations.htm", "IHS WellTest oil correlations", "", "used", "Ng-Egbogah pour point version exists (image eq420.svg not readable)"),
    ("https://www.ihsenergy.ca/support/documentation_ca/WellTest/content/generatedimages/equations/equation420.svg", "Ng-Egbogah pour point equation image", "", "unreachable", "fetch error; shell blocked"),
    ("https://www.ihsenergy.ca/support/documentation_ca/Harmony/content/html_files/reference_material/calculations_and_correlations/oil_correlations.htm", "IHS Harmony oil correlations", "", "no_content", "equations are PNG images"),
    ("http://fekete.com/SAN/TheoryAndEquations/WellTestTheoryEquations/Ng_and_Egbogah.htm", "Fekete Ng and Egbogah", "", "unreachable", "robots disallowed"),
    ("https://www.mdpi.com/1996-1073/14/4/930", "Hadavimoghaddam et al. Prediction of dead oil viscosity ML vs classical", 2021, "no_content", "Table 1 is an image; PDF returned binary"),
    ("https://www.redalyc.org/journal/5722/572261628002/572261628002.pdf", "Marin Velasquez. Viscosity model heavy dead crudes Monagas (Enfoque UTE 8(3))", 2017, "used", "Glaso, Bennison, Naseri cross-check"),
    ("https://intechopen.com/chapters/40684", "Al-Rawahi et al. Viscosity correlation Omani Fahud crude", 2012, "used", "Appendix A Beal, B-R, Glaso, Labedi, Kartoatmodjo (garbled signs)"),
    ("https://biblat.unam.mx/hevila/Ingenieriapetrolera/2019/vol59/no2/3.pdf", "Arzapalo et al. Evaluation of viscosity correlations 10-16 API Gulf of Mexico", 2019, "no_content", "Appendix A equations missing in extraction"),
    ("https://ctyf.journal.ecopetrol.com.co/index.php/ctyf/article/view/319", "Pertuz Parra et al. Extra-heavy oil viscosity Colombia", 2014, "no_content", "landing page only"),
    ("https://katalog.lib.cas.cz/KNAV/EdsRecord/edsair,edsair.doi...........8e2064776f8c772ea7085bd09bd133cc", "Ng and Egbogah improved temperature-viscosity correlation (catalogue)", 1983, "unreachable", "bot protection"),
    ("https://www.oiml.org/en/files/pdf_r/r063-e94.pdf", "OIML R 63 Petroleum measurement tables", 1994, "no_content", "index of tables only"),
    ("https://www.ogj.com/home/article/17234322/new-equations-predict-boiling-point-from-viscosity-gravity", "Gomez. New equations predict boiling point from viscosity, gravity (OGJ)", 1996, "used", "ranges; equations are images"),
    ("https://cpme.tu.edu.iq/images/mhadrat-mkhtlft/م.م_جاسم/خواص_مواد_3/lec-9.pdf", "Tikrit University lecture 9 petroleum properties", "", "unreachable", "robots disallowed"),
    ("https://cdn.standards.iteh.ai/samples/23092/b14826d85cdd4755a615c78135051b7e/ASTM-D2502-92-2002-.pdf", "ASTM D2502-92(2002) preview", 2002, "used", "scope, precision, worked example"),
    ("https://jawchemist.blogspot.com/p/mw-calc-full.html", "JAWChemist. Calculation to estimate the molecular weight (D2502 chart model)", 2020, "used", "Hirschler equations"),
    ("https://burjcdigital.urjc.es/items/6c1b9103-8f17-42eb-8794-93c92675e3d9/full", "Robustillo et al. Assessment of methods for total wax content (record)", 2012, "used", "abstract"),
    ("https://burjcdigital.urjc.es/bitstreams/49e877cc-f97e-43c1-9119-d7c433729b55/download", "Robustillo et al. 2012 full text", 2012, "used", "Tables 1-5; Eq 6 garbled"),
    ("https://api.openalex.org/works?search=pour%20point%20correlation%20crude%20oil%20wax%20content%20API%20gravity", "OpenAlex search pour point wax API", "", "used", "lead list"),
    ("https://github.com/NOAA-ORR-ERD/noaa-oil-data", "NOAA ADIOS Oil Library data", 2024, "used", "1134 fresh crude records extracted"),
    ("https://github.com/m2b/API11_1VCF", "API 11.1 VCF implementation with standard examples", "", "used", "2004 crude procedure and Example 1, 2"),
    ("https://github.com/jjgomera/pychemqt", "pychemqt petro.py", "", "used", "API TDB 11A4.2, 11A4.4, 2B8.1, Riazi-Daubert"),
    ("https://github.com/zentechnologygroup/pvt-cpp", "pvt-cpp dead-oil viscosity correlations", "", "used", "Beal, B-R, Ng-Egbogah, Glaso, Kartoatmodjo, Naseri, Petrosky, De Ghetto"),
    ("https://github.com/EverJRamosI/petpropy", "petpropy oil viscosity", "", "used", "cross-check"),
    ("https://github.com/mwburgoyne/pyResToolbox", "pyResToolbox", "", "no_content", "Beggs-Robinson only"),
    ("https://github.com/yohanesnuwara/reservoir-engineering", "reservoir-engineering notebooks", "", "used", "Beggs-Robinson exp form, Egbogah"),
    ("https://github.com/Kandimus/tritonn", "tritonn density.h", "", "used", "1980 K0 constants (via code search)"),
]
with open(os.path.join(HERE, "log.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["url", "title", "year", "status", "notes"])
    w.writerows(LOG)
print(len(LOG), "log rows")
