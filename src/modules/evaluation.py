"""Does synthetic data help? Test on REAL oils only, grouped by oil (GroupKFold), repeated.

Conditions (same folds for all):
  real_only        model trained on the real training fold
  synth_only       model trained only on synthetic rows (generator calibrated WITHOUT any WAT data)
  real_plus_synth  real training fold + synthetic rows (synthetic weight w per row)
  physics_direct   no ML: posterior-predictive WAT from the generator given API, wax, pour
  correlation_*    published bulk-input correlations (VNIIneft, Trebin), no fitting
Metrics in Kelvin terms: RMSE, MAE, R2, AARD (% of WAT in K).
"""
import numpy as np, pandas as pd, warnings
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from xgboost import XGBRegressor
warnings.filterwarnings("ignore")
FEATS = ["api15", "pour_c", "wax_wt_pct"]

def models():
    return {"ExtraTrees": lambda: ExtraTreesRegressor(n_estimators=300, min_samples_leaf=2, random_state=0, n_jobs=1),
            "XGBoost": lambda: XGBRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, verbosity=0, n_jobs=1, random_state=0),
            "SVR": lambda: Pipeline([("s", StandardScaler()), ("m", SVR(C=30, gamma="scale", epsilon=1.0))])}

def metrics(y, p):
    e = p - y; ok = np.isfinite(p)
    e, y2 = e[ok], y[ok]
    return dict(RMSE=np.sqrt(np.mean(e**2)), MAE=np.mean(abs(e)), R2=1 - np.sum(e**2) / np.sum((y2 - y2.mean())**2),
                AARD=np.mean(abs(e) / (y2 + 273.15)) * 100, coverage=ok.mean())

def run(L, S, phys_pred=None, corr_preds=None, w_synth=0.3, reps=3, k=5):
    y = L.wat_c.values; g = L.oil_group.values; X = L[FEATS].values
    Xs = S[FEATS].values; ys = S.wat_c.values
    res = []
    for r in range(reps):
        ug = np.unique(g); perm = np.random.default_rng(r).permutation(len(ug)); gm = dict(zip(ug, perm))
        gi = np.array([gm[x] for x in g])
        preds = {}
        for tr, te in GroupKFold(n_splits=k).split(X, y, gi):
            for mn, mk in models().items():
                for cond in ["real_only", "synth_only", "real_plus_synth"]:
                    key = (mn, cond); preds.setdefault(key, np.full(len(y), np.nan))
                    m = mk()
                    if cond == "real_only": m.fit(X[tr], y[tr])
                    elif cond == "synth_only": m.fit(Xs, ys)
                    else:
                        XX = np.r_[X[tr], Xs]; yy = np.r_[y[tr], ys]
                        sw = np.r_[np.ones(len(tr)), np.full(len(ys), w_synth * len(tr) / len(ys))]
                        if mn == "SVR": m.fit(XX, yy, m__sample_weight=sw)
                        else: m.fit(XX, yy, sample_weight=sw)
                    preds[key][te] = m.predict(X[te])
        for (mn, cond), p in preds.items(): res.append(dict(model=mn, condition=cond, rep=r, **metrics(y, p)))
    if phys_pred is not None: res.append(dict(model="generator", condition="physics_direct", rep=0, **metrics(y, phys_pred)))
    for kname, p in (corr_preds or {}).items(): res.append(dict(model=kname, condition="published_correlation", rep=0, **metrics(y, p)))
    R = pd.DataFrame(res)
    return R.groupby(["condition", "model"]).agg(RMSE=("RMSE", "mean"), RMSE_sd=("RMSE", "std"), MAE=("MAE", "mean"),
                                                 R2=("R2", "mean"), AARD=("AARD", "mean"), coverage=("coverage", "mean")).round(3).reset_index()


class NestedBenchmark:
    """5-fold GroupKFold by oil on real rows. The generator is calibrated inside each training fold
    (theta_fold{f}.json from Calibrator.fit_global on U + training oils), so no test-oil WAT leaks.
    Conditions: real_only, synth_only, real_plus_synth, synth_pretrain_residual, physics_feature,
    physics_residual, physics_direct."""
    def __init__(self, table, L, theta_paths, n_synth=2000, k=5, fold_seed=0):
        self.table, self.L, self.theta_paths, self.n_synth, self.k, self.fold_seed = table, L, theta_paths, n_synth, k, fold_seed

    def folds(self):
        g = self.L.oil_group.values
        ug = np.unique(g)
        perm = np.random.default_rng(self.fold_seed).permutation(len(ug))
        gm = dict(zip(ug, perm))
        gi = np.array([gm[x] for x in g])
        return list(GroupKFold(self.k).split(self.L, self.L.wat_c, gi))

    def run(self):
        import json
        from modules.calibrate import posterior_predict
        from modules.generator import generate
        L = self.L
        y = L.wat_c.values
        X = L[FEATS].values
        mix = L.meas_method.value_counts(normalize=True).to_dict()
        P = {}

        def put(key, te, val):
            P.setdefault(key, np.full(len(y), np.nan))
            P[key][te] = val

        for f, (tr, te) in enumerate(self.folds()):
            TH = json.load(open(self.theta_paths[f]))
            th = TH["theta"]
            if "test_rows" in TH:
                assert set(TH["test_rows"]) == set(L.row_id.iloc[te]), "fold mismatch: recalibrate"
            phys_te = posterior_predict(th, self.table, L.iloc[te], K=500)[0]
            phys_tr = posterior_predict(th, self.table, L.iloc[tr], K=500)[0]
            S = pd.concat([generate("forward", self.n_synth, th, mix, seed=10 + f, table=self.table),
                           generate("anchored", self.n_synth, th, mix, seed=20 + f, table=self.table)])
            S = S[S.wax_wt_pct.between(0.2, 45) & S.pour_c.between(-60, 60)]
            Xs, ys = S[FEATS].values, S.wat_c.values
            put(("generator", "physics_direct"), te, phys_te)
            for mn, mk in models().items():
                m = mk(); m.fit(X[tr], y[tr]); put((mn, "real_only"), te, m.predict(X[te]))
                m = mk(); m.fit(Xs, ys); put((mn, "synth_only"), te, m.predict(X[te]))
                XX = np.r_[X[tr], Xs]; yy = np.r_[y[tr], ys]
                sw = np.r_[np.ones(len(tr)), np.full(len(ys), 0.5 * len(tr) / len(ys))]
                m = mk()
                (m.fit(XX, yy, m__sample_weight=sw) if mn == "SVR" else m.fit(XX, yy, sample_weight=sw))
                put((mn, "real_plus_synth"), te, m.predict(X[te]))
                base = mk(); base.fit(Xs, ys)
                m = mk(); m.fit(X[tr], y[tr] - base.predict(X[tr]))
                put((mn, "synth_pretrain_residual"), te, base.predict(X[te]) + m.predict(X[te]))
                m = mk(); m.fit(np.c_[X[tr], phys_tr], y[tr]); put((mn, "physics_feature"), te, m.predict(np.c_[X[te], phys_te]))
                m = mk(); m.fit(X[tr], y[tr] - phys_tr); put((mn, "physics_residual"), te, phys_te + m.predict(X[te]))
            print(f"✓ Fold {f + 1}/{self.k} done")
        R = pd.DataFrame([dict(model=k[0], condition=k[1], **metrics(y, p)) for k, p in P.items()]).round(3).sort_values("RMSE")
        pred = pd.DataFrame({"row_id": L.row_id, "oil_group": L.oil_group, "wat_obs": y, **{f"{a}|{b}": v for (a, b), v in P.items()}})
        return R, pred


def bootstrap_gain(pred, a, b, n=5000, seed=0):
    """Paired bootstrap over oils: RMSE(b) - RMSE(a). Positive means a is better."""
    y = pred.wat_obs.values; g = pred.oil_group.values
    ug = np.unique(g); rng = np.random.default_rng(seed); out = []
    for _ in range(n):
        idx = np.concatenate([np.where(g == x)[0] for x in rng.choice(ug, len(ug))])
        r = lambda p: np.sqrt(np.mean((p[idx] - y[idx]) ** 2))
        out.append(r(pred[b].values) - r(pred[a].values))
    o = np.array(out)
    return dict(mean=o.mean(), lo=np.percentile(o, 2.5), hi=np.percentile(o, 97.5), share_positive=(o > 0).mean())
