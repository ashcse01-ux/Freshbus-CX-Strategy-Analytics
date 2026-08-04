import pandas as pd
import sqlite3
import os
import glob
from datetime import datetime
import json

DB_PATH = 'metrics_helpdesk.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS helpdesk_metrics (
            date TEXT PRIMARY KEY,
            tickets_created INTEGER,
            ftr_tickets INTEGER,
            nftr_tickets INTEGER,
            tickets_closed INTEGER,
            tickets_pending INTEGER,
            inbound_calls_ans INTEGER,
            ticket_not_created_fd INTEGER,
            ftr_res_time_sec REAL,
            nftr_res_time_sec REAL,
            overall_res_time_sec REAL,
            freshdesk_adoption REAL
        )
    ''')
    # Table for complaint types
    c.execute('''
        CREATE TABLE IF NOT EXISTS complaint_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            complaint_type TEXT,
            count INTEGER,
            UNIQUE(date, complaint_type)
        )
    ''')
    conn.commit()
    return conn

def hms_to_seconds(t_str):
    if pd.isna(t_str):
        return None
    try:
        t_str = str(t_str).split('.')[0] # remove ms
        if ' ' in t_str:
            days, time_str = t_str.split(' ')
            if 'days' in days or 'day' in days:
                days = int(days.split(' ')[0])
            else:
                # might be a date 1900-01-01
                if '-' in days:
                    # just take the time part if it parsed as a weird date
                    pass
                else:
                    days = int(days)
        else:
            time_str = t_str
            days = 0
            
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return days * 86400 + h * 3600 + m * 60 + s
        return None
    except Exception as e:
        return None

def process_freshdesk_dump(df, conn):
    if 'Created time' not in df.columns:
        return
        
    df['date'] = pd.to_datetime(df['Created time'], errors='coerce').dt.strftime('%Y-%m-%d')
    df = df.dropna(subset=['date'])
    
    # Process each day
    grouped = df.groupby('date')
    
    for date, group in grouped:
        tickets_created = len(group)
        
        ftr_count = len(group[group['Resolution Type'] == 'FTR - First-time resolution'])
        nftr_count = len(group[~group['Resolution Type'].isin(['FTR - First-time resolution']) & group['Resolution Type'].notna()])
        
        tickets_closed = len(group[group['Status'].isin(['Closed', 'Resolved'])])
        tickets_pending = tickets_created - tickets_closed
        
        # Res time processing
        group['res_sec'] = group['Resolution time (in hrs)'].apply(hms_to_seconds)
        
        ftr_res_time_sec = group[group['Resolution Type'] == 'FTR - First-time resolution']['res_sec'].mean()
        nftr_res_time_sec = group[~group['Resolution Type'].isin(['FTR - First-time resolution']) & group['Resolution Type'].notna()]['res_sec'].mean()
        overall_res_time_sec = group['res_sec'].mean()
        
        c = conn.cursor()
        # UPSERT logic
        c.execute('''
            INSERT INTO helpdesk_metrics (date, tickets_created, ftr_tickets, nftr_tickets, tickets_closed, tickets_pending, ftr_res_time_sec, nftr_res_time_sec, overall_res_time_sec)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                tickets_created=excluded.tickets_created,
                ftr_tickets=excluded.ftr_tickets,
                nftr_tickets=excluded.nftr_tickets,
                tickets_closed=excluded.tickets_closed,
                tickets_pending=excluded.tickets_pending,
                ftr_res_time_sec=excluded.ftr_res_time_sec,
                nftr_res_time_sec=excluded.nftr_res_time_sec,
                overall_res_time_sec=excluded.overall_res_time_sec
        ''', (date, tickets_created, ftr_count, nftr_count, tickets_closed, tickets_pending, ftr_res_time_sec, nftr_res_time_sec, overall_res_time_sec))
        
        # Complaint tracker
        complaints = group['Complaint Type'].value_counts()
        for ctype, count in complaints.items():
            if pd.notna(ctype):
                c.execute('''
                    INSERT INTO complaint_metrics (date, complaint_type, count)
                    VALUES (?, ?, ?)
                    ON CONFLICT(date, complaint_type) DO UPDATE SET count=excluded.count
                ''', (date, str(ctype), int(count)))
                
    conn.commit()

def process_inbound_dump(df, conn):
    if 'Call Date' not in df.columns:
        return
        
    df['date'] = pd.to_datetime(df['Call Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df = df.dropna(subset=['date'])
    
    # Only inbound answered
    df_ans = df[(df['Call Type'] == 'Inbound') & (df['Status'] == 'Answered')]
    
    grouped = df_ans.groupby('date')
    
    for date, group in grouped:
        ans_calls = len(group)
        
        # For this script we simulate the MIS logic of matching tickets. 
        # In actual practice, it's comparing 'Caller No' to FD 'Customer Mobile'.
        # But wait, looking at the MIS sheet, "Ticket Not Created FD" is computed manually.
        # We can implement a simple heuristic: 5% of answered calls, or we can actually match them if we load both into memory.
        # Let's write the real matching logic!
        pass

if __name__ == '__main__':
    conn = init_db()
    
    # 1. Process Freshdesk Excel
    fd_excel = r'../Freshdesk Automation - Help Desk/Dump/FreshDesk Automation - Helpdesk , Compliants Tracker , Helpdesk Adoption - Dump - 1st jan 2026 to 20th july 2026.xlsx'
    if os.path.exists(fd_excel):
        print("Processing Freshdesk Excel...")
        df_fd_ex = pd.read_excel(fd_excel)
        process_freshdesk_dump(df_fd_ex, conn)
        
    # 2. Process Freshdesk CSV
    fd_csv = r'../Freshdesk Automation - Help Desk/Dump/FreshDesk Automation - Helpdesk , Compliants Tracker , Helpdesk Adoption - Dump - 21st july 2026 to 29th july 2026.csv'
    if os.path.exists(fd_csv):
        print("Processing Freshdesk CSV...")
        df_fd_csv = pd.read_csv(fd_csv)
        process_freshdesk_dump(df_fd_csv, conn)
        
    # 3. Process Inbound Calls
    ib_excel = r'../Freshdesk Automation - Help Desk/Sheets/Inbound Call VS Fresh Desk - it is Helpdesk adoption.xlsx'
    if os.path.exists(ib_excel):
        print("Processing Inbound Calls...")
        df_ib = pd.read_excel(ib_excel, sheet_name='Inbound Call ')
        
        df_ib['date'] = pd.to_datetime(df_ib['Call Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        df_ib = df_ib.dropna(subset=['date'])
        df_ans = df_ib[(df_ib['Call Type'] == 'Inbound') & (df_ib['Status'] == 'Answered')]
        
        # To match precisely, let's load the FD dump into memory
        if os.path.exists(fd_excel):
            df_fd_all = pd.concat([pd.read_excel(fd_excel), pd.read_csv(fd_csv)])
        else:
            df_fd_all = pd.read_csv(fd_csv)
            
        df_fd_all['date'] = pd.to_datetime(df_fd_all['Created time'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # We need to map caller number. In inbound: `Caller No`. In FD: `Customer Mobile` or `PNR` (sometimes phone is there)
        # Often `Caller No` is 91xxxxxxxxxx. `Customer Mobile` might be xxxxxxxxxx.
        def norm_phone(p):
            p = str(p).replace('.0', '').strip()
            if p.startswith('91') and len(p) == 12:
                return p[2:]
            return p
            
        df_ans['norm_caller'] = df_ans['Caller No'].apply(norm_phone)
        df_fd_all['norm_cust'] = df_fd_all['Customer Mobile'].apply(norm_phone)
        
        grouped = df_ans.groupby('date')
        for date, group in grouped:
            ans_calls = len(group)
            
            # Find FD tickets for this date
            fd_today = df_fd_all[df_fd_all['date'] == date]
            fd_phones = set(fd_today['norm_cust'].tolist())
            
            # How many inbound calls didn't result in a ticket?
            not_created = 0
            for phone in group['norm_caller']:
                if phone not in fd_phones:
                    not_created += 1
                    
            adoption = (ans_calls - not_created) / ans_calls if ans_calls > 0 else 0
            
            c = conn.cursor()
            c.execute('''
                UPDATE helpdesk_metrics
                SET inbound_calls_ans = ?,
                    ticket_not_created_fd = ?,
                    freshdesk_adoption = ?
                WHERE date = ?
            ''', (ans_calls, not_created, adoption, date))
            
            if c.rowcount == 0:
                # Insert if missing
                c.execute('''
                    INSERT INTO helpdesk_metrics (date, inbound_calls_ans, ticket_not_created_fd, freshdesk_adoption)
                    VALUES (?, ?, ?, ?)
                ''', (date, ans_calls, not_created, adoption))
        
        conn.commit()

    print("Done!")
