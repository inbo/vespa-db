import { useVespaStore } from '@/stores/vespaStore';
import { createRouter, createWebHashHistory } from 'vue-router';
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
    name: 'map',
    component: MapPage,
    meta: { 
      activeView: 'map' 
    }
  },
  {
    path: '/map/observation/:id',
    name: 'ObservationDetailMap',
    component: MapPage,
    meta: { 
      activeView: 'map' 
    }
  },
  {
    path: '/table/observation/:id',
    name: 'ObservationDetailTable',
    component: TableViewPage,
    meta: { 
      activeView: 'table' 
    }
  },
  {
    path: '/table',
    name: 'TableView',
    component: TableViewPage,
    meta: { 
      activeView: 'table' 
    }
  },
  {
    path: '/',
    name: 'Home',
    component: MapPage,
    meta: { 
      activeView: 'map' 
    }
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    component: ChangePasswordPage
  }
];

const router = createRouter({
  history: createWebHashHistory(),
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