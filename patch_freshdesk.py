import re

with open('freshdesk.html', 'r', encoding='utf-8') as f:
    html = f.read()

kpi_html = '''
    <div class="kpi-grid">
      <div class="kpi-box">
        <div class="kpi-label">Total Tickets Created</div>
        <div class="kpi-val" id="kpi-created">--</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-label">Tickets Closed</div>
        <div class="kpi-val" id="kpi-closed">--</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-label">FTR Tickets</div>
        <div class="kpi-val" id="kpi-ftr">--</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-label">Helpdesk Adoption</div>
        <div class="kpi-val" id="kpi-adoption">--</div>
      </div>
      <div class="kpi-box">
        <div class="kpi-label">Avg Resolution Time</div>
        <div class="kpi-val" id="kpi-restime">--</div>
      </div>
    </div>
'''
html = re.sub(r'<div class="kpi-grid">.*?</div>\s*</div>', kpi_html + '</div>', html, flags=re.DOTALL)

charts_html = '''
    <div class="ch-grid">
      <div class="ch-box">
        <div class="ch-title">Tickets Created vs Closed</div>
        <div class="ch-wrap"><canvas id="ch-tickets"></canvas></div>
      </div>
      <div class="ch-box">
        <div class="ch-title">FTR vs NFTR Trends</div>
        <div class="ch-wrap"><canvas id="ch-ftr"></canvas></div>
      </div>
      <div class="ch-box ch-full">
        <div class="ch-title">Helpdesk Adoption Rate (%)</div>
        <div class="ch-wrap"><canvas id="ch-adoption"></canvas></div>
      </div>
    </div>
'''
html = re.sub(r'<div class="ch-grid">.*?</div>\s*</div>\s*</div>\s*</div>', charts_html + '</div></div></div>', html, count=1, flags=re.DOTALL)

with open('freshdesk.html', 'w', encoding='utf-8') as f:
    f.write(html)
