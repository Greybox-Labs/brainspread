const ChatPanel = {
  name: "ChatPanel",
  components: {
    ChatHistory: window.ChatHistory,
  },
  props: {
    chatContextBlocks: {
      type: Array,
      default: () => [],
    },
    visibleBlocks: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["open-settings", "remove-context-block", "clear-context"],
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
      showContextArea: false,
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
      const saved = localStorage.getItem("chatPanel.isOpen");
      return saved !== null ? JSON.parse(saved) : true;
    },
    loadWidth() {
      const saved = localStorage.getItem("chatPanel.width");
      return saved ? parseInt(saved) : 400;
    },
    saveOpenState() {
      localStorage.setItem("chatPanel.isOpen", JSON.stringify(this.isOpen));
    },
    saveWidth() {
      localStorage.setItem("chatPanel.width", this.width.toString());
    },
    togglePanel() {
      this.isOpen = !this.isOpen;
      this.saveOpenState();
    },
    async sendMessage() {
      if (!this.message) return;
      if (!this.selectedModel) {
        console.error("No model selected");
        this.messages.push({
          role: "assistant",
          content:
            "Error: No AI model selected. Please select a model or configure your API keys in settings.",
          created_at: new Date().toISOString(),
        });
        return;
      }
      const userMsg = {
        role: "user",
        content: this.message,
        created_at: new Date().toISOString(),
      };
      this.messages.push(userMsg);
      this.scrollToBottom(); // Scroll after adding user message
      const payload = {
        message: this.message,
        model: this.selectedModel,
        session_id: this.currentSessionId,
        context_blocks: this.chatContextBlocks,
      };
      this.message = "";
      this.loading = true;
      try {
        const result = await window.apiService.sendAIMessage(payload);
        if (result.success) {
          this.messages.push({
            role: "assistant",
            content: result.data.response,
            created_at: new Date().toISOString(),
          });
          if (result.data.session_id && !this.currentSessionId) {
            this.currentSessionId = result.data.session_id;
          }
          this.scrollToBottom(); // Scroll after adding assistant response
        } else {
          // Handle error response
          const errorMsg = result.error || "Failed to send message";
          this.messages.push({
            role: "assistant",
            content: `Error: ${errorMsg}`,
            created_at: new Date().toISOString(),
          });
        }
      } catch (err) {
        console.error(err);
        this.messages.push({
          role: "assistant",
          content:
            "Error: Failed to send message. Please check your connection and try again.",
          created_at: new Date().toISOString(),
        });
      } finally {
        this.loading = false;
      }
    },
    async onSessionSelected(session) {
      try {
        const result = await window.apiService.getChatSessionDetail(
          session.uuid
        );
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
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
      // Shift+Enter will naturally create a newline (default behavior)
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const messagesContainer = this.$el.querySelector(".messages");
        if (messagesContainer) {
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
      });
    },
    formatTimestamp(timestamp) {
      if (!timestamp) return "";
      const date = new Date(timestamp);
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();

      if (isToday) {
        // Show only time for today's messages
        return date.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
      } else {
        // Show date and time for older messages
        return (
          date.toLocaleDateString() +
          " " +
          date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        );
      }
    },

    async loadAISettings() {
      try {
        const result = await window.apiService.getAISettings();
        if (result.success) {
          this.aiSettings = result.data;
          this.selectedModel = result.data.current_model;

          // If no current model or it's not available, pick the first available one
          if (
            !this.selectedModel ||
            !this.isModelAvailable(this.selectedModel)
          ) {
            const availableModels = this.getAvailableModels();
            if (availableModels.length > 0) {
              this.selectedModel = availableModels[0].value;
            }
          }
        }
      } catch (error) {
        console.error("Failed to load AI settings:", error);
      }
    },

    isModelAvailable(modelName) {
      const availableModels = this.getAvailableModels();
      return availableModels.some((model) => model.value === modelName);
    },

    toggleModelSelector() {
      this.showModelSelector = !this.showModelSelector;

      if (this.showModelSelector) {
        // Check if dropdown would be cut off and position accordingly
        this.$nextTick(() => {
          const dropdown = this.$el.querySelector(".model-dropdown");
          const button = this.$el.querySelector(".model-selector-btn");

          if (dropdown && button) {
            const buttonRect = button.getBoundingClientRect();
            const viewportHeight = window.innerHeight;
            const dropdownHeight = Math.min(
              300,
              this.getAvailableModels().length * 40
            ); // estimated height

            // If there's not enough space below, show above
            if (buttonRect.bottom + dropdownHeight > viewportHeight - 20) {
              dropdown.classList.add("show-above");
            } else {
              dropdown.classList.remove("show-above");
            }
          }
        });
      }
    },

    getAvailableModels() {
      if (!this.aiSettings) return [];

      // Return all enabled models from providers with API keys
      const allModels = [];
      Object.keys(this.aiSettings.provider_configs).forEach((providerName) => {
        const config = this.aiSettings.provider_configs[providerName];
        if (config.has_api_key && config.enabled_models) {
          config.enabled_models.forEach((model) => {
            allModels.push({
              value: model,
              label: `${providerName}: ${model}`,
              provider: providerName,
            });
          });
        }
      });

      return allModels;
    },

    getCurrentModelLabel() {
      if (!this.aiSettings) return "Loading...";

      const allModels = this.getAvailableModels();
      if (allModels.length === 0) return "No models available";

      if (!this.selectedModel) return "Select model";

      const currentModel = allModels.find(
        (model) => model.value === this.selectedModel
      );

      return currentModel ? currentModel.label : this.selectedModel;
    },

    async selectModel(modelData) {
      try {
        this.selectedModel = modelData.value;
        this.showModelSelector = false;

        // Update user's default model with the correct provider
        const updateData = {
          provider: modelData.provider,
          model: modelData.value,
        };

        await window.apiService.updateAISettings(updateData);
        await this.loadAISettings(); // Refresh settings
      } catch (error) {
        console.error("Failed to update model:", error);
      }
    },

    openSettings() {
      // Emit event to parent to open settings modal with AI tab
      this.$emit("open-settings", "ai");
    },

    // Context management methods
    toggleContextArea() {
      this.showContextArea = !this.showContextArea;
    },

    removeContextBlock(blockId) {
      this.$emit("remove-context-block", blockId);
    },

    clearAllContext() {
      this.$emit("clear-context");
    },

    getContextPreview(block) {
      return block.content.length > 50
        ? block.content.substring(0, 50) + "..."
        : block.content;
    },

    getContextCount() {
      return this.chatContextBlocks.length;
    },

    hasContext() {
      return this.chatContextBlocks.length > 0;
    },
  },
  template: `
    <div class="chat-panel" :class="{ open: isOpen }" :style="isOpen ? { width: width + 'px' } : {}">
      <div class="chat-resize-handle" 
           :class="{ resizing: isResizing }"
           @mousedown="startResize">
      </div>
      <button class="chat-toggle" @click="togglePanel">ai</button>
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
        
        <!-- Context Area -->
        <div class="context-area" v-if="hasContext() || showContextArea">
          <div class="context-header">
            <span class="context-title">
              Context ({{ getContextCount() }})
            </span>
            <div class="context-actions">
              <button 
                v-if="hasContext()" 
                @click="clearAllContext" 
                class="context-clear-btn" 
                title="Clear all context"
              >
                ✕
              </button>
            </div>
          </div>
          <div class="context-blocks" v-if="hasContext()">
            <div 
              v-for="block in chatContextBlocks" 
              :key="block.uuid" 
              class="context-block"
            >
              <div class="context-block-content">
                {{ getContextPreview(block) }}
              </div>
              <button 
                @click="removeContextBlock(block.uuid)" 
                class="context-block-remove"
                title="Remove from context"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
        
        <div class="input-area">
          <div class="chat-controls">
            <div class="model-selector" v-if="aiSettings">
              <button 
                class="model-selector-btn" 
                @click="toggleModelSelector"
                :title="getCurrentModelLabel()"
              >
                {{ getCurrentModelLabel() }}
                <span class="dropdown-arrow">▼</span>
              </button>
              <div v-if="showModelSelector" class="model-dropdown">
                <div v-if="getAvailableModels().length === 0" class="model-option disabled">
                  No models available. Configure API keys in settings.
                </div>
                <div 
                  v-else
                  v-for="model in getAvailableModels()" 
                  :key="model.value"
                  class="model-option"
                  :class="{ active: model.value === selectedModel }"
                  @click="selectModel(model)"
                >
                  {{ model.label }}
                </div>
              </div>
            </div>
            <button 
              class="context-btn" 
              @click="toggleContextArea" 
              :class="{ active: hasContext() }"
              :title="hasContext() ? 'Context (' + getContextCount() + ')' : 'Add context'"
            >
              ctx
            </button>
            <button class="settings-btn" @click="openSettings" title="AI Settings">cfg</button>
          </div>
          <div class="message-input">
            <textarea v-model="message" placeholder="Ask something..." @keydown="handleKeydown"></textarea>
            <button @click="sendMessage" :disabled="loading">
              {{ loading ? 'sending...' : 'send' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
};

window.ChatPanel = ChatPanel;
