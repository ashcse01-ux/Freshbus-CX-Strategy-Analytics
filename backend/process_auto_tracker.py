import pandas as pd
import json
import math
import datetime

# Parse metrics from the AUTOMATIC Metrics Tracker (not manual)
# These metrics are manually entered by agents in the auto tracker but
# cannot be computed from raw Ozonetel data.
AUTO_FILE = '../Inbound Dashboard_Automatic Metrics Tracker.xlsx'

print("Reading Call Drop / Blank Call Not Done from Automatic Metrics Tracker...")
df = pd.read_excel(AUTO_FILE, sheet_name='Inbound Metrics', header=None)

# Find row indices by label (col 0)
ROW_LABELS = {
    'Call Drop': 39,
    'Blank Call': 40,
    'Call Drop Not Done': 42,
    'Blank Call Not Done': 43,
    'Overall Call Not Done': 44,
    'Agent Disconnected': 51,
    'Call Not Disposed': 60,
}

# Date row is row index 1
output_data = {}
for col_idx in range(1, df.shape[1]):
    date_val = df.iloc[1, col_idx]
    if pd.isna(date_val):
        continue

    parsed_date = None
    if isinstance(date_val, (pd.Timestamp, datetime.datetime)):
        parsed_date = date_val
    elif isinstance(date_val, str):
        try:
            parsed_date = pd.to_datetime(date_val, errors='coerce')
        except:
            pass

    if parsed_date is not None and pd.notna(parsed_date):
        date_str = pd.Timestamp(parsed_date).strftime('%Y-%m-%d')
        # Only process 2026-01-01 to 2026-07-14
        if '2026-01-01' <= date_str <= '2026-07-14':
            day_data = {}
            for label, row_idx in ROW_LABELS.items():
                val = df.iloc[row_idx, col_idx]
                if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
                    val = 0
                day_data[label] = int(val) if isinstance(val, (int, float)) else 0
            output_data[date_str] = day_data

with open('auto_tracker_daily.json', 'w') as f:
    json.dump(output_data, f, indent=4)

print(f"Processed {len(output_data)} dates (2026-01-01 to 2026-07-14).")

# Spot-check
for d in ['2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09', '2026-01-10']:
    if d in output_data:
        print(f"  {d}: {output_data[d]}")
