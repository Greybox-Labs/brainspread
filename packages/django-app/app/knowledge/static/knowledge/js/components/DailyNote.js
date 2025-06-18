// Daily Note Component - Logseq-style daily notes with blocks
const DailyNote = {
  data() {
    return {
      currentDate: this.getLocalDateString(),
      page: null,
      blocks: [],
      loading: false,
      error: null,
      successMessage: "",
    };
  },

  async mounted() {
    await this.loadPage();
  },

  methods: {
    getLocalDateString() {
      // Get user's local date, not UTC date
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },

    async loadPage() {
      this.loading = true;
      this.error = null;

      try {
        const result = await window.apiService.getPageWithBlocks(null, this.currentDate);
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

    async onDateChange() {
      await this.loadPage();
    },

    async createBlock(content = "", parent = null, order = null) {
      if (!this.page) return;

      try {
        const blockOrder = order !== null ? order : this.getNextOrder(parent);
        const result = await window.apiService.createBlock({
          page_id: this.page.id,
          content: content,
          parent_id: parent ? parent.id : null,
          block_type: 'bullet',
          content_type: 'text',
          order: blockOrder
        });

        if (result.success) {
          await this.loadPage(); // Reload to get updated structure
          // Find the newly created block and put it in edit mode if it's empty
          if (content === "") {
            this.$nextTick(() => {
              const newBlock = this.blocks.find(b => b.content === content && b.order === blockOrder);
              if (newBlock) {
                this.startEditing(newBlock);
              }
            });
          }
        }
      } catch (error) {
        console.error("Failed to create block:", error);
        this.error = "Failed to create block";
      }
    },

    async updateBlock(block, newContent) {
      try {
        const result = await window.apiService.updateBlock({
          block_id: block.id,
          content: newContent
        });

        if (result.success) {
          // Update local state and reload page to refresh tags
          block.content = newContent;
          await this.loadPage(); // Reload to get updated tags
        }
      } catch (error) {
        console.error("Failed to update block:", error);
        this.error = "Failed to update block";
      }
    },

    async deleteBlock(block) {
      try {
        const result = await window.apiService.deleteBlock({
          block_id: block.id
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
      return siblings.length > 0 ? Math.max(...siblings.map(b => b.order)) + 1 : 0;
    },

    formatDate(dateString) {
      // Parse the date string manually to avoid timezone conversion issues
      // dateString format: "2025-06-17"
      const [year, month, day] = dateString.split('-');
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString();
    },

    onBlockContentChange(block, newContent) {
      // Debounced update
      clearTimeout(block.updateTimeout);
      block.updateTimeout = setTimeout(() => {
        this.updateBlock(block, newContent);
      }, 500);
    },

    onBlockKeyDown(event, block) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        this.createBlock("", block.parent, block.order + 1);
      } else if (event.key === 'Tab') {
        event.preventDefault();
        // TODO: Implement indentation/outdentation
      }
    },

    addNewBlock() {
      this.createBlock("");
    },

    formatContentWithTags(content) {
      if (!content) return '';
      
      // Replace hashtags with styled spans
      return content.replace(/#([a-zA-Z0-9_-]+)/g, '<span class="inline-tag">#$1</span>');
    },

    startEditing(block) {
      block.isEditing = true;
      this.$nextTick(() => {
        // Focus the textarea when editing starts
        const textareas = this.$refs.blockTextarea;
        if (textareas) {
          const textarea = Array.isArray(textareas) ? textareas.find(t => t) : textareas;
          if (textarea) textarea.focus();
        }
      });
    },

    stopEditing(block) {
      block.isEditing = false;
    }
  },

  template: `
    <div class="daily-note">
      <header class="daily-note-header">
        <h1>📅 Daily Note</h1>
        <div class="date-picker">
          <input
            v-model="currentDate"
            type="date"
            @change="onDateChange"
            class="form-control"
          />
        </div>
      </header>

      <div v-if="loading" class="loading">Loading page...</div>

      <div v-else-if="page" class="daily-note-content">
        <h2>{{ formatDate(currentDate) }}</h2>

        <div class="blocks-container">
          <div v-for="block in blocks" :key="block.id" class="block-wrapper">
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
              >×</button>
            </div>

            <!-- Render children blocks recursively -->
            <div v-if="block.children && block.children.length" class="block-children">
              <div v-for="child in block.children" :key="child.id" class="block-wrapper child-block">
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
                  >×</button>
                </div>
              </div>
            </div>
          </div>

          <button @click="addNewBlock" class="add-block-btn">
            + Add new block
          </button>
        </div>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>
    </div>
  `,
};

// Register component globally
window.DailyNote = DailyNote;
