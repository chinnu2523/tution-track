import os
import re

file_path = "/Users/madarauchiha/Tution Center/tuition-center.html"
with open(file_path, "r") as f:
    html = f.read()

# 1. Add CSS for light-mode, btn-icon, timeline, and tabs
if ".light-mode {" not in html:
    css_insert = """
.light-mode {
  --bg:#f4f6fa;--bg2:#ffffff;--surface:#ffffff;--surface2:#f9fafb;--surface3:#eff2f6;
  --border:#e5e7eb;--border2:#d1d5db;
  --text:#111827;--text2:#4b5563;--text3:#9ca3af;
  --shadow:0 8px 40px rgba(0,0,0,0.08);
}
.btn-icon{display:flex;align-items:center;justify-content:center;width:34px;height:34px;background:var(--surface2);border:1px solid var(--border);border-radius:50%;color:var(--text2);cursor:pointer;transition:all 0.15s;position:relative;}
.btn-icon:hover{background:var(--surface3);color:var(--text);}
.bell-badge{position:absolute;top:-4px;right:-4px;background:var(--red);color:white;font-size:9px;font-weight:700;padding:2px 5px;border-radius:10px;}

.modal-tabs{display:flex;border-bottom:1px solid var(--border);margin-bottom:20px;}
.mtab{padding:10px 20px;font-family:'Syne',sans-serif;font-weight:700;cursor:pointer;color:var(--text2);border-bottom:2px solid transparent;transition:all 0.2s;}
.mtab.active{color:var(--blue);border-bottom-color:var(--blue);}
.mtab-content{display:none;}
.mtab-content.active{display:block;}

.timeline-box{display:flex;flex-direction:column;gap:16px;max-height:300px;overflow-y:auto;padding-right:10px;}
.t-item{display:flex;gap:12px;}
.t-line{width:2px;background:var(--border);position:relative;margin-top:6px;min-height:40px;}
.t-dot{position:absolute;top:0;left:-4px;width:10px;height:10px;border-radius:50%;background:var(--blue);border:2px solid var(--surface);}
.t-cont{background:var(--surface2);border:1px solid var(--border);border-radius:var(--r);padding:10px;flex:1;}
.t-date{font-size:10px;color:var(--text2);margin-bottom:2px;}
.t-txt{font-size:13px;}

.att-box{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:10px;}
.att-btn{padding:10px;border-radius:var(--r);text-align:center;cursor:pointer;border:1px solid var(--border);background:var(--surface2);font-weight:600;}
.att-btn.p:hover,.att-btn.p.act{background:rgba(16,185,129,0.1);color:var(--green);border-color:var(--green);}
.att-btn.a:hover,.att-btn.a.act{background:rgba(244,63,94,0.1);color:var(--red);border-color:var(--red);}
.att-btn.l:hover,.att-btn.l.act{background:rgba(245,158,11,0.1);color:var(--amber);border-color:var(--amber);}
"""
    html = html.replace("/* ── AMBIENT BG ── */", css_insert + "\n/* ── AMBIENT BG ── */")

# 2. Add Theme Toggle and Notification Bell to Header
header_inject = """
      <div class="header-right">
        <button class="btn-icon" onclick="toggleTheme()" id="themeBtn">☀️</button>
        <button class="btn-icon" onclick="showOverdue()" title="Overdue notifications">
            🔔<div class="bell-badge" id="bellBadge" style="display:none">0</div>
        </button>
"""
html = html.replace('<div class="header-right">', header_inject, 1)

# 3. Add to JS: Theme implementation
js_theme = """
function toggleTheme() {
    const isLight = document.body.classList.toggle('light-mode');
    localStorage.setItem('tt_theme', isLight ? 'light' : 'dark');
    document.getElementById('themeBtn').textContent = isLight ? '🌙' : '☀️';
}
if(localStorage.getItem('tt_theme')==='light'){
    document.body.classList.add('light-mode');
    document.getElementById('themeBtn').textContent='🌙';
}
"""
if "toggleTheme(" not in html:
    html = html.replace("let students=[],", js_theme + "\nlet students=[],")

# 4. Modify 'renderTable' to add WhatsApp button
wa_code = r"""
        const dueMonths = MONTHS.filter(m => !s.months[m] && MONTHS.indexOf(m) <= CM).join(', ');
        const waMsg = encodeURIComponent(`Dear Parent, this is a gentle reminder that tuition fees for ${dueMonths || 'recent months'} are pending for ${s.name}. Please clear the dues at the earliest.`);
        const waBtn = `<a href="https://wa.me/91${s.phone}?text=${waMsg}" target="_blank" style="text-decoration:none" title="Remind on WhatsApp">💬</a>`;
        
        tr.innerHTML=`
          <td><div class="t-name">${esc(s.name)}</div><div class="t-sub">${esc(s.phone)} ${waBtn}</div></td>
"""
html = re.sub(r'tr\.innerHTML\s*=\s*`\s*<td><div class="t-name">\$\{esc\(s\.name\)\}.*?t-sub">\$\{esc\(s\.phone\)\}.*?</td>', wa_code.strip(), html, flags=re.DOTALL)

# 5. Overdue Badge Calculation in renderTable
overdue_calc = """
    // OVERDUE BADGE
    let overdueCount = 0;
    students.forEach(s => {
        if (!s.months[MONTHS[CM]] || (CM > 0 && !s.months[MONTHS[CM-1]])) {
            overdueCount++;
        }
    });
    const b = document.getElementById('bellBadge');
    if(b) {
        b.textContent = overdueCount;
        b.style.display = overdueCount > 0 ? 'block' : 'none';
    }
    
    tb.innerHTML='';
"""
if "let overdueCount =" not in html:
    html = html.replace("tb.innerHTML='';", overdue_calc)

# 6. Re-structuring the Student Modal (stuModal) to contain Tabs
modal_replace_old = """
    <div class="modal-body" style="padding:24px;">
      
      <div class="form-row">
"""
modal_replace_new = """
    <div class="modal-body" style="padding:24px;">
      <div class="modal-tabs">
        <div class="mtab active" onclick="switchStuTab('details')" id="tab-details">Details</div>
        <div class="mtab" onclick="switchStuTab('timeline')" id="tab-timeline">Payment Timeline</div>
        <div class="mtab" onclick="switchStuTab('attendance')" id="tab-attendance">Attendance</div>
      </div>
      
      <div id="mtc-details" class="mtab-content active">
"""
if "switchStuTab" not in html:
    html = html.replace(modal_replace_old, modal_replace_new)
    
    # Close the div at the end of the form
    modal_end_old = """      <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:10px;">"""
    modal_end_new = """      </div> <!-- end mtc-details -->
      
      <div id="mtc-timeline" class="mtab-content">
        <div class="timeline-box" id="stuTimelineBox">
            <div style="font-size:12px;color:var(--text3);">Loading timeline...</div>
        </div>
      </div>
      
      <div id="mtc-attendance" class="mtab-content">
        <input type="date" id="attDate" value="" style="margin-bottom:10px;padding:8px;border-radius:var(--r);background:var(--surface2);border:1px solid var(--border);color:var(--text);">
        <div class="att-box">
            <div class="att-btn p" onclick="markAtt('Present')">Present</div>
            <div class="att-btn a" onclick="markAtt('Absent')">Absent</div>
            <div class="att-btn l" onclick="markAtt('Leave')">Leave</div>
        </div>
        <div class="timeline-box" id="stuAttBox" style="margin-top:10px;"></div>
      </div>

      <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:10px;">"""
    html = html.replace(modal_end_old, modal_end_new)

# 7. Add fetch details logic in openEditModal!
js_modal_open_old = """function openEditModal(id){
  const s=students.find(x=>x.id===id);"""
js_modal_open_new = """async function openEditModal(id){
  const s=students.find(x=>x.id===id);
  editId=id;
  // Fetch timeline asynchronously
  fetchStudentExtras(id);
"""
if "fetchStudentExtras" not in html:
    html = html.replace(js_modal_open_old, js_modal_open_new)

    js_extras = """
function switchStuTab(t) {
    document.querySelectorAll('.mtab').forEach(e=>e.classList.remove('active'));
    document.querySelectorAll('.mtab-content').forEach(e=>e.classList.remove('active'));
    document.getElementById('tab-'+t).classList.add('active');
    document.getElementById('mtc-'+t).classList.add('active');
}

async function fetchStudentExtras(id) {
    document.getElementById('stuTimelineBox').innerHTML = '<div style="font-size:12px;color:var(--text3);">Loading timeline...</div>';
    document.getElementById('stuAttBox').innerHTML = '';
    document.getElementById('attDate').value = new Date().toISOString().slice(0,10);
    
    const {data} = await api('/api/students/'+id+'/details');
    if(data.ok) {
        // Render Timeline
        let th = '';
        data.payments.forEach(p => {
            th += `<div class="t-item"><div class="t-line"><div class="t-dot"></div></div><div class="t-cont"><div class="t-date">${fmtD(p.paid_at)}</div><div class="t-txt">Paid Rs. ${p.amount} for ${p.month}</div></div></div>`;
        });
        if(!th) th = '<div style="font-size:12px;color:var(--text3);">No payments recorded yet.</div>';
        document.getElementById('stuTimelineBox').innerHTML = th;
        
        // Render Attendance
        let ah = '';
        data.attendance.forEach(a => {
            const clr = a.status==='Present'?'var(--green)':a.status==='Absent'?'var(--red)':'var(--amber)';
            ah += `<div class="t-item"><div class="t-line"><div class="t-dot" style="background:${clr}"></div></div><div class="t-cont"><div class="t-date">${a.date}</div><div class="t-txt">${a.status}</div></div></div>`;
        });
        if(!ah) ah = '<div style="font-size:12px;color:var(--text3);">No attendance recorded.</div>';
        document.getElementById('stuAttBox').innerHTML = ah;
    }
}

async function markAtt(st) {
    if(!editId) return;
    const d = document.getElementById('attDate').value;
    const {data} = await api('/api/students/'+editId+'/attendance', 'POST', {date: d, status: st});
    if(data.ok) {
        toast('Marked ' + st + ' on ' + d, st==='Present'?'s':st==='Absent'?'e':'i');
        fetchStudentExtras(editId);
    }
}

function showOverdue() {
    document.getElementById('filterStatus').value = 'due';
    renderTable(); updateStats();
    toast('Showing overdue accounts', 'i');
}
"""
    html = html.replace("function validate(){", js_extras + "\nfunction validate(){")

with open(file_path, "w") as f:
    f.write(html)
print("Injected UI features successfully.")
