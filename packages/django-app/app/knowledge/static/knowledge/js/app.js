const { createApp } = Vue;

// Global Vue app for knowledge base
const KnowledgeApp = createApp({
  data() {
    const isAuth = window.apiService.isAuthenticated();
    const cachedUser = window.apiService.getCurrentUser();

    return {
      user: cachedUser, // Load user immediately from cache
      isAuthenticated: isAuth, // Check immediately
      currentView: isAuth ? "journal" : "login", // Set view immediately
      loading: isAuth && !cachedUser, // Only show loading if we have token but no cached user
      showSettings: false, // Settings modal state
      settingsActiveTab: "general", // Default tab for settings modal
      // Chat context management
      chatContextBlocks: [], // Array of blocks in chat context
      visibleBlocks: [], // Array of currently visible blocks
    };
  },

  components: {
    DailyNote: window.DailyNote,
    LoginForm: window.LoginForm,
    HistoricalSidebar: window.HistoricalSidebar,
    HistoricalDailyNoteBlocks: window.HistoricalDailyNoteBlocks,
    SettingsModal: window.SettingsModal,
    ChatPanel: window.ChatPanel,
  },

  async mounted() {
    console.log("Knowledge app mounted");

    // Apply initial theme
    this.applyTheme();

    // If we have cached user data, we can show the app immediately
    if (this.isAuthenticated && this.user) {
      this.loading = false;
    }

    // Then verify with server (this happens in background)
    await this.checkAuth();

    // Check for timezone changes after authentication
    if (this.isAuthenticated) {
      this.checkTimezoneChange();
    }

    // Reapply theme after auth check in case user data was updated
    this.applyTheme();
  },

  methods: {
    async checkAuth() {
      // Only set loading if we're not already authenticated
      if (!this.isAuthenticated) {
        this.loading = true;
      }

      if (window.apiService.isAuthenticated()) {
        try {
          const result = await window.apiService.me();
          if (result.success) {
            this.user = result.data.user;
            this.isAuthenticated = true;
            this.currentView = "journal";
          } else {
            this.handleLogout();
          }
        } catch (error) {
          console.error("Auth check failed:", error);
          this.handleLogout();
        }
      } else {
        this.currentView = "login";
        this.isAuthenticated = false;
      }

      this.loading = false;
    },

    onLoginSuccess(user) {
      this.user = user;
      this.isAuthenticated = true;
      this.currentView = "journal";

      // Check timezone after login (with a small delay to ensure user data is updated)
      setTimeout(() => {
        this.checkTimezoneChange();
      }, 1000);
    },

    async handleLogout() {
      try {
        await window.apiService.logout();
      } catch (error) {
        console.error("Logout error:", error);
      } finally {
        this.user = null;
        this.isAuthenticated = false;
        this.currentView = "login";
      }
    },

    checkTimezoneChange() {
      if (window.apiService.checkTimezoneChange()) {
        const browserTimezone = window.apiService.getCurrentBrowserTimezone();
        const currentUser = window.apiService.getCurrentUser();

        const message = `Your device's timezone appears to have changed from ${currentUser.timezone} to ${browserTimezone}. Would you like to update your timezone preference?`;

        if (confirm(message)) {
          this.updateTimezone(browserTimezone);
        }
      }
    },

    async updateTimezone(newTimezone) {
      try {
        const result = await window.apiService.updateUserTimezone(newTimezone);
        if (result.success) {
          console.log("Timezone updated successfully");
          // Optionally reload the page to refresh with new timezone
          // window.location.reload();
        }
      } catch (error) {
        console.error("Failed to update timezone:", error);
        alert("Failed to update timezone. Please try again.");
      }
    },

    onNavigateToDate(date) {
      // Navigate to the daily note URL
      window.location.href = `/knowledge/daily/${date}/`;
    },

    // Theme and settings methods
    openSettings(activeTab = "general") {
      this.settingsActiveTab = activeTab;
      this.showSettings = true;
    },

    closeSettings() {
      this.showSettings = false;
      this.settingsActiveTab = "general"; // Reset to default
    },

    onChatPanelOpenSettings(activeTab) {
      this.openSettings(activeTab);
    },

    onThemeUpdated(updatedUser) {
      // Update user data with new theme
      this.user = { ...this.user, ...updatedUser };

      // Apply the new theme
      this.applyTheme();
    },

    applyTheme() {
      const theme = this.user?.theme || "dark";
      document.documentElement.setAttribute("data-theme", theme);
    },

    // Chat context management methods
    addBlockToContext(block, parentUuid = null) {
      // Don't add if already in context
      if (!this.chatContextBlocks.find((b) => b.uuid === block.uuid)) {
        this.chatContextBlocks.push({
          uuid: block.uuid,
          content: block.content,
          block_type: block.block_type,
          created_at: block.created_at,
          parent_uuid: parentUuid,
        });
      }

      // Recursively add all child blocks
      if (block.children && block.children.length) {
        block.children.forEach((child) => {
          this.addBlockToContext(child, block.uuid);
        });
      }
    },

    removeBlockFromContext(blockUuid) {
      // Get all block UUIDs to remove (block + all descendants)
      const uuidsToRemove = this.getBlockAndDescendantUuids(blockUuid);

      // Remove all blocks (parent + descendants) from context
      this.chatContextBlocks = this.chatContextBlocks.filter(
        (b) => !uuidsToRemove.includes(b.uuid)
      );
    },

    getBlockAndDescendantUuids(blockUuid) {
      const uuidsToRemove = [blockUuid];

      // Use the stored parent relationships to find descendants
      const findDescendantsInContext = (parentUuid) => {
        const children = this.chatContextBlocks.filter(
          (block) => block.parent_uuid === parentUuid
        );

        children.forEach((child) => {
          uuidsToRemove.push(child.uuid);
          // Recursively find grandchildren
          findDescendantsInContext(child.uuid);
        });
      };

      // Find all descendants using the context relationships
      findDescendantsInContext(blockUuid);

      return uuidsToRemove;
    },

    isBlockInContext(blockUuid) {
      return this.chatContextBlocks.some((b) => b.uuid === blockUuid);
    },

    clearChatContext() {
      this.chatContextBlocks = [];
    },

    updateVisibleBlocks(blocks) {
      this.visibleBlocks = blocks;
    },

    onBlockAddToContext(block) {
      this.addBlockToContext(block);
    },

    onBlockRemoveFromContext(blockId) {
      this.removeBlockFromContext(blockId);
    },
  },

  template: `
        <div class="journals-app" :class="{ 'initial-load': loading && !user }">
            <!-- Show loading during initial auth check to prevent login flash -->
            <div v-if="loading && !user" class="loading-container" style="min-height: 100vh; display: flex; align-items: center; justify-content: center;">
                <div class="loading">Loading...</div>
            </div>

            <!-- Authenticated state -->
            <div v-else-if="isAuthenticated">
                <nav class="navbar">
                    <div class="nav-content">
                        <h1><a href="/knowledge/" class="brand-link">brainspread</a></h1>
                        <div class="nav-right">
                            <span class="user-info">Hello, {{ user?.email }}</span>
                            <button @click="openSettings()" class="settings-btn">settings</button>
                            <button @click="handleLogout" class="btn btn-outline">LOGOUT</button>
                        </div>
                    </div>
                </nav>

                <main class="main-content">
                    <div v-if="loading" class="loading-container">
                        <div class="loading">Loading...</div>
                    </div>
                    <div v-else class="content-layout">
                        <HistoricalSidebar v-if="!$refs.dailyNote?.isTagPage" @navigate-to-date="onNavigateToDate" />
                        <div class="main-content-area">
                            <DailyNote
                                ref="dailyNote"
                                :chat-context-blocks="chatContextBlocks"
                                :is-block-in-context="isBlockInContext"
                                @block-add-to-context="onBlockAddToContext"
                                @block-remove-from-context="onBlockRemoveFromContext"
                                @visible-blocks-changed="updateVisibleBlocks"
                            />
                        </div>
                        <ChatPanel
                            :chat-context-blocks="chatContextBlocks"
                            :visible-blocks="visibleBlocks"
                            @open-settings="onChatPanelOpenSettings"
                            @remove-context-block="onBlockRemoveFromContext"
                            @clear-context="clearChatContext"
                        />
                    </div>
                </main>
            </div>

            <!-- Login state -->
            <main v-else class="main-content">
                <div class="auth-container">
                    <LoginForm @login-success="onLoginSuccess" />
                </div>
            </main>
        </div>

        <!-- Settings Modal -->
        <SettingsModal
            :is-open="showSettings"
            :user="user"
            :active-tab="settingsActiveTab"
            @close="closeSettings"
            @theme-updated="onThemeUpdated"
        />
    `,
});

// Mount the app when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  KnowledgeApp.mount("#app");
});
