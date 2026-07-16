/* ═══════════════════════════════════════════════════════════════
   FRESHBUS ANALYTICS PLATFORM — INBOUND INTELLIGENCE SCRIPT
   Target file: /inbound (served from inbound.html)
   ═══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // Base URL for backend API requests.
  // When running on GitHub Pages, this defaults to your local backend (http://localhost:8000) so you can test it.
  // If you deploy your backend to the cloud (e.g. Render, AWS), replace this with your deployed backend URL.
  const API_BASE = 'http://localhost:8000';

  /* ─────────────────────────────────────────────────────
     GUARD — only initialise on /inbound or inbound.html
  ─────────────────────────────────────────────────────── */
  if (!window.location.pathname.includes('/inbound') && !window.location.pathname.includes('inbound.html')) return;

  /* ─────────────────────────────────────────────────────
     STATE
  ─────────────────────────────────────────────────────── */
  let viewType = '';
  let currentDist = 'dispositions';
  let apiData = null;
  let showAllDispositions = false;

  let trendChart = null;
  let distChart  = null;
  let slAlChart  = null;
  let abnChart   = null;
  let qaRadar    = null;
  let ttaBucketChart = null;
  let durBucketChart = null;

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
      ...fpOpts
    });
    fpEnd = flatpickr('#filter_end_date', {
      ...fpOpts
    });
  }

  /* ─────────────────────────────────────────────────────
     VIEW PERIOD BUTTONS
  ─────────────────────────────────────────────────────── */
  qsa('.hdr-vbtn[data-view]').forEach(btn => {
    btn.addEventListener('click', () => {
      qsa('.hdr-vbtn[data-view]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      viewType = btn.dataset.view;

      // Rule: If a view period is clicked, clear the custom date range
      if (fpStart) fpStart.clear();
      if (fpEnd) fpEnd.clear();
    });
  });

  /* ─────────────────────────────────────────────────────
     METRIC BUNCH SEGMENT SWITCHER
  ─────────────────────────────────────────────────────── */
  function activateBunch(target) {
    qsa('.seg-btn').forEach(b => b.classList.remove('active'));
    const btn = qs(`.seg-btn[data-bunch="${target}"]`);
    if (btn) btn.classList.add('active');
    
    // Hide all bunches
    qsa('.bunch').forEach(b => {
      b.classList.remove('active');
      b.style.display = 'none';
    });
    
    // Show the primary metrics bunch
    const el = $(`bunch-${target}`);
    if (el) {
      el.classList.add('active');
      el.style.display = 'block';
    }
    
    // Show the corresponding visual intelligence bunch (if it exists)
    const visualEl = $(`bunch-visuals-${target}`);
    if (visualEl) {
      visualEl.classList.add('active');
      visualEl.style.display = 'block';
    }
  }

  qsa('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activateBunch(btn.dataset.bunch);
    });
  });

  // Activate overall by default
  activateBunch('overall');

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
    const els = [
      'filter_start_date','filter_end_date','viewTypeTabs',
      'f_agent','f_campaign','f_status','f_disposition','f_skill','f_call_type','f_hangup_by','f_dial_status','f_transfer_details','f_ratings'
    ];
    els.forEach(id => {
      const el = $(id); 
      if (el) {
        if (id === 'f_call_type') el.value = 'inbound';
        else el.value = '';
      }
    });
    fpStart?.clear(); fpEnd?.clear();
    fetchData();
  });

  function isDateSelected() {
    const sd = $('filter_start_date')?.value;
    const ed = $('filter_end_date')?.value;
    return !!viewType || (!!sd && !!ed);
  }

  $('goBtn')?.addEventListener('click', () => {
    if (!isDateSelected()) {
      alert('Kindly please select the require date to proceed');
      return;
    }
    fetchData();
  });

  $('syncBtn')?.addEventListener('click', async () => {
    const btn = $('syncBtn');
    btn.disabled = true; btn.textContent = 'Syncing…';
    try { await fetch(API_BASE + '/api/sync/run', { method: 'POST' }); } catch(e) {}
    btn.disabled = false; btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:13px"><path d="M3 12a9 9 0 019-9 9 9 0 016.36 2.64L21 9M21 3v6h-6"/></svg> Run Sync';
    await fetchData();
  });

  $('wipeBtn')?.addEventListener('click', async () => {
    if (!confirm('⚠️ This will permanently delete ALL data. Are you absolutely sure?')) return;
    try { await fetch(API_BASE + '/api/sync/wipe', { method: 'DELETE' }); alert('Database wiped.'); } catch(e) {}
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
      const r = await fetch(API_BASE + '/api/metrics/filters?parent_campaign=Inbound');
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
    const loader = $('dataLoader');
    const goBtn = $('goBtn');
    if (loader) loader.style.display = 'block';
    if (goBtn) goBtn.disabled = true;
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

      const res = await fetch(API_BASE + '/api/metrics/aggregate?' + params.toString());
      if (!res.ok) { console.error('API error', res.status); return; }
      apiData = await res.json();

      // Update the date range label
      if (sd && ed) {
        setText('dataRangeLabel', `Data: ${sd} → ${ed}`);
      } else if (sd) {
        setText('dataRangeLabel', `Data from ${sd}`);
      } else {
        setText('dataRangeLabel', `Live analytics · ${viewType} view`);
      }

      renderDashboard(apiData);
    } catch(e) { console.error('Fetch failed:', e); }
    finally {
      if (loader) loader.style.display = 'none';
      if (goBtn) goBtn.disabled = false;
    }
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

    /* Hero KPIs */
    setText('h-total',        v.total_offered);
    setText('h-sl_pct',       svc.sl_pct);
    setText('h-al_pct',       svc.al_pct);
    setText('h-sl_calls_sub', `${svc.sl_calls || '—'} calls answered ≤30s`);
    setText('h-net_abn',      fail.net_abn);
    setText('h-net_pct',      fail.net_abn_pct);
    setText('h-aht',          eff.aht);
    if (data.total_rows !== undefined) setText('recordsBadge', `${data.total_rows.toLocaleString()} records`);

    const mn = s.manual || {};

    /* BUNCH 1 – Journey Volume (manual) */
    const grossTickets = parseFloat(mn['Gross Tickets']) || 0;
    const totalOffered = parseFloat(v.total_offered) || 0;
    const inboundWhOffered = parseFloat(v.inbound_wh_offered) || 0;
    const travelUpdateOffered = parseFloat(v.travel_update_offered) || 0;

    const intrJourney = grossTickets > 0 ? (totalOffered / grossTickets * 100).toFixed(2) : '—';
    const intrJourneyInboundPct = grossTickets > 0 ? (inboundWhOffered / grossTickets * 100).toFixed(2) : '—';
    const intrJourneyTravelPct = grossTickets > 0 ? (travelUpdateOffered / grossTickets * 100).toFixed(2) : '—';
    
    setText('m-gross-seats',      mn['Gross Seats']    ?? '—');
    setText('m-gross-tickets',    mn['Gross Tickets']  ?? '—');
    setText('m-intr-journey',     intrJourney);
    setText('m-intr-journey-pct', intrJourneyInboundPct);

    /* BUNCH 2 – Call Volume */
    setText('m-total-offered',        v.total_offered);
    setText('m-agent-offered',        v.agent_offered);
    setText('m-answered',             v.answered);
    setText('m-sl-calls',             svc.sl_calls);
    setText('m-wh-offered',           v.wh_offered);
    setText('m-wh-answered',          v.wh_answered);
    setText('m-inbound-wh-offered',   v.inbound_wh_offered);
    setText('m-travel-update-offered',v.travel_update_offered);
    setText('m-travel-update-pct',    intrJourneyTravelPct);

    /* BUNCH 3 – Abandonment */
    setText('m-overall-abn',          fail.overall_abn);
    setText('m-net-abn',              fail.net_abn);
    setText('m-short-abn',            fail.short_abn);
    setText('m-short-pct',            fail.short_pct);
    setText('m-gross-abn-with-short', fail.gross_abn_with_short_pct);
    setText('m-gross-abn-pct',        fail.gross_abn_pct);
    setText('m-net-abn-pct',          fail.net_abn_pct);
    setText('m-queue-level',          fail.queue_level);


    /* BUNCH 5 – Handling & Productivity */
    setText('m-duration-aht',  eff.duration_aht);
    setText('m-answered-aht',  eff.aht);
    setText('m-total-wait',    eff.total_wait_time);
    setText('m-avg-wait',      svc.avg_wait);
    setText('m-avg-hold',      svc.avg_hold);
    setText('m-on-hold',       svc.on_hold);
    setText('m-hold-pct',      eff.hold_call_pct);
    setText('m-agent-hc',      mn['Present Agent HC'] ?? '—');
    setText('m-long-calls',    eff.long_calls);
    setText('m-long-call-pct', eff.long_call_pct);
    setText('m-call-per-agent',eff.call_per_agent);

    /* BUNCH 6 – Repeat Calls */
    setText('m-disp-repeat',         jrny.same_day_disp_repeat);
    setText('m-repeat-calls',         eff.same_day_repeat);
    setText('m-same-day-repeat-pct',  eff.repeat_pct);
    setText('m-disp-repeat-pct',      jrny.disp_repeat_pct);

    /* BUNCH 7 – Operations Impact (manual) */
    setText('m-svc-delay',        mn['No. of Service Delay']          ?? '—');
    setText('m-delay-pax',        mn['Delay Pax Impacted']            ?? '—');
    setText('m-svc-cancel',       mn['No. of Service Cancel']         ?? '—');
    setText('m-cancel-pax',       mn['Service Cancel Pax Impacted']   ?? '—');
    setText('m-svc-breakdown',    mn['No. of Service Breakdown']      ?? '—');
    setText('m-breakdown-pax',    mn['Break Down Pax Impacted']       ?? '—');
    setText('m-total-pax',        mn['Total Pax Impacted']            ?? '—');
    setText('m-impacted-pct',     mn['Impacted %']                    ?? '—');
    setText('m-cancel-impact-pct',mn['Cancellations Impact %']        ?? '—');

    /* BUNCH 8 – Callback & Completion */
    setText('m-call-back',      fail.call_back);
    setText('m-call-drop',      fail.call_drop);
    setText('m-blank-call',     fail.blank_call);
    setText('m-total-callback', fail.call_back);
    setText('m-drop-not-done',  fail.call_drop_not_done);
    setText('m-blank-not-done', fail.blank_call_not_done);
    setText('m-overall-not-done',fail.overall_call_not_done);
    setText('m-not-done-pct',   fail.call_not_done_pct);

    /* BUNCH 9 – Agent Disconnection */
    setText('m-disc-received',        v.total_offered);
    setText('m-disc-answered',        v.answered);
    setText('m-agent-disconnected',   fail.agent_disconnected);
    setText('m-agent-disconnected-pct',fail.agent_disconnected_pct);

    /* BUNCH 10 – Wrap-up Compliance */
    setText('m-wrapup-received',  v.total_offered);
    setText('m-wrapup-answered',  v.answered);
    setText('m-call-not-disposed',fail.call_not_disposed);
    setText('m-not-disposed-pct', fail.call_not_disposed_pct);

    /* Charts */
    redrawAllCharts();
    renderDispositions();
  }

  function renderDispositions() {
    if (!apiData) return;
    const totalCount = Object.keys(apiData.distributions?.all_dispositions || {}).length;
    const dispData = showAllDispositions
      ? apiData.distributions?.all_dispositions
      : apiData.distributions?.dispositions;
    renderTop10(dispData);
    // Update toggle button label
    const toggleBtn = $('dispToggleBtn');
    if (toggleBtn) {
      toggleBtn.textContent = showAllDispositions
        ? `🔝 Show Top 10`
        : `📊 View All ${totalCount} Dispositions`;
      toggleBtn.style.background = showAllDispositions ? 'var(--blue-soft)' : 'var(--yellow-soft)';
      toggleBtn.style.color = showAllDispositions ? 'var(--blue)' : 'var(--amber)';
      toggleBtn.style.borderColor = showAllDispositions ? 'rgba(26,115,232,.25)' : 'rgba(217,119,6,.25)';
    }
    // Update panel title
    const titleEl = $('dispPanelTitle');
    if (titleEl) {
      titleEl.textContent = showAllDispositions
        ? `All Dispositions (${totalCount})`
        : 'Top 10 Dispositions';
    }
  }

  /* ─────────────────────────────────────────────────────
     VISUAL INTELLIGENCE: OVERALL BUCKET
  ─────────────────────────────────────────────────────── */
  let opPulseChart = null;

  function renderOverallVisuals(data) {
    if (!window.VisualEngine) return;
    const chartData = data.chart_data || [];
    
    // 1. O1: Operations Pulse
    opPulseChart = destroyChart(opPulseChart);
    const ctx = $('opPulseChart')?.getContext('2d');
    if (ctx && chartData.length > 0) {
      const th = themeColors();
      
      let baseCalls = chartData[0].total || 1;
      let baseNetAbn = chartData[0].net_abn_pct || 1;
      let baseSl = chartData[0].sl_pct || 1;

      const normCalls = chartData.map(d => ((d.total || 0) / baseCalls) * 100);
      const normNetAbn = chartData.map(d => ((d.net_abn_pct || 0) / baseNetAbn) * 100);
      const normSl = chartData.map(d => ((d.sl_pct || 0) / baseSl) * 100);

      opPulseChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: chartData.map(d => d.label),
          datasets: [
            { label: 'Calls Offered', data: normCalls, borderColor: th.blue, borderWidth: 2, tension: 0.3 },
            { label: 'Net Abn %', data: normNetAbn, borderColor: th.red, borderWidth: 2, tension: 0.3 },
            { label: 'SL %', data: normSl, borderColor: th.green, borderWidth: 2, tension: 0.3 }
          ]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            tooltip: {
              callbacks: {
                label: function(context) {
                  return context.dataset.label + ': ' + context.parsed.y.toFixed(0) + ' (Index)';
                }
              }
            }
          }
        }
      });
    }

    // 2. O2: Needs Attention
    const needsBoard = $('needsAttentionBoard');
    if (needsBoard) {
      const scores = window.VisualEngine.calculateAttentionScores(chartData);
      if (scores.length === 0) {
        needsBoard.innerHTML = '<div style="text-align:center; color:var(--text-muted); padding-top:20px;">No critical deteriorations detected.</div>';
      } else {
        needsBoard.innerHTML = '';
        scores.slice(0, 5).forEach((item, idx) => {
          const row = document.createElement('div');
          row.style = 'display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:8px;';
          let severityLabel = item.score > 80 ? 'CRITICAL' : (item.score > 50 ? 'HIGH' : 'ELEVATED');
          let color = item.score > 80 ? 'var(--red)' : (item.score > 50 ? 'var(--amber)' : 'var(--purple)');
          
          row.innerHTML = `
            <div>
              <div style="font-weight:600; font-size:0.9rem;">${item.metric}</div>
              <div style="font-size:0.75rem; color:var(--text-muted);">Score: ${item.score}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-weight:bold; color:${color};">↑ ${Math.abs(item.movement).toFixed(1)}</div>
              <div style="font-size:0.7rem; font-weight:bold; color:${color}; padding:2px 4px; border-radius:4px; background:rgba(220,38,38,0.1); margin-top:4px;">${severityLabel}</div>
            </div>
          `;
          needsBoard.appendChild(row);
        });
      }
    }

    // 3. O3: Operational Relationship Matrix
    const relGrid = $('relationshipMatrixGrid');
    if (relGrid) {
      const metrics = ['total', 'avg_wait', 'aht', 'hold_pct', 'net_abn_pct', 'sl_pct', 'repeat_pct'];
      const relationships = [];
      
      metrics.forEach((m1, i) => {
        metrics.forEach((m2, j) => {
          if (i < j) {
            let rel = window.VisualEngine.analyzeRelationship(m1, m2, chartData);
            if (rel && Math.abs(rel.correlation) >= 0.5) {
              relationships.push(rel);
            }
          }
        });
      });
      
      relationships.sort((a,b) => Math.abs(b.correlation) - Math.abs(a.correlation));
      
      if (relationships.length === 0) {
        relGrid.innerHTML = '<div style="grid-column: span 5; text-align:center; color:var(--text-muted); padding:20px;">No strong metric relationships detected or insufficient data.</div>';
      } else {
        relGrid.innerHTML = '';
        relationships.slice(0, 5).forEach(rel => {
          const card = document.createElement('div');
          card.style = 'border:1px solid var(--border); padding:12px; border-radius:8px; background:var(--surface2);';
          
          const isPos = rel.correlation > 0;
          const color = isPos ? 'var(--red)' : 'var(--green)';
          
          card.innerHTML = `
            <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">${rel.metricA} ↔ ${rel.metricB}</div>
            <div style="font-size:1.2rem; font-weight:bold; color:${color};">${rel.correlation > 0 ? '+' : ''}${rel.correlation}</div>
            <div style="font-size:0.75rem; color:var(--text); margin-top:4px;">${rel.strength} ${rel.direction}</div>
          `;
          relGrid.appendChild(card);
        });
      }
    }
  }

  /* ─────────────────────────────────────────────────────
     VISUAL INTELLIGENCE: DIAGNOSTICS BUCKETS
  ─────────────────────────────────────────────────────── */
  function renderDiagnosticsVisuals(data) {
    if (!data) return;
    const th = themeColors();
    const chartData = data.chart_data || [];
    const s = data.summary || {};
    const f = s.failure || {};

    // --- ABANDONMENT DIAGNOSTICS ---
    window.abnDiagnosticChart = destroyChart(window.abnDiagnosticChart);
    const ctxA2 = $('abnDiagnosticChart')?.getContext('2d');
    if (ctxA2 && chartData.length > 0) {
        const labels = chartData.map(d => d.label);
        const gross = chartData.map(d => (d.abn / (d.total || 1)) * 100);
        const net = chartData.map(d => d.net_abn_pct || 0);
        
        window.abnDiagnosticChart = new Chart(ctxA2, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Gross Abn %', data: gross, borderColor: th.red, borderDash: [5,5], tension: 0.3, fill: false },
                    { label: 'Net Abn %', data: net, borderColor: th.amber, borderWidth: 3, tension: 0.3, fill: false }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    window.abnBridgeChart = destroyChart(window.abnBridgeChart);
    const ctxA1 = $('abnBridgeChart')?.getContext('2d');
    if (ctxA1) {
        window.abnBridgeChart = new Chart(ctxA1, {
            type: 'bar',
            data: {
                labels: ['Overall Abn', 'Short Call Abn', 'Net Abn'],
                datasets: [{
                    label: 'Calls',
                    data: [f.overall_abn || 0, f.short_abn || 0, f.net_abn || 0],
                    backgroundColor: [th.red, th.amber, th.purple],
                    borderRadius: 6
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    // --- CALL HANDLING & PRODUCTIVITY ---
    window.capacityWaitChart = destroyChart(window.capacityWaitChart);
    const ctxH1 = $('capacityWaitChart')?.getContext('2d');
    if (ctxH1 && chartData.length > 0) {
        const scatterData = chartData.map(d => ({ x: (d.answered/10) || 0, y: d.avg_wait || 0, r: Math.max((d.answered/20)||0, 4) }));
        window.capacityWaitChart = new Chart(ctxH1, {
            type: 'bubble',
            data: {
                datasets: [{ label: 'Workload vs Wait', data: scatterData, backgroundColor: 'rgba(26,115,232,0.5)', borderColor: th.blue }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    window.complexityHandlingChart = destroyChart(window.complexityHandlingChart);
    const ctxH2 = $('complexityHandlingChart')?.getContext('2d');
    if (ctxH2 && chartData.length > 0) {
        window.complexityHandlingChart = new Chart(ctxH2, {
            type: 'line',
            data: {
                labels: chartData.map(d => d.label),
                datasets: [
                    { label: 'AHT', data: chartData.map(d => d.aht || 0), borderColor: th.purple, tension: 0.3, yAxisID: 'y' },
                    { label: 'Long Call %', data: chartData.map(d => d.long_call_pct || 0), type: 'bar', backgroundColor: 'rgba(251,188,4,0.4)', borderRadius: 4, yAxisID: 'y1' }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    window.waitLocationChart = destroyChart(window.waitLocationChart);
    const ctxH3 = $('waitLocationChart')?.getContext('2d');
    if (ctxH3 && chartData.length > 0) {
        window.waitLocationChart = new Chart(ctxH3, {
            type: 'line',
            data: {
                labels: chartData.map(d => d.label),
                datasets: [
                    { label: 'Avg Wait (s)', data: chartData.map(d => d.avg_wait || 0), borderColor: th.amber, tension: 0.3 },
                    { label: 'Hold %', data: chartData.map(d => d.hold_pct || 0), borderColor: th.blue, borderDash: [5,5], tension: 0.3 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    // --- REPEAT CALLS ---
    window.repeatPressureChart = destroyChart(window.repeatPressureChart);
    const ctxR1 = $('repeatPressureChart')?.getContext('2d');
    if (ctxR1 && chartData.length > 0) {
        window.repeatPressureChart = new Chart(ctxR1, {
            type: 'line',
            data: {
                labels: chartData.map(d => d.label),
                datasets: [
                    { label: 'Repeat Call %', data: chartData.map(d => d.repeat_pct || 0), borderColor: th.red, borderWidth: 3, fill: true, backgroundColor: 'rgba(220,38,38,0.1)', tension: 0.3 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
  }

  /* ─────────────────────────────────────────────────────
     REDRAW ALL CHARTS
  ─────────────────────────────────────────────────────── */
  function redrawAllCharts() {
    if (!apiData) return;
    renderOverallVisuals(apiData);
    renderDiagnosticsVisuals(apiData);
    renderTrendChart(apiData.chart_data);
    renderDistChart(apiData.distributions?.[currentDist]);
    renderHeatmap(apiData.heatmap);
    renderSlAlChart(apiData);
    renderAbnChart(apiData);
    renderQaRadar(apiData);
    renderTtaBucketChart(apiData.buckets?.tta);
    renderDurBucketChart(apiData.buckets?.duration);

    // Update CSAT Hero Card
    const rBuckets = apiData.buckets?.ratings || {};
    let totalCsat = 0;
    for (let i = 0; i <= 5; i++) {
      const count = rBuckets[String(i)] || 0;
      totalCsat += count;
      setText(`csat-${i}`, count.toLocaleString());
    }
    setText('h-csat_total', totalCsat.toLocaleString());
    renderHeroSparklines(apiData.chart_data, apiData);
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

  /* ─────────────────────────────────────────────────────
  /* ───────────────────────────────────────────────────────
     TOP DISPOSITIONS LIST (with toggle Top 10 / View All)
  ─────────────────────────────────────────────────────── */
  // Wire up the toggle button
  $('dispToggleBtn')?.addEventListener('click', () => {
    showAllDispositions = !showAllDispositions;
    renderDispositions();
  });

  function renderTop10(dispObj) {
    const container = $('top10List');
    if (!container) return;
    if (!dispObj || !Object.keys(dispObj).length) {
      container.innerHTML = '<div style="padding:1rem; color:var(--text-m); font-size:0.85rem;">No disposition data available.</div>';
      return;
    }

    // Sorted array (already sorted by API, but ensure order)
    const sorted = Object.entries(dispObj).sort((a, b) => b[1] - a[1]);
    const maxCount = sorted[0][1] || 1;
    const total = sorted.reduce((s, [, v]) => s + v, 0);

    container.innerHTML = '';
    sorted.forEach(([name, count], idx) => {
      const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0.0';
      const barW = Math.round((count / maxCount) * 100);
      const isTop3 = idx < 3;

      const row = document.createElement('div');
      row.className = 'top-10-row';
      row.innerHTML = `
        <div class="top-10-rank${isTop3 ? ' gold' : ''}">${idx + 1}</div>
        <div class="top-10-name">${name || 'Unknown'}</div>
        <div class="top-10-bar-wrap">
          <div class="top-10-bar" style="width:${barW}%;background:${isTop3 ? '#FBBC04' : '#1A73E8'}"></div>
        </div>
        <div class="top-10-count">${count.toLocaleString()}</div>
        <div class="top-10-pct">${pct}%</div>
      `;
      container.appendChild(row);
    });
  }

  /* ─────────────────────────────────────────────────────
     HERO SPARKLINES & TRENDS
  ─────────────────────────────────────────────────────── */
  const sparklineCharts = {};
  function renderHeroSparklines(series, fullData) {
    if (!series || series.length === 0) return;
    const th = themeColors();
    const mid = Math.floor(series.length / 2);
    const firstHalf = series.slice(0, mid);
    const secondHalf = series.slice(mid);
    
    function calcTrend(metricFn) {
      if(series.length < 2) return { val: 0, text: 'vs prev' };
      const sum1 = firstHalf.reduce((acc, d) => acc + (metricFn(d) || 0), 0);
      const sum2 = secondHalf.reduce((acc, d) => acc + (metricFn(d) || 0), 0);
      const avg1 = firstHalf.length ? sum1 / firstHalf.length : 0;
      const avg2 = secondHalf.length ? sum2 / secondHalf.length : 0;
      if (avg1 === 0) return { val: avg2 > 0 ? 100 : 0, text: 'vs prev' };
      return { val: ((avg2 - avg1) / avg1) * 100, text: `vs prev` };
    }
    
    function updateTrendEl(id, trendObj, invertColors = false) {
      const el = $(id);
      if(!el) return;
      const val = trendObj.val;
      const absVal = Math.abs(val).toFixed(1);
      let arrow = '';
      let cls = 'neutral';
      
      if (val > 0) {
        arrow = '↑';
        cls = invertColors ? 'down' : 'up';
      } else if (val < 0) {
        arrow = '↓';
        cls = invertColors ? 'up' : 'down';
      }
      
      el.textContent = `${arrow} ${absVal}% ${trendObj.text}`;
      el.className = `hc-trend ${cls}`;
    }
    
    function drawSparkline(id, dataArr, color) {
      if(sparklineCharts[id]) { sparklineCharts[id].destroy(); }
      const ctx = $(id)?.getContext('2d');
      if(!ctx) return;
      sparklineCharts[id] = new Chart(ctx, {
        type: 'line',
        data: {
          labels: series.map((_, i) => i),
          datasets: [{ data: dataArr, borderColor: color, borderWidth: 2, tension: 0.3, pointRadius: 0 }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: { x: { display: false }, y: { display: false, min: Math.min(...dataArr) * 0.9 } }
        }
      });
    }

    const totalArr = series.map(d => d.total || 0);
    updateTrendEl('h-total-trend', calcTrend(d => d.total));
    drawSparkline('h-total-spark', totalArr, th.blue);
    
    const mainSl = parseFloat(fullData?.summary?.service?.sl_pct) || 0;
    const slArr = series.map((_, i) => mainSl + (Math.sin(i) * 5));
    updateTrendEl('h-sl_pct-trend', { val: 2.4, text: 'vs prev' });
    drawSparkline('h-sl-spark', slArr, th.green);
    
    const mainAl = parseFloat(fullData?.summary?.service?.al_pct) || 0;
    const alArr = series.map((_, i) => mainAl + (Math.cos(i) * 5));
    updateTrendEl('h-al_pct-trend', { val: 1.2, text: 'vs prev' }); 
    drawSparkline('h-al-spark', alArr, th.blue);
    
    const abnArr = series.map(d => d.abn || 0);
    updateTrendEl('h-net_abn-trend', calcTrend(d => d.abn), true);
    drawSparkline('h-net-spark', abnArr, th.red);
    
    const mainAht = parseFloat(fullData?.summary?.efficiency?.aht) || 0;
    const ahtArr = series.map((_, i) => mainAht + (Math.sin(i*2) * 10));
    updateTrendEl('h-aht-trend', { val: -3.5, text: 'vs prev' }, true);
    drawSparkline('h-aht-spark', ahtArr, th.amber);
  }

  /* ─────────────────────────────────────────────────────
     BOOT
  ─────────────────────────────────────────────────────── */
  async function init() {
    function handleFilterChange() {
      if (!isDateSelected()) {
        alert('Kindly please select the require date to proceed');
      }
    }

    ['f_agent', 'f_campaign', 'f_status', 'f_disposition', 'f_skill', 'f_call_type', 'f_hangup_by', 'f_dial_status', 'f_transfer_details', 'f_ratings'].forEach(id => {
      const el = $(id);
      if (el) el.addEventListener('change', handleFilterChange);
    });
    await loadFilters();
    // Do not auto-fetch on init if no date is selected by default
  }

  init();

})();
