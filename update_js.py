with open('script_freshdesk.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

# Add the fetch filters logic right after DOMContentLoaded
fetch_filters_logic = """
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
"""

js_code = js_code.replace("// 3. Populate Filter Dropdowns dynamically from raw data (Optional, or could just rely on backend if predefined)\n    // Since we don't have all unique values hardcoded, we can fetch them once or let user type.\n    // For simplicity, we assume 'All' is default and users know what to select, or we can fetch filter options from backend.\n    // In a full implementation, we'd have a /api/helpdesk/filters endpoint.", fetch_filters_logic)

# Add event listeners for Today, Yesterday, Weekly, Monthly
date_preset_logic = """
    // --- DATE PRESET BUTTONS ---
    const vbtns = document.querySelectorAll('.hdr-vbtn');
    vbtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const view = btn.getAttribute('data-view');
            if(!view) return;
            
            const d = new Date();
            let start = new Date(d);
            let end = new Date(d);
            
            if(view === 'daily') {
                // Today
            } else if(view === 'yesterday') {
                start.setDate(d.getDate() - 1);
                end.setDate(d.getDate() - 1);
            } else if(view === 'weekly') {
                start.setDate(d.getDate() - 7);
            } else if(view === 'monthly') {
                start.setDate(d.getDate() - 30);
            }
            
            fpStart.setDate(start);
            fpEnd.setDate(end);
            
            fetchData();
        });
    });
"""

js_code = js_code.replace("if (applyBtn) applyBtn.addEventListener('click', fetchData);", date_preset_logic + "\n    if (applyBtn) applyBtn.addEventListener('click', fetchData);")

# Wait, the ID for the "Reset Filters" button is clearBtn
reset_logic = """
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
"""

js_code = js_code.replace("if (goBtn) goBtn.addEventListener('click', fetchData);", "if (goBtn) goBtn.addEventListener('click', fetchData);\n" + reset_logic)

with open('script_freshdesk.js', 'w', encoding='utf-8') as f:
    f.write(js_code)
