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
                                    placeholder="Gebruikersnaam">
                            </div>
                            <div class="form-group mb-3">
                                <label for="password" class="form-label">Wachtwoord</label>
                                <input type="password" id="password" class="form-control" v-model="password"
                                    placeholder="Wachtwoord">
                            </div>
                            <button @click="login" class="btn btn-success w-100">Login</button>
                            <p v-if="error" class="mt-3 text-danger">{{ error }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import NavbarComponent from './NavbarComponent.vue';

export default {
    components: {
        NavbarComponent,
    },
    setup() {
        const router = useRouter();
        const vespaStore = useVespaStore();
        const username = ref('');
        const password = ref('');
        const error = computed(() => {
            return Array.isArray(vespaStore.error) ? vespaStore.error.join(', ') : vespaStore.error;
        });

        const login = async () => {
            await vespaStore.login({ username: username.value, password: password.value });
            if (vespaStore.isLoggedIn) {
                router.push('/map');
            }
        };

        return {
            username,
            password,
            login,
            error
        };
    }
};
</script>

  