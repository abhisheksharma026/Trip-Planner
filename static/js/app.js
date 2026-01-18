// Trip Planner Web Application JavaScript

class TripPlannerApp {
    constructor() {
        this.userId = 'web_user_' + Date.now();
        this.sessionId = null;
        this.isLoading = false;
        this.hasInteracted = false;  // Track if user has sent any query
        
        this.init();
    }
    
    init() {
        this.loadSampleQueries();
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        const chatForm = document.getElementById('chatForm');
        const newSessionBtn = document.getElementById('newSessionBtn');
        const satisfiedBtn = document.getElementById('satisfiedBtn');
        const queryInput = document.getElementById('queryInput');
        
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
        
        newSessionBtn.addEventListener('click', () => {
            this.startNewSession();
        });
        
        if (satisfiedBtn) {
            satisfiedBtn.addEventListener('click', () => {
                this.markSatisfied();
            });
        }
        
        // Allow Enter key to send (Shift+Enter for new line)
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });
    }
    
    async loadSampleQueries() {
        try {
            const response = await fetch('/api/samples');
            const data = await response.json();
            
            if (data.success) {
                this.renderSamples(data.samples);
            }
        } catch (error) {
            console.error('Failed to load samples:', error);
            document.getElementById('samplesGrid').innerHTML = 
                '<div class="error">Failed to load sample queries</div>';
        }
    }
    
    renderSamples(samples) {
        const grid = document.getElementById('samplesGrid');
        grid.innerHTML = '';
        
        samples.forEach(sample => {
            const card = document.createElement('div');
            card.className = 'sample-card';
            card.innerHTML = `
                <div class="sample-card-title">${sample.title}</div>
                <div class="sample-card-description">${sample.description}</div>
                <div class="sample-card-query">"${sample.query}"</div>
            `;
            
            card.addEventListener('click', () => {
                this.useSampleQuery(sample.query);
            });
            
            grid.appendChild(card);
        });
    }
    
    useSampleQuery(query) {
        const input = document.getElementById('queryInput');
        input.value = query;
        input.focus();
        // Optionally auto-submit
        // this.handleSubmit();
    }
    
    async handleSubmit() {
        const input = document.getElementById('queryInput');
        const query = input.value.trim();
        
        if (!query || this.isLoading) {
            return;
        }
        
        // Add user message to chat
        this.addMessage(query, 'user');
        input.value = '';
        
        // Show loading state and thinking indicator
        this.setLoading(true);
        this.showThinkingIndicator();
        
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
            
            // Check if response is ok
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}: ${response.statusText}` }));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Debug logging
            console.log('Response data:', data);
            
            if (data.success) {
                // Ensure response is a string
                const responseText = typeof data.response === 'string' 
                    ? data.response 
                    : (data.response ? JSON.stringify(data.response, null, 2) : '');
                
                if (responseText && responseText.trim()) {
                    this.addMessage(responseText, 'agent');
                } else {
                    console.warn('Empty response received:', data);
                    this.addMessage(
                        'Received an empty response. Please try again.',
                        'agent'
                    );
                }
                
                if (data.session_id) {
                    this.sessionId = data.session_id;
                }
                
                // Show the satisfied button after getting a response
                this.hasInteracted = true;
                this.showSatisfiedButton(true);
            } else {
                const errorMsg = data.error || 'Something went wrong';
                console.error('API Error:', errorMsg);
                this.addMessage(
                    `Error: ${errorMsg}`,
                    'agent'
                );
            }
        } catch (error) {
            console.error('Network/Request Error:', error);
            const errorMessage = error.message || 'Unknown error occurred';
            this.addMessage(
                `Sorry, I encountered an error: ${errorMessage}. Please try again or start a new session.`,
                'agent'
            );
        } finally {
            // Always re-enable the UI, even if there was an error
            this.hideThinkingIndicator();
            this.setLoading(false);
        }
    }
    
    showThinkingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        
        // Remove any existing thinking indicator
        this.hideThinkingIndicator();
        
        // Create thinking indicator
        const thinkingDiv = document.createElement('div');
        thinkingDiv.id = 'thinkingIndicator';
        thinkingDiv.className = 'message agent-message thinking-message';
        thinkingDiv.innerHTML = `
            <div class="message-avatar">AI</div>
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
        
        // Scroll to show thinking indicator
        requestAnimationFrame(() => {
            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        });
    }
    
    hideThinkingIndicator() {
        const thinkingIndicator = document.getElementById('thinkingIndicator');
        if (thinkingIndicator) {
            thinkingIndicator.remove();
        }
    }
    
    addMessage(text, type) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatar = type === 'user' ? 'You' : 'AI';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <p>${this.formatMessage(text)}</p>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom with smooth behavior
        // Use requestAnimationFrame to ensure DOM is updated
        requestAnimationFrame(() => {
            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        });
    }
    
    formatMessage(text) {
        // Convert markdown headers (###, ##, #) to bold - must be on their own line
        // Process in reverse order (### first) to avoid conflicts
        let formatted = text
            .replace(/^###\s+(.+)$/gm, '<strong>$1</strong>')  // ### Header -> <strong>Header</strong>
            .replace(/^####\s+(.+)$/gm, '<strong>$1</strong>')
            .replace(/^##\s+(.+)$/gm, '<strong>$1</strong>')   // ## Header -> <strong>Header</strong>
            .replace(/^#\s+(.+)$/gm, '<strong>$1</strong>');  // # Header -> <strong>Header</strong>
        
        // Basic markdown-like formatting
        formatted = formatted
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
        
        return formatted;
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        const sendBtn = document.getElementById('sendBtn');
        const input = document.getElementById('queryInput');
        
        if (!sendBtn || !input) {
            console.error('Could not find send button or input element');
            return;
        }
        
        if (loading) {
            sendBtn.disabled = true;
            input.disabled = true;
            const btnText = sendBtn.querySelector('.btn-text');
            const btnLoader = sendBtn.querySelector('.btn-loader');
            if (btnText) btnText.style.display = 'none';
            if (btnLoader) btnLoader.style.display = 'inline';
        } else {
            sendBtn.disabled = false;
            input.disabled = false;
            const btnText = sendBtn.querySelector('.btn-text');
            const btnLoader = sendBtn.querySelector('.btn-loader');
            if (btnText) btnText.style.display = 'inline';
            if (btnLoader) btnLoader.style.display = 'none';
            // Ensure input is focused and ready for next query
            setTimeout(() => input.focus(), 100);
        }
    }
    
    async startNewSession() {
        if (confirm('Start a new session? This will clear the conversation history.')) {
            this.userId = 'web_user_' + Date.now();
            this.sessionId = null;
            this.hasInteracted = false;
            this.isLoading = false;  // Reset loading state
            
            // Hide the satisfied button
            this.showSatisfiedButton(false);
            
            // Re-enable input and send button (in case they were disabled from previous satisfaction)
            const input = document.getElementById('queryInput');
            const sendBtn = document.getElementById('sendBtn');
            if (input) {
                input.disabled = false;
                input.placeholder = 'Ask me anything about trip planning...';
                input.value = '';  // Clear any existing text
            }
            if (sendBtn) {
                sendBtn.disabled = false;
                const btnText = sendBtn.querySelector('.btn-text');
                const btnLoader = sendBtn.querySelector('.btn-loader');
                if (btnText) btnText.style.display = 'inline';
                if (btnLoader) btnLoader.style.display = 'none';
            }
            
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = `
                <div class="message agent-message">
                    <div class="message-avatar">AI</div>
                    <div class="message-content">
                        <p>Hello! I'm your AI travel concierge. I can help you plan complete trips by finding flights, hotels, and analyzing your budget. How can I assist you today?</p>
                    </div>
                </div>
            `;
            
            // Send a dummy query to create new session
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
            
            // Focus the input after a short delay
            setTimeout(() => {
                if (input) {
                    input.focus();
                }
            }, 100);
        }
    }
    
    showSatisfiedButton(show) {
        const satisfiedBtn = document.getElementById('satisfiedBtn');
        if (satisfiedBtn) {
            satisfiedBtn.style.display = show ? 'flex' : 'none';
        }
    }
    
    async markSatisfied() {
        // Log satisfaction feedback
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
        
        // Show thank you message
        this.addMessage('Thank you for using AI Trip Planner! I\'m glad I could help. Feel free to start a new session anytime you need travel assistance. Have a great trip!', 'agent');
        
        // Hide the satisfied button
        this.showSatisfiedButton(false);
        
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
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TripPlannerApp();
});

