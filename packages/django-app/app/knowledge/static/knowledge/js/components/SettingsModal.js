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
      selectedTimezone: this.user?.timezone || "UTC",
      isUpdating: false,
      commonTimezones: [
        "UTC",
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Phoenix",
        "America/Anchorage",
        "America/Honolulu",
        "America/Toronto",
        "America/Vancouver",
        "America/Mexico_City",
        "America/Sao_Paulo",
        "America/Argentina/Buenos_Aires",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Europe/Rome",
        "Europe/Madrid",
        "Europe/Amsterdam",
        "Europe/Stockholm",
        "Europe/Moscow",
        "Africa/Cairo",
        "Africa/Johannesburg",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Asia/Hong_Kong",
        "Asia/Singapore",
        "Asia/Seoul",
        "Asia/Mumbai",
        "Asia/Dubai",
        "Asia/Bangkok",
        "Australia/Sydney",
        "Australia/Melbourne",
        "Australia/Perth",
        "Pacific/Auckland",
        "Pacific/Honolulu",
      ],
    };
  },

  watch: {
    user: {
      handler(newUser) {
        if (newUser?.theme) {
          this.selectedTheme = newUser.theme;
        }
        if (newUser?.timezone) {
          this.selectedTimezone = newUser.timezone;
        }
      },
      deep: true,
    },
  },

  methods: {
    selectTheme(theme) {
      this.selectedTheme = theme;
    },

    selectTimezone(timezone) {
      this.selectedTimezone = timezone;
    },

    async saveSettings() {
      if (this.isUpdating) return;

      try {
        this.isUpdating = true;
        let hasUpdates = false;

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
            hasUpdates = true;
          } else {
            console.error("Failed to update theme:", result.errors);
            alert("Failed to update theme. Please try again.");
            return;
          }
        }

        if (this.selectedTimezone !== this.user.timezone) {
          const result = await window.apiService.updateUserTimezone(
            this.selectedTimezone
          );

          if (result.success) {
            console.log("Timezone updated successfully");
            hasUpdates = true;
          } else {
            console.error("Failed to update timezone:", result.errors);
            alert("Failed to update timezone. Please try again.");
            return;
          }
        }

        if (hasUpdates) {
          // Refresh user data to get updated values
          await window.apiService.getCurrentUser();
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

        <div class="settings-section">
          <h3>Time Zone</h3>
          <div class="timezone-selector">
            <select 
              v-model="selectedTimezone"
              class="timezone-select"
              @change="selectTimezone($event.target.value)"
            >
              <option 
                v-for="timezone in commonTimezones"
                :key="timezone"
                :value="timezone"
              >
                {{ timezone.replace('_', ' ') }}
              </option>
            </select>
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
