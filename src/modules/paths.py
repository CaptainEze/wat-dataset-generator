import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

DATA = os.path.join(ROOT, "data")
MASTER = os.path.join(DATA, "master", "wat_master.csv")
BULK_DIR = os.path.join(DATA, "bulk")
NOAA_POOL = os.path.join(BULK_DIR, "noaa_adios_crude_bulk.csv")
LOCAL_POOL = os.path.join(BULK_DIR, "bulk_pool_clean.csv")
LATENT_TABLE = os.path.join(DATA, "derived", "latent_table.npz")
SYNTHETIC_DIR = os.path.join(DATA, "synthetic")
KNOWLEDGE = os.path.join(ROOT, "knowledge")
PARAMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")

RESULTS = os.path.join(ROOT, "results")
PLOTS = os.path.join(ROOT, "plots")


def ensure_dirs():
    for d in (RESULTS, PLOTS):
        os.makedirs(d, exist_ok=True)
