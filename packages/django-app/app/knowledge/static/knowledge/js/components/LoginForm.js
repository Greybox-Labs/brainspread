// Login Form Component
const LoginForm = {
  data() {
    return {
      email: "",
      password: "",
      loading: false,
      error: null,
      showRegister: false,
    };
  },

  methods: {
    async handleLogin() {
      this.loading = true;
      this.error = null;

      try {
        const result = await window.apiService.login(this.email, this.password);

        if (result.success) {
          this.$emit("login-success", result.data.user);
        } else {
          this.error = result.errors?.non_field_errors?.[0] || "login failed";
        }
      } catch (error) {
        console.error("login error:", error);
        this.error = "login failed. please try again.";
      } finally {
        this.loading = false;
      }
    },

    async handleRegister() {
      this.loading = true;
      this.error = null;

      try {
        const result = await window.apiService.register(
          this.email,
          this.password
        );

        if (result.success) {
          this.$emit("login-success", result.data.user);
        } else {
          this.error =
            result.errors?.email?.[0] ||
            result.errors?.non_field_errors?.[0] ||
            "registration failed";
        }
      } catch (error) {
        console.error("registration error:", error);
        this.error = "registration failed. please try again.";
      } finally {
        this.loading = false;
      }
    },

    toggleForm() {
      this.showRegister = !this.showRegister;
      this.error = null;
    },
  },

  template: `
        <div class="login-form">
            <h2>{{ showRegister ? 'register' : 'login' }}</h2>
            
            <form @submit.prevent="showRegister ? handleRegister() : handleLogin()">
                <div class="form-group">
                    <label for="email">email:</label>
                    <input 
                        id="email"
                        v-model="email" 
                        type="email" 
                        required 
                        class="form-control"
                        :disabled="loading"
                        placeholder="test@example.com"
                    />
                </div>
                
                <div class="form-group">
                    <label for="password">password:</label>
                    <input 
                        id="password"
                        v-model="password" 
                        type="password" 
                        required 
                        class="form-control"
                        :disabled="loading"
                        placeholder="testpass123"
                    />
                </div>
                
                <button type="submit" :disabled="loading" class="btn btn-primary">
                    {{ loading ? (showRegister ? 'registering...' : 'logging in...') : (showRegister ? 'register' : 'login') }}
                </button>
                
                <button type="button" @click="toggleForm" class="btn btn-link" :disabled="loading">
                    {{ showRegister ? 'already have an account? login' : 'need an account? register' }}
                </button>
            </form>
            
            <div v-if="error" class="alert alert-error">{{ error }}</div>
        </div>
    `,
};

// Register component globally
window.LoginForm = LoginForm;
