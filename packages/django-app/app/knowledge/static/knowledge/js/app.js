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
    };
  },

  components: {
    DailyNote: window.DailyNote,
    LoginForm: window.LoginForm,
    HistoricalSidebar: window.HistoricalSidebar,
    HistoricalDailyNoteBlocks: window.HistoricalDailyNoteBlocks,
  },

  async mounted() {
    console.log("Knowledge app mounted");
    
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

    switchView(view) {
      this.currentView = view;
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
                        <h1>brainspreader</h1>
                        <div class="nav-right">
                            <span class="user-info">Hello, {{ user?.email }}</span>
                            <button @click="handleLogout" class="btn btn-outline">logout</button>
                        </div>
                    </div>
                </nav>

                <main class="main-content">
                    <div v-if="loading" class="loading-container">
                        <div class="loading">Loading...</div>
                    </div>
                    <div v-else class="content-layout">
                        <HistoricalSidebar @navigate-to-date="onNavigateToDate" />
                        <div class="main-content-area">
                            <DailyNote ref="dailyNote" />
                        </div>
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
    `,
});

// Mount the app when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  KnowledgeApp.mount("#app");
});
