// ToastNotifications Component - Global toast notification system
const ToastNotifications = {
  props: {
    toasts: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["remove-toast"],

  methods: {
    removeToast(toastId) {
      this.$emit("remove-toast", toastId);
    },

    getToastIcon(type) {
      switch (type) {
        case "success":
          return "✓";
        case "error":
          return "✗";
        case "warning":
          return "⚠";
        case "info":
          return "ℹ";
        default:
          return "";
      }
    },
  },

  template: `
    <div class="toast-container">
      <transition-group name="toast" tag="div" class="toast-list">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', 'toast-' + toast.type]"
          @click="removeToast(toast.id)"
        >
          <div class="toast-content">
            <span class="toast-icon">{{ getToastIcon(toast.type) }}</span>
            <span class="toast-message">{{ toast.message }}</span>
            <button 
              class="toast-close"
              @click.stop="removeToast(toast.id)"
              title="Close notification"
            >
              ×
            </button>
          </div>
        </div>
      </transition-group>
    </div>
  `,
};

// Register component globally
window.ToastNotifications = ToastNotifications;
