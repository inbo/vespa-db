import { useVespaStore } from '@/stores/vespaStore';
import { createRouter, createWebHashHistory } from 'vue-router';
import { defineAsyncComponent } from 'vue';
const ModalMessage = defineAsyncComponent(() => import('@/components/ModalMessage.vue'));
const ChangePasswordPage = () => import('../components/ChangePasswordPage.vue');
const Login = () => import('../components/LoginPage.vue');
const MapPage = () => import('../components/MapPage.vue');

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/map',
    redirect: '/'
  },
  {
    path: '/observation/:id',
    name: 'ObservationDetailMap',
    component: MapPage,
    meta: { 
      activeView: 'map' 
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