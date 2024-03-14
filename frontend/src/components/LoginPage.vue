<template>
    <div id="loginApp">
        <navbar-component></navbar-component>
        <div class="modal-content" style="margin-top: 100px;">
            <h2>Login</h2>
            <input type="text" v-model="username" placeholder="Gebruikersnaam" />
            <input type="password" v-model="password" placeholder="Wachtwoord" />
            <button @click="login">Login</button>
        </div>
        <footer-component></footer-component>
    </div>
</template>

<script>
import NavbarComponent from './NavbarComponent.vue';
import FooterComponent from './FooterComponent.vue';

export default {
    components: {
        NavbarComponent,
        FooterComponent
    },
    data() {
        return {
            username: '',
            password: ''
        };
    },
    methods: {
        login() {
            // Login logica
        }
    }
}
</script>

<style scoped>
/* Je CSS hier */
</style>M