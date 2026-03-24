import os
import re
import sqlite3
import json

BASE_DIR = "/Users/madarauchiha/Tution Center"
html_path = os.path.join(BASE_DIR, "tuition-center.html")
db_path = os.path.join(BASE_DIR, "tuition.db")

with open(html_path, "r") as f:
    html = f.read()

# 1. LMS CSS Styles (Glassmorphism & Progress)
lms_css = """
.lms-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
.track-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r2); padding: 20px; position: relative; overflow: hidden; }
.track-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.track-title { font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 700; }
.track-level { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--text3); }

.lms-prog-container { height: 6px; background: var(--surface3); border-radius: 99px; margin: 15px 0; overflow: hidden; }
.lms-prog-bar { height: 100%; background: linear-gradient(90deg, var(--blue), var(--violet)); transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); }

.skill-list { display: flex; flex-direction: column; gap: 8px; margin-top: 15px; }
.skill-item { display: flex; align-items: center; gap: 10px; padding: 10px; background: var(--surface2); border: 1px solid var(--border); border-radius: var(--r); cursor: pointer; transition: all 0.2s; }
.skill-item:hover { background: var(--surface3); border-color: var(--blue); }
.skill-item.done { border-color: var(--green); background: rgba(16,185,129,0.05); }
.skill-check { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 10px; transition: all 0.2s; }
.skill-item.done .skill-check { background: var(--green); border-color: var(--green); color: white; }
.skill-name { font-size: 13px; color: var(--text2); }
.skill-item.done .skill-name { color: var(--text); font-weight: 600; }
"""
if ".lms-grid {" not in html:
    html = html.replace('/* ── AMBIENT BG ── */', lms_css + '\n/* ── AMBIENT BG ── */')

# 2. Student Portal Tab
student_tabs_old = '<div class="fsum-label">PENDING</div><div class="fsum-val r" id="sPending">0</div></div>\n      </div>'
student_tabs_new = student_tabs_old + """
      <div class="modal-tabs" style="margin-top:20px;">
        <div class="mtab active" onclick="switchStuPortalTab('fees')" id="sp-tab-fees">Fees & Attendance</div>
        <div class="mtab" onclick="switchStuPortalTab('learning')" id="sp-tab-learning">LMS Data Portal</div>
      </div>
"""
if 'switchStuPortalTab' not in html:
    html = html.replace(student_tabs_old, student_tabs_new)

# Wrap fee summary and calendar in a content div
portal_content_old = '<div class="cal-section">'
portal_content_new = '<div id="sp-content-fees" class="mtab-content active">\n    <div class="cal-section">'
if 'id="sp-content-fees"' not in html:
    html = html.replace(portal_content_old, portal_content_new, 1)
    # Find end of cal-section to close div
    # This is tricky, I'll search for the end of the student page main
    html = html.replace('</main>\n  </section><!-- Student Page -->', '</div> <!-- end sp-content-fees -->\n    \n    <div id="sp-content-learning" class="mtab-content">\n        <div class="lms-grid" id="lmsTrackGrid"></div>\n    </div>\n  </main>\n  </section><!-- Student Page -->')

# 3. Admin Track Assignment UI
admin_tab_old = '<div class="mtab" onclick="switchStuTab(\'attendance\')" id="tab-attendance">Attendance</div>'
admin_tab_new = admin_tab_old + '\n        <div class="mtab" onclick="switchStuTab(\'lms\')" id="tab-lms">LMS Tracks</div>'
if 'id="tab-lms"' not in html:
    html = html.replace(admin_tab_old, admin_tab_new)

admin_content_old = '<div style="display:flex;justify-content:flex-end;gap:10px;margin-top:10px;">'
admin_content_new = """
      <div id="mtc-lms" class="mtab-content">
        <h3 style="font-family:'Syne',sans-serif; font-size:14px; margin-bottom:10px;">Assign Learning Tracks</h3>
        <div id="availableTracksList" style="display:flex; flex-direction:column; gap:10px;"></div>
      </div>
""" + admin_content_old
if 'id="mtc-lms"' not in html:
    html = html.replace(admin_content_old, admin_content_new)

# 4. JS Logic for LMS
lms_js = r"""
function switchStuPortalTab(t) {
    document.querySelectorAll('#studentPage .mtab').forEach(e=>e.classList.remove('active'));
    document.querySelectorAll('#studentPage .mtab-content').forEach(e=>e.classList.remove('active'));
    document.getElementById('sp-tab-'+t).classList.add('active');
    document.getElementById('sp-content-'+t).classList.add('active');
    if(t === 'learning') loadLMSPortal();
}

async function loadLMSPortal() {
    const grid = document.getElementById('lmsTrackGrid');
    grid.innerHTML = '<div style="color:var(--text3)">Loading LMS data...</div>';
    
    // Fetch all tracks and user details
    const [tRes, dRes] = await Promise.all([
        api('/api/lms/tracks'),
        api('/api/students/' + loggedStu.id + '/details')
    ]);
    
    if(tRes.data.ok && dRes.data.ok) {
        const assigned = dRes.data.student.assigned_tracks || [];
        const done = dRes.data.progress || [];
        const tracks = tRes.data.tracks.filter(t => assigned.includes(t.id));
        
        if(tracks.length === 0) {
            grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:40px; color:var(--text3);">No learning tracks assigned to you yet.</div>';
            return;
        }
        
        grid.innerHTML = tracks.map(t => {
            const trackDone = done.filter(p => p.track_id === t.id);
            const perc = Math.round((trackDone.length / t.skills.length) * 100) || 0;
            return `
                <div class="track-card">
                    <div class="track-header">
                        <div class="track-title">${t.title}</div>
                        <div class="track-level">${t.level}</div>
                    </div>
                    <div style="font-size:12px; color:var(--text2); display:flex; justify-content:space-between;">
                        <span>Progress</span>
                        <span>${perc}%</span>
                    </div>
                    <div class="lms-prog-container">
                        <div class="lms-prog-bar" style="width:${perc}%"></div>
                    </div>
                    <div class="skill-list">
                        ${t.skills.map(s => {
                            const isDone = done.some(p => p.track_id === t.id && p.skill === s);
                            return `
                                <div class="skill-item ${isDone ? 'done' : ''}" onclick="toggleSkill('${t.id}', '${s}')">
                                    <div class="skill-check">${isDone ? '✓' : ''}</div>
                                    <div class="skill-name">${s}</div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }
}

async function toggleSkill(tid, skill) {
    const {data} = await api('/api/lms/progress/toggle', 'POST', {track_id: tid, skill: skill});
    if(data.ok) {
        toast(data.status === 'COMPLETED' ? 'Skill marked as done!' : 'Skill removed', 's');
        loadLMSPortal();
    }
}

// Admin side: load assigned tracks
async function loadAdminLMS(stuId) {
    const list = document.getElementById('availableTracksList');
    list.innerHTML = 'Loading tracks...';
    
    const [tRes, dRes] = await Promise.all([
        api('/api/lms/tracks'),
        api('/api/students/' + stuId + '/details')
    ]);
    
    if(tRes.data.ok && dRes.data.ok) {
        const assigned = dRes.data.student.assigned_tracks || [];
        list.innerHTML = tRes.data.tracks.map(t => {
            const isAssigned = assigned.includes(t.id);
            return `
                <div class="skill-item ${isAssigned ? 'done' : ''}" onclick="toggleAssignTrack('${stuId}', '${t.id}')">
                    <div class="skill-check">${isAssigned ? '✓' : ''}</div>
                    <div class="skill-name">${t.title} (${t.level})</div>
                </div>
            `;
        }).join('');
    }
}

async function toggleAssignTrack(stuId, tid) {
    const s = students.find(x => x.id === stuId);
    if(!s) return;
    if(!s.assigned_tracks) s.assigned_tracks = [];
    
    if(s.assigned_tracks.includes(tid)) {
        s.assigned_tracks = s.assigned_tracks.filter(x => x !== tid);
    } else {
        s.assigned_tracks.push(tid);
    }
    
    const {data} = await api('/api/students/' + stuId, 'PUT', {
        ...s,
        assigned_tracks: s.assigned_tracks
    });
    if(data.ok) {
        toast('Tracks updated', 's');
        loadAdminLMS(stuId);
    }
}
"""
if 'switchStuPortalTab' not in html:
    html = html.replace('async function fetchStudentExtras(id) {', lms_js + '\nasync function fetchStudentExtras(id) {')

# Inject loadAdminLMS into openEditModal
if 'loadAdminLMS(id)' not in html:
    html = html.replace('fetchStudentExtras(id);', 'fetchStudentExtras(id); loadAdminLMS(id);')

with open(html_path, "w") as f:
    f.write(html)

# 5. Seed Initial Tracks
db = sqlite3.connect(db_path)
tracks = [
    ("tr_mth10", "Mathematics Foundation", "Class 10", ["Algebra", "Trigonometry", "Geometry", "Statistics"]),
    ("tr_sci10", "Science Core", "Class 10", ["Physics - Light", "Chemistry - Acids", "Biology - Heredity"]),
    ("tr_ai_tec", "Artificial Intelligence", "Tech", ["Prompt Engineering", "Machine Learning Basics", "Python for AI", "Neural Networks"])
]

for tid, title, level, skills in tracks:
    db.execute("INSERT OR REPLACE INTO tracks (id, title, level, skills) VALUES (?,?,?,?)",
               (tid, title, level, json.dumps(skills)))
db.commit()
db.close()

print("LMS UI injected and tracks seeded.")
