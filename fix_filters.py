import re

with open('freshdesk.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Make the filters normal dropdowns (remove multiple size="3")
html = html.replace(' multiple size="3"', '')

# Wrap each filter in a data-tabs attribute for easy toggling
html = html.replace('<div class="sb-fg">\n      <label>LOB</label>', '<div class="sb-fg" data-tabs="bunch-helpdesk">\n      <label>LOB</label>')
html = html.replace('<div class="sb-fg">\n      <label>Status</label>', '<div class="sb-fg" data-tabs="bunch-helpdesk,bunch-complaint,bunch-adoption">\n      <label>Status</label>')
html = html.replace('<div class="sb-fg">\n      <label>Type</label>', '<div class="sb-fg" data-tabs="bunch-helpdesk">\n      <label>Type</label>')
html = html.replace('<div class="sb-fg">\n      <label>Group</label>', '<div class="sb-fg" data-tabs="bunch-helpdesk">\n      <label>Group</label>')
html = html.replace('<div class="sb-fg">\n      <label>Priority</label>', '<div class="sb-fg" data-tabs="bunch-helpdesk">\n      <label>Priority</label>')
html = html.replace('<div class="sb-fg">\n      <label>Agent</label>', '<div class="sb-fg" data-tabs="bunch-helpdesk,bunch-adoption">\n      <label>Agent</label>')
html = html.replace('<div class="sb-fg">\n      <label>Source (HD Adoption)</label>', '<div class="sb-fg" data-tabs="bunch-adoption">\n      <label>Source (HD Adoption)</label>')
html = html.replace('<div class="sb-fg">\n      <label>Complaint Type</label>', '<div class="sb-fg" data-tabs="bunch-complaint">\n      <label>Complaint Type</label>')

with open('freshdesk.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('script_freshdesk.js', 'r', encoding='utf-8') as f:
    js = f.read()

adjust_logic = """
    function adjustSidebar(targetId) {
        document.querySelectorAll('.sb-fg[data-tabs]').forEach(el => {
            const tabs = el.getAttribute('data-tabs').split(',');
            if(tabs.includes(targetId)) {
                el.style.display = 'flex';
            } else {
                el.style.display = 'none';
            }
        });
    }
    adjustSidebar('bunch-helpdesk'); // Initialize
"""

# Replace the empty adjustSidebar
js = re.sub(r'function adjustSidebar\(targetId\) \{[\s\S]*?\}', adjust_logic, js)

# Since they are not multiple anymore, getSelected should just return the selected value if it's not 'All'
get_selected_logic = """
        const getSelected = (id) => {
            const el = document.getElementById(id);
            if (!el) return [];
            if (el.multiple) {
                return Array.from(el.selectedOptions).map(o => o.value).filter(v => v !== 'All');
            } else {
                return el.value !== 'All' ? [el.value] : [];
            }
        };
"""

js = re.sub(r'const getSelected = \(id\) => \{[\s\S]*?return vals;\n        \};', get_selected_logic.strip(), js)

with open('script_freshdesk.js', 'w', encoding='utf-8') as f:
    f.write(js)
