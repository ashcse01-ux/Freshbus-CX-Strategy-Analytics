import sqlite3
import pandas as pd
import os

db_path = "metrics_inbound.db"
output_path = r"C:\Users\Ayush Jain\.gemini\antigravity-ide\brain\dd6944d7-afef-402d-9095-8be79a3b106d\scratch\calls_19th_july.csv"

# Make sure scratch directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

conn = sqlite3.connect(db_path)
query = "SELECT * FROM call_records WHERE Call_Date LIKE '%19-07-%'"
df = pd.read_sql_query(query, conn)
conn.close()

# The API router does some deduplication and logic, let's just dump the raw DB rows first
# So the user can see what's physically in the database.
df.to_csv(output_path, index=False)
print(f"Dumped {len(df)} rows to {output_path}")
