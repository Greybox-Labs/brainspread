const BlockComponent = {
  name: "BlockComponent",
  props: {
    block: {
      type: Object,
      required: true,
    },
    onBlockContentChange: {
      type: Function,
      required: true,
    },
    onBlockKeyDown: {
      type: Function,
      required: true,
    },
    startEditing: {
      type: Function,
      required: true,
    },
    stopEditing: {
      type: Function,
      required: true,
    },
    deleteBlock: {
      type: Function,
      required: true,
    },
    toggleBlockTodo: {
      type: Function,
      required: true,
    },
    formatContentWithTags: {
      type: Function,
      required: true,
    },
    // Context-related props
    isBlockInContext: {
      type: Function,
      default: () => () => false,
    },
    onBlockAddToContext: {
      type: Function,
      default: () => () => {},
    },
    onBlockRemoveFromContext: {
      type: Function,
      default: () => () => {},
    },
  },
  computed: {
    blockInContext() {
      return this.isBlockInContext(this.block.uuid);
    },
  },
  methods: {
    toggleBlockContext() {
      if (this.blockInContext) {
        this.onBlockRemoveFromContext(this.block.uuid);
      } else {
        this.onBlockAddToContext(this.block);
      }
    },
  },
  template: `
    <div class="block-wrapper" :class="{ 'child-block': block.parent, 'in-context': blockInContext }" :data-block-uuid="block.uuid">
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
          @click="toggleBlockContext"
          class="block-context"
          :class="{ active: blockInContext }"
          :title="blockInContext ? 'Remove from chat context' : 'Add to chat context'"
        >{{ blockInContext ? '-' : '+' }}</button>
        <button
          @click="deleteBlock(block)"
          class="block-delete"
          title="Delete block"
        >del</button>
      </div>
      
      <!-- Recursively render children -->
      <div v-if="block.children && block.children.length" class="block-children">
        <BlockComponent
          v-for="child in block.children"
          :key="child.uuid"
          :block="child"
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
      </div>
    </div>
  `,
};

// Make it available globally
window.BlockComponent = BlockComponent;
