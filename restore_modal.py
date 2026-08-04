modal_html = """
<!-- Excel View Modal Overlay -->
<div id="excelModal" class="excel-modal">
  <div class="excel-modal-content">
    <div class="excel-header">
      <div class="excel-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="16" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
        <span>Data Export View</span>
      </div>
      <div class="excel-actions">
        <div class="hdr-datewrap" style="background:rgba(0,0,0,0.2); border-color:rgba(255,255,255,0.2);">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
          <input type="text" id="excel_start_date" placeholder="Start Date" readonly>
          <span class="sep">→</span>
          <input type="text" id="excel_end_date" placeholder="End Date" readonly>
        </div>
        <button id="excelDownloadBtn" class="sb-btn" style="width:auto; padding:8px 16px; margin:0; background:var(--blue); color:var(--yellow); font-weight:700; border: 2px solid var(--yellow); border-radius: 6px;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
          Download Report
        </button>
        <button id="excelCloseBtn" class="excel-close-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
    </div>
    <div class="excel-body" style="position:relative;">
      <div id="excelLoader" style="display:none; position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width:30px; height:30px; border:3px solid var(--text); border-top-color:transparent; border-radius:50%; animation:spin 1s linear infinite;"></div>
      <table class="excel-table" id="excelTable">
        <thead>
          <tr id="excelRowMonths"></tr>
          <tr id="excelRowWeeks"></tr>
          <tr id="excelRowDays"></tr>
        </thead>
        <tbody id="excelTableBody">
        </tbody>
      </table>
    </div>
  </div>
</div>
"""

css_html = """
<style>
/* Excel Modal Styles */
.excel-modal {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);
  z-index: 10000; opacity: 0; visibility: hidden; transition: all 0.3s ease;
  display: flex; align-items: center; justify-content: center;
}
.excel-modal.show {
  opacity: 1; visibility: visible;
}
.excel-modal-content {
  width: 95%; height: 90%; background: var(--surface-solid);
  border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  display: flex; flex-direction: column; overflow: hidden;
}
.excel-header {
  padding: 16px 24px; background: linear-gradient(135deg, var(--blue), var(--blue-d));
  color: #fff; display: flex; justify-content: space-between; align-items: center;
}
.excel-title {
  display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.1rem;
}
.excel-title svg { width: 20px; height: 20px; }
.excel-actions {
  display: flex; align-items: center; gap: 15px;
}
.excel-close-btn {
  background: transparent; border: none; color: #fff; cursor: pointer; padding: 4px;
  border-radius: 4px; transition: all 0.2s;
}
.excel-close-btn:hover { background: rgba(255,255,255,0.2); }
.excel-close-btn svg { width: 24px; height: 24px; }
.excel-body {
  flex: 1; overflow: auto; padding: 0; background: var(--surface-solid);
}
.excel-table {
  border-collapse: collapse; width: max-content; min-width: 100%; text-align: center;
}
.excel-table th, .excel-table td {
  border: 1px solid var(--border); padding: 8px 12px; font-size: 0.85rem; white-space: nowrap;
}
.excel-table th {
  background: var(--surface2); font-weight: 600; color: var(--text); position: sticky;
}
.excel-table thead tr:nth-child(1) th { top: 0; z-index: 10; }
.excel-table thead tr:nth-child(2) th { top: 35px; z-index: 10; }
.excel-table thead tr:nth-child(3) th { top: 70px; z-index: 10; }
.col-metric {
  position: sticky; left: 0; background: var(--surface-solid); z-index: 20; text-align: left; font-weight: 700;
  box-shadow: 2px 0 5px rgba(0,0,0,0.05); font-family: 'Inter', sans-serif;
}
.col-week {
  cursor: pointer; user-select: none; transition: background 0.2s;
}
.col-week:hover { background: var(--blue-soft); }
.expand-icon { font-size: 0.7em; margin-left: 4px; transition: transform 0.2s; display: inline-block; }
.col-week.collapsed .expand-icon { transform: rotate(-90deg); }
.excel-table tbody tr:hover td { background: var(--surface2); }
</style>
"""

with open('inbound.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure not to double add
if 'id="excelModal"' not in content:
    content = content.replace('</body>', css_html + '\n' + modal_html + '\n</body>')

with open('inbound.html', 'w', encoding='utf-8') as f:
    f.write(content)
