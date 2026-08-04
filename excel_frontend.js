
  /* =========================================
     EXCEL VIEW MODAL (Flat JSON Version)
  ========================================= */
  const excelModal = $('excelModal');
  const excelViewBtn = $('excelViewBtn');
  const excelCloseBtn = $('excelCloseBtn');
  const excelDownloadBtn = $('excelDownloadBtn');
  const excelLoader = $('excelLoader');
  const excelTable = $('excelTable');
  let flatExcelCache = null;

  if (excelViewBtn) {
    excelViewBtn.addEventListener('click', async () => {
      excelModal.classList.add('show');
      if (!flatExcelCache) {
        await loadFlatExcelData();
      } else {
        renderFlatExcelTable(flatExcelCache);
      }
    });
  }

  if (excelCloseBtn) {
    excelCloseBtn.addEventListener('click', () => {
      excelModal.classList.remove('show');
    });
  }

  // Use flatpickr if available for excel dates
  if (window.flatpickr) {
    flatpickr('#excel_start_date', { dateFormat: "Y-m-d" });
    flatpickr('#excel_end_date', { dateFormat: "Y-m-d" });
  }

  // Re-render when dates change
  ['excel_start_date', 'excel_end_date'].forEach(id => {
      const el = $(id);
      if (el) el.addEventListener('change', () => {
          if (flatExcelCache) renderFlatExcelTable(flatExcelCache);
      });
  });

  if (excelDownloadBtn) {
    excelDownloadBtn.addEventListener('click', () => {
      alert("Excel download will use the date filters soon.");
    });
  }

  async function loadFlatExcelData() {
    if(excelLoader) excelLoader.style.display = 'block';
    if(excelTable) excelTable.style.opacity = '0.3';
    try {
      const res = await fetch('/api/excel/view?parent_campaign=Inbound');
      const data = await res.json();
      flatExcelCache = data;
      renderFlatExcelTable(data);
    } catch (e) {
      console.error(e);
      alert('Error loading excel view data');
    }
    if(excelLoader) excelLoader.style.display = 'none';
    if(excelTable) excelTable.style.opacity = '1';
  }

  function renderFlatExcelTable(data) {
    if (!data || !data.columns) return;
    
    const thead = excelTable.querySelector('thead');
    const tbody = excelTable.querySelector('tbody') || $('excelTableBody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    // Read date filters
    let sStr = $('excel_start_date')?.value;
    let eStr = $('excel_end_date')?.value;
    let startDt = sStr ? new Date(sStr) : null;
    let endDt = eStr ? new Date(eStr) : null;
    if (startDt) startDt.setHours(0,0,0,0);
    if (endDt) endDt.setHours(23,59,59,999);

    // Determine visibility of each column
    let colVisible = new Array(data.columns.length).fill(true);
    
    let lastSummaryIdx = -1;
    for (let i = 0; i < data.columns.length; i++) {
        let cDate = data.dates[i];
        if (cDate && cDate.trim() !== '') {
            // It's a day
            let d = new Date(cDate);
            if (isNaN(d)) {
                // handle DD-MMM-YYYY or other formats if needed, assuming M/D/YYYY
            }
            if (!isNaN(d)) {
                if (startDt && d < startDt) colVisible[i] = false;
                if (endDt && d > endDt) colVisible[i] = false;
            }
        } else {
            // It's a summary column (Week or MTD)
            // check if ANY day since lastSummaryIdx is visible
            let anyVisible = false;
            for (let j = lastSummaryIdx + 1; j < i; j++) {
                if (data.dates[j] && colVisible[j]) {
                    anyVisible = true;
                    break;
                }
            }
            if (!anyVisible && startDt) {
                colVisible[i] = false; // Hide summary if all its days are hidden and a filter is active
            }
            lastSummaryIdx = i;
        }
    }

    // Header Rows
    // Top header: the dates (or summary label)
    let trDates = document.createElement('tr');
    trDates.innerHTML = `<th class="col-metric" rowspan="2">Metrics</th>`;
    
    // Bottom header: the weekday name (or summary label again)
    let trCols = document.createElement('tr');
    
    // Collapsible Logic: 
    let currentGroupId = 0;
    
    for (let i = 0; i < data.columns.length; i++) {
        if (!colVisible[i]) continue;
        
        let cName = data.columns[i];
        let cDate = data.dates[i];
        
        let isSummary = (!cDate || cDate.trim() === '');
        let bgStyle = isSummary ? (cName.includes('MTD') ? 'background:rgba(16,185,129,0.8);' : 'background:rgba(26,115,232,0.5);') : '';
        
        if (isSummary) {
            trDates.innerHTML += `<th class="summary-col grp-summary-${currentGroupId}" data-group="${currentGroupId}" rowspan="2" style="${bgStyle}; cursor:pointer;">${cName} <span class="expand-icon">[+]</span></th>`;
            currentGroupId++;
        } else {
            trDates.innerHTML += `<th class="day-col grp-day-${currentGroupId} col-collapsed" style="${bgStyle}">${cDate}</th>`;
            trCols.innerHTML += `<th class="day-col grp-day-${currentGroupId} col-collapsed" style="${bgStyle}">${cName}</th>`;
        }
    }
    
    thead.appendChild(trDates);
    thead.appendChild(trCols);

    // Body Rows
    data.metrics.forEach(m => {
        let tr = document.createElement('tr');
        tr.innerHTML = `<td class="col-metric">${m.name}</td>`;
        
        let gId = 0;
        for (let i = 0; i < data.columns.length; i++) {
            if (!colVisible[i]) continue;
            let val = m.values[i] || '-';
            let cDate = data.dates[i];
            let isSummary = (!cDate || cDate.trim() === '');
            let bgStyle = isSummary ? (data.columns[i].includes('MTD') ? 'background:rgba(16,185,129,0.1); font-weight:bold;' : 'background:rgba(26,115,232,0.1); font-weight:bold;') : '';
            
            if (isSummary) {
                tr.innerHTML += `<td class="summary-col grp-summary-${gId}" style="${bgStyle}">${val}</td>`;
                gId++;
            } else {
                tr.innerHTML += `<td class="day-col grp-day-${gId} col-collapsed" style="${bgStyle}">${val}</td>`;
            }
        }
        tbody.appendChild(tr);
    });

    // Add Collapse/Expand interactions (specifically scoped to this table)
    excelTable.querySelectorAll('.summary-col[data-group]').forEach(th => {
        th.addEventListener('click', () => {
            const gid = th.getAttribute('data-group');
            const icon = th.querySelector('.expand-icon');
            if(!icon) return;
            const isCollapsed = icon.textContent.includes('+');
            
            excelTable.querySelectorAll(`.grp-day-${gid}`).forEach(el => {
                if (isCollapsed) el.classList.remove('col-collapsed');
                else el.classList.add('col-collapsed');
            });
            
            icon.textContent = isCollapsed ? '[-]' : '[+]';
        });
    });
  }
