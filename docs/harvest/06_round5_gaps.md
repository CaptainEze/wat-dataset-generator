# Addendum: gap round (methods, condensates, heavy oils, regions, theses, supplementary data) and master v9 (4 Nov 2026)

## Result
Six agents, about 250 sources. Open data is close to exhausted for these areas. Added 65 rows but only 3 usable (SEA-2 L tier B, Colorado COL-25 and COL-33 tier B-); 58 pending (tier P) and 4 high-pressure (tier X).

## Master v9 (data/master/wat_master.csv)
347 rows, 260 oils. Usable 246 rows (203 oils). Core3 (density or API, pour, wax) 148 rows, 131 oils.

## Findings by area
- Methods: no open round-robin or interlaboratory WAT study exists. Multi-method papers are paywalled or image tables.
- Condensates: only the KG-D6 Reliance assays.
- Heavy oils: master already holds the open ones.
- Regions: Southeast Asia (SEA-2 L, tier B). Vietnam X-field blend and Mae Soon pending, no density.
- Theses: 50 pending rows (Bouzas 2011 ten Spanish crudes DSC and FTIR, Shahruddin 2019 Malaysian CPM, Uzen wells ultrasonic onset, Salehi 2021 nine Iranian crudes). None has density or API.
- Supplementary and ML repositories: nothing on GitHub, Mendeley, Zenodo, Kaggle or Hugging Face held crude WAT data.
- Possible swap: Ridzuan 2020 gives Kerteh WAT 11 C and pour point 28 C; master R36 has the reverse. Flagged.

## Decisions made in the merge
- All Uzen wells share one oil_group `uzen`; Shahruddin Penara rows share `penara`; Colorado rows share `colombia_colorado`.
- Mae Soon duplicates removed. Luliang (WAT 29 C) held: unclear if crude or deposit.

## Unopened leads
Sudan SUST thesis Table.pdf (repository.sustech.edu 3532); Nazarbayev ML thesis; UNICAMP 2016; UFBA 2017; Sousa 2023 Energies 16:406 (17 Brazilian crudes by CPM and DSC, image table); Kok 1996; Ronningsen 1991; Li and Zhang 2003; Springer s13202-018-0480-1 (12 Iranian oils); Kouhi 2025 Fuel 380:133146; ACS Omega 10.1021/acsomega.5c06286, 4c10540, 4c10044; Tarim condensates s13202-023-01716-0; Reliance KG-D6 crude assays (images).
