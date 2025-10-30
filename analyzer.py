import csv
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import math

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='IoT Sensor Data Analyzer'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to the CSV file containing sensor data'
    )
    parser.add_argument(
        '--site',
        type=str,
        default=None,
        help='Filter by specific size (e.g. site_1, site_2)'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Filter by specific device (e.g. device_b_003)'
    )
    parser.add_argument(
        '--metric',
        type=str,
        default=None,
        help='Filter by specific metric (e.g. temperature, humidity, pressure)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        help='Filter by start date/time (format: "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD")'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='Filter by end date/time (format: "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD")'
    )

    args = parser.parse_args()

    # Parse date strings to datetime objects if provided
    if args.start_date:
        try:
            args.start_date = parse_datetime(args.start_date)
        except ValueError as e:
            parser.error(f"Invalid start-date format: {e}")
    
    if args.end_date:
        try:
            args.end_date = parse_datetime(args.end_date)
        except ValueError as e:
            parser.error(f"Invalid end-date format: {e}")
    
    return args

def parse_datetime(date_str):
    formats = [
        "%Y-%m-%d %H:%M:%S %z %Z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Ensure timezone-aware (UTC) for consistent comparisons
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date string: {date_str}")

def should_include(row, args):
    # Filter by site
    if args.site and row['site'] != args.site:
        return False
    
    # Filter by device
    if args.device and row['device'] != args.device:
        return False
    
    # Filter by metric
    if args.metric and row['metric'] != args.metric:
        return False
    
    # Filter by date range
    if args.start_date or args.end_date:
        try:
            row_time = parse_datetime(row['time'].strip())
            
            if args.start_date and row_time < args.start_date:
                return False
            
            if args.end_date and row_time > args.end_date:
                return False
        except (ValueError, KeyError):
            # If we can't parse the time, skip this row or include it
            # For robustness, we'll skip rows with unparseable dates
            return False
    
    return True

def convert_to_float(value_str):
    if value_str is None or value_str.strip() == '':
        return None
    
    try:
        return float(value_str.strip())
    except (ValueError, TypeError):
        # Log warning would go here in production
        return None

def compute_statistics(values):
    # Filter out None values
    valid_values = [v for v in values if v is not None]
    
    if len(valid_values) == 0:
        return {
            'average': 0,
            'min': 0.0,
            'max': 0.0,
            'count': 0,
            'std_dev': 0.0
        }
    
    # Basic statistics
    count = len(valid_values)
    average = sum(valid_values) / count
    min_value = min(valid_values)
    max_value = max(valid_values)
    
    # Standard deviation
    if count == 1:
        std_dev = 0.0
    else:
        variance = sum((x - average) ** 2 for x in valid_values) / count
        std_dev = math.sqrt(variance)
    
    return {
        'average': average,
        'min': min_value,
        'max': max_value,
        'count': count,
        'std_dev': std_dev
    }

def print_aggregation_results(stats):
    # Print formatted aggregation results for all device+site+metric combinations
    print(f"{'Device':<20} {'Site':<10} {'Metric':<15} {'Avg':>10} {'Min':>10} {'Max':>10} {'Count':>8} {'StdDev':>10}")
    print("-" * 100)
    
    for key, stat in sorted(stats.items()):
        print(f"{stat['device']:<20} {stat['site']:<10} {stat['metric']:<15} "
              f"{stat['average']:>10.2f} {stat['min']:>10.2f} {stat['max']:>10.2f} "
              f"{stat['count']:>8} {stat['std_dev']:>10.2f}")


def print_top_10_by_average(top_10):
    # Print top 10 device+site+metric combinations by average value
    print(f"{'Rank':<6} {'Device':<20} {'Site':<10} {'Metric':<15} {'Average':>10}")
    print("-" * 65)
    
    for rank, (key, stat) in enumerate(top_10, 1):
        print(f"{rank:<6} {stat['device']:<20} {stat['site']:<10} {stat['metric']:<15} {stat['average']:>10.2f}")


def print_top_10_by_stddev(top_10):
    # Print top 10 device+site+metric combinations by standard deviation
    print(f"{'Rank':<6} {'Device':<20} {'Site':<10} {'Metric':<15} {'StdDev':>10}")
    print("-" * 65)
    
    for rank, (key, stat) in enumerate(top_10, 1):
        print(f"{rank:<6} {stat['device']:<20} {stat['site']:<10} {stat['metric']:<15} {stat['std_dev']:>10.2f}")

def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Initialize aggregation data structure 
    # where Key is (device, site, metric) 
    # and Value is list of numeric values
    aggregations = defaultdict(list)

    # Process CSV file line-by-line
    try:
        with open(args.input_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Apply filters
                if should_include(row, args):
                    key = (row['device'], row['site'], row['metric'])
                    value = convert_to_float(row['value'])

                    if value is not None:
                        aggregations[key].append(value)
    
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Calcualte stats for each aggregated group
    stats = {}
    for key, values in aggregations.items():
        device, site, metric = key
        stats[key] = {
            'device': device,
            'site': site,
            'metric': metric,
            **compute_statistics(values)
        }

    # Get top 10 by average value
    top_by_avg = sorted(
        stats.items(),
        key=lambda x: x[1]['average'],
        reverse=True
    )[:10]

    # Get top 10 by standard deviation
    top_by_stddev = sorted(
        stats.items(),
        key=lambda x: x[1]['std_dev'],
        reverse=True
    )[:10]

    # Output results
    print('\n')
    print("AGGREGATION RESULTS")
    print("-"*65)
    print(f"\nTotal device+site+metric combinations: {len(stats)}\n")
    
    # Print all aggregations
    print_aggregation_results(stats)
    
    # Print top 10 by average
    print('\n')
    print("TOP 10 BY AVERAGE VALUE")
    print("-"*65)
    print_top_10_by_average(top_by_avg)
    
    # Print top 10 by std dev
    print('\n')
    print("TOP 10 BY STANDARD DEVIATION (HIGHEST VARIABILITY)")
    print("-"*65)
    print_top_10_by_stddev(top_by_stddev)

if __name__ == '__main__':
    main()
