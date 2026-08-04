js_code = """
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Date Pickers
    const today = new Date();
    const lastWeek = new Date(today);
    lastWeek.setDate(today.getDate() - 7);
    
    // Flatpickr initialization
    const fpStart = flatpickr("#filter_start_date", {
        dateFormat: "Y-m-d",
        defaultDate: lastWeek,
    });
    const fpEnd = flatpickr("#filter_end_date", {
        dateFormat: "Y-m-d",
        defaultDate: today,
    });

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
        // Simple logic to show/hide specific filter sections if needed
        // For now, all are visible, but could be refined.
    }

    // 3. Populate Filter Dropdowns dynamically from raw data (Optional, or could just rely on backend if predefined)
    // Since we don't have all unique values hardcoded, we can fetch them once or let user type.
    // For simplicity, we assume 'All' is default and users know what to select, or we can fetch filter options from backend.
    // In a full implementation, we'd have a /api/helpdesk/filters endpoint.
    
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
            const vals = Array.from(el.selectedOptions).map(o => o.value).filter(v => v !== 'All');
            return vals;
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

    if (applyBtn) applyBtn.addEventListener('click', fetchData);
    if (goBtn) goBtn.addEventListener('click', fetchData);
    
    // Auto-fetch on load
    fetchData();
});
"""

with open('script_freshdesk.js', 'w', encoding='utf-8') as f:
    f.write(js_code)
