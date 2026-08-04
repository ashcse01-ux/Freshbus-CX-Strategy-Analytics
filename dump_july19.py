import sqlite3
import pandas as pd
import os

# Connect to the inbound database in backend
db_path = os.path.join('backend', 'metrics_inbound.db')
conn = sqlite3.connect(db_path)

# Query data for July 19th 2026 with correct format DD-MM-YYYY
query = """
SELECT * FROM call_records
WHERE Call_Date = '19-07-2026'
"""

df = pd.read_sql_query(query, conn)
print(f"Total records found for July 19th, 2026: {len(df)}")

# Dump to CSV
output_path = 'july_19_2026_api_dump.csv'
df.to_csv(output_path, index=False)
print(f"Data exported to {output_path}")

conn.close()
