import axios from 'axios';
import { createStore } from 'vuex';

export default createStore({
    state() {
        return {
            isLoggedIn: false,
            username: '',
            userId: null,
            loading: false,
            error: null,
            accessToken: null,
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
        setAccessToken(state, accessToken) {
            state.accessToken = accessToken;
        },
    },
    actions: {
        async fetchUserStatus({ commit }) {
            commit('setLoading', true);
            commit('setError', null);
            try {
                const accessToken = localStorage.getItem('access_token');
                if (!accessToken) {
                    throw new Error('No access token found');
                }
                const response = await axios.get(`${process.env.VUE_APP_API_URL}/user_status/`, {
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                    },
                });
                commit('setLoginStatus', { isLoggedIn: true, username: response.data.username, userId: response.data.user_id });
            } catch (error) {
                console.error('Error fetching user status:', error);
                commit('setError', error.message || 'Failed to fetch user status');
                commit('setLoginStatus', { isLoggedIn: false, username: '', userId: null });
            } finally {
                commit('setLoading', false);
            }
        },
        async loginAction({ commit }, { username, password }) {
            try {
                const response = await axios.post(`${process.env.VUE_APP_API_URL}/token/`, {
                    username,
                    password,
                });
                const accessToken = response.data.access;
                commit('setLoginStatus', { isLoggedIn: true, username: username, userId: response.data.user_id });
                commit('setAccessToken', accessToken);
                localStorage.setItem('access_token', accessToken);
            } catch (error) {
                console.error('Error during login:', error);
                throw error;
            }
        },
        logoutAction({ commit }) {
            localStorage.removeItem('access_token');
            commit('setLoginStatus', { isLoggedIn: false, username: '', userId: null });
            commit('setAccessToken', null);
        },
    },
});