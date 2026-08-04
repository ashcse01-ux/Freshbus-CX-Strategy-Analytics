with open('d:/Freshbus-CX-Strategy-Analytics/Freshdesk Automation - Help Desk/freshbus_helpdesk.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re

# find renderD1 function
match = re.search(r'function renderD1\(\)\s*\{.*?(function renderD2|</script>)', html, flags=re.DOTALL)
if match:
    print(match.group(0)[:1500])
