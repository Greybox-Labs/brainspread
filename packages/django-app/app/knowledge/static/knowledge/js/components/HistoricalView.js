window.HistoricalView = {
  data() {
    return {
      historicalData: null,
      loading: false,
      error: null,
      daysBack: 30,
      limit: 50,
    };
  },

  async mounted() {
    await this.loadHistoricalData();
  },

  methods: {
    async loadHistoricalData() {
      this.loading = true;
      this.error = null;

      try {
        const result = await window.apiService.getHistoricalData(
          this.daysBack,
          this.limit
        );

        if (result.success) {
          this.historicalData = result.data;
        } else {
          this.error = "Failed to load historical data";
        }
      } catch (error) {
        console.error("Error loading historical data:", error);
        this.error = error.message || "Failed to load historical data";
      } finally {
        this.loading = false;
      }
    },

    async updateFilter() {
      await this.loadHistoricalData();
    },

    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString();
    },

    formatTime(dateString) {
      return new Date(dateString).toLocaleTimeString();
    },

    truncateContent(content, maxLength = 100) {
      if (!content) return "";
      return content.length > maxLength
        ? content.substring(0, maxLength) + "..."
        : content;
    },

    getTagColors(tags) {
      if (!tags || !tags.length) return [];
      return tags.map((tag) => ({
        name: tag.name,
        color: tag.color || "#666",
      }));
    },
  },

  template: `
    <div class="historical-view">
      <div class="historical-header">
        <h2>Historical Pages & Blocks</h2>
        <div class="filter-controls">
          <label>
            Days back:
            <select v-model="daysBack" @change="updateFilter">
              <option value="7">7 days</option>
              <option value="30">30 days</option>
              <option value="90">90 days</option>
              <option value="365">1 year</option>
            </select>
          </label>
          <label>
            Limit:
            <select v-model="limit" @change="updateFilter">
              <option value="25">25 items</option>
              <option value="50">50 items</option>
              <option value="100">100 items</option>
            </select>
          </label>
        </div>
      </div>

      <div v-if="loading" class="loading">
        Loading historical data...
      </div>

      <div v-else-if="error" class="error">
        {{ error }}
      </div>

      <div v-else-if="historicalData" class="historical-content">
        <div class="date-range">
          Showing data from {{ formatDate(historicalData.date_range.start) }} 
          to {{ formatDate(historicalData.date_range.end) }}
        </div>

        <div class="historical-sections">
          <!-- Historical Pages -->
          <div class="section">
            <h3>Recent Pages ({{ historicalData.pages.length }})</h3>
            <div v-if="historicalData.pages.length === 0" class="empty-state">
              No pages found in the selected time range.
            </div>
            <div v-else class="pages-grid">
              <div 
                v-for="page in historicalData.pages" 
                :key="page.id" 
                class="page-card"
              >
                <div class="page-header">
                  <h4>{{ page.title }}</h4>
                  <div class="page-meta">
                    <span class="page-type">{{ page.page_type }}</span>
                    <span class="date">{{ formatDate(page.modified_at) }}</span>
                  </div>
                </div>
                <div v-if="page.content" class="page-content">
                  {{ truncateContent(page.content, 150) }}
                </div>
                <div v-if="page.recent_blocks && page.recent_blocks.length" class="recent-blocks">
                  <h5>Recent Blocks:</h5>
                  <div 
                    v-for="block in page.recent_blocks" 
                    :key="block.id"
                    class="block-preview"
                  >
                    <span class="block-type">{{ block.block_type }}</span>
                    <span class="block-content">{{ truncateContent(block.content, 80) }}</span>
                  </div>
                </div>
                <div v-if="page.tags && page.tags.length" class="tags">
                  <span 
                    v-for="tag in getTagColors(page.tags)" 
                    :key="tag.name"
                    class="tag"
                    :style="{ backgroundColor: tag.color }"
                  >
                    {{ tag.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Historical Blocks -->
          <div class="section">
            <h3>Recent Blocks ({{ historicalData.blocks.length }})</h3>
            <div v-if="historicalData.blocks.length === 0" class="empty-state">
              No blocks found in the selected time range.
            </div>
            <div v-else class="blocks-list">
              <div 
                v-for="block in historicalData.blocks" 
                :key="block.id" 
                class="block-card"
              >
                <div class="block-header">
                  <span class="block-type">{{ block.block_type }}</span>
                  <span class="page-title">{{ block.page_title }}</span>
                  <span class="date">{{ formatDate(block.modified_at) }}</span>
                </div>
                <div class="block-content">
                  {{ truncateContent(block.content, 200) }}
                </div>
                <div v-if="block.tags && block.tags.length" class="tags">
                  <span 
                    v-for="tag in getTagColors(block.tags)" 
                    :key="tag.name"
                    class="tag"
                    :style="{ backgroundColor: tag.color }"
                  >
                    {{ tag.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
};
