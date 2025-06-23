// Settings Modal Component
window.SettingsModal = {
  props: {
    isOpen: {
      type: Boolean,
      default: false,
    },
    user: {
      type: Object,
      required: true,
    },
  },

  emits: ["close", "theme-updated"],

  data() {
    return {
      selectedTheme: this.user?.theme || "dark",
      isUpdating: false,
    };
  },

  watch: {
    user: {
      handler(newUser) {
        if (newUser?.theme) {
          this.selectedTheme = newUser.theme;
        }
      },
      deep: true,
    },
  },

  methods: {
    selectTheme(theme) {
      this.selectedTheme = theme;
    },

    async saveSettings() {
      if (this.isUpdating) return;

      try {
        this.isUpdating = true;

        if (this.selectedTheme !== this.user.theme) {
          const result = await window.apiService.updateUserTheme(
            this.selectedTheme
          );

          if (result.success) {
            // Apply theme immediately
            this.applyTheme(this.selectedTheme);

            // Emit theme update event
            this.$emit("theme-updated", result.data.user);

            console.log("Theme updated successfully");
          } else {
            console.error("Failed to update theme:", result.errors);
            alert("Failed to update theme. Please try again.");
          }
        }

        this.closeModal();
      } catch (error) {
        console.error("Error updating settings:", error);
        alert("Failed to update settings. Please try again.");
      } finally {
        this.isUpdating = false;
      }
    },

    closeModal() {
      this.$emit("close");
    },

    applyTheme(theme) {
      // Apply theme to document root
      document.documentElement.setAttribute("data-theme", theme);
    },

    // Handle click outside modal to close
    handleBackdropClick(event) {
      if (event.target === event.currentTarget) {
        this.closeModal();
      }
    },
  },

  template: `
    <div 
      v-if="isOpen" 
      class="settings-modal" 
      @click="handleBackdropClick"
    >
      <div class="settings-modal-content">
        <h2>Settings</h2>
        
        <div class="settings-section">
          <h3>Theme</h3>
          <div class="theme-options">
            <button 
              class="theme-option"
              :class="{ active: selectedTheme === 'dark' }"
              @click="selectTheme('dark')"
              type="button"
            >
              Dark
            </button>
            <button 
              class="theme-option"
              :class="{ active: selectedTheme === 'light' }"
              @click="selectTheme('light')"
              type="button"
            >
              Light
            </button>
          </div>
        </div>

        <div class="modal-actions">
          <button 
            class="btn btn-outline" 
            @click="closeModal"
            :disabled="isUpdating"
            type="button"
          >
            Cancel
          </button>
          <button 
            class="btn btn-primary" 
            @click="saveSettings"
            :disabled="isUpdating"
            type="button"
          >
            {{ isUpdating ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  `,
};
