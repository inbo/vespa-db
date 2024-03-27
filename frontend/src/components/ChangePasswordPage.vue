<template>
  <div id="ChangePasswordMap">
    <navbar-component></navbar-component>
      <div class="modal-content" style="margin-top: 100px;">
        <h2>Change Password</h2>
        <input type="password" v-model="oldPassword" placeholder="Huidig wachtwoord" />
        <input type="password" v-model="newPassword" placeholder="Nieuw wachtwoord" />
        <input type="password" v-model="confirmNewPassword" placeholder="Bevestig nieuw wachtwoord" />
        <button @click="changePassword">Wijzig Password</button>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="successMessage" class="success">{{ successMessage }}</p>
      </div>
    <footer-component></footer-component>
  </div>
</template>

  
<script>
import FooterComponent from '@/components/FooterComponent.vue';
import NavbarComponent from '@/components/NavbarComponent.vue';
import { useVespaStore } from '@/stores/vespaStore';
import { computed, ref } from 'vue';
    
export default {
  components: {
    NavbarComponent,
    FooterComponent,
  },
  setup() {
    const vespaStore = useVespaStore();
    const oldPassword = ref('');
    const newPassword = ref('');
    const confirmNewPassword = ref('');
    const successMessage = ref('');
    const error = computed(() => {
        return Array.isArray(vespaStore.error) ? vespaStore.error.join(', ') : vespaStore.error;
    });

    const changePassword = async () => {
      const success = await vespaStore.changePassword(oldPassword.value, newPassword.value, confirmNewPassword.value);
      if (success) {
        successMessage.value = "Wachtwoord succesvol gewijzigd!";
      }
    };

    return {
      successMessage,
      oldPassword,
      newPassword,
      error,
      changePassword,
      confirmNewPassword,
    };
  },
};
</script>