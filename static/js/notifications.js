/**
 * Notifications JavaScript Module
 * Handles notification polling, display, and interactions
 */

class NotificationManager {
    constructor() {
        this.pollInterval = 30000; // 30 seconds
        this.pollTimer = null;
        this.unreadCount = 0;
        this.init();
    }

    init() {
        // Start polling for notifications
        this.startPolling();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initial fetch
        this.fetchNotifications();
    }

    setupEventListeners() {
        // Mark notification as read on click
        document.addEventListener('click', (e) => {
            if (e.target.closest('.notification-item')) {
                const notificationId = e.target.closest('.notification-item').dataset.notificationId;
                if (notificationId) {
                    this.markAsRead(notificationId);
                }
            }
        });

        // Mark all as read
        const markAllBtn = document.getElementById('mark-all-read');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.markAllAsRead();
            });
        }
    }

    startPolling() {
        this.pollTimer = setInterval(() => {
            this.fetchNotifications();
        }, this.pollInterval);
    }

    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }

    async fetchNotifications() {
        try {
            const response = await fetch('/core/notifications/?format=json', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch notifications');
            }

            const data = await response.json();
            this.updateNotificationUI(data);
        } catch (error) {
            console.error('Error fetching notifications:', error);
        }
    }

    updateNotificationUI(data) {
        // Update badge count
        const badge = document.getElementById('notification-badge');
        if (badge) {
            this.unreadCount = data.unread_count || 0;
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }

        // Update notification list
        const list = document.getElementById('notification-list');
        if (list && data.notifications) {
            this.renderNotifications(list, data.notifications);
        }

        // Show toast for new notifications
        if (data.new_notifications && data.new_notifications.length > 0) {
            this.showNewNotificationToast(data.new_notifications[0]);
        }
    }

    renderNotifications(container, notifications) {
        if (notifications.length === 0) {
            container.innerHTML = '<div class="p-4 text-center text-gray-500">No notifications</div>';
            return;
        }

        container.innerHTML = notifications.slice(0, 5).map(notification => `
            <a href="${notification.action_url || '#'}" 
               class="notification-item block p-4 hover:bg-base-200 transition-colors ${notification.is_read ? 'opacity-60' : ''}"
               data-notification-id="${notification.id}">
                <div class="flex items-start gap-3">
                    <div class="flex-shrink-0">
                        ${this.getNotificationIcon(notification.notification_type)}
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="font-medium text-sm">${notification.title}</p>
                        <p class="text-xs text-gray-600 mt-1">${notification.message}</p>
                        <p class="text-xs text-gray-400 mt-1">${this.formatTimeAgo(notification.created_at)}</p>
                    </div>
                    ${!notification.is_read ? '<div class="w-2 h-2 bg-primary rounded-full"></div>' : ''}
                </div>
            </a>
        `).join('');
    }

    getNotificationIcon(type) {
        const icons = {
            'info': '<svg class="w-5 h-5 text-info" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>',
            'warning': '<svg class="w-5 h-5 text-warning" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>',
            'error': '<svg class="w-5 h-5 text-error" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
            'success': '<svg class="w-5 h-5 text-success" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>'
        };
        return icons[type] || icons['info'];
    }

    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return date.toLocaleDateString();
    }

    async markAsRead(notificationId) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            const response = await fetch(`/core/notifications/${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                // Refresh notifications
                this.fetchNotifications();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async markAllAsRead() {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            const response = await fetch('/core/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                this.fetchNotifications();
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    }

    showNewNotificationToast(notification) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'alert alert-info shadow-lg fixed bottom-4 right-4 w-96 z-50 animate-slide-in';
        toast.innerHTML = `
            <div>
                ${this.getNotificationIcon(notification.notification_type)}
                <div>
                    <h3 class="font-bold">${notification.title}</h3>
                    <div class="text-xs">${notification.message}</div>
                </div>
            </div>
            <button class="btn btn-sm btn-ghost" onclick="this.parentElement.remove()">✕</button>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Initialize notification manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});
