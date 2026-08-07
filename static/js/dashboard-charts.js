/**
 * Topnet APM — dashboard Chart.js renderers.
 */
(function () {
  "use strict";

  var PALETTE = [
    "#15205a",
    "#12b7eb",
    "#f58a12",
    "#059669",
    "#7c3aed",
    "#e11d48",
    "#0ea5e9",
    "#ca8a04",
  ];

  var SOFT = [
    "rgba(21, 32, 90, 0.85)",
    "rgba(18, 183, 235, 0.85)",
    "rgba(245, 138, 18, 0.85)",
    "rgba(5, 150, 105, 0.85)",
    "rgba(124, 58, 237, 0.85)",
    "rgba(225, 29, 72, 0.85)",
    "rgba(14, 165, 233, 0.85)",
    "rgba(202, 138, 4, 0.85)",
  ];

  function colors(n) {
    var out = [];
    for (var i = 0; i < n; i += 1) {
      out.push(SOFT[i % SOFT.length]);
    }
    return out;
  }

  function readData() {
    var el = document.getElementById("dashboard-charts-data");
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      return null;
    }
  }

  function baseOptions(extra) {
    var opts = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 12,
            usePointStyle: true,
            font: { family: "'IBM Plex Sans', sans-serif", size: 12 },
            color: "#475569",
          },
        },
        tooltip: {
          backgroundColor: "rgba(11, 16, 40, 0.92)",
          titleFont: { family: "'Manrope', sans-serif", weight: "700" },
          bodyFont: { family: "'IBM Plex Sans', sans-serif" },
          padding: 10,
          cornerRadius: 10,
        },
      },
    };
    if (extra) {
      Object.keys(extra).forEach(function (key) {
        if (key === "plugins") {
          opts.plugins = Object.assign({}, opts.plugins, extra.plugins);
        } else {
          opts[key] = extra[key];
        }
      });
    }
    return opts;
  }

  function makeDoughnut(id, series) {
    var canvas = document.getElementById(id);
    if (!canvas || !series || !window.Chart) return;
    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: series.labels || [],
        datasets: [
          {
            data: series.values || [],
            backgroundColor: colors((series.values || []).length),
            borderWidth: 2,
            borderColor: "#ffffff",
            hoverOffset: 6,
          },
        ],
      },
      options: baseOptions({
        cutout: "62%",
        plugins: {
          legend: { position: "bottom" },
        },
      }),
    });
  }

  function makeBar(id, series, horizontal) {
    var canvas = document.getElementById(id);
    if (!canvas || !series || !window.Chart) return;
    new Chart(canvas, {
      type: "bar",
      data: {
        labels: series.labels || [],
        datasets: [
          {
            label: "Volume",
            data: series.values || [],
            backgroundColor: colors((series.values || []).length),
            borderRadius: 8,
            maxBarThickness: 42,
          },
        ],
      },
      options: baseOptions({
        indexAxis: horizontal ? "y" : "x",
        plugins: { legend: { display: false } },
        scales: {
          x: {
            grid: { color: "rgba(21, 32, 90, 0.06)" },
            ticks: { color: "#64748b", font: { size: 11 } },
            beginAtZero: true,
            precision: 0,
          },
          y: {
            grid: { color: "rgba(21, 32, 90, 0.06)" },
            ticks: { color: "#64748b", font: { size: 11 }, precision: 0 },
            beginAtZero: true,
          },
        },
      }),
    });
  }

  function makeTrends(id, apps, incidents) {
    var canvas = document.getElementById(id);
    if (!canvas || !window.Chart) return;
    var labels = (apps && apps.labels) || (incidents && incidents.labels) || [];
    new Chart(canvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Applications",
            data: (apps && apps.values) || [],
            borderColor: "#15205a",
            backgroundColor: "rgba(21, 32, 90, 0.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: "#15205a",
          },
          {
            label: "Incidents",
            data: (incidents && incidents.values) || [],
            borderColor: "#f58a12",
            backgroundColor: "rgba(245, 138, 18, 0.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: "#f58a12",
          },
        ],
      },
      options: baseOptions({
        interaction: { mode: "index", intersect: false },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: "#64748b", font: { size: 11 } },
          },
          y: {
            beginAtZero: true,
            grid: { color: "rgba(21, 32, 90, 0.06)" },
            ticks: { color: "#64748b", precision: 0 },
          },
        },
      }),
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var data = readData();
    if (!data || !window.Chart) return;

    makeBar("chart-portfolio", data.portfolio_overview, false);
    makeDoughnut("chart-apps-status", data.apps_by_status);
    makeBar("chart-apps-criticality", data.apps_by_criticality, true);
    makeDoughnut("chart-incidents-status", data.incidents_by_status);
    makeBar("chart-incidents-impact", data.incidents_by_impact, true);
    makeBar("chart-documents-category", data.documents_by_category, true);
    makeBar("chart-certs-expiry", data.certs_expiry_buckets, false);
    makeDoughnut("chart-contracts-status", data.contracts_by_status);
    makeTrends("chart-trends", data.apps_trend_6m, data.incidents_trend_6m);
  });
})();
