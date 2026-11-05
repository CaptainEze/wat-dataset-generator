# WAT dataset harvest: shared brief for all agents

## Project
Project goal: predict crude oil wax appearance temperature (WAT) with machine learning from bulk properties only (density or API gravity, kinematic viscosity at 40 C, pour point, wax content). We are building the first open, multi-method, sourced WAT dataset. How the dataset is built will be written up as a documented method for standardising WAT datasets, so every step must be recorded.

Only publicly available data is allowed. Do not plan around paywalls, private data or company-only files.

## Your job
Search the open web in your assigned territory, find sources (papers, theses, regulator reports, assay sheets, supplementary tables, repositories), read them, and extract every oil that has a measured WAT, plus its bulk properties. Write rows to your own CSV files. Do not touch the master file.

## Output files (your own folder only)
1. `rows.csv`: one row per oil and WAT-method pair. Header exactly:
   `row_id,oil_group,oil_name,country_basin,density_kg_m3,api,wax_wt_pct,wax_method,pour_c,pour_method,visc_cSt_40C,wat_c,wat_method,wdt_c,tier,source,source_url,notes`
2. `log.csv`: one row for EVERY source you open, including rejected ones. Header:
   `source_id,url,title,year,type,status,rows_added,reason`
   status is one of: extracted, rejected, duplicate, unreachable, image_table, no_wat. Reason is one short plain sentence. This file is the audit trail (it feeds a CONSORT-style flow diagram), so do not skip sources.

Row ids: use your prefix then a number, for example `WAF-001`. The lead will renumber on merge.

## Extraction rules (strict)
- Copy only values the source states. Never estimate, infer or fill a blank from memory. A blank is correct when the source is silent.
- Read each value twice: once when you write it and once against the source before saving the file. Typos in numbers are the main risk.
- Units: WAT, pour point, WDT in C. Convert F to C by (F - 32) / 1.8, and say so in notes. Density in kg/m3 at 15 C if stated (g/cm3 times 1000). Leave density blank if only API is given, and fill api. Viscosity column is kinematic viscosity in cSt at 40 C only. If the source gives cP, divide by the stated density and say so in notes. If it gives other temperatures only, leave blank and put the values in notes. Never extrapolate.
- One row per oil and WAT-method pair. If one oil has WAT by CPM and by DSC, write two rows with the same oil_group.
- oil_group: short lowercase id for the oil (field or crude name plus country code if needed). Same oil in different papers shares one group. If unsure whether it is the same oil as an existing master group, use a new group and write "possible duplicate of <group>" in notes. Check `/tmp/claude-0/-home-claude/5f0b162a-a33b-58cc-b1df-d50361861eed/scratchpad/harvest/master_snapshot.csv` first and skip anything already there unless you add a different WAT method for the same oil.
- wat_method: use the closest of: CPM, PLM, DSC, uDSC, viscometry, NIR, FTIR, light transmission, refractive index, ultrasonic, cold finger, filter plugging, IP 389 / ASTM D8420, ASTM D2500 cloud point, high pressure microscopy, other (say what). Record cooling rate, sample thermal history and dead or live state in notes when stated.
- wax_method: UOP 46, modified UOP 46-64, GC, DSC, other, or not stated. pour_method: ASTM D97, D5853, D5950, other, or not stated.
- Live oil or high pressure WAT, WAT of model mixtures, synthetic oils, solvent-diluted oils and inhibitor-treated oils: tier X. Do not put additive or pour-point-depressant results as plain oil rows (use the no-additive value only).
- Cloud point from ASTM D2500 is not WAT. Record it as wat_method "ASTM D2500 cloud point", tier C, with a note.
- Plausibility: if WAT is more than 40 C above pour point, or WAT is below pour point, keep the row but write "PLAUSIBILITY FLAG" and the gap in notes. Do not alter values.
- Censored values (below detection limit): record the limit and write "censored" in notes.
- source: author(s), year, title short form, and the table or page number. source_url: the exact URL you read. Notes: plain English, no em dashes, no long quotes (data values only).

## Tiers
- A: primary lab report or assay from the laboratory or operator, standard methods named, all four inputs and WAT present.
- A-: as A but one input missing, a censored value, or a minor unit ambiguity.
- B: peer-reviewed or thesis primary measurement, method named, most inputs present.
- B-: primary measurement but method vague, or several inputs missing (at least density or API and WAT must exist).
- C: secondary compilation or review table where the primary source was not checked. Always give the original citation in notes if the table shows it.
- D: unverified compilation (no per-row sources). Log it, extract only if the table is large and clearly useful, and mark it clearly.
- X: exclude from modelling but keep for the record (live, high pressure, blends, model oils).
- P: pending, need another page or table before the row is usable.

## Where to look and how
- Use WebSearch (standard mode first, extended when results are thin) and WebFetch. The shell is mostly blocked by the network allowlist (GitHub and package registries work, most journal, repository and company sites do not). Do not try to get around a block with mirrors, proxies, caches, Tor or other routes. If a PDF or page cannot be read with WebFetch, log it as `unreachable` with the URL so the user can open it in his own browser.
- Table that is an image: log as `image_table` and move on.
- Open-access full text is the target. Do not use shadow libraries.
- Prefer sources with tables of many oils. Also read reference lists of good papers to chase primary sources.
- Ready-made search ideas: "wax appearance temperature" with a country, field or crude name; "crude oil assay" "wax appearance"; "WAT" "pour point" "wax content" "API gravity" table; thesis "appendix" crude characterisation; Sodir factpages "wax"; flow assurance case study; "crude oil characterisation" "cloud point" "wax content".

## Effort and stopping
- Work through your territory until you have examined roughly 60 sources, or three search rounds in a row add no new usable oil. Quality first: a row with a wrong number is worse than no row.
- Write `rows.csv` and `log.csv` early and update them as you go, so nothing is lost if you are stopped.
- Stay inside your folder. Do not edit other agents' files or the master. No git, no commits.

## Final report to the lead (under 200 words, plain English)
Number of sources examined, number of rows and oils added, tier counts, the crude types covered (condensate, light, medium, heavy, high wax), the best leads you could not open (with URLs), and any rule you were unsure about.
