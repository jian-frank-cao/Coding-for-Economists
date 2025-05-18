import dask.dataframe as dd

def main():
    # assume we've preconverted CSV→Parquet once (fast repeated loads)
    ddf = dd.read_parquet('big_panel_parquet/',
                          columns=['country','date','value'])

    # ensure dtypes
    ddf['country'] = ddf['country'].astype('category')
    ddf['date'] = dd.to_datetime(ddf['date'])

    # pivot via Dask:
    panel = ddf.set_index(['date','country']).unstack('country')['value']

    growth = panel.pct_change(periods=4)
    vol    = panel.rolling(window=4).std()

    # stack back
    merged = dd.concat([
        growth.stack().rename('growth').reset_index(),
        vol.stack().rename('vol').reset_index().loc[:, ['vol']]
    ], axis=1)

    regions = dd.read_parquet('country_region.parquet')
    merged = merged.merge(regions, on='country')

    # groupby + compute in parallel
    result = merged.groupby('region').agg({'growth':'mean','vol':'mean'}).compute()
    print(result)

if __name__ == '__main__':
    main()
