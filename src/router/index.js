import { useVespaStore } from '@/stores/vespaStore';
import { createRouter, createWebHashHistory } from 'vue-router';
import { defineAsyncComponent } from 'vue';
const ModalMessage = defineAsyncComponent(() => import('@/components/ModalMessage.vue'));
const ChangePasswordPage = () => import('../components/ChangePasswordPage.vue');
const Login = () => import('../components/LoginPage.vue');
const MapPage = () => import('../components/MapPage.vue');
const TableViewPage = () => import('../components/TableViewPage.vue');

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