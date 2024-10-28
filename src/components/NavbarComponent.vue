<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container-fluid">
      <a class="navbar-brand d-flex align-items-center" href="/">
        <img class="me-3" src="../assets/logo.png" alt="Vespa-Watch">
        Vespa-Watch
      </a>
      <div class="d-flex align-items-center">
        <!-- View Mode Toggle -->
        <div class="btn-group me-2" role="group">
          <router-link to="/map" class="btn btn-outline-dark" active-class="active"
            aria-current="page">Map</router-link>
          <router-link to="/table" class="btn btn-outline-dark" active-class="active">Tabel</router-link>
        </div>

        <!-- Export Toggle (Hidden on Medium Devices and below) -->
        <div class="btn-group me-2 d-md-inline-flex">
          <button type="button" class="btn btn-outline-dark dropdown-toggle" data-bs-toggle="dropdown"
            aria-expanded="false">
            Export
          </button>
          <ul class="dropdown-menu">
            <li><button class="dropdown-item" @click="exportData('csv')">CSV</button></li>
          </ul>
        </div>

        <!-- User Login/Logout -->
        <span v-if="isLoggedIn && !loadingAuth" class="navbar-text">
          <div class="btn-group">
            <button type="button" class="btn btn-outline-dark dropdown-toggle" data-bs-toggle="dropdown"
              aria-expanded="false">
              {{ username }}
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><button class="dropdown-item" @click="logout">Uitloggen</button></li>
              <li><button class="dropdown-item" @click="navigateToChangePassword">Wijzig wachtwoord</button></li>
            </ul>
          </div>
        </span>
        <router-link v-if="!isLoggedIn && !loadingAuth" to="/login" class="btn btn-outline-dark"
          active-class="active">Inloggen</router-link>
        <span v-if="loadingAuth" class="navbar-text">Loading...</span> <!-- Placeholder while loading -->
      </div>
    </div>
  </nav>
  <ModalMessage :title="modalTitle" :message="modalMessage" :isVisible="isModalVisible"
    @close="isModalVisible = false" />
</template>

<script>
import ModalMessage from '@/components/ModalMessage.vue';
import { useVespaStore } from '@/stores/vespaStore';
import { Dropdown } from 'bootstrap';
import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

export default {
  components: {
    ModalMessage
  },
  setup() {
    const router = useRouter();
    const vespaStore = useVespaStore();
    const isLoggedIn = computed(() => vespaStore.isLoggedIn);
    const loadingAuth = computed(() => vespaStore.loadingAuth);
    const username = computed(() => vespaStore.user.username);
    const fileInput = ref(null);
    const isModalVisible = ref(false);
    const modalTitle = ref('');
    const modalMessage = ref('');

    watch(() => vespaStore.error, (newError) => {
      if (newError) {
        modalTitle.value = 'Error';
        modalMessage.value = newError;
        isModalVisible.value = true;
      }
    });

    watch(() => vespaStore.successMessage, (newMessage) => {
      if (newMessage) {
        modalTitle.value = 'Success';
        modalMessage.value = newMessage;
        isModalVisible.value = true;
      }
    });

    const logout = async () => {
      await vespaStore.logout();
      router.push('/login');
    };

    const navigateToChangePassword = () => {
      router.push({ name: 'ChangePassword' });
    };

    const exportData = async (format) => {
      await vespaStore.exportData(format);
    };

    return { isLoggedIn, loadingAuth, username, logout, navigateToChangePassword, exportData, fileInput, isModalVisible, modalTitle, modalMessage };
  },
  mounted() {
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
      return new Dropdown(dropdownToggleEl);
    });
  },
};
</script>
