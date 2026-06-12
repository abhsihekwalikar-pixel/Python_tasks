// API Configuration
const API_CONFIG = {
    BASE_URL: 'http://127.0.0.1:8000',
    endpoints: {
        register: '/register',
        login: '/login',
        properties: '/properties',
        users: '/users',
        favorites: '/favorites',
        inquiries: '/inquiries',
        reviews: '/reviews'
    }
};

// Helper to get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

// Check if user is logged in
function isLoggedIn() {
    return localStorage.getItem('token') !== null;
}

// Get current user role
function getUserRole() {
    return localStorage.getItem('role');
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = 'login.html';
}