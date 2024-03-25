// Import the necessary utilities from Pinia and your ApiService
import { default as ApiService, default as instance } from '@/services/apiService';
import { defineStore } from 'pinia';

// Define a single store combining both previous stores
export const useVespaStore = defineStore('vespaStore', {
    state: () => ({
        // States from both stores
        isLoggedIn: false,
        username: '',
        userId: null,
        loading: false,
        error: null,
        selectedMunicipalities: [],
        observations: [],
        user: {},
        authInterval: null,
    }),

    actions: {
        // Actions from the Vuex store
        async getObservations(filterQuery = '') {
            console.log(`Fetching observations with filterQuery: '${filterQuery}'`);
            try {
                const response = await ApiService.get(`/observations${filterQuery}`);
                if (response.status === 200) {
                    console.log("Observations successfully fetched: ", response.data);
                    this.observations = response.data;
                } else {
                    throw new Error(`Network response was not ok, status code: ${response.status}`);
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error);
                this.error = error.message || 'Failed to fetch observations';
            }
        },
        updateSelectedMunicipalities(municipalities) {
            this.selectedMunicipalities = municipalities;
            if (municipalities.length === 0) {
                this.getObservations();
            }
        },

        // Actions from the Pinia auth store
        async loginAction({ username, password }) {
            this.loading = true;
            await instance
                .post("/app_auth/login/", {
                    username: username,
                    password: password
                })
                .then(() => {
                    this.authCheck();
                })
                .catch((error) => {
                    console.error(error);
                    if (error.response && error.response.data) {
                        this.error = error.response.data.error;
                    } else {
                        // Handle cases where error.response or error.response.data is undefined
                        this.error = "An unexpected error occurred";
                    }
                    this.isLoggedIn = false;
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
                        console.log(data.user)
                        this.user = data.user;
                        this.error = "";
                        this.isLoggedIn = true;
                        this.loading = false;

                        if (!this.authInterval) {
                            this.authInterval = setInterval(() => {
                                this.authCheck();
                            }, 1000 * 60 * 21); // 21 minutes in milliseconds
                        }
                    } else {
                        this.error = "";
                        this.isLoggedIn = false;
                        this.loading = false;
                        this.authInterval = null;
                    }
                })
                .catch((error) => {
                    console.error(error.response.data);
                    this.error = error;
                    this.isLoggedIn = false;
                    this.loading = false;
                });
        },
        async logout() {
            this.loading = true;
            await instance
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
