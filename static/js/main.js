// Enhanced Main JavaScript file for Disha LMS with Animations & Feedback

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Disha LMS initialized with animations');

    // Initialize all features
    initAnimations();
    initThemeToggle();
    initOfflineDetection();
    initRippleEffect();
    initToastSystem();
    initScrollReveal();
    initPageTransitions();
    initTableInteractions();
    initFormFeedback();
    autoHideAlerts();
});

// ==================== ANIMATIONS ====================

// Initialize page animations
function initAnimations() {
    // Add page-enter animation to main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('page-enter');
    }

    // Stagger animation for cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        if (index < 4) {
            card.classList.add(`stagger-${index + 1}`);
        }
    });

    // Add hover-lift to interactive elements
    const liftElements = document.querySelectorAll('.card-hover, .btn');
    liftElements.forEach(el => {
        el.classList.add('hover-lift');
    });
}

// Scroll reveal animation
function initScrollReveal() {
    const reveals = document.querySelectorAll('.reveal');

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.1 });

    reveals.forEach(reveal => revealObserver.observe(reveal));
}

// Page transition animations
function initPageTransitions() {
    // Smooth fade-in for page loads
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.3s ease-in';
        document.body.style.opacity = '1';
    }, 10);
}

// ==================== RIPPLE EFFECT ====================

function initRippleEffect() {
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary, .btn-success');

    buttons.forEach(button => {
        button.classList.add('btn-ripple');

        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');

            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });
}

// ==================== TOAST NOTIFICATIONS ====================

let toastContainer = null;

function initToastSystem() {
    // Create toast container
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed bottom-4 right-4 z-50 space-y-3';
    document.body.appendChild(toastContainer);
}

function showToast(message, type = 'info', duration = 5000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} flex items-start max-w-sm shadow-large`;

    const icons = {
        success: '<svg class="w-5 h-5 text-success-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        error: '<svg class="w-5 h-5 text-danger-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        warning: '<svg class="w-5 h-5 text-warning-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
        info: '<svg class="w-5 h-5 text-primary-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };

    toast.innerHTML = `
        ${icons[type] || icons.info}
        <div class="ml-3 flex-1">
            <p class="text-sm font-medium text-gray-900">${message}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="ml-3 flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    `;

    toastContainer.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        toast.style.transition = 'all 0.3s ease-out';
        toast.style.transform = 'translateX(400px)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ==================== TABLE INTERACTIONS ====================

function initTableInteractions() {
    const tableRows = document.querySelectorAll('tbody tr');

    tableRows.forEach(row => {
        row.classList.add('table-row-interactive');

        // Add click animation
        row.addEventListener('click', function(e) {
            // Don't animate if clicking on buttons
            if (e.target.closest('a, button')) return;

            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 200);
        });
    });
}

// ==================== FORM FEEDBACK ====================

function initFormFeedback() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        // Add loading state on submit
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <svg class="animate-spin h-5 w-5 mr-2 inline" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                `;
            }
        });

        // Real-time validation feedback
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.hasAttribute('required') && !this.value.trim()) {
                    this.classList.add('border-danger-500', 'error-shake');
                    setTimeout(() => this.classList.remove('error-shake'), 500);
                } else {
                    this.classList.remove('border-danger-500');
                    if (this.value.trim()) {
                        this.classList.add('success-shake');
                        setTimeout(() => this.classList.remove('success-shake'), 500);
                    }
                }
            });
        });
    });
}

// ==================== LOADING OVERLAY ====================

function showLoading(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="bg-white rounded-lg p-8 text-center">
            <div class="loading-spinner mx-auto mb-4"></div>
            <p class="text-gray-700 font-medium">${message}</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 300);
    }
}

// ==================== PROGRESS BAR ====================

function showProgress(percentage) {
    let progressBar = document.getElementById('progress-bar');

    if (!progressBar) {
        progressBar = document.createElement('div');
        progressBar.id = 'progress-bar';
        progressBar.className = 'fixed top-0 left-0 right-0 z-50 progress-bar';
        progressBar.innerHTML = '<div class="progress-fill" style="width: 0%"></div>';
        document.body.appendChild(progressBar);
    }

    const fill = progressBar.querySelector('.progress-fill');
    fill.style.width = percentage + '%';

    if (percentage >= 100) {
        setTimeout(() => progressBar.remove(), 500);
    }
}

// ==================== THEME TOGGLE ====================

function initThemeToggle() {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    showToast(`Switched to ${newTheme} mode`, 'success', 2000);
}

// ==================== OFFLINE DETECTION ====================

function initOfflineDetection() {
    window.addEventListener('online', () => {
        showToast('You are back online', 'success', 3000);
    });

    window.addEventListener('offline', () => {
        showToast('You are offline. Changes will be synced when you reconnect.', 'warning', 5000);
    });
}

// ==================== NOTIFICATIONS ====================

function showNotification(message, type = 'info') {
    showToast(message, type);
}

// Auto-hide alerts
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Add bounce animation
        alert.classList.add('success-shake');

        setTimeout(() => {
            alert.style.transition = 'all 0.5s ease-out';
            alert.style.transform = 'translateX(400px)';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
}

// ==================== UTILITY FUNCTIONS ====================

// Confirm dialog with animation
function confirmAction(message, onConfirm) {
    const confirmed = confirm(message);
    if (confirmed && onConfirm) {
        showLoading('Processing...');
        onConfirm();
    }
}

// Copy to clipboard with feedback
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success', 2000);
    }).catch(() => {
        showToast('Failed to copy', 'error', 2000);
    });
}

// Smooth scroll to element
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ==================== EXPORT FUNCTIONS ====================

window.DishaLMS = {
    // Theme
    toggleTheme,

    // Notifications
    showNotification,
    showToast,

    // Loading
    showLoading,
    hideLoading,
    showProgress,

    // Utilities
    confirmAction,
    copyToClipboard,
    scrollToElement
};

// Log initialization
console.log('✨ Disha LMS enhanced with animations and interactive feedback');
