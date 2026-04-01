/**
 * MedByte — Chart helpers & UI utilities (v2 — Animated)
 */

// ── Clock ──
function updateClock() {
  const el = document.getElementById('clock');
  if (el) {
    const n = new Date();
    el.textContent = n.toLocaleString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
    });
  }
}
setInterval(updateClock, 1000);
updateClock();

// ── Sidebar Toggle ──
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}
document.addEventListener('click', e => {
  const s = document.getElementById('sidebar');
  const t = document.getElementById('menu-tog');
  if (s && s.classList.contains('open') && !s.contains(e.target) && t && !t.contains(e.target))
    s.classList.remove('open');
});

// ── Modal ──
function openModal(id) {
  const m = document.getElementById(id);
  if (m) { m.classList.add('show'); document.body.style.overflow = 'hidden'; }
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) { m.classList.remove('show'); document.body.style.overflow = ''; }
}
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-bg')) {
    e.target.classList.remove('show');
    document.body.style.overflow = '';
  }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape')
    document.querySelectorAll('.modal-bg.show').forEach(m => {
      m.classList.remove('show'); document.body.style.overflow = '';
    });
});

// ── Chart Color Palette (v2 — Richer) ──
const CC = {
  blue:   { m: '#3b82f6', l: '#60a5fa', g: ['rgba(59,130,246,0.4)',  'rgba(59,130,246,0)'] },
  cyan:   { m: '#06b6d4', l: '#22d3ee', g: ['rgba(6,182,212,0.4)',   'rgba(6,182,212,0)'] },
  green:  { m: '#10b981', l: '#34d399', g: ['rgba(16,185,129,0.4)',  'rgba(16,185,129,0)'] },
  orange: { m: '#f97316', l: '#fb923c', g: ['rgba(249,115,22,0.4)',  'rgba(249,115,22,0)'] },
  purple: { m: '#8b5cf6', l: '#a78bfa', g: ['rgba(139,92,246,0.4)',  'rgba(139,92,246,0)'] },
  red:    { m: '#ef4444', l: '#f87171', g: ['rgba(239,68,68,0.4)',   'rgba(239,68,68,0)'] },
  pink:   { m: '#ec4899', l: '#f472b6', g: ['rgba(236,72,153,0.4)',  'rgba(236,72,153,0)'] },
  indigo: { m: '#6366f1', l: '#818cf8', g: ['rgba(99,102,241,0.4)',  'rgba(99,102,241,0)'] },
};

const BASE_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 1200,
    easing: 'easeInOutCubic',
    delay: (ctx) => ctx.dataIndex * 50,
  },
  plugins: {
    legend: {
      labels: {
        color: '#94a3b8',
        font: { family: 'Inter', size: 11, weight: 600 },
        padding: 16,
        usePointStyle: true,
        pointStyleWidth: 8
      }
    },
    tooltip: {
      backgroundColor: 'rgba(15,22,41,0.95)',
      titleColor: '#e2e8f0',
      bodyColor: '#94a3b8',
      borderColor: 'rgba(99,102,241,0.3)',
      borderWidth: 1,
      padding: 14,
      cornerRadius: 10,
      titleFont: { family: 'Inter', weight: 700, size: 13 },
      bodyFont: { family: 'Inter', size: 12 },
      boxPadding: 6,
    }
  },
  scales: {
    x: {
      ticks: { color: '#64748b', font: { family: 'Inter', size: 10, weight: 500 } },
      grid: { color: 'rgba(99,102,241,0.06)', drawBorder: false }
    },
    y: {
      ticks: { color: '#64748b', font: { family: 'Inter', size: 10, weight: 500 } },
      grid: { color: 'rgba(99,102,241,0.06)', drawBorder: false }
    }
  }
};

function mkGrad(ctx, key, h = 280) {
  const c = CC[key] || CC.blue;
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, c.g[0]);
  g.addColorStop(1, c.g[1]);
  return g;
}

// ── Single-line chart ──
function initLine(id, labels, data, colKey = 'blue', label = 'Patients') {
  const cv = document.getElementById(id);
  if (!cv) return;
  const ctx = cv.getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: CC[colKey].m,
        backgroundColor: mkGrad(ctx, colKey),
        fill: true, tension: 0.45, borderWidth: 2.5,
        pointRadius: 3, pointHoverRadius: 8,
        pointBackgroundColor: CC[colKey].m,
        pointBorderColor: '#0a0e1a', pointBorderWidth: 2,
        pointHoverBackgroundColor: CC[colKey].l,
      }]
    },
    options: { ...BASE_OPTS, plugins: { ...BASE_OPTS.plugins, legend: { display: false } } }
  });
}

// ── Multi-line comparison chart ──
function initCompare(id, labels, datasets) {
  const cv = document.getElementById(id);
  if (!cv) return;
  const ctx = cv.getContext('2d');
  const colKeys = ['indigo', 'cyan', 'green', 'orange'];
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        borderColor: CC[colKeys[i % 4]].m,
        backgroundColor: i === 0 ? mkGrad(ctx, colKeys[i]) : 'transparent',
        fill: i === 0,
        tension: 0.45,
        borderWidth: 2.5,
        borderDash: i === 1 ? [6, 4] : undefined,
        pointRadius: 3, pointHoverRadius: 8,
        pointBackgroundColor: CC[colKeys[i % 4]].m,
        pointBorderColor: '#050810', pointBorderWidth: 2,
        pointHoverBackgroundColor: CC[colKeys[i % 4]].l,
      }))
    },
    options: BASE_OPTS
  });
}

// ── Doughnut ──
function initDonut(id, labels, data) {
  const cv = document.getElementById(id);
  if (!cv) return;
  const colors = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#3b82f6'];
  return new Chart(cv.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: '#0f1629',
        borderWidth: 3,
        hoverOffset: 12,
        spacing: 2,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '72%',
      animation: { animateRotate: true, animateScale: true, duration: 1400, easing: 'easeInOutCubic' },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 11, weight: 600 },
            padding: 14,
            usePointStyle: true,
          }
        },
        tooltip: BASE_OPTS.plugins.tooltip
      }
    }
  });
}

// ── Pie Chart (new) ──
function initPie(id, labels, data) {
  const cv = document.getElementById(id);
  if (!cv) return;
  const colors = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#3b82f6'];
  return new Chart(cv.getContext('2d'), {
    type: 'pie',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: '#0f1629',
        borderWidth: 3,
        hoverOffset: 10,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { animateRotate: true, animateScale: true, duration: 1200 },
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 11, weight: 600 }, padding: 12, usePointStyle: true }
        },
        tooltip: BASE_OPTS.plugins.tooltip
      }
    }
  });
}

// ── Bar chart ──
function initBar(id, labels, datasets) {
  const cv = document.getElementById(id);
  if (!cv) return;
  const colKeys = ['indigo', 'purple', 'cyan', 'green'];
  return new Chart(cv.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        backgroundColor: CC[colKeys[i % 4]].g[0],
        borderColor: CC[colKeys[i % 4]].m,
        borderWidth: 1.5,
        borderRadius: 8,
        borderSkipped: false,
      }))
    },
    options: {
      ...BASE_OPTS,
      animation: {
        ...BASE_OPTS.animation,
        delay: (ctx) => ctx.dataIndex * 80,
      }
    }
  });
}

// ── Polar Area (new) ──
function initPolar(id, labels, data) {
  const cv = document.getElementById(id);
  if (!cv) return;
  const colors = ['rgba(99,102,241,0.6)', 'rgba(6,182,212,0.6)', 'rgba(16,185,129,0.6)', 'rgba(245,158,11,0.6)', 'rgba(239,68,68,0.6)', 'rgba(139,92,246,0.6)'];
  return new Chart(cv.getContext('2d'), {
    type: 'polarArea',
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors.slice(0, labels.length), borderColor: '#0f1629', borderWidth: 2 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { animateRotate: true, animateScale: true, duration: 1400 },
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, padding: 12, usePointStyle: true } },
        tooltip: BASE_OPTS.plugins.tooltip
      },
      scales: { r: { ticks: { display: false }, grid: { color: 'rgba(99,102,241,0.08)' } } }
    }
  });
}

// ── AI Prediction form ──
function runPrediction() {
  const h = document.getElementById('ph')?.value;
  const b = document.getElementById('pb')?.value;
  const s = document.getElementById('ps')?.value;
  const er = document.getElementById('per')?.value;
  if (!h || !b || !s) return;

  const btn = document.getElementById('pred-btn');
  if (btn) { btn.textContent = '⏳ Predicting...'; btn.disabled = true; }

  fetch('/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hour: +h, beds_available: +b, staff_count: +s, er_arrivals: +(er || 5) })
  })
    .then(r => r.json())
    .then(d => {
      document.getElementById('pv').textContent = d.patients_next_hour;
      document.getElementById('pb_need').textContent = d.beds_needed_24h;
      document.getElementById('ps_need').textContent = d.staff_needed_24h;
      document.getElementById('pc').textContent = d.confidence_patients + '%';
      document.getElementById('pr').textContent = d.risk_patients;
      document.getElementById('pu').textContent = d.bed_utilization + '%';
      const rEl = document.getElementById('pr');
      const riskColors = { Critical: '#ef4444', High: '#f97316', Medium: '#f59e0b', Low: '#10b981' };
      rEl.style.color = riskColors[d.risk_patients] || '#10b981';
      document.getElementById('pred-res').style.display = 'block';
      if (btn) { btn.textContent = '🤖 Run Prediction'; btn.disabled = false; }
    })
    .catch(e => { console.error(e); if (btn) { btn.textContent = '🤖 Run Prediction'; btn.disabled = false; } });
}

// ── Acknowledge alert ──
function ackAlert(id, btn) {
  fetch('/alerts/acknowledge/' + id, { method: 'POST' })
    .then(r => {
      if (r.ok) {
        btn.closest('.al').classList.add('acked');
        btn.textContent = '✓'; btn.disabled = true;
        btn.className = 'btn btn-sm btn-ok';
        const b = document.querySelector('.sb-badge');
        if (b) { const c = parseInt(b.textContent) - 1; if (c <= 0) b.style.display = 'none'; else b.textContent = c; }
      }
    });
}

// ── Discharge patient ──
function discharge(id) {
  if (!confirm('Discharge this patient?')) return;
  fetch('/patients/discharge/' + id, { method: 'POST' })
    .then(r => { if (r.ok) location.reload(); });
}

// ── Staggered entrance animations (v2 — smoother) ──
document.addEventListener('DOMContentLoaded', () => {
  // Metric cards
  document.querySelectorAll('.m-card').forEach((c, i) => {
    c.style.animation = `cardIn 0.5s cubic-bezier(0.4,0,0.2,1) ${i * 0.08}s backwards`;
  });
  // Table rows
  document.querySelectorAll('.dt tbody tr').forEach((r, i) => {
    r.style.animation = `rowIn 0.35s ease ${i * 0.04}s backwards`;
  });
  // Resource cards
  document.querySelectorAll('.res-card').forEach((c, i) => {
    c.style.animation = `cardIn 0.45s ease ${i * 0.06}s backwards`;
  });
  // Cards
  document.querySelectorAll('.card').forEach((c, i) => {
    c.style.animation = `cardIn 0.5s ease ${0.1 + i * 0.05}s backwards`;
  });
  // Bed cells
  document.querySelectorAll('.bed-cell').forEach((c, i) => {
    c.style.animation = `cardIn 0.3s ease ${i * 0.02}s backwards`;
  });
  // Alert rows
  document.querySelectorAll('.al').forEach((a, i) => {
    a.style.animation = `rowIn 0.35s ease ${i * 0.05}s backwards`;
  });

  // Counter animation for metric values
  document.querySelectorAll('.m-val').forEach(el => {
    const target = parseInt(el.textContent);
    if (isNaN(target) || target === 0) return;
    const duration = 1000;
    const start = performance.now();
    el.textContent = '0';
    function animate(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      el.textContent = Math.round(target * eased);
      if (progress < 1) requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
  });
});
