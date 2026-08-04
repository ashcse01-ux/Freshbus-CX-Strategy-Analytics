import json

# Full list of metrics provided by the user (50 existing + new metrics with updated ordering and names)
metric_names = [
    "Gross Seats", "Gross Tickets", "Intr/Journey ( Overall )", "Defects", "Defects/Journey",
    "Total Calls Offered", "Agent Calls offered", "Calls Answered", "SL Calls",
    "WH Total calls offered", "WH Calls Answered", "Overall Abn", "Net Abandoned calls",
    "Short Call Abn", "Short Call %- Abn", "Gross Abn%", "Gross Abn%(WO Short Calls)",
    "Net Abn%", "Duration - AHT", "SL%", "AL%", "Total Wait Time", "Avg. Wait Time",
    "On Hold calls", "Hold Call%", "Avg Wait Time", "Avg Hold Time", "Answered - AHT",
    "Present Agent HC", "Handling Time  >5mins", "Long Call %", "Call/Agent",
    "Queue level Abn", "Disposition ( Repeat CallS )", "Same Day Same Disposition - Repeat %",
    "Calls Offered (Inbound +Women Helpline)", "Calls Offered (Travel Update)",
    "Intr/Journey % ( Inbound + WH)", "Intr/Journey %  ( Travel update )", "Repeat calls",
    "Same Day Repeat %", "No. of Service Delay", "Delay Pax Impacted",
    "No. of Service Cancel", "Service Cancel Pax Impacted", "No. of Service Breakdown",
    "Break Down Pax Impacted", "Impacted %", "Total Pax Impacted", "Cancellations Impact %",
    "Call Drop", "Blank Call", "Call Back (Call Drop + Blank Call)",
    "Call Drop Not Done", "Blank Call Not Done", "Overall Call Not Done", "Call Not Done %"
]

with open('extracted_data.tsv', 'r', encoding='utf-8') as f:
    lines = f.readlines()

table_lines = [line.strip('\n') for line in lines if '\t' in line]

if len(table_lines) < 2:
    print("No table data found!")
    exit(1)

# First line is headers, second line is dates
headers = table_lines[0].split('\t')
raw_dates = table_lines[1].split('\t')

from datetime import datetime, timedelta

dates = []
for d in raw_dates:
    d = d.strip()
    if d:
        try:
            dt = datetime.strptime(d, "%m/%d/%Y")
            dt -= timedelta(days=7)
            # format as m/d/yyyy without leading zeros
            dates.append(f"{dt.month}/{dt.day}/{dt.year}")
        except:
            dates.append(d)
    else:
        dates.append("")

metrics = []
for i, name in enumerate(metric_names):
    if i + 2 < len(table_lines):
        # We have data for this row
        parts = table_lines[i + 2].split('\t')
        values = [p.strip() for p in parts]
    else:
        # We don't have data for this row (e.g. new metrics), fill with empty strings
        values = [''] * len(headers)
    
    if name not in ["Defects", "Defects/Journey"]:
        metrics.append({
            "name": name,
            "values": values
        })

data = {
    "columns": [h.strip() for h in headers],
    "dates": [d.strip() for d in dates],
    "metrics": metrics
}

with open('backend/static_excel_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print(f"Generated static_excel_data.json with {len(headers)} columns and {len(metrics)} metrics!")
