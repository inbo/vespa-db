<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-success">
    <div class="container-fluid">
      <router-link to="/" class="navbar-brand" active-class="active">VespaDB</router-link>
      <div class="d-flex align-items-center">
        <!-- View Mode Toggle -->
        <div class="btn-group me-2" role="group">
          <router-link to="/map" class="btn btn-outline-light" active-class="active"
            aria-current="page">Map</router-link>
          <router-link to="/table" class="btn btn-outline-light" active-class="active">Tabel</router-link>
        </div>

        <!-- Export Toggle (Hidden on Small Devices) -->
        <div class="btn-group me-2 d-none d-lg-inline-flex">
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
        <router-link to="/login" class="btn btn-outline-light" active-class="active">Inloggen</router-link>
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

    return { isLoggedIn, username, logout, navigateToChangePassword, exportData, fileInput, isModalVisible, modalTitle, modalMessage };
  },
  mounted() {
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
      return new Dropdown(dropdownToggleEl);
    });
  },
};
</script>
