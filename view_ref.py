with open('d:/Freshbus-CX-Strategy-Analytics/Freshdesk Automation - Help Desk/freshbus_helpdesk.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'id="pgD1"' in line:
        print(''.join(lines[i:i+60]))
        break
