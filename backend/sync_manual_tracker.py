import os
import json
import pandas as pd
from datetime import datetime, timedelta

def sync_tracker():
    excel_path = "../Inbound Dashboard_Manual Metrics Tracker.xlsx"
    print(f"Reading manual metrics from Excel: {excel_path} ...")
    
    # Read sheet Inbound Metrics without headers
    df = pd.read_excel(excel_path, sheet_name="Inbound Metrics", header=None)
    print(f"Loaded sheet with shape: {df.shape}")
    
    day_mapping = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    # Row 0 contains day names
    # Row 1 contains dates
    # Column 0 contains metric names
    # Let's locate the metric names
    metric_names = df.iloc[:, 0].astype(str).str.strip().tolist()
    
    # We will build a dictionary keyed by date string "YYYY-MM-DD"
    # We start our date sequence at January 1st, 2026 for column index 590
    current_date = datetime(2026, 1, 1)
    
    # We also have older historical data before column 590 (from 2025). 
    # Do we need to parse them too?
    # Let's see: column 590 starts 2026-01-01. 
    # The columns from 1 to 588 are from 2023-11-01 to 2025-04-30.
    # Wait, let's see. If the user only wants the dump from Jan 1st 2026 to July 12th 2026, 
    # we can process all columns in the sheet!
    # Wait! Let's check how the dates before 590 are structured.
    # In columns 1 to 588, row 1 contains the actual parsed dates from 2023-11-01 to 2025-04-30.
    # Are those parsed correctly? Yes, because they were from 2023/2024/2025.
    # But wait! Let's check if we can reconstruct them using the same method, or just use their row 1 values.
    # Actually, let's load all columns in the sheet!
    # For columns before 590, if row 1 is a valid datetime, we can use it.
    # For columns starting from 590, we can use our sequential day incrementer starting at 2026-01-01!
    # This is extremely clean and handles both historical and new 2026 data perfectly!
    
    # Let's read the existing manual_daily_metrics.json first to merge/overwrite it.
    json_path = "manual_daily_metrics.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try:
                manual_data = json.load(f)
            except Exception:
                manual_data = {}
    else:
        manual_data = {}
        
    print(f"Loaded {len(manual_data)} existing dates from JSON.")
    
    updated_count = 0
    
    # Loop over all columns starting from index 1
    for col in range(1, df.shape[1]):
        day_val = df.iloc[0, col]
        date_val = df.iloc[1, col]
        
        if not isinstance(day_val, str):
            continue
        day_clean = day_val.strip().lower()
        if day_clean not in day_mapping:
            continue
            
        # Determine the date for this column
        col_date = None
        if col < 590:
            # Historical column: use row 1 date if valid
            if isinstance(date_val, datetime):
                col_date = date_val
            elif pd.notna(date_val):
                # Try parsing string
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        col_date = datetime.strptime(str(date_val).strip(), fmt)
                        break
                    except ValueError:
                        continue
        else:
            # 2026 dump column: use our sequential tracker
            col_date = current_date
            # Increment tracker for the next valid day column
            current_date += timedelta(days=1)
            
        if col_date is None:
            continue
            
        date_str = col_date.strftime("%Y-%m-%d")
        
        # Build metrics dict for this date
        day_metrics = {}
        for row_idx, metric_name in enumerate(metric_names):
            if pd.isna(metric_name) or metric_name == "nan" or row_idx < 2:
                continue
                
            val = df.iloc[row_idx, col]
            if pd.isna(val) or val == "":
                val_float = 0.0
            else:
                try:
                    val_float = float(val)
                except ValueError:
                    val_float = 0.0
            day_metrics[metric_name] = val_float
            
        # Update our dictionary
        manual_data[date_str] = day_metrics
        updated_count += 1

    # Save back to manual_daily_metrics.json
    with open(json_path, "w") as f:
        json.dump(manual_data, f, indent=4)
        
    print(f"Sync complete. Updated/wrote {updated_count} dates to {json_path}.")

if __name__ == "__main__":
    sync_tracker()
