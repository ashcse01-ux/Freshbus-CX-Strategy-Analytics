import os
import glob
import pandas as pd
import hashlib
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from database import get_tenant_db_engine
import models

def parse_date_to_str(val):
    if pd.isna(val):
        return ""
    if isinstance(val, datetime):
        return val.strftime("%d-%m-%Y")
    val_str = str(val).strip()
    # Try parsing
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(val_str, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return val_str

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

def clean_ratings(val):
    if pd.isna(val):
        return ""
    try:
        f_val = float(val)
        if f_val.is_integer():
            return str(int(f_val))
        return str(f_val)
    except:
        return str(val).strip()

def get_row_hash(call_id, date_val, caller_id, start_time, agent_id):
    if call_id and str(call_id).strip() not in ["", "nan"]:
        return hashlib.md5(str(call_id).strip().encode()).hexdigest()
    
    unique_str = f"{str(date_val).strip()}-{str(caller_id).strip()}-{str(start_time).strip()}-{str(agent_id).strip()}"
    return hashlib.md5(unique_str.encode()).hexdigest()

def ingest():
    dump_dir = "../Inbound Dashboard Dump"
    xls_files = glob.glob(os.path.join(dump_dir, "*.xls"))
    xls_files.sort()
    
    engine = get_tenant_db_engine("Inbound")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    all_records = []
    unique_dates = set()
    seen_hashes = set()
    
    print(f"Found {len(xls_files)} files in dump directory.")
    
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
    
    for fpath in xls_files:
        print(f"Reading file: {fpath}")
        df = pd.read_excel(fpath)
        print(f"Loaded {len(df)} rows.")
        
        df = df.rename(columns=mapping)
        
        for idx, row in df.iterrows():
            date_str = parse_date_to_str(row.get("Call_Date"))
            if not date_str:
                continue
            
            unique_dates.add(date_str)
            
            call_id = clean_string(row.get("Call_ID"))
            caller_no = clean_string(row.get("Caller_No"))
            start_time = parse_time_str(row.get("Start_Time"))
            agent_id = clean_string(row.get("Agent_ID"))
            
            h = get_row_hash(call_id, date_str, caller_no, start_time, agent_id)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            
            rec = models.CallRecord(
                row_hash=h,
                Call_ID=call_id,
                Call_Type=clean_string(row.get("Call_Type")),
                Campaign=clean_string(row.get("Campaign")),
                Location=clean_string(row.get("Location")),
                Caller_No=caller_no,
                Caller_E164=clean_string(row.get("Caller_E164")),
                Skill=clean_string(row.get("Skill")),
                Call_Date=date_str,
                Queue_Time=parse_time_str(row.get("Queue_Time")),
                Start_Time=start_time,
                Time_to_Answer=parse_time_str(row.get("Time_to_Answer")),
                End_Time=parse_time_str(row.get("End_Time")),
                Talk_Time=parse_time_str(row.get("Talk_Time")),
                Hold_Time=parse_time_str(row.get("Hold_Time")),
                Duration=parse_time_str(row.get("Duration")),
                Call_Flow=clean_string(row.get("Call_Flow")),
                Dialed_Number=clean_string(row.get("Dialed_Number")),
                Agent=clean_string(row.get("Agent")).split("->")[-1].strip(),
                Disposition=clean_string(row.get("Disposition")),
                Wrapup_Duration=parse_time_str(row.get("Wrapup_Duration")),
                Handling_Time=parse_time_str(row.get("Handling_Time")),
                Status=clean_string(row.get("Status")),
                Dial_Status=clean_string(row.get("Dial_Status")),
                Customer_Dial_Status=clean_string(row.get("Customer_Dial_Status")),
                Agent_Dial_Status=clean_string(row.get("Agent_Dial_Status")),
                Hangup_By=clean_string(row.get("Hangup_By")),
                Transfer_Details=clean_string(row.get("Transfer_Details")),
                UUI=clean_string(row.get("UUI")),
                Comments=clean_string(row.get("Comments")),
                Feedback=clean_string(row.get("Feedback")),
                Customer_Ring_Time=parse_time_str(row.get("Customer_Ring_Time")),
                Recording_URL=clean_string(row.get("Recording_URL")),
                Agent_ID=agent_id,
                Ratings=clean_ratings(row.get("Ratings")),
                Rating_Comments=clean_string(row.get("Rating_Comments")),
                DynamicDid=clean_string(row.get("DynamicDid")),
                DID=clean_string(row.get("DID"))
            )
            all_records.append(rec)

    if not all_records:
        print("No records found to insert.")
        return
        
    print(f"Total unique parsed records: {len(all_records)}")
    print(f"Unique dates to delete/reload: {len(unique_dates)}")
    
    unique_dates_list = list(unique_dates)
    batch_size = 50
    for i in range(0, len(unique_dates_list), batch_size):
        batch = unique_dates_list[i:i+batch_size]
        session.query(models.CallRecord).filter(models.CallRecord.Call_Date.in_(batch)).delete(synchronize_session=False)
    session.commit()
    print("Deleted old records for dates in dump.")
    
    insert_batch_size = 2000
    for i in range(0, len(all_records), insert_batch_size):
        batch = all_records[i:i+insert_batch_size]
        session.bulk_save_objects(batch)
        session.commit()
        print(f"Inserted records {i} to {i + len(batch)}")
        
    session.close()
    print("Ingestion completed successfully!")

if __name__ == "__main__":
    ingest()
