import ApiService from '@/services/apiService';

import L from 'leaflet';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster/dist/leaflet.markercluster';
import 'leaflet/dist/leaflet.css';
import { defineStore } from 'pinia';

export const useVespaStore = defineStore('vespaStore', {
    state: () => ({
        isLoggedIn: false,
        loading: false,
        error: null,
        municipalities: [],
        selectedMunicipalities: [],
        observations: [],
        table_observations: [],
        totalObservations: 0,
        selectedObservation: null,
        nextPage: null,
        previousPage: null,
        loadingObservations: false,
        markerClusterGroup: null,
        authInterval: null,
        isEditing: false,
        map: null,
        viewMode: 'map',
        filters: {
            municipalities: [],
            years: [],
            anbAreasActief: null,
            nestType: null,
            nestStatus: null,
        },
        isDetailsPaneOpen: false,
        user: {},
        userMunicipalities: [],
    }),
    getters: {
        canEditObservation: (state) => (observation) => {
            return state.isLoggedIn && state.userMunicipalities.includes(observation.municipality);
        },
    },
    actions: {
        async getObservations(page = 1, page_size = 25) {
            this.loadingObservations = true;
            const filterQuery = this.createFilterQuery();
            try {
                const response = await ApiService.get(`/observations?${filterQuery}&page=${page}&page_size=${page_size}`);
                if (response.status === 200) {
                    this.table_observations = response.data.results;  // Updating observations instead
                    this.totalObservations = response.data.total;
                    this.nextPage = response.data.next;
                    this.previousPage = response.data.previous;
                } else {
                    throw new Error(`Network response was not ok, status code: ${response.status}`);
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error);
                this.error = error.message || 'Failed to fetch observations';
            } finally {
                this.loadingObservations = false;
            }
        },
        async getObservationsGeoJson() {
            console.log("getObservationsGeoJson")
            this.loading = true;
            const filterQuery = this.createFilterQuery();
            console.log("map bounds:", this.map.getBounds().toBBoxString())
            const bbox = this.map.getBounds().toBBoxString();
            try {
                console.log("api request")
                const response = await ApiService.get(`/observations/dynamic-geojson?${filterQuery}&bbox=${bbox}`);
                console.log("response:", response)
                if (response.status === 200) {
                    console.log("this observations update:" + response.data.features.length)
                    this.observations = response.data.features;
                    console.log("this observations update:" + this.observations.length)

                } else {
                    throw new Error(`Network response was not ok, status code: ${response.status}`);
                }
            } catch (error) {
                console.error('Error fetching observations:', error.message);
                this.error = error.message || 'Failed to fetch observations';
            } finally {
                this.loading = false;
            }
        },
        createFilterQuery() {
            let filterQuery = '';

            if (this.filters.municipalities.length > 0) {
                filterQuery += `municipality_id=${this.filters.municipalities.join(',')}&`;
            }

            if (this.filters.years.length > 0) {
                filterQuery += `year_range=${this.filters.years.join(',')}&`;
            }

            if (this.filters.anbAreasActief !== null && this.filters.anbAreasActief !== undefined) {
                filterQuery += `anb=${this.filters.anbAreasActief}&`;
            }

            if (this.filters.nestType) {
                filterQuery += `nest_type=${this.filters.nestType}&`;
            }

            if (this.filters.nestStatus) {
                filterQuery += `nest_status=${this.filters.nestStatus}&`;
            }

            return filterQuery.endsWith('&') ? filterQuery.slice(0, -1) : filterQuery;
        },
        async applyFilters(filters) {
            this.filters.municipalities = filters.municipalities;
            this.filters.years = filters.years;
            this.filters.anbAreasActief = filters.anbAreasActief;
            this.filters.nestType = filters.nestType;
            this.filters.nestStatus = filters.nestStatus;
        },
        async refresh_data() {
            console.log("viewmode:", this.viewMode)
            if (this.viewMode === 'map') {
                await this.getObservationsGeoJson();
                this.markerClusterGroup.clearLayers();
                this.updateMarkers()
            } else {
                this.getObservations();
            }
        },
        initializeMap() {
            if (!this.map) {
                this.map = L.map('map', {
                    center: [50.8503, 4.3517],
                    zoom: 8,
                    layers: [
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: 'Map data © OpenStreetMap contributors'
                        }),
                        vespaStore.markerClusterGroup = new L.MarkerClusterGroup()
                    ]
                });
            } else {
                this.map._onResize();
            }
        },
        updateMarkers() {
            if (!this.map || !this.markerClusterGroup || !this.observations.length) {
                console.error("No map, marker cluster group, or map observations available");
                return;
            }
            console.log("length:", this.observations.length)
            const geoJsonLayer = L.geoJSON(this.observations, {
                pointToLayer: (feature, latlng) => this.createCircleMarker(feature, latlng)
            });
            this.markerClusterGroup.addLayer(geoJsonLayer);
            this.map.addLayer(this.markerClusterGroup);
        },
        createCircleMarker(feature, latlng) {
            let markerOptions = {
                radius: 5 + (feature.properties.observations_count || 0) * 0.5,
                fillColor: "#FF7800",
                color: "#000",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            };
            return L.circleMarker(latlng, markerOptions).bindPopup(`Observatie ID: ${feature.properties.id}`);
        },
        async reserveObservation(observation) {
            try {
                const reservedObservation = {
                    ...observation,
                    reserved_by: this.user.id
                };
                const response = await ApiService.patch(`/observations/${observation.id}/`, reservedObservation);
                if (response.status === 200) {
                    this.selectedObservation = { ...this.selectedObservation, ...response.data };
                } else {
                    throw new Error('Failed to reserve the observation');
                }
            } catch (error) {
                console.error('Error reserving the observation:', error);
            }
        },
        async cancelReservation(observation) {
            try {
                const updatedObservation = {
                    ...observation,
                    reserved_by: null
                };
                const response = await ApiService.patch(`/observations/${observation.id}/`, updatedObservation);
                if (response.status === 200) {
                    this.selectedObservation = { ...this.selectedObservation, ...response.data };
                } else {
                    throw new Error('Failed to cancel the reservation');
                }
            } catch (error) {
                console.error('Error canceling the reservation:', error);
            }
        },
        async fetchObservationDetails(observationId) {
            try {
                const response = await ApiService.get(`/observations/${observationId}`);
                if (response.status === 200) {
                    this.selectedObservation = response.data;
                    this.isDetailsPaneOpen = true;
                } else {
                    console.error('Failed to fetch observation details:', response.status);
                }
            } catch (error) {
                console.error('Error fetching observation details:', error);
            }
        },
        async updateObservation() {
            try {
                const response = await ApiService.patch(`/observations/${this.selectedObservation.id}/`, this.selectedObservation);
                if (response.status !== 200) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
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
        async updateObservation(observation) {
            try {
                const response = await ApiService.patch(`/observations/${observation.id}/`, observation);
                if (response.status !== 200) {
                    throw new Error('Network response was not ok');
                }
            } catch (error) {
                console.error('Error when updating the observation:', error);
            }
        },
        async exportData(format) {
            const filterQuery = this.createFilterQuery();
            const url = `observations/export?export_format=${format}&${filterQuery}`;

            try {
                const response = await ApiService.get(url, { responseType: 'blob' });
                const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.setAttribute('download', `export.${format}`);
                document.body.appendChild(link);
                link.click();
                link.remove();
            } catch (error) {
                console.error('Error exporting data:', error);
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
                        this.userMunicipalities = data.user.municipalities;
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
