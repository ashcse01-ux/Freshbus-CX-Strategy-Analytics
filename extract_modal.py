import json
import re

transcript_path = r'C:\Users\Ayush Jain\.gemini\antigravity-ide\brain\a8419ef3-5dda-4634-9767-ae6095772f72\.system_generated\logs\transcript_full.jsonl'
lines = []
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        if 'excelModal' in line:
            try:
                data = json.loads(line)
                if 'tool_calls' in data:
                    for call in data['tool_calls']:
                        if call.get('name') == 'write_to_file' or call.get('name') == 'replace_file_content':
                            args = call.get('arguments', {})
                            for k, v in args.items():
                                if isinstance(v, str) and 'id="excelModal"' in v:
                                    lines.append(v)
            except:
                pass

with open('modal_recover.txt', 'w', encoding='utf-8') as f:
    for l in lines:
        f.write(l + '\n---\n')
