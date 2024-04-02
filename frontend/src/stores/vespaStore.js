import ApiService from '@/services/apiService';

import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { defineStore } from 'pinia';

export const useVespaStore = defineStore('vespaStore', {
    state: () => ({
        isLoggedIn: false,
        userId: null,
        loading: false,
        error: null,
        municipalities: [],
        selectedMunicipalities: [],
        observations: [],
        selectedObservation: null,
        markers: [],
        user: {},
        authInterval: null,
        isEditing: false,
        map: null,
        filters: {
            municipalities: [],
            years: [],
            anbAreasActief: false,
            nestType: null,
            nestStatus: null,
        },
    }),

    actions: {
        async getObservations(filterQuery = '') {
            try {
                const response = await ApiService.get(`/observations${filterQuery}`);
                if (response.status === 200) {
                    this.observations = response.data;
                    this.updateMarkers();
                } else {
                    throw new Error(`Network response was not ok, status code: ${response.status}`);
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error);
                this.error = error.message || 'Failed to fetch observations';
            }
        },
        async applyFilters(filters) {
            this.filters.municipalities = filters.municipalities;
            this.filters.years = filters.years;
            this.filters.anbAreasActief = filters.anbAreasActief;
            this.filters.nestType = filters.nestType;
            this.filters.nestStatus = filters.nestStatus;

            let filterQuery = '?';

            if (this.filters.municipalities.length > 0) {
                filterQuery += `municipality_id=${this.filters.municipalities.join(',')}&`;
            }

            if (this.filters.years.length > 0) {
                filterQuery += `year_range=${this.filters.years.join(',')}&`;
            }

            if (this.filters.anbAreasActief !== null && typeof this.filters.anbAreasActief !== 'undefined') {
                filterQuery += `anb=${this.filters.anbAreasActief}&`;
            }

            if (this.filters.nestType) {
                filterQuery += `nest_type=${this.filters.nestType}&`;
            }
            if (this.filters.nestStatus) {
                filterQuery += `nest_status=${this.filters.nestStatus}&`;
            }

            if (filterQuery === '?') {
                filterQuery = '';
            } else {
                filterQuery = filterQuery.endsWith('&') ? filterQuery.slice(0, -1) : filterQuery;
            }


            await this.getObservations(filterQuery);
        },
        initializeMapAndMarkers() {
            if (!this.map && document.getElementById('mapid')) {
                this.map = L.map('mapid').setView([51.0, 4.5], 9);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: 'Map data © OpenStreetMap contributors',
                    maxZoom: 18,
                }).addTo(this.map);
                this.updateMarkers();
            }
        },
        async updateMarkers() {
            if (this.map) {
                this.markers.forEach(marker => this.map.removeLayer(marker));
                this.markers = [];

                if (!this.observations.length) {
                    return;
                }

                this.observations.forEach((observation, index) => {
                    const locationRegex = /POINT \(([^ ]+) ([^ ]+)\)/;
                    const match = observation.location.match(locationRegex);
                    if (match) {
                        const [, longitude, latitude] = match;
                        const marker = L.marker([parseFloat(latitude), parseFloat(longitude)], {
                            icon: L.divIcon({
                                className: 'custom-div-icon',
                                html: "<i class='fa fa-bug' style='color: black; font-size: 24px;'></i>",
                                iconSize: [30, 42],
                                iconAnchor: [15, 42]
                            })
                        }).addTo(this.map)
                            .on('click', () => this.selectObservation(observation));
                        this.markers.push(marker);
                    } else {
                        console.log(`Geen geldige locatie gevonden voor observatie #${index}.`);
                    }
                });
            }
        },
        async updateObservation() {
            try {
                const response = await ApiService.patch(`/observations/${this.selectedObservation.id}/`, this.selectedObservation);
                if (response.status !== 200) {
                    throw new Error('Network response was not ok');
                }
                const data = response.json();
                this.isEditing = false;
            } catch (error) {
                console.error('Error when updating the observation:', error);
            }
        },
        async fetchMunicipalities() {
            try {
                const response = await ApiService.get('/municipalities/');
                if (response.status === 200) {
                    this.municipalities = response.data;
                } else {
                    console.error('Failed to fetch municipalities: Status Code', response.status);
                }
            } catch (error) {
                console.error('Error fetching municipalities:', error);
            }
        },
        async login({ username, password }) {
            this.loading = true;
            await ApiService
                .post("/app_auth/login/", {
                    username: username,
                    password: password
                })
                .then(() => {
                    this.isLoggedIn = true;
                    this.authCheck();
                })
                .catch((error) => {
                    if (error.response && error.response.data) {
                        this.error = error.response.data.error;
                    } else {
                        this.error = "An unexpected error occurred";
                    }
                    this.isLoggedIn = false;
                    this.user = {};
                    this.loading = false;
                });
        },
        async authCheck() {
            this.loading = true;
            await ApiService
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
            await ApiService
                .post("/app_auth/logout/")
                .then(() => {
                    this.isLoggedIn = false;
                    this.user = {};
                    this.loading = false;
                    this.router.push({ name: 'map' });
                })
                .catch((error) => {
                    this.loading = false;
                });
        },
        async changePassword(oldPassword, newPassword, confirmPassword) {
            this.loading = true;
            if (!oldPassword || !newPassword) {
                this.error = "Vul aub alle velden in.";
                this.loading = false;
                return false;
            }
            if (newPassword !== confirmPassword) {
                this.error = "De wachtwoorden komen niet overeen.";
                this.loading = false;
                return false;
            }
            try {
                await ApiService.post("/app_auth/change-password/", {
                    old_password: oldPassword,
                    new_password: newPassword,
                });
                this.loading = false;
                this.error = null;
                return true;
            } catch (error) {
                this.loading = false;
                if (error.response && error.response.data) {
                    const backendMessages = error.response.data;
                    this.error = backendMessages.detail || "Een onverwachte fout is opgetreden.";
                } else {
                    this.error = error.message || "Een onverwachte fout is opgetreden.";
                }
                return false;
            }
        },
    },
});
