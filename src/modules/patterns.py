"""Patterns in the real WAT data: correlations, gaps, within-oil method spread, simple linear fit."""
import numpy as np
import pandas as pd
from scipy import stats


class DataAnalyzer:
    def __init__(self, usable):
        self.u = usable.copy()
        self.u["log_visc"] = np.log10(self.u.visc_cSt_40C)
        self.lines = []

    def _p(self, *a):
        s = " ".join(str(x) for x in a)
        self.lines.append(s)

    def correlations(self):
        cols = ["api15", "pour_c", "wax_wt_pct", "log_visc", "wdt_c"]
        rows = []
        for lab, mask in [("all usable", np.ones(len(self.u), bool)), ("no Benamara", ~self.u.benamara),
                          ("no Benamara, no tier C", ~self.u.benamara & ~self.u.tierC)]:
            v = self.u[mask]
            for c in cols:
                x = v[["wat_c", c]].dropna()
                if len(x) > 5:
                    r, pv = stats.spearmanr(x.wat_c, x[c])
                    rows.append(dict(subset=lab, feature=c, spearman=round(r, 3), n=len(x), p=pv))
        return pd.DataFrame(rows)

    def gaps(self):
        g = self.u.dropna(subset=["pour_c"])
        return dict(wat_minus_pour=g.gap.describe().round(2).to_dict(),
                    wdt_minus_wat=(self.u.wdt_c - self.u.wat_c).describe().round(2).to_dict())

    def within_oil_spread(self):
        multi = self.u.groupby("oil_group").filter(lambda x: len(x) > 1)
        sp = multi.groupby("oil_group").agg(n=("wat_c", "size"),
                                            methods=("wat_method", lambda s: "; ".join(sorted(set(map(str, s))))),
                                            wat_min=("wat_c", "min"), wat_max=("wat_c", "max"))
        sp["range"] = sp.wat_max - sp.wat_min
        return sp.sort_values("range", ascending=False)

    def linear_fit(self, exclude_benamara=True):
        c3 = self.u.dropna(subset=["api15", "pour_c", "wax_wt_pct"])
        if exclude_benamara:
            c3 = c3[~c3.benamara]
        X = np.c_[np.ones(len(c3)), c3.pour_c, c3.wax_wt_pct, c3.api15]
        y = c3.wat_c.values
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        pred = X @ b
        return dict(n=len(c3), intercept=b[0], pour=b[1], wax=b[2], api=b[3],
                    rmse=float(np.sqrt(np.mean((y - pred) ** 2))),
                    r2=float(1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)))
