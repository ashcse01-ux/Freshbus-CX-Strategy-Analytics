import re

with open('styles.css', 'r', encoding='utf-8') as f:
    content = f.read()

# Make the header a beautiful yellow/blue solid background with liquid glass aesthetics
content = re.sub(
    r'\.excel-header \{[\s\S]*?\}',
    """.excel-header {
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, var(--blue-dark) 0%, var(--blue) 60%, var(--yellow) 150%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}""",
    content
)

# Update the header title text colors so they stand out against the dark blue
content = re.sub(
    r'\.excel-title h2 \{[\s\S]*?\}',
    """.excel-title h2 {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}""",
    content
)

content = re.sub(
    r'\.excel-title p \{[\s\S]*?\}',
    """.excel-title p {
  margin: 4px 0 0;
  font-size: 0.95rem;
  color: rgba(255,255,255,0.85);
}""",
    content
)

# Fix col-metric vertical column to be beautiful
content = re.sub(
    r'/\* Fixed First Column - FIX OVERLAP \*/[\s\S]*?\[data-theme="dark"\] \.excel-table \.col-metric \{[\s\S]*?\}',
    """/* Fixed First Column - FIX OVERLAP */
.excel-table .col-metric {
  position: sticky;
  left: 0;
  background: linear-gradient(to right, #f8faff, #ffffff);
  z-index: 20;
  text-align: left;
  min-width: 280px;
  font-weight: 700;
  color: var(--blue-dark);
  box-shadow: 3px 0 10px rgba(0,0,0,0.06);
  border-right: 2px solid var(--blue-soft) !important;
}
[data-theme="dark"] .excel-table .col-metric {
  background: linear-gradient(to right, #111827, #1e293b);
  color: #e2e8f3;
  box-shadow: 3px 0 10px rgba(0,0,0,0.3);
  border-right: 2px solid rgba(255,255,255,0.1) !important;
}""",
    content
)

with open('styles.css', 'w', encoding='utf-8') as f:
    f.write(content)
