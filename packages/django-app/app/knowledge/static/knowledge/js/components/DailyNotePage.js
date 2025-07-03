// DailyNotePage Component - Wrapper for daily note functionality
const DailyNotePage = {
  components: {
    Page: window.Page || {},
  },
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
      currentDate: this.getDateFromURL() || this.getLocalDateString(),
      page: null,
      blocks: [],
      loading: false,
      error: null,
      successMessage: "",
      // Context menu state
      showContextMenu: false,
    };
  },

  async mounted() {
    // Add event listener to close context menu when clicking outside
    document.addEventListener("click", this.handleDocumentClick);
    await this.loadPage();
  },

  beforeUnmount() {
    // Clean up event listeners
    document.removeEventListener("click", this.handleDocumentClick);
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
          this.blocks = this.setupParentReferences(result.data.blocks || []);
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
      this.updateURL(this.currentDate);
      await this.loadPage();
    },

    async handleCreateBlock({ content, parent, order, autoFocus }) {
      if (!this.page) return;

      try {
        const blockOrder = order !== null ? order : this.getNextOrder(parent);
        const result = await window.apiService.createBlock({
          page: this.page.uuid,
          content: content,
          parent: parent ? parent.uuid : null,
          block_type: "bullet",
          content_type: "text",
          order: blockOrder,
        });

        if (result.success) {
          // Add the new block to local state without full page reload
          const newBlock = {
            uuid: result.data.uuid || `temp-${Date.now()}`,
            content: result.data.content || content,
            content_type: result.data.content_type || "text",
            block_type: result.data.block_type || "bullet",
            order: result.data.order || blockOrder,
            parent: parent,
            children: [],
            isEditing: false,
            collapsed: result.data.collapsed || false,
            properties: result.data.properties || {},
            media_url: result.data.media_url || "",
            media_metadata: result.data.media_metadata || {},
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
            newBlock.isEditing = true;
            this.$nextTick(() => {
              this.$nextTick(() => {
                const textarea = document.querySelector(
                  `[data-block-uuid="${newBlock.uuid}"] textarea`
                );
                if (textarea) {
                  textarea.focus();
                  textarea.setSelectionRange(
                    textarea.value.length,
                    textarea.value.length
                  );
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

    async handleUpdateBlock({ block, newContent, skipReload }) {
      try {
        const result = await window.apiService.updateBlock(block.uuid, {
          content: newContent,
          parent: block.parent ? block.parent.uuid : null,
        });

        if (result.success) {
          // Update local state with all returned data
          block.content = newContent;

          // Update block type if it was auto-detected/changed on backend
          if (result.data && result.data.block_type) {
            block.block_type = result.data.block_type;
          }

          // Only reload if explicitly requested
          if (!skipReload) {
            await this.loadPage();
          }
        }
      } catch (error) {
        console.error("Failed to update block:", error);
        this.error = "Failed to update block";
      }
    },

    async handleDeleteBlock(block) {
      const confirmed = confirm(
        `Are you sure you want to delete this block? This will also delete any child blocks and cannot be undone.`
      );

      if (!confirmed) {
        return;
      }

      try {
        const result = await window.apiService.deleteBlock(block.uuid);

        if (result.success) {
          await this.loadPage(); // Reload to get updated structure
        }
      } catch (error) {
        console.error("Failed to delete block:", error);
        this.error = "Failed to delete block";
      }
    },

    async handleToggleBlockTodo(block) {
      try {
        const result = await window.apiService.toggleBlockTodo(block.uuid);
        if (result.success) {
          // Update local state
          block.block_type = result.data.block_type;
          block.content = result.data.content;

          // Clear any previous error messages
          this.error = null;
          this.successMessage = "";
        } else {
          this.error =
            result.errors?.non_field_errors?.[0] || "Failed to toggle todo";
        }
      } catch (error) {
        console.error("Failed to toggle block todo:", error);
        this.error = "Failed to toggle todo. Please try again.";
      }
    },

    async handleIndentBlock(block) {
      // Find the previous sibling block to make it the parent
      const previousSibling = this.findPreviousSibling(block);
      if (!previousSibling) return; // Can't indent if no previous sibling

      try {
        // Save current content first
        await this.handleUpdateBlock({
          block,
          newContent: block.content,
          skipReload: true,
        });

        // Update the block's parent and order
        const newOrder = this.getNextChildOrder(previousSibling);
        const result = await window.apiService.updateBlock(block.uuid, {
          parent: previousSibling.uuid,
          order: newOrder,
        });

        if (result.success) {
          // Update local state
          this.removeBlockFromCurrentParent(block);

          // Add to new parent's children
          if (!previousSibling.children) previousSibling.children = [];
          block.parent = previousSibling;
          block.order = newOrder;
          previousSibling.children.push(block);
          previousSibling.children.sort((a, b) => a.order - b.order);

          // Focus the block again
          this.$nextTick(() => {
            const textarea = document.querySelector(
              `[data-block-uuid="${block.uuid}"] textarea`
            );
            if (textarea) textarea.focus();
          });
        }
      } catch (error) {
        console.error("Failed to indent block:", error);
      }
    },

    async handleOutdentBlock(block) {
      if (!block.parent) return; // Already at root level

      try {
        // Save current content first
        await this.handleUpdateBlock({
          block,
          newContent: block.content,
          skipReload: true,
        });

        // Move to parent's level, right after parent
        const grandparent = block.parent.parent;
        const newOrder = block.parent.order + 1;

        // Update orders of siblings that come after the parent
        this.updateSiblingOrders(grandparent, newOrder);

        const result = await window.apiService.updateBlock(block.uuid, {
          parent: grandparent ? grandparent.uuid : null,
          order: newOrder,
        });

        if (result.success) {
          // Update local state
          this.removeBlockFromCurrentParent(block);

          // Add to new parent level
          block.parent = grandparent;
          block.order = newOrder;

          if (grandparent) {
            if (!grandparent.children) grandparent.children = [];
            grandparent.children.push(block);
            grandparent.children.sort((a, b) => a.order - b.order);
          } else {
            this.blocks.push(block);
            this.blocks.sort((a, b) => a.order - b.order);
          }

          // Focus the block again
          this.$nextTick(() => {
            const textarea = document.querySelector(
              `[data-block-uuid="${block.uuid}"] textarea`
            );
            if (textarea) textarea.focus();
          });
        }
      } catch (error) {
        console.error("Failed to outdent block:", error);
      }
    },

    findPreviousSibling(block) {
      const siblings = block.parent ? block.parent.children : this.blocks;
      const currentIndex = siblings.findIndex((b) => b.uuid === block.uuid);
      return currentIndex > 0 ? siblings[currentIndex - 1] : null;
    },

    getNextChildOrder(parentBlock) {
      if (!parentBlock.children || parentBlock.children.length === 0) return 0;
      return Math.max(...parentBlock.children.map((child) => child.order)) + 1;
    },

    removeBlockFromCurrentParent(block) {
      if (block.parent) {
        const parentChildren = block.parent.children || [];
        const index = parentChildren.findIndex(
          (child) => child.uuid === block.uuid
        );
        if (index !== -1) {
          parentChildren.splice(index, 1);
        }
      } else {
        const index = this.blocks.findIndex((b) => b.uuid === block.uuid);
        if (index !== -1) {
          this.blocks.splice(index, 1);
        }
      }
    },

    updateSiblingOrders(parent, fromOrder) {
      const siblings = parent ? parent.children : this.blocks;
      siblings.forEach((sibling) => {
        if (sibling.order >= fromOrder) {
          sibling.order += 1;
        }
      });
    },

    getNextOrder(parent) {
      const siblings = parent ? parent.children : this.blocks;
      return siblings.length > 0
        ? Math.max(...siblings.map((b) => b.order)) + 1
        : 0;
    },

    formatDate(dateString) {
      // Parse the date string manually to avoid timezone conversion issues
      const [year, month, day] = dateString.split("-");
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString();
    },

    setupParentReferences(blocks, parent = null) {
      // Set up parent object references for hierarchical block data from backend
      return blocks.map((blockData) => {
        const block = {
          ...blockData,
          parent: parent,
          children: [],
        };

        if (blockData.children && blockData.children.length > 0) {
          block.children = this.setupParentReferences(
            blockData.children,
            block
          );
        }

        return block;
      });
    },

    async deletePage() {
      if (!this.page || !this.page.uuid) {
        return;
      }

      const confirmed = confirm(
        `Are you sure you want to delete this daily note for ${this.formatDate(this.currentDate)}? This will delete all blocks and cannot be undone.`
      );

      if (!confirmed) {
        return;
      }

      try {
        const result = await window.apiService.deletePage(this.page.uuid);

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

    handleDocumentClick(event) {
      // Close context menu if clicking outside of it
      const contextMenuContainer = event.target.closest(
        ".context-menu-container"
      );
      if (!contextMenuContainer && this.showContextMenu) {
        this.closeContextMenu();
      }
    },

    toggleContextMenu() {
      this.showContextMenu = !this.showContextMenu;
    },

    closeContextMenu() {
      this.showContextMenu = false;
    },

    async moveUndoneTodosToThisPage() {
      this.loading = true;
      this.error = null;
      this.closeContextMenu();

      try {
        // Use the current page's date as target_date
        const targetDate = this.page?.date || null;
        const result = await window.apiService.moveUndoneTodos(targetDate);

        if (result.success) {
          const data = result.data;
          this.successMessage = data.message;

          // Reload the current page to show the moved TODOs
          await this.loadPage();

          // Clear success message after a few seconds
          setTimeout(() => {
            this.successMessage = "";
          }, 3000);
        } else {
          this.error =
            result.errors?.non_field_errors?.[0] ||
            "Failed to move undone TODOs";
        }
      } catch (error) {
        console.error("Failed to move undone TODOs:", error);
        this.error = "Failed to move undone TODOs. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    // Context management methods
    onBlockAddToContext(block) {
      this.$emit("block-add-to-context", block);
    },

    onBlockRemoveFromContext(blockId) {
      this.$emit("block-remove-from-context", blockId);
    },
  },

  template: `
    <div class="daily-note">
      <!-- Daily Note Header -->
      <header class="daily-note-header">
        <div class="header-controls">
          <input
            v-model="currentDate"
            type="date"
            @change="onDateChange"
            class="form-control date-picker"
          />
        </div>
      </header>

      <!-- Daily Note Content -->
      <div v-if="page" class="daily-note-content">
        <div class="daily-note-title current-note">
          <div class="title-left">
            <h2>{{ formatDate(currentDate) }}</h2>
            <div class="context-menu-container">
              <button
                @click="toggleContextMenu"
                class="btn btn-outline context-menu-btn"
                title="Daily note options"
              >
                ⋮
              </button>
              <div v-if="showContextMenu" class="context-menu" @click.stop>
                <button
                  @click="moveUndoneTodosToThisPage"
                  class="context-menu-item"
                  :disabled="loading"
                >
                  Move unfinished TODOs to this page
                </button>
              </div>
            </div>
          </div>
          <button
            v-if="page && page.uuid"
            @click="deletePage"
            class="btn btn-danger delete-page-btn"
            title="Delete this daily note"
          >
            del
          </button>
        </div>

        <Page
          :page="page"
          :blocks="blocks"
          :loading="loading"
          :error="error"
          :success-message="successMessage"
          :chat-context-blocks="chatContextBlocks"
          :is-block-in-context="isBlockInContext"
          @create-block="handleCreateBlock"
          @update-block="handleUpdateBlock"
          @delete-block="handleDeleteBlock"
          @toggle-block-todo="handleToggleBlockTodo"
          @indent-block="handleIndentBlock"
          @outdent-block="handleOutdentBlock"
          @block-add-to-context="onBlockAddToContext"
          @block-remove-from-context="onBlockRemoveFromContext"
        />
      </div>
    </div>
  `,
};

// Register component globally
window.DailyNotePage = DailyNotePage;
