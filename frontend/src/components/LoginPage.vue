<template>
    <div id="loginApp">
        <navbar-component></navbar-component>
        <div class="modal-content" style="margin-top: 100px;">
            <h2>Login</h2>
            <input type="text" v-model="username" placeholder="Gebruikersnaam" />
            <input type="password" v-model="password" placeholder="Wachtwoord" />
            <button @click="login">Login</button>
            <p v-if="loginError" class="error">{{ loginError }}</p>
        </div>
        <footer-component></footer-component>
    </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';

export default {
    components: {
        NavbarComponent,
        FooterComponent
    },
    setup() {
        const router = useRouter();
        const vespaStore = useVespaStore();
        const username = ref('');
        const password = ref('');
        const loginError = ref(null);

        const login = async () => {
            try {
                await vespaStore.loginAction({ username: username.value, password: password.value });
                router.push('/map');
            } catch (error) {
                loginError.value = "Failed to login. Please check your username and password.";
            }
        };

        return {
            username,
            password,
            loginError,
            login
        };
    }
};
</script>
