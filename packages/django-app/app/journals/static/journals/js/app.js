const { createApp } = Vue;

// Global Vue app for journals
const JournalsApp = createApp({
    data() {
        return {
            message: 'Journals Vue App Loaded'
        }
    },
    mounted() {
        console.log('Journals app mounted');
    }
});

// Mount the app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    JournalsApp.mount('#app');
});