# Addendum: assays and Kok (master v4, 4 Nov 2026)

## Master file: wat_master_v4.csv
- 211 rows, 187 oil groups. Tiers: A 17, A- 8, B 18, B- 130, C 16, P 19, X 3.
- Usable for modelling: 189 rows, 169 oils. Core3: 134 rows, 121 oils.
- Added since v3: 8 south-east Turkey crudes (Kok, Varfolomeev and Nurgaliev 2018, J Pet Sci Eng 168:542-545; DSC WAT 14.2 to 37.8 C; tier B-) and 7 Middle East crudes (Elsharkawy et al. 2000 as reproduced in a later paper; tier C; no pour point).
- Kok rows: the table text came untitled; the paper was identified from the crude count and the WAT range. Viscosity is in cP at an unstated temperature, so not entered. Crude 4 has WAT 43.7 C above pour point, and in crude 8 the WDT (30.0) is below the WAT (37.8). Both flagged.

## TotalEnergies-format assay sheets (46 distinct crudes)
- No sheet has a WAT field or a whole-crude wax value; wax appears only per distillation cut.
- Whole-crude density at 15 C, API, sulphur, pour point, viscosity at 20 and 40 C and acid number saved as data/bulk/totalenergies_whole_crude_all.csv (pour-point pretraining option). Not part of the WAT master.
- Pour points -78 to +15 C, API 14.3 to 68.6.

## Not added
- Hosseinipour et al. five samples A to E: only pseudo-compositions, no density, wax or pour point.
- A regional review table of waxy crudes: secondary, already in the master at tier C.
