# Patterns in the real data (master v9, usable rows: tier not P/X/D, WAT present)
rows 246 oils 203

## Pairwise Spearman rho (n) with WAT
api15: spearman -0.42 pearson -0.35 n=232 p=1.4e-11
pour_c: spearman 0.55 pearson 0.63 n=209 p=4.7e-18
wax_wt_pct: spearman 0.73 pearson 0.66 n=177 p=1.2e-30
log_visc: spearman 0.60 pearson 0.62 n=66 p=1.1e-07
wdt_c: spearman 0.81 pearson 0.82 n=37 p=1.5e-09

## Spearman with WAT, excluding Benamara
api15: -0.16 n=173
pour_c: 0.50 n=150
wax_wt_pct: 0.52 n=118
log_visc: 0.60 n=66
wdt_c: 0.81 n=37

## Spearman with WAT, Benamara only
api15: -0.36 n=59
pour_c: 0.80 n=59
wax_wt_pct: 0.11 n=59

## Spearman with WAT, no tier C, no Benamara
api15: -0.17 n=146
pour_c: 0.53 n=131
wax_wt_pct: 0.55 n=99
log_visc: 0.59 n=65
wdt_c: 0.81 n=37

## Correlations among inputs (Spearman, pairwise complete)
            api15  pour_c  wax_wt_pct  log_visc
api15        1.00   -0.33       -0.35     -0.89
pour_c      -0.33    1.00        0.71      0.34
wax_wt_pct  -0.35    0.71        1.00      0.42
log_visc    -0.89    0.34        0.42      1.00

## WAT minus pour point
count    209.00
mean      27.16
std       17.28
min      -11.50
25%       16.50
50%       23.40
75%       35.20
max       72.20
       count  mean   std   min   25%   50%   75%   max
cls                                                   
<20      9.0  29.6  17.2   0.8  16.7  25.9  41.4  53.7
20-30   35.0  28.9  15.0   1.9  17.5  28.3  39.6  64.8
30-40   81.0  28.9  20.5 -11.5  15.0  22.8  48.0  71.2
40-50   74.0  25.3  13.6   3.3  18.7  23.4  28.4  72.2
>50      4.0  23.0  29.0   2.0   3.6  12.6  32.0  64.5

## WDT minus WAT (same row)
count    37.00
mean      8.80
std       5.41
min      -7.80
25%       5.60
50%       8.03
75%      12.40
max      22.00

## Linear fit WAT ~ pour + wax + api15 (core3, screened, no Benamara)
all core3: n=148 WAT = 34.81 + 0.499*pour + 0.448*wax + -0.407*API ; in-sample RMSE 8.26 C, R2 0.76
core3 no Benamara: n=89 WAT = 33.02 + 0.454*pour + 0.267*wax + -0.219*API ; in-sample RMSE 9.64 C, R2 0.57
core3 no Benamara, screened: n=74 WAT = 29.64 + 0.595*pour + 0.249*wax + -0.196*API ; in-sample RMSE 8.03 C, R2 0.66

## Within-oil repeat and method spread
                   n                                                                                                            methods  wat_min  wat_max  range
oil_group                                                                                                                                                       
ans_s14            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    28.00    46.20  18.20
penara             2                                                   micro-DSC 0.5 C/min onset; viscosity-temperature break (UTM lab)    55.70    72.24  16.54
ans_s03            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    25.70    41.10  15.40
ans_s06            3  CPM; viscometry (break in viscosity-temperature curve), history erased; viscometry, previous thermal history kept    20.30    33.80  13.50
ans_s10            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    30.50    43.20  12.70
dabei_b            3                                                                   DSC; capillary viscometer; polarising microscope    23.65    34.10  10.45
dabei_a            3                                                                   DSC; capillary viscometer; polarising microscope    22.55    32.40   9.85
colombia_colorado  3                                                                                                                DSC    20.80    30.50   9.70
bz25_1             4                                                                                         micropolariscope (XP-300C)    42.00    51.00   9.00
garden_banks       2                                                                                                           CPM; DSC    34.44    43.30   8.86
ans_s05            3  CPM; viscometry (break in viscosity-temperature curve), history erased; viscometry, previous thermal history kept    31.80    40.60   8.80
cote_blanche       3                                                      ChevronTexaco (method not detailed); DSC (Total); DSC (Tulsa)    35.00    40.60   5.60
ans_s04            3  CPM; viscometry (break in viscosity-temperature curve), history erased; viscometry, previous thermal history kept    26.40    31.80   5.40
dj_crude           5                           DSC; NIRS temperature scan; NIRS wavelength scan; polarised microscopy; refractive index    45.95    50.33   4.38
uzen               2                                                   DSC cooling exotherm maximum 1 C/min; PLM (range 50-55 midpoint)    48.40    52.50   4.10
ans_s24            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    32.10    36.00   3.90
kgd6_condensate    5                                                                          ASTM D8420 / IP 389A; ASTM D8420 / IP389A    18.40    21.90   3.50
caratinga          2                                                                     DSC 0.2 C/min (Petrobras); DSC 2 C/min (Tulsa)    47.00    50.36   3.36
ans_s25            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    33.60    36.10   2.50
ans_s26            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    32.00    34.20   2.20
ans_s02            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    27.90    30.00   2.10
kumkol             2                                         DSC cooling 1 C/min (range 38.9-42.3 midpoint); PLM (range 40-45 midpoint)    40.60    42.50   1.90
ans_s08            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    27.10    29.00   1.90
ans_s23            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    30.00    31.50   1.50
ans_s01            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    27.00    28.10   1.10
singh2011_unnamed  2                                                                    CPM; other (density meter, Anton Paar DMA 5000)    57.00    58.00   1.00
angsi              2                                                                         DSC; viscosity-temperature break (UTM lab)    33.32    34.10   0.78
ans_s28            2                                             CPM; viscometry (break in viscosity-temperature curve), history erased    29.10    29.80   0.70

median within-oil range 4.239999999999998 mean 6.39 oils 28

## Method counts in usable rows
wat_method
other               87
DSC                 48
viscometry          30
CPM                 19
not stated          16
uDSC                11
ASTM D2500          11
ASTM D8420           6
viscosity            5
PLM                  4
micropolariscope     4
NIR                  3
micro-DSC            1
light                1