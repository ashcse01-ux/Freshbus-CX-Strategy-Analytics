import re

with open('freshdesk.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update Title
html = html.replace('Inbound Strategy', 'Helpdesk Analytics')
html = html.replace('CX & Strategy Analytics', 'Helpdesk Analytics Dashboard')

# Add sync button
sync_btn = '<button id="sync-btn" style="background:#fff;color:#0c4dc3;border:none;border-radius:6px;padding:8px 16px;font-weight:700;cursor:pointer;margin-right:16px;transition:0.2s;">Sync Sheet</button>\n  <div class="hdr-datewrap"'
html = html.replace('<div class="hdr-datewrap"', sync_btn)

# Update Nav
html = html.replace('Dashboard 1 — Inbound', 'Helpdesk Overview')
html = html.replace('Dashboard 2 — Hourly', 'HD Adoption')
html = html.replace('Dashboard 3 — Agent & Tag', 'Complaint Tracker')

# Clean JS - remove all script tags except external ones
html = re.sub(r'<script(?! src)>.*?</script>', '', html, flags=re.DOTALL)
html = html.replace('</body>', '<script src="script_freshdesk.js"></script>\n</body>')

with open('freshdesk.html', 'w', encoding='utf-8') as f:
    f.write(html)
