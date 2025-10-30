import math
from types import SimpleNamespace
from collections import defaultdict

import analyzer


def test_compute_statistics_basic():
    values = [1.0, 2.0, 3.0, 4.0]
    stats = analyzer.compute_statistics(values)

    assert stats['count'] == 4
    assert stats['min'] == 1.0
    assert stats['max'] == 4.0
    assert stats['average'] == 2.5
    # population std dev: sqrt(((1.5)^2 + (0.5)^2 + (0.5)^2 + (1.5)^2)/4) = sqrt(5/4) = sqrt(1.25)
    assert math.isclose(stats['std_dev'], math.sqrt(1.25), rel_tol=1e-9)


def test_end_to_end_small_csv(tmp_path):
    # Small CSV content spanning two groups
    csv_text = (
        "time,site,device,metric,unit,value\n"
        "2025-01-01 00:00:00 +0000 UTC,site_1,dev_1,temp,Cel,10.0\n"
        "2025-01-01 00:05:00 +0000 UTC,site_1,dev_1,temp,Cel,20.0\n"
        "2025-01-01 00:10:00 +0000 UTC,site_1,dev_1,temp,Cel,30.0\n"
        "2025-01-01 00:00:00 +0000 UTC,site_2,dev_2,humidity,%RH,50.0\n"
        "2025-01-01 00:05:00 +0000 UTC,site_2,dev_2,humidity,%RH,55.0\n"
    )

    csv_path = tmp_path / "mini.csv"
    csv_path.write_text(csv_text, encoding="utf-8")

    # Build aggregations like main() does
    aggregations = defaultdict(list)

    args = SimpleNamespace(site=None, device=None, metric=None, start_date=None, end_date=None)

    import csv
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if analyzer.should_include(row, args):
                key = (row['device'], row['site'], row['metric'])
                value = analyzer.convert_to_float(row['value'])
                if value is not None:
                    aggregations[key].append(value)

    # Compute stats
    stats = {}
    for key, values in aggregations.items():
        device, site, metric = key
        stats[key] = {
            'device': device,
            'site': site,
            'metric': metric,
            **analyzer.compute_statistics(values)
        }

    # Validate the temp group
    temp_key = ('dev_1', 'site_1', 'temp')
    assert temp_key in stats
    s = stats[temp_key]
    assert s['count'] == 3
    assert s['min'] == 10.0
    assert s['max'] == 30.0
    assert s['average'] == 20.0
    # values: [10,20,30] -> variance = ((-10)^2 + 0^2 + 10^2)/3 = 200/3
    assert math.isclose(s['std_dev'], math.sqrt(200.0/3.0), rel_tol=1e-9)

    # Validate the humidity group
    hum_key = ('dev_2', 'site_2', 'humidity')
    assert hum_key in stats
    s2 = stats[hum_key]
    assert s2['count'] == 2
    assert s2['min'] == 50.0
    assert s2['max'] == 55.0
    assert s2['average'] == 52.5
    # values: [50,55] -> variance = ((-2.5)^2 + 2.5^2)/2 = 6.25
    assert math.isclose(s2['std_dev'], math.sqrt(6.25), rel_tol=1e-9)
