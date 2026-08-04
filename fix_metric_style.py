import re

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'''tr\.innerHTML = `<td class="col-metric" style="font-family: \\'Inter\\', sans-serif; font-weight: \n?500;">\$\{mk\}</td>`;'''
replacement = '''tr.innerHTML = `<td class="col-metric" style="font-family: 'Inter', sans-serif; font-weight: 600; text-align: center; padding: 12px 16px; background: var(--bg-card); color: var(--text-main); position: sticky; left: 0; z-index: 2; border-right: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color);">${mk}</td>`;'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(new_content)
