"""Append NOAA ADIOS fresh-crude statistics to local_pool_stats.md. python3 -I noaa_stats.py"""
import numpy as np, pandas as pd
d = pd.read_csv('noaa_adios_crude_bulk.csv')
d['log10_visc40'] = np.log10(d.visc40_cSt)
good_v = ~d.visc_flag.fillna('').str.contains('extrapolated|rises|failed')
d.loc[~good_v, 'log10_visc40'] = np.nan          # use measured or interpolated only
d.loc[d.pour_flag.fillna('').str.startswith(('max', 'min')), 'pour_c'] = np.nan  # drop censored pours
cols = ['api', 'density15', 'log10_visc40', 'pour_c', 'wax_wt_pct', 'sulphur']
L = ['', '# External reference pool: NOAA ADIOS Oil Library (fresh crude oils)', '',
     'Source: github.com/NOAA-ORR-ERD/noaa-oil-data (data/oil, cloned 2026-11-05), records with product_type Crude Oil NOS, Condensate or Tight Oil, first (fresh) sub-sample. '
     'Includes Environment and Climate Change Canada (EC) records, legacy ADIOS records (AD; many from Jokuty et al. 1999 catalogue, oil company letters, OGJ data books), ExxonMobil assays (EX) and others. '
     'Extraction: agents/bulk/extract_noaa.py -> agents/bulk/noaa_adios_crude_bulk.csv. Dynamic viscosities converted to kinematic with density at that temperature. '
     'For the statistics below, visc40 uses only values measured at 40 C or Walther-interpolated between bracketing temperatures (extrapolated values dropped), and censored pour points (max or min only) are dropped. '
     'EC and AD may hold the same oil twice; no de-duplication across collections.', '',
     f'Records: {len(d)}; by collection: ' + ', '.join(f'{k} {v}' for k, v in d.collection.value_counts().items()), '',
     '| variable | n | mean | sd | min | p10 | p25 | median | p75 | p90 | max |', '|---|---|---|---|---|---|---|---|---|---|---|']
for c in cols:
    x = d[c].dropna()
    q = x.quantile([.1, .25, .5, .75, .9])
    L.append(f'| {c} | {len(x)} | {x.mean():.3g} | {x.std():.3g} | {x.min():.3g} | {q[.1]:.3g} | {q[.25]:.3g} | {q[.5]:.3g} | {q[.75]:.3g} | {q[.9]:.3g} | {x.max():.3g} |')
c2 = d[['api', 'pour_c', 'wax_wt_pct', 'sulphur', 'log10_visc40']]
for meth in ('pearson', 'spearman'):
    L += ['', f'## NOAA pairwise {meth} correlations (n in brackets)', '']
    vs = list(c2.columns)
    L.append('| | ' + ' | '.join(vs) + ' |'); L.append('|---' * (len(vs) + 1) + '|')
    for a in vs:
        cells = []
        for b in vs:
            m = c2[[a, b]].dropna()
            cells.append('1' if a == b else (f'{m[a].corr(m[b], method=meth):.2f} ({len(m)})' if len(m) >= 5 else 'n<5'))
        L.append(f'| {a} | ' + ' | '.join(cells) + ' |')
L += ['', '## NOAA simple fits', '']
m = d[['api', 'log10_visc40']].dropna(); m = m[(m.api > 10) & (m.api < 60)]
b, a = np.polyfit(m.api, m.log10_visc40, 1); r = m.log10_visc40 - (a + b * m.api)
L.append(f'- log10(visc40 cSt) = {a:.3f} + ({b:.4f}) x API, 10 < API < 60; n = {len(m)}, residual sd = {r.std():.3f}')
m = d[['wax_wt_pct', 'pour_c']].dropna()
b, a = np.polyfit(m.wax_wt_pct, m.pour_c, 1); r = m.pour_c - (a + b * m.wax_wt_pct)
L.append(f'- pour_c = {a:.2f} + {b:.3f} x wax_wt_pct; n = {len(m)}, residual sd = {r.std():.1f} C')
m = d[['api', 'wax_wt_pct', 'pour_c', 'log10_visc40']].dropna()
if len(m) > 20:
    X = np.c_[np.ones(len(m)), m.api, m.wax_wt_pct, m.log10_visc40]
    co, *_ = np.linalg.lstsq(X, m.pour_c, rcond=None); r = m.pour_c - X @ co
    L.append(f'- pour_c = {co[0]:.2f} + ({co[1]:.3f}) API + {co[2]:.3f} wax + ({co[3]:.2f}) log10 visc40; n = {len(m)}, residual sd = {r.std():.1f} C')
L += ['', '## Pour point by wax class (NOAA)', '', '| wax wt% | n | pour median C | pour p10 | pour p90 |', '|---|---|---|---|---|']
m = d[['wax_wt_pct', 'pour_c']].dropna()
for lo, hi in [(0, 2), (2, 4), (4, 6), (6, 10), (10, 15), (15, 40)]:
    g = m[(m.wax_wt_pct >= lo) & (m.wax_wt_pct < hi)].pour_c
    if len(g):
        L.append(f'| {lo}-{hi} | {len(g)} | {g.median():.0f} | {g.quantile(.1):.0f} | {g.quantile(.9):.0f} |')
L += ['', '## Wax content by API class (NOAA)', '', '| API | n | wax median | wax p10 | wax p90 |', '|---|---|---|---|---|']
m = d[['api', 'wax_wt_pct']].dropna()
for lo, hi in [(0, 20), (20, 30), (30, 40), (40, 50), (50, 90)]:
    g = m[(m.api >= lo) & (m.api < hi)].wax_wt_pct
    if len(g):
        L.append(f'| {lo}-{hi} | {len(g)} | {g.median():.1f} | {g.quantile(.1):.1f} | {g.quantile(.9):.1f} |')
L += ['', '## Walther (ASTM D341) interpolation check on NOAA crudes', '',
      '- 156 crude oils with 3 or more kinematic viscosities above pour point + 5 C: predicting the middle temperature from the outer two gave mean error +0.99 %, mean absolute error 3.6 %, median absolute 0.36 %, 90th percentile absolute 12 % (163 cases).']
open('local_pool_stats.md', 'a').write('\n'.join(L) + '\n')
print('\n'.join(L))
