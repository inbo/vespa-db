import ApiService from '@/services/apiService';
import L from 'leaflet';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet/dist/leaflet.css';
import { defineStore } from 'pinia';

export const useVespaStore = defineStore('vespaStore', {
    state: () => ({
        loadingAuth: true,
        isLoggedIn: false,
        loading: false,
        error: null,
        municipalities: [],
        municipalitiesFetched: false,
        provinces: [],
        provincesFetched: false,
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
            visible: true,
        },
        lastAppliedFilters: null,
        isDetailsPaneOpen: false,
        user: {},
        userMunicipalities: [],
        isAdmin: false,
    }),
    getters: {
        canEditObservation: (state) => (observation) => {
            if (state.isAdmin) {
                return true;
            }
            const municipalityName = state.municipalities.find(m => m.id === observation.municipality)?.name;
            return state.isLoggedIn && state.userMunicipalities.includes(municipalityName);
        },
        canEditAdminFields: (state) => state.isAdmin,
    },
    actions: {
        async getObservations(page = 1, page_size = 25, sortBy = null, sortOrder = 'asc') {
            const currentFilters = JSON.stringify(this.filters);
            if (this.table_observations.length > 0 && currentFilters === this.lastAppliedFilters) {
                return Promise.resolve();
            }
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
                    this.setLastAppliedFilters();
                    return Promise.resolve();
                } else {
                    throw new Error(`Network response was not ok, status code: ${response.status}`);
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error);
                this.error = error.message || 'Failed to fetch observations';
                return Promise.reject(error);
            } finally {
                this.loadingObservations = false;
            }
        },
        async getObservationsGeoJson() {
            const currentFilters = JSON.stringify(this.filters);

            // Check if data needs to be reloaded
            if (this.observations.length > 0 && currentFilters === this.lastAppliedFilters) return;

            this.loadingObservations = true;
            let filterQuery = this.createFilterQuery();
            if (!this.filters.min_observation_date && !this.isLoggedIn) {
                const defaultMinDate = this.formatDateWithoutTime(new Date('April 1, 2021').toISOString());
                filterQuery += (filterQuery ? '&' : '') + `min_observation_datetime=${defaultMinDate}`;
            }

            try {
                const response = await ApiService.get(`/observations/dynamic-geojson?${filterQuery}`);
                if (response.status === 200) {
                    this.observations = response.data.features;
                    this.setLastAppliedFilters();
                } else {
                    throw new Error(`Network response was not ok, status code: ${response.status}`);
                }
            } catch (error) {
                console.error('Error fetching observations:', error.message);
                this.error = error.message || 'Failed to fetch observations';
            } finally {
                this.loadingObservations = false;
            }
        },
        createFilterQuery() {
            let params = {};

            if (this.filters.municipalities.length > 0) {
                params['municipality_id'] = this.filters.municipalities.join(',');
            }

            if (this.filters.provinces.length > 0) {
                params['province_id'] = this.filters.provinces.join(',');
            }

            if (this.filters.anbAreasActief !== null) {
                params['anb'] = this.filters.anbAreasActief;
            }

            if (this.filters.visible !== null) {
                params['visible'] = this.filters.visible;
            }

            if (this.filters.nestType) {
                params['nest_type'] = this.filters.nestType;
            }

            if (this.filters.nestStatus) {
                params['nest_status'] = this.filters.nestStatus;
            }

            if (this.filters.min_observation_date) {
                params['min_observation_datetime'] = this.formatDateWithoutTime(this.filters.min_observation_date);
            }

            if (this.filters.max_observation_date) {
                params['max_observation_datetime'] = this.formatDateWithoutTime(this.filters.max_observation_date);
            }

            return Object.entries(params).map(([key, value]) => `${key}=${encodeURIComponent(value)}`).join('&');
        },
        formatDateWithoutTime(date) {
            const d = new Date(date);
            let month = '' + (d.getMonth() + 1);
            let day = '' + d.getDate();
            const year = d.getFullYear();

            if (month.length < 2) month = '0' + month;
            if (day.length < 2) day = '0' + day;

            return [year, month, day].join('-');
        },
        async applyFilters(filters) {
            this.filters = { ...this.filters, ...filters };
            //await this.getObservations();
        },
        async fetchProvinces() {
            if (this.provincesFetched) return;  // Skip fetching if data is already available

            try {
                const response = await ApiService.get('/provinces/');
                if (response.status === 200) {
                    this.provinces = response.data;
                    this.provincesFetched = true;
                } else {
                    console.error('Failed to fetch provinces: Status Code', response.status);
                }
            } catch (error) {
                console.error('Error fetching provinces:', error);
            }
        },
        async fetchMunicipalities() {
            if (this.municipalitiesFetched) return;  // Skip fetching if data is already available

            try {
                const response = await ApiService.get('/municipalities/');
                if (response.status === 200) {
                    this.municipalities = response.data;
                    this.municipalitiesFetched = true;
                } else {
                    console.error('Failed to fetch municipalities: Status Code', response.status);
                }
            } catch (error) {
                console.error('Error fetching municipalities:', error);
            }
        },
        createCircleMarker(feature, latlng) {
            let fillColor = this.getColorByStatus(feature.properties.status);
            let markerOptions = {
                radius: 10 + (feature.properties.observations_count || 0) * 0.5,
                fillColor: fillColor,
                color: feature.properties.id === this.selectedObservation?.id ? '#ea792a' : '#3c3c3c',
                weight: feature.properties.id === this.selectedObservation?.id ? 4 : 1,
                opacity: 1,
                fillOpacity: 0.8,
                className: feature.properties.id === this.selectedObservation?.id ? 'active-marker' : ''
            };
            const marker = L.circleMarker(latlng, markerOptions);
            return marker;
        },
        async reserveObservation(observation) {
            if (this.user.reservation_count < 50) {
                const response = await ApiService.patch(`/observations/${observation.id}/`, {
                    reserved_by: this.user.id
                });
                if (response.status === 200) {
                    this.selectedObservation = { ...this.selectedObservation, ...response.data };
                    this.updateMarkerColor(observation.id, '#ffc107');
                    await this.authCheck();
                } else {
                    throw new Error('Failed to reserve the observation');
                }
            } else {
                alert('You have reached the maximum number of reservations.');
            }
        },
        updateMarkerColor(observationId, fillColor, edgeColor = fillColor, weight = 4, className = '') {
            const markers = this.markerClusterGroup.getLayers();
            markers.forEach((marker) => {
                if (marker.feature.properties.id === observationId) {
                    marker.setStyle({
                        fillColor: fillColor,
                        color: edgeColor, // Use color for stroke
                        weight: weight
                    });
                    if (className) {
                        marker._path.classList.add(className);
                    } else {
                        marker._path.classList.remove('active-marker');
                    }
                }
            });
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
                    this.updateMarkerColor(observation.id, '#212529');
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
                    eradication_date: new Date().toISOString()
                });
                if (response.status === 200) {
                    this.selectedObservation = response.data;
                    this.updateMarkerColor(observationId, '#00FF00');
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
                    eradication_date: null
                });
                if (response.status === 200) {
                    this.selectedObservation = response.data;
                    this.updateMarkerColor(observationId, '#000000');
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
                    throw new Error('Failed to fetch observation details');
                }
            } catch (error) {
                console.error('Error fetching observation details:', error);
                this.error = 'Het ophalen van observatiedetails is mislukt.';
            }
        },
        formatToISO8601(datetime) {
            if (!datetime) return null;
            const date = new Date(datetime);
            return date.toISOString();
        },
        async updateObservation(observation) {
            observation.observation_datetime = this.formatToISO8601(observation.observation_datetime);
            observation.eradication_date = this.formatToISO8601(observation.eradication_date);

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
        async exportData(format) {
            const filterQuery = this.createFilterQuery();
            const url = `/observations/export?export_format=${format}&${filterQuery}`;

            try {
                const response = await ApiService.get(url, { responseType: 'blob' });
                const blob = new Blob([response.data], { type: response.headers['content-type'] });
                const downloadUrl = window.URL.createObjectURL(blob);
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
        async fetchMunicipalitiesByProvinces(provinceIds) {
            try {
                const response = await ApiService.get(`/municipalities/by_provinces/?province_ids=${provinceIds.join(',')}`);
                if (response.status === 200) {
                    this.municipalities = response.data;
                } else {
                    console.error('Failed to fetch filtered municipalities: Status Code', response.status);
                }
            } catch (error) {
                console.error('Error fetching filtered municipalities:', error);
            }
        },
        async login({ username, password }) {
            this.loading = true;
            this.error = null;
            try {
                const response = await ApiService.post("/login/", { username, password });
                if (response.status === 200) {
                    this.isLoggedIn = true;
                    this.authCheck();
                }
            } catch (error) {
                if (error.response && error.response.data) {
                    const errorMsg = error.response.data.error;
                    if (Array.isArray(errorMsg)) {
                        this.error = errorMsg.join(', ');
                    } else if (errorMsg.startsWith("Invalid username or password")) {
                        this.error = "Ongeldige gebruikersnaam of wachtwoord.";
                    } else {
                        this.error = errorMsg;
                    }
                } else {
                    this.error = "Er is een onverwachte fout opgetreden.";
                }
                this.isLoggedIn = false;
                this.user = {};
                this.loading = false;
            }
        },
        async authCheck() {
            this.loadingAuth = true; // Start loading
            this.loading = true;
            try {
                const response = await ApiService.get("/auth-check");
                const data = response.data;
                if (data.isAuthenticated && data.user) {
                    this.user = data.user;
                    this.userMunicipalities = data.user.municipalities;
                    this.isAdmin = data.user.is_staff;
                    this.error = "";
                    this.isLoggedIn = true;
                } else {
                    this.error = "";
                    this.isLoggedIn = false;
                    this.isAdmin = false;
                }
            } catch (error) {
                this.error = error;
                this.isLoggedIn = false;
            } finally {
                this.loadingAuth = false;
                this.loading = false;
            }
        },
        async logout() {
            this.loading = true;
            await ApiService
                .post("/logout/")
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
            this.error = null;
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
                await ApiService.post("/change-password/", {
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
        setLastAppliedFilters() {
            const currentFilters = JSON.stringify(this.filters);
            if (this.lastAppliedFilters !== currentFilters) {
                this.lastAppliedFilters = currentFilters;
            }
        },
        getColorByStatus(status) {
            if (status === 'eradicated') {
                return '#198754';
            } else if (status === 'reserved') {
                return '#ffc107';
            } else if (status === 'unsuccessful' || status === 'untreated' || status === 'unknown') {
                return '#212529';
            }
            return '#212529';
        },
    },
});