window.HistoricalDailyNoteBlocks = {
  props: ["page"],

  data() {
    return {
      blocks: [],
      loading: false,
    };
  },

  async mounted() {
    await this.loadBlocks();
  },

  methods: {
    async loadBlocks() {
      if (!this.page || !this.page.date) return;

      this.loading = true;
      try {
        const result = await window.apiService.getPageWithBlocks(
          null,
          this.page.date
        );
        if (result.success) {
          this.blocks = result.data.blocks || [];
        }
      } catch (error) {
        console.error("Failed to load historical blocks:", error);
      } finally {
        this.loading = false;
      }
    },

    // Block management methods (same as DailyNote)
    async createBlock(content, parentId = null, order = null) {
      if (!content.trim()) return;

      if (order === null) {
        order = parentId ? 0 : this.blocks.filter((b) => !b.parent_id).length;
      }

      try {
        const result = await window.apiService.createBlock({
          page: this.page.uuid,
          content: content.trim(),
          parent: parentId,
          order: order,
        });

        if (result.success) {
          await this.loadBlocks(); // Reload blocks
        }
      } catch (error) {
        console.error("Failed to create block:", error);
      }
    },

    async updateBlock(block, newContent, skipReload = false) {
      if (!block.uuid) return;

      try {
        const result = await window.apiService.updateBlock(block.uuid, {
          content: newContent,
        });

        if (result.success && !skipReload) {
          await this.loadBlocks();
        }
      } catch (error) {
        console.error("Failed to update block:", error);
      }
    },

    async deleteBlock(block) {
      if (!block.uuid) return;

      try {
        const result = await window.apiService.deleteBlock(block.uuid);

        if (result.success) {
          await this.loadBlocks();
        }
      } catch (error) {
        console.error("Failed to delete block:", error);
      }
    },

    async toggleBlockTodo(block) {
      if (!block.uuid) return;

      try {
        const result = await window.apiService.toggleBlockTodo(block.uuid);
        if (result.success) {
          await this.loadBlocks();
        }
      } catch (error) {
        console.error("Failed to toggle block todo:", error);
      }
    },

    formatContentWithTags(content) {
      if (!content) return "";
      return content.replace(
        /#([a-zA-Z0-9_-]+)/g,
        '<span class="inline-tag">#$1</span>'
      );
    },

    startEditing(block) {
      // Stop editing all other blocks first
      this.getAllBlocks().forEach((b) => {
        if (b.uuid !== block.uuid && b.isEditing) {
          this.updateBlock(b, b.content, true);
          b.isEditing = false;
        }
      });

      block.isEditing = true;
      this.$nextTick(() => {
        const blockElement = document.querySelector(
          `[data-block-uuid="${block.uuid}"] textarea`
        );
        if (blockElement) {
          blockElement.focus();
        }
      });
    },

    stopEditing(block) {
      if (block.isEditing) {
        this.updateBlock(block, block.content);
        block.isEditing = false;
      }
    },

    onBlockContentChange(block, newContent) {
      block.content = newContent;
    },

    getAllBlocks() {
      const flattenBlocks = (blocks) => {
        let result = [];
        blocks.forEach((block) => {
          result.push(block);
          if (block.children) {
            result = result.concat(flattenBlocks(block.children));
          }
        });
        return result;
      };
      return flattenBlocks(this.blocks);
    },

    addNewBlock() {
      this.createBlock("");
    },

    onBlockKeyDown(event, block) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        this.createBlock("", block.parent_id, block.order + 1);
      }
    },
  },

  template: `
    <div class="historical-blocks-container">
      <div v-if="loading" class="loading">Loading blocks...</div>

      <div v-else class="blocks-container">
        <div v-for="block in blocks" :key="block.uuid" class="block-wrapper" :data-block-uuid="block.uuid">
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

          <!-- Render children blocks recursively -->
          <div v-if="block.children && block.children.length" class="block-children">
            <div v-for="child in block.children" :key="child.uuid" class="block-wrapper child-block" :data-block-uuid="child.uuid">
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
  `,
};
