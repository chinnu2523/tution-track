import os
import re

file_path = "/Users/madarauchiha/Tution Center/tuition-center.html"
with open(file_path, "r") as f:
    html = f.read()

# 1. Update Navigation and Pages
if 'showSettings()' not in html:
    header_right_old = '<div class="header-right">'
    header_right_new = '<div class="header-right">\n        <button class="btn-logout" onclick="showSettings()" style="margin-right:5px;">⚙️ Settings</button>'
    html = html.replace(header_right_old, header_right_new, 1)

# Add Settings Page HTML
settings_page_html = """
  <!-- SETTINGS PAGE -->
  <section id="settingsPage" class="page">
    <header class="tt-header">
      <div class="header-inner">
        <div class="logo-area" onclick="showPage('adminPage')" style="cursor:pointer">
          <div class="logo-badge">📚</div>
          <div class="logo-name">Tuition<span>Track</span></div>
        </div>
        <div class="header-right">
          <button class="btn-logout" onclick="showPage('adminPage')">Back to Dashboard</button>
        </div>
      </div>
    </header>
    <main>
      <div class="cpwd-section">
        <h3>Class-wise Fee Structure</h3>
        <p style="font-size:12px; color:var(--text2); margin-bottom:15px;">Set the default monthly fee for each class. This will be used when adding new students.</p>
        <div class="form-row" style="max-width:500px;">
          <div class="fg"><label>Class Name</label><input type="text" id="setClassName" class="field-input" placeholder="e.g. Class 10"></div>
          <div class="fg"><label>Monthly Fee</label><input type="number" id="setClassFee" class="field-input" placeholder="1500"></div>
          <button class="btn-login admin" onclick="saveFeeStructure()" style="width:120px; margin-top:20px;">Save</button>
        </div>
        <div id="feeStructureList" style="margin-top:20px; display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:10px;">
          <!-- List items here -->
        </div>
      </div>
    </main>
  </section>
"""
if 'id="settingsPage"' not in html:
    html = html.replace('</section>\n  <main>', '</section>\n' + settings_page_html + '\n  <main>')

# 2. Update Dashboard UI (adminPage)
dashboard_overhaul = """
    <div class="summary-grid">
      <div class="scard c1"><div class="scard-glow"></div><div class="scard-icon">👥</div><div class="scard-label">Total Students</div><div class="scard-value" id="hTotal">0</div></div>
      <div class="scard c2"><div class="scard-glow"></div><div class="scard-icon">💰</div><div class="scard-label">Monthly Collection</div><div class="scard-value" id="hMonthlyColl">₹0</div></div>
      <div class="scard c3"><div class="scard-glow"></div><div class="scard-icon">⏳</div><div class="scard-label">Pending Fees</div><div class="scard-value" id="hPending">0</div></div>
      <div class="scard c4"><div class="scard-glow"></div><div class="scard-icon">⚠️</div><div class="scard-label">Overdue List</div><div class="scard-value" id="hOverdue">0</div></div>
    </div>
    
    <div style="display:grid; grid-template-columns: 1.5fr 1fr; gap:20px; margin-bottom:20px;">
      <div class="cpwd-section">
        <h3>Recent Payments</h3>
        <div id="recentPaymentsList" style="font-size:13px; display:flex; flex-direction:column; gap:10px;">
          <div style="color:var(--text3)">Loading recent payments...</div>
        </div>
      </div>
      <div class="cpwd-section">
        <h3>Quick Overdue List</h3>
        <div id="quickOverdueList" style="font-size:13px; display:flex; flex-direction:column; gap:10px;">
          <div style="color:var(--text3)">No overdue payments currently.</div>
        </div>
      </div>
    </div>
"""
if 'Total Students' in html:
    # Try to find the summary-grid block and replace it
    html = re.sub(r'<div class="summary-grid">.*?</div>', dashboard_overhaul, html, flags=re.DOTALL)

# 3. Pay Fee Modal
pay_fee_modal = """
<!-- PAY FEE MODAL -->
<div class="overlay" id="payModal">
  <div class="modal" style="max-width:400px;">
    <div class="modal-header">
      <h2 id="payModalTitle">Pay Monthly Fee</h2>
      <button class="close-btn" onclick="closeOv('payModal')">&times;</button>
    </div>
    <div class="modal-body" style="padding:24px;">
      <div class="form-field"><label>Month</label><input type="text" id="payMonth" class="field-input" readonly></div>
      <div class="form-field"><label>Amount</label><input type="number" id="payAmount" class="field-input"></div>
      <div class="form-field">
        <label>Payment Mode</label>
        <select id="payMode" class="field-input" style="appearance:auto;">
          <option value="Cash">Cash</option>
          <option value="UPI">UPI</option>
          <option value="Bank">Bank Transfer</option>
        </select>
      </div>
      <div class="form-field"><label>Remarks</label><input type="text" id="payRemarks" class="field-input" placeholder="Optional notes"></div>
      <button class="btn-login admin" onclick="confirmPayment()" style="margin-top:10px;">Confirm Payment</button>
    </div>
  </div>
</div>
"""
if 'id="payModal"' not in html:
    html = html.replace('</body>', pay_fee_modal + '\n</body>')

# 4. Receipt Template
receipt_template = """
<div id="receiptTemplate" style="display:none; padding:40px; font-family:serif; color:#000; background:#fff;">
  <div style="text-align:center; margin-bottom:20px;">
    <h1 style="margin:0;">TuitionTrack Receipt</h1>
    <p style="margin:5px 0;">Official Fee Acknowledgement</p>
  </div>
  <hr>
  <div style="display:flex; justify-content:space-between; margin:20px 0;">
    <div><strong>Student:</strong> <span id="rctStudent"></span></div>
    <div><strong>Date:</strong> <span id="rctDate"></span></div>
  </div>
  <div style="margin:20px 0;">
    <table style="width:100%; border-collapse:collapse;">
      <tr style="border-bottom:1px solid #ddd;"><th style="text-align:left; padding:10px;">Description</th><th style="text-align:right; padding:10px;">Amount</th></tr>
      <tr><td style="padding:10px;" id="rctDesc">Monthly Fee - </td><td style="text-align:right; padding:10px;">₹<span id="rctAmount"></span></td></tr>
    </table>
  </div>
  <div style="margin:20px 0;"><strong>Payment Mode:</strong> <span id="rctMode"></span></div>
  <div style="margin:20px 0;"><strong>Receipt ID:</strong> <span id="rctId"></span></div>
  <div style="margin-top:50px; text-align:right;">
    <p>____________________</p>
    <p>Authorized Signature</p>
  </div>
</div>
"""
if 'id="receiptTemplate"' not in html:
    html = html.replace('</body>', receipt_template + '\n</body>')

# 5. JS Functionality
js_logic = r"""
let feeStructure = [];

async function showSettings() {
    showPage('settingsPage');
    const {data} = await api('/api/settings/fee-structure');
    if(data.ok) {
        feeStructure = data.fee_structure;
        renderFeeStructure();
    }
}

function renderFeeStructure() {
    const list = document.getElementById('feeStructureList');
    list.innerHTML = feeStructure.map(f => `
        <div class="scard" style="padding:15px;">
            <div style="font-weight:700;">${f.class_name}</div>
            <div style="color:var(--blue); font-size:18px;">₹${f.monthly_fee}</div>
        </div>
    `).join('');
}

async function saveFeeStructure() {
    const cn = document.getElementById('setClassName').value;
    const cf = document.getElementById('setClassFee').value;
    if(!cn || !cf) return toast('Fill all fields', 'e');
    const {data} = await api('/api/settings/fee-structure', 'POST', {class_name: cn, monthly_fee: cf});
    if(data.ok) {
        toast('Updated ' + cn, 's');
        showSettings();
    }
}

async function updateDashboard() {
    const {data} = await api('/api/dashboard/stats');
    if(data.ok) {
        document.getElementById('hTotal').textContent = data.total_students;
        document.getElementById('hMonthlyColl').textContent = '₹' + (data.monthly_collection || 0);
        document.getElementById('hPending').textContent = data.pending_fee_students || 0;
        document.getElementById('hOverdue').textContent = (data.overdue_list || []).length;
        
        const rp = document.getElementById('recentPaymentsList');
        rp.innerHTML = (data.recent_payments || []).map(p => `
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid var(--border); padding-bottom:5px;">
                <span><strong>${p.name}</strong> - ${p.month}</span>
                <span style="color:var(--green)">₹${p.amount} (${p.mode})</span>
            </div>
        `).join('') || '<div style="color:var(--text3)">No recent payments.</div>';
        
        const ql = document.getElementById('quickOverdueList');
        ql.innerHTML = (data.overdue_list || []).map(o => `
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid var(--border); padding-bottom:5px;">
                <span>${o.name} (${o.phone})</span>
                <span style="color:var(--red)">₹${o.amount}</span>
            </div>
        `).join('') || '<div style="color:var(--text3)">All accounts clear!</div>';
    }
}

let pendingPayId = null, pendingPayMonth = null;
function openPayModal(id, month) {
    const s = students.find(x => x.id === id);
    if(!s) return;
    pendingPayId = id; pendingPayMonth = month;
    document.getElementById('payMonth').value = month;
    document.getElementById('payAmount').value = s.monthlyFee;
    openOv('payModal');
}

async function confirmPayment() {
    const amount = document.getElementById('payAmount').value;
    const mode = document.getElementById('payMode').value;
    const remarks = document.getElementById('payRemarks').value;
    
    const {data} = await api('/api/students/' + pendingPayId + '/pay', 'POST', {
        month: pendingPayMonth,
        amount: amount,
        mode: mode,
        remarks: remarks
    });
    
    if(data.ok) {
        toast('Payment recorded! ID: ' + data.receipt_id, 's');
        closeOv('payModal');
        await loadData();
        renderTable();
        updateDashboard();
    } else {
        toast(data.error || 'Payment failed', 'e');
    }
}

async function printReceipt(pId) {
    const s = students.find(x => x.id === editId) || loggedStu;
    const {data} = await api('/api/students/'+s.id+'/details');
    const p = data.payments.find(x => x.id == pId);
    
    document.getElementById('rctStudent').textContent = s.name;
    document.getElementById('rctDate').textContent = new Date(p.paid_at).toLocaleDateString();
    document.getElementById('rctDesc').textContent = 'Monthly Fee - ' + p.month;
    document.getElementById('rctAmount').textContent = p.amount;
    document.getElementById('rctMode').textContent = p.mode;
    document.getElementById('rctId').textContent = p.receipt_id;
    
    const win = window.open('', '', 'width=800,height=600');
    win.document.write('<html><head><title>Receipt</title></head><body>');
    win.document.write(document.getElementById('receiptTemplate').innerHTML);
    win.document.write('</body></html>');
    win.document.close();
    win.print();
}

async function toggleMonth(id, month) {
    const s = students.find(x => x.id === id); if(!s) return;
    if(s.months[month]) {
        // Unpay logic (simple delete)
        s.months[month] = false;
        const {data} = await api('/api/students/' + id, 'PUT', s);
        if(data.ok) { renderTable(); updateDashboard(); toast('Payment Undone', 'i'); }
    } else {
        openPayModal(id, month);
    }
}
"""
if 'showSettings()' not in html:
    html = html.replace('function switchStuTab(t) {', js_logic + '\nfunction switchStuTab(t) {')

# Add dashboard update to main calls
if 'updateDashboard();' not in html:
    html = html.replace('await loadData();', 'await loadData(); updateDashboard();')
if 'updateDashboard();' not in html:
    html = html.replace('renderTable(); updateStats(); updateFilters();', 'renderTable(); updateStats(); updateFilters(); updateDashboard();')

with open(file_path, "w") as f:
    f.write(html)
print("ERP features updated successfully.")
