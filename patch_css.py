import re

with open('styles.css', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "/* =========================================\n   EXCEL VIEW MODAL\n========================================= */"
# Look for the end of the file or another section
end_index = content.find("/* =========================================\n   MEDIA QUERIES", content.find(start_marker))
if end_index == -1:
    end_index = len(content)

new_css = """/* =========================================
   EXCEL VIEW MODAL (LIQUID GLASS UI)
========================================= */
.excel-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.4);
  z-index: 9999;
  display: none;
  opacity: 0;
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 30px;
}
.excel-modal.show {
  display: flex;
  opacity: 1;
  align-items: center;
  justify-content: center;
}
.excel-modal-content {
  background: rgba(255, 255, 255, 0.6);
  width: 100%;
  height: 100%;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25), inset 0 0 0 1px rgba(255, 255, 255, 0.3);
  overflow: hidden;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}
[data-theme="dark"] .excel-modal-content {
  background: rgba(15, 23, 42, 0.6);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}

.excel-header {
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
[data-theme="dark"] .excel-header {
  background: rgba(30, 41, 59, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.excel-title h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}
.excel-title p {
  margin: 4px 0 0;
  font-size: 0.9rem;
  color: var(--text-muted);
}
.excel-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

/* Excel Style Inputs */
.excel-date-wrap {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  padding: 6px 12px;
  gap: 8px;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
  transition: all 0.2s ease;
}
[data-theme="dark"] .excel-date-wrap {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.excel-date-wrap:focus-within {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px var(--blue-soft);
}
.excel-date-wrap input {
  background: transparent;
  border: none;
  color: var(--text);
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: 500;
  outline: none;
  width: 110px;
}

/* Buttons */
.btn-yellow, .btn-blue, .btn-close {
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.btn-yellow {
  background: linear-gradient(135deg, #FFD000 0%, #FBBC04 100%);
  color: #1f2937;
}
.btn-yellow:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(251, 188, 4, 0.4);
}

.btn-blue {
  background: linear-gradient(135deg, #3b82f6 0%, #1A73E8 100%);
  color: #fff;
}
.btn-blue:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(26, 115, 232, 0.4);
}

.btn-close {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}
.btn-close:hover {
  background: #ef4444;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.4);
}

/* Loader */
.excel-loader {
  padding: 40px;
  text-align: center;
  color: var(--blue);
  font-weight: 600;
  font-size: 1.1rem;
}

/* Table Area */
.excel-body {
  flex: 1;
  overflow: auto;
  position: relative;
  background: transparent;
  padding: 0 1px 1px 0; /* space for borders */
}
.excel-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.9rem;
  transition: opacity 0.3s ease;
}
.excel-table th, .excel-table td {
  padding: 12px 16px;
  border-right: 1px solid rgba(0,0,0,0.06);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  white-space: nowrap;
  text-align: center;
  color: var(--text);
}
[data-theme="dark"] .excel-table th, [data-theme="dark"] .excel-table td {
  border-right: 1px solid rgba(255,255,255,0.06);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.excel-table th {
  background: rgba(255, 255, 255, 0.85);
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
[data-theme="dark"] .excel-table th {
  background: rgba(30, 41, 59, 0.85);
}

/* Fixed First Column - FIX OVERLAP */
.excel-table .col-metric {
  position: sticky;
  left: 0;
  /* Use a solid, opaque background so scrolling cells do not bleed through */
  background-color: #ffffff;
  z-index: 20;
  text-align: left;
  min-width: 280px;
  font-weight: 600;
  box-shadow: 2px 0 5px rgba(0,0,0,0.03);
}
[data-theme="dark"] .excel-table .col-metric {
  background-color: #1e293b;
  box-shadow: 2px 0 5px rgba(0,0,0,0.2);
}

/* Ensure top-left corner stays above both row/col headers */
.excel-table thead tr:first-child th.col-metric {
  z-index: 30;
}
.excel-table thead tr:nth-child(2) th.col-metric {
  z-index: 30;
  top: 45px; /* approx height of first row */
}

/* Row Hover */
.excel-table tbody tr {
  transition: background 0.2s ease;
}
.excel-table tbody tr:hover td {
  background-color: rgba(26, 115, 232, 0.05);
}
[data-theme="dark"] .excel-table tbody tr:hover td {
  background-color: rgba(255, 255, 255, 0.05);
}
.excel-table tbody tr:hover td.col-metric {
  /* Must remain solid on hover */
  background-color: #f1f5f9;
}
[data-theme="dark"] .excel-table tbody tr:hover td.col-metric {
  background-color: #334155;
}

/* Collapsible Columns */
.col-collapsed {
  display: none !important;
}
.expand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
  font-size: 0.75rem;
  color: var(--blue);
  cursor: pointer;
  background: var(--blue-soft);
  width: 20px; height: 20px;
  border-radius: 50%;
  transition: all 0.2s ease;
}
.expand-icon:hover {
  background: var(--blue);
  color: #fff;
}
"""

patched = content[:content.find(start_marker)] + new_css

with open('styles.css', 'w', encoding='utf-8') as f:
    f.write(patched)

print("Patched styles.css with liquid glass UI!")
