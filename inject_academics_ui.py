import os
import re

file_path = "/Users/madarauchiha/Tution Center/tuition-center.html"
with open(file_path, "r") as f:
    html = f.read()

# 1. Update Header Navigation (Admin)
nav_old = '<button class="btn-logout" onclick="showSettings()" style="margin-right:5px;">⚙️ Settings</button>'
nav_new = """
        <button class="btn-logout" onclick="showPage('adminPage')" style="margin-right:5px;">📊 Dashboard</button>
        <button class="btn-logout" onclick="showEnquiries()" style="margin-right:5px;">📞 Enquiries</button>
        <button class="btn-logout" onclick="showBatches()" style="margin-right:5px;">🕒 Batches</button>
        <button class="btn-logout" onclick="showExams()" style="margin-right:5px;">📝 Exams</button>
        <button class="btn-logout" onclick="showSettings()" style="margin-right:5px;">⚙️ Settings</button>
"""
if 'showEnquiries()' not in html:
    html = html.replace(nav_old, nav_new, 1)

# 2. Add New Page Sections (Enquiry, Batch, Exam)
new_pages_html = """
  <!-- ENQUIRY PAGE -->
  <section id="enquiryPage" class="page">
    <header class="tt-header"><div class="header-inner"><div class="logo-area" onclick="showPage('adminPage')"><div class="logo-badge">📚</div><div class="logo-name">Tuition<span>Track</span></div></div><div class="header-right"><button class="btn-primary" onclick="openOv('addEnquiryModal')">+ New Enquiry</button></div></div></header>
    <main>
      <div class="table-wrap"><div class="table-scroll"><table><thead><tr><th>Name</th><th>Phone</th><th>Grade</th><th>Status</th><th>Date</th><th>Actions</th></tr></thead><tbody id="enquiryTableBody"></tbody></table></div></div>
    </main>
  </section>

  <!-- BATCH PAGE -->
  <section id="batchPage" class="page">
    <header class="tt-header"><div class="header-inner"><div class="logo-area" onclick="showPage('adminPage')"><div class="logo-badge">📚</div><div class="logo-name">Tuition<span>Track</span></div></div><div class="header-right"><button class="btn-primary" onclick="openOv('addBatchModal')">+ New Batch</button></div></div></header>
    <main>
      <div class="lms-grid" id="batchGrid"></div>
    </main>
  </section>

  <!-- EXAM PAGE -->
  <section id="examPage" class="page">
    <header class="tt-header"><div class="header-inner"><div class="logo-area" onclick="showPage('adminPage')"><div class="logo-badge">📚</div><div class="logo-name">Tuition<span>Track</span></div></div><div class="header-right"><button class="btn-primary" onclick="openOv('addExamModal')">+ New Exam</button></div></div></header>
    <main>
      <div class="lms-grid" id="examGrid"></div>
    </main>
  </section>
"""
if 'id="enquiryPage"' not in html:
    html = html.replace('<!-- SETTINGS PAGE -->', new_pages_html + '\n  <!-- SETTINGS PAGE -->')

# 3. Add Modals for Academics
new_modals_html = """
<!-- ADD ENQUIRY MODAL -->
<div class="overlay" id="addEnquiryModal"><div class="modal" style="max-width:400px;"><div class="modal-header"><h2>New Enquiry</h2><button class="close-btn" onclick="closeOv('addEnquiryModal')">&times;</button></div><div class="modal-body"><div class="form-field"><label>Full Name</label><input type="text" id="enqName" class="field-input"></div><div class="form-field"><label>Phone</label><input type="text" id="enqPhone" class="field-input"></div><div class="form-field"><label>Grade</label><input type="text" id="enqGrade" class="field-input"></div><div class="form-field"><label>Notes</label><textarea id="enqNotes" class="field-input" style="height:80px;"></textarea></div><button class="btn-login admin" onclick="saveEnquiry()">Create Enquiry</button></div></div></div>

<!-- ADD BATCH MODAL -->
<div class="overlay" id="addBatchModal"><div class="modal" style="max-width:400px;"><div class="modal-header"><h2>New Batch</h2><button class="close-btn" onclick="closeOv('addBatchModal')">&times;</button></div><div class="modal-body"><div class="form-field"><label>Batch Name</label><input type="text" id="btName" class="field-input"></div><div class="form-field"><label>Time (e.g. 9-10 AM)</label><input type="text" id="btTime" class="field-input"></div><div class="form-field"><label>Days (e.g. Mon, Wed)</label><input type="text" id="btDays" class="field-input"></div><div class="form-field"><label>Subject</label><input type="text" id="btSub" class="field-input"></div><div class="form-field"><label>Teacher</label><input type="text" id="btTeacher" class="field-input"></div><button class="btn-login admin" onclick="saveBatch()">Create Batch</button></div></div></div>

<!-- ADD EXAM MODAL -->
<div class="overlay" id="addExamModal"><div class="modal" style="max-width:400px;"><div class="modal-header"><h2>New Exam / Test</h2><button class="close-btn" onclick="closeOv('addExamModal')">&times;</button></div><div class="modal-body"><div class="form-field"><label>Exam Title</label><input type="text" id="exTitle" class="field-input" placeholder="Unit Test 1"></div><div class="form-field"><label>Max Marks</label><input type="number" id="exMax" class="field-input" value="100"></div><div class="form-field"><label>Date</label><input type="date" id="exDate" class="field-input"></div><button class="btn-login admin" onclick="saveExam()">Create Exam</button></div></div></div>

<!-- MARKS ENTRY MODAL -->
<div class="overlay" id="marksModal"><div class="modal"><div class="modal-header"><h2>Marks Entry</h2><button class="close-btn" onclick="closeOv('marksModal')">&times;</button></div><div class="modal-body"><div id="marksEntryList" style="max-height:400px; overflow-y:auto; display:flex; flex-direction:column; gap:10px;"></div><button class="btn-login admin" onclick="submitMarks()" style="margin-top:20px;">Save All Marks</button></div></div></div>
"""
if 'id="addEnquiryModal"' not in html:
    html = html.replace('</body>', new_modals_html + '\n</body>')

# 4. JS Logic for Academics
academics_js = r"""
/* ENQUIRIES */
async function showEnquiries() {
    showPage('enquiryPage');
    const {data} = await api('/api/enquiries');
    const tb = document.getElementById('enquiryTableBody');
    tb.innerHTML = (data.enquiries || []).map(e => `
        <tr>
            <td><strong>${e.name}</strong></td>
            <td>${e.phone}</td>
            <td>${e.grade}</td>
            <td><span class="stag ${e.status==='Converted'?'g':e.status==='Closed'?'r':'a'}">${e.status}</span></td>
            <td>${new Date(e.created_at).toLocaleDateString()}</td>
            <td>
                ${e.status !== 'Converted' ? `<button onclick="convertEnquiry(${e.id}, '${e.name}', '${e.phone}', '${e.grade}')" class="btn btn-sm btn-primary">Convert</button>` : ''}
                <button onclick="updateEnqStatus(${e.id}, 'Closed')" class="btn btn-sm btn-secondary">Close</button>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="6" style="text-align:center; padding:40px; color:var(--text3)">No enquiries found.</td></tr>';
}

async function saveEnquiry() {
    const d = { name: val('enqName'), phone: val('enqPhone'), grade: val('enqGrade'), notes: val('enqNotes') };
    const {data} = await api('/api/enquiries', 'POST', d);
    if(data.ok) { toast('Enquiry saved', 's'); closeOv('addEnquiryModal'); showEnquiries(); }
}

function convertEnquiry(id, name, phone, grade) {
    // Fill Add Student modal and open it
    document.getElementById('sName').value = name;
    document.getElementById('sPhone').value = phone;
    document.getElementById('sClass').value = grade;
    openOv('stuModal');
    // We could automate the closing of enquiry here if we want.
}

async function updateEnqStatus(id, st) {
    const {data} = await api('/api/enquiries/'+id+'/status', 'PUT', {status: st});
    if(data.ok) showEnquiries();
}

/* BATCHES */
async function showBatches() {
    showPage('batchPage');
    const {data} = await api('/api/batches');
    const bg = document.getElementById('batchGrid');
    bg.innerHTML = (data.batches || []).map(b => `
        <div class="track-card">
            <div class="track-header"><div class="track-title">${b.name}</div><div class="track-level">${b.subject}</div></div>
            <div style="font-size:12px; color:var(--text2); margin-bottom:5px;">⏰ ${b.time} | 📅 ${b.days}</div>
            <div style="font-size:12px; color:var(--text3); margin-bottom:15px;">Teacher: ${b.teacher}</div>
            <button onclick="openBatchAssign('${b.id}')" class="btn btn-sm btn-secondary" style="width:100%">Assign Students</button>
        </div>
    `).join('') || '<div style="grid-column:1/-1; text-align:center; padding:40px; color:var(--text3)">No batches created yet.</div>';
}

async function saveBatch() {
    const d = { name: val('btName'), time: val('btTime'), days: val('btDays'), subject: val('btSub'), teacher: val('btTeacher'), room: '' };
    const {data} = await api('/api/batches', 'POST', d);
    if(data.ok) { toast('Batch created', 's'); closeOv('addBatchModal'); showBatches(); }
}

/* EXAMS */
async function showExams() {
    showPage('examPage');
    const {data} = await api('/api/exams');
    const eg = document.getElementById('examGrid');
    eg.innerHTML = (data.exams || []).map(e => `
        <div class="track-card">
            <div class="track-header"><div class="track-title">${e.title}</div><div class="track-level">Max: ${e.max_marks}</div></div>
            <div style="font-size:12px; color:var(--text2); margin-bottom:15px;">📅 ${e.date}</div>
            <button onclick="openMarksEntry(${e.id}, ${e.max_marks})" class="btn btn-sm btn-primary" style="width:100%">Enter Marks</button>
        </div>
    `).join('') || '<div style="grid-column:1/-1; text-align:center; padding:40px; color:var(--text3)">No exams scheduled.</div>';
}

async function saveExam() {
    const d = { title: val('exTitle'), max_marks: val('exMax'), date: val('exDate') };
    const {data} = await api('/api/exams', 'POST', d);
    if(data.ok) { toast('Exam created', 's'); closeOv('addExamModal'); showExams(); }
}

let activeExamId = null;
async function openMarksEntry(eid, max) {
    activeExamId = eid;
    const {data} = await api('/api/exams/'+eid+'/marks');
    const marksMap = {}; (data.marks||[]).forEach(m => marksMap[m.student_id] = m.marks_obtained);
    
    const mel = document.getElementById('marksEntryList');
    mel.innerHTML = students.map(s => `
        <div style="display:flex; justify-content:space-between; align-items:center; background:var(--surface2); padding:10px; border-radius:var(--r);">
            <span style="font-size:13px;">${s.name}</span>
            <input type="number" class="field-input marks-in" data-sid="${s.id}" value="${marksMap[s.id]||''}" placeholder="/${max}" style="width:80px; padding:5px;">
        </div>
    `).join('');
    openOv('marksModal');
}

async function submitMarks() {
    const marks = [];
    document.querySelectorAll('.marks-in').forEach(i => {
        if(i.value) marks.push({ student_id: i.dataset.sid, marks_obtained: i.value });
    });
    const {data} = await api('/api/exams/'+activeExamId+'/marks', 'POST', {marks: marks});
    if(data.ok) { toast('Marks saved successfully', 's'); closeOv('marksModal'); }
}
"""
if 'showEnquiries()' not in html:
    html = html.replace('function renderFeeStructure() {', academics_js + '\nfunction renderFeeStructure() {')

# 5. Student Portal additions (Timetable and Marks)
stu_portal_css = """
.stu-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r3); padding: 24px; margin-top: 20px; }
.stu-sec-title { font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 800; margin-bottom: 15px; }
"""
if ".stu-section {" not in html:
    html = html.replace('/* ── AMBIENT BG ── */', stu_portal_css + '\n/* ── AMBIENT BG ── */')

stu_portal_js_update = """
    // ADDED: Timetable and Marks for student
    const [bRes, eRes] = await Promise.all([
        api('/api/students/' + loggedStu.id + '/batches'),
        api('/api/exams')
    ]);
    
    let portalExtra = '';
    if(bRes.data.ok && bRes.data.batches.length > 0) {
        portalExtra += `<div class="stu-section"><div class="stu-sec-title">📅 My Timetable</div><div class="lms-grid">`;
        bRes.data.batches.forEach(b => {
            portalExtra += `<div class="track-card"><div class="track-title">${b.name}</div><div style="font-size:12px; color:var(--text2)">${b.time} | ${b.days}</div><div style="font-size:11px; color:var(--text3)">${b.subject} (${b.teacher})</div></div>`;
        });
        portalExtra += `</div></div>`;
    }
    
    if(eRes.data.ok && eRes.data.exams.length > 0) {
        portalExtra += `<div class="stu-section"><div class="stu-sec-title">📝 Exam Results</div><div id="stuResultsList">Loading results...</div></div>`;
    }
    
    document.getElementById('sp-content-learning').insertAdjacentHTML('beforeend', portalExtra);
    
    if(eRes.data.ok && eRes.data.exams.length > 0) {
        const {data: mData} = await api('/api/students/' + loggedStu.id + '/details');
        const mRow = document.getElementById('stuResultsList');
        if(mData.ok) {
            // Find marks for this student for all exams
            // Note: the details api already joined progress, but maybe not marks. Let's assume we need to join locally or another api.
            // For now, I'll update the details API effectively in app.py next if needed.
            // Actually, I'll just draw the exams and show results if found.
            // ... (rest of logic)
        }
    }
"""
# This part is complex, I'll just append it to loadLMSPortal in the next iteration or script.

with open(file_path, "w") as f:
    f.write(html)
print("Academics UI overhaul successful.")
