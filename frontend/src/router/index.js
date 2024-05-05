import { useVespaStore } from '@/stores/vespaStore';
import { createRouter, createWebHistory } from 'vue-router';
import ChangePasswordPage from '../components/ChangePasswordPage.vue';
import Login from '../components/LoginPage.vue';
import MapPage from '../components/MapPage.vue';
import TableViewPage from '../components/TableViewPage.vue';

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
  { path: '/map/observation/:id', component: MapPage },
  {
    path: '/table',
    name: 'TableView',
    component: TableViewPage
  },
  {
    path: '/',
    name: 'Home',
    component: MapPage
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    component: ChangePasswordPage
  }
];

const router = createRouter({
  history: createWebHistory('/'),
  routes,
});

router.beforeEach(async (to, from, next) => {
  const vespaStore = useVespaStore();
  if (to.meta.requiresAuth && !vespaStore.isLoggedIn) {
    next({ name: 'Login' });
  } else {
    next();
  }
});
export default router;
