with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix broken characters from previous script encoding issue
content = content.replace("- ", "▶ ")
content = content.replace("-", "▼")

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(content)
