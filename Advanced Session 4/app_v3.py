import os
import glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from dask.distributed import Client

try:
    profile
except NameError:
    def profile(func):
        return func

def discover_country_tasks(base_dir):
    tasks = []
    for entry in os.listdir(base_dir):
        full = os.path.join(base_dir, entry)
        if not (entry.startswith("code=") and os.path.isdir(full)):
            continue

        code = entry.split("=", 1)[1]
        pattern = os.path.join(full, "*.parquet")
        files = sorted(glob.glob(pattern))
        if files:
            tasks.append((code, files))
    return tasks

def process_country(code, parquet_paths, window = 52):
    # parquet_paths: list of all .parquet files for a single country-partition
    # read them all (value only), concatenate into one 1-D numpy array
    arrays = []
    for path in parquet_paths:
        tbl = pq.read_table(path, columns=['value'])
        arrays.append(tbl.column('value').to_numpy())
    series = np.concatenate(arrays)
    # now do the window‐period rolling growth & vol
    growth = (series[window:] - series[:-window]) / series[:-window]
    windows = np.lib.stride_tricks.sliding_window_view(series, window)
    vol    = np.std(windows, axis=1)
    return code, (growth.mean(), vol.mean())

@profile
def run_analysis_v3():
    # Discover tasks
    tasks = discover_country_tasks('gdp_panel_parquet/')

    # Launch Dask
    client = Client() 

    # Submit Tasks
    futures = client.map(lambda args: process_country(*args), tasks)
    results = client.gather(futures)

    # Close Dask
    client.close() 

    # Build DataFrame & merge
    df = pd.DataFrame(
        [(code, g, v) for code, (g, v) in results],
        columns=['code','avg_growth','avg_vol']
    )
    regions = pd.read_csv('country_region.csv', dtype={"code": str})
    df = df.merge(regions, on="code", how="left")

    # Aggregate by region
    result = df.groupby("region")[["avg_growth", "avg_vol"]].mean()

    return result

if __name__ == '__main__':
    run_analysis_v3()
