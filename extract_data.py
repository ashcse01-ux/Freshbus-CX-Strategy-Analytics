import re
import os

with open('d:/Freshbus-CX-Strategy-Analytics/Freshdesk Automation - Help Desk/freshbus_helpdesk.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract RAW_HD
print("Extracting RAW_HD...")
match_hd = re.search(r'const RAW_HD\s*=\s*(\[.*?\]);', html, flags=re.DOTALL)
if match_hd:
    with open('d:/Freshbus-CX-Strategy-Analytics/backend/raw_hd.json', 'w', encoding='utf-8') as f:
        f.write(match_hd.group(1))
    print("Saved raw_hd.json")
else:
    print("RAW_HD not found")

# Extract RAW_HDA
print("Extracting RAW_HDA...")
match_hda = re.search(r'const RAW_HDA\s*=\s*(\[.*?\]);', html, flags=re.DOTALL)
if match_hda:
    with open('d:/Freshbus-CX-Strategy-Analytics/backend/raw_hda.json', 'w', encoding='utf-8') as f:
        f.write(match_hda.group(1))
    print("Saved raw_hda.json")
else:
    print("RAW_HDA not found")
