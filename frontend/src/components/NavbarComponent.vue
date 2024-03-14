<template>
    <nav id="navbar">
        <a href="/">VespaWatch Dashboard</a>
        <div class="nav-right">
            <span v-if="isLoggedIn">
                Hallo, {{ username }}!
                <button @click="logoutAction">Uitloggen</button>
            </span>
            <a v-else href="/login" class="button-style">Inloggen</a>
        </div>
    </nav>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
    computed: {
        ...mapState(['isLoggedIn', 'username']),
    },
    methods: {
        ...mapActions(['checkLoginStatus', 'logoutAction']),

        logout() {
            this.logoutAction().then(() => {
                this.$router.push('/login');
            });
        },
    },
    created() {
        this.checkLoginStatus();
    },
};
</script>