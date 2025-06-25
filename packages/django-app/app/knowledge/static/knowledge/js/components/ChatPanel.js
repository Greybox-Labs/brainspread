const ChatPanel = {
  name: "ChatPanel",
  components: {
    ChatHistory: window.ChatHistory,
  },
  data() {
    return {
      isOpen: this.loadOpenState(),
      message: "",
      messages: [],
      loading: false,
      width: this.loadWidth(),
      isResizing: false,
      minWidth: 300,
      maxWidth: 800,
      currentSessionId: null,
      showModelSelector: false,
      aiSettings: null,
      selectedModel: null,
    };
  },
  mounted() {
    this.setupResizeListener();
    this.loadAISettings();
  },
  beforeUnmount() {
    this.removeResizeListener();
  },
  updated() {
    // Auto-scroll to bottom when messages are updated
    this.scrollToBottom();
  },
  methods: {
    loadOpenState() {
      const saved = localStorage.getItem('chatPanel.isOpen');
      return saved !== null ? JSON.parse(saved) : true;
    },
    loadWidth() {
      const saved = localStorage.getItem('chatPanel.width');
      return saved ? parseInt(saved) : 400;
    },
    saveOpenState() {
      localStorage.setItem('chatPanel.isOpen', JSON.stringify(this.isOpen));
    },
    saveWidth() {
      localStorage.setItem('chatPanel.width', this.width.toString());
    },
    togglePanel() {
      this.isOpen = !this.isOpen;
      this.saveOpenState();
    },
    async sendMessage() {
      if (!this.message) return;
      const userMsg = { 
        role: "user", 
        content: this.message,
        created_at: new Date().toISOString()
      };
      this.messages.push(userMsg);
      this.scrollToBottom(); // Scroll after adding user message
      const payload = { 
        message: this.message,
        session_id: this.currentSessionId 
      };
      this.message = "";
      this.loading = true;
      try {
        const result = await window.apiService.sendAIMessage(payload);
        if (result.success) {
          this.messages.push({ 
            role: "assistant", 
            content: result.data.response,
            created_at: new Date().toISOString()
          });
          if (result.data.session_id && !this.currentSessionId) {
            this.currentSessionId = result.data.session_id;
          }
          this.scrollToBottom(); // Scroll after adding assistant response
        }
      } catch (err) {
        console.error(err);
      } finally {
        this.loading = false;
      }
    },
    async onSessionSelected(session) {
      try {
        const result = await window.apiService.getChatSessionDetail(session.uuid);
        if (result.success) {
          this.messages = result.data.messages;
          this.currentSessionId = session.uuid;
          this.scrollToBottom(); // Scroll to bottom after loading session messages
        }
      } catch (error) {
        console.error("Failed to load session:", error);
      }
    },
    startNewChat() {
      this.messages = [];
      this.currentSessionId = null;
    },
    setupResizeListener() {
      this.resizeHandler = this.handleMouseMove.bind(this);
      this.stopResizeHandler = this.stopResize.bind(this);
    },
    removeResizeListener() {
      document.removeEventListener("mousemove", this.resizeHandler);
      document.removeEventListener("mouseup", this.stopResizeHandler);
    },
    startResize(e) {
      this.isResizing = true;
      this.startX = e.clientX;
      this.startWidth = this.width;
      document.addEventListener("mousemove", this.resizeHandler);
      document.addEventListener("mouseup", this.stopResizeHandler);
      e.preventDefault();
    },
    handleMouseMove(e) {
      if (!this.isResizing) return;
      const deltaX = this.startX - e.clientX; // Reversed for right sidebar
      const newWidth = this.startWidth + deltaX;
      if (newWidth >= this.minWidth && newWidth <= this.maxWidth) {
        this.width = newWidth;
      }
    },
    stopResize() {
      this.isResizing = false;
      document.removeEventListener("mousemove", this.resizeHandler);
      document.removeEventListener("mouseup", this.stopResizeHandler);
      this.saveWidth(); // Save width when resize is finished
    },
    handleKeydown(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
      // Shift+Enter will naturally create a newline (default behavior)
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const messagesContainer = this.$el.querySelector('.messages');
        if (messagesContainer) {
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
      });
    },
    formatTimestamp(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();
      
      if (isToday) {
        // Show only time for today's messages
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else {
        // Show date and time for older messages
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
    },
    
    async loadAISettings() {
      try {
        const result = await window.apiService.getAISettings();
        if (result.success) {
          this.aiSettings = result.data;
          this.selectedModel = result.data.current_model;
        }
      } catch (error) {
        console.error("Failed to load AI settings:", error);
      }
    },
    
    toggleModelSelector() {
      this.showModelSelector = !this.showModelSelector;
    },
    
    getAvailableModels() {
      if (!this.aiSettings || !this.aiSettings.current_provider) return [];
      
      const currentProvider = this.aiSettings.providers.find(
        p => p.name === this.aiSettings.current_provider
      );
      
      if (!currentProvider) return [];
      
      const providerConfig = this.aiSettings.provider_configs[this.aiSettings.current_provider];
      if (providerConfig && providerConfig.enabled_models && providerConfig.enabled_models.length > 0) {
        return providerConfig.enabled_models;
      }
      
      return currentProvider.models;
    },
    
    async selectModel(model) {
      try {
        this.selectedModel = model;
        this.showModelSelector = false;
        
        // Update user's default model
        const updateData = {
          provider: this.aiSettings.current_provider,
          model: model
        };
        
        await window.apiService.updateAISettings(updateData);
        await this.loadAISettings(); // Refresh settings
      } catch (error) {
        console.error("Failed to update model:", error);
      }
    },
    
    openSettings() {
      // Emit event to parent to open settings modal with AI tab
      this.$emit('open-settings', 'ai');
    },
  },
  template: `
    <div class="chat-panel" :class="{ open: isOpen }" :style="{ width: width + 'px' }">
      <div class="chat-resize-handle" 
           :class="{ resizing: isResizing }"
           @mousedown="startResize">
      </div>
      <button class="chat-toggle" @click="togglePanel">AI</button>
      <div class="chat-content">
        <div class="chat-header">
          <ChatHistory @session-selected="onSessionSelected" />
          <button class="new-chat-btn" @click="startNewChat" title="Start new chat">+</button>
        </div>
        <div class="messages">
          <div v-for="(msg, index) in messages" :key="index" :class="['message-bubble', msg.role]">
            <div class="message-content">{{ msg.content }}</div>
            <div class="message-timestamp">{{ formatTimestamp(msg.created_at) }}</div>
          </div>
          <div v-if="loading" class="message-bubble assistant loading">
            <div class="message-content loading-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
        <div class="input-area">
          <div class="chat-controls">
            <div class="model-selector" v-if="aiSettings">
              <button 
                class="model-selector-btn" 
                @click="toggleModelSelector"
                :title="selectedModel || 'Select Model'"
              >
                {{ selectedModel || 'Model' }}
                <span class="dropdown-arrow">▼</span>
              </button>
              <div v-if="showModelSelector" class="model-dropdown">
                <div 
                  v-for="model in getAvailableModels()" 
                  :key="model"
                  class="model-option"
                  :class="{ active: model === selectedModel }"
                  @click="selectModel(model)"
                >
                  {{ model }}
                </div>
              </div>
            </div>
            <button class="settings-btn" @click="openSettings" title="AI Settings">⚙️</button>
          </div>
          <div class="message-input">
            <textarea v-model="message" placeholder="Ask something..." @keydown="handleKeydown"></textarea>
            <button @click="sendMessage" :disabled="loading">
              {{ loading ? 'Sending...' : 'Send' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
};

window.ChatPanel = ChatPanel;
