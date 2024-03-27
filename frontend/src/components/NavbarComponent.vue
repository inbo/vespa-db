<template>
  <nav id="navbar">
    <a href="/">VespaWatch Dashboard</a>
    <div class="nav-right">
      <span v-if="isLoggedIn">
        Hallo, {{ username }}!
        <a href="javascript:void(0);" @click="logout" class="button-style">Uitloggen</a>
        <a href="javascript:void(0);" @click="navigateToChangePassword" class="button-style">Change Password</a>
      </span>
      <a v-else href="/login" class="button-style">Inloggen</a>
    </div>
  </nav>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed } from 'vue';
import { useRouter } from 'vue-router';

export default {
  setup() {
    const router = useRouter();
    const vespaStore = useVespaStore();
    const isLoggedIn = computed(() => vespaStore.isLoggedIn);
    const username = computed(() => vespaStore.user.username);

    const logout = async () => {
      await vespaStore.logout();
      router.push('/login');
    };
    const navigateToChangePassword = () => {
      router.push({ name: 'ChangePassword' });
    };
    return { isLoggedIn, username, logout, navigateToChangePassword };
  },
};
</script>
