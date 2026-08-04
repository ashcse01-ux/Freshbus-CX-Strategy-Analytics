with open('campaign.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
# Remove Weekly Sheet Doc
html = re.sub(r'<div class="dash-card locked">.*?Weekly Sheet Doc Analytics Dashboard.*?</div>\s*</div>', '', html, flags=re.DOTALL)
# Remove Incentives Analytics
html = re.sub(r'<div class="dash-card locked">.*?Incentives Analytics Dashboard.*?</div>\s*</div>', '', html, flags=re.DOTALL)
# Remove Ops Tech Issue
html = re.sub(r'<div class="dash-card locked">.*?Ops Tech Issue.*?</div>\s*</div>', '', html, flags=re.DOTALL)

with open('campaign.html', 'w', encoding='utf-8') as f:
    f.write(html)
