import csv
from statistics import pstdev

try:
    profile
except NameError:
    def profile(func):
        return func

@profile
def run_analysis_v0():
    # Load Data
    gdp = {}
    path = 'gdp_panel.csv'
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            country = row['code']
            value = float(row['value'])
            if country not in gdp:
                gdp[country] = []
            gdp[country].append(value)
    
    regions = {}
    path = 'country_region.csv'
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            country = row['code']
            region = row['region']
            if country not in regions:
                regions[country] = region

    # Compute dgp growth rate and volitility
    metrics = {}
    window = 52
    for country, series in gdp.items():
        growth = []
        vol = []
        for i in range(window, len(series)):
            prev = series[i-window]
            curr = series[i]
            growth.append((curr - prev) / prev)
            vol.append(pstdev(series[i-window:i]))
        metrics[country] = {'growth': growth, 'vol': vol}

    # Aggregate Regions
    agg = {}  # plain dict

    for country, m in metrics.items():
        region = regions[country]
        if region not in agg:
            agg[region] = {'growth': [], 'vol': []}
        agg[region]['growth'].extend(m['growth'])
        agg[region]['vol'].extend(m['vol'])
    
    result = {}
    for region, d in agg.items():
        total_growth = sum(d['growth'])
        total_vol    = sum(d['vol'])
        count_growth = len(d['growth'])
        count_vol    = len(d['vol'])
        result[region] = {
            'avg_growth': total_growth / count_growth if count_growth else 0,
            'avg_vol':    total_vol    / count_vol    if count_vol    else 0
        }
    return result

if __name__ == '__main__':
    run_analysis_v0()