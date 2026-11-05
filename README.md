# WAT Dataset Generator

Wax appearance temperature (WAT) prediction for crude oils from bulk properties (API or density, pour point, wax content, viscosity at 40 C).
This repository holds the open, multi-method WAT dataset built from public sources, the knowledge base extracted from the literature, and a physics-informed generator of synthetic WAT datapoints.

MEng thesis work, Department of Petroleum and Gas Engineering, University of Port Harcourt.

## Project Structure

```
wat-dataset-generator/
├── src/
│   ├── main.py                    # Objectives-based workflow
│   ├── generate.py                # Standalone synthetic data generator
│   │
│   ├── modules/
│   │   ├── paths.py               # Project paths
│   │   ├── data.py                # Real data loading (usable rows, labelled, unlabelled pool)
│   │   ├── patterns.py            # Correlations, gaps, within-oil method spread
│   │   ├── network.py             # Knowledge network (sources, equations, facts, oils, citations)
│   │   ├── thermo.py              # Solid-liquid equilibrium engine (Coutinho 2006 n-alkane properties)
│   │   ├── bulk.py                # Density, viscosity, pour point and MW correlations
│   │   ├── inputs.py              # Copula sampler of realistic bulk-property vectors
│   │   ├── physics.py             # Latent lookup table, solid wax curve, true WAT
│   │   ├── measurement.py         # Method detection thresholds, supercooling, noise
│   │   ├── latent.py              # Hidden n-paraffin description and forward simulator
│   │   ├── calibrate.py           # Maximum simulated likelihood calibration
│   │   ├── correlations.py        # Registry of extracted equations, bulk WAT correlations
│   │   ├── generator.py           # Synthetic datapoint generator (forward, anchored)
│   │   ├── evaluation.py          # Nested benchmark on real oils, bootstrap
│   │   └── params/                # Fitted generator parameters (theta_*.json)
│   │
│   └── scripts/
│       ├── harvest/               # Merge, verification and scanning scripts used to build the dataset
│       └── knowledge/             # Extraction scripts used by the literature agents
│
├── data/
│   ├── master/wat_master.csv      # Current master dataset (v9: 347 rows, 260 oils)
│   ├── master/history/            # Every master version v1 to v9
│   ├── harvest/                   # Per-round, per-territory rows, source logs, verification
│   ├── bulk/                      # Crudes with bulk properties but no WAT (NOAA ADIOS, assays, local)
│   ├── derived/latent_table.npz   # Precomputed physics table (8,640 engine runs)
│   └── synthetic/                 # Generated datasets
│
├── knowledge/
│   ├── correlations/              # 31 equations, 24 facts
│   ├── thermo/                    # 32 models, 22 facts, validation sets
│   ├── effects/                   # 84 facts, within-oil method pairs
│   ├── bulk/                      # 19 models, 24 facts, local pool statistics
│   ├── network/                   # OpenAlex citation network, candidate papers
│   ├── graph/                     # Combined knowledge graph (GraphML, nodes, edges)
│   └── source_inventory.csv       # 724 sources opened during data collection
│
├── docs/
│   ├── harvest/                   # Data collection log, round by round
│   ├── harvest_briefs/            # Briefs given to each collection and extraction round
│   ├── knowledge_study.md         # Knowledge study and generator write-up
│   ├── real_data_patterns.md      # Patterns found in the real data
│   └── results/                   # Benchmark results and predictions
│
├── results/                       # Workflow outputs (ignored)
└── plots/                         # Figures (ignored)
```

## Quick Start

### Installation

Install required dependencies: numpy, pandas, scipy, scikit-learn, xgboost, networkx, joblib, matplotlib, openpyxl (versions in requirements.txt).

### Basic Usage

Run from the src directory. The default runs objectives 1, 2, 4 and 5 with the shipped calibrations. Objective 3 recalibrates the generator (about 20 minutes per run on 2 cores).

```
cd src
python main.py
python main.py --objective 1,2
python main.py --objective 4 --fast
python generate.py --mode anchored --n 5000 --method CPM --out ../data/synthetic/synth_cpm.csv
```

## Workflow

### Objective 1: Analyse the real dataset
- Loads usable master rows (tier not P, X or D) and puts density on one basis (API at 15 C)
- Spearman correlations with and without the Benamara set and tier C rows
- WAT minus pour point, WDT minus WAT, within-oil method spread, linear baseline

Outputs: objective1_correlations.csv, objective1_within_oil_spread.csv, objective1_summary.json

### Objective 2: Build the knowledge network
- Joins sources, 91 equations, 154 facts, properties, WAT methods, 260 oil groups and the citation network
- Builds the physics lookup table if missing

Outputs: knowledge/graph/wat_knowledge_graph.graphml, nodes.csv, edges.csv

### Objective 3: Calibrate the generator
- WAT-free calibration on 501 real crudes with API, wax and pour point (unsupervised)
- Joint calibration adding the real WAT rows

Outputs: theta_U.json, theta_J.json

### Objective 4: Benchmark on real oils
- 5-fold GroupKFold by oil on 77 rows (61 oils), generator calibrated inside each training fold
- Real only, synthetic only, real plus synthetic, synthetic pre-training, physics as a feature, physics as a baseline

Outputs: objective4_benchmark.csv, objective4_predictions.csv

### Objective 5: Generate synthetic datapoints
- Forward mode: inputs from the copula, WAT from physics and measurement
- Anchored mode: real crudes from the bulk pool, simulated WAT

Outputs: synth_forward.csv, synth_anchored.csv, synth_forward_CPM.csv

## Results

| Approach | Best model | RMSE (C) | MAE (C) | R² |
|---|---|---|---|---|
| Real data only | Extra Trees | 9.43 | 8.03 | 0.50 |
| Physics prediction as an extra input | Extra Trees | 8.64 | 6.93 | 0.58 |
| Physics as baseline, model learns the residual | Extra Trees | 8.66 | 7.29 | 0.58 |
| Generator alone | | 9.66 | 8.12 | 0.48 |
| Real plus synthetic rows | SVR | 9.43 | 7.33 | 0.50 |
| Synthetic rows only | XGBoost | 10.38 | 8.84 | 0.40 |

Paired bootstrap over oils: physics as an input lowers Extra Trees RMSE by 0.79 C (95% interval 0.16 to 1.44).

## Data Rules

- Public sources only. Every row has a source, URL, tier and verification status.
- Tiers: A, A- (primary lab or operator report), B, B- (peer-reviewed or thesis measurement), C (secondary or cloud point), D (unverified compilation), P (pending), X (excluded: live oil, high pressure, blends, model oils).
- One row per oil and WAT method; the same oil or field shares one oil_group, used for grouped cross-validation.
- Synthetic rows are never test data. A generator calibrated with real WAT is calibrated inside training folds only.

See docs/knowledge_study.md for the generator design, known weak points and next steps.
