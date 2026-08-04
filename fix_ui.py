import re

with open('freshdesk.html', 'r', encoding='utf-8') as f:
    html = f.read()

# I will find the beginning of .app-main
app_main_start = html.find('<main class="app-main">')
if app_main_start == -1:
    print("Could not find app-main")
    
# Let's rebuild the app-main section explicitly!
new_main = '''<main class="app-main">
    <div class="pg-head">
      <div>
        <h1>Helpdesk Analytics</h1>
        <p>Live performance analytics &middot; All metrics per business formulas</p>
      </div>
      <span class="pg-badge">Live A Database</span>
    </div>

    <!-- TABS -->
    <div class="seg-bar">
      <button class="seg-btn active" data-bunch="bunch-helpdesk">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
        Helpdesk
      </button>
      <button class="seg-btn" data-bunch="bunch-complaint">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Complaint Tracker
      </button>
      <button class="seg-btn" data-bunch="bunch-adoption">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        HD Adoption
      </button>
    </div>

    <!-- METRIC BUNCHES -->
    <div id="bunch-helpdesk" class="bunch active">
      <div class="bunch-grid">
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Tickets Created</div></div><div class="mc-val" id="hd-tickets-created">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">FTR Tickets</div></div><div class="mc-val" id="hd-ftr-tickets">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">NFTR Tickets</div></div><div class="mc-val" id="hd-nftr-tickets">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Blanks (FTR/NFTR)</div></div><div class="mc-val" id="hd-blanks">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Tickets Closed</div></div><div class="mc-val" id="hd-tickets-closed">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Tickets Pending (Open)</div></div><div class="mc-val" id="hd-tickets-pending">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Inbound Calls Ans</div></div><div class="mc-val" id="hd-calls-ans">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Ticket Not Created FD</div></div><div class="mc-val" id="hd-not-created">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Resolution Time (FTR Avg Hrs)</div></div><div class="mc-val" id="hd-ftr-restime">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Resolution Time (NFTR Avg Hrs)</div></div><div class="mc-val" id="hd-nftr-restime">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Overall Resolution Time (Avg Hrs)</div></div><div class="mc-val" id="hd-overall-restime">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Fresh Desk Adoption %</div></div><div class="mc-val" id="hd-fd-adoption">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Seats</div></div><div class="mc-val" id="hd-seats">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">PNR</div></div><div class="mc-val" id="hd-pnr">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Defect Rate %</div></div><div class="mc-val" id="hd-defect-rate">0</div></div>
      </div>
      <h3 style="margin:1rem 0; font-family:'Plus Jakarta Sans';">Ticket Source Breakdowns</h3>
      <div class="bunch-grid">
        <div class="mc"><div class="mc-head"><div class="mc-lbl">InBound FTR</div></div><div class="mc-val" id="hd-inbound-ftr">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">InBound NFTR</div></div><div class="mc-val" id="hd-inbound-nftr">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">InBound Res Time</div></div><div class="mc-val" id="hd-inbound-rt">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">OutBound FTR</div></div><div class="mc-val" id="hd-outbound-ftr">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">OutBound NFTR</div></div><div class="mc-val" id="hd-outbound-nftr">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">OutBound Res Time</div></div><div class="mc-val" id="hd-outbound-rt">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Email FTR</div></div><div class="mc-val" id="hd-email-ftr">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Email NFTR</div></div><div class="mc-val" id="hd-email-nftr">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Email Res Time</div></div><div class="mc-val" id="hd-email-rt">0</div></div>
      </div>
    </div>

    <div id="bunch-complaint" class="bunch">
      <div class="bunch-grid">
        <div class="mc"><div class="mc-head"><div class="mc-lbl">New Tickets</div></div><div class="mc-val" id="comp-new">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Back Dated Total Cases</div></div><div class="mc-val" id="comp-backdated">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Closed</div></div><div class="mc-val" id="comp-closed">0</div></div>
      </div>
    </div>

    <div id="bunch-adoption" class="bunch">
      <div class="bunch-grid">
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Tickets Created</div></div><div class="mc-val" id="adop-tickets-created">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">FTR Tickets</div></div><div class="mc-val" id="adop-ftr-tickets">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">NFTR Tickets (Overall)</div></div><div class="mc-val" id="adop-nftr-tickets">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Blanks (FTR/NFTR)</div></div><div class="mc-val" id="adop-blanks">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Tickets Closed</div></div><div class="mc-val" id="adop-tickets-closed">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Ticket Pending (Open)</div></div><div class="mc-val" id="adop-tickets-pending">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Inbound Calls Ans</div></div><div class="mc-val" id="adop-calls-ans">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Ticket Not Created FD</div></div><div class="mc-val" id="adop-not-created">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">FTR Resolution Time (Avg Hr)</div></div><div class="mc-val" id="adop-ftr-restime">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">NFTR Resolution Time (Avg Hr)</div></div><div class="mc-val" id="adop-nftr-restime">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Overall Resolution Time (Avg Hr)</div></div><div class="mc-val" id="adop-overall-restime">0</div></div>
        <div class="mc"><div class="mc-head"><div class="mc-lbl">Fresh Desk Adoption %</div></div><div class="mc-val" id="adop-fd-adoption">0</div></div>
      </div>
    </div>
  </main>
</div>
'''

html = re.sub(r'<main class="app-main">.*?</main>\s*</div>', new_main, html, flags=re.DOTALL)

with open('freshdesk.html', 'w', encoding='utf-8') as f:
    f.write(html)
