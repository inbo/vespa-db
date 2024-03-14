import { createRouter, createWebHistory } from 'vue-router';
//import Login from '../components/Login.vue';
import MapPage from '../components/MapPage.vue';
import store from '../store';

const routes = [
  // {
  //   path: '/login',
  //   name: 'Login',
  //   component: Login
  // },
  {
    path: '/map',
    name: 'MapPage',
    component: MapPage
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  if (!store.state.isLoggedIn) {
    await store.dispatch('checkLoginStatus');
  }
  next();
});

export default router;
