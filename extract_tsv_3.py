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

target_msg = None
for msg in msgs:
    if len(msg) > 40000:
        target_msg = msg
        break

if target_msg:
    with open('extracted_data.tsv', 'w', encoding='utf-8') as f:
        f.write(target_msg)
    print(f"Successfully extracted massive TSV with length {len(target_msg)}!")
else:
    print("Could not find the target message.")
