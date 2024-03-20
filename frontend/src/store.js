import ApiService from '@/services/apiService';
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
                let headers = {};

                if (accessToken) {
                    headers.Authorization = `Bearer ${accessToken}`;
                }

                const response = await axios.get(`/user_status/`, { headers });

                if (response.data.is_logged_in) {
                    commit('setLoginStatus', { isLoggedIn: true, username: response.data.username, userId: response.data.user_id });
                }
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
                const response = await ApiService.post('/token/', {
                    username,
                    password,
                });
                const accessToken = response.data.access;
                localStorage.setItem('access_token', accessToken);
                commit('setLoginStatus', { isLoggedIn: true, username: username, userId: response.data.user_id });
                commit('setAccessToken', accessToken);
            } catch (error) {
                console.error('Error during login:', error);
                throw error;
            }
        },

        logoutAction({ commit }) {
            localStorage.removeItem('access_token');
            ApiService.removeHeader();
            commit('setLoginStatus', { isLoggedIn: false, username: '', userId: null });
            commit('setAccessToken', null);
        },

    },
});