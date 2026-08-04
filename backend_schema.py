import sqlite3
conn = sqlite3.connect('backend/metrics_helpdesk.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
for row in cursor.fetchall():
    print(row[0])
