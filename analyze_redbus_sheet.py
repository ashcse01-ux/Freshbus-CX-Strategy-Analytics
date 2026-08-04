import pandas as pd

url = "https://docs.google.com/spreadsheets/d/1W-pIPAfKhNuQvhp2o52rPlenQXo3q92379t4YxGuiX8/export?format=xlsx"
print("Downloading and analyzing sheets...")
try:
    xls = pd.ExcelFile(url)
    print("Sheets available:", xls.sheet_names)
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        print(f"\n--- Sheet: {sheet} ---")
        print("Columns:", list(df.columns))
        print("Shape:", df.shape)
        print("Head (first 3 rows):")
        print(df.head(3))
except Exception as e:
    print("Error:", e)
