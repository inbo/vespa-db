<template>
  <div id="ChangePasswordMap" class="d-flex flex-column vh-100">
    <navbar-component></navbar-component>
    <div class="container h-100">
      <div class="row h-100 align-items-center justify-content-center">
        <div class="col-md-8 col-lg-5">
          <div class="card shadow">
            <div class="card-body">
              <h2 class="card-title text-center">Wijzig Wachtwoord</h2>
              <div class="mb-3">
                <label for="oldPassword" class="form-label">Huidig Wachtwoord</label>
                <input type="password" id="oldPassword" class="form-control" v-model="oldPassword"
                  @keyup.enter="changePassword" placeholder="Huidig wachtwoord">
              </div>
              <div class="mb-3">
                <label for="newPassword" class="form-label">Nieuw Wachtwoord</label>
                <input type="password" id="newPassword" class="form-control" v-model="newPassword"
                  @keyup.enter="changePassword" placeholder="Nieuw wachtwoord">
              </div>
              <div class="mb-3">
                <label for="confirmNewPassword" class="form-label">Bevestig Nieuw Wachtwoord</label>
                <input type="password" id="confirmNewPassword" class="form-control" v-model="confirmNewPassword"
                  @keyup.enter="changePassword" placeholder="Bevestig nieuw wachtwoord">
              </div>
              <button @click="changePassword" class="btn btn-success w-100">Wijzig Wachtwoord</button>
              <p v-if="formattedError" class="mt-3 text-danger">{{ formattedError }}</p>
              <p v-if="successMessage" class="mt-3 text-success">{{ successMessage }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import NavbarComponent from '@/components/NavbarComponent.vue';
import { useVespaStore } from '@/stores/vespaStore';
import { computed, ref } from 'vue';

export default {
  components: {
    NavbarComponent,
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

    const formattedError = computed(() => {
      if (!error.value) return null;
      if (error.value.includes("Invalid username or password")) {
        return "Ongeldige gebruikersnaam of wachtwoord.";
      }
      if (error.value.includes("Vul aub alle velden in")) {
        return "Vul aub alle velden in.";
      }
      if (error.value.includes("De wachtwoorden komen niet overeen")) {
        return "De wachtwoorden komen niet overeen.";
      }
      return error.value;
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
      confirmNewPassword,
      formattedError,
      changePassword,
    };
  },
};
</script>
