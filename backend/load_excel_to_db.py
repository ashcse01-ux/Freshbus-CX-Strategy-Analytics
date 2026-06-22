import pandas as pd
from datetime import datetime, time
import uuid

from database import get_tenant_db_engine
from sqlalchemy.orm import sessionmaker
import models

def parse_time_to_sec(t):
    if pd.isna(t):
        return 0
    if isinstance(t, str):
        parts = t.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    elif isinstance(t, time):
        return t.hour * 3600 + t.minute * 60 + t.second
    elif isinstance(t, (int, float)):
        return int(t)
    return 0

def parse_time_to_string(total_seconds):
    total_seconds = int(max(0, total_seconds))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def load_excel_to_db(excel_path):
    print(f"Reading Excel file: {excel_path} ...")
    # Read header=None to manually locate the dates row
    df = pd.read_excel(excel_path, header=None)
    
    date_row_idx = None
    for i in range(5):
        row_vals = df.iloc[i].values
        has_date = any(isinstance(v, datetime) for v in row_vals)
        if has_date:
            date_row_idx = i
            break
            
    if date_row_idx is None:
        print("Could not automatically locate the date row. Using row 1 as fallback.")
        date_row_idx = 1
        
    dates = df.iloc[date_row_idx].values
    metric_names = df.iloc[:, 0].astype(str).str.strip().tolist()
    
    def get_row_val(metric_name, col_idx):
        try:
            r_idx = next(i for i, v in enumerate(metric_names) if str(v).lower() == metric_name.lower())
            return df.iloc[r_idx, col_idx]
        except StopIteration:
            return 0
            
    engine = get_tenant_db_engine("Inbound")
    TenantSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TenantSessionLocal()
    
    for col_idx, d in enumerate(dates):
        if not isinstance(d, datetime):
            continue # skip columns that are not dates
            
        if d > datetime(2026, 6, 7):
            print(f"Skipping {d.date()} - API data takes over from June 8th onwards.")
            continue
            
        formatted_date = d.strftime("%d-%m-%Y")
        
        # Extract individual metrics corresponding to current DB schema needs
        ans = int(pd.to_numeric(get_row_val('calls answered', col_idx), errors='coerce') or 0)
        abn = int(pd.to_numeric(get_row_val('overall abn', col_idx), errors='coerce') or 0)
        wh_ans = int(pd.to_numeric(get_row_val('wh calls answered', col_idx), errors='coerce') or 0)
        wh_offered = int(pd.to_numeric(get_row_val('wh total calls offered', col_idx), errors='coerce') or 0)
        tu_offered = int(pd.to_numeric(get_row_val('calls offered (travel update)', col_idx), errors='coerce') or 0)
        
        net_abn = int(pd.to_numeric(get_row_val('net abandoned calls', col_idx), errors='coerce') or 0)
        short_abn = int(pd.to_numeric(get_row_val('short call abn', col_idx), errors='coerce') or 0)
        queue_fail = int(pd.to_numeric(get_row_val('queue level abn', col_idx), errors='coerce') or 0)
        
        sl_calls = int(pd.to_numeric(get_row_val('sl calls', col_idx), errors='coerce') or 0)
        long_calls = int(pd.to_numeric(get_row_val('handling time  >5mins', col_idx), errors='coerce') or 0)
        on_hold = int(pd.to_numeric(get_row_val('on hold calls', col_idx), errors='coerce') or 0)
        
        avg_wait = parse_time_to_sec(get_row_val('avg wait time', col_idx))
        avg_hold = parse_time_to_sec(get_row_val('avg hold time', col_idx))
        aht = parse_time_to_sec(get_row_val('answered - aht', col_idx))
        
        same_day_repeat = int(pd.to_numeric(get_row_val('repeat calls', col_idx), errors='coerce') or 0)
        same_day_disp_repeat = int(pd.to_numeric(get_row_val('disposition ( repeat calls )', col_idx), errors='coerce') or 0)
        
        if ans == 0 and abn == 0:
            continue
            
        print(f"Loading generated CallRecords into DB for {formatted_date} ...")
        # Remove old data for this specific date to prevent duplicates
        db.query(models.CallRecord).filter(models.CallRecord.Call_Date == formatted_date).delete()
        
        remaining_abn = abn - (net_abn + short_abn + queue_fail)
        if remaining_abn < 0:
            queue_fail = max(0, queue_fail + remaining_abn)
            
        # Generating proportional Time-To-Answer to match average
        total_wait_sec = avg_wait * ans
        ttas = [15] * sl_calls + [45] * max(0, ans - sl_calls)
        diff = total_wait_sec - sum(ttas)
        for i in range(ans):
            if diff > 0:
                ttas[i] += 1; diff -= 1
            elif diff < 0 and ttas[i] > 0:
                ttas[i] -= 1; diff += 1

        # Generating Hold Time proportionally
        holds = [avg_hold] * on_hold + [0] * max(0, ans - on_hold)
        
        # Generating Average Handling Time proportionally
        total_handling_sec = aht * ans
        handlings = [350] * long_calls + [100] * max(0, ans - long_calls)
        diff = total_handling_sec - sum(handlings)
        for i in range(ans):
            if diff > 0:
                handlings[i] += 1; diff -= 1
            elif diff < 0 and handlings[i] > 0:
                handlings[i] -= 1; diff += 1

        tu_ans = min(tu_offered, max(0, ans - wh_ans))
        tu_abn = tu_offered - tu_ans
        
        daily_records = []
        def create_rec(status, camp, dur_sec, tta_sec, hold_sec, hand_sec, agent, caller, disp):
            return models.CallRecord(
                row_hash=str(uuid.uuid4()), Call_ID=str(uuid.uuid4()), Call_Date=formatted_date,
                Start_Time="10:00:00", Status=status, Campaign=camp, Agent=agent,
                Caller_No=caller, Disposition=disp, Time_to_Answer=parse_time_to_string(tta_sec),
                Duration=parse_time_to_string(dur_sec), Hold_Time=parse_time_to_string(hold_sec),
                Handling_Time=parse_time_to_string(hand_sec), Call_Type="inbound"
            )

        # Distribute Campaign tags on answered calls
        for i in range(ans):
            camp = 'inbound_cc_womenhelpline' if i < wh_ans else ('inbound_cc_travelupdate' if i < wh_ans + tu_ans else 'inbound_cc')
            daily_records.append(create_rec('answered', camp, handlings[i], ttas[i], holds[i], handlings[i], 'Agent_1', f"C_{i}", 'Resolved'))
            
        # Distribute Campaign tags on abandoned calls
        for i in range(abn):
            camp = 'inbound_cc_womenhelpline' if i < (wh_offered - wh_ans) else ('inbound_cc_travelupdate' if i < (wh_offered - wh_ans) + tu_abn else 'inbound_cc')
            if i < net_abn: dur, agent = 10, 'Agent_1'
            elif i < net_abn + short_abn: dur, agent = 3, 'Agent_1'
            elif i < net_abn + short_abn + queue_fail: dur, agent = 10, ''
            else: dur, agent = 10, 'Agent_1'
            daily_records.append(create_rec('unanswered', camp, dur, 10, 0, 0, agent, f"U_{i}", ''))

        # Distribute repeat caller identities to match repeat metrics
        if same_day_repeat > 0 and daily_records:
            t_call, t_disp = daily_records[0].Caller_No, daily_records[0].Disposition
            d_cnt, r_cnt = same_day_disp_repeat, same_day_repeat - same_day_disp_repeat
            for i in range(1, len(daily_records)):
                if d_cnt > 0:
                    daily_records[i].Caller_No, daily_records[i].Disposition = t_call, t_disp
                    d_cnt -= 1
                elif r_cnt > 0:
                    daily_records[i].Caller_No, daily_records[i].Disposition = t_call, f"Disp_{i}"
                    r_cnt -= 1

        db.add_all(daily_records)
        db.commit()

    db.close()
    print("\nDatabase load completed successfully! The historical data is perfectly aligned to standard schema.")

if __name__ == "__main__":
    load_excel_to_db("Inbound Metric Data_1st April 2025 to 18th June 2026.xlsx")
