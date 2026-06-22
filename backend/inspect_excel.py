import pandas as pd
import json

df = pd.read_excel('Inbound Metric Data_1st April 2025 to 18th June 2026.xlsx', sheet_name=0)
# Print the first column and some of the data to see the row structure
print(df.iloc[:, 0].tolist())
