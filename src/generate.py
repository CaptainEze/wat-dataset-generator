import argparse
from modules.generator import SyntheticGenerator

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate synthetic WAT datapoints")
    p.add_argument("--mode", default="forward", choices=["forward", "anchored"])
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--theta", default="modules/params/theta_J.json")
    p.add_argument("--method", default=None, help="fix one WAT method, e.g. CPM, DSC, D8420, viscometry")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="../data/synthetic/synth.csv")
    a = p.parse_args()
    df = SyntheticGenerator(a.theta, a.seed).run(a.mode, a.n, method=a.method)
    df.to_csv(a.out, index=False)
    print(f"✓ {len(df)} rows -> {a.out}")
