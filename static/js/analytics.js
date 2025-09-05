// DOM elements
const totalUrlsElement = document.getElementById('total-urls');
const totalClicksElement = document.getElementById('total-clicks');
const activeUrlsElement = document.getElementById('active-urls');
const topCountryElement = document.getElementById('top-country');
const recentActivityTable = document.querySelector('#recent-activity tbody');

// Chart instances
let clicksOverTimeChart;
let geographicDistributionChart;
let topUrlsChart;
let deviceTypesChart;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

// Load all dashboard data
async function loadDashboardData() {
    try {
        // Load statistics
        await loadStatistics();
        
        // Load chart data and initialize charts
        await loadChartData();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Load statistics data
async function loadStatistics() {
    try {
        const response = await fetch('/admin/dashboard/stats');
        const stats = await response.json();
        
        if (response.ok) {
            totalUrlsElement.textContent = stats.total_urls;
            totalClicksElement.textContent = stats.total_clicks;
            activeUrlsElement.textContent = stats.active_urls;
            topCountryElement.textContent = stats.top_country || 'Unknown';
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Load all chart data
async function loadChartData() {
    try {
        // Initialize all charts with empty data
        initClicksOverTimeChart();
        initGeographicDistributionChart();
        initTopUrlsChart();
        initDeviceTypesChart();
        
        // Load clicks over time data
        await loadClicksOverTimeData();
        
        // Load geographic distribution data
        await loadGeographicDistributionData();
        
        // Load top URLs data
        await loadTopUrlsData();
        
        // Load device types data
        await loadDeviceTypesData();
        
        // Load recent activity
        loadRecentActivity();
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

// Load clicks over time data
async function loadClicksOverTimeData() {
    try {
        const response = await fetch('/admin/dashboard/chart/clicks-over-time');
        const data = await response.json();
        
        if (response.ok) {
            updateClicksOverTimeChart(data);
        }
    } catch (error) {
        console.error('Error loading clicks over time data:', error);
    }
}

// Load geographic distribution data
async function loadGeographicDistributionData() {
    try {
        const response = await fetch('/admin/dashboard/chart/geographic-distribution');
        const data = await response.json();
        
        if (response.ok) {
            updateGeographicDistributionChart(data);
        }
    } catch (error) {
        console.error('Error loading geographic distribution data:', error);
    }
}

// Load top URLs data
async function loadTopUrlsData() {
    try {
        const response = await fetch('/admin/dashboard/chart/top-urls');
        const data = await response.json();
        
        if (response.ok) {
            updateTopUrlsChart(data);
        }
    } catch (error) {
        console.error('Error loading top URLs data:', error);
    }
}

// Load device types data
async function loadDeviceTypesData() {
    try {
        const response = await fetch('/admin/dashboard/chart/device-types');
        const data = await response.json();
        
        if (response.ok) {
            updateDeviceTypesChart(data);
        }
    } catch (error) {
        console.error('Error loading device types data:', error);
    }
}

// Initialize clicks over time chart
function initClicksOverTimeChart() {
    const ctx = document.getElementById('clicks-over-time').getContext('2d');
    
    // Initialize with empty data
    const data = {
        labels: [],
        datasets: [{
            label: 'Clicks',
            data: [],
            backgroundColor: 'rgba(102, 126, 234, 0.6)',
            borderColor: 'rgba(102, 126, 234, 1)',
            borderWidth: 1
        }]
    };
    
    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    };
    
    clicksOverTimeChart = new Chart(ctx, config);
}

// Update clicks over time chart with real data
function updateClicksOverTimeChart(chartData) {
    clicksOverTimeChart.data.labels = chartData.labels;
    clicksOverTimeChart.data.datasets[0].data = chartData.clicks;
    clicksOverTimeChart.update();
}

// Initialize geographic distribution chart
function initGeographicDistributionChart() {
    const ctx = document.getElementById('geographic-distribution').getContext('2d');
    
    // Initialize with empty data
    const data = {
        labels: [],
        datasets: [{
            label: 'Clicks by Country',
            data: [],
            backgroundColor: [
                'rgba(102, 126, 234, 0.6)',
                'rgba(118, 75, 162, 0.6)',
                'rgba(255, 99, 132, 0.6)',
                'rgba(54, 162, 235, 0.6)',
                'rgba(255, 206, 86, 0.6)',
                'rgba(75, 192, 192, 0.6)',
                'rgba(153, 102, 255, 0.6)'
            ],
            borderColor: [
                'rgba(102, 126, 234, 1)',
                'rgba(118, 75, 162, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)'
            ],
            borderWidth: 1
        }]
    };
    
    const config = {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    };
    
    geographicDistributionChart = new Chart(ctx, config);
}

// Update geographic distribution chart with real data
function updateGeographicDistributionChart(chartData) {
    geographicDistributionChart.data.labels = chartData.labels;
    geographicDistributionChart.data.datasets[0].data = chartData.clicks;
    geographicDistributionChart.update();
}

// Initialize top URLs chart
function initTopUrlsChart() {
    const ctx = document.getElementById('top-urls').getContext('2d');
    
    // Initialize with empty data
    const data = {
        labels: [],
        datasets: [{
            label: 'Click Count',
            data: [],
            backgroundColor: 'rgba(118, 75, 162, 0.6)',
            borderColor: 'rgba(118, 75, 162, 1)',
            borderWidth: 1
        }]
    };
    
    const config = {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    };
    
    topUrlsChart = new Chart(ctx, config);
}

// Update top URLs chart with real data
function updateTopUrlsChart(chartData) {
    topUrlsChart.data.labels = chartData.labels;
    topUrlsChart.data.datasets[0].data = chartData.clicks;
    topUrlsChart.update();
}

// Initialize device types chart
function initDeviceTypesChart() {
    const ctx = document.getElementById('device-types').getContext('2d');
    
    // Initialize with empty data
    const data = {
        labels: [],
        datasets: [{
            label: 'Clicks by Device',
            data: [],
            backgroundColor: [
                'rgba(54, 162, 235, 0.6)',
                'rgba(255, 99, 132, 0.6)',
                'rgba(255, 206, 86, 0.6)'
            ],
            borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 206, 86, 1)'
            ],
            borderWidth: 1
        }]
    };
    
    const config = {
        type: 'pie',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    };
    
    deviceTypesChart = new Chart(ctx, config);
}

// Update device types chart with real data
function updateDeviceTypesChart(chartData) {
    deviceTypesChart.data.labels = chartData.labels;
    deviceTypesChart.data.datasets[0].data = chartData.clicks;
    deviceTypesChart.update();
}

// Load recent activity
async function loadRecentActivity() {
    try {
        const response = await fetch('/admin/dashboard/recent');
        const activities = await response.json();
        
        if (response.ok) {
            populateRecentActivity(activities);
        }
    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

// Populate recent activity table
function populateRecentActivity(activities) {
    recentActivityTable.innerHTML = '';
    
    activities.forEach(activity => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${activity.short_code}</td>
            <td>${activity.original_url}</td>
            <td>${activity.ip_address}</td>
            <td>${activity.country || 'Unknown'}</td>
            <td>${new Date(activity.timestamp).toLocaleString()}</td>
        `;
        recentActivityTable.appendChild(row);
    });
}