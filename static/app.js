const el = {
  kpiSamples: document.getElementById('kpiSamples'),
  kpiCpu: document.getElementById('kpiCpu'),
  kpiRam: document.getElementById('kpiRam'),
  kpiCritical: document.getElementById('kpiCritical'),
  runtimeState: document.getElementById('runtimeState'),
  intervalInput: document.getElementById('intervalInput'),
  pauseBtn: document.getElementById('pauseBtn'),
  resumeBtn: document.getElementById('resumeBtn'),
  applyIntervalBtn: document.getElementById('applyIntervalBtn'),
  alertsBody: document.getElementById('alertsBody'),
  hourBtn: document.getElementById('hourBtn'),
  dayBtn: document.getElementById('dayBtn'),
};

let lineChart = null;
let barChart = null;
let rollupMode = 'hour';

function formatSeverityClass(sev) {
  const s = String(sev || '').toLowerCase();
  if (s === 'critical') return 'sev-critical';
  if (s === 'warning') return 'sev-warning';
  return '';
}

function createLineChart(labels, cpu, ram, disk) {
  const ctx = document.getElementById('lineChart');
  if (lineChart) lineChart.destroy();
  lineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'CPU %', data: cpu, borderColor: '#1d4ed8', tension: 0.2 },
        { label: 'RAM %', data: ram, borderColor: '#0891b2', tension: 0.2 },
        { label: 'Disco %', data: disk, borderColor: '#b45309', tension: 0.2 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: { y: { min: 0, max: 100 } },
      plugins: { legend: { position: 'bottom' } },
    },
  });
}

function createBarChart(labels, cpu, ram, disk) {
  const ctx = document.getElementById('barChart');
  if (barChart) barChart.destroy();
  barChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'CPU promedio', data: cpu, backgroundColor: '#2563eb' },
        { label: 'RAM promedio', data: ram, backgroundColor: '#06b6d4' },
        { label: 'Disco promedio', data: disk, backgroundColor: '#f59e0b' },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: { y: { min: 0, max: 100 } },
      plugins: { legend: { position: 'bottom' } },
    },
  });
}

function renderAlerts(items) {
  el.alertsBody.innerHTML = (items || []).map((it) => `
    <tr>
      <td>${it.id}</td>
      <td>${it.created_at}</td>
      <td class="${formatSeverityClass(it.severity)}">${it.severity}</td>
      <td>${it.reason}</td>
      <td>${it.value}</td>
      <td>${it.threshold}</td>
    </tr>
  `).join('');
}

async function loadStats() {
  const res = await fetch('/api/stats');
  if (!res.ok) return;
  const data = await res.json();

  el.kpiSamples.textContent = data.total_samples;
  el.kpiCritical.textContent = data.alerts_critical;

  if (data.latest) {
    el.kpiCpu.textContent = `${data.latest.cpu_percent}%`;
    el.kpiRam.textContent = `${data.latest.ram_percent}%`;
  }

  const runtime = data.runtime;
  const txt = runtime.is_sampling ? `activo · cada ${runtime.sample_seconds}s` : 'pausado';
  el.runtimeState.textContent = `Estado: ${txt}`;
}

async function loadSeries() {
  const res = await fetch('/api/series?limit=240');
  if (!res.ok) return;
  const data = await res.json();
  const items = data.items || [];

  const labels = items.map((x) => x.created_at.slice(11));
  const cpu = items.map((x) => x.cpu_percent);
  const ram = items.map((x) => x.ram_percent);
  const disk = items.map((x) => x.disk_percent);

  createLineChart(labels, cpu, ram, disk);
}

async function loadRollup() {
  const res = await fetch(`/api/rollup?mode=${rollupMode}`);
  if (!res.ok) return;
  const data = await res.json();
  const items = data.items || [];

  const labels = items.map((x) => x.bucket.slice(5, 16));
  const cpu = items.map((x) => x.cpu_avg);
  const ram = items.map((x) => x.ram_avg);
  const disk = items.map((x) => x.disk_avg);

  createBarChart(labels, cpu, ram, disk);
}

async function loadAlerts() {
  const res = await fetch('/api/alerts?limit=120');
  if (!res.ok) return;
  const data = await res.json();
  renderAlerts(data.items || []);
}

async function sendControl(action, value = null) {
  const payload = value === null ? { action } : { action, value };
  await fetch('/api/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  await loadStats();
}

async function refreshAll() {
  await Promise.all([loadStats(), loadSeries(), loadRollup(), loadAlerts()]);
}

el.pauseBtn.addEventListener('click', () => sendControl('pause'));
el.resumeBtn.addEventListener('click', () => sendControl('resume'));
el.applyIntervalBtn.addEventListener('click', () => {
  const value = parseFloat(el.intervalInput.value || '2');
  sendControl('interval', value);
});

el.hourBtn.addEventListener('click', async () => {
  rollupMode = 'hour';
  el.hourBtn.classList.add('active');
  el.dayBtn.classList.remove('active');
  await loadRollup();
});

el.dayBtn.addEventListener('click', async () => {
  rollupMode = 'day';
  el.dayBtn.classList.add('active');
  el.hourBtn.classList.remove('active');
  await loadRollup();
});

refreshAll();
setInterval(refreshAll, 4000);
