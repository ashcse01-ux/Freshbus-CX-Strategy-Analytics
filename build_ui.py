with open('inbound.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re

# 1. Change title and JS references
html = html.replace('Inbound Intelligence', 'Helpdesk Analytics')
html = html.replace('script.js', 'script_freshdesk.js')

# 2. Update Sidebar Filters
# Helpdesk filters: LOB , Status , Type , Group , Priority , Agent
new_sidebar = """<aside class="sidebar">
    <div class="sb-sec">Filters</div>
    
    <div class="sb-fg">
      <label>LOB</label>
      <select id="filter_lob" multiple size="3">
        <option value="All" selected>All</option>
      </select>
    </div>
    
    <div class="sb-fg">
      <label>Status</label>
      <select id="filter_status" multiple size="3">
        <option value="All" selected>All</option>
      </select>
    </div>
    
    <div class="sb-fg">
      <label>Type</label>
      <select id="filter_type" multiple size="3">
        <option value="All" selected>All</option>
      </select>
    </div>
    
    <div class="sb-fg">
      <label>Group</label>
      <select id="filter_group" multiple size="3">
        <option value="All" selected>All</option>
      </select>
    </div>
    
    <div class="sb-fg">
      <label>Priority</label>
      <select id="filter_priority" multiple size="3">
        <option value="All" selected>All</option>
      </select>
    </div>
    
    <div class="sb-fg">
      <label>Agent</label>
      <select id="filter_agent" multiple size="3">
        <option value="All" selected>All</option>
      </select>
    </div>
    
    <div class="sb-fg">
      <label>Source (HD Adoption)</label>
      <select id="filter_source" multiple size="3">
        <option value="All" selected>All</option>
      </select>
    </div>

    <div class="sb-fg">
      <label>Complaint Type</label>
      <select id="filter_complaint_type" multiple size="3">
        <option value="All" selected>All</option>
      </select>
    </div>

    <div class="sb-sec" style="margin-top:.5rem;">Actions</div>
    <button class="sb-btn sb-btn-primary" id="applyBtn">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      Apply Filters
    </button>
    <button class="sb-btn sb-btn-primary" id="clearBtn" style="background:var(--surface2);color:var(--text-muted);margin-top:2px;">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>
      Reset Filters
    </button>
  </aside>"""

html = re.sub(r'<aside class="sidebar">.*?</aside>', new_sidebar, html, flags=re.DOTALL)

# 3. Update the Seg-bar Tabs
new_tabs = """<div class="seg-bar">
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
    </div>"""

html = re.sub(r'<div class="seg-bar">.*?</div>', new_tabs, html, flags=re.DOTALL)

# 4. Update Header actions to include Go button properly inside hdr-acts
# Wait, the Date Bar is already in inbound.html:
# <input type="text" id="filter_start_date"> ... <input type="text" id="filter_end_date">
# Then it has #refreshBtn. We'll change #refreshBtn to a "Go" button.
html = html.replace('id="refreshBtn" title="Refresh data"', 'id="goBtn" title="Fetch Data"')
html = html.replace('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 019-9 9 9 0 016.36 2.64L21 9M21 3v6h-6M21 12a9 9 0 01-9 9 9 9 0 01-6.36-2.64L3 15M3 21v-6h6"/></svg>', 'GO')

# 5. Build Metric Bunches
# Helpdesk: Tickets Created, FTR Tickets, NFTR Tickets, (Blanks), Tickets Closed, Ticket Pending, Inbound Calls Ans, Ticket Not Created FD, Resolution Time (Avg), NFTR Resolution Time, Overall Resolution Time, Fresh Desk Adoption, Seats, PNR, Defect Rate, Ticket Source (InBound, OutBound, Email).

def make_card(id, lbl, val='0'):
    return f'''
    <div class="mc">
      <div class="mc-head">
        <div class="mc-lbl">{lbl}</div>
        <div class="mc-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
      </div>
      <div class="mc-val" id="{id}">{val}</div>
    </div>
    '''

bunch_helpdesk = '<div id="bunch-helpdesk" class="bunch active"><div class="bunch-grid">' + \
    make_card('hd-tickets-created', 'Tickets Created') + \
    make_card('hd-ftr-tickets', 'FTR Tickets') + \
    make_card('hd-nftr-tickets', 'NFTR Tickets') + \
    make_card('hd-blanks', 'Blanks (FTR/NFTR)') + \
    make_card('hd-tickets-closed', 'Tickets Closed') + \
    make_card('hd-tickets-pending', 'Tickets Pending (Open)') + \
    make_card('hd-calls-ans', 'Inbound Calls Ans') + \
    make_card('hd-not-created', 'Ticket Not Created FD') + \
    make_card('hd-ftr-restime', 'Resolution Time (FTR Avg Hrs)') + \
    make_card('hd-nftr-restime', 'Resolution Time (NFTR Avg Hrs)') + \
    make_card('hd-overall-restime', 'Overall Resolution Time (Avg Hrs)') + \
    make_card('hd-fd-adoption', 'Fresh Desk Adoption %') + \
    make_card('hd-seats', 'Seats') + \
    make_card('hd-pnr', 'PNR') + \
    make_card('hd-defect-rate', 'Defect Rate %') + \
    '</div><h3 style="margin:1rem 0; font-family:\'Plus Jakarta Sans\';">Ticket Source Breakdowns</h3><div class="bunch-grid">' + \
    make_card('hd-inbound-ftr', 'InBound FTR') + \
    make_card('hd-inbound-nftr', 'InBound NFTR') + \
    make_card('hd-inbound-rt', 'InBound Res Time') + \
    make_card('hd-outbound-ftr', 'OutBound FTR') + \
    make_card('hd-outbound-nftr', 'OutBound NFTR') + \
    make_card('hd-outbound-rt', 'OutBound Res Time') + \
    make_card('hd-email-ftr', 'Email FTR') + \
    make_card('hd-email-nftr', 'Email NFTR') + \
    make_card('hd-email-rt', 'Email Res Time') + \
    '</div></div>'

bunch_complaint = '<div id="bunch-complaint" class="bunch"><div class="bunch-grid">' + \
    make_card('comp-new', 'New Tickets') + \
    make_card('comp-backdated', 'Back Dated Total Cases') + \
    make_card('comp-closed', 'Closed') + \
    '</div></div>'

bunch_adoption = '<div id="bunch-adoption" class="bunch"><div class="bunch-grid">' + \
    make_card('adop-tickets-created', 'Tickets Created') + \
    make_card('adop-ftr-tickets', 'FTR Tickets') + \
    make_card('adop-nftr-tickets', 'NFTR Tickets (Overall)') + \
    make_card('adop-blanks', 'Blanks (FTR/NFTR)') + \
    make_card('adop-tickets-closed', 'Tickets Closed') + \
    make_card('adop-tickets-pending', 'Ticket Pending (Open)') + \
    make_card('adop-calls-ans', 'Inbound Calls Ans') + \
    make_card('adop-not-created', 'Ticket Not Created FD') + \
    make_card('adop-ftr-restime', 'FTR Resolution Time (Avg Hr)') + \
    make_card('adop-nftr-restime', 'NFTR Resolution Time (Avg Hr)') + \
    make_card('adop-overall-restime', 'Overall Resolution Time (Avg Hr)') + \
    make_card('adop-fd-adoption', 'Fresh Desk Adoption %') + \
    '</div></div>'

# Replace everything inside <div class="app-main"> until the ending </div> of app-main
# Wait, let's just replace all the <div class="bunch ..."> elements.
html = re.sub(r'<div id="bunch-ans".*?</div>\s*</div>\s*</div>', bunch_helpdesk + bunch_complaint + bunch_adoption, html, flags=re.DOTALL)

with open('freshdesk.html', 'w', encoding='utf-8') as f:
    f.write(html)
