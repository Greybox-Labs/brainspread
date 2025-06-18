window.HistoricalSidebar = {
  data() {
    return {
      historicalData: null,
      loading: false,
      error: null,
      daysBack: 30,
      limit: 25,
      isOpen: false,
      width: 400,
      isResizing: false,
      minWidth: 300,
      maxWidth: 800,
    };
  },

  mounted() {
    this.loadHistoricalData();
    this.setupResizeListener();
  },

  beforeUnmount() {
    this.removeResizeListener();
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

    toggleSidebar() {
      this.isOpen = !this.isOpen;
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
        color: tag.color || "#00ff00",
      }));
    },

    // Resize functionality
    setupResizeListener() {
      this.resizeHandler = (e) => this.handleMouseMove(e);
      this.stopResizeHandler = () => this.stopResize();
    },

    removeResizeListener() {
      if (this.resizeHandler) {
        document.removeEventListener('mousemove', this.resizeHandler);
        document.removeEventListener('mouseup', this.stopResizeHandler);
      }
    },

    startResize(e) {
      this.isResizing = true;
      this.startX = e.clientX;
      this.startWidth = this.width;
      
      document.addEventListener('mousemove', this.resizeHandler);
      document.addEventListener('mouseup', this.stopResizeHandler);
      
      e.preventDefault();
    },

    handleMouseMove(e) {
      if (!this.isResizing) return;
      
      const deltaX = e.clientX - this.startX;
      const newWidth = this.startWidth - deltaX; // Subtract because we're resizing from the left edge
      
      if (newWidth >= this.minWidth && newWidth <= this.maxWidth) {
        this.width = newWidth;
      }
    },

    stopResize() {
      this.isResizing = false;
      document.removeEventListener('mousemove', this.resizeHandler);
      document.removeEventListener('mouseup', this.stopResizeHandler);
    },
  },

  template: `
    <div class="historical-sidebar-container">
      <!-- Sidebar Toggle Button -->
      <button 
        @click="toggleSidebar" 
        class="sidebar-toggle-btn"
        :class="{ active: isOpen }"
        title="Toggle History Sidebar"
      >
        <span v-if="isOpen">←</span>
        <span v-else>→</span>
        History
      </button>

      <!-- Sidebar -->
      <div 
        v-if="isOpen"
        class="historical-sidebar"
        :style="{ width: width + 'px' }"
      >
        <!-- Resize Handle -->
        <div 
          class="sidebar-resize-handle"
          @mousedown="startResize"
          :class="{ resizing: isResizing }"
        ></div>

        <div class="sidebar-content">
          <div class="sidebar-header">
            <h3>History</h3>
            <div class="filter-controls">
              <label>
                Days:
                <select v-model="daysBack" @change="updateFilter">
                  <option value="7">7</option>
                  <option value="30">30</option>
                  <option value="90">90</option>
                </select>
              </label>
              <label>
                Limit:
                <select v-model="limit" @change="updateFilter">
                  <option value="15">15</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                </select>
              </label>
            </div>
          </div>

          <div v-if="loading" class="sidebar-loading">
            Loading...
          </div>

          <div v-else-if="error" class="sidebar-error">
            {{ error }}
          </div>

          <div v-else-if="historicalData" class="sidebar-data">
            <div class="date-range">
              {{ formatDate(historicalData.date_range.start) }} - 
              {{ formatDate(historicalData.date_range.end) }}
            </div>

            <!-- Recent Pages -->
            <div v-if="historicalData.pages && historicalData.pages.length" class="sidebar-section">
              <h4>Recent Pages ({{ historicalData.pages.length }})</h4>
              <div class="sidebar-items">
                <div 
                  v-for="page in historicalData.pages" 
                  :key="page.id" 
                  class="sidebar-item page-item"
                >
                  <div class="item-header">
                    <span class="item-title">{{ page.title }}</span>
                    <span class="item-type">{{ page.page_type }}</span>
                  </div>
                  <div class="item-meta">{{ formatDate(page.modified_at) }}</div>
                  <div v-if="page.content" class="item-content">
                    {{ truncateContent(page.content, 80) }}
                  </div>
                  <div v-if="page.recent_blocks && page.recent_blocks.length" class="recent-blocks-preview">
                    <span class="preview-label">Recent blocks:</span>
                    <div v-for="block in page.recent_blocks.slice(0, 2)" :key="block.id" class="block-preview">
                      {{ truncateContent(block.content, 40) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Recent Blocks -->
            <div v-if="historicalData.blocks && historicalData.blocks.length" class="sidebar-section">
              <h4>Recent Blocks ({{ historicalData.blocks.length }})</h4>
              <div class="sidebar-items">
                <div 
                  v-for="block in historicalData.blocks" 
                  :key="block.id" 
                  class="sidebar-item block-item"
                >
                  <div class="item-header">
                    <span class="item-type block-type">{{ block.block_type }}</span>
                    <span class="item-page">{{ block.page_title }}</span>
                  </div>
                  <div class="item-meta">{{ formatDate(block.modified_at) }}</div>
                  <div class="item-content">{{ truncateContent(block.content, 100) }}</div>
                  <div v-if="block.tags && block.tags.length" class="item-tags">
                    <span 
                      v-for="tag in getTagColors(block.tags)" 
                      :key="tag.name"
                      class="sidebar-tag"
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
    </div>
  `,
};