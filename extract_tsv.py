import json

log_path = r'C:\Users\Ayush Jain\.gemini\antigravity-ide\brain\a8419ef3-5dda-4634-9767-ae6095772f72\.system_generated\logs\transcript_full.jsonl'
msgs = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        if 'USER_INPUT' in line:
            msgs.append(json.loads(line))

if msgs:
    last_msg = msgs[-1]['content']
    with open('extracted_data.tsv', 'w', encoding='utf-8') as f:
        f.write(last_msg)
    print("Successfully extracted TSV!")
else:
    print("No USER_INPUT found.")
