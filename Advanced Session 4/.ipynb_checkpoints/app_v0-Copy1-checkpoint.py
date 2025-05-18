import csv
from collections import defaultdict
from statistics import pstdev

def load_csv(path):
    data = defaultdict(list)
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            country = row['country']
            data[country].append(float(row['value']))
    return data

def compute_metrics(data, window=4):
    out = {}
    for country, series in data.items():
        growth = []
        vol = []
        for i in range(window, len(series)):
            prev = series[i-window]
            curr = series[i]
            growth.append((curr - prev) / prev)
            vol.append(pstdev(series[i-window:i]))
        out[country] = {'growth': growth, 'vol': vol}
    return out

def aggregate_region(metrics, mapping):
    # mapping: country → region
    agg = defaultdict(lambda: {'growth': [], 'vol': []})
    for country, m in metrics.items():
        region = mapping[country]
        agg[region]['growth'].extend(m['growth'])
        agg[region]['vol'].extend(m['vol'])
    # compute regional averages
    return {r: {
        'avg_growth': sum(d['growth'])/len(d['growth']),
        'avg_vol': sum(d['vol'])/len(d['vol'])
    } for r, d in agg.items()}

if __name__ == '__main__':
    data = load_csv('big_panel.csv')             # millions of rows
    mapping = load_csv('country_region.csv')     # small file
    metrics = compute_metrics(data)
    region_stats = aggregate_region(metrics, mapping)
    print(region_stats)


def run_analysis():
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

    mapping = {}
    path = 'country_region.csv'
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            country = row['code']
            region = row['region']
            if country not in mapping:
                mapping[country] = region

    # Compute dgp growth rate and volitility
    metrics = {}
    window = 4
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
        region = mapping[country]
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