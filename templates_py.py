"""All HTML templates as Python strings for Flask render_template_string."""

# ─── JavaScript (embedded) ───
JS = """
function toggleSidebar(){document.getElementById('sidebar').classList.toggle('open')}
document.addEventListener('click',e=>{const s=document.getElementById('sidebar');const t=document.getElementById('menu-tog');if(s&&s.classList.contains('open')&&!s.contains(e.target)&&t&&!t.contains(e.target))s.classList.remove('open')});
function updateClock(){const el=document.getElementById('clock');if(el){const n=new Date();el.textContent=n.toLocaleString('en-US',{weekday:'short',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true})}}
setInterval(updateClock,1000);updateClock();
function openModal(id){const m=document.getElementById(id);if(m){m.classList.add('show');document.body.style.overflow='hidden'}}
function closeModal(id){const m=document.getElementById(id);if(m){m.classList.remove('show');document.body.style.overflow=''}}
document.addEventListener('click',e=>{if(e.target.classList.contains('modal-bg')){e.target.classList.remove('show');document.body.style.overflow=''}});
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.modal-bg.show').forEach(m=>{m.classList.remove('show');document.body.style.overflow=''})});

const CC={blue:{m:'#3b82f6',g:['rgba(59,130,246,0.3)','rgba(59,130,246,0)']},cyan:{m:'#06b6d4',g:['rgba(6,182,212,0.3)','rgba(6,182,212,0)']},green:{m:'#10b981',g:['rgba(16,185,129,0.3)','rgba(16,185,129,0)']},orange:{m:'#f59e0b',g:['rgba(245,158,11,0.3)','rgba(245,158,11,0)']},red:{m:'#ef4444',g:['rgba(239,68,68,0.3)','rgba(239,68,68,0)']}};
const CO={responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#64748b',font:{family:'Inter',size:11},padding:14,usePointStyle:true,pointStyleWidth:7}},tooltip:{backgroundColor:'#1e293b',titleColor:'#f1f5f9',bodyColor:'#cbd5e1',borderColor:'#334155',borderWidth:1,padding:10,cornerRadius:8}},scales:{x:{ticks:{color:'#94a3b8',font:{family:'Inter',size:10}},grid:{color:'rgba(0,0,0,0.05)'}},y:{ticks:{color:'#94a3b8',font:{family:'Inter',size:10}},grid:{color:'rgba(0,0,0,0.05)'}}}};

function mkGrad(ctx,k){const c=CC[k]||CC.blue;const g=ctx.createLinearGradient(0,0,0,280);g.addColorStop(0,c.g[0]);g.addColorStop(1,c.g[1]);return g}

function initLine(id,labels,data){const cv=document.getElementById(id);if(!cv)return;const ctx=cv.getContext('2d');new Chart(ctx,{type:'line',data:{labels:labels,datasets:[{label:'Patients',data:data,borderColor:CC.blue.m,backgroundColor:mkGrad(ctx,'blue'),fill:true,tension:.4,borderWidth:2.5,pointRadius:3,pointHoverRadius:5,pointBackgroundColor:CC.blue.m,pointBorderColor:'#0a0e1a',pointBorderWidth:2}]},options:{...CO,plugins:{...CO.plugins,legend:{display:false}}}})}

function initDonut(id,labels,data){const cv=document.getElementById(id);if(!cv)return;new Chart(cv.getContext('2d'),{type:'doughnut',data:{labels:labels,datasets:[{data:data,backgroundColor:['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4'],borderColor:'#0a0e1a',borderWidth:3,hoverOffset:6}]},options:{responsive:true,maintainAspectRatio:false,cutout:'68%',plugins:{legend:{position:'bottom',labels:{color:'#94a3b8',font:{family:'Inter',size:10},padding:10,usePointStyle:true}},tooltip:CO.plugins.tooltip}}})}

function initCompare(id,labels,actual,predicted){const cv=document.getElementById(id);if(!cv)return;const ctx=cv.getContext('2d');new Chart(ctx,{type:'line',data:{labels:labels,datasets:[{label:'Actual',data:actual,borderColor:CC.blue.m,backgroundColor:mkGrad(ctx,'blue'),fill:true,tension:.4,borderWidth:2.5,pointRadius:3,pointBackgroundColor:CC.blue.m,pointBorderColor:'#0a0e1a',pointBorderWidth:2},{label:'Predicted',data:predicted,borderColor:CC.cyan.m,borderDash:[6,4],fill:false,tension:.4,borderWidth:2,pointRadius:3,pointBackgroundColor:CC.cyan.m,pointBorderColor:'#0a0e1a',pointBorderWidth:2}]},options:CO})}

function runPrediction(){const h=document.getElementById('ph')?.value;const b=document.getElementById('pb')?.value;const s=document.getElementById('ps')?.value;if(!h||!b||!s)return;fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({hour:+h,beds:+b,staff:+s})}).then(r=>r.json()).then(d=>{document.getElementById('pv').textContent=d.predicted_patients;document.getElementById('pc').textContent=d.confidence+'%';document.getElementById('pr').textContent=d.risk_level;document.getElementById('pu').textContent=d.utilization+'%';const r=document.getElementById('pr');r.style.color=d.risk_level==='High'?'#ef4444':d.risk_level==='Medium'?'#f59e0b':'#10b981';document.getElementById('pred-res').style.display='block'}).catch(e=>console.error(e))}

function ackAlert(id,btn){fetch('/alerts/acknowledge/'+id,{method:'POST'}).then(r=>{if(r.ok){btn.closest('.al').classList.add('acked');btn.textContent='✓';btn.disabled=true;btn.className='btn btn-sm btn-ok';const b=document.querySelector('.sb-badge');if(b){const c=parseInt(b.textContent)-1;if(c<=0)b.style.display='none';else b.textContent=c}}}).catch(e=>console.error(e))}

function discharge(id){if(!confirm('Discharge this patient?'))return;fetch('/patients/discharge/'+id,{method:'POST'}).then(r=>{if(r.ok)location.reload()}).catch(e=>console.error(e))}

document.addEventListener('DOMContentLoaded',()=>{document.querySelectorAll('.m-card').forEach((c,i)=>{c.style.animation='stIn 0.4s ease '+(i*0.08)+'s backwards'});document.querySelectorAll('.dt tbody tr').forEach((r,i)=>{r.style.animation='stIn 0.3s ease '+(i*0.04)+'s backwards'})});
"""

# ─── Base Layout ───
BASE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="Hospital AI Resource Management System">
<title>{{ title }} — MedByte</title>
<style>{{ css|safe }}</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="app">
<aside class="sidebar" id="sidebar">
<div class="sb-head"><span style="font-size:24px">🏥</span><div><h1>MedByte</h1><small>Resource Management</small></div></div>
<nav class="sb-nav">
<div class="sb-section">Overview</div>
<a href="/" class="sb-link {{ 'active' if page=='dashboard' }}"><span>📊</span> Dashboard</a>
<div class="sb-section">Management</div>
<a href="/resources" class="sb-link {{ 'active' if page=='resources' }}"><span>🛏️</span> Resources</a>
<a href="/patients" class="sb-link {{ 'active' if page=='patients' }}"><span>👥</span> Patients</a>
<a href="/alerts" class="sb-link {{ 'active' if page=='alerts' }}"><span>🚨</span> Alerts{% if pa > 0 %}<span class="sb-badge">{{ pa }}</span>{% endif %}</a>
<div class="sb-section">Intelligence</div>
<a href="/predictions" class="sb-link {{ 'active' if page=='predictions' }}"><span>🤖</span> AI Predictions</a>
<div class="sb-section">System</div>
<a href="/settings" class="sb-link {{ 'active' if page=='settings' }}"><span>⚙️</span> Settings</a>
</nav>
<div class="sb-foot"><div class="avatar">A</div><div><div style="font-size:12px;font-weight:600;color:var(--text)">Admin</div><div style="font-size:10px;color:var(--text3)">Administrator</div></div></div>
</aside>
<main class="main">
<header class="top-bar">
<div style="display:flex;align-items:center;gap:12px">
<button id="menu-tog" onclick="toggleSidebar()" style="display:none;background:none;border:none;color:var(--text2);font-size:20px;cursor:pointer" class="mob-show">☰</button>
<h2>{{ header }}</h2></div>
<div style="display:flex;align-items:center;gap:14px">
<span class="clock" id="clock"></span>
<a href="/alerts" style="font-size:18px;position:relative">🔔{% if pa > 0 %}<span style="position:absolute;top:-2px;right:-4px;width:7px;height:7px;background:var(--red);border-radius:50%;border:2px solid var(--bg-primary)"></span>{% endif %}</a>
</div></header>
{% if flash_msgs %}
<div class="flash-c">{% for cat,msg in flash_msgs %}<div class="flash flash-{{ 'ok' if cat=='success' else 'err' }}">{{ msg }}</div>{% endfor %}</div>
{% endif %}
<div class="page">{{ content|safe }}</div>
</main></div>
<script>{{ js|safe }}</script>
{{ extra_js|safe }}
</body></html>"""

# ─── Dashboard ───
DASHBOARD = """
<div class="metrics">
<div class="m-card blue"><div class="m-top"><span class="m-label">Active Patients</span><span class="m-icon">👥</span></div><div class="m-val">{{ pc.admitted or 0 }}</div><div class="m-sub">{{ pc.critical or 0 }} critical</div></div>
<div class="m-card green"><div class="m-top"><span class="m-label">Beds Available</span><span class="m-icon">🛏️</span></div><div class="m-val">{{ ba }}</div><div class="m-sub {{ 'bad' if bu > 80 else 'good' }}">{{ bu }}% utilized</div></div>
<div class="m-card purple"><div class="m-top"><span class="m-label">Staff On Duty</span><span class="m-icon">👨‍⚕️</span></div><div class="m-val">{{ sod }}</div><div class="m-sub">of {{ ts }} total</div></div>
<div class="m-card cyan"><div class="m-top"><span class="m-label">AI Prediction</span><span class="m-icon">🤖</span></div><div class="m-val">{{ pred }}</div><div class="m-sub {{ 'bad' if pred > ba else 'good' }}">patients next hr</div></div>
</div>
<div class="charts-row">
<div class="card"><div class="card-h"><span class="card-t">📈 Patient Trend (24h)</span></div><div class="card-b"><div class="chart-wrap"><canvas id="trendChart"></canvas></div></div></div>
<div class="card"><div class="card-h"><span class="card-t">🍩 Resource Usage</span></div><div class="card-b"><div class="chart-wrap"><canvas id="donutChart"></canvas></div></div></div>
</div>
<div class="charts-row">
<div class="card"><div class="card-h"><span class="card-t">🚨 Recent Alerts</span><a href="/alerts" class="btn btn-sm btn-s">View All</a></div>
<div class="card-b np">{% if alerts %}{% for a in alerts[:5] %}
<div class="al {{ 'acked' if a.acknowledged }}"><span class="al-dot {{ 'cr' if a.severity=='CRITICAL' else 'wr' if a.severity=='WARNING' else 'inf' if a.severity=='INFO' else 'nr' }}"></span><div class="al-c"><div class="al-msg">{{ a.message }}</div><div class="al-meta">{{ a.severity }} {% if a.department %}· {{ a.department }}{% endif %} · {{ a.created_at }}</div></div>
<span class="badge badge-{{ 'd' if a.severity=='CRITICAL' else 'w' if a.severity=='WARNING' else 'i' }}">{{ a.severity }}</span></div>
{% endfor %}{% else %}<div class="empty"><div class="ei">✅</div><h3>All Clear</h3></div>{% endif %}</div></div>
<div class="card"><div class="card-h"><span class="card-t">💡 AI Recommendations</span></div>
<div class="card-b np">{% if recs %}{% for r in recs %}
<div class="al"><span class="al-dot {{ 'cr' if r.priority=='High' else 'wr' if r.priority=='Medium' else 'inf' }}"></span><div class="al-c"><div class="al-msg">{{ r.action }}</div><div class="al-meta">Priority: {{ r.priority }}</div></div></div>
{% endfor %}{% else %}<div class="empty"><div class="ei">🤖</div><h3>System Optimal</h3></div>{% endif %}</div></div>
</div>
"""

DASHBOARD_JS = """<script>
initLine('trendChart', {{ tl|tojson }}, {{ td|tojson }});
initDonut('donutChart', {{ rl|tojson }}, {{ rd|tojson }});
</script>"""

# ─── Resources ───
RESOURCES = """
<div class="metrics">{% for s in rs %}
<div class="m-card {{ ['blue','green','purple','orange','cyan'][loop.index0 % 5] }}"><div class="m-top"><span class="m-label">{{ s.category }}</span><span class="m-icon">{{ '🛏️' if s.category=='Beds' else '🔧' if s.category=='Equipment' else '🦽' if s.category=='Mobility' else '🩸' }}</span></div><div class="m-val">{{ s.available }}/{{ s.total }}</div><div class="m-sub">{{ ((s.in_use / s.total) * 100)|round(0)|int }}% in use</div></div>
{% endfor %}</div>
<div class="sec-h"><h3 class="sec-t">All Resources</h3></div>
<div class="res-grid">{% for r in resources %}
<div class="res-card"><div class="res-top"><span class="res-title">{{ r.name }}</span><span class="badge badge-{{ 'd' if r.status=='critical' else 'w' if r.status=='warning' else 's' }}">{{ r.status|upper }}</span></div>
{% set pct = ((r.in_use / r.total) * 100)|round(0)|int if r.total > 0 else 0 %}
<div class="prog"><div class="prog-top"><span class="prog-nm">Utilization</span><span class="prog-vl">{{ pct }}%</span></div><div class="prog-track"><div class="prog-fill {{ 'r' if pct > 85 else 'o' if pct > 65 else 'g' }}" style="width:{{ pct }}%"></div></div></div>
<div class="res-stats"><div class="rs"><div class="rs-v" style="color:var(--green)">{{ r.available }}</div><div class="rs-l">Available</div></div><div class="rs"><div class="rs-v" style="color:var(--accent)">{{ r.in_use }}</div><div class="rs-l">In Use</div></div><div class="rs"><div class="rs-v" style="color:var(--yellow)">{{ r.maintenance }}</div><div class="rs-l">Maint.</div></div></div>
<form method="POST" action="/resources/update" style="margin-top:12px"><input type="hidden" name="resource_id" value="{{ r.id }}">
<div class="fr"><div class="fg" style="margin-bottom:6px"><input type="number" name="available" class="fc" value="{{ r.available }}" min="0" max="{{ r.total }}"></div><div class="fg" style="margin-bottom:6px"><input type="number" name="in_use" class="fc" value="{{ r.in_use }}" min="0" max="{{ r.total }}"></div></div>
<input type="hidden" name="maintenance" value="{{ r.maintenance }}"><button type="submit" class="btn btn-sm btn-p" style="width:100%">Update</button></form></div>
{% endfor %}</div>"""

# ─── Patients ───
PATIENTS = """
<div class="metrics">
<div class="m-card blue"><div class="m-top"><span class="m-label">Admitted</span><span class="m-icon">🏥</span></div><div class="m-val">{{ cn.admitted or 0 }}</div></div>
<div class="m-card red"><div class="m-top"><span class="m-label">Critical</span><span class="m-icon">⚠️</span></div><div class="m-val">{{ cn.critical or 0 }}</div></div>
<div class="m-card green"><div class="m-top"><span class="m-label">Discharged</span><span class="m-icon">✅</span></div><div class="m-val">{{ cn.discharged or 0 }}</div></div>
<div class="m-card purple"><div class="m-top"><span class="m-label">Total</span><span class="m-icon">📋</span></div><div class="m-val">{{ cn.total or 0 }}</div></div>
</div>
<div class="card"><div class="card-h"><span class="card-t">👥 Patient Records</span><button class="btn btn-p" onclick="openModal('addP')">➕ Add Patient</button></div>
<div class="card-b np"><table class="dt"><thead><tr><th>Patient</th><th>Age/Gender</th><th>Condition</th><th>Severity</th><th>Dept</th><th>Bed</th><th>Admitted</th><th>Status</th><th>Action</th></tr></thead>
<tbody>{% for p in patients %}<tr>
<td style="font-weight:600">{{ p.name }}</td><td>{{ p.age or '—' }}/{{ p.gender or '—' }}</td><td>{{ p.condition or '—' }}</td>
<td><span class="badge badge-{{ 'd' if p.severity=='Critical' else 'w' if p.severity=='Moderate' else 's' }}">{{ p.severity }}</span></td>
<td>{{ p.department_name or '—' }}</td><td><code class="bed">{{ p.bed_number or '—' }}</code></td>
<td style="font-size:11px;color:var(--text3)">{{ p.admitted_at[:16] if p.admitted_at else '—' }}</td>
<td><span class="badge badge-{{ 's' if p.status=='Admitted' else 'n' }}">{{ p.status }}</span></td>
<td>{% if p.status=='Admitted' %}<button class="btn btn-sm btn-d" onclick="discharge({{ p.id }})">Discharge</button>{% else %}<span style="color:var(--text3);font-size:11px">Done</span>{% endif %}</td>
</tr>{% endfor %}{% if not patients %}<tr><td colspan="9"><div class="empty"><div class="ei">👥</div><h3>No patients</h3></div></td></tr>{% endif %}</tbody></table></div></div>
<div class="modal-bg" id="addP"><div class="modal"><div class="modal-h"><h3>➕ Admit Patient</h3><button class="modal-x" onclick="closeModal('addP')">&times;</button></div>
<form method="POST" action="/patients/add"><div class="modal-bd">
<div class="fr"><div class="fg"><label class="fl">Name</label><input type="text" name="name" class="fc" required></div><div class="fg"><label class="fl">Age</label><input type="number" name="age" class="fc" min="0" max="150"></div></div>
<div class="fr"><div class="fg"><label class="fl">Gender</label><select name="gender" class="fc"><option value="M">Male</option><option value="F">Female</option><option value="O">Other</option></select></div><div class="fg"><label class="fl">Severity</label><select name="severity" class="fc"><option value="Stable">Stable</option><option value="Moderate">Moderate</option><option value="Critical">Critical</option></select></div></div>
<div class="fg"><label class="fl">Condition</label><input type="text" name="condition" class="fc" placeholder="e.g. Pneumonia"></div>
<div class="fr"><div class="fg"><label class="fl">Department</label><select name="department_id" class="fc">{% for d in depts %}<option value="{{ d.id }}">{{ d.icon }} {{ d.name }}</option>{% endfor %}</select></div><div class="fg"><label class="fl">Bed</label><input type="text" name="bed_number" class="fc" placeholder="e.g. A-01"></div></div>
<div class="fg"><label class="fl">Notes</label><textarea name="notes" class="fc" rows="2"></textarea></div>
</div><div class="modal-ft"><button type="button" class="btn btn-s" onclick="closeModal('addP')">Cancel</button><button type="submit" class="btn btn-p">Admit</button></div></form></div></div>"""

# ─── Predictions ───
PREDICTIONS = """
<div class="charts-row">
<div class="card"><div class="card-h"><span class="card-t">🔮 Prediction Simulator</span></div><div class="card-b">
<div class="fr"><div class="fg"><label class="fl">Hour (1-24)</label><input type="number" id="ph" class="fc" value="12" min="1" max="24"></div><div class="fg"><label class="fl">Beds Available</label><input type="number" id="pb" class="fc" value="{{ ba }}" min="0"></div></div>
<div class="fg"><label class="fl">Staff Available</label><input type="number" id="ps" class="fc" value="{{ sa }}" min="0"></div>
<button class="btn btn-p" onclick="runPrediction()" style="width:100%;margin-top:8px">🤖 Run Prediction</button>
<div id="pred-res" style="display:none;margin-top:20px">
<div class="pred-res"><div class="pred-num" id="pv">—</div><div class="pred-lbl">Predicted Patients</div>
<div class="pred-row"><div class="pred-d"><div class="pred-dv" id="pc">—</div><div class="pred-dl">Confidence</div></div><div class="pred-d"><div class="pred-dv" id="pr">—</div><div class="pred-dl">Risk Level</div></div><div class="pred-d"><div class="pred-dv" id="pu">—</div><div class="pred-dl">Utilization</div></div></div></div>
</div></div></div>
<div class="card"><div class="card-h"><span class="card-t">📊 Current Alerts</span></div><div class="card-b np">
{% for a in alerts %}
<div class="al"><span class="al-dot {{ 'cr' if a.severity=='CRITICAL' else 'wr' if a.severity=='WARNING' else 'inf' if a.severity=='INFO' else 'nr' }}"></span><div class="al-c"><div class="al-msg">{{ a.message }}</div><div class="al-meta">{{ a.severity }}{% if a.type %} · {{ a.type }}{% endif %}</div></div></div>
{% endfor %}{% if not alerts %}<div class="empty"><div class="ei">✅</div><h3>All Clear</h3></div>{% endif %}</div></div>
</div>
<div class="card"><div class="card-h"><span class="card-t">📈 Actual vs Predicted</span></div><div class="card-b"><div class="chart-wrap"><canvas id="compChart"></canvas></div></div></div>"""

PREDICTIONS_JS = """<script>
initCompare('compChart', {{ tl|tojson }}, {{ td|tojson }}, {{ pd|tojson }});
</script>"""

# ─── Alerts ───
ALERTS = """
<div class="metrics">
<div class="m-card red"><div class="m-top"><span class="m-label">Pending</span><span class="m-icon">⏳</span></div><div class="m-val">{{ ac.pending or 0 }}</div></div>
<div class="m-card orange"><div class="m-top"><span class="m-label">Critical</span><span class="m-icon">🔴</span></div><div class="m-val">{{ ac.critical or 0 }}</div></div>
<div class="m-card green"><div class="m-top"><span class="m-label">Resolved</span><span class="m-icon">✅</span></div><div class="m-val">{{ (ac.total or 0) - (ac.pending or 0) }}</div></div>
<div class="m-card blue"><div class="m-top"><span class="m-label">Total</span><span class="m-icon">📋</span></div><div class="m-val">{{ ac.total or 0 }}</div></div>
</div>
<div class="card"><div class="card-h"><span class="card-t">🚨 Alert Center</span></div><div class="card-b np">
{% for a in alerts %}
<div class="al {{ 'acked' if a.acknowledged }}"><span class="al-dot {{ 'cr' if a.severity=='CRITICAL' else 'wr' if a.severity=='WARNING' else 'inf' if a.severity=='INFO' else 'nr' }}"></span>
<div class="al-c"><div class="al-msg">{{ a.message }}</div><div class="al-meta">{{ a.severity }} · {{ a.type }}{% if a.department %} · {{ a.department }}{% endif %} · {{ a.created_at }}{% if a.acknowledged %} · ✓ Acknowledged{% endif %}</div></div>
<div>{% if not a.acknowledged %}<button class="btn btn-sm btn-s" onclick="ackAlert({{ a.id }},this)">Acknowledge</button>{% else %}<span class="badge badge-s">✓ Done</span>{% endif %}</div></div>
{% endfor %}{% if not alerts %}<div class="empty"><div class="ei">✅</div><h3>No alerts</h3></div>{% endif %}</div></div>"""

# ─── Settings ───
SETTINGS = """
<div class="charts-row">
<div class="card"><div class="card-h"><span class="card-t">➕ Add Hourly Data</span></div><div class="card-b">
<form method="POST" action="/settings">
<div class="fr"><div class="fg"><label class="fl">Hour</label><input type="number" name="hour" class="fc" value="11" min="1" max="24"></div><div class="fg"><label class="fl">Patients</label><input type="number" name="patients" class="fc" value="50" min="0"></div></div>
<div class="fr"><div class="fg"><label class="fl">Beds Available</label><input type="number" name="beds" class="fc" value="20" min="0"></div><div class="fg"><label class="fl">Staff Available</label><input type="number" name="staff" class="fc" value="5" min="0"></div></div>
<button type="submit" class="btn btn-p" style="width:100%;margin-top:8px">💾 Save Data</button>
</form></div></div>
<div class="card"><div class="card-h"><span class="card-t">🏥 Departments</span></div><div class="card-b np">
<table class="dt"><thead><tr><th>Icon</th><th>Name</th><th>Floor</th><th>Beds</th></tr></thead><tbody>
{% for d in depts %}<tr><td>{{ d.icon }}</td><td style="font-weight:600">{{ d.name }}</td><td>{{ d.floor }}</td><td>{{ d.total_beds }}</td></tr>{% endfor %}
</tbody></table></div></div>
</div>
<div class="card"><div class="card-h"><span class="card-t">👨‍⚕️ Staff Roster</span></div><div class="card-b np">
<table class="dt"><thead><tr><th>Name</th><th>Role</th><th>Dept</th><th>Shift</th><th>Status</th><th>Contact</th></tr></thead><tbody>
{% for s in staff %}<tr>
<td style="font-weight:600">{{ s.name }}</td><td>{{ s.role }}</td><td>{{ s.department_name or '—' }}</td><td>{{ s.shift }}</td>
<td><span class="badge badge-{{ 's' if s.status=='On Duty' else 'w' if s.status=='Off Duty' else 'n' }}">{{ s.status }}</span></td>
<td style="font-size:11px;color:var(--text3)">{{ s.email }}</td></tr>{% endfor %}
</tbody></table></div></div>"""
