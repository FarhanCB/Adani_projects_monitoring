(() => {
  if (typeof Chart === "undefined") return;
  const root = document.querySelector("[data-charts-root]");
  if (!root) return;

  const COLORS = {
    up: "#15803d",
    down: "#c2410c",
    pending: "#b45309",
    blue: "#1a6fd0",
    blueSoft: "rgba(26, 111, 208, 0.18)",
    grid: "rgba(91, 113, 144, 0.18)",
    text: "#5b7190",
  };

  Chart.defaults.font.family = '"Plus Jakarta Sans", sans-serif';
  Chart.defaults.color = COLORS.text;

  let donutChart = null;
  let barChart = null;
  let trendChart = null;
  const miniCharts = new Map();
  const trendLabels = [];
  const trendDown = [];
  const TREND_MAX = 20;

  function pushTrend(downCount) {
    const now = new Date();
    const label = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    trendLabels.push(label);
    trendDown.push(downCount);
    while (trendLabels.length > TREND_MAX) {
      trendLabels.shift();
      trendDown.shift();
    }
  }

  function initDonut() {
    const canvas = document.getElementById("chart-fleet-donut");
    if (!canvas) return;
    const up = Number(root.dataset.initUp || 0);
    const down = Number(root.dataset.initDown || 0);
    const unknown = Number(root.dataset.initUnknown || 0);
    donutChart = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: ["Working fine", "Needs attention", "Still checking"],
        datasets: [
          {
            data: [up, down, unknown],
            backgroundColor: [COLORS.up, COLORS.down, COLORS.pending],
            borderWidth: 0,
            hoverOffset: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { usePointStyle: true, pointStyle: "circle", padding: 14 },
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw}`,
            },
          },
        },
        animation: { animateRotate: true, duration: 700 },
      },
    });
  }

  function initBars(projects) {
    const canvas = document.getElementById("chart-project-bars");
    if (!canvas) return;
    const labels = (projects || []).map((p) => p.name);
    const ups = (projects || []).map((p) => (p.health || {}).up || 0);
    const downs = (projects || []).map((p) => (p.health || {}).down || 0);
    barChart = new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Working",
            data: ups,
            backgroundColor: COLORS.up,
            borderRadius: 6,
            barPercentage: 0.7,
          },
          {
            label: "Problems",
            data: downs,
            backgroundColor: COLORS.down,
            borderRadius: 6,
            barPercentage: 0.7,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          x: {
            stacked: false,
            grid: { display: false },
            ticks: { maxRotation: 0, autoSkip: true, font: { size: 11 } },
          },
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, precision: 0 },
            grid: { color: COLORS.grid },
          },
        },
        plugins: {
          legend: {
            position: "bottom",
            labels: { usePointStyle: true, pointStyle: "circle", padding: 14 },
          },
        },
        animation: { duration: 650 },
      },
    });
  }

  function initTrend(down) {
    const canvas = document.getElementById("chart-down-trend");
    if (!canvas) return;
    pushTrend(down);
    trendChart = new Chart(canvas, {
      type: "line",
      data: {
        labels: trendLabels,
        datasets: [
          {
            label: "Problems",
            data: trendDown,
            borderColor: COLORS.down,
            backgroundColor: "rgba(194, 65, 12, 0.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointHoverRadius: 5,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxTicksLimit: 6, font: { size: 10 } },
          },
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, precision: 0 },
            grid: { color: COLORS.grid },
          },
        },
        plugins: { legend: { display: false } },
        animation: { duration: 500 },
      },
    });
  }

  function initMiniDonuts() {
    document.querySelectorAll("[data-mini-donut]").forEach((canvas) => {
      const card = canvas.closest("[data-project-id]");
      const id = card?.getAttribute("data-project-id");
      if (!id) return;
      const up = Number(canvas.dataset.up || 0);
      const down = Number(canvas.dataset.down || 0);
      const unknown = Number(canvas.dataset.unknown || 0);
      const total = up + down + unknown;
      const chart = new Chart(canvas, {
        type: "doughnut",
        data: {
          labels: ["Working fine", "Needs attention", "Still checking"],
          datasets: [
            {
              data: total ? [up, down, unknown] : [0, 0, 1],
              backgroundColor: total
                ? [COLORS.up, COLORS.down, COLORS.pending]
                : ["#d7e2ef", "#d7e2ef", "#d7e2ef"],
              borderWidth: 0,
            },
          ],
        },
        options: {
          responsive: false,
          cutout: "70%",
          plugins: { legend: { display: false }, tooltip: { enabled: true } },
          animation: { duration: 400 },
        },
      });
      miniCharts.set(id, chart);
    });
  }

  function updateCharts(payload) {
    const fleet = payload.fleet || {};
    const projects = payload.projects || [];
    const up = fleet.up || 0;
    const down = fleet.down || 0;
    const unknown = fleet.unknown || 0;

    if (donutChart) {
      donutChart.data.datasets[0].data = [up, down, unknown];
      donutChart.update("active");
    }

    if (barChart) {
      barChart.data.labels = projects.map((p) => p.name);
      barChart.data.datasets[0].data = projects.map((p) => (p.health || {}).up || 0);
      barChart.data.datasets[1].data = projects.map((p) => (p.health || {}).down || 0);
      barChart.update("active");
    }

    if (trendChart) {
      pushTrend(down);
      trendChart.data.labels = [...trendLabels];
      trendChart.data.datasets[0].data = [...trendDown];
      trendChart.update("none");
    }

    projects.forEach((p) => {
      const chart = miniCharts.get(p.id);
      if (!chart) return;
      const h = p.health || {};
      const u = h.up || 0;
      const d = h.down || 0;
      const unk = h.unknown || 0;
      const total = u + d + unk;
      chart.data.datasets[0].data = total ? [u, d, unk] : [0, 0, 1];
      chart.data.datasets[0].backgroundColor = total
        ? [COLORS.up, COLORS.down, COLORS.pending]
        : ["#d7e2ef", "#d7e2ef", "#d7e2ef"];
      chart.update("none");
    });
  }

  // Expose for app.js refresh loop
  window.PingCharts = { update: updateCharts };

  async function bootstrap() {
    try {
      const res = await fetch(window.API_URLS.status, { headers: { Accept: "application/json" } });
      const data = res.ok ? await res.json() : { fleet: {}, projects: [] };
      initDonut();
      initBars(data.projects || []);
      initTrend((data.fleet || {}).down || Number(root.dataset.initDown || 0));
      initMiniDonuts();
      updateCharts(data);
    } catch {
      initDonut();
      initBars([]);
      initTrend(Number(root.dataset.initDown || 0));
      initMiniDonuts();
    }
  }

  bootstrap();
})();
