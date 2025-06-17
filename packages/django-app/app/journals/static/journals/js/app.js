const { createApp } = Vue;

// Global Vue app for journals
const JournalsApp = createApp({
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
    LoginForm: window.LoginForm,
  },

  async mounted() {
    console.log("Journals app mounted");
    await this.checkAuth();
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
  },

  template: `
        <div class="journals-app">
            <nav v-if="isAuthenticated" class="navbar">
                <div class="nav-content">
                    <h1>📔 Daily Journals</h1>
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
                    <JournalEntry />
                </div>
            </main>
        </div>
    `,
});

// Mount the app when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  JournalsApp.mount("#app");
});
