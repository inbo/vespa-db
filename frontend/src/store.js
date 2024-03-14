import { createStore } from 'vuex';

export default createStore({
  state() {
    return {
      isLoggedIn: false,
      username: '',
      userId: null,
    };
  },
  mutations: {
    setLoginStatus(state, { isLoggedIn, username, userId }) {
      state.isLoggedIn = isLoggedIn;
      state.username = username;
      state.userId = userId;
    },
  },
  actions: {
    async checkLoginStatus({ commit }) {
      try {
        const response = await fetch('/check_login/', {
          method: 'GET',
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          commit('setLoginStatus', { isLoggedIn: data.isLoggedIn, username: data.username, userId: data.user_id });
        } else {
          commit('setLoginStatus', { isLoggedIn: false, username: '', userId: null });
        }
      } catch (error) {
        console.error('Error checking login status:', error);
        commit('setLoginStatus', { isLoggedIn: false, username: '', userId: null });
      }
    },
  },
});
