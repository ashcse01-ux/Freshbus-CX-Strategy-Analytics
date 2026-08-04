with open('inbound.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the scripts
scripts = """<script src="visual_engine.js"></script>
<script src="script.js"></script>"""
content = content.replace(scripts, '')

# Add them right before </body>
content = content.replace('</body>', scripts + '\n</body>')

with open('inbound.html', 'w', encoding='utf-8') as f:
    f.write(content)
