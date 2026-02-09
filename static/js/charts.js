/**
 * Chart.js Configurations for DailyHands
 * Interactive charts replacing Matplotlib static PNGs
 */

// Global Chart.js defaults
Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
Chart.defaults.color = '#64748b';
Chart.defaults.plugins.legend.display = true;
Chart.defaults.plugins.legend.position = 'bottom';

/**
 * Contractor Dashboard - Requests Over Time (Line Chart)
 */
function renderContractorRequestsChart(canvasId, apiUrl) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Work Requests',
                        data: data.counts,
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#6366f1',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Requests Over Last 6 Months',
                            font: { size: 16, weight: 'bold' },
                            color: '#1e293b'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: { size: 14 },
                            bodyFont: { size: 13 },
                            callbacks: {
                                label: function(context) {
                                    return `Requests: ${context.parsed.y}`;
                                }
                            }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                font: { size: 12 }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: { size: 12 }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            document.getElementById(canvasId).parentElement.innerHTML = 
                '<div class="alert alert-danger">Failed to load chart data</div>';
        });
}

/**
 * Agency Dashboard - Earnings Overview (Bar Chart)
 */
function renderAgencyEarningsChart(canvasId, apiUrl) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Earned',
                            data: data.earned,
                            backgroundColor: 'rgba(16, 185, 129, 0.8)',
                            borderColor: '#10b981',
                            borderWidth: 2,
                            borderRadius: 6
                        },
                        {
                            label: 'Penalty Bonus',
                            data: data.penalty,
                            backgroundColor: 'rgba(245, 158, 11, 0.8)',
                            borderColor: '#f59e0b',
                            borderWidth: 2,
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Earnings Over Last 6 Months',
                            font: { size: 16, weight: 'bold' },
                            color: '#1e293b'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: { size: 14 },
                            bodyFont: { size: 13 },
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ₹${context.parsed.y.toLocaleString()}`;
                                }
                            }
                        },
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                padding: 15,
                                font: { size: 12 }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '₹' + value.toLocaleString();
                                },
                                font: { size: 12 }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: { size: 12 }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            document.getElementById(canvasId).parentElement.innerHTML = 
                '<div class="alert alert-danger">Failed to load chart data</div>';
        });
}

/**
 * Request Earnings - Worker Breakdown (Doughnut Chart)
 */
function renderWorkerEarningsChart(canvasId, apiUrl) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.names,
                    datasets: [{
                        label: 'Earnings',
                        data: data.earnings,
                        backgroundColor: [
                            'rgba(99, 102, 241, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(168, 85, 247, 0.8)',
                            'rgba(217, 70, 239, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(20, 184, 166, 0.8)',
                            'rgba(6, 182, 212, 0.8)'
                        ],
                        borderColor: '#fff',
                        borderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Worker-wise Earnings Distribution',
                            font: { size: 16, weight: 'bold' },
                            color: '#1e293b'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: { size: 14 },
                            bodyFont: { size: 13 },
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ₹${value.toLocaleString()} (${percentage}%)`;
                                }
                            }
                        },
                        legend: {
                            display: true,
                            position: 'right',
                            labels: {
                                padding: 15,
                                font: { size: 11 },
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    return data.labels.map((label, i) => ({
                                        text: `${label}: ₹${data.datasets[0].data[i].toLocaleString()}`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    }));
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            document.getElementById(canvasId).parentElement.innerHTML = 
                '<div class="alert alert-danger">Failed to load chart data</div>';
        });
}

/**
 * Worker Days Worked - Bar Chart
 */
function renderWorkerDaysChart(canvasId, apiUrl) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.names,
                    datasets: [{
                        label: 'Days Worked',
                        data: data.days,
                        backgroundColor: [
                            'rgba(99, 102, 241, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(168, 85, 247, 0.8)',
                            'rgba(217, 70, 239, 0.8)',
                            'rgba(236, 72, 153, 0.8)'
                        ],
                        borderColor: [
                            '#6366f1',
                            '#8b5cf6',
                            '#a855f7',
                            '#d946ef',
                            '#ec4899'
                        ],
                        borderWidth: 2,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Days Worked by Each Worker',
                            font: { size: 16, weight: 'bold' },
                            color: '#1e293b'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: { size: 14 },
                            bodyFont: { size: 13 },
                            callbacks: {
                                label: function(context) {
                                    return `Days: ${context.parsed.y}`;
                                }
                            }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                font: { size: 12 }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: { size: 11 }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            document.getElementById(canvasId).parentElement.innerHTML = 
                '<div class="alert alert-danger">Failed to load chart data</div>';
        });
}
