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
    activeTab: {
      type: String,
      default: "general",
    },
  },

  emits: ["close", "theme-updated"],

  data() {
    return {
      selectedTheme: this.user?.theme || "dark",
      selectedTimezone: this.user?.timezone || "UTC",
      isUpdating: false,
      aiSettings: null,
      loadingAISettings: false,
      currentTab: this.activeTab || "general",
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
    activeTab: {
      handler(newTab) {
        this.currentTab = newTab || "general";
      },
      immediate: true,
    },
    isOpen: {
      async handler(newValue) {
        if (newValue) {
          this.currentTab = this.activeTab || "general";
          await this.loadAISettings();
        }
      },
    },
  },

  async mounted() {
    if (this.isOpen) {
      await this.loadAISettings();
    }
  },

  methods: {
    selectTheme(theme) {
      this.selectedTheme = theme;
      // Apply theme immediately so user can see the change
      this.applyTheme(theme);
    },

    selectTimezone(timezone) {
      this.selectedTimezone = timezone;
    },

    async saveSettings() {
      if (this.isUpdating) return;

      try {
        this.isUpdating = true;
        let hasUpdates = false;

        // Save general settings
        if (this.currentTab === "general") {
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
        }

        // Save AI settings
        if (this.currentTab === "ai") {
          await this.saveAISettings();
          hasUpdates = true;
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

    switchTab(tab) {
      this.currentTab = tab;
    },

    async loadAISettings() {
      if (this.loadingAISettings || this.aiSettings) return;

      try {
        this.loadingAISettings = true;
        const result = await window.apiService.getAISettings();
        if (result.success) {
          this.aiSettings = result.data;

          // Initialize form data
          this.aiSettings.formData = {
            selectedProvider: this.aiSettings.current_provider || "",
            selectedModel: this.aiSettings.current_model || "",
            apiKeys: {},
            enabledModels: {},
          };

          // Initialize API keys and enabled models from provider configs
          Object.keys(this.aiSettings.provider_configs).forEach(
            (providerName) => {
              const config = this.aiSettings.provider_configs[providerName];
              this.aiSettings.formData.apiKeys[providerName] = "";
              this.aiSettings.formData.enabledModels[providerName] =
                config.enabled_models || [];
            }
          );
        }
      } catch (error) {
        console.error("Failed to load AI settings:", error);
      } finally {
        this.loadingAISettings = false;
      }
    },

    async saveAISettings() {
      if (!this.aiSettings) return;

      try {
        this.isUpdating = true;

        // Only include API keys that have been entered (not empty)
        const apiKeys = {};
        Object.keys(this.aiSettings.formData.apiKeys).forEach(
          (providerName) => {
            const apiKey = this.aiSettings.formData.apiKeys[providerName];
            if (apiKey && apiKey.trim() !== "") {
              apiKeys[providerName] = apiKey;
            }
          }
        );

        const updateData = {
          provider: this.aiSettings.formData.selectedProvider,
          model: this.aiSettings.formData.selectedModel,
          api_keys: apiKeys,
          provider_configs: {},
        };

        // Build provider configs
        Object.keys(this.aiSettings.formData.enabledModels).forEach(
          (providerName) => {
            updateData.provider_configs[providerName] = {
              is_enabled: true,
              enabled_models:
                this.aiSettings.formData.enabledModels[providerName],
            };
          }
        );

        const result = await window.apiService.updateAISettings(updateData);
        if (result.success) {
          console.log("AI settings updated successfully");
        } else {
          console.error("Failed to update AI settings:", result.errors);
          alert("Failed to update AI settings. Please try again.");
        }
      } catch (error) {
        console.error("Error updating AI settings:", error);
        alert("Failed to update AI settings. Please try again.");
      }
    },

    getAvailableModels(providerName) {
      if (!this.aiSettings) return [];
      const provider = this.aiSettings.providers.find(
        (p) => p.name === providerName
      );
      return provider ? provider.models : [];
    },

    getAllEnabledModels() {
      if (!this.aiSettings) return [];

      // Return all enabled models from providers with API keys
      const allModels = [];
      Object.keys(this.aiSettings.provider_configs).forEach((providerName) => {
        const config = this.aiSettings.provider_configs[providerName];
        if (config.has_api_key && config.enabled_models) {
          config.enabled_models.forEach((model) => {
            allModels.push({
              value: model,
              label: `${providerName}: ${model}`,
              provider: providerName,
            });
          });
        }
      });

      return allModels;
    },

    onModelChange() {
      // When a model is selected, automatically set the provider
      if (this.aiSettings.formData.selectedModel) {
        const selectedModelData = this.getAllEnabledModels().find(
          (model) => model.value === this.aiSettings.formData.selectedModel
        );
        if (selectedModelData) {
          this.aiSettings.formData.selectedProvider =
            selectedModelData.provider;
        }
      } else {
        this.aiSettings.formData.selectedProvider = "";
      }
    },

    toggleModel(providerName, model) {
      if (!this.aiSettings.formData.enabledModels[providerName]) {
        this.aiSettings.formData.enabledModels[providerName] = [];
      }

      const enabledModels =
        this.aiSettings.formData.enabledModels[providerName];
      const index = enabledModels.indexOf(model);

      if (index > -1) {
        enabledModels.splice(index, 1);
      } else {
        enabledModels.push(model);
      }
    },

    isModelEnabled(providerName, model) {
      if (
        !this.aiSettings ||
        !this.aiSettings.formData.enabledModels[providerName]
      ) {
        return false;
      }
      return this.aiSettings.formData.enabledModels[providerName].includes(
        model
      );
    },
  },

  template: `
    <div
      v-if="isOpen"
      class="settings-modal"
      @click="handleBackdropClick"
    >
      <div class="settings-modal-content">
        <h2>settings</h2>

        <div class="settings-tabs">
          <button
            :class="{ active: currentTab === 'general' }"
            @click="switchTab('general')"
            type="button"
          >
          general
          </button>
          <button
            :class="{ active: currentTab === 'ai' }"
            @click="switchTab('ai')"
            type="button"
          >
            ai
          </button>
        </div>

        <div v-if="currentTab === 'general'" class="tab-content">
          <div class="settings-section">
            <h3>theme</h3>
            <div class="theme-selector">
              <select
                v-model="selectedTheme"
                class="theme-select"
                @change="selectTheme($event.target.value)"
              >
                <option value="dark">dark</option>
                <option value="light">light</option>
                <option value="solarized_dark">solarized dark</option>
                <option value="purple">purple</option>
                <option value="earthy">earthy</option>
                <option value="forest">forest</option>
              </select>
            </div>
          </div>

          <div class="settings-section">
            <h3>time zone</h3>
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
        </div>

        <div v-if="currentTab === 'ai'" class="tab-content">
          <div v-if="loadingAISettings" class="loading">
            loading ai settings...
          </div>

          <div v-else-if="aiSettings" class="ai-settings">
            <div class="settings-section">
              <h3>model</h3>
              <div class="model-selection">
                <label>default model:</label>
                <select v-model="aiSettings.formData.selectedModel" @change="onModelChange">
                  <option value="">select model</option>
                  <option
                    v-for="model in getAllEnabledModels()"
                    :key="model.value"
                    :value="model.value"
                  >
                    {{ model.label }}
                  </option>
                </select>
              </div>
            </div>

            <div class="settings-section">
              <h3>api keys</h3>
              <div v-for="provider in aiSettings.providers" :key="provider.name" class="api-key-input">
                <label>{{ provider.name }} api key:</label>
                <input
                  type="password"
                  v-model="aiSettings.formData.apiKeys[provider.name]"
                  :placeholder="aiSettings.provider_configs[provider.name]?.has_api_key ? 'api key configured' : 'enter api key'"
                />
              </div>
            </div>

            <div class="settings-section">
              <h3>available models</h3>
              <div v-for="provider in aiSettings.providers" :key="provider.name" class="provider-models">
                <h4>{{ provider.name }}</h4>
                <div class="model-checkboxes">
                  <label v-for="model in provider.models" :key="model" class="model-checkbox">
                    <input
                      type="checkbox"
                      :checked="isModelEnabled(provider.name, model)"
                      @change="toggleModel(provider.name, model)"
                    />
                    {{ model }}
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button
            class="btn btn-outline"
            @click="closeModal"
            :disabled="isUpdating"
            type="button"
          >
            cancel
          </button>
          <button
            class="btn btn-primary"
            @click="saveSettings"
            :disabled="isUpdating"
            type="button"
          >
            {{ isUpdating ? 'saving...' : 'save' }}
          </button>
        </div>
      </div>
    </div>
  `,
};
