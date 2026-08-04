import re

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'''let metricKeys = \[\];\s*try \{\s*metricKeys = Object\.keys\(data\.months\[0\]\.weeks\[0\]\.days\[0\]\.metrics\);\s*\} catch\(e\) \{\s*metricKeys = \[.*?\];\s*\}\s*function renderExcelTable\(data\) \{'''

replacement = '''function renderExcelTable(data) {
      let metricKeys = [];
      try {
        metricKeys = Object.keys(data.months[0].weeks[0].days[0].metrics);
      } catch(e) {
        metricKeys = ["Total Calls", "Total Answered", "Total Abandoned", "Service Level %", "Answer Level %", "Abandon %", "AHT"];
      }'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(new_content)
