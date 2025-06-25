const ChatPanel = {
  name: "ChatPanel",
  data() {
    return {
      isOpen: false,
      message: "",
      messages: [],
      loading: false,
    };
  },
  methods: {
    togglePanel() {
      this.isOpen = !this.isOpen;
    },
    async sendMessage() {
      if (!this.message) return;
      const userMsg = { role: "user", content: this.message };
      this.messages.push(userMsg);
      const payload = { message: this.message, api_key: this.$root.user?.api_key };
      this.message = "";
      this.loading = true;
      try {
        const result = await window.apiService.sendAIMessage(payload);
        if (result.success) {
          this.messages.push({ role: "assistant", content: result.data.response });
        }
      } catch (err) {
        console.error(err);
      } finally {
        this.loading = false;
      }
    },
  },
  template: `
    <div class="chat-panel" :class="{ open: isOpen }">
      <button class="chat-toggle" @click="togglePanel">AI</button>
      <div class="chat-content">
        <div class="messages">
          <div v-for="(msg, index) in messages" :key="index" :class="['msg', msg.role]">
            <pre>{{ msg.content }}</pre>
          </div>
        </div>
        <div class="input-area">
          <textarea v-model="message" placeholder="Ask something..."></textarea>
          <button @click="sendMessage" :disabled="loading">Send</button>
        </div>
      </div>
    </div>
  `,
};

window.ChatPanel = ChatPanel;
