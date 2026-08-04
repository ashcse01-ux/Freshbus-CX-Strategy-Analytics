import json
from datetime import datetime

def is_date(string):
    try:
        datetime.strptime(string, "%m/%d/%Y")
        return True
    except ValueError:
        return False

with open('backend/mis_raw.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

header_line = lines[0].strip().split('\t')
seats_line = lines[1].strip().split('\t')
pnr_line = lines[2].strip().split('\t')
defect_line = lines[3].strip().split('\t')

mis_data = {}

for i, val in enumerate(header_line):
    if is_date(val):
        date_obj = datetime.strptime(val, "%m/%d/%Y")
        date_str = date_obj.strftime("%Y-%m-%d")
        
        try:
            seats = seats_line[i].replace(',', '').strip()
            pnr = pnr_line[i].replace(',', '').strip()
            defect = defect_line[i].replace('%', '').strip()
            
            mis_data[date_str] = {
                "seats": int(seats) if seats else 0,
                "pnr": int(pnr) if pnr else 0,
                "defect_rate": float(defect) if defect else 0.0
            }
        except IndexError:
            # Maybe the row is shorter
            mis_data[date_str] = {
                "seats": 0,
                "pnr": 0,
                "defect_rate": 0.0
            }

with open('backend/mis_daily.json', 'w', encoding='utf-8') as f:
    json.dump(mis_data, f, indent=2)

print(f"Processed {len(mis_data)} dates.")
