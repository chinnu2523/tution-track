// ══════════════════════════════════════════════════════
//  CONSTANTS & STATE
// ══════════════════════════════════════════════════════
const MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const MF=['January','February','March','April','May','June','July','August','September','October','November','December'];
const CM=new Date().getMonth(), CY=new Date().getFullYear();

let students=[], editId=null, delId=null, fmM={}, curRole=null, loggedStu=null;

// ══════════════════════════════════════════════════════
//  UTILS
// ══════════════════════════════════════════════════════
const esc = s => String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const fmtD = iso => (!iso) ? '—' : new Date(iso).toLocaleDateString('en-IN', {day:'numeric', month:'short', year:'numeric'});
const defM = () => { const m={}; MONTHS.forEach(n => m[n]=false); return m; };

async function api(path, method='GET', body=null) {
    const opts = {method, headers:{}};
    if (body) { opts.headers['Content-Type']='application/json'; opts.body=JSON.stringify(body); }
    try {
        const res = await fetch(path, opts);
        const data = await res.json();
        return {status: res.status, data};
    } catch(e) { return {status: 500, data: {ok: false, error: e.message}}; }
}

function toast(msg, type='i') {
    const z = document.getElementById('toastZone');
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<span style="font-size:14px">${{s:'✓',e:'✕',i:'ℹ'}[type]||'ℹ'}</span><span>${msg}</span>`;
    z.appendChild(t);
    setTimeout(() => { t.style.opacity='0'; t.style.transform='translateX(110%)'; setTimeout(()=>t.remove(), 300); }, 3000);
}

// ══════════════════════════════════════════════════════
//  NAVIGATION & UI
// ══════════════════════════════════════════════════════
function showPage(id) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

function selectRole(role) {
    document.getElementById('tab-admin').classList.toggle('active', role==='admin');
    document.getElementById('tab-student').classList.toggle('active', role==='student');
    document.getElementById('adminLoginForm').style.display = role==='admin'?'block':'none';
    document.getElementById('studentLoginForm').style.display = role==='student'?'block':'none';
}

function showSection(sid) {
    const sections = ['adminDashboardSection', 'enquiriesSection', 'batchesSection', 'examsSection', 'settingsSection', 'attendanceSection', 'expenseSection'];
    sections.forEach(s => {
        const el = document.getElementById(s);
        if(!el) return;
        if(s === sid) { el.style.display='block'; setTimeout(()=>el.classList.add('active'), 10); } 
        else { el.classList.remove('active'); el.style.display='none'; }
    });
}
function showDashboard() { showSection('adminDashboardSection'); refreshDashboard(); }
function showEnquiries() { showSection('enquiriesSection'); loadEnquiries(); }
function showBatches() { showSection('batchesSection'); loadBatches(); }
function showExams() { showSection('examsSection'); loadExams(); }
function showSettings() { showSection('settingsSection'); }
function showAttendance() { showSection('attendanceSection'); loadAttendance(); }
function showExpenses() { showSection('expenseSection'); loadExpenses(); }

function openOv(id) { document.getElementById(id).classList.add('open'); }
function closeOv(id) { document.getElementById(id).classList.remove('open'); }

async function loadEnquiries() {
    const {data} = await api('/api/enquiries');
    if(!data.ok) return;
    document.getElementById('enquiryTableBody').innerHTML = data.enquiries.map(e => `
        <tr>
            <td><strong>${esc(e.name)}</strong></td>
            <td>${esc(e.phone)}</td>
            <td>${esc(e.grade || '—')}</td>
            <td><span class="cbadge" style="background:rgba(245,158,11,0.1); color:var(--amber)">${esc(e.status)}</span></td>
            <td>${fmtD(e.created_at)}</td>
            <td><button class="btn btn-sm btn-secondary" onclick="updateEnqStatus(${e.id})">Enroll</button></td>
        </tr>
    `).join('') || '<tr><td colspan="6" style="text-align:center; padding:40px; color:var(--text3)">No enquiries found</td></tr>';
}

async function loadBatches() {
    const {data} = await api('/api/batches');
    if(!data.ok) return;
    document.getElementById('batchTableBody').innerHTML = data.batches.map(b => `
        <tr><td><strong>${esc(b.name)}</strong></td><td>${esc(b.subject)}</td><td>${esc(b.time)} (${esc(b.days)})</td><td>${esc(b.teacher)}</td><td>${esc(b.room || '—')}</td></tr>
    `).join('') || '<tr><td colspan="5" style="text-align:center; padding:40px; color:var(--text3)">No batches found</td></tr>';
}

async function loadExams() {
    const {data} = await api('/api/exams');
    if(!data.ok) return;
    document.getElementById('examTableBody').innerHTML = data.exams.map(e => `
        <tr><td>${fmtD(e.date)}</td><td><strong>${esc(e.title)}</strong></td><td>${e.max_marks}</td><td>${esc(e.class_name || 'All')}</td><td><button class="btn btn-sm btn-primary" onclick="openMarksModal(${e.id}, '${esc(e.title)}')">Marks</button></td></tr>
    `).join('') || '<tr><td colspan="5" style="text-align:center; padding:40px; color:var(--text3)">No exams scheduled</td></tr>';
}

function exportBackup() { window.open('/api/admin/backup', '_blank'); }

// ══════════════════════════════════════════════════════
//  DATA & FILTERS
// ══════════════════════════════════════════════════════
async function loadData() {
    const {data} = await api('/api/students');
    if (data && data.ok) students = data.students;
    else students = [];
}
function saveData() {}
function genId(){return 'st_'+Date.now()+'_'+Math.random().toString(36).slice(2,6);}


// ══════════════════════════════════════════════════════
//  ADMIN TABLE
// ══════════════════════════════════════════════════════
function renderTable() {
    const q = document.getElementById('searchInput').value.toLowerCase();
    const c = document.getElementById('filterClass').value;
    const s = document.getElementById('filterSchool').value;
    const m = document.getElementById('filterMonth').value;
    const st = document.getElementById('filterStatus').value;

    const f = students.filter(x => {
        const matchesQ = x.name.toLowerCase().includes(q) || x.phone.includes(q);
        const matchesC = !c || x.class === c;
        const matchesS = !s || x.school === s;
        const matchesM = !m || x.months[m];
        const matchesSt = !st || (st === 'due' ? !x.months[MONTHS[CM]] : x.months[MONTHS[CM]]);
        return matchesQ && matchesC && matchesS && matchesM && matchesSt;
    });

    const tbody = document.getElementById('tbody');
    if(!tbody) return;
    tbody.innerHTML = f.map((x, i) => {
        const pc = MONTHS.filter(m => x.months[m]).length;
        const pct = Math.round(pc/12*100);
        return `
            <tr>
                <td style="color:var(--text3);font-family:'DM Mono',monospace;font-size:11px">${i+1}</td>
                <td><div class="sname">${esc(x.name)}</div><div class="smeta">${fmtD(x.created_at)}</div></td>
                <td style="color:var(--text2);font-size:13px">${esc(x.school)}</td>
                <td><span class="cbadge">${esc(x.class)}</span></td>
                <td><a href="tel:${esc(x.phone)}" style="color:var(--text2);text-decoration:none;font-size:13px">${esc(x.phone)}</a></td>
                <td><span class="fee-m">₹${(x.joiningFee||0).toLocaleString()}</span></td>
                <td><span class="fee-m">₹${(x.monthlyFee||0).toLocaleString()}</span></td>
                <td><div class="prog-wrap"><div class="prog-bar" style="width:${pct}%"></div></div><div style="font-size:10px;color:var(--text3);margin-top:2px;font-family:'DM Mono',monospace">${pc}/12</div></td>
                ${MONTHS.map((m, mi) => `<td class="mcell"><button class="mt ${x.months[m]?'paid':'unpaid'}" onclick="toggleMonth('${x.id}','${m}')" title="${x.months[m]?'Paid':'Unpaid'} — ${m}" style="${mi===CM?'outline:2px solid var(--blue);outline-offset:2px':''}">${x.months[m]?'✓':'✕'}</button></td>`).join('')}
                <td><div style="display:flex;gap:5px"><button class="btn btn-secondary btn-sm" onclick="openEditModal('${x.id}')">Edit</button><button class="btn btn-danger btn-sm" onclick="openDelConfirm('${x.id}')">Del</button></div></td>
            </tr>
        `;
    }).join('');
    document.getElementById('tCount').textContent = `${f.length} of ${students.length} students`;
    document.getElementById('tMonthLabel').textContent = `Current: ${MF[CM]} ${CY}`;
}

async function refreshDashboard() {
    const {data} = await api('/api/dashboard/stats');
    if(!data.ok) return;
    const set = (id, val) => { const el = document.getElementById(id); if(el) el.textContent = val; };
    set('hTotal', data.total_students);
    set('hMonthlyColl', '₹' + data.monthly_collection.toLocaleString());
    set('hExpenses', '₹' + data.monthly_expenses.toLocaleString());
    set('hNetProfit', '₹' + data.net_profit.toLocaleString());
    set('hPending', data.pending_fee_students);
    set('hOverdue', data.overdue_list.length);

    const rpList = document.getElementById('recentPaymentsList');
    if(rpList) rpList.innerHTML = (data.recent_payments || []).map(p => `<div style="display:flex; justify-content:space-between; padding:10px; background:rgba(255,255,255,0.03); border-radius:8px; border-left:3px solid var(--blue)"><div><div style="font-weight:600">${esc(p.name)}</div><div style="font-size:11px; color:var(--text3)">${p.month} — ${p.mode}</div></div><div style="text-align:right"><div class="g" style="font-weight:600">₹${p.amount}</div><div style="font-size:11px; color:var(--text3)">${fmtD(p.paid_at)}</div></div></div>`).join('') || '<div style="color:var(--text3); text-align:center; padding:20px;">No recent payments</div>';

    const odList = document.getElementById('quickOverdueList');
    if(odList) odList.innerHTML = (data.overdue_list || []).map(o => `<div style="display:flex; justify-content:space-between; padding:10px; background:rgba(244,63,94,0.05); border-radius:8px; border-left:3px solid var(--red)"><div><div style="font-weight:600">${esc(o.name)}</div><div style="font-size:11px; color:var(--text3)">${esc(o.phone)}</div></div><div style="text-align:right"><div class="r" style="font-weight:600">₹${o.amount}</div><button class="btn btn-sm btn-secondary" style="margin-top:4px" onclick="openEditModal('${o.id}')">Fix</button></div></div>`).join('') || '<div style="color:var(--text3); text-align:center; padding:20px;">All fees clear! 🎉</div>';
}
function updateStats() { refreshDashboard(); }
function updateDashboard() { refreshDashboard(); }

function updateFilters() {
    const cls = [...new Set(students.map(s => s.class))].sort();
    const sch = [...new Set(students.map(s => s.school))].sort();
    const fc = document.getElementById('filterClass'), fs = document.getElementById('filterSchool');
    if(fc) fc.innerHTML = '<option value="">All Classes</option>' + cls.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('');
    if(fs) fs.innerHTML = '<option value="">All Schools</option>' + sch.map(s => `<option value="${esc(s)}">${esc(s)}</option>`).join('');
    const fm = document.getElementById('filterMonth');
    if(fm) fm.innerHTML = '<option value="">Month</option>' + MONTHS.map((m,i) => `<option value="${m}"${i===CM?' selected':''}>${MF[i]}</option>`).join('');
}

async function toggleMonth(id, month) {
    const s = students.find(x => x.id === id); if(!s) return;
    const old = s.months[month];
    s.months[month] = !s.months[month];
    const {data} = await api('/api/students/' + id, 'PUT', s);
    if(data.ok) {
        renderTable(); refreshDashboard();
        toast(`${s.name} — ${month}: ${s.months[month]?'✓ Paid':'✗ Unpaid'}`, s.months[month]?'s':'i');
    } else {
        s.months[month] = old;
        toast('Update failed', 'e');
    }
}

// ══════════════════════════════════════════════════════
//  STUDENT PORTAL
// ══════════════════════════════════════════════════════
// ══════════════════════════════════════════════════════
//  STUDENT PORTAL
// ══════════════════════════════════════════════════════
function renderStudentPortal(s) {
    const pc = MONTHS.filter(m => s.months[m]).length;
    const tDue = (12 - pc) * (s.monthlyFee || 0);
    const curPaid = s.months[MONTHS[CM]];

    document.getElementById('stuPortalContent').innerHTML = `
        <div class="stu-hero">
            <div class="stu-hero-top">
                <div class="stu-av">${s.name[0].toUpperCase()}</div>
                <div class="stu-info">
                    <h2>${esc(s.name)}</h2><div style="color:var(--text2);font-size:14px">${esc(s.school)}</div>
                    <div class="stu-tags">
                        <span class="stag">${esc(s.class)}</span><span class="stag">📞 ${esc(s.phone)}</span>
                        <span class="stag ${curPaid?'g':'r'}">${curPaid?'✓ Paid':'⚠ Due'}</span>
                        <span class="stag">Joined ${fmtD(s.created_at)}</span>
                    </div>
                </div>
            </div>
            <div class="fee-summary">
                <div class="fsum"><div class="fsum-label">Monthly Fee</div><div class="fsum-val">₹${(s.monthlyFee||0).toLocaleString()}</div></div>
                <div class="fsum"><div class="fsum-label">Joining Fee</div><div class="fsum-val">₹${(s.joiningFee||0).toLocaleString()}</div></div>
                <div class="fsum"><div class="fsum-label">Months Paid</div><div class="fsum-val g">${pc} / 12</div></div>
                <div class="fsum"><div class="fsum-label">Total Paid</div><div class="fsum-val g">₹${(s.totalPaid||0).toLocaleString()}</div></div>
                <div class="fsum"><div class="fsum-label">Balance Due</div><div class="fsum-val ${tDue>0?'r':'g'}">₹${tDue.toLocaleString()}</div></div>
                <div class="fsum"><div class="fsum-label">This Month</div><div class="fsum-val ${curPaid?'g':'r'}">${curPaid?'✓ Paid':'✗ Unpaid'}</div></div>
            </div>
        </div>
        <div class="cal-section">
            <div class="cal-title">Fee Payment Calendar — ${CY}</div>
            <div class="cal-grid">${MONTHS.map((m, i) => `<div class="cal-card ${s.months[m]?'paid':''} ${i===CM?'cur':''}"><div class="cal-mname">${m}</div><div class="cal-status ${s.months[m]?'paid':'unpaid'}">${s.months[m]?'Paid':'Pending'}</div><div class="cal-amt">₹${(s.monthlyFee||0).toLocaleString()}</div></div>`).join('')}</div>
        </div>
    `;
}

// ══════════════════════════════════════════════════════
//  AUTH & SESSION
// ══════════════════════════════════════════════════════
async function adminLogin() {
    const u = document.getElementById('adminUser').value.trim();
    const p = document.getElementById('adminPass').value;
    const {data} = await api('/api/login/admin', 'POST', {username:u, password:p});
    if(data.ok) {
        curRole = 'admin'; document.getElementById('adminUDisplay').textContent = data.user;
        showPage('adminPage'); showSection('adminDashboardSection');
        await loadData(); refreshDashboard(); renderTable(); updateFilters();
        toast('Welcome, ' + data.user + '!', 's');
    } else toast(data.error || 'Login failed', 'e');
}

async function studentLogin() {
    const n = document.getElementById('stuName').value.trim();
    const ph = document.getElementById('stuPhone').value.trim();
    const {data} = await api('/api/login/student', 'POST', {name:n, phone:ph});
    if(data.ok) {
        curRole = 'student'; loggedStu = data.student;
        document.getElementById('stuDispName').textContent = data.student.name;
        document.getElementById('stuAvChar').textContent = data.student.name[0].toUpperCase();
        renderStudentPortal(data.student); showPage('studentPage');
        toast('Welcome, ' + data.student.name + '!', 's');
    } else toast(data.error || 'Student not found', 'e');
}

async function logout() {
    await api('/api/logout', 'POST'); curRole = null; loggedStu = null;
    showPage('loginPage'); toast('Logged out', 'i');
}

async function restoreSession() {
    const {data} = await api('/api/auth/me');
    if(data.ok) {
        if(data.user.role === 'admin') {
            curRole = 'admin'; document.getElementById('adminUDisplay').textContent = data.user.user_id;
            showPage('adminPage'); showSection('adminDashboardSection');
            await loadData(); refreshDashboard(); renderTable(); updateFilters();
            return true;
        } else if(data.user.role === 'student') {
            const res = await api('/api/student/me');
            if(res.data.ok) {
                curRole = 'student'; loggedStu = res.data.student;
                renderStudentPortal(loggedStu); showPage('studentPage');
                return true;
            }
        }
    }
    return false;
}

// ══════════════════════════════════════════════════════
//  MODALS & CRUD
// ══════════════════════════════════════════════════════
function openAddModal() { editId=null; fmM=defM(); document.getElementById('modalTitle').textContent='Add Student'; clearForm(); openOv('stuModal'); }
async function openEditModal(id) {
    const s = students.find(x => x.id === id); if(!s) return;
    editId = id; fmM = {...s.months};
    document.getElementById('modalTitle').textContent = 'Edit — ' + s.name;
    document.getElementById('fName').value = s.name; document.getElementById('fSchool').value = s.school;
    document.getElementById('fClass').value = s.class; document.getElementById('fPhone').value = s.phone;
    document.getElementById('fJoining').value = s.joiningFee || ''; document.getElementById('fMonthly').value = s.monthlyFee || '';
    openOv('stuModal');
}

async function saveStudent() {
    const p = {
        name: document.getElementById('fName').value,
        school: document.getElementById('fSchool').value,
        class: document.getElementById('fClass').value,
        phone: document.getElementById('fPhone').value,
        joiningFee: Number(document.getElementById('fJoining').value),
        monthlyFee: Number(document.getElementById('fMonthly').value),
        months: fmM
    };
    const res = await api('/api/students' + (editId ? '/' + editId : ''), editId ? 'PUT' : 'POST', p);
    if(res.data.ok) { toast('Student saved', 's'); closeOv('stuModal'); await loadData(); renderTable(); refreshDashboard(); }
    else toast(res.data.error || 'Failed to save', 'e');
}
async function confirmDelete() {
    if(!delId) return;
    const res = await api('/api/students/' + delId, 'DELETE');
    if(res.data.ok) { toast('Student deleted', 'i'); closeOv('confirmModal'); await loadData(); renderTable(); refreshDashboard(); }
}

async function saveEnquiry() {
    const p = { name: document.getElementById('enqName').value, phone: document.getElementById('enqPhone').value, grade: document.getElementById('enqGrade').value, notes: document.getElementById('enqNotes').value };
    const res = await api('/api/enquiries', 'POST', p);
    if(res.data.ok) { toast('Enquiry saved', 's'); closeOv('addEnquiryModal'); loadEnquiries(); }
}

async function saveBatch() {
    const p = { name: document.getElementById('btName').value, time: document.getElementById('btTime').value, days: document.getElementById('btDays').value, subject: document.getElementById('btSub').value, teacher: document.getElementById('btTeacher').value };
    const res = await api('/api/batches', 'POST', p);
    if(res.data.ok) { toast('Batch created', 's'); closeOv('addBatchModal'); loadBatches(); }
}

async function saveExam() {
    const p = { title: document.getElementById('exTitle').value, max_marks: document.getElementById('exMax').value, date: document.getElementById('exDate').value };
    const res = await api('/api/exams', 'POST', p);
    if(res.data.ok) { toast('Exam scheduled', 's'); closeOv('addExamModal'); loadExams(); }
}

// ══════════════════════════════════════════════════════
//  ATTENDANCE & MARKS
// ══════════════════════════════════════════════════════
async function loadAttendance() {
    const d = document.getElementById('attDate').value; if(!d) return;
    const [sRes, aRes] = await Promise.all([api('/api/students'), api('/api/attendance?date='+d)]);
    if(sRes.data.ok && aRes.data.ok) {
        const attMap = {}; aRes.data.attendance.forEach(a => attMap[a.student_id] = a.status);
        document.getElementById('attTableBody').innerHTML = sRes.data.students.map(s => `
            <tr>
                <td>${esc(s.name)}</td><td>${esc(s.class)}</td>
                <td><div class="att-box" style="margin:0;"><div class="att-btn p ${attMap[s.id]==='P'?'act':''}" onclick="setAtt('${s.id}','P')">P</div><div class="att-btn a ${attMap[s.id]==='A'?'act':''}" onclick="setAtt('${s.id}','A')">A</div></div></td>
            </tr>
        `).join('');
    }
}

async function setAtt(sid, st) {
    const d = document.getElementById('attDate').value;
    const res = await api('/api/attendance', 'POST', {student_id: sid, date: d, status: st});
    if(res.data.ok) { toast('Marked ' + st, 's'); loadAttendance(); }
}

// ══════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════


function clearForm() { ['fName','fSchool','fClass','fPhone','fJoining', 'fMonthly'].forEach(id => document.getElementById(id).value = ''); }
function openDelConfirm(id) { delId=id; openOv('confirmModal'); }


async function saveBulkAttendance() {
    const date = document.getElementById('attDate').value;
    const records = [];
    document.querySelectorAll('#attTableBody tr').forEach(tr => {
        const act = tr.querySelector('.att-btn.act');
        if(act) {
            const sid = act.getAttribute('onclick').match(/'([^']+)'\)$/)[1];
            records.push({student_id: sid, status: act.textContent});
        }
    });
    const {data} = await api('/api/attendance/bulk', 'POST', {date, records});
    if(data.ok) toast('Attendance saved for '+records.length+' students', 's');
}

// Expense JS
async function loadExpenses() {
    const list = document.getElementById('expenseTableBody');
    list.innerHTML = '<tr><td colspan="6">Loading...</td></tr>';
    const {data} = await api('/api/expenses');
    if(data.ok) {
        list.innerHTML = data.expenses.map(e => `
            <tr>
                <td>${esc(e.date)}</td>
                <td class="sname">${esc(e.title)}</td>
                <td><span class="cbadge">${esc(e.category)}</span></td>
                <td class="fee-m">₹${e.amount.toLocaleString()}</td>
                <td>${esc(e.mode)}</td>
                <td><button class="btn btn-sm btn-danger" onclick="deleteExpense('${e.id}')">Delete</button></td>
            </tr>
        `).join('') || '<tr><td colspan="6">No expenses found</td></tr>';
    }
}

async function saveExpense() {
    const title = document.getElementById('expTitle').value;
    const amount = Number(document.getElementById('expAmount').value);
    const category = document.getElementById('expCat').value;
    const date = document.getElementById('expDate').value;
    const mode = document.getElementById('expMode').value;
    
    if(!title || !amount || !date) { toast('Please fill all required fields', 'e'); return; }
    
    const {data} = await api('/api/expenses', 'POST', {title, amount, category, date, mode});
    if(data.ok) {
        toast('Expense recorded', 's');
        closeOv('addExpenseModal');
        loadExpenses();
    }
}

async function deleteExpense(eid) {
    if(!confirm('Delete this expense?')) return;
    const {data} = await api('/api/expenses/'+eid, 'DELETE');
    if(data.ok) {
        toast('Expense deleted', 's');
        loadExpenses();
    }
}

window.seedDemo = function() {};

window.onload = async () => {
  try {
    const restored = await restoreSession();
    if(!restored) showPage('loginPage');
    else showSection('adminDashboardSection'); 
  } catch(e) {
    console.error("Init Error:", e);
    showPage('loginPage');
  } finally {
    const cn = localStorage.getItem('tt_center_name');
    if(cn) document.querySelectorAll('.logo-name').forEach(el => el.innerHTML = `${esc(cn)}<span>Track</span>`);

    setTimeout(()=>{
      const ls = document.getElementById('loadScreen');
      if(ls) {
        ls.style.transition = 'opacity 0.5s'; 
        ls.style.opacity = '0'; 
        setTimeout(()=>ls.remove(), 500);
      }
    }, 400);
  }
};

function toggleTheme() {
    document.body.classList.toggle('light-mode');
}

function showOverdue() {
    document.getElementById('adminDashboardSection').scrollIntoView({behavior: 'smooth'});
    toast('Showing overdue list', 'i');
}

function exportCSV() {
    if(!students.length) return toast('No data to export', 'e');
    const headers = ['Name', 'Phone', 'School', 'Class', 'MonthlyFee', ...MONTHS];
    const rows = students.map(s => [
        `"${s.name}"`, `"${s.phone}"`, `"${s.school}"`, `"${s.class}"`, s.monthlyFee,
        ...MONTHS.map(m => s.months[m] ? 'Paid' : 'Unpaid')
    ].join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `TuitionTrack_Students_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
}

async function changePwd() {
    const cur = document.getElementById('curPwd').value;
    const newP = document.getElementById('newPwd').value;
    const conf = document.getElementById('confPwd').value;
    if(!cur || !newP || !conf) return toast('Fill all fields', 'e');
    if(newP !== conf) return toast('Passwords do not match', 'e');
    if(newP.length < 6) return toast('Min 6 chars req', 'e');
    
    const {data} = await api('/api/admin/change_pwd', 'POST', {current: cur, new: newP});
    if(data && data.ok) {
        toast('Password updated', 's');
        ['curPwd', 'newPwd', 'confPwd'].forEach(id => document.getElementById(id).value = '');
    } else {
        toast(data?.error || 'Update failed', 'e');
    }
}

function saveSettings() {
    const name = document.getElementById('setCenterName').value;
    if(name) {
        localStorage.setItem('tt_center_name', name);
        document.querySelectorAll('.logo-name').forEach(el => el.innerHTML = `${esc(name)}<span>Track</span>`);
        toast('Profile updated', 's');
    }
}

async function updateEnqStatus(eid) {
    const {data} = await api('/api/enquiries/'+eid+'/status', 'PUT', {status: 'Enrolled'});
    if(data.ok) { toast('Enquiry enrolled', 's'); loadEnquiries(); }
}

let activeExamId = null;
async function openMarksModal(eid, title) {
    activeExamId = eid;
    document.querySelector('#marksModal h2').textContent = 'Marks: ' + title;
    const {data: sData} = await api('/api/students');
    const {data: mData} = await api('/api/exams/'+eid+'/marks');
    const existing = {};
    if(mData && mData.ok) { mData.marks.forEach(m => existing[m.student_id] = m.marks_obtained); }
    if(sData && sData.ok) {
        document.getElementById('marksEntryList').innerHTML = sData.students.map(s => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px; border-bottom:1px solid var(--border);">
                <span>${esc(s.name)} <small>(${esc(s.class)})</small></span>
                <input type="number" class="field-input mark-input" data-sid="${s.id}" value="${existing[s.id]||''}" style="width:80px; padding:5px;">
            </div>
        `).join('');
    }
    openOv('marksModal');
}

async function submitMarks() {
    if(!activeExamId) return;
    const inputs = document.querySelectorAll('.mark-input');
    const marks = [];
    inputs.forEach(inp => {
        if(inp.value !== '') marks.push({student_id: inp.dataset.sid, marks_obtained: Number(inp.value)});
    });
    const {data} = await api('/api/exams/'+activeExamId+'/marks', 'POST', {marks});
    if(data.ok) { toast('Marks saved!', 's'); closeOv('marksModal'); }
}

function confirmPayment() {
    toast('Payment processed', 's');
    closeOv('payModal');
}
