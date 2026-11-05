# WAT knowledge study and synthetic datapoint framework

Working notes, not a thesis chapter. Everything here is traceable to a file in this folder.

## 1. What was gathered (knowledge/)

| Folder | What it holds |
|---|---|
| knowledge/correlations | 31 explicit equations (WAT, WDT, cloud point, pour point, wax content), 24 facts, 73 sources. Each python field runs; misprints found in Hosseinipour 2019 and Benamara 2019 (refits given). |
| knowledge/thermo | 32 models, 22 facts, 42 sources, thermo_wat.py (n-alkane properties from Coutinho 2006, multisolid and ideal solid solution WAT, n-paraffin distribution builder), test_thermo.py, validation_sets.csv (40 predicted vs measured rows, incl. 13 Colombian crudes not in master). |
| knowledge/effects | 84 facts (method offsets, detection limits, cooling rate, thermal history, WDT gap, pressure, asphaltenes), 9 small models, within_oil_pairs.csv (276 within-oil method pairs from 39 oils). |
| knowledge/bulk | 19 models, 24 facts, bulk_relations.py (API MPMS 11.1 density, ASTM D341 Walther, 9 dead-oil viscosity correlations, pour point and MW), noaa_adios_crude_bulk.csv (1134 crudes), bulk_pool_clean.csv (374 local crudes). |
| knowledge/network | OpenAlex citation network (nodes.csv, edges.csv), network_summary.md with the ranked list of unopened open-access papers likely to hold WAT tables. |

Registry: 91 equations (40 read from full text, 49 secondary citations, 2 abstracts), 154 facts.

## 2. Knowledge network (network/)
`knowledge/graph/wat_knowledge_graph.graphml` (open in Gephi or Cytoscape), plus nodes.csv and edges.csv.
About 1,955 nodes: papers, theses, assays, datasets, ML studies, our 260 oil groups, WAT methods, properties, equations and facts.
Edge types: cites, measures (source to oil), wat_by (oil to method), reports, uses_method, trains_on, provides_equation, states_fact, input_to, predicts, subject_of, affects.
Rebuild: `python src/main.py --objective 2`.

## 3. Patterns in the real data (docs/real_data_patterns.md, docs/results/within_oil_spread.csv)
- Spearman with WAT: wax 0.73, log viscosity 0.60, pour 0.55, API -0.42 (all usable rows). Without Benamara: wax 0.52, pour 0.50, API -0.16.
- WAT minus pour point: median 23 C (middle half 16 to 35 C). WDT minus WAT: median 8 C.
- Same oil, different method: median spread 4.2 C over 28 oils, up to 18 C.

## 4. The generator (src/modules/)
Latent-variable simulator. For each crude:
1. Inputs: API, log viscosity at 40 C, wax content from a Gaussian copula fitted on 1,408 real crudes (inputs.py), or a real crude taken directly (anchored mode).
2. Hidden description (latent.py): n-paraffin share of the measured wax, mass-mean carbon number and spread of the n-paraffin block, oil molar mass, solid-solution factor, gel threshold.
3. Physics (physics.py): n-paraffin distribution, solid wax curve and WAT from the thermo engine (bracket between multisolid and ideal solid solution, f from 10 published systems). A lookup table (data/derived/latent_table.npz, 8,640 engine runs) makes this fast.
4. Measurement (measurement.py): each method reports WAT when the solid reaches its detection threshold (literature values), relative to a sensitive reference method, minus supercooling that grows with cooling rate, plus repeatability noise; methods needing much more solid than the oil makes near onset report no WAT (cap 20 C, Coutinho and Daridon 2005). Pour point is the temperature where the solid reaches a gel threshold.
5. Calibration (calibrate.py): hidden-description prior tuned by maximum simulated likelihood on (a) 501 real crudes with API, wax and pour point but no WAT (unsupervised term) and optionally (b) real WAT rows. Fitted values: src/modules/params/theta_U.json (no WAT used) and src/modules/params/theta_J.json (joint).
6. Output (generate.py): one row per synthetic crude with inputs, measured WAT, method, true WAT, latent values, pool id, importance ESS and theta file.

Commands
```
cd src
python generate.py --mode forward  --n 5000 --out ../data/synthetic/synth_forward.csv
python generate.py --mode anchored --n 5000 --out ../data/synthetic/synth_anchored.csv
python generate.py --mode forward  --n 2000 --method CPM --out ../data/synthetic/synth_cpm.csv
```

## 5. Rules for using synthetic rows
- Synthetic rows are for pre-training, augmentation or as a physics feature. They are never test data.
- Any generator calibrated with real WAT must be calibrated inside the training folds only (NestedBenchmark in src/modules/evaluation.py, with theta_fold*.json).
- Report every result with and without synthetic data.

## 6. Known weak points (to fix or to state)
- Oil molar mass uses the Cragoe formula from memory (low confidence); a latent multiplier absorbs some error.
- DSC detection threshold (0.1 to 0.5 wt%) is low confidence; simulated CPM minus DSC is 8 to 12 C against 6 C (mean, range 2 to 10.5) in the literature.
- The WAT-free calibration cannot fix the WAT level (pour point and wax alone leave it unidentified): it predicts about 8.5 C too low. WAT data is needed to calibrate, inside folds.
- Pedersen B constant printed 6.584e-4 vs 6.584e-6 in NeqSim code: not used by the main path.

## 7. Results (5-fold GroupKFold by oil, 77 real rows, 61 oils, generator recalibrated by differential evolution inside each training fold)
File: docs/results/nested3_results.csv, docs/results/nested3_predictions.csv, per-fold calibrations src/modules/params/theta_fold0..4.json.

| Approach | Best model | RMSE C | MAE C | R2 |
|---|---|---|---|---|
| Real data only | Extra Trees | 9.43 | 8.03 | 0.50 |
| Physics prediction as an extra input | Extra Trees | 8.64 | 6.93 | 0.58 |
| Physics as baseline, ML learns the residual | Extra Trees | 8.66 | 7.29 | 0.58 |
| Generator alone (no ML) | | 9.66 | 8.12 | 0.48 |
| Real plus synthetic rows | SVR | 9.43 | 7.33 | 0.50 |
| Synthetic rows only | XGBoost | 10.38 | 8.84 | 0.40 |
| Published bulk correlations (VNIIneft, Trebin) | | 16.0 to 18.5 | | negative |

Paired bootstrap over oils (5000 resamples): physics-as-input lowers Extra Trees RMSE by 0.79 C (95% interval 0.16 to 1.44), MAE by 1.10 C (0.41 to 1.78).
Reading: the knowledge helps most when injected as a physics-based feature, not as extra synthetic rows. Synthetic rows alone carry the generator's simplifications (too-tight pour point link, low-confidence DSC threshold) into the model.
An earlier run (docs/results/DO_NOT_QUOTE_leaky_nested_results.csv) started each fold from a calibration that had seen all oils; it is kept only as a record and must not be quoted.

## 8. Production synthetic files (data/synthetic/)
Calibrated on all real data (theta_J): use for exploration or final pre-training only, never inside an evaluation.
- synth_forward_thetaJ.csv: 9,087 rows, method mix as in the real data
- synth_anchored_thetaJ.csv: 5,000 rows on real NOAA and local crudes (real inputs, simulated WAT)
- synth_forward_CPM_thetaJ.csv: 3,000 rows, CPM only
Synthetic patterns vs real: WAT minus pour median 26 to 27 C (real 23 to 24), Spearman WAT vs pour 0.78 (real 0.50 to 0.55, too tight), vs wax 0.46 to 0.63 (real 0.52 to 0.73), vs API about -0.1 (real -0.16).

## 9. Next improvements
1. Let the DSC detection threshold and the gel threshold vary per crude with calibrated spread (loosens the WAT-pour link).
2. Replace the Cragoe molar mass (from memory) with a sourced correlation; add viscosity to the latent link.
3. Add Benamara and tier C rows as separate calibration sets with their own method (pour-point tester, cloud point).
4. Repeat the nested test with 3 different fold seeds (one seed so far).
5. Feed the 13 Colombian crudes in knowledge/thermo/validation_sets.csv into the master after a check.
