<template>
    <div id="loginApp">
        <navbar-component></navbar-component>
        <div class="modal-content" style="margin-top: 100px;">
            <h2>Login</h2>
            <input type="text" v-model="username" placeholder="Gebruikersnaam" />
            <input type="password" v-model="password" placeholder="Wachtwoord" />
            <button @click="login">Login</button>
            <p v-if="error" class="error">{{ error }}</p>
        </div>
        <footer-component></footer-component>
    </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed, ref } from 'vue';
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
