<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-success">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">VespaWatch Dashboard</a>
      <div class="d-flex">
        <span v-if="isLoggedIn" class="navbar-text">
          <div class="btn-group">
            <button type="button" class="btn btn-outline-light dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
              Menu
            </button>
            <ul class="dropdown-menu">
              <li><button class="dropdown-item" @click="logout">Uitloggen</button></li>
              <li><button class="dropdown-item" @click="navigateToChangePassword">Change Password</button></li>
            </ul>
          </div>
        </span>
        <a v-else href="/login" class="btn btn-outline-light ms-2">Inloggen</a>
      </div>
    </div>
  </nav>
</template>
<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed } from 'vue';
import { useRouter } from 'vue-router';

export default {
  setup() {
    const router = useRouter();
    const vespaStore = useVespaStore();
    const isLoggedIn = computed(() => vespaStore.isLoggedIn);
    const username = computed(() => vespaStore.user.username);

    const logout = async () => {
      await vespaStore.logout();
      router.push('/login');
    };
    const navigateToChangePassword = () => {
      router.push({ name: 'ChangePassword' });
    };
    return { isLoggedIn, username, logout, navigateToChangePassword };
  },
};
</script>