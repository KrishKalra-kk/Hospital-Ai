"""All CSS styles as a Python string — White/Light Premium Theme."""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg-primary: #f0f2f5; --bg-secondary: #ffffff; --bg-card: #ffffff;
    --bg-sidebar: #1e293b; --bg-input: #f8fafc;
    --accent: #4f46e5; --accent-glow: rgba(79,70,229,0.15); --accent2: #0ea5e9;
    --grad: linear-gradient(135deg, #4f46e5, #0ea5e9);
    --green: #059669; --yellow: #d97706; --red: #dc2626; --purple: #7c3aed;
    --text: #1e293b; --text2: #64748b; --text3: #94a3b8;
    --border: #e2e8f0; --border2: #cbd5e1;
    --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.05);
    --sidebar-w: 250px; --header-h: 60px; --radius: 14px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
    font-family: 'Inter', sans-serif; background: var(--bg-primary); color: var(--text);
    line-height: 1.6; min-height: 100vh; overflow-x: hidden;
}
a { color: var(--accent); text-decoration: none; }
.app { display: flex; min-height: 100vh; }

/* Sidebar — keeps dark for contrast */
.sidebar {
    width: var(--sidebar-w); background: var(--bg-sidebar); 
    position: fixed; top: 0; left: 0; height: 100vh; z-index: 100; display: flex; flex-direction: column;
    transition: transform 0.3s ease; box-shadow: 2px 0 8px rgba(0,0,0,0.1);
}
.sb-head { padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; gap: 10px; height: var(--header-h); }
.sb-head h1 { font-size: 15px; color: #fff; }
.sb-head small { font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; }
.sb-nav { flex: 1; padding: 12px 10px; overflow-y: auto; }
.sb-section { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; padding: 8px 12px 4px; }
.sb-link {
    display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: 8px;
    color: #94a3b8; font-size: 13px; font-weight: 500; transition: all 0.15s; margin-bottom: 2px; text-decoration: none; position: relative;
}
.sb-link:hover { background: rgba(255,255,255,0.06); color: #e2e8f0; }
.sb-link.active { background: rgba(79,70,229,0.2); color: #a5b4fc; }
.sb-link.active::before {
    content: ''; position: absolute; left: 0; width: 3px; height: 18px;
    background: var(--grad); border-radius: 0 3px 3px 0;
}
.sb-badge {
    margin-left: auto; background: var(--red); color: #fff; font-size: 10px; font-weight: 700;
    padding: 1px 6px; border-radius: 10px; animation: pulse-b 2s infinite;
}
@keyframes pulse-b { 0%,100%{opacity:1} 50%{opacity:0.6} }
.sb-foot { padding: 14px 16px; border-top: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; gap: 10px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--grad); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; color: #fff; }

/* Main */
.main { margin-left: var(--sidebar-w); flex: 1; min-height: 100vh; background: var(--bg-primary); }
.top-bar {
    height: var(--header-h); background: #ffffff; 
    border-bottom: 1px solid var(--border); display: flex; align-items: center;
    justify-content: space-between; padding: 0 28px; position: sticky; top: 0; z-index: 50;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.top-bar h2 { font-size: 18px; font-weight: 700; color: var(--text); }
.clock { font-size: 12px; color: var(--text3); font-variant-numeric: tabular-nums; }
.page { padding: 24px 28px; }

/* Metrics Grid */
.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
.m-card {
    background: #ffffff; border: 1px solid var(--border); 
    border-radius: var(--radius); padding: 20px; position: relative; overflow: hidden;
    transition: all 0.3s; box-shadow: var(--shadow);
}
.m-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); border-color: var(--border2); }
.m-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.m-card.blue::before { background: linear-gradient(90deg, #4f46e5, #818cf8); }
.m-card.green::before { background: linear-gradient(90deg, #059669, #34d399); }
.m-card.purple::before { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
.m-card.cyan::before { background: linear-gradient(90deg, #0ea5e9, #67e8f9); }
.m-card.orange::before { background: linear-gradient(90deg, #d97706, #fbbf24); }
.m-card.red::before { background: linear-gradient(90deg, #dc2626, #f87171); }
.m-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.m-label { font-size: 12px; font-weight: 600; color: var(--text2); text-transform: uppercase; letter-spacing: 0.04em; }
.m-icon { font-size: 22px; }
.m-val { font-size: 28px; font-weight: 800; color: var(--text); line-height: 1.1; margin-bottom: 4px; }
.m-sub { font-size: 11px; font-weight: 500; color: var(--text3); }
.m-sub.bad { color: var(--red); } .m-sub.good { color: var(--green); }

/* Card */
.card { background: #ffffff; border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; margin-bottom: 20px; box-shadow: var(--shadow); }
.card-h { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border); background: #fafbfc; }
.card-t { font-size: 15px; font-weight: 700; color: var(--text); }
.card-b { padding: 20px; }
.card-b.np { padding: 0; }

/* Charts */
.charts-row { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-bottom: 20px; }
.chart-wrap { position: relative; width: 100%; height: 280px; padding: 6px; }

/* Table */
table.dt { width: 100%; border-collapse: collapse; }
.dt th { padding: 10px 14px; text-align: left; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text2); background: #f8fafc; border-bottom: 2px solid var(--border); }
.dt td { padding: 12px 14px; font-size: 13px; color: var(--text); border-bottom: 1px solid var(--border); vertical-align: middle; }
.dt tr { transition: background 0.15s; }
.dt tbody tr:hover { background: #f8fafc; }

/* Badge */
.badge { display: inline-flex; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-s { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
.badge-w { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.badge-d { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.badge-i { background: #eef2ff; color: #4f46e5; border: 1px solid #c7d2fe; }
.badge-n { background: #f8fafc; color: var(--text2); border: 1px solid var(--border); }

/* Button */
.btn {
    display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px;
    font-size: 13px; font-weight: 600; font-family: 'Inter', sans-serif; cursor: pointer; border: none; transition: all 0.15s;
}
.btn-p { background: var(--grad); color: #fff; box-shadow: 0 2px 8px rgba(79,70,229,0.25); }
.btn-p:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(79,70,229,0.35); }
.btn-s { background: #fff; color: var(--text); border: 1px solid var(--border2); }
.btn-s:hover { border-color: var(--accent); background: #f8fafc; }
.btn-d { background: #fef2f2; color: var(--red); border: 1px solid #fecaca; }
.btn-d:hover { background: #fee2e2; }
.btn-ok { background: #ecfdf5; color: var(--green); border: 1px solid #a7f3d0; }
.btn-ok:hover { background: #d1fae5; }
.btn-sm { padding: 5px 12px; font-size: 11px; }

/* Form */
.fg { margin-bottom: 16px; }
.fl { display: block; font-size: 12px; font-weight: 600; color: var(--text2); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.04em; }
.fc {
    width: 100%; padding: 9px 12px; background: #fff; border: 1px solid var(--border2);
    border-radius: 8px; color: var(--text); font-size: 13px; font-family: 'Inter', sans-serif; transition: all 0.15s;
}
.fc:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
.fc::placeholder { color: var(--text3); }
select.fc { appearance: none; background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2364748b' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e"); background-position: right 8px center; background-repeat: no-repeat; background-size: 18px; padding-right: 32px; background-color: #fff; }
.fr { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
textarea.fc { resize: vertical; }

/* Progress */
.prog { margin-bottom: 14px; }
.prog-top { display: flex; justify-content: space-between; margin-bottom: 4px; }
.prog-nm { font-size: 12px; color: var(--text); } .prog-vl { font-size: 11px; color: var(--text2); font-weight: 600; }
.prog-track { height: 7px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
.prog-fill { height: 100%; border-radius: 4px; transition: width 1s ease; }
.prog-fill.g { background: linear-gradient(90deg, #059669, #34d399); }
.prog-fill.o { background: linear-gradient(90deg, #d97706, #fbbf24); }
.prog-fill.r { background: linear-gradient(90deg, #dc2626, #f87171); }
.prog-fill.b { background: linear-gradient(90deg, #4f46e5, #818cf8); }

/* Alert item */
.al { display: flex; align-items: flex-start; gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--border); transition: background 0.15s; }
.al:hover { background: #f8fafc; }
.al:last-child { border-bottom: none; }
.al-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.al-dot.cr { background: var(--red); box-shadow: 0 0 6px rgba(220,38,38,0.3); }
.al-dot.wr { background: var(--yellow); box-shadow: 0 0 6px rgba(217,119,6,0.3); }
.al-dot.inf { background: var(--accent); box-shadow: 0 0 6px rgba(79,70,229,0.3); }
.al-dot.nr { background: var(--green); box-shadow: 0 0 6px rgba(5,150,105,0.3); }
.al-c { flex: 1; }
.al-msg { font-size: 13px; font-weight: 500; color: var(--text); margin-bottom: 3px; }
.al-meta { font-size: 11px; color: var(--text3); }
.al.acked { opacity: 0.45; }

/* Resource grid */
.res-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.res-card { background: #ffffff; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; transition: all 0.3s; box-shadow: var(--shadow); }
.res-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); border-color: var(--border2); }
.res-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.res-title { font-size: 14px; font-weight: 700; color: var(--text); }
.res-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 12px; }
.rs { text-align: center; padding: 6px; border-radius: 8px; background: #f8fafc; border: 1px solid var(--border); }
.rs-v { font-size: 16px; font-weight: 700; color: var(--text); }
.rs-l { font-size: 9px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.06em; }

/* Modal */
.modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); z-index: 999; display: none; align-items: center; justify-content: center; }
.modal-bg.show { display: flex; }
.modal { background: #ffffff; border: 1px solid var(--border); border-radius: 16px; width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto; animation: slideUp 0.3s ease; box-shadow: var(--shadow-lg); }
.modal-h { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid var(--border); background: #fafbfc; border-radius: 16px 16px 0 0; }
.modal-h h3 { font-size: 16px; font-weight: 700; color: var(--text); }
.modal-x { background: none; border: none; color: var(--text3); font-size: 22px; cursor: pointer; }
.modal-x:hover { color: var(--text); }
.modal-bd { padding: 20px 24px; }
.modal-ft { padding: 14px 24px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 10px; background: #fafbfc; border-radius: 0 0 16px 16px; }

/* Prediction */
.pred-res { text-align: center; padding: 32px 16px; }
.pred-num { font-size: 56px; font-weight: 800; background: var(--grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1; margin-bottom: 6px; }
.pred-lbl { font-size: 13px; color: var(--text2); margin-bottom: 20px; }
.pred-row { display: flex; justify-content: center; gap: 28px; }
.pred-d { text-align: center; }
.pred-dv { font-size: 18px; font-weight: 700; color: var(--text); }
.pred-dl { font-size: 10px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.06em; }

/* Flash */
.flash-c { position: fixed; top: 72px; right: 28px; z-index: 200; }
.flash { padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; margin-bottom: 6px; animation: slideR 0.3s ease; box-shadow: var(--shadow-md); }
.flash-ok { background: #ecfdf5; border: 1px solid #a7f3d0; color: var(--green); }
.flash-err { background: #fef2f2; border: 1px solid #fecaca; color: var(--red); }

/* Empty */
.empty { text-align: center; padding: 48px 16px; color: var(--text3); }
.empty .ei { font-size: 40px; margin-bottom: 12px; opacity: 0.5; }
.empty h3 { font-size: 16px; color: var(--text2); margin-bottom: 6px; }

/* Section header */
.sec-h { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.sec-t { font-size: 16px; font-weight: 700; color: var(--text); }

/* Animations */
@keyframes slideUp { from{transform:translateY(16px);opacity:0} to{transform:translateY(0);opacity:1} }
@keyframes slideR { from{transform:translateX(100%);opacity:0} to{transform:translateX(0);opacity:1} }
@keyframes stIn { from{transform:translateY(8px);opacity:0} to{transform:translateY(0);opacity:1} }

/* Responsive */
@media(max-width:768px) {
    .sidebar{transform:translateX(-100%)} .sidebar.open{transform:translateX(0)}
    .main{margin-left:0} .charts-row{grid-template-columns:1fr} .fr{grid-template-columns:1fr}
    .metrics{grid-template-columns:1fr 1fr} .res-grid{grid-template-columns:1fr}
    .page{padding:16px 12px}
}
@media(max-width:480px) { .metrics{grid-template-columns:1fr} }

::-webkit-scrollbar{width:5px} ::-webkit-scrollbar-track{background:transparent} ::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#94a3b8}

code.bed { color: #0ea5e9; background: #f0f9ff; padding: 2px 7px; border-radius: 4px; font-size: 12px; border: 1px solid #bae6fd; }
"""
