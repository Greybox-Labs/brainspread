// Page Component - Generic page renderer for blocks
const Page = {
  components: {
    BlockComponent: window.BlockComponent || {},
  },
  props: {
    page: {
      type: Object,
      required: true,
    },
    blocks: {
      type: Array,
      default: () => [],
    },
    chatContextBlocks: {
      type: Array,
      default: () => [],
    },
    isBlockInContext: {
      type: Function,
      default: () => () => false,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    error: {
      type: String,
      default: null,
    },
    successMessage: {
      type: String,
      default: "",
    },
  },
  emits: [
    "block-add-to-context",
    "block-remove-from-context",
    "visible-blocks-changed",
    "create-block",
    "update-block",
    "delete-block",
    "toggle-block-todo",
    "indent-block",
    "outdent-block",
    "focus-next-block",
    "focus-previous-block",
    "start-editing",
    "stop-editing",
  ],
  data() {
    return {
      // Track blocks being deleted to prevent save conflicts
      deletingBlocks: new Set(),
      isNavigating: false,
    };
  },

  mounted() {
    // Add event delegation for clickable hashtags in content
    document.addEventListener("click", this.handleTagClick);
  },

  beforeUnmount() {
    // Clean up event listeners
    document.removeEventListener("click", this.handleTagClick);
  },

  methods: {
    async createBlock(
      content = "",
      parent = null,
      order = null,
      autoFocus = true
    ) {
      this.$emit("create-block", { content, parent, order, autoFocus });
    },

    async updateBlock(block, newContent, skipReload = false) {
      this.$emit("update-block", { block, newContent, skipReload });
    },

    async deleteBlock(block) {
      this.$emit("delete-block", block);
    },

    async deleteEmptyBlock(block) {
      // Mark block as being deleted to prevent save conflicts
      this.deletingBlocks.add(block.uuid);

      // Find the previous block to focus after deletion
      const previousBlock = this.findPreviousBlock(block);

      try {
        await this.deleteBlock(block);

        // Focus the previous block if it exists
        if (previousBlock) {
          this.$nextTick(() => {
            this.startEditing(previousBlock);
            // Position cursor at the end of the previous block
            this.$nextTick(() => {
              const textarea = document.querySelector(
                `[data-block-uuid="${previousBlock.uuid}"] textarea`
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
      } catch (error) {
        console.error("Failed to delete empty block:", error);
        // Remove from deleting set on error
        this.deletingBlocks.delete(block.uuid);
      } finally {
        // Clean up tracking after a delay to ensure blur events have processed
        setTimeout(() => {
          this.deletingBlocks.delete(block.uuid);
        }, 100);
      }
    },

    findPreviousBlock(currentBlock) {
      const allBlocks = this.getAllBlocks();
      const currentIndex = allBlocks.findIndex(
        (b) => b.uuid === currentBlock.uuid
      );
      return currentIndex > 0 ? allBlocks[currentIndex - 1] : null;
    },

    async toggleBlockTodo(block) {
      this.$emit("toggle-block-todo", block);
    },

    getNextOrder(parent) {
      const siblings = parent ? parent.children : this.blocks;
      return siblings.length > 0
        ? Math.max(...siblings.map((b) => b.order)) + 1
        : 0;
    },

    async createBlockAfter(currentBlock) {
      const newOrder = currentBlock.order + 1;
      const siblings = currentBlock.parent
        ? currentBlock.parent.children
        : this.blocks;

      // Find all blocks that need to be shifted (same parent, order >= newOrder)
      const blocksToShift = siblings.filter(
        (block) => block.uuid !== currentBlock.uuid && block.order >= newOrder
      );

      // Shift existing blocks down by updating their orders
      for (const block of blocksToShift) {
        await this.updateBlock(block, block.content, true);
        block.order = block.order + 1;
      }

      // Create the new block at the desired position
      await this.createBlock("", currentBlock.parent, newOrder);
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
        await this.createBlockAfter(block);
      } else if (
        event.key === "Backspace" &&
        block.content.trim() === "" &&
        event.target.selectionStart === 0
      ) {
        event.preventDefault();
        // If block has children (is a parent), delete it and go to previous block
        if (block.children && block.children.length > 0) {
          await this.deleteEmptyBlock(block);
        } else if (block.parent) {
          // If block has no children but has a parent, unindent it
          await this.outdentBlock(block);
        } else {
          // If block is at root level with no children, delete it
          await this.deleteEmptyBlock(block);
        }
      } else if (event.key === " ") {
        // Handle double-space indentation for mobile users
        const textarea = event.target;
        const currentContent = textarea.value;
        const cursorPos = textarea.selectionStart;

        // Check if the previous character is also a space (double-space) AND we're at the beginning of the block
        if (
          cursorPos > 0 &&
          currentContent[cursorPos - 1] === " " &&
          cursorPos <= 2
        ) {
          event.preventDefault();
          // Remove the current space that would be added and the previous space
          const newContent =
            currentContent.slice(0, cursorPos - 1) +
            currentContent.slice(cursorPos);
          block.content = newContent;

          // Update textarea value and cursor position
          textarea.value = newContent;
          textarea.setSelectionRange(cursorPos - 1, cursorPos - 1);

          // Save current content and indent the block
          await this.updateBlock(block, newContent, true);
          await this.indentBlock(block);
        }
      } else if (event.key === "Tab") {
        event.preventDefault();
        if (event.shiftKey) {
          // Outdent - move block to parent's level
          await this.outdentBlock(block);
        } else {
          // Indent - make this block a child of the previous sibling
          await this.indentBlock(block);
        }
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

    async indentBlock(block) {
      this.$emit("indent-block", block);
    },

    async outdentBlock(block) {
      this.$emit("outdent-block", block);
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

    startEditing(block) {
      // Stop editing all other blocks first (save them)
      const allBlocks = this.getAllBlocks();
      allBlocks.forEach((b) => {
        if (b.uuid !== block.uuid && b.isEditing) {
          this.updateBlock(b, b.content, true); // Save without reload
          b.isEditing = false;
        }
      });

      block.isEditing = true;
      this.$nextTick(() => {
        // Focus the specific textarea for this block
        const blockElement = document.querySelector(
          `[data-block-uuid="${block.uuid}"] textarea`
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

      // Don't try to save blocks that are being deleted
      if (this.deletingBlocks.has(block.uuid)) {
        block.isEditing = false;
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
      const currentIndex = allBlocks.findIndex(
        (b) => b.uuid === currentBlock.uuid
      );

      if (currentIndex >= 0 && currentIndex < allBlocks.length - 1) {
        const nextBlock = allBlocks[currentIndex + 1];
        this.isNavigating = true;
        this.startEditing(nextBlock);
      }
    },

    focusPreviousBlock(currentBlock) {
      const allBlocks = this.getAllBlocks();
      const currentIndex = allBlocks.findIndex(
        (b) => b.uuid === currentBlock.uuid
      );

      if (currentIndex > 0) {
        const previousBlock = allBlocks[currentIndex - 1];
        this.isNavigating = true;
        this.startEditing(previousBlock);
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
    <div class="page-content">
      <div v-if="loading" class="loading">Loading page...</div>
      
      <div v-else-if="page" class="page-blocks">
        <div class="blocks-container">
          <BlockComponent
            v-for="block in blocks"
            :key="block.uuid"
            :block="block"
            :onBlockContentChange="onBlockContentChange"
            :onBlockKeyDown="onBlockKeyDown"
            :startEditing="startEditing"
            :stopEditing="stopEditing"
            :deleteBlock="deleteBlock"
            :toggleBlockTodo="toggleBlockTodo"
            :formatContentWithTags="formatContentWithTags"
            :isBlockInContext="isBlockInContext"
            :onBlockAddToContext="onBlockAddToContext"
            :onBlockRemoveFromContext="onBlockRemoveFromContext"
          />
          <button @click="addNewBlock" class="add-block-btn">
            + add new block
          </button>
        </div>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>
    </div>
  `,
};

// Register component globally
window.Page = Page;
