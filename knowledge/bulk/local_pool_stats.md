# Local bulk pool statistics

Built by agents/bulk/build_pool.py from master_v9.csv, harvest4 nigeria_bulk_only_raw.csv, harvest6 round3_bulk_only_raw.csv, harvest/assays totalenergies_whole_crude_all.csv and ans2 alaska_no_wat_samples.csv. Density at other temperatures corrected to 15 C with the 1980 crude-oil tables form (K0 = 613.9723). Missing API or density filled from the other with API MPMS 11.1-2004. Viscosity at 40 C converted with ASTM D341 (Walther) only where two kinematic values at other temperatures were stated; those rows say so in notes.

Raw records: 612. Distinct crudes after merging same name and same rounded API: 374.

## Records per source (raw)

| source | records |
|---|---|
| master_v9 | 347 |
| nigeria_bulk | 131 |
| round3_bulk | 81 |
| totalenergies | 46 |
| alaska_ans2 | 7 |

## Univariate summary of the cleaned pool (one row per distinct crude)

| variable | n | mean | sd | min | p10 | p25 | median | p75 | p90 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| api15 | 341 | 34.9 | 10.1 | 11.8 | 22.8 | 28.1 | 34.9 | 41 | 46.4 | 77.5 |
| density15 | 341 | 853 | 51.3 | 677 | 795 | 820 | 850 | 886 | 918 | 987 |
| visc40_cSt | 176 | 57.9 | 408 | 0.515 | 1.79 | 2.71 | 5.33 | 13.4 | 44.2 | 5.09e+03 |
| pour_c | 301 | -1.61 | 25.1 | -78 | -36 | -18 | 2 | 15 | 30 | 60 |
| wax_wt_pct | 175 | 12.5 | 10 | 0 | 2.19 | 4.82 | 8.7 | 18.6 | 28.4 | 41 |
| sulphur | 45 | 0.487 | 0.575 | 0.0019 | 0.0642 | 0.146 | 0.243 | 0.628 | 1.04 | 2.52 |
| log10_visc40 | 176 | 0.842 | 0.618 | -0.288 | 0.254 | 0.433 | 0.726 | 1.13 | 1.64 | 3.71 |

## Pairwise pearson correlations (pairwise complete; n in brackets)

| | api15 | pour_c | wax_wt_pct | sulphur | log10_visc40 |
|---|---|---|---|---|---|
| api15 | 1 | -0.15 (287) | -0.01 (155) | -0.56 (45) | -0.85 (176) |
| pour_c | -0.15 (287) | 1 | 0.60 (143) | 0.19 (45) | 0.11 (165) |
| wax_wt_pct | -0.01 (155) | 0.60 (143) | 1 | n<5 | 0.09 (56) |
| sulphur | -0.56 (45) | 0.19 (45) | n<5 | 1 | 0.61 (45) |
| log10_visc40 | -0.85 (176) | 0.11 (165) | 0.09 (56) | 0.61 (45) | 1 |

## Pairwise spearman correlations (pairwise complete; n in brackets)

| | api15 | pour_c | wax_wt_pct | sulphur | log10_visc40 |
|---|---|---|---|---|---|
| api15 | 1 | -0.05 (287) | -0.02 (155) | -0.85 (45) | -0.91 (176) |
| pour_c | -0.05 (287) | 1 | 0.69 (143) | 0.32 (45) | 0.05 (165) |
| wax_wt_pct | -0.02 (155) | 0.69 (143) | 1 | n<5 | 0.17 (56) |
| sulphur | -0.85 (45) | 0.32 (45) | n<5 | 1 | 0.89 (45) |
| log10_visc40 | -0.91 (176) | 0.05 (165) | 0.17 (56) | 0.89 (45) | 1 |

## Completeness of input combinations (cleaned pool)

- api+pour: 287 crudes
- api+pour+wax: 136 crudes
- api+pour+visc40: 165 crudes
- api+pour+wax+visc40: 54 crudes
- api+visc40: 176 crudes
- api+wax: 155 crudes

## Simple fitted relations on the cleaned pool (for consistency checks, not physics)

- log10(visc40 cSt) = 2.641 + (-0.0526) x API; n = 176, residual sd = 0.324 log10 units
- pour_c = -10.49 + 1.353 x wax_wt_pct; n = 143, residual sd = 18.7 C
- pour_c = -6.27 + (-0.133) x API + 1.297 x wax; n = 136, residual sd = 18.1 C

## Caveats

- Wax content methods differ (UOP 46 acetone precipitation, HTGC, DSC, not stated). Values are pooled as reported.
- Some pour points are upper bounds (ASTM D5853 maximum, or censored such as "below -28 C"); see notes.
- Several TotalEnergies sheets appear in more than one pool; merging by name and rounded API removes most repeats, but different sample years of the same grade with different API stay as separate rows.
- Viscosity at 40 C from Walther extrapolation outside the measured range is less reliable, especially when the lower temperature is below the WAT (non-Newtonian, wax-structured oil).
- API is defined at 60 F (15.56 C); the column is named api15 as requested.

# External reference pool: NOAA ADIOS Oil Library (fresh crude oils)

Source: github.com/NOAA-ORR-ERD/noaa-oil-data (data/oil, cloned 2026-11-05), records with product_type Crude Oil NOS, Condensate or Tight Oil, first (fresh) sub-sample. Includes Environment and Climate Change Canada (EC) records, legacy ADIOS records (AD; many from Jokuty et al. 1999 catalogue, oil company letters, OGJ data books), ExxonMobil assays (EX) and others. Extraction: agents/bulk/extract_noaa.py -> agents/bulk/noaa_adios_crude_bulk.csv. Dynamic viscosities converted to kinematic with density at that temperature. For the statistics below, visc40 uses only values measured at 40 C or Walther-interpolated between bracketing temperatures (extrapolated values dropped), and censored pour points (max or min only) are dropped. EC and AD may hold the same oil twice; no de-duplication across collections.

Records: 1134; by collection: AD 850, NO 153, EC 69, EX 58, GN 4

| variable | n | mean | sd | min | p10 | p25 | median | p75 | p90 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| api | 1134 | 33.9 | 9.73 | 9.4 | 21.3 | 28.5 | 34.4 | 38.9 | 45.1 | 80.5 |
| density15 | 1134 | 858 | 50.3 | 667 | 801 | 830 | 853 | 884 | 925 | 1e+03 |
| log10_visc40 | 314 | 0.942 | 0.758 | -0.347 | 0.181 | 0.477 | 0.777 | 1.23 | 1.96 | 3.75 |
| pour_c | 1008 | -12.7 | 22.8 | -83.2 | -43 | -29 | -12 | 3 | 15.3 | 55 |
| wax_wt_pct | 423 | 5.57 | 4.64 | 0 | 1 | 2.7 | 4.8 | 7 | 10 | 32 |
| sulphur | 313 | 0.927 | 1.27 | 0.001 | 0.0633 | 0.15 | 0.393 | 1.05 | 2.5 | 7.2 |

## NOAA pairwise pearson correlations (n in brackets)

| | api | pour_c | wax_wt_pct | sulphur | log10_visc40 |
|---|---|---|---|---|---|
| api | 1 | -0.09 (1008) | -0.03 (423) | -0.64 (313) | -0.86 (314) |
| pour_c | -0.09 (1008) | 1 | 0.51 (395) | -0.09 (298) | 0.11 (292) |
| wax_wt_pct | -0.03 (423) | 0.51 (395) | 1 | -0.27 (111) | -0.05 (71) |
| sulphur | -0.64 (313) | -0.09 (298) | -0.27 (111) | 1 | 0.43 (131) |
| log10_visc40 | -0.86 (314) | 0.11 (292) | -0.05 (71) | 0.43 (131) | 1 |

## NOAA pairwise spearman correlations (n in brackets)

| | api | pour_c | wax_wt_pct | sulphur | log10_visc40 |
|---|---|---|---|---|---|
| api | 1 | 0.01 (1008) | -0.01 (423) | -0.67 (313) | -0.92 (314) |
| pour_c | 0.01 (1008) | 1 | 0.49 (395) | -0.20 (298) | 0.02 (292) |
| wax_wt_pct | -0.01 (423) | 0.49 (395) | 1 | -0.23 (111) | -0.04 (71) |
| sulphur | -0.67 (313) | -0.20 (298) | -0.23 (111) | 1 | 0.64 (131) |
| log10_visc40 | -0.92 (314) | 0.02 (292) | -0.04 (71) | 0.64 (131) | 1 |

## NOAA simple fits

- log10(visc40 cSt) = 3.323 + (-0.0701) x API, 10 < API < 60; n = 308, residual sd = 0.363
- pour_c = -24.04 + 2.536 x wax_wt_pct; n = 395, residual sd = 19.4 C
- pour_c = -36.35 + (0.179) API + 2.134 wax + (4.39) log10 visc40; n = 65, residual sd = 19.6 C

## Pour point by wax class (NOAA)

| wax wt% | n | pour median C | pour p10 | pour p90 |
|---|---|---|---|---|
| 0-2 | 60 | -30 | -66 | -3 |
| 2-4 | 84 | -15 | -36 | 8 |
| 4-6 | 106 | -6 | -38 | 17 |
| 6-10 | 98 | -6 | -23 | 12 |
| 10-15 | 33 | 12 | -25 | 29 |
| 15-40 | 14 | 30 | 8 | 38 |

## Wax content by API class (NOAA)

| API | n | wax median | wax p10 | wax p90 |
|---|---|---|---|---|
| 0-20 | 31 | 2.5 | 0.3 | 6.0 |
| 20-30 | 75 | 4.0 | 1.0 | 8.5 |
| 30-40 | 230 | 5.2 | 2.2 | 12.0 |
| 40-50 | 66 | 4.6 | 1.2 | 8.0 |
| 50-90 | 21 | 0.7 | 0.0 | 4.0 |

## Walther (ASTM D341) interpolation check on NOAA crudes

- 156 crude oils with 3 or more kinematic viscosities above pour point + 5 C: predicting the middle temperature from the outer two gave mean error +0.99 %, mean absolute error 3.6 %, median absolute 0.36 %, 90th percentile absolute 12 % (163 cases).
