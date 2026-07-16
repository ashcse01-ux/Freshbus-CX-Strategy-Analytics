import os
import json
import pandas as pd
from datetime import datetime, timedelta
import hashlib
from sqlalchemy.orm import Session
import io
import requests

from database import get_tenant_db_engine
import models

MANUAL_CSV_URL = "https://docs.google.com/spreadsheets/d/1ewwDxoCutZq_CKo9cJA8B9wHMTlOQPbd/export?format=csv&gid=741407078"
AUTO_CSV_URL = "https://docs.google.com/spreadsheets/d/1fvMnnJ2a3EeMuYZojCyJxLEGbOdaM7XVbY_QwtpxKS0/export?format=csv&gid=0"

def parse_time_str(val):
    if pd.isna(val):
        return ""
    if isinstance(val, datetime):
        return val.strftime("%H:%M:%S")
    if isinstance(val, pd.Timedelta):
        total_seconds = int(val.total_seconds())
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    return str(val).strip()

def clean_string(val):
    if pd.isna(val):
        return ""
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
    return str(val).strip()

def get_row_hash(call_id, date_val, caller_id, start_time, agent_id):
    if call_id and str(call_id).strip() not in ["", "nan"]:
        return hashlib.md5(str(call_id).strip().encode()).hexdigest()
    
    unique_str = f"{str(date_val).strip()}-{str(caller_id).strip()}-{str(start_time).strip()}-{str(agent_id).strip()}"
    return hashlib.md5(unique_str.encode()).hexdigest()

def sync_manual_metrics():
    print(f"Reading manual metrics from Google Sheets...")
    try:
        df = pd.read_csv(MANUAL_CSV_URL, header=None)
    except Exception as e:
        print(f"Failed to read manual metrics CSV: {e}")
        return 0
        
    day_mapping = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    metric_names = df.iloc[:, 0].astype(str).str.strip().tolist()
    current_date = datetime(2026, 1, 1)
    
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "manual_daily_metrics.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try:
                manual_data = json.load(f)
            except Exception:
                manual_data = {}
    else:
        manual_data = {}
        
    updated_count = 0
    
    for col in range(1, df.shape[1]):
        day_val = df.iloc[0, col]
        date_val = df.iloc[1, col]
        
        if not isinstance(day_val, str):
            continue
        day_clean = day_val.strip().lower()
        if day_clean not in day_mapping:
            continue
            
        col_date = None
        if col < 590:
            if isinstance(date_val, datetime):
                col_date = date_val
            elif pd.notna(date_val):
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        col_date = datetime.strptime(str(date_val).strip(), fmt)
                        break
                    except ValueError:
                        continue
        else:
            col_date = current_date
            current_date += timedelta(days=1)
            
        if col_date is None:
            continue
            
        date_str = col_date.strftime("%Y-%m-%d")
        
        day_metrics = {}
        for row_idx, metric_name in enumerate(metric_names):
            if pd.isna(metric_name) or metric_name == "nan" or row_idx < 2:
                continue
                
            val = df.iloc[row_idx, col]
            if pd.isna(val) or val == "" or str(val).strip() == "-":
                val = 0.0
            
            try:
                if isinstance(val, str):
                    val = float(val.replace(",", "").replace("%", "").strip())
                val = float(val)
            except Exception:
                val = 0.0
                
            day_metrics[metric_name] = val
            
        if date_str not in manual_data or manual_data[date_str] != day_metrics:
            manual_data[date_str] = day_metrics
            updated_count += 1
            
    with open(json_path, "w") as f:
        json.dump(manual_data, f, indent=4)
        
    print(f"Updated {updated_count} manual metrics dates.")
    return updated_count

def sync_auto_metrics(db_tenant: Session, missing_dates: list):
    print("Reading automatic metrics dump from Google Sheets...")
    try:
        df = pd.read_csv(AUTO_CSV_URL)
    except pd.errors.EmptyDataError:
        print("Automatic metrics sheet is empty.")
        return 0
    except Exception as e:
        print(f"Failed to read automatic metrics CSV: {e}")
        return 0
        
    if df.empty:
        print("Automatic metrics sheet has no rows.")
        return 0
        
    mapping = {
        "Call ID": "Call_ID",
        "Call Type": "Call_Type",
        "Campaign": "Campaign",
        "Location": "Location",
        "Caller No": "Caller_No",
        "Caller_E164": "Caller_E164",
        "Skill": "Skill",
        "Call Date": "Call_Date",
        "Queue Time": "Queue_Time",
        "Start Time": "Start_Time",
        "Time to Answer": "Time_to_Answer",
        "End Time": "End_Time",
        "Talk Time": "Talk_Time",
        "Hold Time": "Hold_Time",
        "Duration": "Duration",
        "Call Flow": "Call_Flow",
        "Dialed Number": "Dialed_Number",
        "Agent": "Agent",
        "Disposition": "Disposition",
        "Wrapup Duration": "Wrapup_Duration",
        "Handling Time": "Handling_Time",
        "Status": "Status",
        "Dial Status": "Dial_Status",
        "Customer Dial Status": "Customer_Dial_Status",
        "Agent Dial Status": "Agent_Dial_Status",
        "Hangup By": "Hangup_By",
        "Transfer Details": "Transfer_Details",
        "UUI": "UUI",
        "Comments": "Comments",
        "Feedback": "Feedback",
        "Customer Ring Time": "Customer_Ring_Time",
        "Recording URL": "Recording_URL",
        "Agent ID": "Agent_ID",
        "Ratings": "Ratings",
        "Rating Comments": "Rating_Comments",
        "DynamicDid": "DynamicDid",
        "DID": "DID"
    }
    
    df = df.rename(columns=mapping)
    
    # Filter rows based on missing dates to make it ultra fast
    if 'Call_Date' in df.columns:
        # Expected format from dump is DD-MM-YYYY or YYYY-MM-DD
        # Missing dates are YYYY-MM-DD
        def is_missing(d_str):
            if pd.isna(d_str): return False
            d_str = str(d_str).strip()
            # parse
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    parsed = datetime.strptime(d_str.split()[0], fmt.split()[0]).strftime("%Y-%m-%d")
                    return parsed in missing_dates
                except ValueError:
                    pass
            return False
            
        df = df[df['Call_Date'].apply(is_missing)]
        
    if df.empty:
        print("No missing dates found in the data dump.")
        return 0
        
    records_to_insert = []
    
    for _, row in df.iterrows():
        call_id = clean_string(row.get('Call_ID', ''))
        call_date = str(row.get('Call_Date', '')).strip()
        
        # parse to DD-MM-YYYY for the hash if needed, or keep original
        parsed_date = call_date
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                parsed_date = datetime.strptime(call_date.split()[0], fmt.split()[0]).strftime("%d-%m-%Y")
                break
            except Exception:
                pass
                
        row_hash = get_row_hash(
            call_id,
            parsed_date,
            clean_string(row.get('Caller_No', '')),
            parse_time_str(row.get('Start_Time', '')),
            clean_string(row.get('Agent_ID', ''))
        )
        
        record = models.CallRecord(
            row_hash=row_hash,
            Call_ID=call_id,
            Call_Type=clean_string(row.get('Call_Type', '')),
            Campaign=clean_string(row.get('Campaign', '')),
            Location=clean_string(row.get('Location', '')),
            Caller_No=clean_string(row.get('Caller_No', '')),
            Caller_E164=clean_string(row.get('Caller_E164', '')),
            Skill=clean_string(row.get('Skill', '')),
            Call_Date=parsed_date,
            Queue_Time=parse_time_str(row.get('Queue_Time', '')),
            Start_Time=parse_time_str(row.get('Start_Time', '')),
            Time_to_Answer=parse_time_str(row.get('Time_to_Answer', '')),
            End_Time=parse_time_str(row.get('End_Time', '')),
            Talk_Time=parse_time_str(row.get('Talk_Time', '')),
            Hold_Time=parse_time_str(row.get('Hold_Time', '')),
            Duration=parse_time_str(row.get('Duration', '')),
            Call_Flow=clean_string(row.get('Call_Flow', '')),
            Dialed_Number=clean_string(row.get('Dialed_Number', '')),
            Agent=clean_string(row.get('Agent', '')),
            Disposition=clean_string(row.get('Disposition', '')),
            Wrapup_Duration=parse_time_str(row.get('Wrapup_Duration', '')),
            Handling_Time=parse_time_str(row.get('Handling_Time', '')),
            Status=clean_string(row.get('Status', '')),
            Dial_Status=clean_string(row.get('Dial_Status', '')),
            Customer_Dial_Status=clean_string(row.get('Customer_Dial_Status', '')),
            Agent_Dial_Status=clean_string(row.get('Agent_Dial_Status', '')),
            Hangup_By=clean_string(row.get('Hangup_By', '')),
            Transfer_Details=clean_string(row.get('Transfer_Details', '')),
            UUI=clean_string(row.get('UUI', '')),
            Comments=clean_string(row.get('Comments', '')),
            Feedback=clean_string(row.get('Feedback', '')),
            Customer_Ring_Time=parse_time_str(row.get('Customer_Ring_Time', '')),
            Recording_URL=clean_string(row.get('Recording_URL', '')),
            Agent_ID=clean_string(row.get('Agent_ID', '')),
            Ratings=clean_string(row.get('Ratings', '')),
            Rating_Comments=clean_string(row.get('Rating_Comments', '')),
            DynamicDid=clean_string(row.get('DynamicDid', '')),
            DID=clean_string(row.get('DID', ''))
        )
        records_to_insert.append(record)
        
    if records_to_insert:
        # Ignore duplicate row_hash during bulk insert manually to avoid integrity errors
        # SQLAlchemy bulk save will crash if duplicates exist. Better to just merge or ignore
        for rec in records_to_insert:
            try:
                db_tenant.merge(rec)
            except Exception:
                pass
        db_tenant.commit()
        
    return len(records_to_insert)
