"""Extract fresh-crude bulk properties from the NOAA ADIOS Oil Library
(github.com/NOAA-ORR-ERD/noaa-oil-data, data/oil/*/*.json, CC0 public data).
Usage: python3 -I extract_noaa.py <path to data/oil> <out.csv>
One row per record, first sub-sample (fresh oil, 0 % evaporated) only.
"""
import csv, glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bulk_relations as br

CRUDE_TYPES = ('Crude Oil NOS', 'Condensate', 'Tight Oil')
WAX_NAMES = ('wax_content', 'Waxes', 'Wax')
S_NAMES = ('sulfur', 'Sulfur Content', 'Sulfur Mass Fraction', 'Sulfur', 'Sulfur Wt. %')


def T_to_C(v, u):
    if v is None:
        return None
    if u == 'K':
        return v - 273.15
    if u == 'F':
        return (v - 32) / 1.8
    return v


def mval(m):
    """Return (value, flag) from a measurement dict."""
    if m is None:
        return None, ''
    if m.get('value') is not None:
        return m['value'], ''
    lo, hi = m.get('min_value'), m.get('max_value')
    if lo is not None and hi is not None:
        return 0.5 * (lo + hi), f'range {lo}..{hi}'
    if hi is not None:
        return hi, f'max {hi} (true value at or below)'
    if lo is not None:
        return lo, f'min {lo} (true value at or above)'
    return None, ''


def dens_kgm3(m):
    v, _ = mval(m)
    if v is None:
        return None
    u = m.get('unit')
    if u in ('g/mL', 'g/cm^3'):
        return v * 1000.0
    return v


def frac_pct(m):
    v, _ = mval(m)
    if v is None:
        return None
    u = m.get('unit')
    if u == 'fraction':
        return v * 100.0
    if u == 'ppm':
        return v / 1e4
    if u == 'mg/g':
        return v / 10.0
    return v


KV = {'m^2/s': 1e6, 'cSt': 1.0, 'mm^2/s': 1.0}
DV = {'kg/(m s)': 1000.0, 'mPas': 1.0, 'mPa.s': 1.0, 'mPa s': 1.0, 'cP': 1.0}


def main(root, out):
    rows = []
    for f in sorted(glob.glob(os.path.join(root, '*', '*.json'))):
        d = json.load(open(f))
        m = d['metadata']
        if m.get('product_type') not in CRUDE_TYPES or not d.get('sub_samples'):
            continue
        s = d['sub_samples'][0]
        pp = s.get('physical_properties', {}) or {}
        notes = []
        api = m.get('API')
        # densities
        dens = []
        for x in pp.get('densities', []) or []:
            r = dens_kgm3(x.get('density'))
            t = T_to_C(x.get('ref_temp', {}).get('value'), x.get('ref_temp', {}).get('unit'))
            if r and t is not None and 600 < r < 1100:
                dens.append((t, r))
        rho15 = None
        d15 = [r for t, r in dens if abs(t - 15) < 0.6]
        if d15:
            rho15 = d15[0]
        elif dens:
            t, r = min(dens, key=lambda z: abs(z[0] - 15))
            if abs(t - 15) <= 30:
                rho15 = br.rho15_from_rho_T_1980(r, t)
                notes.append(f'rho15 from rho at {t:.1f} C (Table 53A form)')
        if rho15 is None and api is not None:
            rho15 = br.rho15_from_api(api)
            notes.append('rho15 from API')
        if api is None and rho15 is not None:
            api = br.api_from_rho15(rho15)
            notes.append('API from rho15')
        # viscosities -> kinematic list
        kv = []
        for x in pp.get('kinematic_viscosities', []) or []:
            v, flag = mval(x.get('viscosity'))
            u = x.get('viscosity', {}).get('unit')
            t = T_to_C(x.get('ref_temp', {}).get('value'), x.get('ref_temp', {}).get('unit'))
            if v is None or u not in KV or t is None or flag:
                continue
            kv.append((t, v * KV[u], 'kin'))
        for x in pp.get('dynamic_viscosities', []) or []:
            v, flag = mval(x.get('viscosity'))
            u = x.get('viscosity', {}).get('unit')
            t = T_to_C(x.get('ref_temp', {}).get('value'), x.get('ref_temp', {}).get('unit'))
            if v is None or u not in DV or t is None or flag or rho15 is None:
                continue
            rhoT = br.rho_T_from_rho15_1980(rho15, t)
            kv.append((t, br.dyn_to_kin(v * DV[u], rhoT), 'dyn'))
        kv = sorted({round(t, 2): (t, v, k) for t, v, k in kv if v > 0}.values())
        visc40, vflag = None, ''
        at40 = [v for t, v, k in kv if abs(t - 40) < 0.6]
        if at40:
            visc40 = at40[0]
            vflag = 'measured at 40 C'
        elif len(kv) >= 2:
            # choose the two points that bracket 40 C, else the two nearest
            below = [z for z in kv if z[0] < 40]
            above = [z for z in kv if z[0] > 40]
            if below and above:
                p1, p2 = below[-1], above[0]
                how = 'interpolated'
            else:
                pts = sorted(kv, key=lambda z: abs(z[0] - 40))[:2]
                p1, p2 = sorted(pts)
                how = 'extrapolated'
            if abs(p1[0] - p2[0]) >= 5 and min(p1[1], p2[1]) > 0.3:
                try:
                    A, B = br.walther_fit(p1[1], p1[0], p2[1], p2[0])
                    if B > 0:
                        visc40 = br.walther_visc(A, B, 40.0)
                        vflag = f'Walther {how} from {p1[0]:.0f} C and {p2[0]:.0f} C'
                    else:
                        vflag = 'viscosity rises with T in source; not converted'
                except ValueError:
                    vflag = 'Walther failed'
        pour, pflag = None, ''
        if pp.get('pour_point'):
            mm = pp['pour_point'].get('measurement')
            pour, pflag = mval(mm)
            pour = T_to_C(pour, (mm or {}).get('unit'))
        wax = sul = None
        for b in s.get('bulk_composition', []) or []:
            if b['name'] in WAX_NAMES and wax is None:
                wax = frac_pct(b.get('measurement'))
            if b['name'] in S_NAMES and sul is None:
                sul = frac_pct(b.get('measurement'))
        ref = (m.get('reference') or {}).get('reference', '').replace('\n', ' ')[:160]
        rows.append({
            'oil_id': d.get('oil_id'), 'name': m.get('name'), 'location': m.get('location'),
            'product_type': m.get('product_type'), 'api': api,
            'density15': rho15, 'visc40_cSt': visc40, 'visc_flag': vflag,
            'n_visc_points': len(kv),
            'pour_c': pour, 'pour_flag': pflag, 'wax_wt_pct': wax, 'sulphur': sul,
            'collection': d.get('oil_id', '')[:2], 'reference': ref,
            'notes': '; '.join(notes)})
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print(len(rows), 'rows written to', out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
