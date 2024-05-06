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
        provinces: [],
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
            provinces: [],
            anbAreasActief: null,
            nestType: null,
            nestStatus: null,
            min_observation_date: null,
            max_observation_date: null,
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
        async getObservations(page = 1, page_size = 25, sortBy = null, sortOrder = 'asc') {
            this.loadingObservations = true;
            const orderQuery = sortBy ? `&ordering=${sortOrder === 'asc' ? '' : '-'}${sortBy}` : '';
            const filterQuery = this.createFilterQuery();
            try {
                const response = await ApiService.get(`/observations?${filterQuery}${orderQuery}&page=${page}&page_size=${page_size}`);
                if (response.status === 200) {
                    this.table_observations = response.data.results;
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
            const additionalFilters = this.isLoggedIn ? '' : `&min_observation_datetime=${new Date('April 1, 2021').toISOString()}`;

            try {
                const response = await ApiService.get(`/observations/dynamic-geojson?${filterQuery}${additionalFilters}`);
                if (response.status === 200) {
                    this.observations = response.data.features;
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
            const params = [];

            if (this.filters.municipalities.length > 0) {
                params.push(`municipality_id=${this.filters.municipalities.join(',')}`);
            }

            if (this.filters.provinces.length > 0) {
                params.push(`province_id=${this.filters.provinces.join(',')}`);
            }

            if (this.filters.anbAreasActief !== null) {
                params.push(`anb=${this.filters.anbAreasActief}`);
            }

            if (this.filters.nestType) {
                params.push(`nest_type=${this.filters.nestType}`);
            }

            if (this.filters.nestStatus) {
                params.push(`nest_status=${this.filters.nestStatus}`);
            }

            if (this.filters.min_observation_date) {
                params.push(`min_observation_datetime=${this.filters.min_observation_date}`);
            }

            if (this.filters.max_observation_date) {
                params.push(`max_observation_datetime=${this.filters.max_observation_date}`);
            }

            return params.length > 0 ? params.join('&') : '';
        },
        async applyFilters(filters) {
            this.filters = { ...this.filters, ...filters };
        },
        async fetchProvinces() {
            try {
                const response = await ApiService.get('/provinces/');
                if (response.status === 200) {
                    this.provinces = response.data;
                } else {
                    console.error('Failed to fetch provinces: Status Code', response.status);
                }
            } catch (error) {
                console.error('Error fetching provinces:', error);
            }
        },
        async fetchMunicipalities() {
            try {
                const response = await ApiService.get('/municipalities/');
                if (response.status === 200) {
                    this.municipalities.value = response.data;
                } else {
                    console.error('Failed to fetch municipalities: Status Code', response.status);
                }
            } catch (error) {
                console.error('Error fetching municipalities:', error);
            }
        },
        createCircleMarker(feature, latlng) {
            let markerOptions = {
                radius: 10 + (feature.properties.observations_count || 0) * 0.5,
                fillColor: "#FF7800",
                color: "#000",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            };
            return L.circleMarker(latlng, markerOptions).bindPopup(`Observatie ID: ${feature.properties.id}`);
        },
        async reserveObservation(observation) {
            if (this.user.reservation_count < 50) {
                const response = await ApiService.patch(`/observations/${observation.id}/`, {
                    reserved_by: this.user.id
                });
                if (response.status === 200) {
                    this.selectedObservation = { ...this.selectedObservation, ...response.data };
                    // Perform authCheck to update reservation_count
                    await this.authCheck();
                } else {
                    throw new Error('Failed to reserve the observation');
                }
            } else {
                alert('You have reached the maximum number of reservations.');
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
        async markObservationAsEradicated(observationId) {
            try {
                const response = await ApiService.patch(`/observations/${observationId}/`, {
                    eradication_datetime: new Date().toISOString()
                });
                if (response.status === 200) {
                    this.selectedObservation = response.data;
                    return response.data;
                } else {
                    throw new Error('Failed to mark observation as eradicated');
                }
            } catch (error) {
                console.error('Error marking observation as eradicated:', error);
                throw error;
            }
        },
        async markObservationAsNotEradicated(observationId) {
            try {
                const response = await ApiService.patch(`/observations/${observationId}/`, {
                    eradication_datetime: null
                });
                if (response.status === 200) {
                    this.selectedObservation = response.data;
                    return response.data;
                } else {
                    throw new Error('Failed to mark observation as not eradicated');
                }
            } catch (error) {
                console.error('Error marking observation as not eradicated:', error);
                throw error;
            }
        },
        async fetchObservationDetails(observationId) {
            try {
                const response = await ApiService.get(`/observations/${observationId}`);
                if (response.status === 200) {
                    this.selectedObservation = response.data;
                } else {
                    console.error('Failed to fetch observation details:', response.status);
                }
            } catch (error) {
                console.error('Error fetching observation details:', error);
            }
        },
        formatToISO8601(datetime) {
            if (!datetime) return null;
            const date = new Date(datetime);
            return date.toISOString();
        },
        async updateObservation(observation) {
            observation.observation_datetime = this.formatToISO8601(observation.observation_datetime);
            observation.eradication_datetime = this.formatToISO8601(observation.eradication_datetime);

            try {
                const response = await ApiService.patch(`/observations/${observation.id}/`, observation);
                if (response.status === 200) {
                    this.selectedObservation = response.data;
                    return response.data;
                } else {
                    throw new Error('Network response was not ok');
                }
            } catch (error) {
                console.error('Error when updating the observation:', error);
                return null;
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
                return response
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
