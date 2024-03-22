import { default as ApiService, default as instance } from '@/services/apiService';
import { defineStore } from "pinia";
import { createStore } from 'vuex';

export default createStore({
    state() {
        return {
            isLoggedIn: false,
            username: '',
            userId: null,
            loading: false,
            error: null,
            selectedMunicipalities: [],
            observations: [],
        };
    },
    mutations: {
        setLoginStatus(state, { isLoggedIn, username, userId }) {
            console.log("setting login status", isLoggedIn, username, userId)
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
        setSelectedMunicipalities(state, municipalities) {
            state.selectedMunicipalities = municipalities;
        },
        setObservations(state, observations) {  // Optioneel
            state.observations = observations;
        },
    },
    actions: {
        async fetchUserStatus({ commit }) {
            commit('setLoading', true);
            commit('setError', null);
            try {
                let headers = {};
                const response = await ApiService.get(`/user_status/`, { headers });

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
            this.loading = true;
            await instance
                .post("/app_auth/login/", {
                    username: username,
                    password: password
                })
                .then(() => {
                    this.authCheck();
                    commit('setLoginStatus', { isLoggedIn: true, username: username, userId: response.data.user_id });
                })
                .catch((error) => {
                    console.error(error);
                    if (error.response && error.response.data) {
                        this.error = error.response.data.error;
                    } else {
                        // Handle cases where error.response or error.response.data is undefined
                        this.error = "An unexpected error occurred";
                    }
                    this.loggedOut = true;
                    this.user = {};
                    this.loading = false;
                });
        },
        async authCheck() {
            this.loading = true;
            await instance
                .get("/app_auth/auth-check")
                .then((response) => {
                    const data = response.data;
                    if (data.isAuthenticated && data.user) {
                        this.user = data.user;
                        this.error = "";
                        this.loggedOut = false;
                        this.loading = false;

                        if (!this.authInterval) {
                            this.authInterval = setInterval(() => {
                                this.authCheck();
                            }, 1000 * 60 * 21); // 21 minutes in miliseconds
                        }
                    } else {
                        this.error = "";
                        this.loggedOut = true;
                        this.loading = false;
                        this.authInterval = null;
                    }
                })
                .catch((error) => {
                    console.error(error.response.data);
                    this.error = error;
                    this.loggedOut = true;
                    this.loading = false;
                });
        },
        async getObservations({ commit }, filterQuery = '') {
            console.log(`Ophalen van observaties met filterQuery: '${filterQuery}'`);
            try {
                const response = await ApiService.get(`/observations${filterQuery}`); // Verwijder de slash voor filterQuery
                if (response.status === 200) {
                    console.log("Observaties succesvol opgehaald: ", response.data);
                    commit('setObservations', response.data);
                } else {
                    throw new Error(`Network response was not ok, status code: ${response.status}`);
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error);
            }
        },
        updateSelectedMunicipalities({ commit, dispatch }, municipalities) {
            commit('setSelectedMunicipalities', municipalities);
            if (municipalities.length === 0) {
                dispatch('getObservations');
            }
        },
        async logoutAction({ commit }) {
            this.loading = true;
            await instance
                .get("/api-auth/logout/")
                .then(() => {
                    this.authCheck();
                    commit('setLoginStatus', { isLoggedIn: false, username: '', userId: null });
                })
                .catch((error) => {
                    console.error(error.response.data);
                    this.error = error.response.data.error;
                    this.loading = false;
                });
        },
    },
});
export const useAppAuthStore = defineStore("app_auth", {
    state: () => ({
        loggedOut: true,
        error: "",
        user: {},
        loading: false,
        authInterval: null,
    }),
    getters: {},
    actions: {
        async loginAction({ commit }, { username, password }) {
            this.loading = true;
            await instance
                .post("/app_auth/login/", {
                    username: username,
                    password: password
                })
                .then(() => {
                    this.authCheck();
                    commit('setLoginStatus', { isLoggedIn: true, username: username, userId: response.data.user_id });
                })
                .catch((error) => {
                    console.error(error);
                    if (error.response && error.response.data) {
                        this.error = error.response.data.error;
                    } else {
                        // Handle cases where error.response or error.response.data is undefined
                        this.error = "An unexpected error occurred";
                    }
                    this.loggedOut = true;
                    this.user = {};
                    this.loading = false;
                });
        },
        async authCheck() {
            this.loading = true;
            await api
                .get("/app_auth/auth-check")
                .then((response) => {
                    const data = response.data;
                    if (data.isAuthenticated && data.user) {
                        this.user = data.user;
                        this.error = "";
                        this.loggedOut = false;
                        this.loading = false;

                        if (!this.authInterval) {
                            this.authInterval = setInterval(() => {
                                this.authCheck();
                            }, 1000 * 60 * 21); // 21 minutes in miliseconds
                        }
                    } else {
                        this.error = "";
                        this.loggedOut = true;
                        this.loading = false;
                        this.authInterval = null;
                    }
                })
                .catch((error) => {
                    console.error(error.response.data);
                    this.error = error;
                    this.loggedOut = true;
                    this.loading = false;
                });
        },
        async logout() {
            this.loading = true;
            await api
                .get("/api-auth/logout/")
                .then(() => {
                    this.authCheck();
                })
                .catch((error) => {
                    console.error(error.response.data);
                    this.error = error.response.data.error;
                    this.loading = false;
                });
        },
    },
});