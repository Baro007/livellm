// LiveLLM Observability Dashboard Client Engine
document.addEventListener('DOMContentLoaded', () => {
  initUtcClock();
  loadModels();
  loadAlerts();
  loadDiurnalHeatmap();
  loadDriftChart();
  loadLatencyChart();
  setupEventListeners();
  loadDynamicCatalog();
  initCitizenTelemetry();

  const savedKey = localStorage.getItem('livellm_api_key');
  if (savedKey && document.getElementById('probe-api-key')) {
    document.getElementById('probe-api-key').value = savedKey;
  }
  const savedBaseUrl = localStorage.getItem('livellm_base_url');
  if (savedBaseUrl && document.getElementById('probe-base-url')) {
    document.getElementById('probe-base-url').value = savedBaseUrl;
  }
});

let driftChartInstance = null;
let latencyChartInstance = null;

// 1. UTC CLOCK & GLOBAL TRAFFIC STATE
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

    clockEl.textContent = `${hoursStr}:${utcMins}:${utcSecs} UTC`;

    // Peak hours: 14:00 - 18:00 UTC
    if (utcHours >= 14 && utcHours <= 18) {
      trafficBadge.className = 'traffic-badge peak';
      trafficText.textContent = `ZİRVE TRAFİK ZAMANI (14-18 UTC) • Yüksek Kuyruk & Darboğaz`;
    } else {
      trafficBadge.className = 'traffic-badge normal';
      trafficText.textContent = `Normal Trafik Koşulları • Kararlı Çıkarım`;
    }
  }

  update();
  setInterval(update, 1000);
}

// 2. FETCH MODELS
async function loadModels() {
  try {
    const res = await fetch('/api/models');
    const data = await res.json();
    const grid = document.getElementById('models-grid');
    grid.innerHTML = '';

    data.models.forEach(m => {
      const card = document.createElement('div');
      const isNerfed = m.current_status.includes('Degraded') || m.active_alerts > 0;
      card.className = `model-card ${isNerfed ? 'has-alert' : ''}`;
      
      const statusClass = isNerfed ? 'degraded' : 'optimal';
      const statusLabel = isNerfed ? 'Nerf Uyarısı' : 'Optimal';

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
            <span class="stat-label">TEMEL HIZ</span>
            <span class="stat-value">${m.baseline_tps} <small style="font-size:10px; color:var(--text-muted)">TPS</small></span>
          </div>
          <div class="stat-item">
            <span class="stat-label">TEMEL TTFT</span>
            <span class="stat-value">${m.baseline_ttft_ms} <small style="font-size:10px; color:var(--text-muted)">ms</small></span>
          </div>
          <div class="stat-item">
            <span class="stat-label">DOĞRULUK ORANI</span>
            <span class="stat-value">${(m.base_accuracy * 100).toFixed(1)}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">AKTİF ALARM</span>
            <span class="stat-value" style="color: ${m.active_alerts > 0 ? '#f87171' : 'var(--accent-green)'}">
              ${m.active_alerts > 0 ? m.active_alerts + ' KRİTİK' : 'Yok'}
            </span>
          </div>
        </div>
      `;

      card.addEventListener('click', () => {
        document.getElementById('model-selector').value = m.id;
        document.getElementById('probe-model').value = m.id;
        loadDriftChart(m.id);
        loadLatencyChart(m.id);
      });

      grid.appendChild(card);
    });
  } catch (err) {
    console.error('Failed to load models', err);
  }
}

// 3. FETCH ALERTS
async function loadAlerts() {
  try {
    const res = await fetch('/api/alerts');
    const data = await res.json();
    const container = document.getElementById('alerts-container');

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
              <strong>Page-Hinkley İstatistiği:</strong> PH = ${a.ph_score} (Kritik Eşik: λ = ${a.threshold}) • 
              <strong>Yetenek Aşınması:</strong> %${a.drop_percentage} gerileme.
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

// 4. 24-HOUR DIURNAL HEATMAP
async function loadDiurnalHeatmap() {
  try {
    const res = await fetch('/api/metrics/diurnal');
    const resData = await res.json();
    const container = document.getElementById('heatmap-container');
    container.innerHTML = '';

    // Group by model
    const modelsMap = {};
    resData.data.forEach(d => {
      if (!modelsMap[d.model_id]) modelsMap[d.model_id] = [];
      modelsMap[d.model_id].push(d);
    });

    // Render Hour header
    const headerRow = document.createElement('div');
    headerRow.className = 'heatmap-row';
    headerRow.innerHTML = '<div class="heatmap-row-header">UTC SAATİ ➔</div>';
    for (let h = 0; h < 24; h++) {
      const isPeak = resData.peak_hours_utc.includes(h);
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

      const modelHeader = document.createElement('div');
      modelHeader.className = 'heatmap-row-header';
      modelHeader.textContent = modelId;
      row.appendChild(modelHeader);

      hours.sort((a, b) => a.hour_utc - b.hour_utc);

      hours.forEach(hData => {
        const cell = document.createElement('div');
        cell.className = 'heatmap-cell';
        
        // Color scale based on TPS
        const tps = hData.avg_tps;
        const ttft = hData.avg_ttft_ms;
        const color = getHeatmapColor(tps);
        cell.style.backgroundColor = color;
        cell.textContent = Math.round(tps);
        cell.title = `${modelId} @ ${hData.hour_utc}:00 UTC\nOrtalama TPS: ${tps}\nOrtalama TTFT: ${ttft}ms\nP99 TTFT: ${hData.p99_ttft_ms}ms\nDoğruluk: ${(hData.accuracy_rate * 100).toFixed(1)}%`;

        row.appendChild(cell);
      });

      container.appendChild(row);
    }
  } catch (err) {
    console.error('Failed to render heatmap', err);
  }
}

function getHeatmapColor(tps) {
  // Color interpolator: < 45 = red, 45-65 = amber, 65-90 = emerald, > 90 = cyan
  if (tps < 45) return 'rgba(239, 68, 68, 0.85)';
  if (tps < 65) return 'rgba(245, 158, 11, 0.8)';
  if (tps < 85) return 'rgba(16, 185, 129, 0.75)';
  return 'rgba(0, 240, 255, 0.75)';
}

// 5. LONGITUDINAL DRIFT & NERF CHART
async function loadDriftChart(selectedModel = null) {
  const modelId = selectedModel || document.getElementById('model-selector').value || 'gpt-4o';
  try {
    const res = await fetch(`/api/metrics/drift?model_id=${modelId}`);
    const data = await res.json();
    const ctx = document.getElementById('driftChart').getContext('2d');

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
            label: 'Deterministik Doğruluk Oranı (%)',
            data: accuracyData,
            borderColor: '#00f0ff',
            backgroundColor: 'rgba(0, 240, 255, 0.08)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.2,
            yAxisID: 'y'
          },
          {
            label: 'Page-Hinkley Kümülatif Sapma (PH Skoru)',
            data: phScores,
            borderColor: '#ef4444',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: data.series.map(s => s.is_nerf_alert ? 6 : 0),
            pointBackgroundColor: '#ef4444',
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
          legend: { labels: { color: '#9aa5be', font: { family: 'Plus Jakarta Sans' } } },
          tooltip: {
            backgroundColor: '#101522',
            titleColor: '#fff',
            bodyColor: '#9aa5be',
            borderColor: '#2e3a5f',
            borderWidth: 1
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#5e6b8a' } },
          y: {
            type: 'linear',
            position: 'left',
            min: 50,
            max: 100,
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#00f0ff', callback: val => `${val}%` }
          },
          y1: {
            type: 'linear',
            position: 'right',
            min: 0,
            max: 15,
            grid: { drawOnChartArea: false },
            ticks: { color: '#ef4444', callback: val => `PH ${val}` }
          }
        }
      }
    });
  } catch (err) {
    console.error('Failed to load drift chart', err);
  }
}

// 6. TAIL LATENCY CHART (P50/P95/P99)
async function loadLatencyChart(selectedModel = null) {
  const modelId = selectedModel || document.getElementById('model-selector').value || 'gpt-4o';
  try {
    const res = await fetch(`/api/metrics/latency?model_id=${modelId}`);
    const data = await res.json();
    const ctx = document.getElementById('latencyChart').getContext('2d');

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
            label: 'P50 Medyan TTFT (ms)',
            data: p50Data,
            backgroundColor: 'rgba(16, 185, 129, 0.7)',
            borderRadius: 4
          },
          {
            label: 'P95 Kuyruk TTFT (ms)',
            data: p95Data,
            backgroundColor: 'rgba(245, 158, 11, 0.7)',
            borderRadius: 4
          },
          {
            label: 'P99 KV Tahliye Sıçraması (ms)',
            data: p99Data,
            backgroundColor: 'rgba(239, 68, 68, 0.85)',
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#9aa5be', font: { family: 'Plus Jakarta Sans' } } }
        },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#5e6b8a' } },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#9aa5be', callback: val => `${val} ms` }
          }
        }
      }
    });
  } catch (err) {
    console.error('Failed to load latency chart', err);
  }
}

// 7. EVENT LISTENERS & LIVE PROBE EXECUTION
function setupEventListeners() {
  // Tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetId = `tab-${btn.dataset.tab}`;
      document.getElementById(targetId).classList.add('active');
    });
  });

  // Model Selector
  document.getElementById('model-selector').addEventListener('change', e => {
    const val = e.target.value;
    loadDriftChart(val);
    loadLatencyChart(val);
  });

  // Refresh Button
  document.getElementById('btn-refresh-all').addEventListener('click', () => {
    loadModels();
    loadAlerts();
    loadDiurnalHeatmap();
    loadDriftChart();
    loadLatencyChart();
  });

  // Live Probe Runner
  document.getElementById('btn-run-probe').addEventListener('click', async () => {
    const modelId = document.getElementById('probe-model').value;
    const tier = parseInt(document.getElementById('probe-tier').value);
    const useNonce = document.getElementById('probe-nonce').checked;

    const apiKey = document.getElementById('probe-api-key').value.trim();
    const baseUrl = document.getElementById('probe-base-url').value.trim();
    if (apiKey) localStorage.setItem('livellm_api_key', apiKey);
    if (baseUrl) localStorage.setItem('livellm_base_url', baseUrl);

    const statusBadge = document.getElementById('probe-status-badge');
    const modeBadge = document.getElementById('probe-mode-badge');
    const runBtn = document.getElementById('btn-run-probe');
    const streamOutput = document.getElementById('stream-output');

    statusBadge.className = 'badge badge-running';
    statusBadge.textContent = 'Çıkarım Yapılıyor...';
    modeBadge.textContent = apiKey ? '🟢 Canlı Sağlayıcı API Bağlantısı Kuruluyor...' : '🟡 Kalibre Edilmiş Simülasyon Çalıştırılıyor...';
    modeBadge.style.color = apiKey ? 'var(--accent-green)' : 'var(--accent-amber)';

    runBtn.disabled = true;
    streamOutput.textContent = `[LiveLLM Probe Initiated] Hedef: ${modelId} • Tier: ${tier} • Nonce: ${useNonce ? 'Aktif' : 'Pasif'}\n` +
      `Mod: ${apiKey ? 'Gerçek Canlı API Bağlantısı (' + (baseUrl || 'Resmi Sağlayıcı') + ')' : 'Kalibre Edilmiş Benchmark Modu'}\nBağlantı kuruluyor...\n`;

    // Clear gauges
    document.getElementById('res-ttft').textContent = '... ms';
    document.getElementById('res-tps').textContent = '... tps';
    document.getElementById('res-tpot').textContent = '... ms';
    document.getElementById('res-eval').textContent = '...';

    try {
      const res = await fetch('/api/probe/live', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: modelId,
          tier: tier,
          use_nonce: useNonce,
          custom_api_key: apiKey || null,
          custom_base_url: baseUrl || null
        })
      });

      const result = await res.json();
      const tele = result.telemetry;
      const evalRes = result.evaluation;

      // Update execution mode indicator
      if (result.execution_mode === 'real_live_api') {
        modeBadge.textContent = '🟢 GERÇEK CANLI API ÇIKARIMI (Live HTTP SSE)';
        modeBadge.style.color = 'var(--accent-green)';
      } else if (result.execution_mode && result.execution_mode.startsWith('live_api_failed')) {
        modeBadge.textContent = '⚠️ ' + result.execution_mode;
        modeBadge.style.color = 'var(--accent-red)';
      } else {
        modeBadge.textContent = '🟡 KALİBRE EDİLMİŞ VERİ (API Key Girilmedi)';
        modeBadge.style.color = 'var(--accent-amber)';
      }

      // Update gauges
      document.getElementById('res-ttft').textContent = `${tele.ttft_ms} ms`;
      document.getElementById('res-tps').textContent = `${tele.tps} tps`;
      document.getElementById('res-tpot').textContent = `${tele.tpot_ms} ms`;

      const evalBadge = document.getElementById('res-eval');
      if (evalRes.is_correct) {
        evalBadge.textContent = 'BAŞARILI ✓';
        evalBadge.style.color = 'var(--accent-green)';
      } else {
        evalBadge.textContent = 'BAŞARISIZ ✗';
        evalBadge.style.color = 'var(--accent-red)';
      }
      document.getElementById('res-eval-sub').textContent = evalRes.debug || 'Doğrulandı';

      // Typewriter emulation of received text
      streamOutput.textContent = `[Cache-Buster Nonce]: ${result.nonce_used || 'Devre dışı'}\n` +
        `[Çıkarım Modu]: ${result.execution_mode || 'Standart'}\n\n`;
      let text = tele.full_text;
      let i = 0;
      const interval = setInterval(() => {
        if (i < text.length) {
          streamOutput.textContent += text.slice(i, i + 3);
          i += 3;
          streamOutput.scrollTop = streamOutput.scrollHeight;
        } else {
          clearInterval(interval);
          streamOutput.textContent += `\n\n[Tamamlandı] TTFT: ${tele.ttft_ms}ms | TPS: ${tele.tps} | Token: ${tele.universal_tokens}`;
          loadModels(); // Refresh model health indicators with the new live run
        }
      }, 15);

      statusBadge.className = 'badge badge-idle';
      statusBadge.textContent = 'Tamamlandı';
      runBtn.disabled = false;

    } catch (err) {
      console.error('Probe execution failed', err);
      statusBadge.className = 'badge badge-idle';
      statusBadge.textContent = 'Hata Oluştu';
      runBtn.disabled = false;
      streamOutput.textContent += `\n[HATA]: ${err.message}`;
    }
  });
}

// 8. DYNAMIC CATALOG LOADER (Astra & Free-Tier Models)
async function loadDynamicCatalog() {
  try {
    const res = await fetch('/api/catalog/dynamic');
    const catalog = await res.json();

    const selectors = [
      document.getElementById('model-selector'),
      document.getElementById('probe-model')
    ];

    selectors.forEach(sel => {
      if (!sel) return;
      const currentVal = sel.value;
      sel.innerHTML = '';

      // Group 1: 🌟 2026 Frontier Modeller (Astra, Gemini 3.8, Claude Fable, DeepSeek V4)
      const groupFrontier = document.createElement('optgroup');
      groupFrontier.label = '🌟 2026 Frontier Modeller (Astra / Fable / 3.8 / V4)';
      catalog.frontier_models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = `${m.name} (${m.provider})`;
        groupFrontier.appendChild(opt);
      });
      sel.appendChild(groupFrontier);

      // Group 2: 🆓 Sıfır Maliyetli Açık Havuz (:free & Free Tiers)
      const groupFree = document.createElement('optgroup');
      groupFree.label = '🆓 Sıfır Maliyetli Açık Havuz ($0.00 / :free)';
      catalog.free_models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = `${m.name} [Ücretsiz]`;
        groupFree.appendChild(opt);
      });
      sel.appendChild(groupFree);

      if (currentVal && Array.from(sel.options).some(o => o.value === currentVal)) {
        sel.value = currentVal;
      }
    });
  } catch (err) {
    console.error('Failed to load dynamic catalog', err);
  }
}

// 9. CITIZEN TELEMETRY (Amme Hizmeti - Dağıtık Topluluk Gözlemcisi)
function initCitizenTelemetry() {
  const toggle = document.getElementById('citizen-telemetry-toggle');
  const label = document.getElementById('citizen-telemetry-label');
  if (!toggle) return;

  const isOptedIn = localStorage.getItem('livellm_citizen_optin') === 'true';
  toggle.checked = isOptedIn;
  updateCitizenLabel(isOptedIn);

  toggle.addEventListener('change', e => {
    const checked = e.target.checked;
    localStorage.setItem('livellm_citizen_optin', checked ? 'true' : 'false');
    updateCitizenLabel(checked);
    if (checked) {
      runCitizenPulse();
    }
  });

  function updateCitizenLabel(active) {
    if (active) {
      label.textContent = 'Arka planda anonim testlere katılıyor (Aktif • Dağıtık Düğüm)';
      label.style.color = 'var(--accent-green)';
    } else {
      label.textContent = 'Arka planda anonim testlere katıl (Pasif)';
      label.style.color = 'var(--text-muted)';
    }
  }

  // Periodic lightweight micro-probe every 5 minutes if opted in
  setInterval(() => {
    if (toggle.checked) {
      runCitizenPulse();
    }
  }, 300000);

  async function runCitizenPulse() {
    try {
      // Run probe on a zero-cost model
      const res = await fetch('/api/probe/live', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: 'nex-agi/nex-n2.5-pro:free',
          tier: 1,
          use_nonce: true
        })
      });
      const data = await res.json();
      // Submit crowd telemetry
      await fetch('/api/telemetry/crowd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: data.telemetry.model_id,
          ttft_ms: data.telemetry.ttft_ms,
          tps: data.telemetry.tps,
          tpot_ms: data.telemetry.tpot_ms,
          universal_tokens: data.telemetry.universal_tokens,
          is_correct: data.evaluation ? data.evaluation.is_correct : true,
          region_hint: 'Community Browser Client'
        })
      });
      console.log('[LiveLLM Citizen Telemetry] Micro-pulse contributed successfully.');
    } catch (e) {
      console.warn('[Citizen Telemetry] Pulse skipped:', e.message);
    }
  }
}
