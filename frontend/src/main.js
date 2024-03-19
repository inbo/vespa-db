/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins';
import '@fortawesome/fontawesome-free/css/all.css';
import 'leaflet/dist/leaflet.css';
import './assets/style.css';

// Components
import App from './App.vue';
import router from './router';
import store from './store';

// Composables
import { createApp } from 'vue';

const app = createApp(App)

app.use(store)
app.use(router)

registerPlugins(app)

app.mount('#app')