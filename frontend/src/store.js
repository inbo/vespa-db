import { createStore } from 'vuex';

export default createStore({
  state() {
    return {
        isLoggedIn: false,
        username: '',
        userId: null,
        loading: false,
        error: null,
    };
  },
  mutations: {
    setLoginStatus(state, { isLoggedIn, username, userId }) {
      state.isLoggedIn = isLoggedIn;
      state.username = username;
      state.userId = userId;
    },
    setLoading(state, loading) {
        state.loading = loading;
    },
    setError(state, error) {
        state.error = error;
    },
  },
  actions: {
    async checkLoginStatus({ commit }) {
      commit('setLoading', true);
      commit('setError', null); // Reset error state
      try {
        const response = await fetch('/check_login/', {
          method: 'GET',
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          commit('setLoginStatus', { isLoggedIn: data.isLoggedIn, username: data.username, userId: data.user_id });
        } else {
          throw new Error('Failed to fetch login status');
        }
      } catch (error) {
        console.error('Error checking login status:', error);
        commit('setError', error.message || 'Failed to check login status');
        commit('setLoginStatus', { isLoggedIn: false, username: '', userId: null });
      } finally {
        commit('setLoading', false);
      }
    },
  },
});