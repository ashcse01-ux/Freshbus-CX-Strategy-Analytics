import re

# Fix script.js download API_BASE
with open('script.js', 'r', encoding='utf-8') as f:
    script_content = f.read()

script_content = script_content.replace(
    "let url = '/api/excel/export?parent_campaign=Inbound';",
    "let url = API_BASE + '/api/excel/export?parent_campaign=Inbound';"
)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(script_content)

# Fix inbound.html button colors
with open('inbound.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

old_btn = 'id="excelDownloadBtn" class="sb-btn" style="width:auto; padding:8px 16px; margin:0; background:var(--blue); color:var(--yellow); font-weight:700; border: 2px solid var(--yellow); border-radius: 6px;"'
new_btn = 'id="excelDownloadBtn" class="sb-btn" style="width:auto; padding:8px 16px; margin:0; background:var(--yellow); color:var(--blue-d); font-weight:800; border:none; border-radius: 6px; box-shadow: 0 4px 12px rgba(251,188,4,0.3);"'

if old_btn in html_content:
    html_content = html_content.replace(old_btn, new_btn)

with open('inbound.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
