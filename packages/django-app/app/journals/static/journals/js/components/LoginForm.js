// Login Form Component
const LoginForm = {
    data() {
        return {
            email: 'test@example.com', // Pre-filled for testing
            password: 'testpass123',   // Pre-filled for testing
            loading: false,
            error: null,
            showRegister: false
        }
    },
    
    methods: {
        async handleLogin() {
            this.loading = true;
            this.error = null;
            
            try {
                const result = await window.apiService.login(this.email, this.password);
                
                if (result.success) {
                    this.$emit('login-success', result.data.user);
                } else {
                    this.error = result.errors?.non_field_errors?.[0] || 'Login failed';
                }
            } catch (error) {
                console.error('Login error:', error);
                this.error = 'Login failed. Please try again.';
            } finally {
                this.loading = false;
            }
        },

        async handleRegister() {
            this.loading = true;
            this.error = null;
            
            try {
                const result = await window.apiService.register(this.email, this.password);
                
                if (result.success) {
                    this.$emit('login-success', result.data.user);
                } else {
                    this.error = result.errors?.email?.[0] || result.errors?.non_field_errors?.[0] || 'Registration failed';
                }
            } catch (error) {
                console.error('Registration error:', error);
                this.error = 'Registration failed. Please try again.';
            } finally {
                this.loading = false;
            }
        },

        toggleForm() {
            this.showRegister = !this.showRegister;
            this.error = null;
        }
    },
    
    template: `
        <div class="login-form">
            <h2>{{ showRegister ? 'Register' : 'Login' }}</h2>
            
            <form @submit.prevent="showRegister ? handleRegister() : handleLogin()">
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input 
                        id="email"
                        v-model="email" 
                        type="email" 
                        required 
                        class="form-control"
                        :disabled="loading"
                    />
                </div>
                
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input 
                        id="password"
                        v-model="password" 
                        type="password" 
                        required 
                        class="form-control"
                        :disabled="loading"
                    />
                </div>
                
                <button type="submit" :disabled="loading" class="btn btn-primary">
                    {{ loading ? (showRegister ? 'Registering...' : 'Logging in...') : (showRegister ? 'Register' : 'Login') }}
                </button>
                
                <button type="button" @click="toggleForm" class="btn btn-link" :disabled="loading">
                    {{ showRegister ? 'Already have an account? Login' : 'Need an account? Register' }}
                </button>
            </form>
            
            <div v-if="error" class="alert alert-error">{{ error }}</div>
        </div>
    `
};

// Register component globally
window.LoginForm = LoginForm;