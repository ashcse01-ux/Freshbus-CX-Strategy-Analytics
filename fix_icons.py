import re

with open('excel_frontend.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure we have the [-] symbol in the innerHTML
content = re.sub(r'<span class="expand-icon">[^<]+</span>', '<span class="expand-icon">[-]</span>', content)

# Fix the Javascript toggle logic to use includes
content = re.sub(r'const isCollapsed = icon\.textContent === \'.*?\';', 'const isCollapsed = icon.textContent.includes(\'+\');', content)
content = re.sub(r'icon\.textContent = isCollapsed \? \'.*?\' : \'.*?\';', 'icon.textContent = isCollapsed ? \'[-]\' : \'[+]\';', content)

with open('excel_frontend.js', 'w', encoding='utf-8') as f:
    f.write(content)
