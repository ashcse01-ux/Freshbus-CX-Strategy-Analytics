import re

with open('excel_frontend.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace corrupted icons with [-] and [+]
content = re.sub(r'<span class="expand-icon">[^<]+</span>', '<span class="expand-icon">[-]</span>', content)
content = re.sub(r"icon\.textContent === '[^']+'", "icon.textContent === '[+]'", content)
content = re.sub(r"icon\.textContent = isCollapsed \? '[^']+' : '[^']+'", "icon.textContent = isCollapsed ? '[-]' : '[+]'", content)

with open('excel_frontend.js', 'w', encoding='utf-8') as f:
    f.write(content)
