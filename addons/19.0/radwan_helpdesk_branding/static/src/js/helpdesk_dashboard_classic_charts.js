// Keep Helpdesk dashboard charts calm and classic without changing data routes.
(function () {
    "use strict";

    var palette = {
        text: "#25313d",
        muted: "#6b7785",
        grid: "rgba(37, 49, 61, 0.09)",
        blue: "#4f83b6",
        teal: "#4fa8a3",
        green: "#4f9d69",
        amber: "#c99a3b",
        red: "#bf5b5b",
        slate: "#7a8793",
    };

    function destroyExistingChart(Chart, canvas) {
        if (Chart && Chart.getChart) {
            var existing = Chart.getChart(canvas);
            if (existing) {
                existing.destroy();
            }
        }
    }

    function legendOptions(display) {
        return {
            display: display !== false,
            position: "top",
            labels: {
                color: palette.muted,
                boxWidth: 12,
                boxHeight: 12,
                padding: 14,
            },
        };
    }

    function basePlugins(displayLegend) {
        return {
            legend: legendOptions(displayLegend),
            tooltip: {
                backgroundColor: "#202a34",
                titleColor: "#ffffff",
                bodyColor: "#ffffff",
                padding: 10,
                displayColors: true,
            },
        };
    }

    function cartesianScales() {
        return {
            x: {
                grid: {
                    display: false,
                    drawBorder: false,
                },
                ticks: {
                    color: palette.muted,
                },
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: palette.grid,
                    drawBorder: false,
                },
                ticks: {
                    color: palette.muted,
                    precision: 0,
                },
            },
        };
    }

    function patchDashboard() {
        var dashboard = window.HelpdeskDashboard;
        if (!dashboard || dashboard.__radwanClassicCharts) {
            return Boolean(dashboard && dashboard.__radwanClassicCharts);
        }

        dashboard.__radwanClassicCharts = true;

        dashboard.renderTicketTrendChart = function (data) {
            var ctx = document.getElementById("chart-ticket-trend");
            if (!ctx || !this.Chart) {
                return;
            }
            destroyExistingChart(this.Chart, ctx);
            new this.Chart(ctx, {
                type: "line",
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: "Tickets Created",
                        data: data.values || [],
                        borderColor: palette.teal,
                        backgroundColor: "rgba(79, 168, 163, 0.12)",
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 4,
                        tension: 0.25,
                        fill: true,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: basePlugins(true),
                    scales: cartesianScales(),
                },
            });
        };

        dashboard.renderStateDistributionChart = function (data) {
            var ctx = document.getElementById("chart-state-distribution");
            if (!ctx || !this.Chart) {
                return;
            }
            destroyExistingChart(this.Chart, ctx);
            new this.Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [palette.blue, palette.amber, palette.teal, palette.green, palette.slate, palette.red],
                        borderColor: "#ffffff",
                        borderWidth: 2,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "62%",
                    plugins: basePlugins(true),
                },
            });
        };

        dashboard.renderPriorityDistributionChart = function (data) {
            var ctx = document.getElementById("chart-priority-distribution");
            if (!ctx || !this.Chart) {
                return;
            }
            destroyExistingChart(this.Chart, ctx);
            new this.Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: "Tickets by Priority",
                        data: data.values || [],
                        backgroundColor: [palette.green, palette.amber, "#b87945", palette.red],
                        borderRadius: 4,
                        maxBarThickness: 44,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: basePlugins(false),
                    scales: cartesianScales(),
                },
            });
        };

        dashboard.renderSLAStatusChart = function (data) {
            var ctx = document.getElementById("chart-sla-status");
            if (!ctx || !this.Chart) {
                return;
            }
            destroyExistingChart(this.Chart, ctx);
            new this.Chart(ctx, {
                type: "pie",
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [palette.green, palette.amber, palette.red, palette.slate],
                        borderColor: "#ffffff",
                        borderWidth: 2,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: basePlugins(true),
                },
            });
        };

        return true;
    }

    function waitForDashboard(attempt) {
        if (patchDashboard() || attempt > 80) {
            return;
        }
        window.setTimeout(function () {
            waitForDashboard(attempt + 1);
        }, 250);
    }

    waitForDashboard(0);
})();
