import '@fortawesome/fontawesome-free/css/all.css';
import 'leaflet/dist/leaflet.css';
import { createApp } from 'vue';
import App from './App.vue';
import './assets/style.css';
import router from './router';
import store from './store';

createApp(App).use(store).use(router).mount('#app');