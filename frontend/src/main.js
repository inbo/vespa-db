// main.js

// Import necessary modules
import { registerPlugins } from '@/plugins';
import { createPinia } from 'pinia';
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { useVespaStore } from './stores/vespaStore';

// Import CSS
import '@fortawesome/fontawesome-free/css/all.css';
import 'leaflet/dist/leaflet.css';
import './assets/style.css';

import 'bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';


const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

registerPlugins(app);

// Initialize and use the vespaStore for authentication check
const vespaStore = useVespaStore();
vespaStore.authCheck();

app.mount('#app');
