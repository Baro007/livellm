// LiveLLM Observability Dashboard Client Engine
// Optimized for Netlify Static Jamstack & FastAPI Local Server

let allModelsData = [];
let driftCache = null;
let latencyCache = null;
let activeProviderFilter = 'all';
let searchQuery = '';

let driftChartInstance = null;
let latencyChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  initUtcClock();
  initTenMinCountdown();
  setupEventListeners();
  loadAllData();
});

// Helper: Resilient fetch with fallback to static /data/ directory
async function fetchWithStaticFallback(apiPath, staticPath) {
  try {
    const res = await fetch(apiPath);
    if (res.ok) {
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        return await res.json();
      }
    }
  } catch (e) {
    // API failed, fallback to static
  }

  // Fallback to static JSON
  const staticRes = await fetch(staticPath);
  return await staticRes.json();
}

// 1. UTC CLOCK & GLOBAL TRAFFIC STATUS
function initUtcClock() {
  const clockEl = document.getElementById('utc-clock');
  const trafficBadge = document.getElementById('traffic-window-badge');
  const trafficText = document.getElementById('traffic-status-text');

  function update() {
    const now = new Date();
    const utcHours = now.getUTCHours();
    const utcMins = String(now.getUTCMinutes()).padStart(2, '0');
    const utcSecs = String(now.getUTCSeconds()).padStart(2, '0');
    const hoursStr = String(utcHours).padStart(2, '0');

    if (clockEl) {
      clockEl.textContent = `${hoursStr}:${utcMins}:${utcSecs}`;
    }

    // Global Peak hours: 14:00 - 18:00 UTC
    if (trafficBadge && trafficText) {
      if (utcHours >= 14 && utcHours <= 18) {
        trafficBadge.className = 'traffic-badge peak';
        trafficText.textContent = `ZİRVE SAATLER (14-18 UTC) • Yüksek Kuyruk`;
      } else {
        trafficBadge.className = 'traffic-badge normal';
        trafficText.textContent = `Normal Trafik Koşulları`;
      }
    }
  }

  update();
  setInterval(update, 1000);
}

// 2. 10-MINUTE RECURRING BENCHMARK COUNTDOWN
function initTenMinCountdown() {
  const cdEl = document.getElementById('ten-min-countdown');
  if (!cdEl) return;

  function update() {
    const now = new Date();
    const mins = now.getUTCMinutes() % 10;
    const secs = now.getUTCSeconds();
    const totalRemaining = (9 - mins) * 60 + (60 - secs);

    if (totalRemaining <= 2) {
      cdEl.textContent = 'Ölçülüyor...';
      setTimeout(() => {
        loadAllData();
      }, 4000);
      return;
    }

    const m = Math.floor(totalRemaining / 60);
    const s = totalRemaining % 60;
    cdEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  update();
  setInterval(update, 1000);
}

// 3. MASTER DATA LOADER
async function loadAllData() {
  await Promise.all([
    loadModels(),
    loadAlerts(),
    loadDiurnalHeatmap(),
    loadDriftChart(),
    loadLatencyChart()
  ]);
}

// 4. FETCH AND RENDER MODELS FLEET
async function loadModels() {
  try {
    const data = await fetchWithStaticFallback('/api/models', '/data/models.json');
    allModelsData = data.models || [];
    renderModelCards();

    const countEl = document.getElementById('kpi-total-models');
    if (countEl && allModelsData.length > 0) {
      countEl.textContent = `${allModelsData.length} Model`;
    }
  } catch (err) {
    console.error('Failed to load models', err);
  }
}

function renderModelCards() {
  const grid = document.getElementById('models-grid');
  if (!grid) return;
  grid.innerHTML = '';

  const filtered = allModelsData.filter(m => {
    // Provider filter
    if (activeProviderFilter !== 'all') {
      const p = m.provider.toLowerCase();
      if (activeProviderFilter === 'google' && !p.includes('google')) return false;
      if (activeProviderFilter === 'groq' && !p.includes('groq')) return false;
      if (activeProviderFilter === 'openrouter' && !p.includes('openrouter')) return false;
      if (activeProviderFilter === 'openai' && !p.includes('openai')) return false;
    }

    // Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchName = m.name.toLowerCase().includes(q);
      const matchId = m.id.toLowerCase().includes(q);
      const matchProv = m.provider.toLowerCase().includes(q);
      if (!matchName && !matchId && !matchProv) return false;
    }

    return true;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 30px; color: var(--text-dim);">Arama kriterlerine uygun model bulunamadı.</div>`;
    return;
  }

  filtered.forEach(m => {
    const card = document.createElement('div');
    const isNerfed = m.current_status.includes('Degraded') || m.active_alerts > 0;
    card.className = `model-card ${isNerfed ? 'has-alert' : ''}`;

    const statusClass = isNerfed ? 'degraded' : 'optimal';
    const statusLabel = isNerfed ? 'Nerf / Gerileme' : 'Formunda';

    card.innerHTML = `
      <div class="model-card-top">
        <div>
          <div class="model-name">${m.name}</div>
          <div class="model-provider">${m.provider} • ${m.tier}</div>
        </div>
        <span class="status-tag ${statusClass}">${statusLabel}</span>
      </div>
      <div class="model-card-stats">
        <div class="stat-item">
          <span class="stat-label">HIZ</span>
          <span class="stat-value">${m.baseline_tps} <small style="font-size:10px; color:var(--text-dim)">TPS</small></span>
        </div>
        <div class="stat-item">
          <span class="stat-label">İLK YANIT</span>
          <span class="stat-value">${m.baseline_ttft_ms} <small style="font-size:10px; color:var(--text-dim)">ms</small></span>
        </div>
        <div class="stat-item">
          <span class="stat-label">DOĞRULUK</span>
          <span class="stat-value">${(m.base_accuracy * 100).toFixed(1)}%</span>
        </div>
      </div>
    `;

    card.addEventListener('click', () => {
      const sel = document.getElementById('model-selector');
      if (sel) {
        sel.value = m.id;
        loadDriftChart(m.id);
        loadLatencyChart(m.id);
      }

      document.querySelectorAll('.model-card').forEach(c => c.style.borderColor = '');
      card.style.borderColor = 'var(--cyan)';
    });

    grid.appendChild(card);
  });
}

// 5. FETCH CRITICAL ALERTS
async function loadAlerts() {
  try {
    const data = await fetchWithStaticFallback('/api/alerts', '/data/alerts.json');
    const container = document.getElementById('alerts-container');
    if (!container) return;

    if (data.alerts && data.alerts.length > 0) {
      container.style.display = 'block';
      container.innerHTML = '';

      data.alerts.forEach(a => {
        const div = document.createElement('div');
        div.className = 'alert-banner';
        div.innerHTML = `
          <div class="alert-icon">⚠️</div>
          <div>
            <div class="alert-title">${a.model_name} (${a.provider}): ${a.alert_type} Doğrulandı</div>
            <div class="alert-body">
              <strong>Tespit:</strong> ${a.details}<br>
              <strong>Page-Hinkley Skoru:</strong> PH = ${a.ph_score} (Kritik Eşik: λ = ${a.threshold}) • 
              <strong>Yetenek Aşınması:</strong> %${a.drop_percentage} düşüş.
            </div>
          </div>
        `;
        container.appendChild(div);
      });
    } else {
      container.style.display = 'none';
    }
  } catch (err) {
    console.error('Failed to load alerts', err);
  }
}

// 6. 24-HOUR DIURNAL HEATMAP
async function loadDiurnalHeatmap() {
  try {
    const resData = await fetchWithStaticFallback('/api/metrics/diurnal', '/data/diurnal.json');
    const container = document.getElementById('heatmap-container');
    if (!container) return;
    container.innerHTML = '';

    // Group by model
    const modelsMap = {};
    (resData.data || []).forEach(d => {
      if (!modelsMap[d.model_id]) modelsMap[d.model_id] = [];
      modelsMap[d.model_id].push(d);
    });

    // Render Hour header
    const headerRow = document.createElement('div');
    headerRow.className = 'heatmap-row';
    headerRow.innerHTML = '<div class="heatmap-row-header">UTC SAATİ ➔</div>';
    const peakHours = resData.peak_hours_utc || [14, 15, 16, 17, 18];

    for (let h = 0; h < 24; h++) {
      const isPeak = peakHours.includes(h);
      const hLabel = document.createElement('div');
      hLabel.className = `heatmap-hour-label ${isPeak ? 'peak-hour' : ''}`;
      hLabel.textContent = `${h}h`;
      headerRow.appendChild(hLabel);
    }
    container.appendChild(headerRow);

    // Render each model row
    for (const [modelId, hours] of Object.entries(modelsMap)) {
      const row = document.createElement('div');
      row.className = 'heatmap-row';

      const rowTitle = document.createElement('div');
      rowTitle.className = 'heatmap-row-header';
      rowTitle.textContent = modelId;
      row.appendChild(rowTitle);

      hours.sort((a, b) => a.hour_utc - b.hour_utc);

      hours.forEach(h => {
        const cell = document.createElement('div');
        cell.className = 'heatmap-cell';

        const tps = h.avg_tps;
        let bg = '';
        if (tps >= 150) {
          bg = 'rgba(16, 185, 129, 0.75)'; // green
        } else if (tps >= 90) {
          bg = 'rgba(59, 130, 246, 0.7)'; // blue
        } else if (tps >= 60) {
          bg = 'rgba(245, 158, 11, 0.75)'; // amber
        } else {
          bg = 'rgba(244, 63, 94, 0.85)'; // red
        }

        cell.style.backgroundColor = bg;
        cell.textContent = Math.round(tps);
        cell.title = `${modelId} @ ${h.hour_utc}:00 UTC\nOrtalama Hız: ${tps.toFixed(1)} TPS\nİlk Yanıt (TTFT): ${h.avg_ttft_ms.toFixed(0)} ms\nP99 Gecikme: ${h.p99_ttft_ms.toFixed(0)} ms`;

        row.appendChild(cell);
      });

      container.appendChild(row);
    }
  } catch (err) {
    console.error('Failed to load diurnal heatmap', err);
  }
}

// 7. LONGITUDINAL DRIFT & NERF CHART
async function loadDriftChart(selectedModel = null) {
  const modelId = selectedModel || (document.getElementById('model-selector') ? document.getElementById('model-selector').value : null) || 'gemini-3.8-flash';
  try {
    let data = null;
    try {
      const res = await fetch(`/api/metrics/drift?model_id=${modelId}`);
      if (res.ok) data = await res.json();
    } catch (e) {}

    if (!data) {
      if (!driftCache) {
        const staticRes = await fetch('/data/drift.json');
        driftCache = await staticRes.json();
      }
      data = driftCache[modelId] || Object.values(driftCache)[0];
    }

    const chartEl = document.getElementById('driftChart');
    if (!chartEl || !data || !data.series) return;
    const ctx = chartEl.getContext('2d');

    const labels = data.series.map(s => `Gün ${s.day_index}`);
    const accuracyData = data.series.map(s => (s.accuracy * 100).toFixed(1));
    const phScores = data.series.map(s => s.ph_score);

    if (driftChartInstance) {
      driftChartInstance.destroy();
    }

    driftChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Doğruluk Oranı (%)',
            data: accuracyData,
            borderColor: '#00f0ff',
            backgroundColor: 'rgba(0, 240, 255, 0.08)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.2,
            yAxisID: 'y'
          },
          {
            label: 'Page-Hinkley Nerf Sapma Skoru',
            data: phScores,
            borderColor: '#f43f5e',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: data.series.map(s => s.is_nerf_alert ? 6 : 0),
            pointBackgroundColor: '#f43f5e',
            tension: 0.1,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: '#8b97b0', font: { family: 'Plus Jakarta Sans', size: 12 } } },
          tooltip: {
            backgroundColor: '#0e121a',
            titleColor: '#fff',
            bodyColor: '#8b97b0',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#54627d' } },
          y: {
            type: 'linear',
            position: 'left',
            min: 50,
            max: 100,
            grid: { color: 'rgba(255,255,255,0.04)' },
            ticks: { color: '#00f0ff', callback: val => `${val}%` }
          },
          y1: {
            type: 'linear',
            position: 'right',
            min: 0,
            max: 15,
            grid: { drawOnChartArea: false },
            ticks: { color: '#f43f5e', callback: val => `PH ${val}` }
          }
        }
      }
    });
  } catch (err) {
    console.error('Failed to load drift chart', err);
  }
}

// 8. TAIL LATENCY CHART
async function loadLatencyChart(selectedModel = null) {
  const modelId = selectedModel || (document.getElementById('model-selector') ? document.getElementById('model-selector').value : null) || 'gemini-3.8-flash';
  try {
    let data = null;
    try {
      const res = await fetch(`/api/metrics/latency?model_id=${modelId}`);
      if (res.ok) data = await res.json();
    } catch (e) {}

    if (!data) {
      if (!latencyCache) {
        const staticRes = await fetch('/data/latency.json');
        latencyCache = await staticRes.json();
      }
      data = latencyCache[modelId] || Object.values(latencyCache)[0];
    }

    const chartEl = document.getElementById('latencyChart');
    if (!chartEl || !data || !data.latency_data) return;
    const ctx = chartEl.getContext('2d');

    const labels = data.latency_data.map(d => `${d.hour_utc}:00 UTC`);
    const p50Data = data.latency_data.map(d => d.p50);
    const p95Data = data.latency_data.map(d => d.p95);
    const p99Data = data.latency_data.map(d => d.p99);

    if (latencyChartInstance) {
      latencyChartInstance.destroy();
    }

    latencyChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'P50 Medyan İlk Yanıt (ms)',
            data: p50Data,
            backgroundColor: 'rgba(16, 185, 129, 0.75)',
            borderRadius: 4
          },
          {
            label: 'P95 Kuyruk Beklemesi (ms)',
            data: p95Data,
            backgroundColor: 'rgba(245, 158, 11, 0.75)',
            borderRadius: 4
          },
          {
            label: 'P99 Zirve KV Sıçraması (ms)',
            data: p99Data,
            backgroundColor: 'rgba(244, 63, 94, 0.85)',
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#8b97b0', font: { family: 'Plus Jakarta Sans', size: 12 } } },
          tooltip: {
            backgroundColor: '#0e121a',
            titleColor: '#fff',
            bodyColor: '#8b97b0',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#54627d' } },
          y: {
            grid: { color: 'rgba(255,255,255,0.04)' },
            ticks: { color: '#8b97b0', callback: val => `${val} ms` }
          }
        }
      }
    });
  } catch (err) {
    console.error('Failed to load latency chart', err);
  }
}

// 9. EVENT LISTENERS
function setupEventListeners() {
  // Tabs
  document.querySelectorAll('.tab-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-item').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetId = `tab-${btn.dataset.tab}`;
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  // Model Selector dropdown for charts
  const modelSel = document.getElementById('model-selector');
  if (modelSel) {
    modelSel.addEventListener('change', e => {
      const val = e.target.value;
      loadDriftChart(val);
      loadLatencyChart(val);
    });
  }

  // Refresh Button
  const refreshBtn = document.getElementById('btn-refresh-all');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadAllData();
    });
  }

  // Provider Filter Pills
  document.querySelectorAll('.filter-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeProviderFilter = btn.dataset.filter;
      renderModelCards();
    });
  });

  // Search input
  const searchInput = document.getElementById('model-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', e => {
      searchQuery = e.target.value;
      renderModelCards();
    });
  }
}
