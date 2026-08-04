with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
new_logo = '''<div class="lp-logo" style="display:flex; align-items:center; gap:12px; text-decoration:none; flex-shrink:0; margin-bottom:3.5rem;">
  <div class="hdr-lm" style="width:48px; height:48px; border-radius:8px; display:flex; align-items:center; justify-content:center;">
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:100%;">
      <path d="M 32 82 L 32 20 C 32 14, 37 10, 43 10 L 71 10 C 80 10, 84 21, 76 28 L 56 46 L 70 46 C 79 46, 83 57, 75 64 L 43 92 C 35 99, 32 92, 32 85 Z" fill="#FFEA20"/>
    </svg>
  </div>
  <div class="hdr-brand-wrap" style="display: flex; flex-direction: column; justify-content: center; margin-top:-2px;">
    <span class="hdr-ln" style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.8rem; font-weight:800; color:#FFEA20; line-height:1.1; letter-spacing:-0.03em;">Fresh Bus</span>
    <span class="hdr-sub" style="font-size:0.8rem; font-weight:600; color:rgba(255,255,255,0.65); letter-spacing:0.06em; text-transform:uppercase; margin-top:2px;">Analytics Platform</span>
  </div>
</div>'''

html = re.sub(r'<div class="lp-logo">.*?</div>\s*</div>\s*</div>', new_logo, html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
