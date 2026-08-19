(function () {
  const cfg = window.APM_SERVER_MONITORING;
  if (!cfg) return;

  const URL = cfg.url;
  let refreshTimer = null;
  let lastUpdate = null;

  const chartOpts = (label, color) => ({
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label,
          data: [],
          borderColor: color,
          backgroundColor: color + "22",
          fill: true,
          tension: 0.3,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { display: true, ticks: { maxTicksToAutoSkip: true, maxRotation: 0 } },
        y: { beginAtZero: true, max: 100 },
      },
      plugins: { legend: { display: false } },
      animation: false,
    },
  });

  const cpuChart = new Chart(document.getElementById("chart-cpu"), chartOpts("CPU %", "#6366f1"));
  const ramChart = new Chart(document.getElementById("chart-ram"), chartOpts("RAM %", "#f59e0b"));
  const diskChart = new Chart(document.getElementById("chart-disk"), chartOpts("Disque %", "#10b981"));
  const netChart = new Chart(document.getElementById("chart-net"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "Envoyé", data: [], borderColor: "#6366f1", tension: 0.3, pointRadius: 0 },
        { label: "Reçu", data: [], borderColor: "#f59e0b", tension: 0.3, pointRadius: 0 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { x: { ticks: { maxRotation: 0 } }, y: { beginAtZero: true } },
      animation: false,
    },
  });

  function colorGauge(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("gauge-ok", "gauge-warn", "gauge-crit");
    if (val >= 90) el.classList.add("gauge-crit");
    else if (val >= 70) el.classList.add("gauge-warn");
    else el.classList.add("gauge-ok");
  }

  function fmtTime(iso) {
    return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function updateLiveStatus(ok) {
    const dot = document.getElementById("live-dot");
    const label = document.getElementById("live-label");
    if (!dot || !label) return;
    dot.classList.toggle("is-live", ok);
    dot.classList.toggle("is-error", !ok);
    if (ok && lastUpdate) {
      label.textContent = "En direct · MAJ " + fmtTime(lastUpdate);
    } else if (!ok) {
      label.textContent = "Erreur de connexion";
    }
  }

  function hideEmptyState() {
    const empty = document.getElementById("monitoring-empty");
    if (empty) empty.hidden = true;
  }

  function refresh() {
    const hours = document.getElementById("time-range").value;
    fetch(URL + "?hours=" + hours, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    })
      .then((r) => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then((data) => {
        const m = data.metrics || [];
        if (m.length) hideEmptyState();

        const labels = m.map((p) => fmtTime(p.collected_at));
        cpuChart.data.labels = labels;
        cpuChart.data.datasets[0].data = m.map((p) => p.cpu_percent);
        cpuChart.update();
        ramChart.data.labels = labels;
        ramChart.data.datasets[0].data = m.map((p) => p.memory_percent);
        ramChart.update();
        diskChart.data.labels = labels;
        diskChart.data.datasets[0].data = m.map((p) => p.disk_percent);
        diskChart.update();
        netChart.data.labels = labels;
        netChart.data.datasets[0].data = m.map((p) => p.net_bytes_sent);
        netChart.data.datasets[1].data = m.map((p) => p.net_bytes_recv);
        netChart.update();

        const s = data.summary;
        if (s && s.cpu !== undefined) {
          document.getElementById("val-cpu").textContent = s.cpu.toFixed(1) + " %";
          document.getElementById("val-ram").textContent = s.ram.toFixed(1) + " %";
          document.getElementById("val-disk").textContent = s.disk.toFixed(1) + " %";
          document.getElementById("val-load").textContent = s.load.toFixed(2);
          document.getElementById("val-uptime").textContent = s.uptime_h + " h";
          colorGauge("gauge-cpu", s.cpu);
          colorGauge("gauge-ram", s.ram);
          colorGauge("gauge-disk", s.disk);
          lastUpdate = s.collected_at || new Date().toISOString();
        }
        updateLiveStatus(true);
      })
      .catch(() => updateLiveStatus(false));
  }

  function getRefreshMs() {
    const sel = document.getElementById("refresh-interval");
    return parseInt(sel ? sel.value : "5000", 10);
  }

  function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    refresh();
    refreshTimer = setInterval(refresh, getRefreshMs());
  }

  document.getElementById("time-range").addEventListener("change", refresh);
  document.getElementById("refresh-interval").addEventListener("change", startAutoRefresh);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      if (refreshTimer) clearInterval(refreshTimer);
      refreshTimer = null;
    } else {
      startAutoRefresh();
    }
  });

  startAutoRefresh();
})();
