import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/LoginPage.vue';
import MapPage from '../components/MapPage.vue';
import store from '../store';

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

router.beforeEach(async (to, from, next) => {
  if (!store.state.isLoggedIn) {
    await store.dispatch('fetchUserStatus');
  }
  next();
});

export default router;
