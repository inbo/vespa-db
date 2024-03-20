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
        this.logoutAction();
        this.$router.push('/login');
      },
    },
    created() {
      this.fetchUserStatus();
    },
    mounted() {
      if (this.isLoggedIn) {
        this.$router.push('/map'); 
      }
    }, 
  };
  </script>
  