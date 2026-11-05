# WAT data harvest log (updated 4 Nov 2026, evening)

## Where the dataset stands (wat_master_v3.csv)
- 196 rows, 172 oil groups. Tiers: A 17, A- 8, B 18, B- 122, C 9, P (pending) 19, X (excluded) 3.
- Usable for modelling (not P, X or D, WAT present): 174 rows, 154 oils.
- With density or API, pour point and wax (core3): 126 rows, 113 oils. Adding viscosity at 40 C (core4): 21 rows, 19 oils.
- Oils with two or more WAT methods: 11.
- Coverage of the usable rows: North Africa 65 rows (59 are Benamara), Asia-Pacific 54, South America 17, West Africa 13, North America 9, Central Asia 5, Europe 4, Middle East 1. By API class: above 40 API 73 rows, 30 to 40 API 48, 20 to 30 API 29, under 20 API 10.
- New columns in v3: density_T_c (temperature at which density was measured), qc_flags, harvest_id (original agent row), verified (double-entry status).

## How round 2 was run (for the methodology chapter)
1. A shared brief fixed the columns, units, tiers, controlled WAT method vocabulary and extraction rules (copy only stated values; no inference; one row per oil and method pair; plausibility flags; censored values marked).
2. Eight agents searched in parallel by territory: West and Central Africa, North Sea and Europe, Middle East and North Africa and Central Asia, Asia-Pacific, the Americas, open repositories and compilation papers, method-comparison studies, and crude-type balance. Each wrote its own rows file and a source log, never the master.
3. Every source opened was logged with a status. Round 2 log: 422 entries, 340 unique URLs. By best status per URL: no WAT in source 137, unreachable 79, duplicate 39, rejected 39, extracted 34, image table 12.
4. Merge: 146 new rows. 11 cross-agent duplicates removed. 4 master tier C rows upgraded to their primary papers (Mt McKyle; Nigeria A, B, C). 4 Khalda rows held as pending because two readers got different table values. Ranges entered as midpoints (rule to confirm with Patrick).
5. Independent double entry: 51 rows from 33 sources were re-read blind by separate checkers who were not shown the first values. 195 field comparisons: 175 agreed. 2 differed only by cooling rate chosen (Libya DSC at 1 and 3 K/min). 18 were blanks on one side: 8 densities the first reader had missed (now filled), 6 about what counts as wax or pour (n-alkanes by GC is not total wax; censored pour below -24 C), and 4 about whether a printed range or 'waxing point' is a WAT. No transcription typos were found. Checkers read pages through a fetch tool that summarises text, so values are one step removed from the PDFs; a spot check against PDFs is still advisable. Only 51 of the 135 new or upgraded rows were checked; the rest are marked not_checked.

## Main cautions
- Benamara et al. (59 Algerian crudes) supplies 59 of the 113 core3 oils. Fields are not named, density is at 20 C, WAT came from a rotational pour point tester (torque slope change), and the source has no API or viscosity. Report results with and without it. One row in the source has a freezing point above its pour point, probably a typo.
- Viscosity at 40 C is present in only 24 usable rows, so a viscosity-free model should be the main one.
- Density temperature varies (76 rows at 20 C, others at 15, 40 or 80 C, three unknown). Harmonisation rule needs Patrick.
- Oliveira 2018 (9 Brazilian oils): wax column is the GC n-alkane sum, a proxy, flagged.
- Method labels still hold free text in many rows and must be collapsed to a controlled list before modelling.
- Plausibility flags (WAT minus pour above 40 C or below 0): 11 rows kept for the cleaning step.
- Heavy oils (under 20 API) and condensates are thin. No agent found a condensate with a stock tank WAT beyond those already held.

## Still pending (at v3; see later addenda)
- Alaska North Slope (Anyanwu 2007): 37 rows built but not merged (completed in v8).
- Held out: Kouhi and Khodapanah 2022 (114 rows, tier D, not for training).
- DISKOS text corpus: the chunks already on disk gave nothing usable (OCR stripped numbers). The 5.7 GB scan is still worth running but expect a small yield (src/scripts/harvest/scan_diskos_v2.py).

## Blocked sources to open in a browser
- Ronningsen et al. 1991 parts 1 and 3 (17 North Sea crudes): orbit.dtu.dk record.
- Equinor crude assay files (Heidrun, Draugen, Norne, Skarv, Alvheim, Oseberg, Statfjord, Gullfaks).
- Joseph and Oyinkuro 2025 (Niger Delta, Egypt J Petrol); Kok 1996 (15 Turkish crudes, doi 10.1016/0016-2361(96)00046-4); Kok and Nurgaliev 2018 (8 Turkish crudes); Elsharkawy 2000 (SPE 54006).
- Energies 2019 12(6):967 (WAT by region table is an image); Alcazar-Vara 2011 and Coto 2014 (primaries for Mexico and South America rows).
- PMC pages behind a robot check: PMC9161395, PMC13425321, PMC8506093, PMC12878762.

## Open decisions for Patrick
- Harmonising density and viscosity measured at non-standard temperatures to a common basis.
- Whether tier C rows, lab blends (BZ25-1), censored pour points and the Benamara torque-slope method stay in training.
- A WAT given as a range: midpoint (current) or exclude.
- Rheometer flow-curve WAT labelled as viscometry.
- How to treat a GC n-alkane sum as a wax-content proxy.

## Earlier rounds (rows R01 to R65)
- Company assays and tenders (Medanito, MJ-N4A, Das Blend, Brent, Albacora Leste), DOE/Tulsa BC15150, Kelechukwu 2011 (Malaysia), Sigitov 2014 (Kazakhstan), Chulalongkorn thesis (Thailand), DJ crude (5 WAT methods), Sharma 2016, Dong 2022, Bohai Bay BZ25-1, PETRONAS Kerteh, Dehloran, Palermo Brazil, Dabei condensates, Taiwo 2012, Uba 2004 (SPE 88963), Mmata 2018 (SPE-193459-MS, excluded: live fluid).
- No usable WAT in: TotalEnergies and Tullow assay sheets (WAT field blank), Ceypetco, ExxonMobil Usan, Jokuty 1996, USGS/NETL 9,076-oil database, Sodir Troll sample, Sudanese thesis tables, Akinyemi 2016.
- WellDatabase (US/Canada well headers and production): every export and document tool is behind a paywall and the data has no fluid properties.
