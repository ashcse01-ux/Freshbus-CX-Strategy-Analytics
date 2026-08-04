import pandas as pd
import os

file_path = "d:\\Freshbus-CX-Strategy-Analytics\\Redbus Analytics Dashboard Preloaded Data Dump\\Redbus Dashboard for Automation - 1st June to 14th July.xlsx"

try:
    xls = pd.ExcelFile(file_path)
    print("Sheets available:", xls.sheet_names)
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
        print(f"\n--- Sheet: {sheet} ---")
        print("Columns:", list(df.columns))
        print("Head (first 2 rows):")
        print(df.head(2).to_dict(orient="records"))
except Exception as e:
    print("Error:", e)
