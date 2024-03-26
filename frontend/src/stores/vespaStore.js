import ApiService from '@/services/apiService';

import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { defineStore } from 'pinia';

export const useVespaStore = defineStore('vespaStore', {
    state: () => ({
        isLoggedIn: false,
        username: '',
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

            let filterQuery = '?';

            if (this.filters.municipalities.length > 0) {
                filterQuery += `municipality_id=${this.filters.municipalities.join(',')}&`;
            }

            if (this.filters.years.length > 0) {
                filterQuery += `year_range=${this.filters.years.join(',')}&`;
            }

            if (this.filters.anbAreasActief) {
                // Include ANB areas filter
            }

            if (filterQuery === '?') {
                filterQuery = '';
            } else {
                // Remove the trailing '&' if present
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
