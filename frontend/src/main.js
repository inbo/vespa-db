import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import './assets/style.css'
import 'leaflet/dist/leaflet.css';
import '@fortawesome/fontawesome-free/css/all.css';

createApp(App).use(router).mount('#app');