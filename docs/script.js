/* ═══════════════════════════════════════════════════════════════
   FRESHBUS ANALYTICS PLATFORM — INBOUND INTELLIGENCE SCRIPT
   Target file: /inbound (served from inbound.html)
   ═══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ─────────────────────────────────────────────────────
     GUARD — only initialise on /inbound
  ─────────────────────────────────────────────────────── */
  if (!window.location.pathname.includes('/inbound')) return;

  /* ─────────────────────────────────────────────────────
     STATE
  ─────────────────────────────────────────────────────── */
  let viewType = 'daily';
  let currentDist = 'dispositions';
  let apiData = null;

  let trendChart = null;
  let distChart  = null;
  let slAlChart  = null;
  let abnChart   = null;
  let qaRadar    = null;
  let ttaBucketChart = null;
  let durBucketChart = null;
  let ratingDistChart = null;

  /* ─────────────────────────────────────────────────────
     HELPERS
  ─────────────────────────────────────────────────────── */
  const $ = id => document.getElementById(id);
  const qs = (sel, ctx = document) => ctx.querySelector(sel);
  const qsa = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  function setText(id, val) {
    const el = $(id);
    if (el) el.textContent = (val !== undefined && val !== null) ? val : '—';
  }

  function setValWithUnit(id, val, unit = '') {
    const el = $(id);
    if (!el) return;
    if (val !== undefined && val !== null) {
      el.innerHTML = `${val}<span class="mc-unit">${unit}</span>`;
    } else {
      el.textContent = '—';
    }
  }

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function themeColors() {
    const dark = isDark();
    return {
      text:   dark ? '#94a3b8' : '#6b7280',
      grid:   dark ? '#1e2d45' : '#e2e8f3',
      blue:   '#1A73E8',
      green:  '#16a34a',
      red:    '#dc2626',
      amber:  '#d97706',
      yellow: '#FBBC04',
      purple: '#7c3aed',
    };
  }

  function destroyChart(ref) { if (ref) { try { ref.destroy(); } catch(e) {} } return null; }

  /* ─────────────────────────────────────────────────────
     THEME TOGGLE
  ─────────────────────────────────────────────────────── */
  const themeBtn = $('themeBtn');
  const themeIco = $('themeIco');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const isDarkNow = isDark();
      document.documentElement.setAttribute('data-theme', isDarkNow ? 'light' : 'dark');
      // Update icon
      if (themeIco) {
        themeIco.innerHTML = isDarkNow
          ? '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'
          : '<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>';
      }
      if (apiData) redrawAllCharts();
    });
  }

  /* ─────────────────────────────────────────────────────
     DATE PICKERS (Flatpickr)
  ─────────────────────────────────────────────────────── */
  const fpOpts = { dateFormat: 'Y-m-d', allowInput: false };
  let fpStart, fpEnd;
  if (window.flatpickr) {
    fpStart = flatpickr('#filter_start_date', {
      ...fpOpts,
      onChange: () => fetchData()
    });
    fpEnd = flatpickr('#filter_end_date', {
      ...fpOpts,
      onChange: () => fetchData()
    });
  }

  /* ─────────────────────────────────────────────────────
     VIEW PERIOD BUTTONS
  ─────────────────────────────────────────────────────── */
  qsa('.hdr-vbtn').forEach(btn => {
    btn.addEventListener('click', () => {
      qsa('.hdr-vbtn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      viewType = btn.dataset.view;
      fetchData();
    });
  });

  /* ─────────────────────────────────────────────────────
     METRIC BUNCH SEGMENT SWITCHER
  ─────────────────────────────────────────────────────── */
  qsa('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      qsa('.seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const target = btn.dataset.bunch;
      qsa('.bunch').forEach(b => b.classList.remove('active'));
      const el = $(`bunch-${target}`);
      if (el) el.classList.add('active');
    });
  });

  /* ─────────────────────────────────────────────────────
     DISTRIBUTION CHART SEGMENT
  ─────────────────────────────────────────────────────── */
  qsa('.ph-seg[data-dist]').forEach(btn => {
    btn.addEventListener('click', () => {
      qsa('.ph-seg[data-dist]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentDist = btn.dataset.dist;
      if (apiData) renderDistChart(apiData.distributions?.[currentDist]);
    });
  });

  /* ─────────────────────────────────────────────────────
     SIDEBAR FILTERS
  ─────────────────────────────────────────────────────── */
  $('applyBtn')?.addEventListener('click', fetchData);
  $('refreshBtn')?.addEventListener('click', () => { fetchData(); animateSpin('refreshBtn'); });
  $('clearBtn')?.addEventListener('click', () => {
    ['f_agent','f_campaign','f_status','f_disposition','f_skill','f_call_type','f_hangup_by','f_dial_status','f_transfer_details','f_ratings'].forEach(id => {
      const el = $(id); 
      if (el) {
        if (id === 'f_call_type') el.value = 'inbound';
        else el.value = '';
      }
    });
    fpStart?.clear(); fpEnd?.clear();
    fetchData();
  });

  $('syncBtn')?.addEventListener('click', async () => {
    const btn = $('syncBtn');
    btn.disabled = true; btn.textContent = 'Syncing…';
    try { await fetch('/api/sync/run', { method: 'POST' }); } catch(e) {}
    btn.disabled = false; btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:13px"><path d="M3 12a9 9 0 019-9 9 9 0 016.36 2.64L21 9M21 3v6h-6"/></svg> Run Sync';
    await fetchData();
  });

  $('wipeBtn')?.addEventListener('click', async () => {
    if (!confirm('⚠️ This will permanently delete ALL data. Are you absolutely sure?')) return;
    try { await fetch('/api/sync/wipe', { method: 'DELETE' }); alert('Database wiped.'); } catch(e) {}
  });

  function animateSpin(id) {
    const el = $(id);
    if (!el) return;
    el.style.transition = 'transform 0.5s';
    el.style.transform = 'rotate(360deg)';
    setTimeout(() => { el.style.transform = ''; }, 600);
  }

  /* ─────────────────────────────────────────────────────
     LOAD FILTER OPTIONS
  ─────────────────────────────────────────────────────── */
  async function loadFilters() {
    try {
      const r = await fetch('/api/metrics/filters?parent_campaign=Inbound');
      if (!r.ok) return;
      const d = await r.json();
      const fillSelect = (id, values) => {
        const el = $(id); if (!el) return;
        const cur = el.value;
        el.innerHTML = '<option value="">All</option>';
        (values || []).forEach(v => {
          const o = document.createElement('option');
          o.value = v; o.textContent = v;
          if (v === cur) o.selected = true;
          el.appendChild(o);
        });
      };
      fillSelect('f_agent', d.agents);
      fillSelect('f_campaign', d.campaigns);
      fillSelect('f_status', d.statuses);
      fillSelect('f_disposition', d.dispositions);
      fillSelect('f_skill', d.skills);
      fillSelect('f_call_type', d.call_types);
      fillSelect('f_hangup_by', d.hangups);
      fillSelect('f_dial_status', d.dial_statuses);
    } catch(e) { console.warn('Filters load failed:', e); }
  }

  /* ─────────────────────────────────────────────────────
     CORE DATA FETCH
  ─────────────────────────────────────────────────────── */
  async function fetchData() {
    try {
      const params = new URLSearchParams();
      params.set('parent_campaign', 'Inbound');
      params.set('view_type', viewType);

      const agent = $('f_agent')?.value;
      const camp  = $('f_campaign')?.value;
      const stat  = $('f_status')?.value;
      const disp  = $('f_disposition')?.value;
      const skill = $('f_skill')?.value;
      const ctype = $('f_call_type')?.value;
      const hby   = $('f_hangup_by')?.value;
      const dstat = $('f_dial_status')?.value;
      const tdet  = $('f_transfer_details')?.value;
      const rate  = $('f_ratings')?.value;

      if (agent) params.set('agent', agent);
      if (camp)  params.set('campaign', camp);
      if (stat)  params.set('status', stat);
      if (disp)  params.set('disposition', disp);
      if (skill) params.set('skill', skill);
      if (ctype) params.set('call_type', ctype);
      if (hby)   params.set('hangup_by', hby);
      if (dstat) params.set('dial_status', dstat);
      if (tdet)  params.set('transfer_details', tdet);
      if (rate)  params.set('rating', rate);

      const sd = $('filter_start_date')?.value;
      const ed = $('filter_end_date')?.value;
      if (sd) params.set('start_date', sd);
      if (ed) params.set('end_date', ed);

      const res = await fetch('/api/metrics/aggregate?' + params.toString());
      if (!res.ok) { console.error('API error', res.status); return; }
      apiData = await res.json();
      renderDashboard(apiData);
    } catch(e) { console.error('Fetch failed:', e); }
  }

  /* ─────────────────────────────────────────────────────
     RENDER DASHBOARD
  ─────────────────────────────────────────────────────── */
  function renderDashboard(data) {
    const s = data.summary || {};
    const v = s.volume || {};
    const svc = s.service || {};
    const eff = s.efficiency || {};
    const fail = s.failure || {};
    const jrny = s.journey || {};

    /* --- Hero KPIs --- */
    setText('h-total',    v.total_offered);
    setText('h-sl_pct',   svc.sl_pct);
    setText('h-sl_calls_sub', `${svc.sl_calls || '—'} calls answered ≤30s`);
    setText('h-net_abn',  fail.net_abn);
    setText('h-net_pct',  fail.net_abn_pct);
    setText('h-aht',      eff.aht);

    /* --- Records badge --- */
    if (data.total_rows !== undefined) {
      setText('recordsBadge', `${data.total_rows.toLocaleString()} records`);
    }

    /* --- BUNCH 1: Volume & Funnel --- */
    setText('m-answered',              v.answered);
    setText('m-overall_abn',           fail.overall_abn);
    setText('m-al_pct',                svc.al_pct);
    setText('m-wh_offered',            v.wh_offered);
    setText('m-wh_answered',           v.wh_answered);
    setText('m-travel_update_offered', v.travel_update_offered);
    setText('m-inbound_wh_offered',    v.inbound_wh_offered);

    /* --- BUNCH 2: Service & Ops --- */
    setText('m-agent_offered',  v.agent_offered);
    setText('m-sl_calls',       svc.sl_calls);
    setText('m-sl_pct',         svc.sl_pct);
    setText('m-avg_wait',       svc.avg_wait);
    setText('m-avg_hold',       svc.avg_hold);
    setText('m-on_hold',        svc.on_hold);
    setText('m-long_calls',     eff.long_calls);
    setText('m-long_call_pct',  eff.long_call_pct);

    /* --- BUNCH 3: Abandonment --- */
    setText('m-net_abn',         fail.net_abn);
    setText('m-net_abn_pct',     fail.net_abn_pct);
    setText('m-short_abn',       fail.short_abn);
    setText('m-short_pct',       fail.short_pct);
    setText('m-gross_abn_pct',   fail.gross_abn_pct);
    setText('m-queue_level',     fail.queue_level);

    /* --- BUNCH 4: Exceptions & QA --- */
    setText('m-same_day_repeat',       eff.same_day_repeat);
    setText('m-repeat_pct',            eff.repeat_pct);
    setText('m-disp_repeat_pct',       jrny.disp_repeat_pct);
    setText('m-call_drop',             fail.call_drop);
    setText('m-blank_call',            fail.blank_call);
    setText('m-call_back',             fail.call_back);
    setText('m-agent_disconnected',    fail.agent_disconnected);
    setText('m-agent_disconnected_pct',fail.agent_disconnected_pct);

    /* --- Charts --- */
    redrawAllCharts();

    /* --- Top 10 Dispositions --- */
    renderTop10(data.distributions?.dispositions);
  }

  /* ─────────────────────────────────────────────────────
     REDRAW ALL CHARTS
  ─────────────────────────────────────────────────────── */
  function redrawAllCharts() {
    if (!apiData) return;
    renderTrendChart(apiData.chart_data);
    renderDistChart(apiData.distributions?.[currentDist]);
    renderHeatmap(apiData.heatmap);
    renderSlAlChart(apiData);
    renderAbnChart(apiData);
    renderQaRadar(apiData);
    renderTtaBucketChart(apiData.buckets?.tta);
    renderDurBucketChart(apiData.buckets?.duration);
    renderRatingDistChart(apiData.buckets?.ratings);
  }

  /* ─────────────────────────────────────────────────────
     CHART 1: VOLUME vs ABANDONMENT TREND (Mixed bar/line)
  ─────────────────────────────────────────────────────── */
  function renderTrendChart(series) {
    trendChart = destroyChart(trendChart);
    const ctx = $('trendChart')?.getContext('2d');
    if (!ctx || !series?.length) return;
    const th = themeColors();

    trendChart = new Chart(ctx, {
      data: {
        labels: series.map(d => d.label),
        datasets: [
          {
            type: 'line', label: 'Offered',
            data: series.map(d => d.total || 0),
            borderColor: th.blue, backgroundColor: 'rgba(26,115,232,0.08)',
            borderWidth: 2.5, fill: true, tension: 0.4,
            pointRadius: 3, pointHoverRadius: 6, yAxisID: 'y'
          },
          {
            type: 'line', label: 'Answered',
            data: series.map(d => d.answered || 0),
            borderColor: th.green,
            borderWidth: 2, fill: false, tension: 0.4,
            borderDash: [5, 4], pointRadius: 2, pointHoverRadius: 5, yAxisID: 'y'
          },
          {
            type: 'bar', label: 'Abandoned',
            data: series.map(d => d.abn || 0),
            backgroundColor: 'rgba(220,38,38,0.6)',
            borderRadius: 4, yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: th.text, usePointStyle: true, boxWidth: 8, padding: 18 } },
          tooltip: { padding: 10, cornerRadius: 8 }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: th.text, maxRotation: 0 } },
          y: {
            position: 'left', grid: { color: th.grid },
            ticks: { color: th.text }, title: { display: true, text: 'Calls', color: th.text, font: { size: 11 } }
          },
          y1: {
            position: 'right', grid: { drawOnChartArea: false },
            ticks: { color: th.red }, title: { display: true, text: 'Abandoned', color: th.red, font: { size: 11 } }
          }
        }
      }
    });
  }

  /* ─────────────────────────────────────────────────────
     CHART 2: DISTRIBUTION (Doughnut)
  ─────────────────────────────────────────────────────── */
  function renderDistChart(distObj) {
    distChart = destroyChart(distChart);
    const ctx = $('distChart')?.getContext('2d');
    if (!ctx || !distObj) return;
    const th = themeColors();
    const palette = [th.blue, th.yellow, th.green, th.red, th.purple, '#0ea5e9', '#f43f5e', '#8b5cf6', '#06b6d4', '#84cc16'];
    const labels = Object.keys(distObj).slice(0, 10);
    const values = Object.values(distObj).slice(0, 10);

    distChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data: values, backgroundColor: palette, borderWidth: 0, hoverOffset: 10 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            position: 'right',
            labels: { color: th.text, usePointStyle: true, boxWidth: 8, padding: 14, font: { size: 11 } }
          }
        }
      }
    });
  }

  /* ─────────────────────────────────────────────────────
     HEATMAP: Day × Hour grid
  ─────────────────────────────────────────────────────── */
  function renderHeatmap(heatmapData) {
    const hdrs = $('hmHdrs');
    const rows = $('hmRows');
    if (!hdrs || !rows) return;
    hdrs.innerHTML = '';
    rows.innerHTML = '';

    if (!heatmapData?.length) return;

    const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const maxVal = Math.max(...heatmapData.flat(), 1);
    const tip = $('hmTip');

    /* Hour labels */
    const blank = document.createElement('div');
    blank.className = 'hm-h-lbl';
    hdrs.appendChild(blank);
    for (let h = 0; h < 24; h++) {
      const d = document.createElement('div');
      d.className = 'hm-h-lbl';
      d.textContent = h % 3 === 0 ? h : '';
      hdrs.appendChild(d);
    }

    /* Rows */
    heatmapData.forEach((row, dIdx) => {
      const rowEl = document.createElement('div');
      rowEl.className = 'hm-row-wrap';

      const dayLabel = document.createElement('div');
      dayLabel.className = 'hm-day-lbl';
      dayLabel.textContent = DAYS[dIdx] || dIdx;
      rowEl.appendChild(dayLabel);

      row.forEach((val, h) => {
        const cell = document.createElement('div');
        cell.className = 'hm-cell';
        if (val > 0) {
          const ratio = val / maxVal;
          // Yellow-heat gradient: low blues → yellow → orange-red
          if (ratio < 0.25)      cell.style.background = `rgba(147,197,253,${ratio * 4 * 0.75 + 0.1})`;
          else if (ratio < 0.5)  cell.style.background = `rgba(96,165,250,${0.5 + ratio * 0.5})`;
          else if (ratio < 0.75) cell.style.background = `rgba(251,188,4,${0.5 + ratio * 0.5})`;
          else                   cell.style.background = `rgba(234,88,12,${0.6 + ratio * 0.4})`;
        }

        cell.addEventListener('mouseenter', e => {
          if (tip) {
            tip.style.display = 'block';
            tip.innerHTML = `<strong>${DAYS[dIdx]}</strong> at <strong>${h}:00 – ${h + 1}:00</strong><br>${val} calls`;
            tip.style.left = (e.clientX + 12) + 'px';
            tip.style.top =  (e.clientY + 12) + 'px';
          }
        });
        cell.addEventListener('mousemove', e => {
          if (tip) { tip.style.left = (e.clientX + 12) + 'px'; tip.style.top = (e.clientY + 12) + 'px'; }
        });
        cell.addEventListener('mouseleave', () => { if (tip) tip.style.display = 'none'; });
        rowEl.appendChild(cell);
      });
      rows.appendChild(rowEl);
    });
  }

  /* ─────────────────────────────────────────────────────
     CHART 3: SL% vs AL% Horizontal Bar
  ─────────────────────────────────────────────────────── */
  function renderSlAlChart(data) {
    slAlChart = destroyChart(slAlChart);
    const ctx = $('slAlChart')?.getContext('2d');
    if (!ctx) return;
    const th = themeColors();
    const sl = parseFloat(data?.summary?.service?.sl_pct) || 0;
    const al = parseFloat(data?.summary?.service?.al_pct) || 0;

    slAlChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Service Level (SL%)', 'Answer Level (AL%)'],
        datasets: [
          {
            data: [sl, al],
            backgroundColor: [
              sl >= 80 ? th.green : sl >= 60 ? th.amber : th.red,
              al >= 80 ? th.blue  : al >= 60 ? th.amber : th.red
            ],
            borderRadius: 6, barThickness: 32
          },
          {
            data: [100, 100],
            backgroundColor: isDark() ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.04)',
            borderRadius: 6, barThickness: 32
          }
        ]
      },
      options: {
        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => ` ${ctx.raw}%` } }
        },
        scales: {
          x: { min: 0, max: 100, grid: { color: th.grid }, ticks: { color: th.text, callback: v => v + '%' } },
          y: { grid: { display: false }, ticks: { color: th.text, font: { weight: '600' } } }
        }
      }
    });
  }

  /* ─────────────────────────────────────────────────────
     CHART 4: Abandonment Breakdown (Doughnut)
  ─────────────────────────────────────────────────────── */
  function renderAbnChart(data) {
    abnChart = destroyChart(abnChart);
    const ctx = $('abnChart')?.getContext('2d');
    if (!ctx) return;
    const th = themeColors();
    const f = data?.summary?.failure || {};
    const net   = parseFloat(f.net_abn) || 0;
    const short = parseFloat(f.short_abn) || 0;
    const queue = parseFloat(f.queue_level) || 0;

    abnChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Net Abandoned', 'Short Call Abn', 'Queue Failure'],
        datasets: [{
          data: [net, short, queue],
          backgroundColor: [th.red, th.amber, th.purple],
          borderWidth: 0, hoverOffset: 10
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: '68%',
        plugins: {
          legend: { position: 'bottom', labels: { color: th.text, usePointStyle: true, boxWidth: 8, padding: 14 } }
        }
      }
    });
  }

  /* ─────────────────────────────────────────────────────
     CHART 5: Quality Exception Radar
  ─────────────────────────────────────────────────────── */
  function renderQaRadar(data) {
    qaRadar = destroyChart(qaRadar);
    const ctx = $('qaRadar')?.getContext('2d');
    if (!ctx) return;
    const th = themeColors();
    const f = data?.summary?.failure || {};
    const e = data?.summary?.efficiency || {};

    const vals = [
      Math.min(parseFloat(f.net_abn_pct) || 0, 30),     // cap at 30 for radar clarity
      Math.min(parseFloat(f.gross_abn_pct) || 0, 30),
      Math.min(parseFloat(e.long_call_pct) || 0, 25),
      Math.min(parseFloat(e.repeat_pct) || 0, 20),
      Math.min(parseFloat(f.agent_disconnected_pct) || 0, 15),
    ];

    qaRadar = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: ['Net Abn%', 'Gross Abn%', 'Long Call%', 'Repeat%', 'Agent Disc%'],
        datasets: [{
          label: 'Exception Levels',
          data: vals,
          backgroundColor: 'rgba(220,38,38,0.1)',
          borderColor: th.red,
          borderWidth: 2,
          pointBackgroundColor: th.red,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { labels: { color: th.text, boxWidth: 8 } } },
        scales: {
          r: {
            grid: { color: th.grid },
            ticks: { color: th.text, font: { size: 10 }, backdropColor: 'transparent' },
            pointLabels: { color: th.text, font: { size: 11, weight: '600' } }
          }
        }
      }
    });
  }

  function renderTtaBucketChart(buckets) {
    ttaBucketChart = destroyChart(ttaBucketChart);
    const ctx = $('ttaBucketChart')?.getContext('2d');
    if (!ctx) return;
    const th = themeColors();
    const labels = Object.keys(buckets || {});
    const values = Object.values(buckets || {});
    
    const colors = [
      'rgba(22, 163, 74, 0.7)',
      'rgba(251, 188, 4, 0.7)',
      'rgba(217, 119, 6, 0.7)',
      'rgba(220, 38, 38, 0.7)',
      'rgba(153, 27, 27, 0.7)'
    ];

    ttaBucketChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels.length ? labels : ['0-10s', '11-30s', '31-60s', '1-2m', '>2m'],
        datasets: [{
          label: 'Calls',
          data: values.length ? values : [0, 0, 0, 0, 0],
          backgroundColor: colors,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Calls: ${ctx.raw}`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: th.text, font: { size: 9 } } },
          y: { grid: { color: th.grid }, ticks: { color: th.text, font: { size: 9 }, precision: 0 } }
        }
      }
    });
  }

  function renderDurBucketChart(buckets) {
    durBucketChart = destroyChart(durBucketChart);
    const ctx = $('durBucketChart')?.getContext('2d');
    if (!ctx) return;
    const th = themeColors();
    const labels = Object.keys(buckets || {});
    const values = Object.values(buckets || {});
    
    const colors = [
      'rgba(45, 212, 191, 0.7)',
      'rgba(20, 184, 166, 0.7)',
      'rgba(13, 148, 136, 0.7)',
      'rgba(9, 79, 72, 0.7)',
      'rgba(4, 47, 43, 0.7)'
    ];

    durBucketChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels.length ? labels : ['<1m', '1-3m', '3-5m', '5-10m', '>10m'],
        datasets: [{
          label: 'Calls',
          data: values.length ? values : [0, 0, 0, 0, 0],
          backgroundColor: colors,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Calls: ${ctx.raw}`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: th.text, font: { size: 9 } } },
          y: { grid: { color: th.grid }, ticks: { color: th.text, font: { size: 9 }, precision: 0 } }
        }
      }
    });
  }

  function renderRatingDistChart(buckets) {
    ratingDistChart = destroyChart(ratingDistChart);
    const ctx = $('ratingDistChart')?.getContext('2d');
    if (!ctx) return;
    const th = themeColors();
    
    const labels = ['0 ★', '1 ★', '2 ★', '3 ★', '4 ★', '5 ★'];
    const values = [
      buckets?.['0'] || 0,
      buckets?.['1'] || 0,
      buckets?.['2'] || 0,
      buckets?.['3'] || 0,
      buckets?.['4'] || 0,
      buckets?.['5'] || 0
    ];
    
    const bgColors = [
      'rgba(220, 38, 38, 0.7)',
      'rgba(239, 68, 68, 0.7)',
      'rgba(249, 115, 22, 0.7)',
      'rgba(245, 158, 11, 0.7)',
      'rgba(234, 179, 8, 0.7)',
      'rgba(16, 185, 129, 0.7)'
    ];

    ratingDistChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Feedback Count',
          data: values,
          backgroundColor: bgColors,
          borderColor: bgColors.map(c => c.replace('0.7', '1')),
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Rating ${ctx.label}: ${ctx.raw} calls`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: th.text, font: { size: 10, weight: '600' } } },
          y: { grid: { color: th.grid }, ticks: { color: th.text, font: { size: 9 }, precision: 0 } }
        }
      }
    });
  }

  /* ─────────────────────────────────────────────────────
     TOP 10 DISPOSITIONS LIST
  ─────────────────────────────────────────────────────── */
  function renderTop10(dispObj) {
    const container = $('top10List');
    if (!container) return;
    if (!dispObj || !Object.keys(dispObj).length) {
      container.innerHTML = '<div style="padding:1rem; color:var(--text-m); font-size:0.85rem;">No disposition data available.</div>';
      return;
    }

    // Sort descending, take top 10
    const sorted = Object.entries(dispObj)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    const maxCount = sorted[0][1] || 1;
    const total = sorted.reduce((s, [, v]) => s + v, 0);

    container.innerHTML = '';
    sorted.forEach(([name, count], idx) => {
      const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0.0';
      const barW = Math.round((count / maxCount) * 100);

      const row = document.createElement('div');
      row.className = 'top-10-row';
      row.innerHTML = `
        <div class="top-10-rank${idx < 3 ? ' gold' : ''}">${idx + 1}</div>
        <div class="top-10-name">${name || 'Unknown'}</div>
        <div class="top-10-bar-wrap">
          <div class="top-10-bar" style="width:${barW}%;background:${idx === 0 ? '#FBBC04' : '#1A73E8'}"></div>
        </div>
        <div class="top-10-count">${count.toLocaleString()}</div>
        <div class="top-10-pct">${pct}%</div>
      `;
      container.appendChild(row);
    });
  }

  /* ─────────────────────────────────────────────────────
     BOOT
  ─────────────────────────────────────────────────────── */
  async function init() {
    qsa('.sidebar select').forEach(select => {
      select.addEventListener('change', fetchData);
    });
    await loadFilters();
    await fetchData();
  }

  init();

})();
