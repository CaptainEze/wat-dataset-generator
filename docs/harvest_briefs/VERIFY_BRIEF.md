# Blind verification brief (double-entry check)

You are an independent checker for a WAT (crude oil wax appearance temperature) dataset. Another person already extracted values from the sources in your task file, but you have NOT been told those values, on purpose. Extract them yourself from the source.

Your task file: /tmp/claude-0/-home-claude/5f0b162a-a33b-58cc-b1df-d50361861eed/scratchpad/harvest/verify/<V>_task.csv (columns row_id, oil_name, source, source_url).
For each row, open source_url with WebFetch (do not use the shell for websites; it is blocked; do not try to get around blocks). Find the oil named in oil_name and record exactly what the source states:
density_kg_m3 and the temperature it was measured at (density_T_c), api, wax_wt_pct and wax method, pour_c and pour method, visc_cSt_40C (kinematic, cSt, 40 C only; if cP, give the cP value and the density used in notes), wat_c and WAT method, wdt_c.
Rules: copy only what the source states; leave blank what it does not state; convert F to C and g/cm3 to kg/m3 and say so; never guess. If the page cannot be read, or the table is an image, write status = unreachable or image_table and move on. Read each number twice. Do not read any file other than your task file and this brief. In particular do NOT open the merged dataset or other agents' files.

Output: /tmp/claude-0/-home-claude/5f0b162a-a33b-58cc-b1df-d50361861eed/scratchpad/harvest/verify/<V>_result.csv with columns:
row_id,status,density_kg_m3,density_T_c,api,wax_wt_pct,pour_c,visc_cSt_40C,wat_c,wat_method,wdt_c,notes
status is one of: read, unreachable, image_table, not_found.
Final report to the lead: under 100 words, plain English: rows read, rows you could not read, anything odd in the source (inconsistent numbers inside the paper).
