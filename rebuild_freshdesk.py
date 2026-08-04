import re

with open('freshdesk.html', 'r', encoding='utf-8') as f:
    html = f.read()

style_match = re.search(r'<style>.*?</style>', html, flags=re.DOTALL)
css = style_match.group(0) if style_match else '<style></style>'

new_html = f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FreshBus | Helpdesk Analytics</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  {css}
</head>
<body>
<!-- HEADER -->
<header class="hdr">
  <a href="campaign.html" class="hdr-logo">
    <div class="hdr-lm">
      <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M 32 82 L 32 20 C 32 14, 37 10, 43 10 L 71 10 C 80 10, 84 21, 76 28 L 56 46 L 70 46 C 79 46, 83 57, 75 64 L 43 92 C 35 99, 32 92, 32 85 Z" fill="#FFEA20"/>
      </svg>
    </div>
    <div class="hdr-brand-wrap">
      <span class="hdr-ln">Fresh Bus</span>
      <span class="hdr-sub">Helpdesk Analytics Dashboard</span>
    </div>
  </a>

  <!-- Date pickers -->
  <button id="sync-btn" style="background:#fff;color:#0c4dc3;border:none;border-radius:6px;padding:8px 16px;font-weight:700;cursor:pointer;margin-right:16px;transition:0.2s;">Sync Sheet</button>
  <div class="hdr-fill"></div>
  <div class="hdr-user">
    <div class="hdr-av"><img src="https://ui-avatars.com/api/?name=Admin&background=FFEA20&color=0c4dc3&size=64" alt=""></div>
    <span class="hdr-un">Admin</span>
  </div>
</header>

<div class="app-body">
<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="sb-sec">Overview</div>
  <button class="sb-btn sb-btn-primary tnav-btn on" id="tn-ov" onclick="nav('pgOv','tn-ov')">Summary</button>
  
  <div class="sb-sec">Dashboards</div>
  <button class="sb-btn tnav-btn" id="tn-d1" onclick="nav('pgD1','tn-d1')">Dashboard 1 - Helpdesk</button>
  <button class="sb-btn tnav-btn" id=\"tn-d2\" onclick="nav('pgD2','tn-d2')">Dashboard 2 - HD Adoption</button>
  <button class="sb-btn tnav-btn" id="tn-d3" onclick="nav('pgD3','tn-d3')">Dashboard 3 - Complaints</button>
</aside>

<main class="app-main">
  <!-- PAGE: OVERVIEW -->
  <div class="dash-pg" id="pgOv">
    <div class="pg-head">
      <div>
        <h1>Helpdesk Overview Summary</h1>
        <p>High-level metrics across all support channels.</p>
      </div>
    </div>
    
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
  </div>

  <!-- PAGE: D1 HELPDESK -->
  <div class="dash-pg" id="pgD1" style="display:none;">
    <div class="pg-head">
      <div>
        <h1>Dashboard 1 - Helpdesk</h1>
        <p>Detailed breakdown of ticket statuses, agents, and resolution.</p>
      </div>
    </div>
    <div style="padding:40px; text-align:center; color:#666;">
       <h2>Helpdesk Detailed View</h2>
       <p>Filters and data tables for deep dive analysis will be rendered here.</p>
    </div>
  </div>

  <!-- PAGE: D2 HD ADOPTION -->
  <div class="dash-pg" id="pgD2" style="display:none;">
    <div class="pg-head">
      <div>
        <h1>Dashboard 2 - Freshdesk Adoption</h1>
        <p>Inbound Calls vs Ticket creation mapping.</p>
      </div>
    </div>
    <div style="padding:40px; text-align:center; color:#666;">
       <h2>HD Adoption View</h2>
       <p>Adoption mapping charts and tables will be rendered here.</p>
    </div>
  </div>

  <!-- PAGE: D3 COMPLAINTS -->
  <div class="dash-pg" id="pgD3" style="display:none;">
    <div class="pg-head">
      <div>
        <h1>Dashboard 3 - Complaint Tracker</h1>
        <p>Breakdown of all complaint types and categories.</p>
      </div>
    </div>
    <div style="padding:40px; text-align:center; color:#666;">
       <h2>Complaint Tracker View</h2>
       <p>Complaint categorization and pivot tables will be rendered here.</p>
    </div>
  </div>
</main>
</div>
<script src="script_freshdesk.js"></script>
</body>
</html>
'''

with open('freshdesk.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
