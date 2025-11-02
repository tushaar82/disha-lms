// Main JavaScript file for Disha LMS

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Disha LMS initialized');
    
    // Initialize theme toggle
    initThemeToggle();
    
    // Initialize offline detection
    initOfflineDetection();
    
    // Auto-hide alerts after 5 seconds
    autoHideAlerts();
});

// Theme toggle functionality
function initThemeToggle() {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Offline detection
function initOfflineDetection() {
    window.addEventListener('online', () => {
        showNotification('You are back online', 'success');
    });
    
    window.addEventListener('offline', () => {
        showNotification('You are offline. Changes will be synced when you reconnect.', 'warning');
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} shadow-lg fixed top-4 right-4 z-50 max-w-md`;
    alertDiv.innerHTML = `
        <div>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Auto-hide alerts
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
}

// Form validation helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('input-error');
            isValid = false;
        } else {
            input.classList.remove('input-error');
        }
    });
    
    return isValid;
}

// Loading state helper
function setLoadingState(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner"></span> Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
    }
}

// Export functions for use in other scripts
window.DishaLMS = {
    toggleTheme,
    showNotification,
    validateForm,
    setLoadingState
};
