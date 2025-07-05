// Page Component - Handles both regular pages and tag pages in Logseq style
const PagePage = {
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
      pageSlug: this.getSlugFromURL(),
      currentDate: this.getDateFromURL(),
      page: null,
      directBlocks: [], // Blocks that belong directly to this page
      referencedBlocks: [], // Blocks from other pages that reference this page
      loading: false,
      error: null,
      isEditingTitle: false,
      newTitle: "",
      showContextMenu: false,
      showPageMenu: false,
      selectedDate: null, // For date selector
    };
  },

  async mounted() {
    document.addEventListener("click", this.handleDocumentClick);
    document.addEventListener("click", this.handleTagClick);
    await this.loadPage();
  },

  beforeUnmount() {
    document.removeEventListener("click", this.handleDocumentClick);
    document.removeEventListener("click", this.handleTagClick);
  },

  computed: {
    isDaily() {
      return this.page?.page_type === "daily";
    },

    pageTitle() {
      return this.page?.title || "untitled page";
    },

    totalDirectBlocks() {
      return this.directBlocks.length;
    },

    totalReferencedBlocks() {
      return this.referencedBlocks.length;
    },

    hasReferencedBlocks() {
      return this.referencedBlocks.length > 0;
    },
  },

  methods: {
    getSlugFromURL() {
      const pathParts = window.location.pathname.split("/");
      const pageIndex = pathParts.indexOf("page");
      if (pageIndex !== -1 && pathParts[pageIndex + 1]) {
        return decodeURIComponent(pathParts[pageIndex + 1]);
      }
      return null;
    },

    getDateFromURL() {
      const slug = this.getSlugFromURL();
      if (slug && /^\d{4}-\d{2}-\d{2}$/.test(slug)) {
        return slug;
      }
      return null;
    },

    async loadPage() {
      this.loading = true;
      this.error = null;

      try {
        let result;

        // Use unified page loading - all pages go through the same API
        if (this.currentDate) {
          result = await window.apiService.getPageWithBlocks(
            null,
            this.currentDate
          );
        } else {
          result = await window.apiService.getPageWithBlocks(
            null,
            null,
            this.pageSlug
          );
        }

        if (result.success) {
          this.page = result.data.page;
          this.directBlocks = this.setupParentReferences(
            result.data.direct_blocks || []
          );
          this.referencedBlocks = result.data.referenced_blocks || [];
        } else {
          this.error = "Failed to load page";
        }

        if (this.page) {
          this.newTitle = this.page.title || "";
          this.initializeDateSelector();
        }
      } catch (error) {
        console.error("Failed to load page:", error);
        this.error = "Failed to load page";
      } finally {
        this.loading = false;
      }
    },

    setupParentReferences(blocks, parent = null) {
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

    async handleCreateBlock({ content, parent, order, autoFocus }) {
      if (!this.page) return;

      try {
        const blockOrder = order !== null ? order : this.getNextOrder(parent);
        const result = await window.apiService.createBlock({
          page: this.page.uuid,
          content: content,
          parent: parent?.uuid ?? null,
          block_type: "bullet",
          content_type: "text",
          order: blockOrder,
        });

        if (result.success) {
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

          if (parent) {
            if (!parent.children) parent.children = [];
            parent.children.push(newBlock);
            parent.children.sort((a, b) => a.order - b.order);
          } else {
            this.directBlocks.push(newBlock);
            this.directBlocks.sort((a, b) => a.order - b.order);
          }

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
          block.content = newContent;
          if (result.data && result.data.block_type) {
            block.block_type = result.data.block_type;
          }
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

      if (!confirmed) return;

      try {
        const result = await window.apiService.deleteBlock(block.uuid);
        if (result.success) {
          await this.loadPage();
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
          block.block_type = result.data.block_type;
          block.content = result.data.content;
          this.error = null;
        } else {
          this.error =
            result.errors?.non_field_errors?.[0] || "Failed to toggle todo";
        }
      } catch (error) {
        console.error("Failed to toggle block todo:", error);
        this.error = "Failed to toggle todo. Please try again.";
      }
    },

    getNextOrder(parent) {
      const siblings = parent ? parent.children : this.directBlocks;
      return siblings.length > 0
        ? Math.max(...siblings.map((b) => b.order)) + 1
        : 0;
    },

    async handleCreateBlockAfter(currentBlock) {
      // Calculate the new order (right after current block)
      const newOrder = currentBlock.order + 1;
      const siblings = currentBlock.parent
        ? currentBlock.parent.children
        : this.directBlocks;

      // Find blocks that need to be shifted down
      const blocksToShift = siblings.filter(
        (block) => block.uuid !== currentBlock.uuid && block.order >= newOrder
      );

      try {
        // Shift existing blocks down by updating their orders in the backend
        for (const block of blocksToShift) {
          await window.apiService.updateBlock(block.uuid, {
            content: block.content,
            parent: block.parent ? block.parent.uuid : null,
            order: block.order + 1,
          });
          // Update local state
          block.order = block.order + 1;
        }

        // Create the new block at the desired position
        return await this.handleCreateBlock({
          content: "",
          parent: currentBlock.parent,
          order: newOrder,
          autoFocus: true,
        });
      } catch (error) {
        console.error("Failed to create block after current:", error);
        this.error = "Failed to create block";
        return { success: false };
      }
    },

    handleDocumentClick(event) {
      const contextMenuContainer = event.target.closest(
        ".context-menu-container"
      );

      if (!contextMenuContainer && this.showContextMenu) {
        this.closeContextMenu();
      }

      if (!contextMenuContainer && this.showPageMenu) {
        this.closePageMenu();
      }
    },

    closeContextMenu() {
      this.showContextMenu = false;
    },

    // Page menu methods
    togglePageMenu() {
      this.showPageMenu = !this.showPageMenu;
    },

    closePageMenu() {
      this.showPageMenu = false;
    },

    async deletePage() {
      if (!this.page) return;

      const confirmed = confirm(
        `Are you sure you want to delete the page "${this.page.title}"? This will also delete all direct blocks and cannot be undone.`
      );

      if (!confirmed) return;

      try {
        const result = await window.apiService.deletePage(this.page.uuid);
        if (result.success) {
          this.closePageMenu();
          // Navigate to today's page after deletion
          const today = new Date();
          const year = today.getFullYear();
          const month = String(today.getMonth() + 1).padStart(2, "0");
          const day = String(today.getDate()).padStart(2, "0");
          const todayString = `${year}-${month}-${day}`;
          window.location.href = `/knowledge/page/${todayString}/`;
        } else {
          this.error = "Failed to delete page";
        }
      } catch (error) {
        console.error("Failed to delete page:", error);
        this.error = "Failed to delete page";
      }
    },

    async moveUndoneTodos() {
      if (!this.page) return;

      try {
        const targetDate = this.isDaily
          ? this.currentDate || this.page.date
          : null;
        const result = await window.apiService.moveUndoneTodos(targetDate);

        if (result.success) {
          this.closePageMenu();
          const movedCount = result.data.moved_count;
          const message = result.data.message;

          if (movedCount > 0) {
            this.$parent.addToast(
              `Moved ${movedCount} undone TODOs to ${this.page.title}`,
              "success"
            );
            // Reload the page to show the moved todos
            await this.loadPage();
          } else {
            this.$parent.addToast(
              message || "No undone TODOs found to move",
              "info"
            );
          }
        } else {
          this.error = "Failed to move undone TODOs";
          this.$parent.addToast("Failed to move undone TODOs", "error");
        }
      } catch (error) {
        console.error("Failed to move undone TODOs:", error);
        this.error = "Failed to move undone TODOs";
        this.$parent.addToast("Failed to move undone TODOs", "error");
      }
    },

    // Date navigation methods
    onDateChange() {
      if (this.selectedDate) {
        window.location.href = `/knowledge/page/${this.selectedDate}/`;
      }
    },

    initializeDateSelector() {
      if (this.isDaily && this.currentDate) {
        this.selectedDate = this.currentDate;
      } else if (this.isDaily && this.page?.date) {
        this.selectedDate = this.page.date;
      }
    },

    handleTagClick(event) {
      if (event.target.classList.contains("clickable-tag")) {
        event.preventDefault();
        const tagName = event.target.getAttribute("data-tag");
        if (tagName) {
          this.goToTag(tagName);
        }
      }
    },

    goToTag(tagName) {
      const url = `/knowledge/page/${encodeURIComponent(tagName)}/`;
      window.location.href = url;
    },

    formatContentWithTags(content) {
      if (!content) return "";
      return content.replace(
        /#([a-zA-Z0-9_-]+)/g,
        '<span class="inline-tag clickable-tag" data-tag="$1">#$1</span>'
      );
    },

    formatDate(dateString) {
      const [year, month, day] = dateString.split("-");
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString();
    },

    onBlockAddToContext(block) {
      this.$emit("block-add-to-context", block);
    },

    onBlockRemoveFromContext(blockId) {
      this.$emit("block-remove-from-context", blockId);
    },

    // Page-specific methods (copied from PagePage)
    async updatePageTitle() {
      if (!this.page || !this.newTitle.trim()) {
        this.isEditingTitle = false;
        this.newTitle = this.page?.title || "";
        return;
      }

      try {
        const result = await window.apiService.updatePage(this.page.uuid, {
          title: this.newTitle.trim(),
        });

        if (result.success) {
          this.page.title = this.newTitle.trim();
          this.isEditingTitle = false;
          this.$parent.addToast("Page title updated successfully", "success");
        } else {
          this.error = "Failed to update page title";
        }
      } catch (error) {
        console.error("Failed to update page title:", error);
        this.error = "Failed to update page title";
      }
    },

    startEditingTitle() {
      this.isEditingTitle = true;
      this.newTitle = this.page?.title || "";
      this.$nextTick(() => {
        const input = this.$refs.titleInput;
        if (input) {
          input.focus();
          input.select();
        }
      });
    },

    cancelEditingTitle() {
      this.isEditingTitle = false;
      this.newTitle = this.page?.title || "";
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
            this.directBlocks.push(block);
            this.directBlocks.sort((a, b) => a.order - b.order);
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
      const siblings = block.parent ? block.parent.children : this.directBlocks;
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
        const index = this.directBlocks.findIndex((b) => b.uuid === block.uuid);
        if (index !== -1) {
          this.directBlocks.splice(index, 1);
        }
      }
    },

    updateSiblingOrders(parent, fromOrder) {
      const siblings = parent ? parent.children : this.directBlocks;
      siblings.forEach((sibling) => {
        if (sibling.order >= fromOrder) {
          sibling.order += 1;
        }
      });
    },

    // Referenced Block Editing Methods
    startEditingReferencedBlock(block) {
      block.isEditing = true;
      this.$nextTick(() => {
        // Find the textarea for this specific block using the data attribute
        const textarea = document.querySelector(
          `[data-block-uuid="${block.uuid}"] .block-content`
        );
        if (textarea) {
          textarea.focus();
          textarea.select();
        }
      });
    },

    async stopEditingReferencedBlock(block) {
      if (!block.isEditing) return;

      try {
        // Update the block content via API
        const result = await window.apiService.updateBlock(block.uuid, {
          content: block.content,
        });

        if (result.success) {
          // Update the block with the response data
          Object.assign(block, result.data);
          block.isEditing = false;

          // Refresh the page context since the block might have new tags
          await this.loadPage();
        } else {
          console.error("Failed to update referenced block:", result.error);
          // Revert changes on failure
          block.isEditing = false;
        }
      } catch (error) {
        console.error("Error updating referenced block:", error);
        block.isEditing = false;
      }
    },

    handleReferencedBlockKeyDown(block, event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        this.stopEditingReferencedBlock(block);
      } else if (event.key === "Escape") {
        event.preventDefault();
        // Cancel editing without saving
        block.isEditing = false;
      }
    },

    async handleToggleReferencedBlockTodo(block) {
      if (block.block_type === "todo") {
        await this.updateReferencedBlockType(block, "done");
      } else if (block.block_type === "done") {
        await this.updateReferencedBlockType(block, "bullet");
      } else {
        await this.updateReferencedBlockType(block, "todo");
      }
    },

    async updateReferencedBlockType(block, newType) {
      try {
        const result = await window.apiService.updateBlock(block.uuid, {
          block_type: newType,
        });

        if (result.success) {
          block.block_type = newType;

          // Refresh the page context since the block type changed
          await this.loadPage();
        } else {
          console.error(
            "Failed to update referenced block type:",
            result.error
          );
        }
      } catch (error) {
        console.error("Error updating referenced block type:", error);
      }
    },

    toggleReferencedBlockContext(block) {
      if (this.isBlockInContext(block.uuid)) {
        this.onBlockRemoveFromContext(block.uuid);
      } else {
        this.onBlockAddToContext(block);
      }
    },
  },

  template: `
    <div class="page-page">
      <!-- Loading State -->
      <div v-if="loading" class="loading">
        Loading page...
      </div>

      <!-- Error State -->
      <div v-if="error" class="error">
        {{ error }}
      </div>

      <!-- Page Content -->
      <div v-else-if="page" class="page-content">
        <!-- Page Header -->
        <div class="page-header">
          <div class="page-title-container">
            <!-- Daily Note Header -->
            <div v-if="isDaily" class="daily-note-title current-note page-header-flex">
              <div class="title-left">
                <input
                  type="date"
                  v-model="selectedDate"
                  @change="onDateChange"
                  class="date-picker"
                  title="Navigate to date"
                />
              </div>
              <div class="header-controls">
                <div class="context-menu-container">
                  <button @click="togglePageMenu" class="btn btn-outline context-menu-btn" title="Daily note options">
                    ⋮
                  </button>
                  <div v-if="showPageMenu" class="context-menu" @click.stop>
                    <button @click="moveUndoneTodos" class="context-menu-item" :disabled="loading">
                      move undone TODOs here
                    </button>
                    <button @click="deletePage" class="context-menu-item context-menu-danger">
                      delete page
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Regular Page Title (Editable) -->
            <div v-else class="page-title-container page-header-flex">
              <div class="page-header-flex-left">
                <div v-if="!isEditingTitle" class="page-title-display">
                  <h1 class="page-title-text">{{ page.title || 'Untitled Page' }}</h1>
                </div>
                <div v-else class="page-title-edit">
                  <input
                    ref="titleInput"
                    v-model="newTitle"
                    @keyup.enter="updatePageTitle"
                    @keyup.escape="cancelEditingTitle"
                    @blur="updatePageTitle"
                    class="form-control page-title-input"
                    placeholder="Enter page title"
                  />
                  <button @click="updatePageTitle" class="btn btn-success save-title-btn" title="Save title">
                    ✓
                  </button>
                  <button @click="cancelEditingTitle" class="btn btn-outline cancel-title-btn" title="Cancel">
                    ✗
                  </button>
                </div>
              </div>
              <div class="page-actions">
                <div class="context-menu-container">
                  <button @click="togglePageMenu" class="btn btn-outline context-menu-btn" title="Page options">
                    ⋮
                  </button>
                  <div v-if="showPageMenu" class="context-menu" @click.stop>
                    <button @click="startEditingTitle" class="context-menu-item">
                      edit title
                    </button>
                    <button @click="deletePage" class="context-menu-item context-menu-danger">
                      delete page
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Direct Blocks Section -->
        <div class="direct-blocks-section">
          <Page
            :page="page"
            :blocks="directBlocks"
            :loading="loading"
            :error="error"
            :chat-context-blocks="chatContextBlocks"
            :is-block-in-context="isBlockInContext"
            @create-block="handleCreateBlock"
            @create-block-after="handleCreateBlockAfter"
            @update-block="handleUpdateBlock"
            @delete-block="handleDeleteBlock"
            @toggle-block-todo="handleToggleBlockTodo"
            @indent-block="handleIndentBlock"
            @outdent-block="handleOutdentBlock"
            @block-add-to-context="onBlockAddToContext"
            @block-remove-from-context="onBlockRemoveFromContext"
          />
        </div>

        <!-- Linked References Section (Logseq style) -->
        <div v-if="hasReferencedBlocks" class="linked-references-section">
          <h3 class="linked-references-title">
            {{ totalReferencedBlocks }} Linked Reference{{ totalReferencedBlocks !== 1 ? 's' : '' }}
          </h3>
          
          <div class="referenced-blocks-container">
            <div v-for="block in referencedBlocks" :key="block.uuid" class="referenced-block-wrapper" :class="{ 'in-context': isBlockInContext(block.uuid) }" :data-block-uuid="block.uuid">
              <div class="block">
                <div
                  class="block-bullet"
                  :class="{ 'todo': block.block_type === 'todo', 'done': block.block_type === 'done' }"
                  @click="handleToggleReferencedBlockTodo(block)"
                >
                  <span v-if="block.block_type === 'todo'">☐</span>
                  <span v-else-if="block.block_type === 'done'">☑</span>
                  <span v-else>•</span>
                </div>
                <div class="block-content-wrapper">
                  <div class="block-meta">
                    <span class="page-title">{{ block.page_type === 'daily' ? formatDate(block.page_title) : block.page_title }}</span>
                    <span v-if="block.page_date" class="page-date">{{ formatDate(block.page_date) }}</span>
                  </div>
                  <div 
                    v-if="!block.isEditing"
                    class="block-content-display" 
                    :class="{ 'completed': block.block_type === 'done' }"
                    @click="startEditingReferencedBlock(block)"
                  >
                    <div v-html="formatContentWithTags(block.content)" class="block-text"></div>
                  </div>
                  <div v-else class="block-content-edit">
                    <textarea
                      v-model="block.content"
                      @blur="stopEditingReferencedBlock(block)"
                      @keydown="handleReferencedBlockKeyDown(block, $event)"
                      class="block-content"
                      :class="{ 'completed': block.block_type === 'done' }"
                      :placeholder="'Enter content...'"
                      ref="referencedBlockTextarea"
                    ></textarea>
                  </div>
                </div>
                <button
                  @click="toggleReferencedBlockContext(block)"
                  class="block-context"
                  :class="{ active: isBlockInContext(block.uuid) }"
                  :title="isBlockInContext(block.uuid) ? 'Remove from chat context' : 'Add to chat context'"
                >{{ isBlockInContext(block.uuid) ? '-' : '+' }}</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="totalDirectBlocks === 0 && !hasReferencedBlocks" class="no-content">
          <p>This page is empty. Start typing to add content.</p>
        </div>
      </div>
    </div>
  `,
};

// Register component globally
window.PagePage = PagePage;
