// Function to send the property data to the backend
async function createProperty(propertyData) {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.endpoints.properties}`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(propertyData)
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Property listed successfully!', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        } else {
            const errorMsg = data.detail || 'Failed to add property';
            showMessage(errorMsg, 'error');
        }

    } catch (error) {
        console.error('Create property error:', error);
        showMessage('Connection error. Is the backend running?', 'error');
    }
}