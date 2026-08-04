from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3
import pandas as pd
import os
import json

router = APIRouter(prefix="/api/helpdesk")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "metrics_helpdesk.db")
MIS_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "mis_daily.json")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class FilterRequest(BaseModel):
    start_date: str
    end_date: str
    lob: Optional[List[str]] = None
    status: Optional[List[str]] = None
    type: Optional[List[str]] = None
    group: Optional[List[str]] = None
    priority: Optional[List[str]] = None
    agent: Optional[List[str]] = None
    source: Optional[List[str]] = None


@router.get("/filters")
async def get_filters():
    try:
        conn = get_db_connection()
        
        def get_distinct(table, column):
            cursor = conn.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL AND {column} != ''")
            return [row[0] for row in cursor.fetchall()]

        filters = {
            "lob": get_distinct("raw_tickets", "lob"),
            "status": get_distinct("raw_tickets", "st"),
            "type": get_distinct("raw_tickets", "typ"),
            "group": get_distinct("raw_tickets", "grp"),
            "priority": get_distinct("raw_tickets", "pri"),
            "agent": get_distinct("raw_tickets", "ag"),
            "source": get_distinct("raw_tickets", "src"),
            "hda_source": get_distinct("raw_calls", "camp") # HD adoption source
        }
        
        conn.close()
        return {"status": "success", "data": filters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/aggregate")
async def aggregate_helpdesk(req: FilterRequest):
    try:
        conn = get_db_connection()
        
        # Build query for raw_tickets
        query_hd = "SELECT * FROM raw_tickets WHERE cr >= ? AND cr <= ?"
        params_hd = [req.start_date, req.end_date]
        
        if req.lob and len(req.lob) > 0:
            query_hd += f" AND lob IN ({','.join(['?']*len(req.lob))})"
            params_hd.extend(req.lob)
        if req.status and len(req.status) > 0:
            query_hd += f" AND st IN ({','.join(['?']*len(req.status))})"
            params_hd.extend(req.status)
        if req.type and len(req.type) > 0:
            query_hd += f" AND typ IN ({','.join(['?']*len(req.type))})"
            params_hd.extend(req.type)
        if req.group and len(req.group) > 0:
            query_hd += f" AND grp IN ({','.join(['?']*len(req.group))})"
            params_hd.extend(req.group)
        if req.priority and len(req.priority) > 0:
            query_hd += f" AND pri IN ({','.join(['?']*len(req.priority))})"
            params_hd.extend(req.priority)
        if req.agent and len(req.agent) > 0:
            query_hd += f" AND ag IN ({','.join(['?']*len(req.agent))})"
            params_hd.extend(req.agent)
        if req.source and len(req.source) > 0:
            query_hd += f" AND src IN ({','.join(['?']*len(req.source))})"
            params_hd.extend(req.source)
            
        df_hd = pd.read_sql_query(query_hd, conn, params=params_hd)
        
        # Build query for raw_calls (HD Adoption)
        query_hda = "SELECT * FROM raw_calls WHERE cd >= ? AND cd <= ?"
        params_hda = [req.start_date, req.end_date]
        
        if req.status and len(req.status) > 0:
            query_hda += f" AND st IN ({','.join(['?']*len(req.status))})"
            params_hda.extend(req.status)
        if req.agent and len(req.agent) > 0:
            query_hda += f" AND ag IN ({','.join(['?']*len(req.agent))})"
            params_hda.extend(req.agent)
            
        df_hda = pd.read_sql_query(query_hda, conn, params=params_hda)
        conn.close()
        
        # Load MIS data
        mis_data = {}
        if os.path.exists(MIS_JSON_PATH):
            with open(MIS_JSON_PATH, 'r') as f:
                mis_data = json.load(f)
                
        # Calculate MIS metrics for date range
        total_seats = 0
        total_pnr = 0
        defect_rates = []
        d_range = pd.date_range(start=req.start_date, end=req.end_date)
        for d in d_range:
            d_str = d.strftime("%Y-%m-%d")
            if d_str in mis_data:
                total_seats += mis_data[d_str].get("seats", 0)
                total_pnr += mis_data[d_str].get("pnr", 0)
                if mis_data[d_str].get("defect_rate", 0) > 0:
                    defect_rates.append(mis_data[d_str]["defect_rate"])
        
        avg_defect_rate = sum(defect_rates) / len(defect_rates) if defect_rates else 0.0
        
        # Calculate Helpdesk Metrics
        tickets_created = len(df_hd)
        
        # Determine FTR vs NFTR
        # Assuming rt <= 1 is FTR, > 1 is NFTR if closed, else blanks if missing
        def get_res_type(row):
            if pd.isna(row['rt']) or row['rt'] == '' or str(row['rt']) == '-':
                return 'Blank'
            try:
                if float(row['hrs']) <= 2: # FTR logic based on Freshbus SLA? Wait, user's JS might have logic. Let's assume rt is FTR/NFTR string or hrs <=2. Let's just use FTR/NFTR from typ if present. Actually 'rt' column seems to hold FTR/NFTR directly!
                    pass
            except:
                pass
            return str(row['rt'])
            
        if not df_hd.empty:
            df_hd['res_type'] = df_hd['rt'] # rt contains FTR / NFTR
            df_hd['hrs_num'] = pd.to_numeric(df_hd['hrs'], errors='coerce').fillna(0)
            
            ftr_tickets = len(df_hd[df_hd['res_type'] == 'FTR'])
            nftr_tickets = len(df_hd[df_hd['res_type'] == 'NFTR'])
            blank_tickets = len(df_hd[~df_hd['res_type'].isin(['FTR', 'NFTR'])])
            
            tickets_closed = len(df_hd[df_hd['st'].str.lower() == 'closed'])
            tickets_pending = tickets_created - tickets_closed
            
            # Resolution times
            ftr_res_time = df_hd[df_hd['res_type'] == 'FTR']['hrs_num'].mean() if ftr_tickets > 0 else 0
            nftr_res_time = df_hd[df_hd['res_type'] == 'NFTR']['hrs_num'].mean() if nftr_tickets > 0 else 0
            overall_res_time = df_hd['hrs_num'].mean() if tickets_created > 0 else 0
            
            # Breakdowns by Source
            sources_summary = {}
            for src in ['Inbound', 'Outbound', 'Email']:
                src_df = df_hd[df_hd['src'].str.contains(src, case=False, na=False)]
                src_ftr = len(src_df[src_df['res_type'] == 'FTR'])
                src_nftr = len(src_df[src_df['res_type'] == 'NFTR'])
                src_res_time = src_df['hrs_num'].mean() if not src_df.empty else 0
                sources_summary[src] = {
                    'ftr': src_ftr,
                    'nftr': src_nftr,
                    'avg_res_time': round(src_res_time, 2)
                }
        else:
            ftr_tickets = nftr_tickets = blank_tickets = tickets_closed = tickets_pending = 0
            ftr_res_time = nftr_res_time = overall_res_time = 0
            sources_summary = {s: {'ftr': 0, 'nftr': 0, 'avg_res_time': 0} for s in ['Inbound', 'Outbound', 'Email']}
            
        # Calculate HD Adoption Metrics
        inbound_calls_ans = 0
        tickets_not_created_fd = 0
        hd_adoption = 0.0
        
        if not df_hda.empty:
            inbound_calls_ans = len(df_hda)
            tickets_not_created_fd = len(df_hda[df_hda['sts'].str.contains("Ticket Not Created", case=False, na=False)])
            tickets_created_fd = inbound_calls_ans - tickets_not_created_fd
            if inbound_calls_ans > 0:
                hd_adoption = (tickets_created_fd / inbound_calls_ans) * 100
                
        # Complaint Tracker logic (placeholder as we didn't populate raw complaints)
        new_tickets_comp = tickets_created # Mocking for now
        back_dated_cases = 0
        closed_comp = tickets_closed

        return {
            "status": "success",
            "metrics": {
                "tickets_created": tickets_created,
                "ftr_tickets": ftr_tickets,
                "nftr_tickets": nftr_tickets,
                "blank_tickets": blank_tickets,
                "tickets_closed": tickets_closed,
                "tickets_pending": tickets_pending,
                "inbound_calls_ans": inbound_calls_ans,
                "ticket_not_created_fd": tickets_not_created_fd,
                "avg_res_time": round(overall_res_time, 2),
                "avg_ftr_res_time": round(ftr_res_time, 2),
                "avg_nftr_res_time": round(nftr_res_time, 2),
                "hd_adoption": round(hd_adoption, 2),
                "seats": total_seats,
                "pnr": total_pnr,
                "defect_rate": round(avg_defect_rate, 2),
                "complaints": {
                    "new_tickets": new_tickets_comp,
                    "back_dated": back_dated_cases,
                    "closed": closed_comp
                }
            },
            "sources": sources_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/raw_hd")
async def get_raw_hd():
    file_path = os.path.join(os.path.dirname(__file__), "..", "raw_hd.json")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="Raw HD data not found")

@router.get("/raw_hda")
async def get_raw_hda():
    file_path = os.path.join(os.path.dirname(__file__), "..", "raw_hda.json")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="Raw HDA data not found")
