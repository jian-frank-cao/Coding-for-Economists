import pandas as pd

try:
    profile
except NameError:
    def profile(func):
        return func

@profile
def run_analysis_v1():
    # Load Data
    gdp = pd.read_csv(
        'gdp_panel.csv',
        usecols=['code','year','value'], # Only read necessary columns
        parse_dates=['year'],
        dtype={'code':'category'}
    ).sort_values(['code','year'])

    regions = pd.read_csv(
        'country_region.csv',
        usecols=['code','region'], # Only read necessary columns
        dtype={'code':'category', 'region':'category'}
    ).sort_values(['code'])

    window = 52
    # Compute GDP Growth and Volatility
    # pivot to wide form: rows=date, cols=country
    panel = gdp.pivot(index='year', columns='code', values='value')
    
    # rolling growth: pct_change over window periods
    growth = panel.pct_change(periods=window, fill_method=None)
    
    # rolling volatility: std over window periods
    vol = panel.rolling(window=window).std()
    
    # melt back to long form & merge region info
    growth = growth.stack().rename('growth').reset_index()
    vol    = vol.stack().rename('vol').reset_index()
    metrics = pd.merge(growth, vol, on=['year','code'])
    metrics = metrics.merge(regions, on='code')

    # Aggregate Regions
    result = (
        metrics
        .groupby(['region'], observed=False)
        .agg(avg_growth=('growth','mean'),
             avg_vol=('vol','mean'))
    )
    return result

if __name__ == '__main__':
    run_analysis_v1()