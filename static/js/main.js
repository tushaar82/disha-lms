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
    
    // Initialize sidebar toggle
    initSidebarToggle();
    
    // Initialize responsive utilities
    initResponsiveUtilities();
    
    // Check for print parameter and trigger print dialog
    checkPrintParameter();
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

// Auto-hide alerts (only for success/info messages, not warnings/errors/insights)
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert, .info-card');
    alerts.forEach(alert => {
        // Don't auto-hide warning, error, insight, or deep analysis cards
        if (alert.classList.contains('info-card-warning') || 
            alert.classList.contains('info-card-error') ||
            alert.classList.contains('alert-warning') ||
            alert.classList.contains('alert-error') ||
            alert.hasAttribute('data-persist') ||
            alert.hasAttribute('data-insight') ||
            alert.closest('.insights-section') ||
            alert.closest('.deep-insights') ||
            alert.closest('.recommendations') ||
            alert.closest('.performance-insights') ||
            alert.closest('.key-insights') ||
            alert.id && (alert.id.includes('insight') || alert.id.includes('recommendation'))) {
            return; // Skip auto-hiding these - keep them forever
        }
        
        // Only auto-hide success and info messages (like form submission confirmations)
        if (alert.classList.contains('info-card-success') || 
            alert.classList.contains('info-card-info') ||
            alert.classList.contains('alert-success') ||
            alert.classList.contains('alert-info')) {
            setTimeout(() => {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.5s';
                setTimeout(() => alert.remove(), 500);
            }, 5000);
        }
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

// Sidebar toggle functionality
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    
    if (!sidebarToggle || !sidebar) return;
    
    // Toggle sidebar on mobile
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('mobile-hidden');
        if (sidebarOverlay) {
            sidebarOverlay.classList.toggle('hidden');
        }
    });
    
    // Close sidebar when clicking overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.add('mobile-hidden');
            sidebarOverlay.classList.add('hidden');
        });
    }
    
    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !sidebar.classList.contains('mobile-hidden')) {
            sidebar.classList.add('mobile-hidden');
            if (sidebarOverlay) {
                sidebarOverlay.classList.add('hidden');
            }
        }
    });
}

// Responsive utilities
function initResponsiveUtilities() {
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            handleResize();
        }, 250);
    });
}

function handleResize() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    
    // Auto-hide sidebar on mobile, show on desktop
    if (window.innerWidth >= 1024) {
        if (sidebar) sidebar.classList.remove('mobile-hidden');
        if (sidebarOverlay) sidebarOverlay.classList.add('hidden');
    } else {
        if (sidebar) sidebar.classList.add('mobile-hidden');
        if (sidebarOverlay) sidebarOverlay.classList.add('hidden');
    }
}

function isMobile() {
    return window.innerWidth < 768;
}

function isTablet() {
    return window.innerWidth >= 768 && window.innerWidth < 1024;
}

// Enhanced notification with icons and colors
function showNotificationEnhanced(message, type = 'info', duration = 5000) {
    const icons = {
        success: '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
        error: '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
        warning: '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>',
        info: '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'
    };
    
    const colors = {
        success: 'bg-success-500',
        error: 'bg-error-500',
        warning: 'bg-warning-500',
        info: 'bg-info-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 ${colors[type]} text-white px-4 py-3 rounded-lg shadow-elevated flex items-center gap-3 animate-slide-in-right max-w-md`;
    notification.innerHTML = `
        ${icons[type]}
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-auto">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    if (duration > 0) {
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}

// Enhanced form validation with visual feedback
function validateFormEnhanced(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    let firstInvalidInput = null;
    
    inputs.forEach(input => {
        const value = input.value.trim();
        const parent = input.parentElement;
        
        // Remove existing error messages
        const existingError = parent.querySelector('.form-error');
        if (existingError) existingError.remove();
        
        if (!value) {
            input.classList.add('border-error-500');
            input.classList.remove('border-gray-300');
            
            // Add error message
            const errorMsg = document.createElement('p');
            errorMsg.className = 'form-error';
            errorMsg.textContent = 'This field is required';
            parent.appendChild(errorMsg);
            
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = input;
        } else {
            input.classList.remove('border-error-500');
            input.classList.add('border-gray-300');
        }
    });
    
    // Focus on first invalid input
    if (firstInvalidInput) {
        firstInvalidInput.focus();
        firstInvalidInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    return isValid;
}

// Loading overlay
function showLoading() {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
    overlay.innerHTML = `
        <div class="bg-white rounded-lg p-6 flex flex-col items-center gap-4">
            <div class="spinner w-12 h-12 border-4 border-primary-500"></div>
            <p class="text-gray-700 font-medium">Loading...</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
}

// Confirm delete dialog
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Auto-save form data to localStorage
function autoSaveForm(formId, key) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    // Load saved data
    const savedData = localStorage.getItem(key);
    if (savedData) {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach(name => {
            const input = form.querySelector(`[name="${name}"]`);
            if (input) input.value = data[name];
        });
    }
    
    // Save on input
    form.addEventListener('input', function() {
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });
        localStorage.setItem(key, JSON.stringify(data));
    });
    
    // Clear on submit
    form.addEventListener('submit', function() {
        localStorage.removeItem(key);
    });
}

// Check for print parameter in URL and trigger print dialog
function checkPrintParameter() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('print') === 'true') {
        console.log('Print parameter detected, triggering print dialog...');
        
        // Hide elements that shouldn't be printed
        hidePrintExcludedElements();
        
        // Wait for page to fully load (including charts/images)
        setTimeout(function() {
            window.print();
            
            // After printing, remove the print parameter from URL
            const url = new URL(window.location);
            url.searchParams.delete('print');
            window.history.replaceState({}, '', url);
            
            // Show hidden elements again
            showPrintExcludedElements();
        }, 1000); // 1 second delay to ensure everything is loaded
    }
}

// Hide elements that shouldn't appear in print
function hidePrintExcludedElements() {
    // Add print-hidden class to elements
    const elementsToHide = document.querySelectorAll('.no-print, .sidebar, .navbar, .btn, button, .alert');
    elementsToHide.forEach(el => {
        el.classList.add('print-hidden-temp');
        el.style.display = 'none';
    });
}

// Show elements again after print
function showPrintExcludedElements() {
    const elements = document.querySelectorAll('.print-hidden-temp');
    elements.forEach(el => {
        el.classList.remove('print-hidden-temp');
        el.style.display = '';
    });
}

// Export functions for use in other scripts
window.DishaLMS = {
    toggleTheme,
    showNotification,
    showNotificationEnhanced,
    validateForm,
    validateFormEnhanced,
    setLoadingState,
    showLoading,
    hideLoading,
    confirmDelete,
    autoSaveForm,
    isMobile,
    isTablet,
    checkPrintParameter
};
