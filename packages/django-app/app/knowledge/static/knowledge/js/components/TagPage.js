// Tag Page Component - Dedicated page for viewing tag content
const TagPage = {
  components: {},
  props: {
    chatContextBlocks: {
      type: Array,
      default: () => [],
    },
    isBlockInContext: {
      type: Function,
      default: () => () => false,
    },
  },
  emits: [
    "block-add-to-context",
    "block-remove-from-context",
    "visible-blocks-changed",
  ],
  data() {
    return {
      currentTag: this.getTagFromURL(),
      tagData: null,
      blocks: [],
      loading: false,
      error: null,
      // Track blocks being deleted to prevent save conflicts
      deletingBlocks: new Set(),
      // Context menu state
      showContextMenu: false,
    };
  },

  async mounted() {
    // Add event listener to close context menu when clicking outside
    document.addEventListener("click", this.handleDocumentClick);
    // Add event delegation for clickable hashtags in content
    document.addEventListener("click", this.handleTagClick);

    if (this.currentTag) {
      await this.loadTagContent();
    } else {
      this.error = "No tag specified in URL";
    }
  },

  beforeUnmount() {
    // Clean up event listeners
    document.removeEventListener("click", this.handleDocumentClick);
    document.removeEventListener("click", this.handleTagClick);
  },

  computed: {
    pageTitle() {
      return this.currentTag ? `#${this.currentTag}` : "Tag";
    },

    tagBlocks() {
      return this.blocks || [];
    },

    tagPages() {
      return this.tagData?.pages || [];
    },

    totalContent() {
      return this.tagBlocks.length + this.tagPages.length;
    },
  },

  methods: {
    getTagFromURL() {
      // Extract tag from URL like /knowledge/tag/tagname/
      const pathParts = window.location.pathname.split("/");
      const tagIndex = pathParts.indexOf("tag");
      if (tagIndex !== -1 && pathParts[tagIndex + 1]) {
        return decodeURIComponent(pathParts[tagIndex + 1]);
      }
      return null;
    },

    async loadTagContent() {
      this.loading = true;
      this.error = null;

      try {
        const result = await window.apiService.getTagContent(this.currentTag);
        if (result.success) {
          this.tagData = result.data;
          this.blocks = this.setupParentReferences(result.data.blocks || []);
        } else {
          this.error = "Failed to load tag content";
        }
      } catch (error) {
        console.error("Failed to load tag content:", error);
        this.error = "Failed to load tag content";
      } finally {
        this.loading = false;
      }
    },

    setupParentReferences(blocks) {
      // Create a map for quick lookup
      const blockMap = new Map();

      // First pass: index all blocks
      blocks.forEach((block) => {
        block.children = [];
        blockMap.set(block.uuid, block);
      });

      // Second pass: establish parent-child relationships
      const rootBlocks = [];
      blocks.forEach((block) => {
        if (block.parent_uuid) {
          const parent = blockMap.get(block.parent_uuid);
          if (parent) {
            parent.children.push(block);
            block.parent = parent;
          } else {
            // Parent not found in current set, treat as root
            rootBlocks.push(block);
          }
        } else {
          rootBlocks.push(block);
        }
      });

      // Sort children by order
      blockMap.forEach((block) => {
        if (block.children.length > 0) {
          block.children.sort((a, b) => a.order - b.order);
        }
      });

      // Sort root blocks by order
      rootBlocks.sort((a, b) => a.order - b.order);

      return rootBlocks;
    },

    handleDocumentClick(event) {
      // Close context menu if clicking outside of it
      const contextMenuContainer = event.target.closest(
        ".context-menu-container"
      );
      if (!contextMenuContainer && this.showContextMenu) {
        this.closeContextMenu();
      }
    },

    closeContextMenu() {
      this.showContextMenu = false;
    },

    onBlocksChanged() {
      // Emit visible blocks for chat context
      this.$emit("visible-blocks-changed", this.tagBlocks);
    },

    onBlockAddToContext(block) {
      this.$emit("block-add-to-context", block);
    },

    onBlockRemoveFromContext(block) {
      this.$emit("block-remove-from-context", block);
    },

    goToPage(pageUuid) {
      // Navigate to a specific page
      window.location.href = `/knowledge/page/${pageUuid}/`;
    },

    handleTagClick(event) {
      // Check if the clicked element is a clickable tag
      if (event.target.classList.contains("clickable-tag")) {
        event.preventDefault();
        const tagName = event.target.getAttribute("data-tag");
        if (tagName) {
          this.goToTag(tagName);
        }
      }
    },

    goToTag(tagName) {
      // Navigate to the tag page with full page redirect
      const url = `/knowledge/tag/${encodeURIComponent(tagName)}/`;
      window.location.href = url;
    },

    formatContentWithTags(content) {
      if (!content) return "";

      // Replace hashtags with clickable styled spans (anywhere in content, not just at start)
      return content.replace(
        /#([a-zA-Z0-9_-]+)/g,
        '<span class="inline-tag clickable-tag" data-tag="$1">#$1</span>'
      );
    },

    formatDate(dateString) {
      // Parse the date string manually to avoid timezone conversion issues
      // dateString format: "2025-06-17"
      const [year, month, day] = dateString.split("-");
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString();
    },

    toggleBlockTodo(block) {
      // No-op for tag page - blocks are read-only
    },

    getPageUrl(page) {
      // Generate URL for a page (daily note or regular page)
      if (page.date) {
        return `/knowledge/daily/${page.date}/`;
      }
      return `/knowledge/page/${page.uuid}/`;
    },
  },

  template: `
    <div class="tag-page">
      <!-- Header matching original exactly -->
      <header class="daily-note-header">
        <h1>tag: {{ currentTag }}</h1>
      </header>

      <!-- Loading State -->
      <div v-if="loading" class="loading">
        Loading tag content...
      </div>

      <!-- Error State -->
      <div v-if="error" class="error">
        {{ error }}
      </div>


      <!-- Tag Content (matching original DailyNote styling exactly) -->
      <div v-else-if="tagData" class="tag-page-content">
        <div class="tag-stats">
          <span class="stats-text">
            {{ tagData.total_content }} items
            ({{ tagData.total_blocks }} blocks, {{ tagData.total_pages }} pages)
          </span>
        </div>

        <div v-if="tagBlocks.length > 0" class="blocks-container">
          <div v-for="block in tagBlocks" :key="block.uuid" class="block-wrapper" :data-block-uuid="block.uuid">
            <div class="block">
              <div
                class="block-bullet"
                :class="{ 'todo': block.block_type === 'todo', 'done': block.block_type === 'done' }"
                @click="block.block_type === 'todo' || block.block_type === 'done' ? toggleBlockTodo(block) : null"
              >
                <span v-if="block.block_type === 'todo'">☐</span>
                <span v-else-if="block.block_type === 'done'">☑</span>
                <span v-else>•</span>
              </div>
              <div class="block-content-display" :class="{ 'completed': block.block_type === 'done' }">
                <div class="block-meta">
                  <span class="page-title">{{ block.page_title }}</span>
                  <span v-if="block.page_date" class="page-date">{{ formatDate(block.page_date) }}</span>
                </div>
                <div v-html="formatContentWithTags(block.content)" class="block-text"></div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="tagData.pages && tagData.pages.length > 0" class="pages-container">
          <h3>Pages with this tag:</h3>
          <div v-for="page in tagData.pages" :key="page.uuid" class="page-item">
            <a :href="getPageUrl(page)" class="page-link">{{ page.title }}</a>
            <span v-if="page.date" class="page-date">{{ formatDate(page.date) }}</span>
          </div>
        </div>

        <div v-if="tagBlocks.length === 0 && (!tagData.pages || tagData.pages.length === 0)" class="no-content">
          No content found for tag #{{ currentTag }}
        </div>
      </div>
    </div>
  `,
};

// Make it globally available
window.TagPage = TagPage;
