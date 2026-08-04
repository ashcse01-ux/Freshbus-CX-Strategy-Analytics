import re
import os

with open("inbound.html", "r", encoding="utf-8") as f:
    content = f.read()

# Extract the CSS block
css_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
css = css_match.group(1) if css_match else ""

html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FreshBus | Redbus Analytics</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
  <style>
  {css}
  </style>
</head>
<body>
  <div class="hdr">
    <a href="#" class="hdr-logo">
      <div class="hdr-lm">
        <svg viewBox="0 0 24 24" fill="none" stroke="#FFEA20" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg>
      </div>
      <div class="hdr-brand-wrap">
        <div class="hdr-ln">FreshBus</div>
        <div class="hdr-sub">Redbus Analytics</div>
      </div>
    </a>
  </div>

  <div class="app-body">
    <div class="sidebar">
      <div class="sb-sec">Filters</div>
      <div class="sb-fg">
        <label>Date Range</label>
        <input type="text" id="datePicker" placeholder="Select dates...">
      </div>
      <div class="sb-fg">
        <label>Route</label>
        <select id="routeFilter">
            <option value="all">All Routes</option>
        </select>
      </div>
      <button class="sb-btn sb-btn-primary" id="goBtn" style="margin-top: 10px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
        Sync & Update
      </button>
    </div>

    <div class="app-main">
      <div class="pg-head">
        <div>
          <h1>Redbus Dashboard</h1>
          <p>KPIs and Route-wise Analytics for Redbus</p>
        </div>
      </div>

      <div class="hero-row" id="kpiContainer">
        <!-- Cards injected by JS -->
      </div>

      <div style="display:flex; gap:1.5rem; flex-wrap:wrap;">
        <div class="hero-card" style="flex:1; min-width:300px; padding:1.5rem;">
          <div class="hc-lbl">Route-wise Performance</div>
          <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:0.85rem;" id="routeTable">
            <thead>
              <tr style="border-bottom:1px solid var(--border); text-align:left;">
                <th style="padding:8px;">Route</th>
                <th style="padding:8px;">Travel Count</th>
                <th style="padding:8px;">Rating Count</th>
                <th style="padding:8px;">Avg Rating</th>
                <th style="padding:8px;">Response Rate</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>

        <div class="hero-card" style="flex:1; min-width:300px; padding:1.5rem;">
          <div class="hc-lbl">TL Performance</div>
          <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:0.85rem;" id="tlTable">
            <thead>
              <tr style="border-bottom:1px solid var(--border); text-align:left;">
                <th style="padding:8px;">TL Name</th>
                <th style="padding:8px;">Count</th>
                <th style="padding:8px;">Avg Rating</th>
                <th style="padding:8px;">Response Rate</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <script>
    flatpickr("#datePicker", {{ mode: "range", dateFormat: "Y-m-d" }});

    function createCard(title, value) {{
        return `
            <div class="hero-card" style="--accent:var(--blue);">
                <div class="hc-top">
                    <div class="hc-lbl">${{title}}</div>
                </div>
                <div class="hc-val">${{value}}</div>
            </div>
        `;
    }}

    async function loadData() {{
        try {{
            const res = await fetch('/api/redbus/metrics');
            const result = await res.json();
            if(result.status === 'success') {{
                const data = result.data;
                const container = document.getElementById('kpiContainer');
                container.innerHTML = '';
                
                // Cards
                for (const [key, val] of Object.entries(data.cards)) {{
                    container.innerHTML += createCard(key, val);
                }}

                // Routes Table
                const routeTbody = document.querySelector('#routeTable tbody');
                routeTbody.innerHTML = '';
                data.routes.forEach(r => {{
                    routeTbody.innerHTML += `
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:8px; font-weight:600;">${{r.route}}</td>
                            <td style="padding:8px;">${{r.travel_count}}</td>
                            <td style="padding:8px;">${{r.rating_count}}</td>
                            <td style="padding:8px; color:var(--green); font-weight:700;">${{r.avg_rating}}</td>
                            <td style="padding:8px; color:var(--blue); font-weight:700;">${{r.response_rate}}</td>
                        </tr>
                    `;
                }});

                // TL Table
                const tlTbody = document.querySelector('#tlTable tbody');
                tlTbody.innerHTML = '';
                data.tls.forEach(t => {{
                    tlTbody.innerHTML += `
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:8px; font-weight:600;">${{t.tl}}</td>
                            <td style="padding:8px;">${{t.count}}</td>
                            <td style="padding:8px; color:var(--green); font-weight:700;">${{t.avg}}</td>
                            <td style="padding:8px; color:var(--blue); font-weight:700;">${{t.response_rate}}</td>
                        </tr>
                    `;
                }});
            }}
        }} catch(e) {{
            console.error('Error loading data', e);
        }}
    }}

    document.getElementById('goBtn').addEventListener('click', loadData);
    
    // Initial load
    loadData();
  </script>
</body>
</html>
"""

with open("redbus.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Created redbus.html successfully!")
