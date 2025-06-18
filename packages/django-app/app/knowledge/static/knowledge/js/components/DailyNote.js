// Daily Note Component - Logseq-style daily notes with blocks
const DailyNote = {
  data() {
    return {
      currentDate: this.getDateFromURL() || this.getLocalDateString(),
      page: null,
      blocks: [],
      historicalData: null,
      historicalBlocksCache: {},
      loading: false,
      error: null,
      successMessage: "",
      isNavigating: false,
      // Tag page data
      currentTag: null,
      tagData: null,
      isTagPage: false,
    };
  },

  async mounted() {
    // Register component when it's available
    if (window.HistoricalDailyNoteBlocks) {
      this.$options.components = this.$options.components || {};
      this.$options.components.HistoricalDailyNoteBlocks =
        window.HistoricalDailyNoteBlocks;
    }
    
    // Add event delegation for clickable tags
    document.addEventListener('click', this.handleTagClick);
    
    // Check if we're on a tag page
    this.currentTag = this.getTagFromURL();
    this.isTagPage = !!this.currentTag;
    
    if (this.isTagPage) {
      await this.loadTagContent();
    } else {
      await this.loadPage();
      await this.loadHistoricalData();
    }
  },

  beforeUnmount() {
    // Clean up event listener
    document.removeEventListener('click', this.handleTagClick);
  },

  methods: {
    getLocalDateString() {
      // Get user's local date, not UTC date
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, "0");
      const day = String(now.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    },

    getDateFromURL() {
      // Extract date from URL like /knowledge/daily/2025-06-17/
      const pathParts = window.location.pathname.split("/");
      const dailyIndex = pathParts.indexOf("daily");
      if (dailyIndex !== -1 && pathParts[dailyIndex + 1]) {
        const dateStr = pathParts[dailyIndex + 1];
        // Validate date format YYYY-MM-DD
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
          return dateStr;
        }
      }
      return null;
    },

    getTagFromURL() {
      // Extract tag from URL like /knowledge/tag/tagname/
      const pathParts = window.location.pathname.split("/");
      const tagIndex = pathParts.indexOf("tag");
      if (tagIndex !== -1 && pathParts[tagIndex + 1]) {
        return decodeURIComponent(pathParts[tagIndex + 1]);
      }
      return null;
    },

    updateURL(date) {
      // Update URL without page reload
      const newPath = `/knowledge/daily/${date}/`;
      if (window.location.pathname !== newPath) {
        window.history.pushState({}, "", newPath);
      }
    },

    async loadPage() {
      this.loading = true;
      this.error = null;

      try {
        const result = await window.apiService.getPageWithBlocks(
          null,
          this.currentDate
        );
        if (result.success) {
          this.page = result.data.page;
          this.blocks = result.data.blocks || [];
        } else {
          this.error = "Failed to load page";
        }
      } catch (error) {
        console.error("Failed to load page:", error);
        this.error = "Failed to load page";
      } finally {
        this.loading = false;
      }
    },

    async loadTagContent() {
      this.loading = true;
      this.error = null;

      try {
        const result = await window.apiService.getTagContent(this.currentTag);
        if (result.success) {
          this.tagData = result.data;
          this.blocks = result.data.blocks || [];
          this.page = null; // No page for tag view
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

    async onDateChange() {
      this.updateURL(this.currentDate);
      await this.loadPage();
    },

    async createBlock(content = "", parent = null, order = null, autoFocus = true) {
      if (!this.page) return;

      try {
        const blockOrder = order !== null ? order : this.getNextOrder(parent);
        const result = await window.apiService.createBlock({
          page_id: this.page.id,
          content: content,
          parent_id: parent ? parent.id : null,
          block_type: "bullet",
          content_type: "text",
          order: blockOrder,
        });

        if (result.success) {
          // Add the new block to local state without full page reload
          // Use the actual data returned from the API (includes auto-detected block_type)
          const newBlock = {
            id: result.data.uuid || result.data.id || `temp-${Date.now()}`,
            content: result.data.content || content,
            content_type: result.data.content_type || "text", 
            block_type: result.data.block_type || "bullet", // This will include auto-detected types
            order: result.data.order || blockOrder,
            parent: parent,
            children: [],
            isEditing: false,
            collapsed: result.data.collapsed || false,
            properties: result.data.properties || {},
            media_url: result.data.media_url || "",
            media_metadata: result.data.media_metadata || {}
          };
          
          // Insert the new block in the correct position
          if (parent) {
            if (!parent.children) parent.children = [];
            parent.children.push(newBlock);
            parent.children.sort((a, b) => a.order - b.order);
          } else {
            this.blocks.push(newBlock);
            this.blocks.sort((a, b) => a.order - b.order);
          }
          
          // Auto-focus the newly created block if requested
          if (autoFocus) {
            // Mark the block as editing immediately so Vue renders the textarea
            newBlock.isEditing = true;
            
            // Wait for Vue to render the textarea, then focus it
            this.$nextTick(() => {
              this.$nextTick(() => {
                const textarea = document.querySelector(`[data-block-id="${newBlock.id}"] textarea`);
                if (textarea) {
                  textarea.focus();
                  textarea.setSelectionRange(textarea.value.length, textarea.value.length);
                } else {
                  // If textarea still not found, try one more time after a short delay
                  setTimeout(() => {
                    const retryTextarea = document.querySelector(`[data-block-id="${newBlock.id}"] textarea`);
                    if (retryTextarea) {
                      retryTextarea.focus();
                      retryTextarea.setSelectionRange(retryTextarea.value.length, retryTextarea.value.length);
                    }
                  }, 50);
                }
              });
            });
          }
        }
        
        return result;
      } catch (error) {
        console.error("Failed to create block:", error);
        this.error = "Failed to create block";
        return { success: false };
      }
    },

    async updateBlock(block, newContent, skipReload = false) {
      try {
        const result = await window.apiService.updateBlock({
          block_id: block.id,
          content: newContent,
        });

        if (result.success) {
          // Update local state with all returned data
          block.content = newContent;
          
          // Update block type if it was auto-detected/changed on backend
          if (result.data && result.data.block_type) {
            block.block_type = result.data.block_type;
          }
          
          // Only reload if explicitly requested (rare cases when tags need refresh)
          if (!skipReload) {
            await this.loadPage(); // Reload to get updated tags
          }
        }
      } catch (error) {
        console.error("Failed to update block:", error);
        this.error = "Failed to update block";
      }
    },

    async deleteBlock(block) {
      try {
        const result = await window.apiService.deleteBlock({
          block_id: block.id,
        });

        if (result.success) {
          await this.loadPage(); // Reload to get updated structure
        }
      } catch (error) {
        console.error("Failed to delete block:", error);
        this.error = "Failed to delete block";
      }
    },

    async toggleBlockTodo(block) {
      try {
        const result = await window.apiService.toggleBlockTodo(block.id);
        if (result.success) {
          // Update local state
          block.block_type = result.data.block_type;
        }
      } catch (error) {
        console.error("Failed to toggle block todo:", error);
        this.error = "Failed to toggle todo";
      }
    },

    getNextOrder(parent) {
      const siblings = parent ? parent.children : this.blocks;
      return siblings.length > 0
        ? Math.max(...siblings.map((b) => b.order)) + 1
        : 0;
    },

    async refreshTagsOnly() {
      // Refresh page data but preserve current editing state
      try {
        const currentlyEditing = this.getAllBlocks().filter(b => b.isEditing);
        await this.loadPage();
        
        // Restore editing state after reload
        currentlyEditing.forEach(block => {
          const refreshedBlock = this.getAllBlocks().find(b => b.id === block.id);
          if (refreshedBlock) {
            refreshedBlock.isEditing = true;
            this.$nextTick(() => {
              const textarea = document.querySelector(`[data-block-id="${refreshedBlock.id}"] textarea`);
              if (textarea) {
                textarea.focus();
              }
            });
          }
        });
      } catch (error) {
        console.error("Failed to refresh tags:", error);
      }
    },

    formatDate(dateString) {
      // Parse the date string manually to avoid timezone conversion issues
      // dateString format: "2025-06-17"
      const [year, month, day] = dateString.split("-");
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString();
    },

    onBlockContentChange(block, newContent) {
      // Just update the local content, don't save yet
      block.content = newContent;
    },

    async onBlockKeyDown(event, block) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        // Save current block before creating new one
        await this.updateBlock(block, block.content, true);
        this.createBlock("", block.parent, block.order + 1);
      } else if (event.key === "Tab") {
        event.preventDefault();
        // TODO: Implement indentation/outdentation
      } else if (event.key === "ArrowDown") {
        const textarea = event.target;
        const cursorPos = textarea.selectionStart;
        const value = textarea.value;

        // For single line content, check if cursor is at end
        if (value.indexOf("\n") === -1) {
          // Single line - if cursor is at end, move to next block
          if (cursorPos === value.length) {
            event.preventDefault();
            this.focusNextBlock(block);
          }
        } else {
          // Multi-line content
          const lines = value.substr(0, cursorPos).split("\n");
          const currentLine = lines.length - 1;
          const totalLines = value.split("\n").length;

          // If cursor is on the last line, move to next block
          if (currentLine === totalLines - 1) {
            event.preventDefault();
            this.focusNextBlock(block);
          }
        }
      } else if (event.key === "ArrowUp") {
        const textarea = event.target;
        const cursorPos = textarea.selectionStart;
        const value = textarea.value;

        // For single line content, check if cursor is at beginning
        if (value.indexOf("\n") === -1) {
          // Single line - if cursor is at beginning, move to previous block
          if (cursorPos === 0) {
            event.preventDefault();
            this.focusPreviousBlock(block);
          }
        } else {
          // Multi-line content
          const lines = value.substr(0, cursorPos).split("\n");
          const currentLine = lines.length - 1;

          // If cursor is on the first line, move to previous block
          if (currentLine === 0) {
            event.preventDefault();
            this.focusPreviousBlock(block);
          }
        }
      }
    },

    addNewBlock() {
      this.createBlock("");
    },

    formatContentWithTags(content) {
      if (!content) return "";

      // Replace hashtags with clickable styled spans
      return content.replace(
        /#([a-zA-Z0-9_-]+)/g,
        '<span class="inline-tag clickable-tag" data-tag="$1">#$1</span>'
      );
    },

    handleTagClick(event) {
      // Check if the clicked element is a clickable tag
      if (event.target.classList.contains('clickable-tag')) {
        event.preventDefault();
        const tagName = event.target.getAttribute('data-tag');
        if (tagName) {
          this.goToTag(tagName);
        }
      }
    },

    goToTag(tagName) {
      // Navigate to the tag page without full page reload
      const url = `/knowledge/tag/${encodeURIComponent(tagName)}/`;
      window.history.pushState({}, '', url);
      
      // Update the current component state for tag page
      this.currentTag = tagName;
      this.isTagPage = true;
      this.loadTagContent();
    },

    goBackToDailyNotes() {
      // Navigate back to daily notes without page reload
      const url = '/knowledge/';
      window.history.pushState({}, '', url);
      
      // Reset to daily note view
      this.isTagPage = false;
      this.currentTag = null;
      this.tagData = null;
      this.loadPage();
    },

    getPageUrl(page) {
      // Generate URL for a page (daily note or regular page)
      if (page.date) {
        return `/knowledge/daily/${page.date}/`;
      }
      return `/knowledge/page/${page.slug || page.uuid}/`;
    },

    startEditing(block) {
      // Stop editing all other blocks first (save them)
      const allBlocks = this.getAllBlocks();
      allBlocks.forEach((b) => {
        if (b.id !== block.id && b.isEditing) {
          this.updateBlock(b, b.content, true); // Save without reload
          b.isEditing = false;
        }
      });

      block.isEditing = true;
      this.$nextTick(() => {
        // Focus the specific textarea for this block
        const blockElement = document.querySelector(
          `[data-block-id="${block.id}"] textarea`
        );
        if (blockElement) {
          blockElement.focus();
        }
      });
    },

    async stopEditing(block) {
      // Don't stop editing if we're navigating between blocks
      if (this.isNavigating) {
        this.isNavigating = false;
        return;
      }

      // Save the block when user stops editing (blur event)
      // Skip reload to preserve cursor positions of other blocks
      await this.updateBlock(block, block.content, true);
      block.isEditing = false;
    },

    getAllBlocks() {
      // Get all blocks in document order (flattened tree)
      const result = [];
      const addBlocks = (blocks) => {
        for (const block of blocks) {
          result.push(block);
          if (block.children && block.children.length) {
            addBlocks(block.children);
          }
        }
      };
      addBlocks(this.blocks);
      return result;
    },

    focusNextBlock(currentBlock) {
      const allBlocks = this.getAllBlocks();
      const currentIndex = allBlocks.findIndex((b) => b.id === currentBlock.id);

      if (currentIndex >= 0 && currentIndex < allBlocks.length - 1) {
        const nextBlock = allBlocks[currentIndex + 1];
        this.isNavigating = true;
        this.startEditing(nextBlock);
      }
    },

    focusPreviousBlock(currentBlock) {
      const allBlocks = this.getAllBlocks();
      const currentIndex = allBlocks.findIndex((b) => b.id === currentBlock.id);

      if (currentIndex > 0) {
        const previousBlock = allBlocks[currentIndex - 1];
        this.isNavigating = true;
        this.startEditing(previousBlock);
      }
    },

    async loadHistoricalData() {
      try {
        const result = await window.apiService.getHistoricalData(7, 20);
        if (result.success) {
          this.historicalData = result.data;
        }
      } catch (error) {
        console.error("Failed to load historical data:", error);
      }
    },

    formatDate(dateString) {
      // Handle date strings properly to avoid timezone issues
      if (
        typeof dateString === "string" &&
        dateString.match(/^\d{4}-\d{2}-\d{2}$/)
      ) {
        // For YYYY-MM-DD format, parse manually to avoid timezone issues
        const [year, month, day] = dateString.split("-");
        const date = new Date(
          parseInt(year),
          parseInt(month) - 1,
          parseInt(day)
        );
        return date.toLocaleDateString();
      }
      return new Date(dateString).toLocaleDateString();
    },

    truncateContent(content, maxLength = 80) {
      if (!content) return "";
      return content.length > maxLength
        ? content.substring(0, maxLength) + "..."
        : content;
    },

    async deletePage() {
      if (!this.page || !this.page.id) {
        return;
      }

      const confirmed = confirm(
        `Are you sure you want to delete this daily note for ${this.formatDate(this.currentDate)}? This will delete all blocks and cannot be undone.`
      );

      if (!confirmed) {
        return;
      }

      try {
        const result = await window.apiService.deletePage(this.page.id);

        if (result.success) {
          this.successMessage = "Daily note deleted successfully";

          // Redirect to knowledge base to avoid auto-creating the same page
          setTimeout(() => {
            window.location.href = "/knowledge/";
          }, 1000);
        } else {
          this.error = "Failed to delete daily note";
        }
      } catch (error) {
        console.error("Error deleting page:", error);
        this.error = "Failed to delete daily note";
      }
    },

    getHistoricalBlocks(historicalPage) {
      // Return cached blocks if available, otherwise return empty array
      const cacheKey = historicalPage.id;
      if (this.historicalBlocksCache[cacheKey]) {
        return this.historicalBlocksCache[cacheKey];
      }

      // Load blocks for this historical page asynchronously
      this.loadHistoricalPageBlocks(historicalPage);
      return [];
    },

    async loadHistoricalPageBlocks(historicalPage) {
      const cacheKey = historicalPage.id;

      try {
        const result = await window.apiService.getPageWithBlocks(
          null,
          historicalPage.date
        );
        if (result.success) {
          this.historicalBlocksCache[cacheKey] = result.data.blocks || [];
          this.$forceUpdate(); // Force re-render to show the loaded blocks
        }
      } catch (error) {
        console.error("Failed to load historical blocks:", error);
      }
    },
  },

  template: `
    <div class="daily-note">
      <!-- Tag Page Header -->
      <header v-if="isTagPage" class="daily-note-header">
        <h1>tag: {{ currentTag }}</h1>
        <div class="header-controls">
          <button @click="goBackToDailyNotes" class="btn btn-outline">← back to daily notes</button>
        </div>
      </header>
      
      <!-- Daily Note Header -->
      <header v-else class="daily-note-header">
        <h1>daily note</h1>
        <div class="header-controls">
          <input
            v-model="currentDate"
            type="date"
            @change="onDateChange"
            class="form-control date-picker"
          />
          <button
            v-if="page && page.id && blocks.length === 0"
            @click="deletePage"
            class="btn btn-danger delete-page-btn"
            title="Delete this daily note"
          >
            del
          </button>
        </div>
      </header>

      <div v-if="loading" class="loading">Loading{{ isTagPage ? ' tag content' : ' page' }}...</div>

      <!-- Tag Page Content -->
      <div v-else-if="isTagPage && tagData" class="tag-page-content">
        <div class="tag-stats">
          <span class="tag-display inline-tag">{{ currentTag }}</span>
          <span class="stats-text">
            {{ tagData.total_content }} items 
            ({{ tagData.total_blocks }} blocks, {{ tagData.total_pages }} pages)
          </span>
        </div>

        <div v-if="blocks.length > 0" class="blocks-container">
          <div v-for="block in blocks" :key="block.id" class="block-wrapper" :data-block-id="block.id">
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

        <div v-if="blocks.length === 0 && (!tagData.pages || tagData.pages.length === 0)" class="no-content">
          No content found for tag #{{ currentTag }}
        </div>
      </div>

      <!-- Daily Note Content -->
      <div v-else-if="!isTagPage && page" class="daily-note-content">
        <h2>{{ formatDate(currentDate) }}</h2>

        <div class="blocks-container">
          <div v-for="block in blocks" :key="block.id" class="block-wrapper" :data-block-id="block.id">
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
              <div
                v-if="!block.isEditing"
                class="block-content-display"
                :class="{ 'completed': block.block_type === 'done' }"
                @click="startEditing(block)"
                v-html="formatContentWithTags(block.content)"
              ></div>
              <textarea
                v-else
                :value="block.content"
                @input="onBlockContentChange(block, $event.target.value)"
                @keydown="onBlockKeyDown($event, block)"
                @blur="stopEditing(block)"
                class="block-content"
                :class="{ 'completed': block.block_type === 'done' }"
                rows="1"
                placeholder="Start writing..."
                ref="blockTextarea"
              ></textarea>
              <button
                @click="deleteBlock(block)"
                class="block-delete"
                title="Delete block"
              >del</button>
            </div>

            <!-- Render children blocks recursively -->
            <div v-if="block.children && block.children.length" class="block-children">
              <div v-for="child in block.children" :key="child.id" class="block-wrapper child-block" :data-block-id="child.id">
                <div class="block">
                  <div
                    class="block-bullet"
                    :class="{ 'todo': child.block_type === 'todo', 'done': child.block_type === 'done' }"
                    @click="child.block_type === 'todo' || child.block_type === 'done' ? toggleBlockTodo(child) : null"
                  >
                    <span v-if="child.block_type === 'todo'">☐</span>
                    <span v-else-if="child.block_type === 'done'">☑</span>
                    <span v-else>•</span>
                  </div>
                  <div
                    v-if="!child.isEditing"
                    class="block-content-display"
                    :class="{ 'completed': child.block_type === 'done' }"
                    @click="startEditing(child)"
                    v-html="formatContentWithTags(child.content)"
                  ></div>
                  <textarea
                    v-else
                    :value="child.content"
                    @input="onBlockContentChange(child, $event.target.value)"
                    @keydown="onBlockKeyDown($event, child)"
                    @blur="stopEditing(child)"
                    class="block-content"
                    :class="{ 'completed': child.block_type === 'done' }"
                    rows="1"
                    placeholder="Start writing..."
                    ref="blockTextarea"
                  ></textarea>
                  <button
                    @click="deleteBlock(child)"
                    class="block-delete"
                    title="Delete block"
                  >del</button>
                </div>
              </div>
            </div>
          </div>

          <button @click="addNewBlock" class="add-block-btn">
            + add new block
          </button>
        </div>
      </div>

      <!-- Historical Daily Notes -->
      <div v-if="historicalData && historicalData.pages && historicalData.pages.length" class="historical-notes">
        <div
          v-for="historicalPage in historicalData.pages
            .filter(p => p.page_type === 'daily' && p.date !== currentDate)
            .sort((a, b) => new Date(b.date || b.modified_at) - new Date(a.date || a.modified_at))"
          :key="'historical-' + historicalPage.id"
          class="historical-daily-note"
        >
          <h2>{{ formatDate(historicalPage.date) }}</h2>

          <!-- Load full block data for this historical page -->
          <div class="historical-blocks-container">
            <div v-for="block in getHistoricalBlocks(historicalPage)" :key="block.id" class="block-wrapper" :data-block-id="block.id">
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
                <div
                  v-if="!block.isEditing"
                  class="block-content-display"
                  :class="{ 'completed': block.block_type === 'done' }"
                  @click="startEditing(block)"
                  v-html="formatContentWithTags(block.content)"
                ></div>
                <textarea
                  v-else
                  :value="block.content"
                  @input="onBlockContentChange(block, $event.target.value)"
                  @keydown="onBlockKeyDown($event, block)"
                  @blur="stopEditing(block)"
                  class="block-content"
                  :class="{ 'completed': block.block_type === 'done' }"
                  rows="1"
                  placeholder="Start writing..."
                ></textarea>
                <button
                  @click="deleteBlock(block)"
                  class="block-delete"
                  title="Delete block"
                >del</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>
    </div>
  `,
};

// Register component globally
window.DailyNote = DailyNote;
