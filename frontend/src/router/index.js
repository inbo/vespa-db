import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/LoginPage.vue';
import MapPage from '../components/MapPage.vue';
import appAuthStore from '../store';


const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/map',
    name: 'MapPage',
    component: MapPage
  },
  {
    path: '/',
    name: 'Home',
    component: MapPage
  }
];

const router = createRouter({
  history: createWebHistory('/'),
  routes,
});

Router.beforeEach(() => {
  appAuthStore.authCheck();
});

export default router;
