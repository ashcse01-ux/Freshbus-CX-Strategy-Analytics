import re
import json
import datetime

log_path = '/Users/ash/.gemini/antigravity/brain/5c22d7c8-2ef9-464b-a953-b54676e8099a/.system_generated/logs/overview.txt'

with open(log_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the user request containing the excel data
# We look for "excel data file i am attaching ok..."
match = re.search(r'excel data file i am attaching ok\.\.\.(.*?)<USER_REQUEST>', content, re.DOTALL)
if not match:
    # Try finding it until the end of file or next marker
    match = re.search(r'excel data file i am attaching ok\.\.\.(.*)', content, re.DOTALL)

if not match:
    print("Could not find the TSV data in logs.")
    exit(1)

raw_data = match.group(1).strip()

lines = [line for line in raw_data.split('\n') if line.strip()]

with open('/Users/ash/Freshbus CX Analytics/backend/raw_manual_data.txt', 'w') as f:
    f.write(raw_data)

print(f"Extracted {len(lines)} lines of raw data. Saved to raw_manual_data.txt")
