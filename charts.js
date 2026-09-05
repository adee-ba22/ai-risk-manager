/**
 * AI Risk Manager - Chart.js Helper Module
 */

let severityChart = null;
let statusChart = null;

function renderSeverityDistributionChart(distData) {
    const ctx = document.getElementById('chart-severity-dist');
    if (!ctx) return;

    const dataValues = [
        distData.Critical || 0,
        distData.High || 0,
        distData.Medium || 0,
        distData.Low || 0
    ];

    if (severityChart) {
        severityChart.destroy();
    }

    severityChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Critical', 'High', 'Medium', 'Low'],
            datasets: [{
                data: dataValues,
                backgroundColor: [
                    '#ef4444', // Red
                    '#f97316', // Orange
                    '#eab308', // Yellow
                    '#10b981'  // Green
                ],
                borderWidth: 2,
                borderColor: '#0f172a'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#94a3b8',
                        font: { size: 11, weight: '600' },
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#ffffff',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            cutout: '70%'
        }
    });
}

function renderStatusDistributionChart(statusData) {
    const ctx = document.getElementById('chart-status-dist');
    if (!ctx) return;

    const dataValues = [
        statusData.Open || 0,
        statusData['In Progress'] || 0,
        statusData.Mitigated || 0
    ];

    if (statusChart) {
        statusChart.destroy();
    }

    statusChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Open', 'In Progress', 'Mitigated'],
            datasets: [{
                label: 'Risk Count',
                data: dataValues,
                backgroundColor: [
                    '#f59e0b', // Amber
                    '#06b6d4', // Cyan
                    '#10b981'  // Emerald
                ],
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#ffffff',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', font: { weight: '600' } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', stepSize: 1, precision: 0 }
                }
            }
        }
    });
}
