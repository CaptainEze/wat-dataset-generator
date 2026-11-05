# Addendum: Niger Delta round and master v6 (4 Nov 2026)

## What was done
Eight agents (regulators, oil companies, Nigerian operators, theses, journals, flow assurance, spill and environmental documents, open datasets), then four continuation agents after a usage limit. Roughly 250 sources logged. Sources were queried directly (OpenAlex, Crossref, SEC archive, GitHub, oil property libraries, company assay PDFs).

## Findings
- No Nigerian regulator or oil company publishes a per-grade WAT. Total and Exxon assay sheets for Bonny Light, Forcados, Qua Iboe, Bonga, Erha, Usan, Akpo, Amenam, Egina, EA, Brass River give pour point, API and sometimes viscosity, but no WAT and almost no whole-crude wax.
- Total sheets give viscosity at 10 and 50 C only, so the 40 C column stays blank.
- The Total Wax row on Exxon sheets looks like unlabelled cut values; Usan pour -77 C and wax 4.0 are doubtful.
- Real new WAT-type data is almost all cloud point (ASTM D2500), tier C.

## Master v6
- 244 rows, 217 oils. 28 rows added (R217 to R244): 11 tier C cloud points, 3 tier B- (two Shell Niger Delta waxy crudes with ASTM D5772, one Shallsuku 2023 refinery sample), 5 pending, 9 tier X (Falade 2010 model predictions).
- Seven-well Port Harcourt set (ELE, OBGE, SBR, EGB, OMR, ORD, OZR): entered once. Paper calls the value cloud point/WAT, measured with a D2500-type tester; its tables disagree on pour point for OMR and ORD.
- R244 (Shallsuku) prints "240C" and "280C" with the degree sign lost, read as 24 and 28 C.

## Held out
- Seplat flowline file (144 rows, tier D, GitHub Uma-Energy, SlugeDatasetSeplat.xlsx): no oil names, methods or lab; may be synthetic. data/bulk/seplat_sluge_tierD_HELD_unverified.csv.
- Bulk-only pool: 131 rows, 92 distinct names (data/bulk/nigeria_bulk_only_raw.csv).

## Caution
Tier C cloud points raise the usable count but are not WAT. Run results with and without them.

## Unread leads
sciencepg jeece.20251002.13 and pse.20261001.14; Edimeh 2020; EJP 1070 (Joseph 2025); jerr 2026 v28i31817; Adeyanju 2016 subsea thesis (UNILAG); SPE 212026, 178317, 203618, 128600, 234951, 206180; NNPC Annual Statistical Bulletin 2005; BP Bonny appraisal (Energy Institute 49819/49820); UNEP Ogoniland.
