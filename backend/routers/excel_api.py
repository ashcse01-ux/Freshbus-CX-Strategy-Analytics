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
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static_excel_data.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"columns": [], "dates": [], "metrics": []}
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
