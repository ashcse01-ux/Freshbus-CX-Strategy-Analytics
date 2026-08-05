import pandas as pd
import io
import time
import traceback
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from database import get_tenant_db_engine

router = APIRouter(prefix="/api/excel", tags=["excel"])

# Simple in-memory cache
EXCEL_CACHE = {}

def parse_time_to_seconds(time_str):
    if not time_str or pd.isna(time_str) or str(time_str).strip() == '':
        return 0
    try:
        parts = str(time_str).strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0

def process_dataframe(df):
    text_cols = ['Status', 'Agent', 'Disposition', 'Hangup_By', 'Call_Type']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
            df.loc[df[col].isin(['nan', 'none', 'null']), col] = ''
    
    df['Call_Date_DT'] = pd.to_datetime(df['Call_Date'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['Call_Date_DT'])
    
    if 'Time_to_Answer' in df.columns:
        df['TTA_Sec'] = df['Time_to_Answer'].apply(parse_time_to_seconds)
    else:
        df['TTA_Sec'] = 0
        
    if 'Duration' in df.columns:
        df['Dur_Sec'] = df['Duration'].apply(parse_time_to_seconds)
    else:
        df['Dur_Sec'] = 0

    df['WeekNo'] = df['Call_Date_DT'].dt.isocalendar().week
    
    return df

def aggregate_metrics(df):
    total = len(df)
    ans = len(df[df['Status'] == 'answered'])
    unans = len(df[df['Status'] == 'unanswered'])
    
    # 1. Total Calls Offered
    # 2. Total Calls Answered
    # 3. Total Calls Abandoned
    # 4. Service Level %
    sl_calls = len(df[(df['Status'] == 'answered') & (df['TTA_Sec'] <= 20)])
    sl_pct = (sl_calls / ans * 100) if ans > 0 else 0
    
    # 5. Answer Level %
    al_pct = (ans / total * 100) if total > 0 else 0
    
    # 6. Abn %
    abn_pct = (unans / total * 100) if total > 0 else 0
    
    # 7. AHT
    aht = df[df['Status'] == 'answered']['Dur_Sec'].mean() if ans > 0 else 0
    if pd.isna(aht): aht = 0
    
    return {
        "Total Calls": total,
        "Total Answered": ans,
        "Total Abandoned": unans,
        "Service Level %": f"{sl_pct:.1f}%",
        "Answer Level %": f"{al_pct:.1f}%",
        "Abandon %": f"{abn_pct:.1f}%",
        "AHT": f"{int(aht//60):02d}:{int(aht%60):02d}"
    }

@router.get("/view")
def get_excel_view(parent_campaign: str = Query("Inbound")):
    try:
        import os
        import json
        from datetime import datetime
        from sqlalchemy.orm import sessionmaker
        import models

        static_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static_excel_data.json')
        if not os.path.exists(static_json_path):
            return {"columns": [], "dates": [], "metrics": []}
            
        with open(static_json_path, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)
            
        engine = get_tenant_db_engine(parent_campaign)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Load all rows from daily_manual_metrics table
        db_rows = db.query(models.DailyManualMetric).all()
        db.close()
        manual_metrics = {row.date: row for row in db_rows}

        # Load call records from the DB
        call_df = pd.read_sql("SELECT * FROM call_records", engine)
        
        # Pre-process call records for fast aggregation
        if not call_df.empty:
            call_df['date_key'] = pd.to_datetime(call_df['Call_Date'], format='%d-%m-%Y', errors='coerce').dt.strftime('%Y-%m-%d')
            for col in ['Status', 'Agent', 'Campaign', 'Disposition', 'Hangup_By']:
                if col in call_df.columns:
                    call_df[col] = call_df[col].astype(str).str.strip().str.lower()
                    
            call_df['TTA_Sec'] = call_df['Time_to_Answer'].apply(parse_time_to_seconds)
            call_df['Duration_Sec'] = call_df['Duration'].apply(parse_time_to_seconds)
            call_df['Hold_Sec'] = call_df['Hold_Time'].apply(parse_time_to_seconds)
            call_df['Handling_Sec'] = call_df['Handling_Time'].apply(parse_time_to_seconds)
        else:
            call_df['date_key'] = pd.Series(dtype='str')
            call_df['TTA_Sec'] = pd.Series(dtype='int')
            call_df['Duration_Sec'] = pd.Series(dtype='int')
            call_df['Hold_Sec'] = pd.Series(dtype='int')
            call_df['Handling_Sec'] = pd.Series(dtype='int')

        # Load auto tracker JSON
        auto_tracker_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'auto_tracker_daily.json')
        auto_tracker_data = {}
        if os.path.exists(auto_tracker_path):
            try:
                with open(auto_tracker_path, 'r') as f:
                    auto_tracker_data = json.load(f)
            except Exception:
                pass

        # Helper to convert dates like "1/1/2026" to "YYYY-MM-DD"
        def parse_to_iso_date(d_str):
            if not d_str:
                return None
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return datetime.strptime(d_str.strip(), fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return None

        # Helper to format seconds to standard H:MM:SS format
        def format_hms(seconds):
            if pd.isna(seconds) or seconds <= 0:
                return "0:00:00"
            seconds = int(round(seconds))
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h}:{m:02d}:{s:02d}"

        # Helper to format counts
        def fmt_num(val):
            return "" if val is None or pd.isna(val) else f"{int(round(val))}"
            
        # Helper to format percentage values
        def fmt_pct(val):
            return "" if val is None or pd.isna(val) else f"{val:.2f}%"

        # Mapping columns to target dates
        col_dates_map = {}
        for i, c_date in enumerate(structured_data["dates"]):
            if c_date:
                iso = parse_to_iso_date(c_date)
                col_dates_map[i] = [iso] if iso else []
            else:
                col_dates_map[i] = []

        for i, c_date in enumerate(structured_data["dates"]):
            c_name = structured_data["columns"][i]
            if not c_date:
                if "MTD" in c_name:
                    month_abbr = c_name.split()[0][:3].lower()
                    month_map = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
                    target_month = month_map.get(month_abbr)
                    target_dates = []
                    for d in structured_data["dates"]:
                        iso = parse_to_iso_date(d)
                        if iso:
                            dt = datetime.strptime(iso, "%Y-%m-%d")
                            if dt.month == target_month:
                                target_dates.append(iso)
                    col_dates_map[i] = target_dates
                else:
                    target_dates = []
                    for j in range(i + 1, len(structured_data["dates"])):
                        next_date = structured_data["dates"][j]
                        if not next_date:
                            break
                        iso = parse_to_iso_date(next_date)
                        if iso:
                            target_dates.append(iso)
                    col_dates_map[i] = target_dates

        # Calculate metrics dictionary per column
        calculated_columns = []
        for i in range(len(structured_data["columns"])):
            target_dates = col_dates_map[i]
            if not target_dates:
                calculated_columns.append({name: "" for name in [m["name"] for m in structured_data["metrics"]]})
                continue
                
            # Filter call records
            sub_df = call_df[call_df['date_key'].isin(target_dates)]
            # Filter manual metrics
            sub_manual = [manual_metrics[d] for d in target_dates if d in manual_metrics]
            
            # Manual metrics sums
            gross_seats = sum(getattr(r, 'gross_seats', 0) or 0 for r in sub_manual)
            gross_tickets = sum(getattr(r, 'gross_tickets', 0) or 0 for r in sub_manual)
            service_delay_count = sum(getattr(r, 'service_delay_count', 0) or 0 for r in sub_manual)
            delay_pax_impacted = sum(getattr(r, 'delay_pax_impacted', 0) or 0 for r in sub_manual)
            service_cancel_count = sum(getattr(r, 'service_cancel_count', 0) or 0 for r in sub_manual)
            cancel_pax_impacted = sum(getattr(r, 'cancel_pax_impacted', 0) or 0 for r in sub_manual)
            service_breakdown_count = sum(getattr(r, 'service_breakdown_count', 0) or 0 for r in sub_manual)
            breakdown_pax_impacted = sum(getattr(r, 'breakdown_pax_impacted', 0) or 0 for r in sub_manual)
            total_pax_impacted = sum(getattr(r, 'total_pax_impacted', 0) or 0 for r in sub_manual)

            # Manual metrics for new drop/disconnect/disposed fields
            call_drop_not_done_manual = sum(getattr(r, 'call_drop_not_done', 0) or 0 for r in sub_manual) if sub_manual else None
            blank_call_not_done_manual = sum(getattr(r, 'blank_call_not_done', 0) or 0 for r in sub_manual) if sub_manual else None
            overall_call_not_done_manual = sum(getattr(r, 'overall_call_not_done', 0) or 0 for r in sub_manual) if sub_manual else None
            agent_disconnected_manual = sum(getattr(r, 'agent_disconnected', 0) or 0 for r in sub_manual) if sub_manual else None
            call_not_disposed_manual = sum(getattr(r, 'call_not_disposed', 0) or 0 for r in sub_manual) if sub_manual else None
            
            # Manual metrics averages
            def avg_attr(attr):
                vals = [getattr(r, attr) for r in sub_manual if getattr(r, attr) is not None]
                return sum(vals) / len(vals) if vals else None
                
            intr_journey_overall = avg_attr('intr_journey_overall')
            defects = avg_attr('defects')
            defects_journey = avg_attr('defects_journey')
            present_agent_hc = avg_attr('present_agent_hc')
            intr_journey_inbound_wh = avg_attr('intr_journey_inbound_wh')
            intr_journey_travel = avg_attr('intr_journey_travel')
            impacted_pct = avg_attr('impacted_pct')
            cancellations_impact_pct = avg_attr('cancellations_impact_pct')

            call_not_done_pct_manual = avg_attr('call_not_done_pct')
            agent_disconnected_pct_manual = avg_attr('agent_disconnected_pct')
            call_not_disposed_pct_manual = avg_attr('call_not_disposed_pct')

            # Call metrics calculations
            total_calls = len(sub_df)
            ans = len(sub_df[sub_df['Status'] == 'answered'])
            unans = len(sub_df[sub_df['Status'] == 'unanswered'])
            agent_calls_offered = len(sub_df[sub_df['Agent'] != ''])
            
            sub_df_answered = sub_df[sub_df['Status'] == 'answered']
            
            sl_calls = len(sub_df[(sub_df['Status'] == 'answered') & (sub_df['TTA_Sec'] <= 30)])
            wh_offered = len(sub_df[sub_df['Campaign'] == 'inbound_cc_womenhelpline'])
            wh_answered = len(sub_df[(sub_df['Campaign'] == 'inbound_cc_womenhelpline') & (sub_df['Status'] == 'answered')])
            
            net_abandoned = len(sub_df[(sub_df['Status'] == 'unanswered') & (sub_df['Duration_Sec'] > 5) & (sub_df['Agent'] != '')])
            short_abn = len(sub_df[(sub_df['Status'] == 'unanswered') & (sub_df['Duration_Sec'] <= 5)])
            
            short_call_pct = (short_abn / ans * 100) if ans > 0 else 0
            gross_abn_pct = (unans / total_calls * 100) if total_calls > 0 else 0
            gross_abn_wo_short = ((unans - short_abn) / total_calls * 100) if total_calls > 0 else 0
            net_abn_pct = (net_abandoned / total_calls * 100) if total_calls > 0 else 0
            
            aht_dur = sub_df_answered['Duration_Sec'].mean() if not sub_df_answered.empty else 0
            sl_pct = (sl_calls / ans * 100) if ans > 0 else 0
            al_pct = (ans / agent_calls_offered * 100) if agent_calls_offered > 0 else 0
            
            total_wait = sub_df_answered['TTA_Sec'].sum() if not sub_df_answered.empty else 0
            avg_wait = sub_df_answered['TTA_Sec'].mean() if not sub_df_answered.empty else 0
            
            on_hold = len(sub_df_answered[sub_df_answered['Hold_Sec'] > 0])
            hold_pct = (on_hold / ans * 100) if ans > 0 else 0
            
            hold_df = sub_df_answered[sub_df_answered['Hold_Sec'] > 0]
            avg_hold = hold_df['Hold_Sec'].mean() if not hold_df.empty else 0
            
            ans_aht = sub_df_answered['Handling_Sec'].mean() if not sub_df_answered.empty else 0
            
            handling_gt_5 = len(sub_df_answered[sub_df_answered['Duration_Sec'] > 300])
            long_call_pct = (handling_gt_5 / ans * 100) if ans > 0 else 0
            
            call_per_agent = (ans / present_agent_hc) if present_agent_hc and present_agent_hc > 0 else 0
            queue_fail = len(sub_df[(sub_df['Agent'] == '') & (sub_df['Status'] == 'unanswered') & (sub_df['Duration_Sec'] > 5)])
            
            # Repeat Call Logic
            repeat_calls_count = 0
            same_day_disp_repeat = 0
            if not sub_df.empty:
                dup_sub = sub_df.duplicated(subset=['Caller_No', 'date_key'], keep='first')
                repeat_calls_count = int(dup_sub.sum())
                
                disp_df = sub_df[sub_df['Disposition'] != '']
                disp_dup = disp_df.duplicated(subset=['Caller_No', 'date_key', 'Disposition'], keep='first')
                same_day_disp_repeat = int(disp_dup.sum())
                
            same_day_disp_repeat_pct = (same_day_disp_repeat / ans * 100) if ans > 0 else 0
            
            travel_update_offered = len(sub_df[sub_df['Campaign'] == 'inbound_cc_travelupdate'])
            inbound_wh_offered = total_calls - travel_update_offered
            
            same_day_repeat_pct = (repeat_calls_count / total_calls * 100) if total_calls > 0 else 0

            # Auto tracker integration
            call_drop = 0
            blank_call = 0
            call_drop_not_done = 0
            blank_call_not_done = 0
            overall_call_not_done = 0
            
            has_json_data = False
            if auto_tracker_data:
                for d in target_dates:
                    if d in auto_tracker_data:
                        has_json_data = True
                        call_drop += auto_tracker_data[d].get('Call Drop', 0)
                        blank_call += auto_tracker_data[d].get('Blank Call', 0)
                        call_drop_not_done += auto_tracker_data[d].get('Call Drop Not Done', 0)
                        blank_call_not_done += auto_tracker_data[d].get('Blank Call Not Done', 0)
                        overall_call_not_done += auto_tracker_data[d].get('Overall Call Not Done', 0)
                        
            if not has_json_data:
                call_drop = len(sub_df[sub_df['Disposition'] == 'call drop'])
                blank_call = len(sub_df[(sub_df['Disposition'] == 'others_blank call') & (sub_df['Duration_Sec'] > 5)])
                call_drop_not_done = len(sub_df[(sub_df['Disposition'] == 'call drop') & (sub_df['Comments'] == '')])
                blank_call_not_done = len(sub_df[(sub_df['Disposition'] == 'others_blank call') & (sub_df['Duration_Sec'] > 5) & (sub_df['Comments'] == '')])
                overall_call_not_done = call_drop_not_done + blank_call_not_done

            # Prioritize manual metrics DB/Excel rows if available
            if call_drop_not_done_manual is not None:
                call_drop_not_done = call_drop_not_done_manual
            if blank_call_not_done_manual is not None:
                blank_call_not_done = blank_call_not_done_manual
            if overall_call_not_done_manual is not None:
                overall_call_not_done = overall_call_not_done_manual
                
            call_back = call_drop + blank_call
            
            if call_not_done_pct_manual is not None:
                call_not_done_pct = call_not_done_pct_manual * 100 if call_not_done_pct_manual <= 1.0 else call_not_done_pct_manual
            else:
                call_not_done_pct = (overall_call_not_done / call_back * 100) if call_back > 0 else 0

            # Calculate agent disconnection and call disposal metrics
            if agent_disconnected_manual is not None:
                agent_disconnected = agent_disconnected_manual
            else:
                agent_disconnected = len(sub_df[(sub_df['Status'] == 'answered') & (sub_df['Hangup_By'] == 'agenthangup')])

            if agent_disconnected_pct_manual is not None:
                agent_disconnected_pct = agent_disconnected_pct_manual * 100 if agent_disconnected_pct_manual <= 1.0 else agent_disconnected_pct_manual
            else:
                agent_disconnected_pct = (agent_disconnected / ans * 100) if ans > 0 else 0

            if call_not_disposed_manual is not None:
                call_not_disposed = call_not_disposed_manual
            else:
                call_not_disposed = len(sub_df[(sub_df['Status'] == 'answered') & (sub_df['Disposition'] == '')])

            if call_not_disposed_pct_manual is not None:
                call_not_disposed_pct = call_not_disposed_pct_manual * 100 if call_not_disposed_pct_manual <= 1.0 else call_not_disposed_pct_manual
            else:
                call_not_disposed_pct = (call_not_disposed / ans * 100) if ans > 0 else 0

            calculated_columns.append({
                "Gross Seats": fmt_num(gross_seats) if sub_manual else "",
                "Gross Tickets": fmt_num(gross_tickets) if sub_manual else "",
                "Intr/Journey ( Overall )": fmt_pct(intr_journey_overall * 100) if intr_journey_overall is not None else "",
                "Defects": fmt_num(defects) if defects is not None else "",
                "Defects/Journey": fmt_pct(defects_journey * 100) if defects_journey is not None else "",
                "Total Calls Offered": fmt_num(total_calls),
                "Agent Calls offered": fmt_num(agent_calls_offered),
                "Calls Answered": fmt_num(ans),
                "SL Calls": fmt_num(sl_calls),
                "WH Total calls offered": fmt_num(wh_offered),
                "WH Calls Answered": fmt_num(wh_answered),
                "Overall Abn": fmt_num(unans),
                "Net Abandoned calls": fmt_num(net_abandoned),
                "Short Call Abn": fmt_num(short_abn),
                "Short Call %- Abn": fmt_pct(short_call_pct),
                "Gross Abn%": fmt_pct(gross_abn_pct),
                "Gross Abn%(WO Short Calls)": fmt_pct(gross_abn_wo_short),
                "Net Abn%": fmt_pct(net_abn_pct),
                "Duration - AHT": format_hms(aht_dur),
                "SL%": fmt_pct(sl_pct),
                "AL%": fmt_pct(al_pct),
                "Total Wait Time": format_hms(total_wait),
                "Avg. Wait Time": format_hms(avg_wait),
                "On Hold calls": fmt_num(on_hold),
                "Hold Call%": fmt_pct(hold_pct),
                "Avg Wait Time": format_hms(avg_wait),
                "Avg Hold Time": format_hms(avg_hold),
                "Answered - AHT": format_hms(ans_aht),
                "Present Agent HC": fmt_num(present_agent_hc) if present_agent_hc is not None else "",
                "Handling Time  >5mins": fmt_num(handling_gt_5),
                "Long Call %": fmt_pct(long_call_pct),
                "Call/Agent": f"{call_per_agent:.2f}" if call_per_agent else "",
                "Queue level Abn": fmt_num(queue_fail),
                "Disposition ( Repeat CallS )": fmt_num(same_day_disp_repeat),
                "Same Day Same Disposition - Repeat %": fmt_pct(same_day_disp_repeat_pct),
                "Calls Offered (Inbound +Women Helpline)": fmt_num(inbound_wh_offered),
                "Calls Offered (Travel Update)": fmt_num(travel_update_offered),
                "Intr/Journey % ( Inbound + WH)": fmt_pct(intr_journey_inbound_wh * 100) if intr_journey_inbound_wh is not None else "",
                "Intr/Journey %  ( Travel update )": fmt_pct(intr_journey_travel * 100) if intr_journey_travel is not None else "",
                "Repeat calls": fmt_num(repeat_calls_count),
                "Same Day Repeat %": fmt_pct(same_day_repeat_pct),
                "No. of Service Delay": fmt_num(service_delay_count) if sub_manual else "",
                "Delay Pax Impacted": fmt_num(delay_pax_impacted) if sub_manual else "",
                "No. of Service Cancel": fmt_num(service_cancel_count) if sub_manual else "",
                "Service Cancel Pax Impacted": fmt_num(cancel_pax_impacted) if sub_manual else "",
                "No. of Service Breakdown": fmt_num(service_breakdown_count) if sub_manual else "",
                "Break Down Pax Impacted": fmt_num(breakdown_pax_impacted) if sub_manual else "",
                "Impacted %": fmt_pct(impacted_pct * 100) if impacted_pct is not None else "",
                "Total Pax Impacted": fmt_num(total_pax_impacted) if sub_manual else "",
                "Cancellations Impact %": fmt_pct(cancellations_impact_pct * 100) if cancellations_impact_pct is not None else "",
                "Call Drop": fmt_num(call_drop),
                "Blank Call": fmt_num(blank_call),
                "Call Back (Call Drop + Blank Call)": fmt_num(call_back),
                "Call Drop Not Done": fmt_num(call_drop_not_done),
                "Blank Call Not Done": fmt_num(blank_call_not_done),
                "Overall Call Not Done": fmt_num(overall_call_not_done),
                "Call Not Done %": fmt_pct(call_not_done_pct),
                "Agent Disconnected": fmt_num(agent_disconnected),
                "Agent Disconnected %": fmt_pct(agent_disconnected_pct),
                "Call Not Disposed": fmt_num(call_not_disposed),
                "Call Not Disposed %": fmt_pct(call_not_disposed_pct)
            })

        # 4. Map values back to metrics array (reordered: call metrics first, then manual metrics)
        call_metric_names = [
            "Total Calls Offered", "Agent Calls offered", "Calls Answered", "SL Calls",
            "WH Total calls offered", "WH Calls Answered", "Overall Abn", "Net Abandoned calls",
            "Short Call Abn", "Short Call %- Abn", "Gross Abn%", "Gross Abn%(WO Short Calls)",
            "Net Abn%", "Duration - AHT", "SL%", "AL%", "Total Wait Time", "Avg. Wait Time",
            "On Hold calls", "Hold Call%", "Avg Wait Time", "Avg Hold Time", "Answered - AHT",
            "Handling Time  >5mins", "Long Call %", "Queue level Abn",
            "Disposition ( Repeat CallS )", "Same Day Same Disposition - Repeat %",
            "Calls Offered (Inbound +Women Helpline)", "Calls Offered (Travel Update)",
            "Repeat calls", "Same Day Repeat %", "Call Drop", "Blank Call",
            "Call Back (Call Drop + Blank Call)", "Call Drop Not Done", "Blank Call Not Done",
            "Overall Call Not Done", "Call Not Done %",
            "Agent Disconnected", "Agent Disconnected %",
            "Call Not Disposed", "Call Not Disposed %"
        ]

        manual_metric_names = [
            "Gross Seats", "Gross Tickets", "Intr/Journey ( Overall )", "Defects", "Defects/Journey",
            "Present Agent HC", "Call/Agent", "Intr/Journey % ( Inbound + WH)", 
            "Intr/Journey %  ( Travel update )", "No. of Service Delay", "Delay Pax Impacted",
            "No. of Service Cancel", "Service Cancel Pax Impacted", "No. of Service Breakdown",
            "Break Down Pax Impacted", "Impacted %", "Total Pax Impacted", "Cancellations Impact %"
        ]

        metric_names = call_metric_names + manual_metric_names

        structured_data["metrics"] = []
        for name in metric_names:
            structured_data["metrics"].append({
                "name": name,
                "values": [calculated_columns[i].get(name, "") for i in range(len(structured_data["columns"]))]
            })

        return structured_data
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
def export_excel_view(parent_campaign: str = Query("Inbound"), start_date: str = Query(None), end_date: str = Query(None)):
    try:
        engine = get_tenant_db_engine(parent_campaign)
        df = pd.read_sql("SELECT * FROM call_records", engine)
        
        if df.empty:
            return StreamingResponse(io.BytesIO(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Empty.xlsx"})
            
        df = process_dataframe(df)
        
        if start_date:
            start_dt = pd.to_datetime(start_date, errors='coerce')
            if start_dt.tz: start_dt = start_dt.tz_localize(None)
            df = df[df['Call_Date_DT'] >= start_dt]
        if end_date:
            end_dt = pd.to_datetime(end_date, errors='coerce')
            if end_dt.tz: end_dt = end_dt.tz_localize(None)
            df = df[df['Call_Date_DT'] <= end_dt]
        else:
            yesterday = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
            df = df[df['Call_Date_DT'] <= yesterday]
            
        output = io.BytesIO()
        
        days = df['Call_Date_DT'].dt.date.unique()
        days.sort()
        
        metrics_list = []
        for d in days:
            df_day = df[df['Call_Date_DT'].dt.date == d]
            metrics = aggregate_metrics(df_day)
            metrics['Date'] = d.strftime("%d-%b-%Y")
            metrics_list.append(metrics)
            
        if metrics_list:
            df_export = pd.DataFrame(metrics_list)
            df_export = df_export.set_index('Date').T
            df_export.index.name = 'Metric'
            df_export.reset_index(inplace=True)
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, sheet_name='Daily Metrics', index=False)
                worksheet = writer.sheets['Daily Metrics']
                for i, col in enumerate(df_export.columns):
                    column_len = max(df_export[col].astype(str).map(len).max(), len(str(col))) + 2
                    from openpyxl.utils import get_column_letter
                    worksheet.column_dimensions[get_column_letter(i+1)].width = column_len
                    
        output.seek(0)
        
        file_name = f"Inbound Dashboard_{start_date} to {end_date}.xlsx" if start_date and end_date else "Inbound Dashboard.xlsx"
        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
