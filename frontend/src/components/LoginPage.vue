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
import { mapActions } from 'vuex';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';

export default {
    components: {
        NavbarComponent,
        FooterComponent
    },
    data() {
        return {
            username: '',
            password: '',
            loginError: null
        };
    },
    methods: {
        ...mapActions(['loginAction']),
        async login() {
            this.loginError = null;
            try {
                await this.loginAction({
                    username: this.username,
                    password: this.password
                });
                this.$router.push('/map');
            } catch (error) {
                this.loginError = "Login mislukt. Controleer uw gebruikersnaam en wachtwoord.";
                console.error('Login failed:', error.message);
            }
        }
    }
}
</script>
