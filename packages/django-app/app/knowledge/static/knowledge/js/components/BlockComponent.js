const BlockComponent = {
  name: 'BlockComponent',
  props: {
    block: {
      type: Object,
      required: true
    },
    onBlockContentChange: {
      type: Function,
      required: true
    },
    onBlockKeyDown: {
      type: Function,
      required: true
    },
    startEditing: {
      type: Function,
      required: true
    },
    stopEditing: {
      type: Function,
      required: true
    },
    deleteBlock: {
      type: Function,
      required: true
    },
    toggleBlockTodo: {
      type: Function,
      required: true
    },
    formatContentWithTags: {
      type: Function,
      required: true
    },
    // Drag and drop props
    onDragStart: {
      type: Function,
      required: true
    },
    onDragEnd: {
      type: Function,
      required: true
    },
    onDragOver: {
      type: Function,
      required: true
    },
    onDrop: {
      type: Function,
      required: true
    },
    isDragging: {
      type: Boolean,
      default: false
    },
    dragOverPosition: {
      type: String,
      default: null // 'before', 'after', 'inside'
    }
  },
  template: `
    <div 
      class="block-wrapper" 
      :class="{ 
        'child-block': block.parent,
        'dragging': isDragging,
        'drag-over-before': dragOverPosition === 'before',
        'drag-over-after': dragOverPosition === 'after',
        'drag-over-inside': dragOverPosition === 'inside'
      }" 
      :data-block-id="block.id"
    >
      <!-- Drop zone before block -->
      <div 
        class="drop-zone drop-zone-before"
        @dragover.prevent="onDragOver($event, block, 'before')"
        @drop.prevent="onDrop($event, block, 'before')"
      ></div>
      
      <div 
        class="block"
        draggable="true"
        @dragstart="onDragStart($event, block)"
        @dragend="onDragEnd($event, block)"
      >
        <div
          class="block-bullet drag-handle"
          :class="{ 'todo': block.block_type === 'todo', 'done': block.block_type === 'done' }"
          @click="block.block_type === 'todo' || block.block_type === 'done' ? toggleBlockTodo(block) : null"
          title="Click to toggle todo or drag to reorder"
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
      
      <!-- Drop zone after block (for nesting) -->
      <div 
        class="drop-zone drop-zone-inside"
        @dragover.prevent="onDragOver($event, block, 'inside')"
        @drop.prevent="onDrop($event, block, 'inside')"
      ></div>
      
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
          :onDragStart="onDragStart"
          :onDragEnd="onDragEnd"
          :onDragOver="onDragOver"
          :onDrop="onDrop"
          :isDragging="false"
          :dragOverPosition="null"
        />
      </div>
      
      <!-- Drop zone after block -->
      <div 
        class="drop-zone drop-zone-after"
        @dragover.prevent="onDragOver($event, block, 'after')"
        @drop.prevent="onDrop($event, block, 'after')"
      ></div>
    </div>
  `
};

// Make it available globally
window.BlockComponent = BlockComponent;