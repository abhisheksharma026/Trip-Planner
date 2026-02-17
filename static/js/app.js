/**
 * AI Trip Planner Web Application
 * Professional JavaScript with enhanced UX
 */

// ============================================
// Utility Functions
// ============================================
const Utils = {
    /**
     * Generate a unique ID
     */
    generateId() {
        return `id_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },

    /**
     * Format timestamp for display
     */
    formatTime(date = new Date()) {
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    },

    /**
     * Debounce function execution
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return true;
            } catch (fallbackErr) {
                document.body.removeChild(textArea);
                return false;
            }
        }
    }
};

// ============================================
// Toast Notification System
// ============================================
class ToastManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = containerId;
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    show(options) {
        const {
            type = 'info',
            title = '',
            message = '',
            duration = 5000,
            icon = null
        } = options;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
            error: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
            info: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
            warning: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icon || icons[type] || icons.info}</div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${Utils.escapeHtml(title)}</div>` : ''}
                <div class="toast-message">${Utils.escapeHtml(message)}</div>
            </div>
            <button class="toast-close" aria-label="Close notification">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        `;

        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.dismiss(toast));

        this.container.appendChild(toast);

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(toast), duration);
        }

        return toast;
    }

    dismiss(toast) {
        if (!toast || !toast.parentNode) return;
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    success(message, title = 'Success') {
        return this.show({ type: 'success', title, message });
    }

    error(message, title = 'Error') {
        return this.show({ type: 'error', title, message, duration: 7000 });
    }

    info(message, title = 'Info') {
        return this.show({ type: 'info', title, message });
    }

    warning(message, title = 'Warning') {
        return this.show({ type: 'warning', title, message });
    }
}

// ============================================
// Message Formatter with Enhanced Markdown
// ============================================
class MessageFormatter {
    /**
     * Format message with enhanced markdown support
     */
    static format(text) {
        if (!text) return '';

        // Escape HTML first to prevent XSS
        let formatted = Utils.escapeHtml(text);

        // Process markdown patterns (in order of specificity)

        // Code blocks (```...```) - must be processed first
        formatted = formatted.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
        });

        // Inline code (`...`)
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Headers (must be on their own line)
        formatted = formatted.replace(/^####\s+(.+)$/gm, '<strong>$1</strong>');
        formatted = formatted.replace(/^###\s+(.+)$/gm, '<strong>$1</strong>');
        formatted = formatted.replace(/^##\s+(.+)$/gm, '<strong>$1</strong>');
        formatted = formatted.replace(/^#\s+(.+)$/gm, '<strong>$1</strong>');

        // Bold and Italic
        formatted = formatted.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Links
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

        // Unordered lists
        formatted = formatted.replace(/^[\*\-]\s+(.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // Ordered lists
        formatted = formatted.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');

        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');

        return formatted;
    }

    /**
     * Format message with typing animation
     */
    static formatWithTyping(element, text, speed = 10) {
        element.innerHTML = '';
        const formatted = this.format(text);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = formatted;

        let i = 0;
        const chars = tempDiv.textContent;
        element.textContent = '';

        const typeChar = () => {
            if (i < chars.length) {
                element.textContent += chars.charAt(i);
                i++;
                setTimeout(typeChar, speed);
            } else {
                element.innerHTML = formatted;
            }
        };

        typeChar();
    }
}

// ============================================
// Main Application Class
// ============================================
class TripPlannerApp {
    constructor() {
        this.userId = 'web_user_' + Date.now();
        this.sessionId = null;
        this.isLoading = false;
        this.hasInteracted = false;
        this.messageHistory = [];

        // Initialize toast manager
        this.toast = new ToastManager('toastContainer');

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSampleQueries();
        this.initializeChatStatus();
    }

    setupEventListeners() {
        const chatForm = document.getElementById('chatForm');
        const newSessionBtn = document.getElementById('newSessionBtn');
        const satisfiedBtn = document.getElementById('satisfiedBtn');
        const queryInput = document.getElementById('queryInput');

        // Form submission
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // New session
        newSessionBtn?.addEventListener('click', () => {
            this.startNewSession();
        });

        // Satisfied button
        satisfiedBtn?.addEventListener('click', () => {
            this.markSatisfied();
        });

        // Input keyboard handling
        queryInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });

        // Auto-resize textarea for long inputs (if using textarea instead of input)
        queryInput?.addEventListener('input', Utils.debounce((e) => {
            this.updateChatStatus(e.target.value ? 'Typing...' : 'Ready to help');
        }, 300));
    }

    initializeChatStatus() {
        this.updateChatStatus('Ready to help');
    }

    updateChatStatus(status) {
        const chatStatus = document.getElementById('chatStatus');
        if (chatStatus) {
            chatStatus.textContent = status;
        }
    }

    async loadSampleQueries() {
        try {
            const response = await fetch('/api/samples');
            const data = await response.json();

            if (data.success) {
                this.renderSamples(data.samples);
            } else {
                throw new Error(data.error || 'Failed to load samples');
            }
        } catch (error) {
            console.error('Failed to load samples:', error);
            this.toast.error('Failed to load sample queries. Please refresh the page.');

            const grid = document.getElementById('samplesGrid');
            if (grid) {
                grid.innerHTML = `
                    <div class="sample-card error-state">
                        <div class="sample-card-title">Unable to Load Samples</div>
                        <div class="sample-card-description">Please check your connection and try again</div>
                    </div>
                `;
            }
        }
    }

    renderSamples(samples) {
        const grid = document.getElementById('samplesGrid');
        if (!grid) return;

        grid.innerHTML = '';

        samples.forEach(sample => {
            const card = document.createElement('div');
            card.className = 'sample-card';
            card.setAttribute('role', 'listitem');
            card.setAttribute('tabindex', '0');

            card.innerHTML = `
                <div class="sample-card-title">${Utils.escapeHtml(sample.title)}</div>
                <div class="sample-card-description">${Utils.escapeHtml(sample.description)}</div>
                <div class="sample-card-query">"${Utils.escapeHtml(sample.query)}"</div>
            `;

            // Click handler
            card.addEventListener('click', () => {
                this.useSampleQuery(sample.query);
            });

            // Keyboard handler
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.useSampleQuery(sample.query);
                }
            });

            grid.appendChild(card);
        });
    }

    useSampleQuery(query) {
        const input = document.getElementById('queryInput');
        if (input) {
            input.value = query;
            input.focus();
            // Add visual feedback
            input.classList.add('sample-loaded');
            setTimeout(() => input.classList.remove('sample-loaded'), 300);
        }
    }

    async handleSubmit() {
        const input = document.getElementById('queryInput');
        const query = input?.value.trim();

        if (!query || this.isLoading) {
            return;
        }

        // Add user message
        this.addMessage(query, 'user');
        input.value = '';

        // Update state
        this.isLoading = true;
        this.setLoading(true);
        this.showThinkingIndicator();
        this.updateChatStatus('Agent is thinking...');

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    user_id: this.userId,
                    new_session: false
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({
                    error: `HTTP ${response.status}: ${response.statusText}`
                }));
                
                // Handle 401 - anonymous limit exceeded, show login modal
                if (response.status === 401) {
                    this.hideThinkingIndicator();
                    this.setLoading(false);
                    this.updateChatStatus('Login required');
                    
                    // Show message in chat
                    this.addMessage(
                        '🎉 You\'ve used all 5 free queries! Please log in to continue planning your trip. It\'s free and only takes a moment.',
                        'agent'
                    );
                    
                    // Show login modal
                    if (window.authManager) {
                        window.authManager.showModal();
                    }
                    return;
                }
                
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Check for anonymous remaining queries in headers
            const anonRemaining = response.headers.get('X-Anonymous-Remaining');
            const isAuthenticated = response.headers.get('X-Authenticated') === 'true';
            
            // Show warning when running low on free queries
            if (!isAuthenticated && anonRemaining) {
                const remaining = parseInt(anonRemaining, 10);
                if (remaining <= 2 && remaining > 0) {
                    this.toast.warning(`⚠️ Only ${remaining} free ${remaining === 1 ? 'query' : 'queries'} remaining. Log in to continue planning!`);
                }
            }

            if (data.success) {
                const responseText = typeof data.response === 'string'
                    ? data.response
                    : (data.response ? JSON.stringify(data.response, null, 2) : '');

                if (responseText && responseText.trim()) {
                    this.addMessage(responseText, 'agent');
                } else {
                    this.toast.warning('Received an empty response. Please try again.');
                    this.addMessage(
                        'I received your message but couldn\'t generate a response. Please try again.',
                        'agent'
                    );
                }

                if (data.session_id) {
                    this.sessionId = data.session_id;
                }

                this.hasInteracted = true;
                this.showSatisfiedButton(true);
            } else {
                throw new Error(data.error || 'Something went wrong');
            }
        } catch (error) {
            console.error('Request error:', error);
            this.toast.error(`Network error: ${error.message}`);

            this.addMessage(
                `Sorry, I encountered an error: ${error.message}. Please try again or start a new session.`,
                'agent'
            );
        } finally {
            this.hideThinkingIndicator();
            this.setLoading(false);
            this.updateChatStatus('Ready to help');
        }
    }

    addMessage(text, type) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.setAttribute('role', 'article');

        const avatar = type === 'user' ? '👤' : '✈️';
        const senderName = type === 'user' ? 'You' : 'Travel Assistant';
        const timeStr = Utils.formatTime();

        messageDiv.innerHTML = `
            <div class="message-avatar" aria-hidden="true">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="sender-name">${Utils.escapeHtml(senderName)}</span>
                    <span class="message-time">${timeStr}</span>
                </div>
                <p>${MessageFormatter.format(text)}</p>
                ${type === 'agent' ? `
                    <button class="copy-btn" aria-label="Copy message" data-message="${Utils.escapeHtml(text)}">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                    </button>
                ` : ''}
            </div>
        `;

        // Add copy functionality
        const copyBtn = messageDiv.querySelector('.copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', async () => {
                const messageText = copyBtn.getAttribute('data-message');
                const success = await Utils.copyToClipboard(messageText);
                if (success) {
                    this.toast.success('Message copied to clipboard');
                    copyBtn.classList.add('copied');
                    setTimeout(() => copyBtn.classList.remove('copied'), 2000);
                } else {
                    this.toast.error('Failed to copy message');
                }
            });
        }

        messagesContainer.appendChild(messageDiv);
        this.messageHistory.push({ text, type, time: Date.now() });

        // Smooth scroll to bottom
        requestAnimationFrame(() => {
            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        });
    }

    showThinkingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        // Remove existing thinking indicator
        this.hideThinkingIndicator();

        const thinkingDiv = document.createElement('div');
        thinkingDiv.id = 'thinkingIndicator';
        thinkingDiv.className = 'message agent-message thinking-message';
        thinkingDiv.setAttribute('role', 'status');
        thinkingDiv.setAttribute('aria-live', 'polite');

        thinkingDiv.innerHTML = `
            <div class="message-avatar" aria-hidden="true">✈️</div>
            <div class="message-content thinking-content">
                <div class="thinking-dots">
                    <span class="thinking-text">Agent is thinking</span>
                    <span class="dot">.</span>
                    <span class="dot">.</span>
                    <span class="dot">.</span>
                </div>
                <p class="thinking-subtext">Searching for flights, hotels, and travel information...</p>
            </div>
        `;

        messagesContainer.appendChild(thinkingDiv);

        requestAnimationFrame(() => {
            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        });
    }

    hideThinkingIndicator() {
        const thinkingIndicator = document.getElementById('thinkingIndicator');
        if (thinkingIndicator && thinkingIndicator.parentNode) {
            thinkingIndicator.parentNode.removeChild(thinkingIndicator);
        }
    }

    setLoading(loading) {
        this.isLoading = loading;
        const sendBtn = document.getElementById('sendBtn');
        const input = document.getElementById('queryInput');

        if (!sendBtn || !input) {
            console.error('Required elements not found');
            return;
        }

        if (loading) {
            sendBtn.disabled = true;
            input.disabled = true;

            const btnIcon = sendBtn.querySelector('.btn-icon');
            const btnLoader = sendBtn.querySelector('.btn-loader');

            if (btnIcon) btnIcon.style.display = 'none';
            if (btnLoader) btnLoader.style.display = 'inline';
        } else {
            sendBtn.disabled = false;
            input.disabled = false;

            const btnIcon = sendBtn.querySelector('.btn-icon');
            const btnLoader = sendBtn.querySelector('.btn-loader');

            if (btnIcon) btnIcon.style.display = 'inline';
            if (btnLoader) btnLoader.style.display = 'none';

            setTimeout(() => input.focus(), 100);
        }
    }

    async startNewSession() {
        if (!confirm('Start a new session? This will clear the conversation history.')) {
            return;
        }

        this.userId = 'web_user_' + Date.now();
        this.sessionId = null;
        this.hasInteracted = false;
        this.isLoading = false;
        this.messageHistory = [];

        this.showSatisfiedButton(false);

        // Reset input and button
        const input = document.getElementById('queryInput');
        const sendBtn = document.getElementById('sendBtn');

        if (input) {
            input.disabled = false;
            input.placeholder = 'Ask me anything about trip planning...';
            input.value = '';
        }

        if (sendBtn) {
            sendBtn.disabled = false;
            const btnIcon = sendBtn.querySelector('.btn-icon');
            const btnLoader = sendBtn.querySelector('.btn-loader');
            if (btnIcon) btnIcon.style.display = 'inline';
            if (btnLoader) btnLoader.style.display = 'none';
        }

        // Reset chat messages
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="message agent-message">
                    <div class="message-avatar" aria-hidden="true">✈️</div>
                    <div class="message-content">
                        <div class="message-header">
                            <span class="sender-name">Travel Assistant</span>
                            <span class="message-time">${Utils.formatTime()}</span>
                        </div>
                        <p>Hello! I'm your AI travel concierge. I can help you plan complete trips by finding flights, hotels, and analyzing your budget. How can I assist you today?</p>
                    </div>
                </div>
            `;
        }

        // Create new session on server
        try {
            await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: 'New session',
                    user_id: this.userId,
                    new_session: true
                })
            });
        } catch (error) {
            console.error('Error creating new session:', error);
        }

        this.toast.success('New session started');

        setTimeout(() => {
            if (input) input.focus();
        }, 100);
    }

    showSatisfiedButton(show) {
        const satisfiedBtn = document.getElementById('satisfiedBtn');
        if (satisfiedBtn) {
            satisfiedBtn.style.display = show ? 'flex' : 'none';
        }
    }

    async markSatisfied() {
        try {
            await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    session_id: this.sessionId,
                    feedback: 'satisfied'
                })
            });
        } catch (error) {
            console.error('Error logging feedback:', error);
        }

        this.toast.success('Thank you for your feedback!');
        this.showSatisfiedButton(false);

        this.addMessage(
            'Thank you for using AI Trip Planner! I\'m glad I could help. Feel free to start a new session anytime you need travel assistance. Have a great trip!',
            'agent'
        );

        // Disable input after satisfaction
        const input = document.getElementById('queryInput');
        const sendBtn = document.getElementById('sendBtn');

        if (input) {
            input.disabled = true;
            input.placeholder = 'Session ended. Click "New Session" to start again.';
        }

        if (sendBtn) {
            sendBtn.disabled = true;
        }

        this.updateChatStatus('Session ended');
    }
}

// ============================================
// Authentication Manager
// ============================================
class AuthManager {
    constructor() {
        this.user = null;
        this.isRegisterMode = false;
        
        // DOM elements
        this.userInfoEl = document.getElementById('userInfo');
        this.loginBtnEl = document.getElementById('loginBtn');
        this.userNameEl = document.getElementById('userName');
        this.logoutBtnEl = document.getElementById('logoutBtn');
        this.loginModal = document.getElementById('loginModal');
        this.authForm = document.getElementById('authForm');
        this.modalTitle = document.getElementById('modalTitle');
        this.nameGroup = document.getElementById('nameGroup');
        this.switchModeText = document.getElementById('switchModeText');
        this.switchToRegister = document.getElementById('switchToRegister');
        this.closeModal = document.getElementById('closeModal');
        this.formError = document.getElementById('formError');
        this.submitBtn = document.getElementById('submitBtn');
        
        this.init();
    }
    
    async init() {
        // Check if user is logged in
        await this.checkAuthStatus();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Login button opens modal
        if (this.loginBtnEl) {
            this.loginBtnEl.addEventListener('click', () => this.showModal());
        }
        
        // Close modal
        if (this.closeModal) {
            this.closeModal.addEventListener('click', () => this.hideModal());
        }
        
        // Click outside modal to close
        if (this.loginModal) {
            this.loginModal.addEventListener('click', (e) => {
                if (e.target === this.loginModal) this.hideModal();
            });
        }
        
        // Switch between login and register
        if (this.switchToRegister) {
            this.switchToRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMode();
            });
        }
        
        // Logout
        if (this.logoutBtnEl) {
            this.logoutBtnEl.addEventListener('click', () => this.logout());
        }
        
        // Form submit
        if (this.authForm) {
            this.authForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }
    
    async checkAuthStatus() {
        try {
            const response = await fetch('/api/user');
            const data = await response.json();
            
            if (data.authenticated && data.user) {
                this.user = data.user;
                this.showUserInfo();
            } else {
                this.showLoginButton();
            }
        } catch (error) {
            console.error('Failed to check auth status:', error);
            this.showLoginButton();
        }
    }
    
    showUserInfo() {
        if (this.userInfoEl && this.user) {
            this.userInfoEl.style.display = 'flex';
            if (this.userNameEl) {
                this.userNameEl.textContent = this.user.name || this.user.email;
            }
        }
        if (this.loginBtnEl) {
            this.loginBtnEl.style.display = 'none';
        }
    }
    
    showLoginButton() {
        if (this.userInfoEl) {
            this.userInfoEl.style.display = 'none';
        }
        if (this.loginBtnEl) {
            this.loginBtnEl.style.display = 'inline-flex';
        }
    }
    
    showModal() {
        if (this.loginModal) {
            this.loginModal.style.display = 'flex';
        }
    }
    
    hideModal() {
        if (this.loginModal) {
            this.loginModal.style.display = 'none';
        }
        this.clearError();
    }
    
    toggleMode() {
        this.isRegisterMode = !this.isRegisterMode;
        
        if (this.isRegisterMode) {
            this.modalTitle.textContent = 'Register';
            this.submitBtn.textContent = 'Register';
            this.nameGroup.style.display = 'block';
            this.switchModeText.innerHTML = 'Already have an account? <a href="#" id="switchToRegister">Login</a>';
        } else {
            this.modalTitle.textContent = 'Login';
            this.submitBtn.textContent = 'Login';
            this.nameGroup.style.display = 'none';
            this.switchModeText.innerHTML = 'Don\'t have an account? <a href="#" id="switchToRegister">Register</a>';
        }
        
        // Re-attach event listener
        const switchLink = document.getElementById('switchToRegister');
        if (switchLink) {
            switchLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMode();
            });
        }
        
        this.clearError();
    }
    
    showError(message) {
        if (this.formError) {
            this.formError.textContent = message;
            this.formError.style.display = 'block';
        }
    }
    
    clearError() {
        if (this.formError) {
            this.formError.style.display = 'none';
        }
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const name = document.getElementById('name')?.value || '';
        
        const endpoint = this.isRegisterMode ? '/api/register' : '/api/login';
        const body = this.isRegisterMode
            ? { email, password, name: name || undefined }
            : { email, password };
        
        try {
            this.submitBtn.disabled = true;
            this.submitBtn.textContent = this.isRegisterMode ? 'Registering...' : 'Logging in...';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.user = data.user;
                this.hideModal();
                this.showUserInfo();
                window.location.reload(); // Refresh to update session
            } else {
                this.showError(data.error || 'Authentication failed');
            }
        } catch (error) {
            console.error('Auth error:', error);
            this.showError('Connection error. Please try again.');
        } finally {
            this.submitBtn.disabled = false;
            this.submitBtn.textContent = this.isRegisterMode ? 'Register' : 'Login';
        }
    }
    
    async logout() {
        try {
            await fetch('/api/logout', { method: 'POST' });
            this.user = null;
            window.location.reload();
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
    
    isAuthenticated() {
        return this.user !== null;
    }
    
    getUserId() {
        return this.user?.id || 'web_user';
    }
}


// ============================================
// Initialize Application
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Create global app instance
    window.tripPlannerApp = new TripPlannerApp();
    
    // Create auth manager
    window.authManager = new AuthManager();

    // Add service worker registration for PWA support (optional)
    if ('serviceWorker' in navigator) {
        // Uncomment when service worker is implemented
        // navigator.serviceWorker.register('/sw.js');
    }
});

// Handle visibility change to update connection status
document.addEventListener('visibilitychange', () => {
    const app = window.tripPlannerApp;
    if (!app) return;

    if (document.visibilityState === 'visible') {
        // Page is visible again
        app.updateChatStatus('Ready to help');
    }
});

// Handle beforeunload to warn about unsaved changes
window.addEventListener('beforeunload', (e) => {
    const app = window.tripPlannerApp;
    if (app && app.messageHistory.length > 1) {
        e.preventDefault();
        e.returnValue = '';
    }
});
