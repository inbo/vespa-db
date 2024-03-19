<template>
    <nav id="navbar">
      <a href="/">VespaWatch Dashboard</a>
      <div class="nav-right">
        <span v-if="isLoggedIn">
          Hallo, {{ username }}!
          <a href="javascript:void(0);" @click="logout" class="button-style">Uitloggen</a>
        </span>
        <a v-else href="/login" class="button-style">Inloggen</a>
      </div>
    </nav>
  </template>
  
  <script>
  import { mapActions, mapState } from 'vuex';
  
  export default {
    computed: {
      ...mapState(['isLoggedIn', 'username']),
    },
    methods: {
      ...mapActions(['fetchUserStatus', 'logoutAction']),
  
      logout() {
      this.logoutAction().then(() => {
        localStorage.removeItem('access_token');
        this.$router.push('/map');
      });
    },
    },
    created() {
      console.log('API URL:', process.env.VUE_APP_API_URL);
      this.fetchUserStatus();
    },
    mounted() {
      if (this.isLoggedIn) {
        this.$router.push('/map'); 
      }
    }, 
  };
  </script>
  