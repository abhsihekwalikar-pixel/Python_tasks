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

// Login Function
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
            
            showMessage('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
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

// Show message helper
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

// Protect routes (check authentication)
function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}