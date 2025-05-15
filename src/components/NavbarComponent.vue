<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container-fluid">
      <a class="navbar-brand d-flex align-items-center" href="https://vespawatch.be">
        <img class="me-3" src="../assets/logo.png" alt="Vespa-Watch">
        Vespa-Watch
      </a>
      <div class="d-flex align-items-center">
        <!-- Export Toggle (Hidden on Medium Devices and below) -->
        <div class="btn-group me-2 d-none d-md-inline-flex">
          <button type="button" class="btn btn-outline-dark dropdown-toggle" data-bs-toggle="dropdown"
            aria-expanded="false">
            Export
          </button>
          <ul class="dropdown-menu">
              <li>
                  <button 
                      class="dropdown-item" 
                      @click="exportData('csv')"
                      :disabled="isExporting"
                  >
                      CSV
                  </button>
              </li>
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
  
  <div class="notification-banner">
    <div class="container-fluid">
      <p class="notification-text">
        Dit platform is momenteel nog niet publiek opengesteld. Het is wel reeds toegankelijk voor bestrijders en instanties betrokken in de bestrijding en beheer van Aziatische hoornaars. Indien je een account wil maken: contacteer <a href="mailto:vespawatch@inbo.be" class="notification-link">vespawatch@inbo.be</a>. De publieke lancering vindt plaats nadat alle data van vorige jaren is opgeladen.
      </p>
    </div>
  </div>
  
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
    const isExporting = computed(() => vespaStore.isExporting);

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
      try {
          if (vespaStore.isExporting) return;
          
          await vespaStore.exportData(format);
      } catch (error) {
          modalTitle.value = 'Error';
          modalMessage.value = 'Er is een fout opgetreden tijdens het exporteren.';
          isModalVisible.value = true;
      }
    };

    return { 
      isLoggedIn, 
      loadingAuth, 
      username, 
      logout, 
      navigateToChangePassword, 
      exportData, 
      fileInput, 
      isModalVisible, 
      modalTitle, 
      modalMessage, 
      isExporting
    };
  },
  mounted() {
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
      return new Dropdown(dropdownToggleEl);
    });
  },
};
</script>

<style>
.notification-banner {
  background-color: #fff3cd;
  border-bottom: 1px solid #ffeeba;
  padding: 0.75rem 0;
  position: relative;
  z-index: 1050;
}

.notification-text {
  margin: 0;
  font-size: 0.9rem;
  color: #856404;
  text-align: center;
  line-height: 1.5;
}

.notification-link {
  color: #856404;
  font-weight: bold;
  text-decoration: underline;
}

.notification-link:hover {
  color: #533f03;
}
</style>
