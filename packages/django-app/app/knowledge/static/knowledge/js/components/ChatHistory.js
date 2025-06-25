const ChatHistory = {
  name: "ChatHistory",
  data() {
    return {
      sessions: [],
      loading: false,
      error: null,
      isOpen: false,
    };
  },
  async mounted() {
    await this.loadSessions();
  },
  methods: {
    async loadSessions() {
      this.loading = true;
      this.error = null;
      try {
        const result = await window.apiService.getChatSessions();
        if (result.success) {
          this.sessions = result.data;
        }
      } catch (error) {
        console.error("Failed to load chat sessions:", error);
        this.error = "Failed to load chat history";
      } finally {
        this.loading = false;
      }
    },
    toggleHistory() {
      this.isOpen = !this.isOpen;
    },
    async selectSession(session) {
      this.$emit("session-selected", session);
      this.isOpen = false; // Close the history panel after selecting a session
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString();
    },
  },
  template: `
    <div class="chat-history">
      <button class="history-toggle" @click="toggleHistory">
        History ({{ sessions.length }})
      </button>
      <teleport to=".chat-panel" v-if="isOpen">
        <div class="history-dropdown">
          <div class="history-header">
            <h3>Chat History</h3>
            <button class="close-btn" @click="toggleHistory">×</button>
          </div>
          <div class="history-content">
            <div v-if="loading" class="loading">Loading...</div>
            <div v-else-if="error" class="error">{{ error }}</div>
            <div v-else-if="sessions.length === 0" class="empty">No chat history yet</div>
            <div v-else class="sessions-list">
              <div 
                v-for="session in sessions" 
                :key="session.uuid" 
                class="session-item"
                @click="selectSession(session)"
              >
                <div class="session-title">{{ session.title }}</div>
                <div class="session-preview">{{ session.preview }}</div>
                <div class="session-meta">
                  <span class="session-date">{{ formatDate(session.modified_at) }}</span>
                  <span class="session-count">{{ session.message_count }} messages</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </teleport>
    </div>
  `,
};

window.ChatHistory = ChatHistory;
