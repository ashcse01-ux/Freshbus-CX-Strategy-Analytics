with open('inbound.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Force browser to ignore cache for script.js
content = content.replace('<script src="script.js"></script>', '<script src="script.js?v=3"></script>')

with open('inbound.html', 'w', encoding='utf-8') as f:
    f.write(content)
