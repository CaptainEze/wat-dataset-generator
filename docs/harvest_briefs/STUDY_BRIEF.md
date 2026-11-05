# WAT knowledge study: shared brief for all agents

## Project
Project goal: predict crude oil wax appearance temperature (WAT) with machine learning from bulk properties only (API or density, pour point, wax content, kinematic viscosity at 40 C). We have a hand-built dataset of real measurements (master_v9.csv here: 347 rows, about 150 usable with all three main inputs). Real data is scarce. We now want a FRAMEWORK THAT GENERATES PHYSICALLY CONSISTENT SYNTHETIC DATAPOINTS from published models, correlations and quantitative facts, so models can be pre-trained on synthetic data and then trained and tested on the real data. Your job is to supply the knowledge the generator needs, with sources.

Base folder: /tmp/claude-0/-home-claude/5f0b162a-a33b-58cc-b1df-d50361861eed/scratchpad/study/
Useful local files (read them, do not edit): master_v9.csv (real data, columns include source and source_url), source_inventory.csv (724 sources opened earlier, with status), ../harvest/merged/harvest_source_log_all.csv.
Write ONLY inside your own folder agents/<yours>/.

## Output formats (JSON Lines, one object per line, UTF-8)
### models.jsonl (equations and models)
{"id": "short_id", "name": "...", "target": "WAT|WDT|cloud_point|pour_point|wax_content|viscosity|density|n_paraffin_dist|melting_point|enthalpy_fusion|other",
 "inputs": [{"name": "API", "unit": "deg API", "symbol": "API"}, ...],
 "equation_text": "equation exactly as printed, in plain text",
 "python": "a single Python expression or small function body using the input symbols and numpy as np, that returns the target in the stated unit",
 "coefficients": {"a": 1.23, ...}, "output_unit": "C or K ...",
 "validity": {"API": [min, max], ...}, "fitted_on": "what data, how many points, which oils",
 "reported_accuracy": "R2, AARD, RMSE as stated", "citation": "Author (year). Title. Journal, vol, pages.", "doi": "10....", "url": "...",
 "access": "full_text|abstract_only|secondary_citation", "where": "equation number / page / table",
 "confidence": "high|medium|low", "notes": "plain English"}
### facts.jsonl (quantitative relationships and effects)
{"id": "...", "subject": "cooling_rate", "object": "WAT", "relation": "decreases|increases|offset|range|ratio|equals|threshold",
 "magnitude": "number with unit, e.g. -0.8 C per (C/min) or CPM minus DSC = +2 to +6 C", "value_low": number, "value_high": number, "unit": "...",
 "conditions": "method, oils, temperature range, sample prep", "n_oils": int or null,
 "citation": "...", "doi": "...", "url": "...", "access": "full_text|abstract_only|secondary_citation", "where": "table / figure / page", "confidence": "high|medium|low", "notes": "..."}
### edges.csv (only the network agent writes this)
src_id,src_type,rel,dst_id,dst_type,evidence

### log.csv: every source opened. Columns: url,title,year,status(used|no_content|unreachable|paywalled|duplicate),notes

## Rules
- Only values and equations the source states. Never write an equation or coefficient from memory as if read. If you know a classic equation but could not open the primary text, you may record it with access "secondary_citation" (if read in another paper) or, last resort, "from_memory" with confidence low, so we can verify later. Mark it honestly.
- Copy coefficients exactly, including signs and units. Read each coefficient twice against the page.
- The "python" field must be runnable: test it yourself in the shell (python3 -I -c ...) on one or two input values inside the validity range, and, if the paper gives a worked example or a table of predictions, check that your code reproduces it. Record the check in notes ("reproduces Table 3 row 2: 31.2 C vs 31.2 C").
- Tools: WebSearch and WebFetch (shell is blocked for most hosts except GitHub and package registries; do not use mirrors, proxies, shadow libraries). OpenAlex works through WebFetch: https://api.openalex.org/works?search=...&select=id,doi,title,publication_year,open_access,referenced_works&per-page=50 ; single work: https://api.openalex.org/works/doi:10.xxxx/yyyy . Crossref also works. WebFetch returns a summarised window: for long PDFs use the offset parameter and ask for VERBATIM equations and tables.
- Paywalled papers: read the abstract and any open copy (author repository, PMC, institutional repository, MDPI, Frontiers, conference open pages). Log what you could not open.
- Write files early and append as you go; a usage limit may stop you.
- Plain English in notes; no em dashes.
- Final report under 200 words: counts, the most important items, gaps, and best unopened sources.
