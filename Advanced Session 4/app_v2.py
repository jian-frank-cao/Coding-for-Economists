import dask.dataframe as dd
import pandas as pd

try:
    profile
except NameError:
    def profile(func):
        return func

def summarize_country(df, window=52):
    # If this slice is empty, return an empty DataFrame
    if df.empty:
        return pd.DataFrame(columns=['code','mean_growth','mean_vol'])

    # Otherwise do the rolling stats
    df = df.sort_values('year')
    growth = df['value'].pct_change(periods=window, fill_method=None).mean()
    vol    = df['value'].rolling(window=window).std().mean()
    return pd.DataFrame({
        'code':        [df['code'].iat[0]],
        'mean_growth': [growth],
        'mean_vol':    [vol]
    })

@profile
def run_analysis_v2():
    # Load data
    ddf = dd.read_parquet(
        'gdp_panel_parquet/',
        columns=['code','year','value'],
        engine='pyarrow'
    )
    
    regions = dd.read_parquet('country_region_parquet/')

    # Compute GDP Growth and Volatility
    meta = pd.DataFrame({
        'code':        pd.Series(dtype='object'),
        'mean_growth': pd.Series(dtype='float64'),
        'mean_vol':    pd.Series(dtype='float64'),
    })
    
    country_summaries = ddf.groupby('code', observed=True).apply(
        summarize_country,
        meta=meta
    )
    
    country_summaries = country_summaries.reset_index(drop=True)

    # Aggregate regions
    country_summaries = country_summaries.astype({'code': 'string'})
    regions = regions.astype({'code': 'string'})
    
    country_summaries = country_summaries.merge(regions, on='code')
    
    result = (
        country_summaries
        .groupby('region', observed=True)[['mean_growth', 'mean_vol']]
        .mean()
        .compute()
    )
    return result

if __name__ == '__main__':
    run_analysis_v2()
