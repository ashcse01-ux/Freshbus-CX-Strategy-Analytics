import pandas as pd
import json
import math
import datetime
import urllib.request
import io

sheet_url = 'https://docs.google.com/spreadsheets/d/1ewwDxoCutZq_CKo9cJA8B9wHMTlOQPbd/export?format=xlsx&gid=741407078'
file_path = '../Inbound Dashboard_Manual Metrics Tracker.xlsx'

print("Reading from local file...")
df = pd.read_excel(file_path, sheet_name='Inbound Metrics', header=None)

metrics = [
    'Gross Seats', 'Gross Tickets', 'Intr/Journey', 'Defects', 'Defects/Journey',
    'Present Agent HC', 'Intr/Journey %', 'Travel update %', 'No. of Service Delay',
    'Delay Pax Impacted', 'No. of Service Cancel', 'Service Cancel Pax Impacted',
    'No. of Service Breakdown', 'Break Down Pax Impacted', 'Impacted %',
    'Total Pax Impacted', 'Cancellations Impact %'
]

# Find the row indices for each metric
metric_indices = {}
for idx, val in enumerate(df.iloc[:, 0]):
    if isinstance(val, str):
        v = val.strip()
        if v in metrics:
            metric_indices[v] = idx

output_data = {}

# Process each column starting from index 1
for col_idx in range(1, len(df.columns)):
    date_val = df.iloc[1, col_idx]
    if pd.isna(date_val):
        continue
    
    parsed_date = None
    if isinstance(date_val, (pd.Timestamp, datetime.datetime)):
        # Excel parsed it as D/M/YYYY but user meant M/D/YYYY
        # So a date meant as June 2 (6/2/2026) was parsed as Feb 6 (2026-02-06)
        # We need to swap month and day.
        try:
            parsed_date = datetime.datetime(date_val.year, date_val.day, date_val.month)
        except ValueError:
            parsed_date = date_val
    elif isinstance(date_val, str):
        # String dates like '6/13/2026' (M/D/YYYY)
        try:
            parts = date_val.split('/')
            if len(parts) == 3:
                parsed_date = datetime.datetime(int(parts[2]), int(parts[0]), int(parts[1]))
            else:
                parsed_date = pd.to_datetime(date_val, errors='coerce')
        except:
            parsed_date = pd.to_datetime(date_val, errors='coerce')

    if pd.notna(parsed_date) and parsed_date is not None:
        date_str = parsed_date.strftime('%Y-%m-%d')
        # Filter for 2026-01-01 to 2026-07-13
        if '2026-01-01' <= date_str <= '2026-07-13':
            day_data = {}
            for m in metrics:
                if m in metric_indices:
                    val = df.iloc[metric_indices[m], col_idx]
                    if pd.isna(val):
                        val = 0
                    elif isinstance(val, float) and math.isnan(val):
                        val = 0
                    day_data[m] = float(val)
            output_data[date_str] = day_data

with open('manual_daily_metrics.json', 'w') as f:
    json.dump(output_data, f, indent=4)

print(f"Processed {len(output_data)} dates.")
