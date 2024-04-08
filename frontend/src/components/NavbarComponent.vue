<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-success">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">VespaWatch Dashboard</a>
      <div class="d-flex align-items-center">
        <!-- View Mode Toggle -->
        <div class="btn-group me-2" role="group">
          <input type="radio" class="btn-check" name="viewMode" id="mapView" autocomplete="off" :checked="viewMode === 'map'" @change="setViewMode('map')">
          <label class="btn btn-outline-light" for="mapView">Map</label>

          <input type="radio" class="btn-check" name="viewMode" id="tableView" autocomplete="off" :checked="viewMode === 'table'" @change="setViewMode('table')">
          <label class="btn btn-outline-light" for="tableView">Tabel</label>
        </div>

        <!-- User Login/Logout -->
        <span v-if="isLoggedIn" class="navbar-text">
          <div class="btn-group">
            <button type="button" class="btn btn-outline-light dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
              {{ username }}
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><button class="dropdown-item" @click="logout">Uitloggen</button></li>
              <li><button class="dropdown-item" @click="navigateToChangePassword">Wijzig wachtwoord</button></li>
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
    const viewMode = computed(() => vespaStore.viewMode);

    const setViewMode = (mode) => {
            vespaStore.setViewMode(mode);
    };
    const logout = async () => {
      await vespaStore.logout();
      router.push('/login');
    };
    const navigateToChangePassword = () => {
      router.push({ name: 'ChangePassword' });
    };
    return { isLoggedIn, username, logout, navigateToChangePassword, setViewMode, viewMode };
  },
};
</script>