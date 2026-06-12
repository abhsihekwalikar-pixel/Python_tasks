// ==========================================
// AUTHENTICATION FUNCTIONS
// ==========================================

// Register Function
async function register(email, password, name, role, phone = null) {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.endpoints.register}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password,
                name: name,
                role: role,
                phone: phone
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Registration successful! Please login.', 'success');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1500);
        } else {
            showMessage(data.detail || 'Registration failed', 'error');
        }

        return data;
    } catch (error) {
        console.error('Register error:', error);
        showMessage('Connection error. Make sure the backend is running.', 'error');
    }
}

// Login Function - UPDATED WITH ROLE-BASED REDIRECTION
async function login(email, password) {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.endpoints.login}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Save token and role to localStorage
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('role', data.role);
            
            // Decode the JWT token to extract user_id
            // JWT tokens have 3 parts separated by dots: header.payload.signature
            const tokenParts = data.access_token.split('.');
            const payload = JSON.parse(atob(tokenParts[1])); // Decode the middle part (payload)
            localStorage.setItem('userId', payload.user_id); // Save user_id for later use
            
            showMessage('Login successful! Redirecting...', 'success');
            
            // Redirect to the correct dashboard based on user role
            setTimeout(() => {
                if (data.role === 'admin') {
                    window.location.href = 'admin-dashboard.html'; // Admins go to admin dashboard
                } else {
                    window.location.href = 'user-dashboard.html'; // Regular users go to user dashboard
                }
            }, 1000);
        } else {
            showMessage(data.detail || 'Login failed', 'error');
        }

        return data;
    } catch (error) {
        console.error('Login error:', error);
        showMessage('Connection error. Make sure the backend is running.', 'error');
    }
}

// ==========================================
// HELPER FUNCTIONS
// ==========================================

// Show message helper (for success/error alerts)
function showMessage(message, type = 'error') {
    // Remove existing messages
    const existingMsg = document.querySelector('.alert');
    if (existingMsg) {
        existingMsg.remove();
    }

    // Create new message element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    // Insert at the top of the form or container
    const container = document.querySelector('.auth-container') || document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Check if user is logged in
function isLoggedIn() {
    return localStorage.getItem('token') !== null;
}

// Get current user role
function getUserRole() {
    return localStorage.getItem('role');
}

// Get current user ID
function getUserId() {
    return localStorage.getItem('userId');
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('userId');
    window.location.href = 'login.html';
}

// Protect routes (check authentication)
function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Helper to get auth headers for API requests
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}