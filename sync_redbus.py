import pandas as pd
import json
import os

file_path = r"d:\Freshbus-CX-Strategy-Analytics\Redbus Analytics Dashboard Preloaded Data Dump\Redbus Dashboard for Automation - 1st June to 14th July.xlsx"

try:
    print("Loading data with limited columns to save memory...")
    call_sheet = pd.read_excel(file_path, sheet_name="call sheet", usecols=["PNR", "Call Status", "Tl Names"])
    rating_dump = pd.read_excel(file_path, sheet_name="rating Dump", usecols=["PNR", "Rating", "Route"])
    travel_data = pd.read_excel(file_path, sheet_name="Travel Data", usecols=["Ticket No", "Route"])
    
    print("Preprocessing data...")
    call_sheet['PNR'] = call_sheet['PNR'].astype(str).str.strip().str.upper()
    rating_dump['PNR'] = rating_dump['PNR'].astype(str).str.strip().str.upper()
    travel_data['Ticket No'] = travel_data['Ticket No'].astype(str).str.strip().str.upper()
    
    # KPIs
    meta_redbus_data = travel_data.shape[0]
    total_ratings = rating_dump.shape[0]
    data_assigned = call_sheet.shape[0]
    
    # Merging for Organic / Inorganic
    merged = pd.merge(rating_dump, call_sheet[['PNR', 'Call Status', 'Tl Names']], on='PNR', how='left')
    
    # Fix Call Status strings
    merged['Call Status'] = merged['Call Status'].fillna('').astype(str).str.lower().str.strip()
    
    organic_mask = (merged['Call Status'] == '') | (merged['Call Status'] == 'nan') | (merged['Call Status'] == 'not connected')
    inorganic_mask = merged['Call Status'] == 'connected'
    
    organic_df = merged[organic_mask]
    inorganic_df = merged[inorganic_mask]
    
    organic_count = organic_df.shape[0]
    organic_avg = organic_df['Rating'].mean() if not organic_df.empty else 0
    inorganic_count = inorganic_df.shape[0]
    inorganic_avg = inorganic_df['Rating'].mean() if not inorganic_df.empty else 0
    
    overall_redbus_data = data_assigned + organic_count
    
    # Calculate response rates
    meta_response_rate = (total_ratings / meta_redbus_data * 100) if meta_redbus_data else 0
    org_inorg_total = organic_count + inorganic_count
    org_inorg_response_rate = (org_inorg_total / meta_redbus_data * 100) if meta_redbus_data else 0
    overall_avg = merged['Rating'].mean() if not merged.empty else 0
    inorganic_response_rate = (inorganic_count / data_assigned * 100) if data_assigned else 0
    
    # Route-wise calculations
    # Travel count per route
    route_travel = travel_data.groupby('Route').size().reset_index(name='travel_count')
    # Rating count per route
    route_rating = rating_dump.groupby('Route').agg(rating_count=('PNR', 'count'), avg_rating=('Rating', 'mean')).reset_index()
    
    routes_merged = pd.merge(route_travel, route_rating, on='Route', how='outer').fillna(0)
    routes_merged['response_rate'] = (routes_merged['rating_count'] / routes_merged['travel_count'] * 100).fillna(0)
    
    routes_list = []
    for _, r in routes_merged.iterrows():
        if str(r['Route']) != 'nan':
            routes_list.append({
                "route": str(r['Route']).strip(),
                "travel_count": int(r['travel_count']),
                "rating_count": int(r['rating_count']),
                "avg_rating": round(float(r['avg_rating']), 2),
                "response_rate": f"{r['response_rate']:.1f}%"
            })
            
    # TL-wise calculations (from Inorganic ratings usually, or all merged?)
    # The word doc logic doesn't specify, but TL Name comes from Call Sheet. 
    # So we group by Tl Names on the merged dataset
    tl_rating = merged[merged['Tl Names'].notna()].groupby('Tl Names').agg(count=('PNR', 'count'), avg=('Rating', 'mean')).reset_index()
    # To get response rate per TL, we need the total assigned to that TL
    tl_assigned = call_sheet[call_sheet['Tl Names'].notna()].groupby('Tl Names').size().reset_index(name='assigned_count')
    
    tl_merged = pd.merge(tl_rating, tl_assigned, on='Tl Names', how='outer').fillna(0)
    tl_merged['response_rate'] = (tl_merged['count'] / tl_merged['assigned_count'] * 100).fillna(0)
    
    tl_list = []
    for _, t in tl_merged.iterrows():
        tl_name = str(t['Tl Names']).strip()
        if tl_name != 'nan' and tl_name != '':
            tl_list.append({
                "tl": tl_name,
                "count": int(t['count']),
                "avg": round(float(t['avg']), 2),
                "response_rate": f"{t['response_rate']:.1f}%"
            })
    
    final_data = {
        "cards": {
            "Meta Redbus Data": int(meta_redbus_data),
            "Meta Response Rate %": f"{meta_response_rate:.2f}%",
            "Overall Redbus Data": int(overall_redbus_data),
            "Organic": int(organic_count),
            "Organic (Average)": round(float(organic_avg), 2),
            "Organic + Not Connected": int(organic_count), # Simplified
            "Organic + InOrganic": int(org_inorg_total),
            "Average (Overall Redbus)": round(float(overall_avg), 2),
            "Organic + InOrganic Response Rate %": f"{org_inorg_response_rate:.2f}%",
            "Data Assigned": int(data_assigned),
            "InOrganic Ratings": int(inorganic_count),
            "Difference (Organic / Inorganic)": str(organic_count - inorganic_count),
            "InOrganic Average": round(float(inorganic_avg), 2),
            "InOrganic Response Rate %": f"{inorganic_response_rate:.2f}%",
            "Data Loss MMT": 0, # Placeholders for MMT / IBIBO
            "Data Loss IBIBO": 0
        },
        "routes": routes_list,
        "tls": tl_list
    }
    
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    out_file = os.path.join(backend_dir, 'redbus_data.json')
    with open(out_file, 'w') as f:
        json.dump(final_data, f, indent=4)
        
    print(f"Data successfully synced to {out_file}")

except Exception as e:
    print("Exception during sync:", e)
