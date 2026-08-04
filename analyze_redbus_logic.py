import pandas as pd
import numpy as np

file_path = r"d:\Freshbus-CX-Strategy-Analytics\Redbus Analytics Dashboard Preloaded Data Dump\Redbus Dashboard for Automation - 1st June to 14th July.xlsx"

try:
    print("Loading data...")
    call_sheet = pd.read_excel(file_path, sheet_name="call sheet")
    rating_dump = pd.read_excel(file_path, sheet_name="rating Dump")
    travel_data = pd.read_excel(file_path, sheet_name="Travel Data")
    
    print("Preprocessing data...")
    # Normalize PNRs to string
    call_sheet['PNR'] = call_sheet['PNR'].astype(str).str.strip().str.upper()
    rating_dump['PNR'] = rating_dump['PNR'].astype(str).str.strip().str.upper()
    travel_data['Ticket No'] = travel_data['Ticket No'].astype(str).str.strip().str.upper()
    
    # 1. Overall Redbus Data
    # Meta Redbus Data = Travel Count (from Travel Data)
    meta_redbus_data = travel_data.shape[0]
    
    # Meta Response Rate % = Travel Count / Overall Redbus Data  (Wait, user logic says "Travel Count ÷ Overall Redbus Data". It's probably Rating Count / Travel Count overall)
    # Let's count total ratings in rating dump
    total_ratings = rating_dump.shape[0]
    
    # Data Assigned = Count of records from the Call Sheet
    data_assigned = call_sheet.shape[0]
    
    # Let's implement Organic / InOrganic Classification
    # Compare PNR between Rating Dump and Call Sheet
    merged = pd.merge(rating_dump, call_sheet[['PNR', 'Call Status', 'Tl Names']], on='PNR', how='left')
    
    # Organic: PNR in both and Call Status == "Not Connected", OR PNR in Rating Dump but NOT in Call Sheet
    organic_mask = (merged['Call Status'].isna()) | (merged['Call Status'].str.lower().str.strip() == 'not connected')
    inorganic_mask = (merged['Call Status'].notna()) & (merged['Call Status'].str.lower().str.strip() == 'connected')
    
    organic_df = merged[organic_mask]
    inorganic_df = merged[inorganic_mask]
    
    organic_count = organic_df.shape[0]
    organic_avg = organic_df['Rating'].mean() if not organic_df.empty else 0
    
    inorganic_count = inorganic_df.shape[0]
    inorganic_avg = inorganic_df['Rating'].mean() if not inorganic_df.empty else 0
    
    # Overall Redbus Data = Data Assigned + Organic Data. Wait, user doc says "Data Assigned + Organic Data".
    # Let's calculate exactly as they said.
    overall_redbus_data = data_assigned + organic_count
    
    print("--- KPIs Computed ---")
    print(f"Meta Redbus Data (Travel Count): {meta_redbus_data}")
    print(f"Data Assigned (Call Sheet count): {data_assigned}")
    print(f"Organic Ratings Count: {organic_count}")
    print(f"Organic Average Rating: {organic_avg:.2f}")
    print(f"InOrganic Ratings Count: {inorganic_count}")
    print(f"InOrganic Average Rating: {inorganic_avg:.2f}")
    print(f"Overall Redbus Data (Assigned + Organic): {overall_redbus_data}")
    print(f"Meta Response Rate % (Total Ratings / Travel Count): {total_ratings / meta_redbus_data * 100:.2f}%")
    
except Exception as e:
    print("Exception during analysis:", e)
