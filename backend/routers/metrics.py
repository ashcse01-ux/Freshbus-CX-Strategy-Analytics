from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
import pandas as pd

from database import get_tenant_db_engine, get_master_db
import models
from sqlalchemy.orm import sessionmaker

router = APIRouter(
    prefix="/api/metrics",
    tags=["metrics"],
)

def parse_time_to_seconds(time_str):
    """Converts HH:MM:SS or MM:SS strings to total seconds."""
    if not time_str or pd.isna(time_str) or str(time_str).strip() == '':
        return 0
    try:
        parts = str(time_str).strip().split(':')
        if len(parts) == 3: # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2: # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0

@router.get("/aggregate")
def read_aggregated_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    disposition: Optional[str] = Query(None),
    campaign: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    call_type: Optional[str] = Query(None),
    hangup_by: Optional[str] = Query(None),
    dial_status: Optional[str] = Query(None),
    transfer_details: Optional[str] = Query(None),
    rating: Optional[str] = Query(None),
    agent_hc: int = Query(10), # Manual Entry placeholder
    gross_tickets: int = Query(0), # Manual Entry placeholder
    view_type: str = Query("daily"),
    parent_campaign: str = Query(..., description="The parent campaign name (tenant DB)")
):
    engine = get_tenant_db_engine(parent_campaign)
    TenantSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TenantSessionLocal()
    
    try:
        query = db.query(models.CallRecord)

        # Load dataset to Pandas
        df = pd.read_sql(query.statement, engine)
        if df.empty:
            return {
                "summary": {
                    "volume": {"total_offered":0,"agent_offered":0,"answered":0,"wh_offered":0,"wh_answered":0,"travel_update_offered":0,"inbound_wh_offered":0},
                    "service": {"sl_calls":0,"sl_pct":0,"al_pct":0,"avg_wait":0,"on_hold":0,"avg_hold":0},
                    "efficiency": {"aht":0,"long_calls":0,"long_call_pct":0,"call_per_agent":0,"same_day_repeat":0,"repeat_pct":0},
                    "failure": {"overall_abn":0,"net_abn":0,"net_abn_pct":0,"short_abn":0,"short_pct":0,"gross_abn_pct":0,"queue_level":0},
                    "journey": {"intr_journey_pct":0,"travel_util_pct":0,"same_day_disp_repeat":0,"disp_repeat_pct":0}
                },
                "chart_data": [], "distributions": {}, "heatmap": [], "raw_count": 0, "total_rows": 0,
                "buckets": {"tta": {}, "duration": {}, "ratings": {}}
            }
    finally:
        db.close()

    # --- ROBUST NORMALIZATION ---
    # Convert all object columns to lowercase and strip whitespace
    text_cols = ['Agent', 'Status', 'Campaign', 'Disposition', 'Hangup_By', 'DID', 'Skill', 'Call_Type', 'Dial_Status', 'Transfer_Details', 'Ratings']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
            # Special case: handle 'none' or 'nan' as empty strings
            df.loc[df[col].isin(['nan', 'none', 'null']), col] = ''

    # Date/Time Normalization
    df['Call_Date_DT'] = pd.to_datetime(df['Call_Date'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['Call_Date_DT'])
    
    # Combined Timestamp column
    df['Timestamp'] = pd.to_datetime(df['Call_Date'] + ' ' + df['Start_Time'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
    # Fallback to general parsing if any NaT
    nat_mask = df['Timestamp'].isna() & df['Call_Date'].notna() & df['Start_Time'].notna()
    if nat_mask.any():
        df.loc[nat_mask, 'Timestamp'] = pd.to_datetime(df.loc[nat_mask, 'Call_Date'] + ' ' + df.loc[nat_mask, 'Start_Time'], errors='coerce')

    # --- DEDUPLICATE BY CALL_ID ---
    # OzoneTel may return multiple legs for the same Call_ID (e.g. transfer/retry). 
    # To match manual tracking and avoid double-counting, we resolve each Call_ID to a single "best" leg.
    if 'Call_ID' in df.columns and not df.empty:
        # Priority: answered > unanswered, agent assigned > no agent, disposition > no disposition
        df['_status_score'] = df['Status'].apply(lambda x: 0 if str(x).lower().strip() == 'answered' else 1)
        df['_agent_score'] = df['Agent'].apply(lambda x: 0 if str(x).strip() != '' else 1)
        df['_disp_score'] = df['Disposition'].apply(lambda x: 0 if str(x).strip() != '' else 1)
        
        df = df.sort_values(by=['_status_score', '_agent_score', '_disp_score', 'Timestamp'])
        df = df.drop_duplicates(subset=['Call_ID'], keep='first')
        df = df.drop(columns=['_status_score', '_agent_score', '_disp_score'])

    # --- DEFAULT DATE INTELLIGENCE ---
    # We want "Today" for Daily, but if Today is empty, fall back to the Latest Day found.
    # Weekly and Monthly should show the trailing windows.
    latest_db_date = df['Call_Date_DT'].max()
    current_today = pd.Timestamp.now().normalize()
    
    if not start_date and not end_date:
        if view_type.lower() == "1hr":
            base_time = df['Timestamp'].max()
            if pd.notna(base_time):
                df = df[df['Timestamp'] >= (base_time - pd.Timedelta(hours=1))]
        elif view_type.lower() == "2hr":
            base_time = df['Timestamp'].max()
            if pd.notna(base_time):
                df = df[df['Timestamp'] >= (base_time - pd.Timedelta(hours=2))]
        elif view_type.lower() == "3hr":
            base_time = df['Timestamp'].max()
            if pd.notna(base_time):
                df = df[df['Timestamp'] >= (base_time - pd.Timedelta(hours=3))]
        elif view_type.lower() == "daily":
            # Focus on today, fallback to latest available day in DB
            if (df['Call_Date_DT'] == current_today).any():
                df = df[df['Call_Date_DT'] == current_today]
            else:
                df = df[df['Call_Date_DT'] == latest_db_date]
        elif view_type.lower() == "yesterday":
            yesterday = current_today - pd.Timedelta(days=1)
            df = df[df['Call_Date_DT'] == yesterday]
        elif view_type.lower() == "weekly":
            df = df[df['Call_Date_DT'] >= (current_today - pd.Timedelta(days=7))]
        elif view_type.lower() == "monthly":
            df = df[df['Call_Date_DT'] >= (current_today - pd.Timedelta(days=30))]
    else:
        # Respect explicit filters from Calendar
        if start_date:
            df = df[df['Call_Date_DT'] >= pd.to_datetime(start_date, errors='coerce')]
        if end_date:
            df = df[df['Call_Date_DT'] <= pd.to_datetime(end_date, errors='coerce')]

    # Apply other filters
    if agent: df = df[df['Agent'] == agent.lower().strip()]
    if disposition: df = df[df['Disposition'] == disposition.lower().strip()]
    if campaign: df = df[df['Campaign'] == campaign.lower().strip()]
    if status: df = df[df['Status'] == status.lower().strip()]
    if skill: df = df[df['Skill'] == skill.lower().strip()]
    if call_type: df = df[df['Call_Type'] == call_type.lower().strip()]
    if hangup_by: df = df[df['Hangup_By'] == hangup_by.lower().strip()]
    if dial_status: df = df[df['Dial_Status'] == dial_status.lower().strip()]
    
    # Force Call_Type to 'inbound' by default if not provided, to match manual tracking
    if not call_type:
        df = df[df['Call_Type'].astype(str).str.lower() == 'inbound']

    if transfer_details:
        td = transfer_details.lower().strip()
        if td == 'agent':
            df = df[df['Transfer_Details'].astype(str).str.lower().str.contains(r'\[agent\]', na=False)]
        elif td == 'csat_ivr[ivr]':
            df = df[df['Transfer_Details'].astype(str).str.lower().str.contains(r'\[ivr\]', na=False)]
        elif td == 'phone':
            df = df[df['Transfer_Details'].astype(str).str.lower().str.contains(r'\[phone\]', na=False)]
        elif td == 'n/a':
            df = df[(df['Transfer_Details'].isna()) | (df['Transfer_Details'].astype(str).str.strip() == '') | (df['Transfer_Details'].astype(str).str.lower() == 'none')]

    if rating:
        try:
            target_rating = float(rating)
            df['Ratings_Float'] = pd.to_numeric(df['Ratings'], errors='coerce')
            df = df[df['Ratings_Float'] == target_rating]
        except Exception as e:
            print(f"Error filtering ratings: {e}")

    if df.empty:
        return {
            "summary": {
                "volume": {"total_offered":0,"agent_offered":0,"answered":0,"wh_offered":0,"wh_answered":0,"travel_update_offered":0,"inbound_wh_offered":0},
                "service": {"sl_calls":0,"sl_pct":0,"al_pct":0,"avg_wait":0,"on_hold":0,"avg_hold":0},
                "efficiency": {"aht":0,"long_calls":0,"long_call_pct":0,"call_per_agent":0,"same_day_repeat":0,"repeat_pct":0},
                "failure": {"overall_abn":0,"net_abn":0,"net_abn_pct":0,"short_abn":0,"short_pct":0,"gross_abn_pct":0,"queue_level":0},
                "journey": {"intr_journey_pct":0,"travel_util_pct":0,"same_day_disp_repeat":0,"disp_repeat_pct":0}
            },
            "chart_data": [], "distributions": {}, "heatmap": [], "raw_count": 0, "total_rows": 0,
            "buckets": {"tta": {}, "duration": {}, "ratings": {}}
        }

    # Time Normalization (convert to seconds)
    df['TTA_Sec'] = df['Time_to_Answer'].apply(parse_time_to_seconds)
    df['Duration_Sec'] = df['Duration'].apply(parse_time_to_seconds)
    df['Hold_Sec'] = df['Hold_Time'].apply(parse_time_to_seconds)
    df['Handling_Sec'] = df['Handling_Time'].apply(parse_time_to_seconds)

    # --- METRIC CALCULATIONS ---
    
    # 1. Volume Metrics
    total_calls_offered = len(df)
    calls_answered = int((df['Status'] == 'answered').sum())
    agent_calls_offered = int(((df['Agent'] != '') & df['Status'].isin(['answered', 'unanswered'])).sum())
    
    # WH & Travel Update
    wh_offered = int((df['Campaign'] == 'inbound_cc_womenhelpline').sum())
    wh_answered = int(((df['Campaign'] == 'inbound_cc_womenhelpline') & (df['Status'] == 'answered')).sum())
    travel_update_offered = int((df['Campaign'] == 'inbound_cc_travelupdate').sum())
    inbound_wh_offered = total_calls_offered - travel_update_offered

    # 2. Failure Metrics (Abandonment)
    overall_abn = int((df['Status'] == 'unanswered').sum())
    # Net Abn: Agent assigned, Unanswered, Duration > 5s
    net_abn_calls = int(((df['Agent'] != '') & (df['Status'] == 'unanswered') & (df['Duration_Sec'] > 5)).sum())
    short_abn_calls = int(((df['Agent'] != '') & (df['Status'] == 'unanswered') & (df['Duration_Sec'] <= 5)).sum())
    
    # Queue Level Failure (Abandoned before reaching an agent)
    queue_fail = int(((df['Agent'] == '') & (df['Status'] == 'unanswered')).sum())

    # 3. Quality & Efficiency Metrics
    sl_calls = int(((df['TTA_Sec'] <= 20) & (df['Status'] == 'answered')).sum())
    on_hold_calls = int((df['Hold_Sec'] > 0).sum())
    long_calls_5m = int(((df['Status'] == 'answered') & (df['Handling_Sec'] > 300)).sum())
    
    # 4. Averages
    avg_wait_time = df['TTA_Sec'].mean() if not df.empty else 0
    avg_hold_time = df[df['Hold_Sec'] > 0]['Hold_Sec'].mean() if (df['Hold_Sec'] > 0).any() else 0
    answered_aht = df[df['Status'] == 'answered']['Handling_Sec'].mean() if calls_answered > 0 else 0

    # 5. Repeat Call Logic
    # Group by Caller No and Day to find repeaters
    df['Day_Key'] = df['Call_Date_DT'].dt.date
    repeat_mask = df.duplicated(subset=['Caller_No', 'Day_Key'], keep='first')
    repeat_calls_count = int(repeat_mask.sum())
    
    # Same Day Same Disposition Repeat (Count all rows involved in a same day disp repeat)
    disp_repeat_mask = df.duplicated(subset=['Caller_No', 'Day_Key', 'Disposition'], keep=False)
    same_day_disp_repeat = int(disp_repeat_mask.sum())

    # Additional Drop/Disconnect Metrics
    call_drop = int(((df['Status'] == 'answered') & (df['Disposition'].astype(str).str.contains('call drop', case=False, na=False))).sum())
    blank_call = int(((df['Status'] == 'answered') & (df['Disposition'].astype(str).str.contains('blank call', case=False, na=False))).sum())
    call_back = call_drop + blank_call
    agent_disconnected = int(((df['Status'] == 'answered') & (df['Hangup_By'].astype(str).str.contains('agent', case=False, na=False))).sum())

    # --- RATIO CALCULATIONS ---
    short_call_pct = (short_abn_calls / calls_answered * 100) if calls_answered > 0 else 0
    gross_abn_pct = ((overall_abn - short_abn_calls) / total_calls_offered * 100) if total_calls_offered > 0 else 0
    net_abn_pct = (net_abn_calls / total_calls_offered * 100) if total_calls_offered > 0 else 0
    sl_pct = (sl_calls / calls_answered * 100) if calls_answered > 0 else 0
    al_pct = (calls_answered / agent_calls_offered * 100) if agent_calls_offered > 0 else 0
    long_call_pct = (long_calls_5m / calls_answered * 100) if calls_answered > 0 else 0
    call_per_agent = (calls_answered / agent_hc) if agent_hc > 0 else 0
    
    # Repeat percentages
    same_day_repeat_pct = (repeat_calls_count / total_calls_offered * 100) if total_calls_offered > 0 else 0
    same_day_disp_repeat_pct = (same_day_disp_repeat / calls_answered * 100) if calls_answered > 0 else 0

    # Journey Metrics (using gross_tickets manual entry)
    intr_journey_pct = ((inbound_wh_offered - gross_tickets) / inbound_wh_offered * 100) if inbound_wh_offered > 0 else 0
    travel_update_util_pct = ((travel_update_offered - gross_tickets) / travel_update_offered * 100) if travel_update_offered > 0 else 0
    agent_disconnected_pct = (agent_disconnected / calls_answered * 100) if calls_answered > 0 else 0

    # --- BUCKETIZATION CALCULATIONS ---
    # TTA Buckets: 0-10s, 11-30s, 31-60s, 1-2m, >2m
    tta_buckets = {
        "0-10s": int((df['TTA_Sec'] <= 10).sum()),
        "11-30s": int(((df['TTA_Sec'] > 10) & (df['TTA_Sec'] <= 30)).sum()),
        "31-60s": int(((df['TTA_Sec'] > 30) & (df['TTA_Sec'] <= 60)).sum()),
        "1-2m": int(((df['TTA_Sec'] > 60) & (df['TTA_Sec'] <= 120)).sum()),
        ">2m": int((df['TTA_Sec'] > 120).sum())
    }
    
    # Talk Time (Duration) Buckets: <1m, 1-3m, 3-5m, 5-10m, >10m (for answered calls)
    dur_buckets = {
        "<1m": int(((df['Status'] == 'answered') & (df['Duration_Sec'] < 60)).sum()),
        "1-3m": int(((df['Status'] == 'answered') & (df['Duration_Sec'] >= 60) & (df['Duration_Sec'] < 180)).sum()),
        "3-5m": int(((df['Status'] == 'answered') & (df['Duration_Sec'] >= 180) & (df['Duration_Sec'] < 300)).sum()),
        "5-10m": int(((df['Status'] == 'answered') & (df['Duration_Sec'] >= 300) & (df['Duration_Sec'] < 600)).sum()),
        ">10m": int(((df['Status'] == 'answered') & (df['Duration_Sec'] >= 600)).sum())
    }
    
    # Ratings Buckets: 0, 1, 2, 3, 4, 5
    rating_buckets = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    if 'Ratings' in df.columns:
        df['Ratings_Float'] = pd.to_numeric(df['Ratings'], errors='coerce')
        for val in df['Ratings_Float'].dropna():
            rounded = int(round(val))
            if 0 <= rounded <= 5:
                rating_buckets[str(rounded)] += 1

    # --- DISTRIBUTIONS for Charts ---
    def get_top_dist(col, limit=10):
        """Return top N distribution as ordered dict (excludes blanks)."""
        return (
            df[df[col] != ''][col]
            .value_counts()
            .head(limit)
            .to_dict()
        )

    distributions = {
        "dispositions": get_top_dist('Disposition', 10),
        "campaigns":    get_top_dist('Campaign', 10),
        "hangups":      get_top_dist('Hangup_By', 10),
        "agents":       get_top_dist('Agent', 10)
    }

    # --- HEATMAP DATA (Day vs Hour) ---
    df['Hour'] = pd.to_datetime(df['Start_Time'], errors='coerce').dt.hour
    df['DayOfWeek'] = df['Call_Date_DT'].dt.dayofweek # 0=Mon, 6=Sun
    
    # Optimized Grid Generation for 7x24 Heatmap
    heatmap_grid = pd.DataFrame(0, index=range(7), columns=range(24))
    if not df.empty:
        counts = df.groupby(['DayOfWeek', 'Hour']).size()
        for (day, hour), val in counts.items():
            if pd.notna(day) and pd.notna(hour):
                heatmap_grid.at[int(day), int(hour)] = int(val)
    
    heatmap_data = heatmap_grid.values.tolist()

    # --- TIME SERIES CHART DATA ---
    chart_data = []
    freq_map = {
        "1hr": "5min",
        "2hr": "10min",
        "3hr": "15min",
        "daily": "D",
        "weekly": "W",
        "monthly": "ME",
        "yearly": "YE"
    }
    freq = freq_map.get(view_type.lower(), "D")
    
    resample_col = 'Timestamp' if view_type.lower() in ["1hr", "2hr", "3hr"] else 'Call_Date_DT'
    
    df_resample = df.sort_values(by=resample_col)
    
    for timestamp, g_df in df_resample.resample(freq, on=resample_col):
        if g_df.empty: continue
        if view_type.lower() in ["1hr", "2hr", "3hr"]:
            label = timestamp.strftime('%H:%M')
        else:
            label = timestamp.strftime('%Y-%m-%d')
        chart_data.append({
            "label": label,
            "total": len(g_df),
            "answered": int((g_df['Status'] == 'answered').sum()),
            "abn": int((g_df['Status'] == 'unanswered').sum())
        })

    return {
        "summary": {
            "volume": {
                "total_offered": total_calls_offered,
                "agent_offered": agent_calls_offered,
                "answered": calls_answered,
                "wh_offered": wh_offered,
                "wh_answered": wh_answered,
                "travel_update_offered": travel_update_offered,
                "inbound_wh_offered": inbound_wh_offered
            },
            "service": {
                "sl_calls": sl_calls,
                "sl_pct": round(sl_pct, 2),
                "al_pct": round(al_pct, 2),
                "avg_wait": round(avg_wait_time, 1),
                "on_hold": on_hold_calls,
                "avg_hold": round(avg_hold_time, 1)
            },
            "efficiency": {
                "aht": round(answered_aht, 1),
                "long_calls": long_calls_5m,
                "long_call_pct": round(long_call_pct, 2),
                "call_per_agent": round(call_per_agent, 2),
                "same_day_repeat": repeat_calls_count,
                "repeat_pct": round(same_day_repeat_pct, 2)
            },
            "failure": {
                "overall_abn": overall_abn,
                "net_abn": net_abn_calls,
                "net_abn_pct": round(net_abn_pct, 2),
                "short_abn": short_abn_calls,
                "short_pct": round(short_call_pct, 2),
                "gross_abn_pct": round(gross_abn_pct, 2),
                "queue_level": queue_fail,
                "call_drop": call_drop,
                "blank_call": blank_call,
                "call_back": call_back,
                "agent_disconnected": agent_disconnected,
                "agent_disconnected_pct": round(agent_disconnected_pct, 2)
            },
            "journey": {
                "intr_journey_pct": round(intr_journey_pct, 2),
                "travel_util_pct": round(travel_update_util_pct, 2),
                "same_day_disp_repeat": same_day_disp_repeat,
                "disp_repeat_pct": round(same_day_disp_repeat_pct, 2)
            }
        },
        "distributions": distributions,
        "heatmap": heatmap_data,
        "chart_data": chart_data,
        "raw_count": total_calls_offered,
        "total_rows": total_calls_offered,
        "buckets": {
            "tta": tta_buckets,
            "duration": dur_buckets,
            "ratings": rating_buckets
        }
    }

@router.get("/filters")
def get_filter_options(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    parent_campaign: str = Query(..., description="The parent campaign name (tenant DB)")
):
    engine = get_tenant_db_engine(parent_campaign)
    TenantSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TenantSessionLocal()
    
    try:
        query = db.query(models.CallRecord)
        
        # If a date range is provided, pre-filter the options to show only relevant ones
        if start_date or end_date:
            df = pd.read_sql(query.statement, engine)
            if not df.empty and 'Call_Date' in df.columns:
                df['Call_Date_DT'] = pd.to_datetime(df['Call_Date'], format='%d-%m-%Y', errors='coerce')
                if start_date:
                    df = df[df['Call_Date_DT'] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df['Call_Date_DT'] <= pd.to_datetime(end_date)]
            
            agents = [a for a in df['Agent'].unique() if a] if not df.empty else []
            campaigns = [c for c in df['Campaign'].unique() if c] if not df.empty else []
            statuses = [s for s in df['Status'].unique() if s] if not df.empty else []
            skills = [s for s in df['Skill'].unique() if s] if not df.empty else []
            call_types = [c for c in df['Call_Type'].unique() if c] if not df.empty else []
            hangups = [h for h in df['Hangup_By'].unique() if h] if not df.empty else []
            dial_statuses = [d for d in df['Dial_Status'].unique() if d] if not df.empty else []
            
            if not df.empty:
                disp_counts = df['Disposition'].value_counts()
                top_10 = disp_counts.head(10).index.tolist()
                all_dispositions = disp_counts.index.tolist()
            else:
                top_10 = []
                all_dispositions = []
        else:
            # Fallback to distinct query if no date range
            agents = [r[0] for r in db.query(models.CallRecord.Agent).distinct().all() if r[0]]
            campaigns = [r[0] for r in db.query(models.CallRecord.Campaign).distinct().all() if r[0]]
            statuses = [r[0] for r in db.query(models.CallRecord.Status).distinct().all() if r[0]]
            skills = [r[0] for r in db.query(models.CallRecord.Skill).distinct().all() if r[0]]
            call_types = [r[0] for r in db.query(models.CallRecord.Call_Type).distinct().all() if r[0]]
            hangups = [r[0] for r in db.query(models.CallRecord.Hangup_By).distinct().all() if r[0]]
            dial_statuses = [r[0] for r in db.query(models.CallRecord.Dial_Status).distinct().all() if r[0]]
            
            disp_query = db.query(models.CallRecord.Disposition, func.count(models.CallRecord.Disposition))\
                           .group_by(models.CallRecord.Disposition)\
                           .order_by(func.count(models.CallRecord.Disposition).desc())\
                           .all()
            top_10 = [r[0] for r in disp_query[:10] if r[0]]
            all_dispositions = [r[0] for r in disp_query if r[0]]
    
    finally:
        db.close()

    return {
        "agents": sorted(agents),
        "campaigns": sorted(campaigns),
        "statuses": sorted(statuses),
        "skills": sorted(skills),
        "call_types": sorted(call_types),
        "hangups": sorted(hangups),
        "dial_statuses": sorted(dial_statuses),
        "dispositions": sorted(all_dispositions),
        "top_dispositions": top_10
    }
