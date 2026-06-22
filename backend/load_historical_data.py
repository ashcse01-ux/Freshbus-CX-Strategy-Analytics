import json
import pandas as pd
from datetime import datetime, timedelta
import uuid
import random

from database import get_tenant_db_engine
from sqlalchemy.orm import sessionmaker
import models

def parse_time_to_string(total_seconds):
    total_seconds = int(max(0, total_seconds))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def load_data():
    with open('manual_daily_metrics.json') as f:
        data = json.load(f)

    engine = get_tenant_db_engine("inbound_cc")
    TenantSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TenantSessionLocal()
    
    # Check if data already exists to avoid duplication
    existing_dates = set([r[0] for r in db.query(models.CallRecord.Call_Date).distinct().all()])

    all_records = []

    for date_str, m in data.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt > datetime(2026, 6, 7):
            continue # API data is final from June 8th onwards
            
        formatted_date = dt.strftime("%d-%m-%Y")
        
        # If this date already has records in the DB, skip it (or we could delete them first)
        # We will delete them first to be safe and ensure exact match
        db.query(models.CallRecord).filter(models.CallRecord.Call_Date == formatted_date).delete()
        
        ans = int(m.get('answered', 0))
        abn = int(m.get('overall_abn', 0))
        wh_ans = int(m.get('wh_answered', 0))
        wh_offered = int(m.get('wh_offered', 0))
        tu_offered = int(m.get('travel_update_offered', 0))
        
        # Unanswered splits
        net_abn = int(m.get('net_abn', 0))
        short_abn = int(m.get('short_abn', 0))
        queue_fail = int(m.get('queue_level', 0))
        
        # Handle small mismatch in unanswered
        remaining_abn = abn - (net_abn + short_abn + queue_fail)
        if remaining_abn < 0:
            queue_fail += remaining_abn # Adjust if negative
            queue_fail = max(0, queue_fail)
            remaining_abn = 0
            
        # Answered splits
        sl_calls = int(m.get('sl_calls', 0))
        long_calls = int(m.get('long_calls', 0))
        on_hold = int(m.get('on_hold', 0))
        
        # Averages
        avg_wait = m.get('avg_wait', 0)
        avg_hold = m.get('avg_hold', 0)
        aht = m.get('aht', 0)
        
        # Repeats
        same_day_repeat = int(m.get('same_day_repeat', 0))
        same_day_disp_repeat = int(m.get('same_day_disp_repeat', 0))

        # Generate answered calls
        # 1. Distribute Campaigns
        # We know wh_ans calls are inbound_cc_womenhelpline
        # The rest of answered calls are distributed between travel update and inbound_cc
        # Let's say travel_ans = min(tu_offered, ans - wh_ans) ? We don't have travel_ans exact count.
        # Just distribute them so the total offered matches.
        
        daily_records = []
        
        def create_base_record(status, campaign, duration_sec, tta_sec, hold_sec, handling_sec, agent, caller_no, disp):
            return models.CallRecord(
                row_hash=str(uuid.uuid4()),
                Call_ID=str(uuid.uuid4()),
                Call_Date=formatted_date,
                Start_Time="10:00:00", # Fixed time for simplicity
                Status=status,
                Campaign=campaign,
                Agent=agent,
                Caller_No=caller_no,
                Disposition=disp,
                Time_to_Answer=parse_time_to_string(tta_sec),
                Duration=parse_time_to_string(duration_sec),
                Hold_Time=parse_time_to_string(hold_sec),
                Handling_Time=parse_time_to_string(handling_sec),
                Call_Type="inbound"
            )

        # Pre-calculate arrays for TTA, Handling, Hold
        # TTA
        total_wait_sec = avg_wait * ans
        ttas = [15] * sl_calls + [45] * (ans - sl_calls)
        # Adjust sum to match total_wait_sec
        diff = total_wait_sec - sum(ttas)
        for i in range(ans):
            if diff > 0:
                ttas[i] += 1
                diff -= 1
            elif diff < 0 and ttas[i] > 0:
                ttas[i] -= 1
                diff += 1

        # Hold
        holds = [avg_hold] * on_hold + [0] * (ans - on_hold)
        
        # Handling (AHT)
        total_handling_sec = aht * ans
        handlings = [350] * long_calls + [100] * (ans - long_calls)
        diff = total_handling_sec - sum(handlings)
        for i in range(ans):
            if diff > 0:
                handlings[i] += 1
                diff -= 1
            elif diff < 0 and handlings[i] > 0:
                handlings[i] -= 1
                diff += 1

        # We need tu_offered calls total. Some can be answered, some unanswered.
        # Let's just make travel_update_offered answered calls if possible.
        tu_ans = min(tu_offered, max(0, ans - wh_ans))
        tu_abn = tu_offered - tu_ans

        # Generate Answered Calls
        for i in range(ans):
            if i < wh_ans:
                camp = 'inbound_cc_womenhelpline'
            elif i < wh_ans + tu_ans:
                camp = 'inbound_cc_travelupdate'
            else:
                camp = 'inbound_cc'
                
            rec = create_base_record(
                status='answered',
                campaign=camp,
                duration_sec=handlings[i], # Duration is not strictly checked for answered, Handling is used for AHT
                tta_sec=ttas[i],
                hold_sec=holds[i],
                handling_sec=handlings[i],
                agent='Agent_1',
                caller_no=f"C_{i}",
                disp='Resolved'
            )
            daily_records.append(rec)
            
        # Generate Unanswered Calls
        for i in range(abn):
            if i < (wh_offered - wh_ans):
                camp = 'inbound_cc_womenhelpline'
            elif i < (wh_offered - wh_ans) + tu_abn:
                camp = 'inbound_cc_travelupdate'
            else:
                camp = 'inbound_cc'
                
            if i < net_abn:
                dur = 10
                agent = 'Agent_1'
            elif i < net_abn + short_abn:
                dur = 3
                agent = 'Agent_1'
            elif i < net_abn + short_abn + queue_fail:
                dur = 10
                agent = ''
            else:
                dur = 10
                agent = 'Agent_1'
                
            rec = create_base_record(
                status='unanswered',
                campaign=camp,
                duration_sec=dur,
                tta_sec=10,
                hold_sec=0,
                handling_sec=0,
                agent=agent,
                caller_no=f"U_{i}",
                disp=''
            )
            daily_records.append(rec)
            
        # Fix Repeats
        # same_day_repeat is the number of duplicate caller_nos.
        # same_day_disp_repeat is the number of duplicate caller_nos + disposition.
        # We can pick a random caller_no from answered and duplicate its Caller_No on other answered calls.
        if same_day_repeat > 0 and len(daily_records) > 0:
            target_caller = daily_records[0].Caller_No
            target_disp = daily_records[0].Disposition
            
            # We apply disp repeat first
            disp_count = same_day_disp_repeat
            pure_repeat_count = same_day_repeat - same_day_disp_repeat
            
            for i in range(1, len(daily_records)):
                if disp_count > 0:
                    daily_records[i].Caller_No = target_caller
                    daily_records[i].Disposition = target_disp
                    disp_count -= 1
                elif pure_repeat_count > 0:
                    daily_records[i].Caller_No = target_caller
                    daily_records[i].Disposition = "AnotherDisp_" + str(i)
                    pure_repeat_count -= 1

        db.add_all(daily_records)
        db.commit()
        print(f"Loaded {date_str} with {len(daily_records)} records")

    db.close()

if __name__ == "__main__":
    load_data()
