import json

log_path = r'C:\Users\Ayush Jain\.gemini\antigravity-ide\brain\a8419ef3-5dda-4634-9767-ae6095772f72\.system_generated\logs\transcript_full.jsonl'
msgs = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('type') == 'USER_INPUT':
                msgs.append(data['content'])
        except:
            pass

if msgs:
    # Print lengths to figure out which one is the massive data dump
    for i, msg in enumerate(msgs):
        print(f"Message {i} length: {len(msg)}")
    
    # We want the one with 'Gross Seats\nGross Tickets'
    target_msg = next((m for m in msgs if 'Gross Seats' in m and 'Gross Tickets' in m), None)
    
    if target_msg:
        with open('extracted_data.tsv', 'w', encoding='utf-8') as f:
            f.write(target_msg)
        print("Successfully extracted target TSV!")
    else:
        print("Could not find the target message.")
else:
    print("No USER_INPUT found.")
