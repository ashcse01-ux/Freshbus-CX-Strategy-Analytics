import re

with open('inbound.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix opacity for light mode
content = content.replace('--surface-solid: rgba(255, 255, 255, 0.85);', '--surface-solid: #ffffff;')
# Fix opacity for dark mode
content = content.replace('--surface-solid: rgba(17, 25, 39, 0.9);', '--surface-solid: #111927;')

# Fix Download button colors
btn_old = 'id="excelDownloadBtn" class="sb-btn sb-btn-primary" style="width:auto; padding:8px 16px; margin:0; background:linear-gradient(135deg, #16a34a, #15803d);"'
btn_new = 'id="excelDownloadBtn" class="sb-btn" style="width:auto; padding:8px 16px; margin:0; background:var(--blue); color:var(--yellow); font-weight:700; border: 2px solid var(--yellow); border-radius: 6px;"'
content = content.replace(btn_old, btn_new)

with open('inbound.html', 'w', encoding='utf-8') as f:
    f.write(content)
