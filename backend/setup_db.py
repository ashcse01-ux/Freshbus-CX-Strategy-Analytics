import sqlite3
import json
import os

db_path = 'backend/metrics_helpdesk.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table for MIS data
cursor.execute('''
CREATE TABLE IF NOT EXISTS mis_daily_metrics (
    date TEXT PRIMARY KEY,
    seats INTEGER,
    pnr INTEGER,
    defect_rate REAL
)
''')

# Create table for raw tickets (HD)
cursor.execute('''
CREATE TABLE IF NOT EXISTS raw_tickets (
    id TEXT PRIMARY KEY,
    date TEXT,
    source TEXT,
    lob TEXT,
    status TEXT,
    type TEXT,
    group_name TEXT,
    priority TEXT,
    agent TEXT,
    ftr INTEGER,
    nftr INTEGER,
    is_blank INTEGER,
    is_closed INTEGER,
    is_pending INTEGER,
    res_time_sec REAL
)
''')

# Create table for raw calls (HDA)
cursor.execute('''
CREATE TABLE IF NOT EXISTS raw_calls (
    id TEXT PRIMARY KEY,
    date TEXT,
    source TEXT,
    agent TEXT,
    status TEXT,
    is_ans INTEGER,
    not_created_fd INTEGER
)
''')

# Load MIS data
with open('backend/mis_daily.json', 'r') as f:
    mis_data = json.load(f)
    for date, data in mis_data.items():
        cursor.execute('''
            INSERT OR REPLACE INTO mis_daily_metrics (date, seats, pnr, defect_rate)
            VALUES (?, ?, ?, ?)
        ''', (date, data['seats'], data['pnr'], data['defect_rate']))

# Load raw tickets
with open('backend/raw_hd.json', 'r', encoding='utf-8') as f:
    raw_hd = json.load(f)
    for t in raw_hd:
        date_str = t.get('created_at', '')[:10]
        cursor.execute('''
            INSERT OR REPLACE INTO raw_tickets (
                id, date, source, lob, status, type, group_name, priority, agent,
                ftr, nftr, is_blank, is_closed, is_pending, res_time_sec
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(t.get('id', '')), date_str, str(t.get('source', '')), str(t.get('lob', '')), 
            str(t.get('status', '')), str(t.get('type', '')), str(t.get('group', '')), 
            str(t.get('priority', '')), str(t.get('agent', '')),
            1 if t.get('ftr') else 0, 1 if t.get('nftr') else 0,
            1 if not t.get('ftr') and not t.get('nftr') else 0,
            1 if str(t.get('status', '')).lower() in ['closed', 'resolved'] else 0,
            1 if str(t.get('status', '')).lower() in ['open', 'pending'] else 0,
            float(t.get('res_time_sec', 0))
        ))

# Load raw calls
with open('backend/raw_hda.json', 'r', encoding='utf-8') as f:
    raw_hda = json.load(f)
    for c in raw_hda:
        date_str = c.get('date', '')[:10]
        cursor.execute('''
            INSERT OR REPLACE INTO raw_calls (
                id, date, source, agent, status, is_ans, not_created_fd
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(c.get('id', '')), date_str, str(c.get('source', '')), str(c.get('agent', '')),
            str(c.get('status', '')),
            1 if str(c.get('status', '')).lower() == 'answered' else 0,
            1 if c.get('not_created_fd') else 0
        ))

conn.commit()
conn.close()
print("Database setup complete.")
