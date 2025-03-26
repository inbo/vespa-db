<template>
    <div id="loginApp" class="d-flex flex-column vh-100">
        <navbar-component></navbar-component>
        <div class="container h-100">
            <div class="row h-100 align-items-center justify-content-center">
                <div class="col-md-8 col-lg-5">
                    <div class="card shadow">
                        <div class="card-body">
                            <h2 class="card-title text-center">Login</h2>
                            <div class="form-group mb-3">
                                <label for="username" class="form-label">Gebruikersnaam</label>
                                <input type="text" id="username" class="form-control" v-model="username"
                                    @keyup.enter="showTermsBeforeLogin" placeholder="Gebruikersnaam">
                            </div>
                            <div class="form-group mb-3">
                                <label for="password" class="form-label">Wachtwoord</label>
                                <input type="password" id="password" class="form-control" v-model="password"
                                    @keyup.enter="showTermsBeforeLogin" placeholder="Wachtwoord">
                            </div>
                            <button @click="showTermsBeforeLogin" class="btn btn-success w-100" :disabled="loading">Login</button>
                            <p v-if="formattedError" class="mt-3 text-danger">{{ formattedError }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>        
        <terms-modal 
            @accept="performLogin" 
            @cancel="cancelLogin"
            ref="termsModal">
        </terms-modal>
    </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import NavbarComponent from './NavbarComponent.vue';
import TermsModal from './TermsModal.vue';
import { Modal } from 'bootstrap';

export default {
    components: {
        NavbarComponent,
        TermsModal
    },
    setup() {
        const router = useRouter();
        const vespaStore = useVespaStore();
        const username = ref('');
        const password = ref('');
        const termsModal = ref(null);
        const bootstrapModal = ref(null);
        const loading = ref(false);

        onMounted(() => {
            bootstrapModal.value = new Modal(document.getElementById('termsModal'), {
                backdrop: 'static',
                keyboard: false
            });
        });

        const loginError = computed(() => {
            return Array.isArray(vespaStore.loginError) ? vespaStore.loginError.join(', ') : vespaStore.loginError;
        });

        const formattedError = computed(() => {
            if (!loginError.value) return null;
            return loginError.value;
        });

        // Show terms modal before attempting login
        const showTermsBeforeLogin = () => {
            if (!username.value || !password.value) {
                vespaStore.loginError = "Vul alstublieft een gebruikersnaam en wachtwoord in.";
                return;
            }
            
            // Clear any previous errors
            vespaStore.loginError = null;
            
            // Show the terms modal
            bootstrapModal.value.show();
        };

        // Perform the actual login after terms acceptance
        const performLogin = async () => {
            loading.value = true;
            
            // Hide the modal
            bootstrapModal.value.hide();
            
            // Attempt to login
            await vespaStore.login({ username: username.value, password: password.value });
            
            if (vespaStore.isLoggedIn) {
                router.push('/map');
            }
            
            loading.value = false;
        };

        const cancelLogin = () => {
            bootstrapModal.value.hide();
        };

        return {
            username,
            password,
            loading,
            showTermsBeforeLogin,
            performLogin,
            cancelLogin,
            formattedError,
            termsModal
        };
    }
};
</script>

<style scoped>
.error-container {
    max-width: 100%;
    word-wrap: break-word;
}
</style>