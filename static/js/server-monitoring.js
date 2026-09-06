/* =========================================================
   APM – Server Monitoring JS
   Real-time charts + KPI gauges + progress bars
   ========================================================= */
(function () {
  const cfg = window.APM_SERVER_MONITORING;
  if (!cfg) return;

  const URL = cfg.url;
  let refreshTimer = null;
  let lastUpdate = null;

  /* ── Chart palette ─────────────────────────────────────── */
  const isDark = () => document.documentElement.getAttribute("data-theme") === "dark";

  const gridColor = () => isDark() ? "rgba(255,255,255,.07)" : "rgba(21,32,90,.07)";
  const tickColor = () => isDark() ? "#94a3b8" : "#64748b";

  function baseOpts(max100 = true) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          display: true,
          grid: { color: gridColor() },
          ticks: {
            color: tickColor(),
            maxRotation: 0,
            font: { size: 11, family: "Inter, system-ui, sans-serif" },
          },
        },
        y: {
          beginAtZero: true,
          ...(max100 ? { max: 100 } : {}),
          grid: { color: gridColor() },
          ticks: {
            color: tickColor(),
            font: { size: 11, family: "Inter, system-ui, sans-serif" },
          },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isDark() ? "#1e293b" : "#fff",
          borderColor: isDark() ? "rgba(255,255,255,.1)" : "rgba(21,32,90,.12)",
          borderWidth: 1,
          titleColor: isDark() ? "#e2e8f0" : "#15205a",
          bodyColor: isDark() ? "#94a3b8" : "#475569",
          padding: 10,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y != null ? ctx.parsed.y.toFixed(1) : "—"}`,
          },
        },
      },
      animation: { duration: 300 },
    };
  }

  function makeGradient(canvas, color1, color2) {
    const ctx = canvas.getContext("2d");
    const g = ctx.createLinearGradient(0, 0, 0, canvas.offsetHeight || 260);
    g.addColorStop(0, color1 + "44");
    g.addColorStop(1, color1 + "00");
    return g;
  }

  /* ── CPU chart ─────────────────────────────────────────── */
  const cpuCanvas = document.getElementById("chart-cpu");
  const cpuChart = new Chart(cpuCanvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: "CPU %",
        data: [],
        borderColor: "#12b7eb",
        backgroundColor: makeGradient(cpuCanvas, "#12b7eb", "#15205a"),
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: baseOpts(true),
  });

  /* ── RAM chart ─────────────────────────────────────────── */
  const ramCanvas = document.getElementById("chart-ram");
  const ramChart = new Chart(ramCanvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: "RAM %",
        data: [],
        borderColor: "#6366f1",
        backgroundColor: makeGradient(ramCanvas, "#6366f1", "#8b5cf6"),
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: baseOpts(true),
  });

  /* ── Disk chart ─────────────────────────────────────────── */
  const diskCanvas = document.getElementById("chart-disk");
  const diskChart = new Chart(diskCanvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: "Disque %",
        data: [],
        borderColor: "#f59e0b",
        backgroundColor: makeGradient(diskCanvas, "#f59e0b", "#ef4444"),
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: baseOpts(true),
  });

  /* ── Network chart ─────────────────────────────────────── */
  const netCanvas = document.getElementById("chart-net");
  const netChart = new Chart(netCanvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "Envoyé", data: [], borderColor: "#10b981", backgroundColor: "#10b98122", fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 },
        { label: "Reçu", data: [], borderColor: "#3b82f6", backgroundColor: "#3b82f622", fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 },
      ],
    },
    options: {
      ...baseOpts(false),
      plugins: {
        ...baseOpts(false).plugins,
        legend: { display: true, labels: { color: tickColor(), font: { size: 12, family: "Inter, system-ui, sans-serif" }, boxWidth: 12, boxHeight: 12 } },
      },
    },
  });

  /* ── Gauge helpers ─────────────────────────────────────── */
  function colorGauge(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("gauge-ok", "gauge-warn", "gauge-crit");
    if (val >= 90) el.classList.add("gauge-crit");
    else if (val >= 70) el.classList.add("gauge-warn");
    else el.classList.add("gauge-ok");
  }

  function updateBar(fillId, val) {
    const fill = document.getElementById(fillId);
    if (fill) fill.style.width = Math.min(100, Math.max(0, val)).toFixed(1) + "%";
  }

  /* ── Time formatting ───────────────────────────────────── */
  function fmtTime(iso) {
    return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  /* ── Live indicator ────────────────────────────────────── */
  function updateLiveStatus(ok) {
    const dot   = document.getElementById("live-dot");
    const label = document.getElementById("live-label");
    if (!dot || !label) return;
    dot.classList.toggle("is-live",  ok);
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

  /* ── Main refresh ──────────────────────────────────────── */
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

        cpuChart.data.labels                = labels;
        cpuChart.data.datasets[0].data      = m.map((p) => p.cpu_percent);
        cpuChart.update();

        ramChart.data.labels                = labels;
        ramChart.data.datasets[0].data      = m.map((p) => p.memory_percent);
        ramChart.update();

        diskChart.data.labels               = labels;
        diskChart.data.datasets[0].data     = m.map((p) => p.disk_percent);
        diskChart.update();

        netChart.data.labels                = labels;
        netChart.data.datasets[0].data      = m.map((p) => p.net_bytes_sent);
        netChart.data.datasets[1].data      = m.map((p) => p.net_bytes_recv);
        netChart.update();

        /* KPI gauges + progress bars */
        const s = data.summary;
        if (s && s.cpu !== undefined) {
          document.getElementById("val-cpu").textContent   = s.cpu.toFixed(1) + " %";
          document.getElementById("val-ram").textContent   = s.ram.toFixed(1) + " %";
          document.getElementById("val-disk").textContent  = s.disk.toFixed(1) + " %";
          document.getElementById("val-load").textContent  = s.load.toFixed(2);
          document.getElementById("val-uptime").textContent = s.uptime_h + " h";

          updateBar("bar-cpu-fill",  s.cpu);
          updateBar("bar-ram-fill",  s.ram);
          updateBar("bar-disk-fill", s.disk);

          colorGauge("gauge-cpu",  s.cpu);
          colorGauge("gauge-ram",  s.ram);
          colorGauge("gauge-disk", s.disk);

          /* CPU peak */
          if (m.length) {
            const maxCpu = Math.max(...m.map(p => p.cpu_percent));
            const peakEl = document.getElementById("cpu-peak");
            if (peakEl) peakEl.textContent = "Pic : " + maxCpu.toFixed(1) + " %";
          }

          lastUpdate = s.collected_at || new Date().toISOString();
        }
        updateLiveStatus(true);
      })
      .catch(() => updateLiveStatus(false));
  }

  /* ── Auto refresh control ──────────────────────────────── */
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

  /* Pause polling when tab is hidden */
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
