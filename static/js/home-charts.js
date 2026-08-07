/**
 * Topnet APM — mini-charts for the Accueil page.
 */
(function () {
  "use strict";

  var SOFT = [
    "rgba(225, 29, 72, 0.85)",
    "rgba(245, 138, 18, 0.85)",
    "rgba(202, 138, 4, 0.75)",
    "rgba(5, 150, 105, 0.85)",
  ];

  function readData() {
    var el = document.getElementById("home-charts-data");
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
            boxWidth: 10,
            usePointStyle: true,
            font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
            color: "#475569",
          },
        },
      },
    };
    if (extra) {
      Object.keys(extra).forEach(function (key) {
        opts[key] = extra[key];
      });
    }
    return opts;
  }

  function mount() {
    if (typeof Chart === "undefined") return;
    var data = readData();
    if (!data) return;

    var certsEl = document.getElementById("home-chart-certs");
    if (certsEl && data.certs_expiry_buckets) {
      new Chart(certsEl, {
        type: "doughnut",
        data: {
          labels: data.certs_expiry_buckets.labels,
          datasets: [
            {
              data: data.certs_expiry_buckets.values,
              backgroundColor: SOFT,
              borderWidth: 0,
            },
          ],
        },
        options: baseOptions({
          cutout: "62%",
          plugins: {
            legend: {
              position: "bottom",
              labels: {
                boxWidth: 10,
                usePointStyle: true,
                font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
                color: "#475569",
              },
            },
          },
        }),
      });
    }

    var trendsEl = document.getElementById("home-chart-trends");
    if (trendsEl && data.apps_trend_6m && data.incidents_trend_6m) {
      new Chart(trendsEl, {
        type: "line",
        data: {
          labels: data.apps_trend_6m.labels,
          datasets: [
            {
              label: "Applications",
              data: data.apps_trend_6m.values,
              borderColor: "#12b7eb",
              backgroundColor: "rgba(18, 183, 235, 0.15)",
              tension: 0.35,
              fill: true,
              pointRadius: 3,
            },
            {
              label: "Incidents",
              data: data.incidents_trend_6m.values,
              borderColor: "#e11d48",
              backgroundColor: "rgba(225, 29, 72, 0.08)",
              tension: 0.35,
              fill: true,
              pointRadius: 3,
            },
          ],
        },
        options: baseOptions({
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: "#64748b", font: { size: 10 } },
            },
            y: {
              beginAtZero: true,
              ticks: { precision: 0, color: "#64748b", font: { size: 10 } },
              grid: { color: "rgba(100, 116, 139, 0.15)" },
            },
          },
        }),
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
