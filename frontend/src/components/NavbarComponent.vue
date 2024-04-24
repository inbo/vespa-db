<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-success">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">VespaDB</a>
      <div class="d-flex align-items-center">
        <!-- View Mode Toggle -->
        <div class="btn-group me-2" role="group">
          <router-link to="/map" class="btn btn-outline-light" active-class="active" aria-current="page">Map</router-link>
          <router-link to="/table" class="btn btn-outline-light" active-class="active">Tabel</router-link>
        </div>

        <!-- Export Toggle -->
        <div class="btn-group me-2">
          <button type="button" class="btn btn-outline-light dropdown-toggle" data-bs-toggle="dropdown"
            aria-expanded="false">
            Export
          </button>
          <ul class="dropdown-menu">
            <li><button class="dropdown-item" @click="exportData('csv')">CSV</button></li>
            <li><button class="dropdown-item" @click="exportData('json')">JSON</button></li>
          </ul>
        </div>

        <!-- User Login/Logout -->
        <span v-if="isLoggedIn" class="navbar-text">
          <div class="btn-group">
            <button type="button" class="btn btn-outline-light dropdown-toggle" data-bs-toggle="dropdown"
              aria-expanded="false">
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
import { Dropdown } from 'bootstrap';
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
      vespaStore.viewMode = mode;
    };
    const logout = async () => {
      await vespaStore.logout();
      router.push('/login');
    };
    const navigateToChangePassword = () => {
      router.push({ name: 'ChangePassword' });
    };
    const exportData = (format) => {
      vespaStore.exportData(format);
    };

    return { isLoggedIn, username, logout, navigateToChangePassword, setViewMode, viewMode, exportData };
  },
  mounted() {
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'))
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
      return new Dropdown(dropdownToggleEl);
    });
  },
};
</script>