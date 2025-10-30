IoT Sensor Data Analyzer
========================

A memory-efficient Python script that parses large CSVs of IoT sensor readings and aggregates by device + site + metric. It reports average, min/max, count, and standard deviation and outputs the top 10 groups by highest average and highest variability (std dev). Supports optional filters for date/time range, site, metric, and device.

Project Layout
--------------

- `analyzer.py` — main CLI program
- `sample_data.csv` — example dataset
- `test_analyzer.py` — unit tests for analyzer.py

Requirements and Installation
-----------------------------

Python 3.9+ is recommended. The analyzer itself uses only the standard library. Tests use `pytest`.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Running the Analyzer
--------------------

Basic help:

```
python analyzer.py --help
```

Analyze a CSV:

```
python analyzer.py sample_data.csv
```

Filters (examples)
------------------

- Filter by site:

```
python analyzer.py sample_data.csv --site site_1
```

- Filter by device:

```
python analyzer.py sample_data.csv --device device_b_003
```

- Filter by metric:

```
python analyzer.py sample_data.csv --metric temperature
```

- Date range:

```
python analyzer.py sample_data.csv --start-date "2025-01-02" --end-date "2025-01-05"
```

- Date/time range (to the second):

```
python analyzer.py sample_data.csv --start-date "2025-01-03 12:00:00" --end-date "2025-01-03 18:00:00"
```

- Combine filters:

```
python analyzer.py sample_data.csv --site site_2 --metric pressure --start-date "2025-01-04"
```

Output
------

The program prints a table of all device+site+metric aggregations and then two top-10 lists:
- Top 10 by highest average value
- Top 10 by highest standard deviation (variability)

Data Quality Considerations and Assumptions
-------------------------------------------

- The CSV header is expected to be: `time,site,device,metric,unit,value`.
- `value` is parsed as a float. Rows with empty or non-numeric values are skipped for aggregation.
- Timestamps are parsed from formats like `YYYY-MM-DD HH:MM:SS +0000 UTC`, `YYYY-MM-DD HH:MM:SS`, and `YYYY-MM-DD`.
- Rows with unparseable timestamps are excluded when date filters are applied.
- Metrics may have inconsistent names (e.g., `temp` vs `temperature`). The analyzer treats them as distinct.
- Units are not normalized; aggregations group only by `(device, site, metric)`.

Handling Large Files (Memory Efficiency)
---------------------------------------

- The CSV is processed line-by-line via a streaming reader (`csv.DictReader`), avoiding loading the entire file into memory.
- Only aggregated values per `(device, site, metric)` are stored.
- Statistics are computed after ingestion to minimize repeated work.
- For very large cardinalities (many unique `(device, site, metric)` keys), memory usage scales with the number of groups. If needed, replace the list of values with online (one-pass) statistics (e.g., Welford’s algorithm) to avoid keeping all values per group in memory.

Running Tests
-------------

```
pytest -q
```
