// Journal Entry Component
const JournalEntry = {
  data() {
    return {
      entryDate: new Date().toISOString().split("T")[0],
      content: "",
      tags: [],
      saving: false,
      loading: false,
      error: null,
      successMessage: "",
    };
  },

  async mounted() {
    await this.loadEntry();
  },

  methods: {
    async loadEntry() {
      this.loading = true;
      this.error = null;

      try {
        const result = await window.apiService.getEntry(this.entryDate);
        if (result.success && result.data) {
          this.content = result.data.content || "";
          this.tags = result.data.tags || [];
        } else {
          this.content = "";
          this.tags = [];
        }
      } catch (error) {
        console.error("Failed to load entry:", error);
        this.error = "Failed to load journal entry";
      } finally {
        this.loading = false;
      }
    },

    async saveEntry() {
      this.saving = true;
      this.error = null;
      this.successMessage = "";

      try {
        const result = await window.apiService.createOrUpdateEntry(
          this.entryDate,
          this.content
        );

        if (result.success) {
          this.tags = result.data.tags || [];
          this.successMessage = "Entry saved successfully!";
          setTimeout(() => {
            this.successMessage = "";
          }, 3000);
        } else {
          this.error = "Failed to save entry";
        }
      } catch (error) {
        console.error("Failed to save entry:", error);
        this.error = "Failed to save journal entry";
      } finally {
        this.saving = false;
      }
    },

    async onDateChange() {
      await this.loadEntry();
    },

    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString();
    },
  },

  template: `
        <div class="journal-entry">
            <h2>Journal Entry for {{ formatDate(entryDate) }}</h2>
            
            <div v-if="loading" class="loading">Loading...</div>
            
            <form v-else @submit.prevent="saveEntry">
                <div class="form-group">
                    <label for="entry-date">Date:</label>
                    <input 
                        id="entry-date"
                        v-model="entryDate" 
                        type="date" 
                        @change="onDateChange"
                        class="form-control"
                    />
                </div>
                
                <div class="form-group">
                    <label for="content">Content:</label>
                    <textarea 
                        id="content"
                        v-model="content" 
                        rows="15" 
                        placeholder="Write your journal entry... Use #tags for tagging"
                        class="form-control content-textarea"
                    ></textarea>
                </div>
                
                <button type="submit" :disabled="saving" class="btn btn-primary">
                    {{ saving ? 'Saving...' : 'Save Entry' }}
                </button>
            </form>

            <div v-if="tags.length" class="tags-section">
                <h3>Tags:</h3>
                <span 
                    v-for="tag in tags" 
                    :key="tag.name" 
                    class="tag" 
                    :style="{ backgroundColor: tag.color }"
                >
                    #{{ tag.name }}
                </span>
            </div>

            <div v-if="error" class="alert alert-error">{{ error }}</div>
            <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>
        </div>
    `,
};

// Register component globally
window.JournalEntry = JournalEntry;
