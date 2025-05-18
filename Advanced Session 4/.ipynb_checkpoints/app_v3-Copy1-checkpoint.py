import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import pyarrow.parquet as pq

def process_country(chunk):
    # chunk: NumPy array shape (T,)
    # rolling growth
    growth = (chunk[4:] - chunk[:-4]) / chunk[:-4]
    # rolling volatility
    vol = np.std(np.lib.stride_tricks.sliding_window_view(chunk,4), axis=1)
    return growth.mean(), vol.mean()

def main():
    # 1. Read country list
    meta = pq.read_metadata('big_panel_parquet/')
    countries = meta.schema.names[2:]  # assuming first two fields are date,value

    # 2. Memory-map the Parquet columns
    table = pq.read_table('big_panel_parquet/',
                          columns=['value']+list(countries))
    arr = table.column('value').to_pandas().values  # or use pyarrow memmap

    # 3. Parallel map over countries
    with ProcessPoolExecutor() as exe:
        futures = {
            exe.submit(process_country, arr[:, i]): countries[i]
            for i in range(len(countries))
        }
        results = {futures[f]: f.result() for f in futures}

    # 4. Aggregate per region
    regions = pd.read_parquet('country_region.parquet')
    df = pd.DataFrame.from_dict(results, orient='index', columns=['g','v'])
    df['country'] = df.index
    df = df.merge(regions, on='country')
    summary = df.groupby('region').mean()[['g','v']]
    print(summary)

if __name__ == '__main__':
    main()


