import re

with open('d:/Freshbus-CX-Strategy-Analytics/freshdesk_clean.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace colors
html = html.replace('--blue:#095FF0;', '--blue:#0c4dc3;')
html = html.replace('--yellow:#FAE823;', '--yellow:#FFEA20;')

# Replace logo
svg_logo = '''<svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="height:27px;">
          <path d="M 32 82 L 32 20 C 32 14, 37 10, 43 10 L 71 10 C 80 10, 84 21, 76 28 L 56 46 L 70 46 C 79 46, 83 57, 75 64 L 43 92 C 35 99, 32 92, 32 85 Z" fill="#FFEA20"/>
        </svg>'''
html = re.sub(r'<img src="data:image/png;base64,.*?" alt="FreshBus">', svg_logo, html, flags=re.DOTALL)

# Make app visible by default and remove login screen
html = html.replace('#app{display:none;', '#app{display:flex;')
html = re.sub(r'<div id="loginScreen">.*?</div>\s*<div id="app">', '<div id="app" class="on">', html, flags=re.DOTALL)

# Inject fetch logic into initApp
new_init = '''function initApp(){
  document.getElementById('app').style.opacity = '0.5';
  Promise.all([
    fetch('/api/helpdesk/raw_hd').then(r=>r.json()),
    fetch('/api/helpdesk/raw_hda').then(r=>r.json())
  ]).then(([hd, hda]) => {
    RAW_HD = hd;
    RAW_HDA = hda;
    document.getElementById('app').style.opacity = '1';
    buildPhoneDateSet();
    populateFilters();
    renderOv();
    document.getElementById('d1-from').value='2026-01-01';
    document.getElementById('d1-to').value='2026-01-31';
    document.getElementById('d1-preset').value='jan';
    renderD1(); renderD2(); renderHDT(); renderHDAT();
  }).catch(e => {
    alert("Error fetching data: " + e.message);
  });
}
window.onload = initApp;'''

html = re.sub(r'function initApp\(\)\{.*?\}', new_init, html, flags=re.DOTALL)

with open('d:/Freshbus-CX-Strategy-Analytics/freshdesk.html', 'w', encoding='utf-8') as f:
    f.write(html)
