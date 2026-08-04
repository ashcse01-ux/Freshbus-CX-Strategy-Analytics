import re

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to find the `const metricKeys = [...]` array and replace it with:
# `const metricKeys = Object.keys(data.months[0].weeks[0].days[0].metrics);`

pattern = re.compile(r'const metricKeys = \[.*?\];', re.DOTALL)
replacement = '''let metricKeys = [];
    try {
      metricKeys = Object.keys(data.months[0].weeks[0].days[0].metrics);
    } catch(e) {
      metricKeys = ["Total Calls", "Total Answered", "Total Abandoned", "Service Level %", "Answer Level %", "Abandon %", "AHT"];
    }'''

new_content = pattern.sub(replacement, content)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(new_content)
