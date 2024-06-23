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
import 'bootstrap/dist/css/bootstrap.min.css';
import 'leaflet/dist/leaflet.css';
import './assets/style.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

registerPlugins(app);

const vespaStore = useVespaStore();
vespaStore.authCheck();

app.mount('#app');
