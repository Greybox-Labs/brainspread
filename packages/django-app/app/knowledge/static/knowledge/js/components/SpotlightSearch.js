// SpotlightSearch Component
window.SpotlightSearch = {
  props: {
    isOpen: {
      type: Boolean,
      default: false,
    },
    query: {
      type: String,
      default: "",
    },
    results: {
      type: Array,
      default: () => [],
    },
    loading: {
      type: Boolean,
      default: false,
    },
    selectedIndex: {
      type: Number,
      default: 0,
    },
  },

  emits: ["close", "query-changed", "navigate", "keydown"],

  watch: {
    isOpen(newValue) {
      if (newValue) {
        document.body.style.overflow = "hidden";
        this.$nextTick(() => {
          this.focusInput();
        });
      } else {
        document.body.style.overflow = "";
      }
    },
  },

  methods: {
    focusInput() {
      const input = this.$refs.searchInput;
      if (input) {
        input.focus();
      }
    },

    handleOverlayClick(event) {
      if (event.target === event.currentTarget) {
        this.$emit("close");
      }
    },

    handleInputChange(event) {
      this.$emit("query-changed", event.target.value);
    },

    handleKeydown(event) {
      this.$emit("keydown", event);
    },

    handleResultClick(index) {
      this.$emit("navigate", index);
    },

    highlightQuery(text, query) {
      if (!query || !text) return text;

      const regex = new RegExp(
        `(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`,
        "gi"
      );
      return text.replace(regex, "<mark>$1</mark>");
    },
  },

  template: `
    <div v-if="isOpen" class="spotlight-overlay" @click="handleOverlayClick">
      <div class="spotlight-modal">
        <div class="spotlight-header">
          <div class="spotlight-search-container">
            <svg class="spotlight-search-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M9 17a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM19 19l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <input
              ref="searchInput"
              type="text"
              class="spotlight-search-input"
              placeholder="search pages..."
              :value="query"
              @input="handleInputChange"
              @keydown="handleKeydown"
            />
            <div class="spotlight-shortcut">
              <kbd>esc</kbd>
            </div>
          </div>
        </div>

        <div class="spotlight-content">
          <div v-if="loading" class="spotlight-loading">
            <div class="loading-spinner"></div>
            <span>Searching...</span>
          </div>

          <div v-else-if="query && results.length === 0" class="spotlight-no-results">
            <p>no pages found for "<strong>{{ query }}</strong>"</p>
          </div>

          <div v-else-if="results.length > 0" class="spotlight-results">
            <div
              v-for="(result, index) in results"
              :key="result.slug"
              class="spotlight-result"
              :class="{ 'selected': index === selectedIndex }"
              @click="handleResultClick(index)"
            >
              <div class="spotlight-result-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3z" stroke="currentColor" stroke-width="1.5" fill="none"/>
                  <path d="M5 6h6M5 8h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="spotlight-result-content">
                <div class="spotlight-result-title" v-html="highlightQuery(result.title, query)"></div>
                <div class="spotlight-result-snippet" v-html="highlightQuery(result.snippet, query)"></div>
                <div class="spotlight-result-path">{{ result.url }}</div>
              </div>
            </div>
          </div>

          <div v-else-if="!query" class="spotlight-empty">
            <p>start typing to search your pages...</p>
          </div>
        </div>

        <div class="spotlight-footer">
          <div class="spotlight-shortcuts">
            <div class="spotlight-shortcut-item">
              <kbd>↑</kbd><kbd>↓</kbd> to navigate
            </div>
            <div class="spotlight-shortcut-item">
              <kbd>enter</kbd> to select
            </div>
            <div class="spotlight-shortcut-item">
              <kbd>esc</kbd> to close
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
};
