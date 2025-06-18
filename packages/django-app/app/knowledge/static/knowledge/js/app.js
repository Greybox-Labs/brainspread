const { createApp } = Vue;

// Global Vue app for knowledge base
const KnowledgeApp = createApp({
  data() {
    return {
      user: null,
      isAuthenticated: false,
      currentView: "journal", // 'journal' or 'login'
      loading: true,
    };
  },

  components: {
    JournalEntry: window.JournalEntry,
    DailyNote: window.DailyNote,
    LoginForm: window.LoginForm,
  },

  async mounted() {
    console.log("Knowledge app mounted");
    await this.checkAuth();
    
    // Check for timezone changes after authentication
    if (this.isAuthenticated) {
      this.checkTimezoneChange();
    }
  },

  methods: {
    async checkAuth() {
      this.loading = true;

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
          console.log('Timezone updated successfully');
          // Optionally reload the page to refresh with new timezone
          // window.location.reload();
        }
      } catch (error) {
        console.error('Failed to update timezone:', error);
        alert('Failed to update timezone. Please try again.');
      }
    },
  },

  template: `
        <div class="journals-app">
            <nav v-if="isAuthenticated" class="navbar">
                <div class="nav-content">
                    <h1>🧠 Knowledge Base</h1>
                    <div class="nav-right">
                        <span class="user-info">Hello, {{ user?.email }}</span>
                        <button @click="handleLogout" class="btn btn-outline">Logout</button>
                    </div>
                </div>
            </nav>
            
            <main class="main-content">
                <div v-if="loading" class="loading-container">
                    <div class="loading">Loading...</div>
                </div>
                
                <div v-else-if="!isAuthenticated" class="auth-container">
                    <LoginForm @login-success="onLoginSuccess" />
                </div>
                
                <div v-else class="journal-container">
                    <DailyNote />
                </div>
            </main>
        </div>
    `,
});

// Mount the app when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  KnowledgeApp.mount("#app");
});
