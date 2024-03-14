<template>
    <nav id="navbar">
        <a href="/">VespaWatch Dashboard</a>
        <div class="nav-right">
            <span v-if="isLoggedIn">
                Hallo, {{ username }}!
                <button @click="logout">Uitloggen</button>
            </span>
            <a v-else href="/login" class="button-style">Inloggen</a>
        </div>
    </nav>
</template>

<script>
export default {
    data() {
        return {
            isLoggedIn: false,
            userId: null,
            username: '',
        };
    },
    created() {
        this.checkLoginStatus();
    },
    methods: {
        setLoginStatus(isLoggedIn, username, userId) {
            this.isLoggedIn = isLoggedIn;
            this.username = username;
            this.userId = userId;
        },
        checkLoginStatus() {
            try {
                const response = await fetch('/check_login/', {
                    method: 'GET',
                    credentials: 'include'
                });
                if (response.ok) {
                    const data = await response.json();
                    this.setLoginStatus(data.isLoggedIn, data.username, data.user_id);
                    console.log("Login status from store: ", this.state.isLoggedIn);
                } else {
                    this.setLoginStatus(false, '', null);
                }
            } catch (error) {
                console.error('Error checking login status:', error);
                this.setLoginStatus(false, '', null);
            }
        },
        logout() {
            //TODO: ADD LOGOUT IMPLEMENTATIOn
            this.isLoggedIn = false;
            this.username = '';
            this.userId = '';
            this.$router.push('/login');
        },
    },
};
</script>

<style scoped>
#navbar {
    display: flex;
    justify-content: space-between;
    padding: 1rem;
    background-color: #4C7742;
    color: white;
}

.nav-right {
    display: flex;
    align-items: center;
}

.button-style {
    margin-left: 1rem;
    background-color: #36532d;
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 5px;
}

.button-style:hover {
    background-color: #2e4424;
}
</style>