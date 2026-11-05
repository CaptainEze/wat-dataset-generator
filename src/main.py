import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from modules.paths import RESULTS, PARAMS, LATENT_TABLE, SYNTHETIC_DIR, ensure_dirs
from modules.data import usable_rows, labelled, unlabelled
from modules.patterns import DataAnalyzer
from modules.network import KnowledgeNetwork
from modules.physics import Table, build_table
from modules.calibrate import Calibrator
from modules.evaluation import NestedBenchmark, bootstrap_gain
from modules.generator import SyntheticGenerator


class WATDatasetSystem:
    def __init__(self, fast=False):
        self.fast = fast
        ensure_dirs()
        print(f"\n{'='*70}")
        print("WAT DATASET GENERATOR - Wax Appearance Temperature")
        print(f"{'='*70}")
        print(f"Results directory: {RESULTS}")

    def objective_1_analyse_real_data(self):
        print("\n" + "="*70)
        print("OBJECTIVE 1: Analyse the real dataset and rank bulk properties")
        print("="*70)
        u = usable_rows()
        print(f"✓ Usable rows: {len(u)} from {u.oil_group.nunique()} oils")
        a = DataAnalyzer(u)
        corr = a.correlations()
        corr.to_csv(f"{RESULTS}/objective1_correlations.csv", index=False)
        a.within_oil_spread().to_csv(f"{RESULTS}/objective1_within_oil_spread.csv")
        json.dump(dict(gaps=a.gaps(), linear_fit=a.linear_fit()), open(f"{RESULTS}/objective1_summary.json", "w"), indent=1, default=float)
        print(corr[corr.subset == "no Benamara"].to_string(index=False))
        print(f"✓ Saved to {RESULTS}/objective1_*")

    def objective_2_build_knowledge(self):
        print("\n" + "="*70)
        print("OBJECTIVE 2: Build the knowledge network and the physics lookup table")
        print("="*70)
        KnowledgeNetwork().build()
        if not os.path.exists(LATENT_TABLE):
            print("Building latent lookup table (about 4 minutes on 2 cores)...")
            build_table(LATENT_TABLE)
        print(f"✓ Latent table: {LATENT_TABLE}")

    def objective_3_calibrate(self):
        print("\n" + "="*70)
        print("OBJECTIVE 3: Calibrate the generator (WAT-free and joint)")
        print("="*70)
        tab = Table(LATENT_TABLE)
        U, L = unlabelled(), labelled()
        maxiter = 5 if self.fast else 30
        for name, LL in [("U", None), ("J", L)]:
            th, (ll, parts) = Calibrator(tab, U, LL).fit_global(maxiter=maxiter)
            path = f"{RESULTS}/theta_{name}.json"
            json.dump(dict(theta=th, ll=ll, parts=parts), open(path, "w"), indent=1)
            print(f"✓ theta_{name}: {path}")
        print("Shipped calibrations are in src/modules/params/ (copy new ones there to use them).")

    def objective_4_benchmark(self):
        print("\n" + "="*70)
        print("OBJECTIVE 4: Benchmark on real oils (nested, no leakage)")
        print("="*70)
        tab = Table(LATENT_TABLE)
        L = labelled()
        paths = [f"{PARAMS}/theta_fold{f}.json" for f in range(5)]
        R, pred = NestedBenchmark(tab, L, paths, n_synth=500 if self.fast else 2000).run()
        R.to_csv(f"{RESULTS}/objective4_benchmark.csv", index=False)
        pred.to_csv(f"{RESULTS}/objective4_predictions.csv", index=False)
        print(R.head(10).to_string(index=False))
        g = bootstrap_gain(pred, "ExtraTrees|physics_feature", "ExtraTrees|real_only")
        print(f"✓ Physics feature vs real only (Extra Trees): RMSE gain {g['mean']:.2f} C, 95% {g['lo']:.2f} to {g['hi']:.2f}")

    def objective_5_generate(self, n=10000):
        print("\n" + "="*70)
        print("OBJECTIVE 5: Generate synthetic datapoints")
        print("="*70)
        gen = SyntheticGenerator(f"{PARAMS}/theta_J.json", seed=101)
        for mode, nn, method in [("forward", n, None), ("anchored", n // 2, None), ("forward", n // 3, "CPM")]:
            df = gen.run(mode, nn, method=method)
            tag = f"{mode}{'_' + method if method else ''}"
            df.to_csv(f"{RESULTS}/synth_{tag}.csv", index=False)
            print(f"✓ {len(df)} rows -> {RESULTS}/synth_{tag}.csv")

    def run(self, objectives):
        steps = {1: self.objective_1_analyse_real_data, 2: self.objective_2_build_knowledge,
                 3: self.objective_3_calibrate, 4: self.objective_4_benchmark, 5: self.objective_5_generate}
        for o in objectives:
            steps[o]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WAT dataset generator workflow")
    parser.add_argument("--objective", default="1,2,4,5", help="comma list of 1-5 (3 recalibrates, slow)")
    parser.add_argument("--fast", action="store_true", help="small runs for a quick check")
    args = parser.parse_args()
    WATDatasetSystem(fast=args.fast).run([int(x) for x in args.objective.split(",")])
