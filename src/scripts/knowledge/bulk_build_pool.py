"""Build agents/bulk/bulk_pool_clean.csv (one row per distinct crude) and
local_pool_stats.md from the local bulk pools.  python3 -I build_pool.py"""
import os, re, sys
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bulk_relations as br

STUDY = os.path.abspath(os.path.join(HERE, '..', '..'))
SCR = os.path.abspath(os.path.join(STUDY, '..'))
P = {
    'master_v9': os.path.join(STUDY, 'master_v9.csv'),
    'nigeria_bulk': os.path.join(SCR, 'harvest4/merged/nigeria_bulk_only_raw.csv'),
    'round3_bulk': os.path.join(SCR, 'harvest6/merged/round3_bulk_only_raw.csv'),
    'totalenergies': os.path.join(SCR, 'harvest/assays/totalenergies_whole_crude_all.csv'),
    'alaska_ans2': os.path.join(SCR, 'ans2/alaska_no_wat_samples.csv'),
}
NUM = r'(\d+(?:\.\d+)?)'


def f2c(t, u):
    return (t - 32) / 1.8 if u.upper() == 'F' else t


def parse_kin_visc(text):
    """Return list of (T_C, cSt) pairs stated in free text (kinematic only)."""
    s = str(text)
    out = []
    for v, t, u in re.findall(NUM + r'\s*(?:cSt|mm2/s)\s+at\s+' + NUM + r'\s*(C|F)\b', s):
        out.append((f2c(float(t), u), float(v)))
    for t, u, v in re.findall(NUM + r'\s*(C|F)\s*\(\s*' + NUM + r'\s*(?:cSt|mm2/s)\s*\)', s):
        out.append((f2c(float(t), u), float(v)))
    for t, u, v in re.findall(NUM + r'\s*(C|F)\s+' + NUM + r'\s*(?:cSt|mm2/s)', s):
        out.append((f2c(float(t), u), float(v)))
    m = re.search(r'at\s+((?:\d+(?:\.\d+)?,?\s*(?:and\s*)?)+)\s*(C|F)\s*\(((?:\d+(?:\.\d+)?,?\s*)+)cSt\)', s)
    if m:
        ts = [float(x) for x in re.findall(NUM, m.group(1))]
        vs = [float(x) for x in re.findall(NUM, m.group(3))]
        if len(ts) == len(vs):
            out += [(f2c(t, m.group(2)), v) for t, v in zip(ts, vs)]
    # unique by temperature
    d = {}
    for t, v in out:
        d.setdefault(round(t, 1), v)
    return sorted(d.items())


def visc40_from_pairs(pairs):
    if len(pairs) < 2:
        return None, ''
    below = [p for p in pairs if p[0] < 40]
    above = [p for p in pairs if p[0] > 40]
    if below and above:
        p1, p2, how = below[-1], above[0], 'interpolated'
    else:
        p1, p2 = sorted(sorted(pairs, key=lambda p: abs(p[0] - 40))[:2])
        how = 'extrapolated'
    try:
        A, B = br.walther_fit(p1[1], p1[0], p2[1], p2[0])
    except ValueError:
        return None, ''
    if B <= 0:
        return None, ''
    return br.walther_visc(A, B, 40.0), f'visc40 Walther {how} from {p1[1]} cSt at {p1[0]:.1f} C and {p2[1]} cSt at {p2[0]:.1f} C'


def std_rows():
    rows = []
    # master_v9 and the two bulk-only pools share a schema
    for src in ('master_v9', 'nigeria_bulk', 'round3_bulk'):
        d = pd.read_csv(P[src])
        for _, r in d.iterrows():
            note = []
            rho, api = r.get('density_kg_m3'), r.get('api')
            tdens = r.get('density_T_c', 15.0) if src == 'master_v9' else 15.0
            if pd.isna(tdens):
                tdens = 15.0
            rho15 = np.nan
            if pd.notna(rho) and float(rho) < 2.0:
                rho = float(rho) * 1000.0
                note.append('density given in g/cm3, multiplied by 1000')
            if pd.notna(rho):
                if abs(tdens - 15.0) > 0.6:
                    rho15 = br.rho15_from_rho_T_1980(float(rho), float(tdens))
                    note.append(f'density at {tdens:g} C corrected to 15 C (1980 Table 53A form)')
                else:
                    rho15 = float(rho)
            if pd.isna(api) and pd.notna(rho15):
                api = br.api_from_rho15(rho15)
                note.append('API computed from density15 (API MPMS 11.1-2004)')
            if pd.isna(rho15) and pd.notna(api):
                rho15 = br.rho15_from_api(float(api))
                note.append('density15 computed from API (API MPMS 11.1-2004)')
            v40 = r.get('visc_cSt_40C')
            if pd.isna(v40):
                v, fl = visc40_from_pairs(parse_kin_visc(r.get('notes')))
                if v is not None:
                    v40 = v
                    note.append(fl)
            pm = str(r.get('pour_method', ''))
            if re.search(r'max|upper|<', pm, re.I):
                note.append(f'pour point method "{pm}" (may be an upper bound)')
            rows.append(dict(name=r.get('oil_name'), group=r.get('oil_group'), country=r.get('country_basin'),
                             api15=api, density15=rho15, visc40_cSt=v40, pour_c=r.get('pour_c'),
                             wax_wt_pct=r.get('wax_wt_pct'), wax_method=r.get('wax_method'),
                             sulphur=np.nan, has_wat=pd.notna(r.get('wat_c')) if src == 'master_v9' else False,
                             source=f"{src}:{r.get('row_id')}", notes='; '.join(note)))
    # TotalEnergies whole-crude assays
    d = pd.read_csv(P['totalenergies'])
    for _, r in d.iterrows():
        note = []
        v40 = r['Viscosity @ 40°C (cSt)']
        rows.append(dict(name=r['Traded Crude'], group=r['Traded Crude'], country=r['Origin'],
                         api15=r['API Gravity'], density15=r['Density @ 15°C (g/cc)'] * 1000.0,
                         visc40_cSt=v40, pour_c=r['Pour Point (°C)'], wax_wt_pct=np.nan, wax_method='',
                         sulphur=r['Total Sulphur (% wt)'], has_wat=False,
                         source=f"totalenergies:{r['file']}", notes='; '.join(note)))
    # Alaska ANS samples without WAT
    d = pd.read_csv(P['alaska_ans2'])
    for _, r in d.iterrows():
        rows.append(dict(name=f"ANS sample {r['sample']}", group='ans_condensate_like', country='USA (Alaska North Slope)',
                         api15=r['api'], density15=br.rho15_from_api(r['api']), visc40_cSt=np.nan,
                         pour_c=r['pour_c'], wax_wt_pct=np.nan, wax_method='', sulphur=np.nan, has_wat=False,
                         source=f"alaska_ans2:{r['sample']}",
                         notes='density15 computed from API; pour point censored (below -28 C reported as -28)' if r['pour_censored'] else 'density15 computed from API'))
    return pd.DataFrame(rows)


STOP = {'crude', 'oil', 'blend', 'the', 'export', 'light', 'heavy', 'medium'}


def key(name):
    toks = re.findall(r'[a-z]+', str(name).lower())
    k = ''.join(t for t in toks if t not in STOP)
    return k or ''.join(toks)


def dedupe(df):
    df = df.copy()
    for c in ['api15', 'density15', 'visc40_cSt', 'pour_c', 'wax_wt_pct', 'sulphur']:
        s = df[c].astype(str)
        cens = df[c].notna() & s.str.startswith('<')
        df.loc[cens, 'notes'] = df.loc[cens, 'notes'].map(lambda n: n) + df.loc[cens, c].map(
            lambda v, c=c: f'; {c} reported as "{v}", stored as the bound value (censored)')
        df[c] = pd.to_numeric(s.str.lstrip('<'), errors='coerce')
    df['nkey'] = df['name'].map(key)
    # light/heavy are meaningful (Bonny Light vs Bonny Medium), keep them in key
    df['nkey2'] = df['name'].map(lambda n: ''.join(t for t in re.findall(r'[a-z]+', re.sub(r'\(.*?\)', '', str(n)).lower()) if t not in {'crude', 'oil', 'the', 'export'}))
    df['api_r'] = df['api15'].round(0)
    out = []
    for (k, a), g in df.groupby(['nkey2', 'api_r'], dropna=False, sort=False):
        g = g.sort_values('has_wat', ascending=False)
        rec = {}
        for c in ['name', 'group', 'country', 'api15', 'density15', 'visc40_cSt', 'pour_c', 'wax_wt_pct', 'wax_method', 'sulphur']:
            vals = g[c].dropna()
            vals = vals[vals.astype(str) != '']
            rec[c] = vals.iloc[0] if len(vals) else np.nan
        rec['n_records'] = len(g)
        rec['has_wat'] = bool(g['has_wat'].any())
        rec['source'] = ' | '.join(g['source'])
        n = [x for x in g['notes'] if x]
        rec['notes'] = ' | '.join(dict.fromkeys(n))
        if len(g) > 1:
            sp = {c: (g[c].max() - g[c].min()) for c in ['api15', 'pour_c', 'wax_wt_pct'] if g[c].notna().sum() > 1}
            sp = {c: v for c, v in sp.items() if v > 0}
            if sp:
                rec['notes'] = (rec['notes'] + ' | ' if rec['notes'] else '') + 'merged records differ: ' + ', '.join(f'{c} spread {v:.1f}' for c, v in sp.items())
        out.append(rec)
    return pd.DataFrame(out)


def stats_md(raw, clean):
    cols = ['api15', 'density15', 'visc40_cSt', 'pour_c', 'wax_wt_pct', 'sulphur']
    L = ['# Local bulk pool statistics', '',
         'Built by agents/bulk/build_pool.py from master_v9.csv, harvest4 nigeria_bulk_only_raw.csv, harvest6 round3_bulk_only_raw.csv, '
         'harvest/assays totalenergies_whole_crude_all.csv and ans2 alaska_no_wat_samples.csv. '
         'Density at other temperatures corrected to 15 C with the 1980 crude-oil tables form (K0 = 613.9723). '
         'Missing API or density filled from the other with API MPMS 11.1-2004. Viscosity at 40 C converted with ASTM D341 (Walther) only where two kinematic values at other temperatures were stated; those rows say so in notes.', '',
         f'Raw records: {len(raw)}. Distinct crudes after merging same name and same rounded API: {len(clean)}.', '']
    L.append('## Records per source (raw)')
    L.append('')
    L.append('| source | records |')
    L.append('|---|---|')
    for s, n in raw['source'].str.split(':').str[0].value_counts().items():
        L.append(f'| {s} | {n} |')
    L += ['', '## Univariate summary of the cleaned pool (one row per distinct crude)', '',
          '| variable | n | mean | sd | min | p10 | p25 | median | p75 | p90 | max |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for c in cols + ['log10_visc40']:
        x = np.log10(clean['visc40_cSt'].astype(float)) if c == 'log10_visc40' else clean[c].astype(float)
        x = x.dropna()
        if len(x) == 0:
            continue
        q = x.quantile([.1, .25, .5, .75, .9])
        L.append(f'| {c} | {len(x)} | {x.mean():.3g} | {x.std():.3g} | {x.min():.3g} | {q[.1]:.3g} | {q[.25]:.3g} | {q[.5]:.3g} | {q[.75]:.3g} | {q[.9]:.3g} | {x.max():.3g} |')
    c2 = clean[cols].astype(float).copy()
    c2['log10_visc40'] = np.log10(c2['visc40_cSt'])
    c2 = c2.drop(columns=['visc40_cSt', 'density15'])
    for meth in ('pearson', 'spearman'):
        L += ['', f'## Pairwise {meth} correlations (pairwise complete; n in brackets)', '']
        vs = list(c2.columns)
        L.append('| | ' + ' | '.join(vs) + ' |')
        L.append('|---' * (len(vs) + 1) + '|')
        for a in vs:
            cells = []
            for b in vs:
                m = c2[[a, b]].dropna()
                if len(m) < 5 or a == b:
                    cells.append('1' if a == b else 'n<5')
                else:
                    cells.append(f'{m[a].corr(m[b], method=meth):.2f} ({len(m)})')
            L.append(f'| {a} | ' + ' | '.join(cells) + ' |')
    L += ['', '## Completeness of input combinations (cleaned pool)', '']
    combos = {'api+pour': ['api15', 'pour_c'], 'api+pour+wax': ['api15', 'pour_c', 'wax_wt_pct'],
              'api+pour+visc40': ['api15', 'pour_c', 'visc40_cSt'], 'api+pour+wax+visc40': ['api15', 'pour_c', 'wax_wt_pct', 'visc40_cSt'],
              'api+visc40': ['api15', 'visc40_cSt'], 'api+wax': ['api15', 'wax_wt_pct']}
    for k, v in combos.items():
        L.append(f'- {k}: {clean[v].dropna().shape[0]} crudes')
    # simple fits useful for the generator
    L += ['', '## Simple fitted relations on the cleaned pool (for consistency checks, not physics)', '']
    m = clean[['api15', 'visc40_cSt']].dropna().astype(float)
    m = m[m.visc40_cSt > 0]
    if len(m) > 10:
        b, a = np.polyfit(m.api15, np.log10(m.visc40_cSt), 1)
        res = np.log10(m.visc40_cSt) - (a + b * m.api15)
        L.append(f'- log10(visc40 cSt) = {a:.3f} + ({b:.4f}) x API; n = {len(m)}, residual sd = {res.std():.3f} log10 units')
    m = clean[['wax_wt_pct', 'pour_c']].dropna().astype(float)
    if len(m) > 10:
        b, a = np.polyfit(m.wax_wt_pct, m.pour_c, 1)
        res = m.pour_c - (a + b * m.wax_wt_pct)
        L.append(f'- pour_c = {a:.2f} + {b:.3f} x wax_wt_pct; n = {len(m)}, residual sd = {res.std():.1f} C')
    m = clean[['api15', 'wax_wt_pct', 'pour_c']].dropna().astype(float)
    if len(m) > 10:
        X = np.c_[np.ones(len(m)), m.api15, m.wax_wt_pct]
        coef, *_ = np.linalg.lstsq(X, m.pour_c, rcond=None)
        res = m.pour_c - X @ coef
        L.append(f'- pour_c = {coef[0]:.2f} + ({coef[1]:.3f}) x API + {coef[2]:.3f} x wax; n = {len(m)}, residual sd = {res.std():.1f} C')
    L += ['', '## Caveats', '',
          '- Wax content methods differ (UOP 46 acetone precipitation, HTGC, DSC, not stated). Values are pooled as reported.',
          '- Some pour points are upper bounds (ASTM D5853 maximum, or censored such as "below -28 C"); see notes.',
          '- Several TotalEnergies sheets appear in more than one pool; merging by name and rounded API removes most repeats, but different sample years of the same grade with different API stay as separate rows.',
          '- Viscosity at 40 C from Walther extrapolation outside the measured range is less reliable, especially when the lower temperature is below the WAT (non-Newtonian, wax-structured oil).',
          '- API is defined at 60 F (15.56 C); the column is named api15 as requested.']
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    raw = std_rows()
    clean = dedupe(raw)
    cols = ['name', 'group', 'country', 'api15', 'density15', 'visc40_cSt', 'pour_c', 'wax_wt_pct', 'wax_method', 'sulphur', 'has_wat', 'n_records', 'source', 'notes']
    for c in ['api15', 'density15', 'visc40_cSt']:
        clean[c] = clean[c].astype(float).round(3)
    clean[cols].to_csv(os.path.join(HERE, 'bulk_pool_clean.csv'), index=False)
    open(os.path.join(HERE, 'local_pool_stats.md'), 'w').write(stats_md(raw, clean))
    print(len(raw), 'raw ->', len(clean), 'distinct')
