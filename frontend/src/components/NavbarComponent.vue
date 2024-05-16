<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-success">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">VespaDB</a>
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

        <!-- Import Button (Hidden on Small Devices) -->
        <div class="btn-group me-2 d-none d-lg-inline-flex">
          <button type="button" class="btn btn-outline-light" @click="triggerFileInput">Import</button>
          <input type="file" ref="fileInput" class="d-none" @change="handleFileUpload" accept=".json,.csv" />
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
  <ModalMessage :title="modalTitle" :message="modalMessage" :isVisible="isModalVisible"
    @close="isModalVisible = false" />
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { Dropdown } from 'bootstrap';
import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import ModalMessage from '@/components/ModalMessage.vue';

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

    const exportData = (format) => {
      vespaStore.exportData(format);
    };

    const handleFileUpload = async (event) => {
      const file = event.target.files[0];
      if (file) {
        if (file.type === 'application/json') {
          const reader = new FileReader();
          reader.onload = async (e) => {
            const jsonContent = e.target.result;
            try {
              const jsonData = JSON.parse(jsonContent);
              await vespaStore.importData(jsonData, true);
            } catch (error) {
              console.error('Error parsing JSON:', error);
              vespaStore.error = 'Invalid JSON file';
            }
          };
          reader.readAsText(file);
        } else {
          const formData = new FormData();
          formData.append('file', file);
          await vespaStore.importData(formData);
        }
      }
    };

    const triggerFileInput = () => {
      fileInput.value.click();
    };

    return { isLoggedIn, username, logout, navigateToChangePassword, exportData, handleFileUpload, triggerFileInput, fileInput, isModalVisible, modalTitle, modalMessage };
  },
  mounted() {
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
      return new Dropdown(dropdownToggleEl);
    });
  },
};
</script>
