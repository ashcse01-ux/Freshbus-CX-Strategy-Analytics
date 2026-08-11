
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Date Pickers
    // Day-1 only: Jan 1 2026 → yesterday (never today/future)
    const DATE_MIN = new Date(2026, 0, 1); // 1 Jan 2026

    function getYesterday() {
        const d = new Date();
        d.setHours(0, 0, 0, 0);
        d.setDate(d.getDate() - 1);
        return d;
    }

    function earliestOf(a, b) {
        if (!a) return b;
        if (!b) return a;
        return a.getTime() <= b.getTime() ? a : b;
    }

    function latestOf(a, b) {
        if (!a) return b;
        if (!b) return a;
        return a.getTime() >= b.getTime() ? a : b;
    }

    function clampToAllowed(date) {
        const yesterday = getYesterday();
        let d = new Date(date);
        d.setHours(0, 0, 0, 0);
        if (d < DATE_MIN) d = new Date(DATE_MIN);
        if (d > yesterday) d = new Date(yesterday);
        return d;
    }

    let isProgrammaticDateChange = false;

    function applyDateBounds() {
        const yesterday = getYesterday();
        const startVal = fpStart.selectedDates[0] || null;
        const endVal = fpEnd.selectedDates[0] || null;

        fpStart.set('minDate', DATE_MIN);
        fpStart.set('maxDate', earliestOf(endVal, yesterday));

        fpEnd.set('minDate', latestOf(startVal, DATE_MIN));
        fpEnd.set('maxDate', yesterday);
    }

    const handleDateChange = () => {
        applyDateBounds();
        if (isProgrammaticDateChange) return;
        const vbtns = document.querySelectorAll('.hdr-vbtn');
        vbtns.forEach(b => b.classList.remove('active'));
    };

    const yesterday = getYesterday();
    const defaultStart = clampToAllowed(new Date(yesterday.getTime() - 6 * 24 * 60 * 60 * 1000));

    // Flatpickr initialization
    const fpStart = flatpickr("#filter_start_date", {
        dateFormat: "Y-m-d",
        allowInput: false,
        defaultDate: defaultStart,
        minDate: DATE_MIN,
        maxDate: yesterday,
        onOpen: applyDateBounds,
        onChange: handleDateChange
    });
    const fpEnd = flatpickr("#filter_end_date", {
        dateFormat: "Y-m-d",
        allowInput: false,
        defaultDate: yesterday,
        minDate: DATE_MIN,
        maxDate: yesterday,
        onOpen: applyDateBounds,
        onChange: handleDateChange
    });
    applyDateBounds();

    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) applyDateBounds();
    });
    window.addEventListener('focus', applyDateBounds);

    // 2. Tab Switching Logic
    const segBtns = document.querySelectorAll('.seg-btn');
    const bunches = document.querySelectorAll('.bunch');
    
    segBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            segBtns.forEach(b => b.classList.remove('active'));
            bunches.forEach(b => b.classList.remove('active'));
            
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-bunch');
            document.getElementById(targetId).classList.add('active');
            
            // Adjust sidebar filters based on active tab
            adjustSidebar(targetId);
        });
    });

    
    function adjustSidebar(targetId) {
        document.querySelectorAll('.sb-fg[data-tabs]').forEach(el => {
            const tabs = el.getAttribute('data-tabs').split(',');
            if(tabs.includes(targetId)) {
                el.style.display = 'flex';
            } else {
                el.style.display = 'none';
            }
        });
    }
    adjustSidebar('bunch-helpdesk'); // Initialize


    
    // --- FETCH AND POPULATE FILTERS ---
    async function loadFilters() {
        try {
            const res = await fetch('/api/helpdesk/filters');
            const data = await res.json();
            if(data.status === 'success') {
                const f = data.data;
                const populate = (id, options) => {
                    const el = document.getElementById(id);
                    if(!el) return;
                    options.forEach(opt => {
                        const o = document.createElement('option');
                        o.value = opt;
                        o.textContent = opt;
                        el.appendChild(o);
                    });
                };
                populate('filter_lob', f.lob);
                populate('filter_status', f.status);
                populate('filter_type', f.type);
                populate('filter_group', f.group);
                populate('filter_priority', f.priority);
                populate('filter_agent', f.agent);
                populate('filter_source', f.hda_source); // source for HD adoption
                populate('filter_complaint_type', f.type); // mock complaint types to type
            }
        } catch(e) {
            console.error("Failed to load filters", e);
        }
    }
    loadFilters();

    
    // 4. Fetch and Render Data
    const applyBtn = document.getElementById('applyBtn');
    const goBtn = document.getElementById('goBtn');
    
    async function fetchData() {
        const startDate = document.getElementById('filter_start_date').value;
        const endDate = document.getElementById('filter_end_date').value;
        
        // Gather selected filters
        const getSelected = (id) => {
            const el = document.getElementById(id);
            if (!el) return [];
            if (el.multiple) {
                return Array.from(el.selectedOptions).map(o => o.value).filter(v => v !== 'All');
            } else {
                return el.value !== 'All' ? [el.value] : [];
            }
        };
        
        const payload = {
            start_date: startDate,
            end_date: endDate,
            lob: getSelected('filter_lob'),
            status: getSelected('filter_status'),
            type: getSelected('filter_type'),
            group: getSelected('filter_group'),
            priority: getSelected('filter_priority'),
            agent: getSelected('filter_agent'),
            source: getSelected('filter_source')
        };
        
        // Show loading state
        const originalGoText = goBtn.innerHTML;
        goBtn.innerHTML = '<span style="font-size:12px;">Loading...</span>';
        goBtn.disabled = true;
        
        try {
            const response = await fetch('/api/helpdesk/aggregate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                renderCards(data);
            } else {
                alert("Error fetching data!");
            }
        } catch (error) {
            console.error(error);
            alert("Network error!");
        } finally {
            goBtn.innerHTML = 'GO';
            goBtn.disabled = false;
        }
    }
    
    function renderCards(data) {
        const m = data.metrics;
        const s = data.sources;
        
        // Helper to update safely
        const update = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };

        // --- Helpdesk Bunch ---
        update('hd-tickets-created', m.tickets_created);
        update('hd-ftr-tickets', m.ftr_tickets);
        update('hd-nftr-tickets', m.nftr_tickets);
        update('hd-blanks', m.blank_tickets);
        update('hd-tickets-closed', m.tickets_closed);
        update('hd-tickets-pending', m.tickets_pending);
        update('hd-calls-ans', m.inbound_calls_ans);
        update('hd-not-created', m.ticket_not_created_fd);
        update('hd-ftr-restime', m.avg_ftr_res_time);
        update('hd-nftr-restime', m.avg_nftr_res_time);
        update('hd-overall-restime', m.avg_res_time);
        update('hd-fd-adoption', m.hd_adoption + '%');
        update('hd-seats', m.seats);
        update('hd-pnr', m.pnr);
        update('hd-defect-rate', m.defect_rate + '%');
        
        // Sources Breakdown
        if(s.Inbound) {
            update('hd-inbound-ftr', s.Inbound.ftr);
            update('hd-inbound-nftr', s.Inbound.nftr);
            update('hd-inbound-rt', s.Inbound.avg_res_time);
        }
        if(s.Outbound) {
            update('hd-outbound-ftr', s.Outbound.ftr);
            update('hd-outbound-nftr', s.Outbound.nftr);
            update('hd-outbound-rt', s.Outbound.avg_res_time);
        }
        if(s.Email) {
            update('hd-email-ftr', s.Email.ftr);
            update('email-nftr', s.Email.nftr); // wait I might have missed hd- prefix, I will check
            update('hd-email-ftr', s.Email.ftr);
            update('hd-email-nftr', s.Email.nftr);
            update('hd-email-rt', s.Email.avg_res_time);
        }

        // --- Complaint Bunch ---
        update('comp-new', m.complaints.new_tickets);
        update('comp-backdated', m.complaints.back_dated);
        update('comp-closed', m.complaints.closed);

        // --- Adoption Bunch ---
        update('adop-tickets-created', m.tickets_created);
        update('adop-ftr-tickets', m.ftr_tickets);
        update('adop-nftr-tickets', m.nftr_tickets);
        update('adop-blanks', m.blank_tickets);
        update('adop-tickets-closed', m.tickets_closed);
        update('adop-tickets-pending', m.tickets_pending);
        update('adop-calls-ans', m.inbound_calls_ans);
        update('adop-not-created', m.ticket_not_created_fd);
        update('adop-ftr-restime', m.avg_ftr_res_time);
        update('adop-nftr-restime', m.avg_nftr_res_time);
        update('adop-overall-restime', m.avg_res_time);
        update('adop-fd-adoption', m.hd_adoption + '%');
    }

    
    // --- DATE PRESET BUTTONS ---
    const vbtns = document.querySelectorAll('.hdr-vbtn');
    vbtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const view = btn.getAttribute('data-view');
            if(!view) return;

            // Toggle active class
            vbtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const end = getYesterday();
            let start = new Date(end);
            
            if(view === 'yesterday') {
                start = new Date(end);
            } else if(view === 'weekly') {
                start.setDate(end.getDate() - 6);
            } else if(view === 'monthly') {
                start.setDate(end.getDate() - 29);
            }

            start = clampToAllowed(start);
            
            isProgrammaticDateChange = true;
            fpStart.setDate(start);
            fpEnd.setDate(end);
            isProgrammaticDateChange = false;
            applyDateBounds();
            
            fetchData();
        });
    });

    if (applyBtn) applyBtn.addEventListener('click', fetchData);
    if (goBtn) goBtn.addEventListener('click', fetchData);

    const clearBtn = document.getElementById('clearBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            document.querySelectorAll('.sb-fg select').forEach(sel => {
                Array.from(sel.options).forEach(opt => {
                    opt.selected = (opt.value === 'All');
                });
            });
            fetchData();
        });
    }

    
    // Auto-fetch on load
    fetchData();
});
