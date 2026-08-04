import sqlite3
import pandas as pd
import glob
import os

# Get path relative to the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'metrics_inbound.db')
dump_dir = os.path.join(os.path.dirname(script_dir), 'Inbound Dashboard Dump')

print("--- Database (metrics_inbound.db) Call Record Ratings ---")
try:
    conn = sqlite3.connect(db_path)
    df_db = pd.read_sql_query("SELECT Ratings FROM call_records", conn)
    print("Total rows in DB:", len(df_db))
    # Replace NaN or empty strings with 'Empty/None' for clear presentation
    df_db['Ratings'] = df_db['Ratings'].fillna('Empty/None').replace('', 'Empty/None')
    print(df_db['Ratings'].value_counts())
except Exception as e:
    print("Error querying database:", e)

print("\n--- Excel Files (Inbound Dashboard Dump/*.xls) Ratings ---")
xls_files = glob.glob(os.path.join(dump_dir, '*.xls'))
if xls_files:
    dfs = []
    for f in xls_files:
        try:
            df = pd.read_excel(f)
            if 'Ratings' in df.columns:
                dfs.append(df['Ratings'])
        except Exception as e:
            print(f"Error reading {f}: {e}")
    if dfs:
        df_excel = pd.concat(dfs)
        print("Total rows in Excel files:", len(df_excel))
        df_excel = df_excel.fillna('Empty/None').replace('', 'Empty/None')
        print(df_excel.value_counts())
    else:
        print("No Ratings column found in any Excel file.")
else:
    print("No Excel files found in path:", dump_dir)
