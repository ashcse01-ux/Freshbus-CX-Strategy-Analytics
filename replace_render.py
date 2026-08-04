import re

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

new_logic = """function renderExcelTable(data) {
    const rowMonths = $('excelRowMonths');
    const rowWeeks = $('excelRowWeeks');
    const rowDays = $('excelRowDays');
    const tbody = $('excelTableBody');
    
    rowMonths.innerHTML = '<th class="col-metric" rowspan="3" style="z-index: 50; top:0; text-align: center; font-family: \\'Inter\\', sans-serif; font-size: 1.1rem; padding: 20px;">Metrics</th>';
    rowWeeks.innerHTML = '';
    rowDays.innerHTML = '';
    tbody.innerHTML = '';

    if (!data.months || data.months.length === 0) return;

    data.months.forEach((m, mIdx) => {
      const mClass = `m-${mIdx}`;
      let mCols = 0;
      
      const shortMonth = m.month_label.split(' ')[0].substring(0, 3);
      
      m.weeks.forEach((w, wIdx) => {
        const wClass = `m-${mIdx}-w-${wIdx}`;
        let wCols = w.days.length + 1; // +1 for week total
        
        const weekNum = w.week_label.replace('Week ', 'W');
        const weekHeader = `${weekNum} - ${shortMonth}`;
        
        rowWeeks.innerHTML += `<th class="col-week ${mClass}" data-target="${wClass}" colspan="${wCols}">${weekHeader} <span class="expand-icon">▼</span></th>`;
        
        w.days.forEach(d => {
          rowDays.innerHTML += `<th class="col-day ${wClass}">${d.day_label}</th>`;
        });
        rowDays.innerHTML += `<th class="col-day week-total-col ${wClass}" style="background:rgba(26,115,232,0.1)">${weekNum} Tot</th>`;
        
        mCols += wCols;
      });
      
      // MTD
      rowWeeks.innerHTML += `<th class="col-week ${mClass} mtd-col" rowspan="2" style="background:#10b981; color:#fff;">MTD - ${shortMonth}</th>`;
      mCols += 1;
      
      rowMonths.innerHTML += `<th class="col-month" data-target="${mClass}" colspan="${mCols}">${m.month_label} <span class="expand-icon">▼</span></th>`;
    });

    metricKeys.forEach(mk => {
      let tr = document.createElement('tr');
      tr.innerHTML = `<td class="col-metric" style="font-family: \\'Inter\\', sans-serif; font-weight: 500;">${mk}</td>`;
      
      data.months.forEach((m, mIdx) => {
        const mClass = `m-${mIdx}`;
        m.weeks.forEach((w, wIdx) => {
          const wClass = `m-${mIdx}-w-${wIdx}`;
          w.days.forEach(d => {
            const val = d.metrics[mk] !== undefined ? d.metrics[mk] : '-';
            tr.innerHTML += `<td class="col-day ${wClass}">${val}</td>`;
          });
          const wTot = w.total[mk] !== undefined ? w.total[mk] : '-';
          tr.innerHTML += `<td class="col-day week-total-col ${wClass}" style="background:rgba(26,115,232,0.05)">${wTot}</td>`;
        });
        const mTot = m.mtd[mk] !== undefined ? m.mtd[mk] : '-';
        tr.innerHTML += `<td class="col-week ${mClass} mtd-col" style="background:rgba(16,185,129,0.05); font-weight:bold;">${mTot}</td>`;
      });
      
      tbody.appendChild(tr);
    });

    // Setup collapsing logic
    document.querySelectorAll('#excelTable .col-month').forEach(th => {
      th.addEventListener('click', (e) => {
        const targetClass = th.getAttribute('data-target');
        const icon = th.querySelector('.expand-icon');
        const isCollapsed = icon.textContent === '▶';
        
        if (!isCollapsed) {
          document.querySelectorAll(`.${targetClass}`).forEach(el => {
            if (!el.classList.contains('mtd-col')) {
              el.classList.add('col-collapsed');
            }
          });
          icon.textContent = '▶';
          if (!th.getAttribute('data-og-colspan')) th.setAttribute('data-og-colspan', th.getAttribute('colspan'));
          th.setAttribute('colspan', 1);
        } else {
          let newColspan = 1;
          
          document.querySelectorAll(`.col-week.${targetClass}`).forEach(weekTh => {
            if (weekTh.classList.contains('mtd-col')) return;
            
            weekTh.classList.remove('col-collapsed');
            const wIcon = weekTh.querySelector('.expand-icon');
            const weekIsCollapsed = wIcon && wIcon.textContent === '▶';
            
            const wTarget = weekTh.getAttribute('data-target');
            if (!weekIsCollapsed) {
               document.querySelectorAll(`.col-day.${wTarget}`).forEach(day => day.classList.remove('col-collapsed'));
               newColspan += parseInt(weekTh.getAttribute('colspan'));
            } else {
               // When week is collapsed, we still show the week-total-col
               document.querySelectorAll(`.col-day.week-total-col.${wTarget}`).forEach(day => day.classList.remove('col-collapsed'));
               newColspan += 1;
            }
          });
          
          icon.textContent = '▼';
          th.setAttribute('colspan', newColspan);
        }
      });
    });

    document.querySelectorAll('#excelTable .col-week').forEach(th => {
      if (th.classList.contains('mtd-col')) return;
      th.addEventListener('click', (e) => {
        const targetClass = th.getAttribute('data-target');
        const icon = th.querySelector('.expand-icon');
        const isCollapsed = icon.textContent === '▶';
        
        const pClass = Array.from(th.classList).find(c => c.startsWith('m-') && !c.includes('-w-'));
        const pTh = document.querySelector(`.col-month[data-target="${pClass}"]`);
        if (pTh && pTh.querySelector('.expand-icon').textContent === '▶') return;
        
        if (!isCollapsed) {
          // Hide all days except week-total-col
          document.querySelectorAll(`.col-day.${targetClass}`).forEach(el => {
            if(!el.classList.contains('week-total-col')) el.classList.add('col-collapsed');
          });
          icon.textContent = '▶';
          
          const ogSpan = parseInt(th.getAttribute('colspan'));
          if (!th.getAttribute('data-og-colspan')) th.setAttribute('data-og-colspan', ogSpan);
          th.setAttribute('colspan', 1);
          
          if (pTh) {
            pTh.setAttribute('colspan', parseInt(pTh.getAttribute('colspan')) - (ogSpan - 1));
          }
        } else {
          document.querySelectorAll(`.col-day.${targetClass}`).forEach(el => el.classList.remove('col-collapsed'));
          icon.textContent = '▼';
          
          const ogSpan = parseInt(th.getAttribute('data-og-colspan'));
          th.setAttribute('colspan', ogSpan);
          
          if (pTh) {
            pTh.setAttribute('colspan', parseInt(pTh.getAttribute('colspan')) + (ogSpan - 1));
          }
        }
      });
    });
  }"""

pattern = re.compile(r'function renderExcelTable\(data\)\s*\{.*?\n  \}', re.DOTALL)
content = pattern.sub(new_logic, content)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(content)
