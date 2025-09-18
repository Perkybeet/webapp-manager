/**
 * Main JavaScript for WebApp Manager SAAS
 */

// Global variables
let refreshIntervals = {};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Add fade-in effect to main content
    const main = document.querySelector('main');
    if (main) {
        main.classList.add('fade-in');
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Set up CSRF token for axios
    setupAxiosDefaults();
    
    // Set up global error handling
    setupGlobalErrorHandling();
}

function setupAxiosDefaults() {
    // Add request interceptor to show loading states
    axios.interceptors.request.use(function(config) {
        showLoadingState(true);
        return config;
    }, function(error) {
        showLoadingState(false);
        return Promise.reject(error);
    });

    // Add response interceptor to hide loading states
    axios.interceptors.response.use(function(response) {
        showLoadingState(false);
        return response;
    }, function(error) {
        showLoadingState(false);
        return Promise.reject(error);
    });
}

function setupGlobalErrorHandling() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        showNotification('Ha ocurrido un error inesperado', 'error');
    });
    
    // Handle general errors
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
    });
}

// Loading state management
function showLoadingState(show) {
    const loadingElements = document.querySelectorAll('.loading-overlay');
    loadingElements.forEach(element => {
        element.style.display = show ? 'flex' : 'none';
    });
    
    // Disable/enable buttons during loading
    const buttons = document.querySelectorAll('button[type="submit"], .btn-primary');
    buttons.forEach(button => {
        if (show) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Cargando...';
        } else {
            button.disabled = false;
            // Restore original text (this is basic, you might want to store original text)
        }
    });
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 1050;
        min-width: 300px;
        max-width: 500px;
    `;
    
    const icon = getNotificationIcon(type);
    notification.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'danger': 
        case 'error': return 'exclamation-triangle';
        case 'warning': return 'exclamation-circle';
        case 'info': return 'info-circle';
        default: return 'bell';
    }
}

// Utility functions
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatUptime(seconds) {
    const days = Math.floor(seconds / (3600 * 24));
    const hours = Math.floor((seconds % (3600 * 24)) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    let result = '';
    if (days > 0) result += `${days}d `;
    if (hours > 0) result += `${hours}h `;
    if (minutes > 0) result += `${minutes}m`;
    
    return result || '0m';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Modal helpers
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        new bootstrap.Modal(modal).show();
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    }
}

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

function confirmDelete(itemName, callback) {
    const message = `¿Está seguro de que desea eliminar "${itemName}"?\n\nEsta acción no se puede deshacer.`;
    confirmAction(message, callback);
}

// Real-time updates
function startRealTimeUpdates(updateFunction, interval = 30000) {
    const intervalId = setInterval(updateFunction, interval);
    refreshIntervals[updateFunction.name] = intervalId;
    return intervalId;
}

function stopRealTimeUpdates(functionName) {
    if (refreshIntervals[functionName]) {
        clearInterval(refreshIntervals[functionName]);
        delete refreshIntervals[functionName];
    }
}

function stopAllRealTimeUpdates() {
    Object.values(refreshIntervals).forEach(intervalId => {
        clearInterval(intervalId);
    });
    refreshIntervals = {};
}

// Clean up intervals when page unloads
window.addEventListener('beforeunload', stopAllRealTimeUpdates);

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copiado al portapapeles', 'success', 2000);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showNotification('Copiado al portapapeles', 'success', 2000);
        } catch (error) {
            showNotification('Error al copiar al portapapeles', 'error');
        }
        
        textArea.remove();
    }
}

// Theme management
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    document.body.setAttribute('data-theme', theme);
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', initializeTheme);

// Search functionality
function setupSearch(searchInputId, targetSelector) {
    const searchInput = document.getElementById(searchInputId);
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase();
        const targets = document.querySelectorAll(targetSelector);
        
        targets.forEach(target => {
            const text = target.textContent.toLowerCase();
            const matches = text.includes(query);
            target.style.display = matches ? '' : 'none';
        });
    });
}

// Status checking
async function checkSystemHealth() {
    try {
        const response = await axios.get('/api/v1/system/health');
        return response.data;
    } catch (error) {
        console.error('Health check failed:', error);
        return { status: 'error', message: 'Health check failed' };
    }
}

// WebSocket connection for real-time updates
class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = 5000;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.callbacks = {};
    }
    
    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.onOpen();
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.onMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.onClose();
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.onError(error);
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.attemptReconnect();
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectInterval);
        }
    }
    
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }
    
    off(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event] = this.callbacks[event].filter(cb => cb !== callback);
        }
    }
    
    onOpen() {
        this.emit('open');
    }
    
    onMessage(data) {
        this.emit('message', data);
        if (data.type) {
            this.emit(data.type, data);
        }
    }
    
    onClose() {
        this.emit('close');
    }
    
    onError(error) {
        this.emit('error', error);
    }
    
    emit(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => callback(data));
        }
    }
}

// Export for use in other scripts
window.WebAppManager = {
    showNotification,
    formatBytes,
    formatUptime,
    formatDate,
    validateForm,
    showModal,
    hideModal,
    confirmAction,
    confirmDelete,
    copyToClipboard,
    toggleTheme,
    setupSearch,
    checkSystemHealth,
    WebSocketManager
};