// DOM elements
const loginSection = document.getElementById('login-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('login-form');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Check if user is already authenticated
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
});

// Check authentication status with server
async function checkAuthentication() {
    try {
        const response = await fetch('/admin/session');
        if (response.ok) {
            showDashboard();
            loadUrls();
        } else {
            showLogin();
        }
    } catch (error) {
        showLogin();
        console.error('Authentication check failed:', error);
    }
}

// Login form submission
loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    
    if (!username || !password) {
        showLoginError('Please enter both username and password');
        return;
    }
    
    try {
        const response = await fetch('/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showDashboard();
            loadUrls();
        } else {
            showLoginError(result.error);
        }
    } catch (error) {
        showLoginError('Login failed. Please try again.');
        console.error('Login error:', error);
    }
});

// Logout functionality
logoutBtn.addEventListener('click', async function() {
    try {
        await fetch('/admin/logout', {
            method: 'POST'
        });
        showLogin();
    } catch (error) {
        showLogin();
        console.error('Logout error:', error);
    }
});

// Tab switching
tabButtons.forEach(button => {
    button.addEventListener('click', function() {
        const tabId = this.getAttribute('data-tab');
        
        // Update active tab button
        tabButtons.forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
        
        // Show corresponding tab content
        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === `${tabId}-tab`) {
                content.classList.add('active');
                
                // Load data for the selected tab
                if (tabId === 'urls') {
                    loadUrls();
                } else if (tabId === 'users') {
                    loadUsers();
                } else if (tabId === 'analytics') {
                    loadAnalytics();
                }
            }
        });
    });
});

// Show dashboard
function showDashboard() {
    loginSection.style.display = 'none';
    dashboardSection.style.display = 'block';
}

// Show login form
function showLogin() {
    loginSection.style.display = 'block';
    dashboardSection.style.display = 'none';
}

// Show login error
function showLoginError(message) {
    loginError.textContent = message;
    loginError.style.display = 'block';
}

// Hide login error
function hideLoginError() {
    loginError.style.display = 'none';
}

// Load URLs for management
async function loadUrls() {
    try {
        const response = await fetch('/admin/urls');
        const urls = await response.json();
        
        if (response.ok) {
            populateUrlsTable(urls);
        } else {
            console.error('Failed to load URLs:', urls.error);
        }
    } catch (error) {
        console.error('Error loading URLs:', error);
    }
}

// Populate URLs table
function populateUrlsTable(urls) {
    const tbody = document.querySelector('#urls-table tbody');
    tbody.innerHTML = '';
    
    urls.forEach(url => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${url.short_code}</td>
            <td>${url.original_url}</td>
            <td>${url.clicks}</td>
            <td>${new Date(url.created_at).toLocaleDateString()}</td>
            <td>${url.is_active ? 'Active' : 'Inactive'}</td>
            <td>
                <button class="toggle-btn" data-id="${url.id}" data-status="${url.is_active}">
                    ${url.is_active ? 'Disable' : 'Enable'}
                </button>
                <button class="delete-btn" data-id="${url.id}">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // Add event listeners to action buttons
    document.querySelectorAll('.toggle-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const status = this.getAttribute('data-status') === '1';
            toggleUrl(id, !status);
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            deleteUrl(id);
        });
    });
}

// Toggle URL status
async function toggleUrl(id, newStatus) {
    try {
        const response = await fetch(`/admin/urls/${id}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_active: newStatus })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadUrls(); // Refresh the table
        } else {
            console.error('Failed to toggle URL:', result.error);
        }
    } catch (error) {
        console.error('Error toggling URL:', error);
    }
}

// Delete URL
async function deleteUrl(id) {
    if (!confirm('Are you sure you want to delete this URL?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/urls/${id}/delete`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadUrls(); // Refresh the table
        } else {
            console.error('Failed to delete URL:', result.error);
        }
    } catch (error) {
        console.error('Error deleting URL:', error);
    }
}

// Load users for management
async function loadUsers() {
    try {
        const response = await fetch('/admin/users');
        const users = await response.json();
        
        if (response.ok) {
            populateUsersTable(users);
        } else {
            console.error('Failed to load users:', users.error);
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Populate users table
function populateUsersTable(users) {
    const tbody = document.querySelector('#users-table tbody');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.username}</td>
            <td>${user.email || 'N/A'}</td>
            <td>${new Date(user.created_at).toLocaleDateString()}</td>
            <td>${user.is_admin ? 'Admin' : 'User'}</td>
            <td>
                <button class="edit-btn" data-id="${user.id}">Edit</button>
                <button class="delete-btn" data-id="${user.id}">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Load analytics data
async function loadAnalytics() {
    try {
        // For demo purposes, we'll generate some sample data
        // In a real application, this would come from the server
        
        // Sample data
        const sampleData = {
            total_urls: 125,
            total_clicks: 3420,
            active_urls: 98
        };
        
        // Update stats
        document.getElementById('total-urls').textContent = sampleData.total_urls;
        document.getElementById('total-clicks').textContent = sampleData.total_clicks;
        document.getElementById('active-urls').textContent = sampleData.active_urls;
        
        // Initialize chart
        initClicksChart();
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// Initialize clicks chart
function initClicksChart() {
    const ctx = document.getElementById('clicks-chart').getContext('2d');
    
    // Sample chart data
    const chartData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
            label: 'URL Clicks',
            data: [120, 190, 150, 220, 180, 250, 300, 280, 200, 230, 270, 310],
            backgroundColor: 'rgba(102, 126, 234, 0.6)',
            borderColor: 'rgba(102, 126, 234, 1)',
            borderWidth: 1
        }]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Monthly Click Statistics'
                }
            }
        }
    });
}