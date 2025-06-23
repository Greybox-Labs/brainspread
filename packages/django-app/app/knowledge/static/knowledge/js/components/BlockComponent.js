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
  },
  template: `
    <div class="block-wrapper" :class="{ 'child-block': block.parent }" :data-block-id="block.id">
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
      
      <!-- Recursively render children -->
      <div v-if="block.children && block.children.length" class="block-children">
        <BlockComponent
          v-for="child in block.children"
          :key="child.id"
          :block="child"
          :onBlockContentChange="onBlockContentChange"
          :onBlockKeyDown="onBlockKeyDown"
          :startEditing="startEditing"
          :stopEditing="stopEditing"
          :deleteBlock="deleteBlock"
          :toggleBlockTodo="toggleBlockTodo"
          :formatContentWithTags="formatContentWithTags"
        />
      </div>
    </div>
  `,
};

// Make it available globally
window.BlockComponent = BlockComponent;
