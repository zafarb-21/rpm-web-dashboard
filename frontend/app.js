const API_BASE = ""; // same domain as backend on Render

const patientSelect = document.getElementById("patientSelect");
const refreshBtn = document.getElementById("refreshBtn");

const el = (id) => document.getElementById(id);

let hrChart, spo2Chart, tempChart, ecgChart;

function setBadge(level) {
  const badge = el("alertBadge");
  badge.className = "badge";
  badge.textContent = level ? level.toUpperCase() : "—";
  if (!level) return;
  badge.classList.add(level.toLowerCase());
}

function fmt(v, suffix = "") {
  if (v === null || v === undefined) return "—";
  if (Number.isFinite(v)) return `${v}${suffix}`;
  return `${v}${suffix}`;
}

async function fetchJSON(path) {
  const r = await fetch(`${API_BASE}${path}`);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return await r.json();
}

async function loadPatients() {
  const data = await fetchJSON("/patients");
  const patients = data.patients || [];
  patientSelect.innerHTML = "";
  for (const p of patients) {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p;
    patientSelect.appendChild(opt);
  }
  if (patients.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No patients yet (ESP32 not publishing)";
    patientSelect.appendChild(opt);
  }
}

function ensureChart(canvasId, label) {
  const ctx = document.getElementById(canvasId);
  return new Chart(ctx, {
    type: "line",
    data: { labels: [], datasets: [{ label, data: [] }] },
    options: {
      responsive: true,
      animation: false,
      plugins: { legend: { display: true } },
      scales: {
        x: { ticks: { maxRotation: 0, autoSkip: true } }
      }
    }
  });
}

function ensureEcgChart(canvasId) {
  const ctx = document.getElementById(canvasId);
  return new Chart(ctx, {
    type: "line",
    data: { labels: [], datasets: [{ label: "ECG", data: [] }] },
    options: {
      responsive: true,
      animation: false,
      plugins: { legend: { display: true } },
      elements: { point: { radius: 0 } },
      scales: {
        x: { display: false },
        y: { display: true }
      }
    }
  });
}

function updateChart(chart, records, field) {
  // records come newest->oldest from your endpoint; reverse for time increasing
  const ordered = [...records].reverse();
  chart.data.labels = ordered.map(r => {
    const d = new Date(r.received_at);
    return d.toLocaleTimeString();
  });
  chart.data.datasets[0].data = ordered.map(r => r[field]);
  chart.update();
}

async function loadLatest(patientId) {
  const data = await fetchJSON(`/latest/vitals/${encodeURIComponent(patientId)}`);
  const v = data.latest || {};

  setBadge(v.alert_level);
  el("receivedAt").textContent = v.received_at ? `received: ${v.received_at}` : "—";

  el("hr").textContent = fmt(v.heart_rate, " bpm");
  el("spo2").textContent = fmt(v.spo2, " %");
  el("temp").textContent = fmt(v.temperature, " °C");
  el("ecgHr").textContent = fmt(v.ecg_heart_rate, " bpm");
  el("battery").textContent = fmt(v.battery, " %");

  el("fall").textContent = `Fall: ${v.fall_detected ? "YES" : "NO"}`;
  el("leadOff").textContent = `Lead-off: ${v.lead_off ? "YES" : "NO"}`;
  el("ecgQuality").textContent = `ECG: ${v.ecg_quality ?? "—"}`;
  el("rssi").textContent = `RSSI: ${v.rssi ?? "—"}`;
}

async function loadHistory(patientId) {
  const data = await fetchJSON(`/history/vitals/${encodeURIComponent(patientId)}?limit=120`);
  const records = data.records || [];

  updateChart(hrChart, records, "heart_rate");
  updateChart(spo2Chart, records, "spo2");
  updateChart(tempChart, records, "temperature");
}

async function loadECG(patientId) {
  const data = await fetchJSON(`/latest/ecg/${encodeURIComponent(patientId)}`);
  const samples = data.ecg_samples || [];

  // Plot the samples as y-values, x-values are sample index
  ecgChart.data.labels = samples.map((_, i) => i);
  ecgChart.data.datasets[0].data = samples;

  ecgChart.update();
}

async function refreshAll() {
  const patientId = patientSelect.value;
  if (!patientId) return;
  await loadLatest(patientId);
  await loadHistory(patientId);
}

async function main() {
  hrChart = ensureChart("hrChart", "HR (bpm)");
  spo2Chart = ensureChart("spo2Chart", "SpO₂ (%)");
  tempChart = ensureChart("tempChart", "Temp (°C)");
  ecgChart = ensureEcgChart("ecgChart");

  await loadPatients();
  await refreshAll();

  patientSelect.addEventListener("change", refreshAll);
  refreshBtn.addEventListener("click", refreshAll);

  // auto-refresh every 5s
  setInterval(refreshAll, 5000);
}

main().catch(err => {
  console.error(err);
  alert("Dashboard error: " + err.message);
});

const ecgCtx = document.getElementById("ecgChart").getContext("2d");

const ecgChart = new Chart(ecgCtx, {
    type: "line",
    data: {
        labels: [],
        datasets: [{
            label: "ECG Signal",
            data: [],
            borderColor: "red",
            borderWidth: 1,
            pointRadius: 0,
            tension: 0
        }]
    },
    options: {
        animation: false,
        scales: {
            x: { display: false },
            y: { beginAtZero: false }
        }
    }
});
