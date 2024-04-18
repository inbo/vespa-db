import ApiService from '@/services/apiService';

import L from 'leaflet';
import { MarkerClusterGroup } from 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster/dist/leaflet.markercluster';
import 'leaflet/dist/leaflet.css';
import { defineStore } from 'pinia';

export const useVespaStore = defineStore('vespaStore', {
    state: () => ({
        isLoggedIn: false,
        loading: false,
        error: null,
        markerClusterGroup: null,
        municipalities: [],
        selectedMunicipalities: [],
        observations: [],
        totalObservations: 0,
        selectedObservation: null,
        nextPage: null,
        previousPage: null,
        loadingObservations: false,
        markers: [],
        user: {},
        authInterval: null,
        isEditing: false,
        map: null,
        filters: {
            municipalities: [],
            years: [],
            anbAreasActief: null,
            nestType: null,
            nestStatus: null,
        },
        isDetailsPaneOpen: false,
        markerClickHandler: null,
        viewMode: 'map',
        userMunicipalities: [],
    }),
    getters: {
        canEditObservation: (state) => (observation) => {
            return state.isLoggedIn && state.userMunicipalities.includes(observation.municipality);
        },
    },
    actions: {
        async getObservations(page = 1, page_size = 10) {
            this.loadingObservations = true;
            const filterQuery = this.createFilterQuery();
            try {
                const response = await ApiService.get(`/observations?${filterQuery}&page=${page}&page_size=${page_size}`);
                if (response.status === 200) {
                    this.observations = response.data.results;
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
            this.loading = true;
            const filterQuery = this.createFilterQuery();
            const bbox = this.map.getBounds().toBBoxString();
            try {
                const response = await ApiService.get(`/observations/dynamic-geojson?${filterQuery}&bbox=${bbox}`);
                if (response.status === 200) {
                    this.observations = response.data.features;
                    this.updateMarkers();
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

            const filterQuery = this.createFilterQuery();

            if (this.viewMode === 'map') {
                this.loadGeoJsonData();
            } else {
                this.getObservations(filterQuery);
            }
        },
        initializeMapAndMarkers(elementId) {
            if (!this.map) {
                this.map = L.map(elementId).setView([50.8503, 4.3517], 8);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: 'Map data © OpenStreetMap contributors',
                    maxZoom: 18,
                }).addTo(this.map);

                this.markerClusterGroup = new MarkerClusterGroup();
                this.map.addLayer(this.markerClusterGroup);

                this.map.whenReady(() => {
                    this.loadGeoJsonData();
                });

                this.map.on('zoomend', () => {
                    this.loadGeoJsonData();
                });
            }
        },
        manageLayersBasedOnZoom() {
            this.map.addLayer(this.markerClusterGroup);
        },
        loadGeoJsonData() {
            if (this.map) {
                const bbox = this.map.getBounds().toBBoxString();
                let params = this.createFilterQuery();
                params = params ? `${params}&bbox=${bbox}` : `bbox=${bbox}`;
                this.getObservationsGeoJson(params);
            }
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
        updateMarkers() {
            if (this.map && this.markerClusterGroup) {
                this.markerClusterGroup.clearLayers();  // Clear previous markers from the cluster group

                const geoJsonLayer = L.geoJSON(this.observations, {
                    pointToLayer: (feature, latlng) => {
                        return this.createCircleMarker(feature, latlng);
                    }
                });

                this.markerClusterGroup.addLayer(geoJsonLayer);
            }
        },
        createCircleMarker(feature, latlng) {
            let markerOptions = {
                radius: 5 + (feature.properties.observations_count || 0) * 0.5,
                fillColor: this.getColor(feature.properties.observations_count || 1),
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            };
            return L.circleMarker(latlng, markerOptions).bindPopup(`Observatie ID: ${feature.properties.id}`);
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
        getColor(count) {
            return count > 10 ? '#800026' :
                count > 5 ? '#BD0026' :
                    count > 3 ? '#E31A1C' :
                        count > 1 ? '#FC4E2A' :
                            '#FFEDA0';
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
                        this.setUserMunicipalities(data.user.municipalities);
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
        selectObservation(observation) {
            this.selectedObservation = observation;
            this.isDetailsPaneOpen = true;
        },
        setViewMode(mode) {
            this.viewMode = mode;
        },
        setUserMunicipalities(municipalities) {
            console.log("Setting user municipalities:" + municipalities)
            this.userMunicipalities = municipalities;
        },
    },
});
