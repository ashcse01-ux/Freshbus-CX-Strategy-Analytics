import sqlite3
import json

conn = sqlite3.connect('backend/metrics_helpdesk.db')
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS mis_daily")
cursor.execute('''
CREATE TABLE mis_daily (
    date TEXT PRIMARY KEY,
    seats INTEGER,
    pnr INTEGER,
    defect_rate REAL
)
''')

with open('backend/mis_daily.json', 'r', encoding='utf-8') as f:
    mis_data = json.load(f)

for date_str, data in mis_data.items():
    cursor.execute('''
    INSERT OR REPLACE INTO mis_daily (date, seats, pnr, defect_rate)
    VALUES (?, ?, ?, ?)
    ''', (date_str, data['seats'], data['pnr'], data['defect_rate']))

conn.commit()
conn.close()
print("Done inserting MIS data into DB.")
