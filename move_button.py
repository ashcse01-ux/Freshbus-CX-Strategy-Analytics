import re

with open('inbound.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the button from the header
pattern_header = r'<button id="openExcelViewBtn"[^>]*>\s*Excel View\s*</button>'
content = re.sub(pattern_header, '', content, flags=re.MULTILINE|re.DOTALL)

# 2. Insert it below OzoneTel Live
target = '<div class="sb-sync"><div class="sb-dot"></div><span>OzoneTel Live</span></div>'
new_button = '\n  <button id="excelViewBtn" class="sb-btn sb-btn-primary" style="margin-top: 15px; width: 100%; background: linear-gradient(135deg, var(--blue), var(--blue-d)); color: #fff;">Excel View</button>'

if new_button not in content:
    content = content.replace(target, target + new_button)

with open('inbound.html', 'w', encoding='utf-8') as f:
    f.write(content)
