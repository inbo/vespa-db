
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
        loadingObservations: false,
        selectedObservation: null,
        markerClusterGroup: null,
        authInterval: null,
        isEditing: false,
        map: null,
        isExporting: false,
        filters: {
            municipalities: [],
            provinces: [],
            anbAreasActief: null,
            nestType: null,
            nestStatus: null,
            min_observation_date: null,
            max_observation_date: null,
        },
        lastAppliedFilters: null,
        isDetailsPaneOpen: false,
        user: {},
        userMunicipalities: [],
        isAdmin: false,
        loginError: null,
        termsAcceptanceLoading: false,
        termsAcceptanceError: null,
        appInitialized: false,
        successMessage: null,
        markerCache: {},
    }),
    getters: {
        canEditObservation: (state) => (observation) => {
            if (state.isAdmin) {
                return true;
            }
            const municipalityName = state.municipalities.find(
                (m) => m.id === observation.municipality
            )?.name;
            return (
                state.isLoggedIn &&
                state.userMunicipalities.includes(municipalityName)
            );
        },
        canEditAdminFields: (state) => state.isAdmin,
    },
    actions: {
        async initializeApp() {
            if (this.appInitialized) return;
            
            try {
              await Promise.all([
                this.fetchMunicipalities(),
                this.fetchProvinces(),
                this.authCheck(), // Include auth check here if it should run once on app start
              ]);
              this.appInitialized = true;
            } catch (error) {
              console.error('Failed to initialize app:', error);
              this.error = 'Failed to initialize application data';
            }
        },
        async getObservationsGeoJson() {
            const currentFilters = JSON.stringify(this.filters);
        
            // Check if data needs to be reloaded
            if (this.observations.length > 0 && currentFilters === this.lastAppliedFilters) return;
        
            this.loadingObservations = true;
            let filterQuery = this.createFilterQuery();
            
            // ALWAYS apply min date filter - regardless of login status
            if (!this.filters.min_observation_date) {
                const defaultMinDate = this.formatDateWithoutTime(new Date('April 1, 2025').toISOString());
                filterQuery += (filterQuery ? '&' : '') + `min_observation_datetime=${defaultMinDate}`;
            }
        
            try {
                const url = `/observations/dynamic-geojson/?${filterQuery}`;
                console.log('[API CALL DEBUG] Calling URL:', url);
                const response = await ApiService.get(url);
                if (response.status === 200) {
                    this.observations = response.data.features || [];
                    console.log('[API RESPONSE DEBUG] Number of observations received:', this.observations.length);
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
            let queryParts = [];
        
            if (this.filters.municipalities.length > 0) {
                console.log('[MUNICIPALITY FILTER DEBUG] Number of municipalities:', this.filters.municipalities.length);
                console.log('[MUNICIPALITY FILTER DEBUG] Municipality IDs:', JSON.stringify(this.filters.municipalities));
                // Add each municipality_id as separate query parameter
                this.filters.municipalities.forEach((id, index) => {
                    console.log(`[MUNICIPALITY FILTER DEBUG] Adding municipality ${index + 1}:`, id);
                    queryParts.push(`municipality_id=${encodeURIComponent(id)}`);
                });
            }
        
            if (this.filters.provinces.length > 0) {
                // Add each province_id as separate query parameter
                this.filters.provinces.forEach(id => {
                    queryParts.push(`province_id=${encodeURIComponent(id)}`);
                });
            }
        
            if (this.filters.anbAreasActief !== null) {
                queryParts.push(`anb=${encodeURIComponent(this.filters.anbAreasActief)}`);
            }
        
            if (this.filters.nestType && this.filters.nestType.length > 0) {
                console.log('[NEST TYPE DEBUG] Nest types:', JSON.stringify(this.filters.nestType));
                // Add each nest_type as separate query parameter
                this.filters.nestType.forEach(type => {
                    queryParts.push(`nest_type=${encodeURIComponent(type)}`);
                });
            }
        
            if (this.filters.nestStatus && this.filters.nestStatus.length > 0) {
                console.log('[NEST STATUS DEBUG] Nest statuses:', JSON.stringify(this.filters.nestStatus));
                // Add each nest_status as separate query parameter
                this.filters.nestStatus.forEach(status => {
                    queryParts.push(`nest_status=${encodeURIComponent(status)}`);
                });
            }
        
            if (this.filters.min_observation_date) {
                queryParts.push(`min_observation_datetime=${encodeURIComponent(this.formatDateWithoutTime(this.filters.min_observation_date))}`);
            } else {
                queryParts.push(`min_observation_datetime=${encodeURIComponent(this.formatDateWithoutTime(new Date('April 1, 2025').toISOString()))}`);
            }
        
            if (this.filters.max_observation_date) {
                queryParts.push(`max_observation_datetime=${encodeURIComponent(this.formatDateWithEndOfDayTime(this.filters.max_observation_date))}`);
            }
        
            const query = queryParts.join('&');
            console.log('[FILTER DEBUG] Total query parts:', queryParts.length);
            console.log('[FILTER DEBUG] Final query string:', query);
            console.log('[FILTER DEBUG] Query string length:', query.length);
            return query;
        },
        formatDateWithoutTime(date) {
            const d = new Date(date);
            const cetString = new Date(d.toLocaleString('en-US', { timeZone: 'Europe/Brussels' }));
            let month = '' + (cetString.getMonth() + 1);
            let day = '' + cetString.getDate();
            const year = cetString.getFullYear();

            if (month.length < 2) month = '0' + month;
            if (day.length < 2) day = '0' + day;

            return [year, month, day].join('-');
        },
        formatDateWithEndOfDayTime(date) {
            // Format to CET
            const d = new Date(date);
            // Ensure the date is interpreted in CET
            const cetString = new Date(d.toLocaleString('en-US', { timeZone: 'Europe/Brussels' }));
            let month = '' + (cetString.getMonth() + 1);
            let day = '' + cetString.getDate();
            const year = cetString.getFullYear();

            if (month.length < 2) month = '0' + month;
            if (day.length < 2) day = '0' + day;

            return `${[year, month, day].join('-')} 23:59:59`;
        },
        async applyFilters(filters) {
            console.log('[APPLY FILTERS DEBUG] Incoming filters:', JSON.stringify(filters));
            console.log('[APPLY FILTERS DEBUG] Current filters before update:', JSON.stringify(this.filters));
            this.filters = { ...this.filters, ...filters };
            console.log('[APPLY FILTERS DEBUG] Filters after update:', JSON.stringify(this.filters));
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
        async updateObservations() {
            try {
              await this.getObservationsGeoJson();
            } catch (error) {
              console.error('Error updating observations:', error);
            }
        },      
        createCircleMarker(feature, latlng) {
            const status = feature.properties.status;
            const styles = this.getColorStylesByStatus(status);

            const opts = {
                radius: 8 + (feature.properties.observations_count || 0) * 0.5, // Adjusted radius slightly
                fillColor: styles.fillColor,
                color: styles.borderColor, // Base border color
                weight: styles.baseWeight, // Base border weight
                opacity: 1,
                fillOpacity: styles.fillOpacity,
                className: `observation-marker status-${status}` // Add status-specific class
            };

            const marker = L.circleMarker(latlng, opts);
            
            // Store original base style for deselection and status updates
            marker.originalStyle = {
                fillColor: styles.fillColor,
                color: styles.borderColor,
                weight: styles.baseWeight,
                fillOpacity: styles.fillOpacity
            };
            marker.feature = feature; // Keep reference to feature for its properties
            return marker;
        },
        refreshMarkerStyle(observationId) {
            const marker = this.markerCache[observationId];
            if (!marker || !marker.feature || !marker.feature.properties) return;
        
            let currentStatus = marker.feature.properties.status;
        
            // If this observation is the currently selected one, its details might be more up-to-date
            if (this.selectedObservation && this.selectedObservation.id === observationId) {
                const statusFromSelected = this.determineStatusFromObservationData(this.selectedObservation);
                if (statusFromSelected !== currentStatus) {
                    currentStatus = statusFromSelected;
                    marker.feature.properties.status = currentStatus; // Update status on the marker's feature data
                }
            }
        
            const styles = this.getColorStylesByStatus(currentStatus);
        
            // Update originalStyle on the marker, in case the status changed
            marker.originalStyle = {
                fillColor: styles.fillColor,
                color: styles.borderColor,
                weight: styles.baseWeight,
                fillOpacity: styles.fillOpacity
            };
        
            let finalStyle = { ...marker.originalStyle }; // Start with base style
        
            const isSelected = this.selectedObservation && this.selectedObservation.id === observationId;
        
            if (isSelected) {
                finalStyle.color = '#ea792a'; // Selection border color
                finalStyle.weight = 4;         // Selection border weight
                marker._path?.classList.add('active-marker');
                if (marker.bringToFront) marker.bringToFront();
            } else {
                marker._path?.classList.remove('active-marker');
            }
        
            marker.setStyle(finalStyle);
        },
        async reserveObservation(observation) {
            if (!this.user || typeof this.user.reservation_count === 'undefined') {
                alert('Gebruikersinformatie niet geladen, kan niet reserveren.');
                return;
            }
            if (this.user.reservation_count < 50) {
                try {
                    const response = await ApiService.patch(`/observations/${observation.id}/`, {
                        reserved_by: this.user.id
                    });
                    if (response.status === 200) {
                        this.selectedObservation = { ...this.selectedObservation, ...response.data };
                        
                        const marker = this.markerCache[observation.id];
                        if (marker && marker.feature && marker.feature.properties) {
                            marker.feature.properties.status = "reserved";
                        }
                        this.refreshMarkerStyle(observation.id);
                        await this.authCheck();
                    } else {
                        throw new Error('Failed to reserve the observation');
                    }
                } catch (error) {
                    console.error('Error reserving observation:', error);
                    this.error = 'Kon de observatie niet reserveren.';
                }
            } else {
                alert('You have reached the maximum number of reservations.');
            }
        },
        async acceptTermsOfService() {
            this.termsAcceptanceLoading = true;
            this.termsAcceptanceError = null;
            
            try {
                const response = await ApiService.post("/accept-terms/", {
                    user_id: this.user.id,
                    accepted: true
                });
                
                if (response.status === 200) {
                    this.user = { ...this.user, hasAcceptedTerms: true };
                    return true;
                } else {
                    throw new Error('Failed to record terms acceptance');
                }
            } catch (error) {
                console.error('Error accepting terms of service:', error);
                
                if (error.response && error.response.data) {
                    this.termsAcceptanceError = error.response.data.error || 'Failed to accept terms of service';
                } else {
                    this.termsAcceptanceError = error.message || 'Failed to accept terms of service';
                }
                
                return false;
            } finally {
                this.termsAcceptanceLoading = false;
            }
        },
        async cancelReservation(observation) {
            try {
                const response = await ApiService.patch(`/observations/${observation.id}/`, {
                    reserved_by: null
                });
                if (response.status === 200) {
                    this.selectedObservation = { ...this.selectedObservation, ...response.data };
                    const marker = this.markerCache[observation.id];
                    if (marker && marker.feature && marker.feature.properties) {
                        // Determine new status (likely 'untreated' if no eradication_result)
                        marker.feature.properties.status = this.determineStatusFromObservationData(response.data);
                    }
                    this.refreshMarkerStyle(observation.id);
                } else {
                    throw new Error('Failed to cancel the reservation');
                }
            } catch (error) {
                console.error('Error canceling reservation:', error);
                this.error = 'Kon de reservatie niet annuleren.';
            }
        },
        async fetchObservationDetails(observationId) {
            this.loading = true;
            try {
                const response = await ApiService.get(`/observations/${observationId}/`);
                if (response.status === 200) {
                    this.selectedObservation = response.data;
                    this.refreshMarkerStyle(observationId); 
                } else {
                    throw new Error('Failed to fetch observation details');
                }
            } catch (error) {
                console.error('Error fetching observation details:', error);
                this.error = "Het ophalen van observatiedetails is mislukt.";
            } finally {
                this.loading = false;
            }
        },
        formatToISO8601(datetime) {
            if (!datetime) return null;
            const date = new Date(datetime);
            return date.toISOString();
        },
        async updateObservation(observation) {
            try {
                // Make a copy to ensure we don't modify the original
                const observationToSend = { ...observation };
                
                // Convert boolean queen_present to explicit true/false
                if ('queen_present' in observationToSend) {
                    observationToSend.queen_present = observationToSend.queen_present === true;
                }
                if ('moth_present' in observationToSend) {
                    observationToSend.moth_present = observationToSend.moth_present === true;
                }
                if ('duplicate_nest' in observationToSend) {
                    observationToSend.duplicate_nest = observationToSend.duplicate_nest === true;
                }
                if ('other_species_nest' in observationToSend) {
                    observationToSend.other_species_nest = observationToSend.other_species_nest === true;
                }
                
                const response = await ApiService.patch(`/observations/${observation.id}/`, observationToSend);
                if (response.status === 200) {
                    this.selectedObservation = response.data; // Update selected observation with full data from response
                    
                const newStatus = this.determineStatusFromObservationData(response.data);
                const markerToUpdate = this.markerCache[observation.id];

                if (markerToUpdate) {
                    if (markerToUpdate.feature && markerToUpdate.feature.properties) {
                        markerToUpdate.feature.properties.status = newStatus;
                    }
                    this.refreshMarkerStyle(observation.id); // Correctly uses observation.id here
                }
                return response.data;
                } else {
                    throw new Error('Network response was not ok');
                }
            } catch (error) {
                console.error('Error when updating the observation:', error);
                return null;
            }
        },
        async acceptTermsOfService() {
            this.termsAcceptanceLoading = true;
            this.termsAcceptanceError = null;
            
            try {
                const response = await ApiService.post("/accept-terms/", {
                    user_id: this.user.id,
                    accepted: true
                });
                
                if (response.status === 200) {
                    this.user = { ...this.user, hasAcceptedTerms: true };
                    return true;
                } else {
                    throw new Error('Failed to record terms acceptance');
                }
            } catch (error) {
                console.error('Error accepting terms of service:', error);
                
                if (error.response && error.response.data) {
                    this.termsAcceptanceError = error.response.data.error || 'Failed to accept terms of service';
                } else {
                    this.termsAcceptanceError = error.message || 'Failed to accept terms of service';
                }
                
                return false;
            } finally {
                this.termsAcceptanceLoading = false;
            }
        },
        async exportData(format) {
            try {
                this.isExporting = true;
        
                const response = await ApiService.get('/observations/export/');
                const exportData = response.data;
        
                if (exportData.status === 'completed') {
                    await this.downloadFileFromApi(`/observations/download_export/?export_id=${exportData.export_id}`);
                } else {
                    throw new Error(exportData.error || 'Unexpected export status');
                }
            } catch (error) {
                console.error('Export error:', error);
                if (error.response && error.response.data) {
                    this.modalTitle = 'Export Error';
                    this.modalMessage = error.response.data.error || 'The export could not be completed.';
                    this.isModalVisible = true;
                } else {
                    this.modalTitle = 'Export Error';
                    this.modalMessage = error.message || 'An unexpected error occurred';
                    this.isModalVisible = true;
                }
            } finally {
                this.isExporting = false;
            }
        },
        async downloadFileFromApi(url) {
            try {
                console.log('Downloading file from:', url);
                
                const response = await ApiService.get(url, {
                    responseType: 'blob',
                });
        
                const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = downloadUrl;
                
                let filename = 'observations_export.csv';
                const disposition = response.headers['content-disposition'];
                if (disposition && disposition.indexOf('filename=') !== -1) {
                    filename = disposition.split('filename=')[1].replace(/"/g, '');
                }
                
                link.setAttribute('download', filename);
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(downloadUrl);
            } catch (error) {
                console.error('Error downloading file:', error);
                throw new Error('Failed to download file: ' + error.message);
            }
        },
        async pollForGeneratedExport(exportId) {
            let completed = false;
            let attempts = 0;
            const maxAttempts = 40; // Poll for up to 20 minutes (30s intervals)
        
            while (!completed && attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 30000)); // Wait 30 seconds for generation
                attempts++;
        
                try {
                    const statusResponse = await ApiService.get(`/observations/export_status/?export_id=${exportId}`);
                    const statusData = statusResponse.data;
        
                    if (statusData.status === 'completed') {
                        // Hide the waiting modal and start download
                        this.isModalVisible = false;
                        await this.downloadFileFromApi(`/observations/download_export/?export_id=${exportId}`);
                        completed = true;
                        break;
                    } else if (statusData.status === 'failed') {
                        throw new Error(statusData.error || 'Export generation failed');
                    } else if (statusData.status === 'pending') {
                        // Update modal with current status
                        if (statusData.message) {
                            this.modalMessage = `${statusData.message} (${attempts}/${maxAttempts} checks)`;
                        }
                        console.log(`Export generation in progress... (attempt ${attempts}/${maxAttempts})`);
                    }
        
                } catch (pollError) {
                    console.warn('Error checking export status:', pollError);
                    // Continue polling despite error, but throw after max attempts
                    if (attempts >= maxAttempts) {
                        throw new Error('Export generation timed out. Please try again later.');
                    }
                }
            }
        
            if (!completed) {
                throw new Error('Export generation timed out. Please try again later.');
            }
        },
        
        async pollForExportCompletion(exportId) {
            // Original polling logic for regular exports (shorter intervals)
            let completed = false;
            let attempts = 0;
        
            while (!completed && attempts < 60) {
                await new Promise(resolve => setTimeout(resolve, 3000)); // 3 second intervals
                attempts++;
        
                try {
                    const statusResponse = await ApiService.get(`/observations/export_status/?export_id=${exportId}`);
                    const statusData = statusResponse.data;
        
                    if (statusData.status === 'completed') {
                        await this.downloadFileFromApi(`/observations/download_export/?export_id=${exportId}`);
                        completed = true;
                        break;
                    } else if (statusData.status === 'failed') {
                        throw new Error(statusData.error || 'Export failed');
                    }
        
                    if (statusData.progress) {
                        console.log(`Export progress: ${statusData.progress}%`);
                    }
                } catch (pollError) {
                    console.warn('Error checking export status:', pollError);
                }
            }
        
            if (!completed) {
                throw new Error('Export timed out. Please try again later.');
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
        async searchAddress(query) {
            try {
                const response = await ApiService.get(`/search-address/?query=${encodeURIComponent(query)}`);
                if (response.status === 200 && response.data) {
                    return response.data;
                }
                return null;
            } catch (error) {
                console.error('Error searching address:', error);
                throw error;
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
                        this.loginError = errorMsg.join(', ');
                    } else if (errorMsg.startsWith("Invalid username or password")) {
                        this.loginError = "Ongeldige gebruikersnaam of wachtwoord.";
                    } else {
                        this.loginError = errorMsg;
                    }
                } else {
                    this.loginError = "Er is een onverwachte fout opgetreden.";
                }
                this.isLoggedIn = false;
                this.user = {};
                this.loading = false;
            }
        },
        async authCheck() {
            this.loadingAuth = true;
            try {
                const response = await ApiService.get("/auth-check/");
                const data = response.data;
                if (data.isAuthenticated && data.user) {
                    this.user = data.user;
                    this.userMunicipalities = data.user.municipalities;
                    this.isAdmin = data.user.is_superuser;
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
                this.isAdmin = false;
            } finally {
                this.loadingAuth = false;
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
        resetFilters(options = {}) {
            this.filters = {
                min_observation_date: options.min_observation_date || '2025-04-01',
                max_observation_date: null,
                provinces: [],
                municipalities: [],
                nestType: null,
                nestStatus: null,
                anbAreasActief: null
            };
            this.getObservationsGeoJson();
        },
        determineStatusFromObservationData(observationData) {
            if (!observationData) return "untreated";
            if (observationData.eradication_result === 'successful') {
                return "eradicated";
            }
            if (observationData.eradication_result !== null && typeof observationData.eradication_result !== 'undefined') {
                return "visited";
            }
            if (observationData.reserved_by !== null && typeof observationData.reserved_by !== 'undefined') {
                return "reserved";
            }
            return "untreated";
        },
        getColorStylesByStatus(status) {
            switch (status) {
                case 'eradicated': // Bestreden nest (Green fill)
                    return { fillColor: '#198754', borderColor: '#145c3f', baseWeight: 1, fillOpacity: 0.8 }; // Darker green border
                case 'visited':    // Bezocht nest (White fill, Green border)
                    return { fillColor: '#FFFFFF', borderColor: '#198754', baseWeight: 2, fillOpacity: 0.9 }; // Green border, thicker
                case 'reserved':   // Gereserveerd nest (Yellow fill)
                    return { fillColor: '#ffc107', borderColor: '#cc9a05', baseWeight: 1, fillOpacity: 0.8 }; // Darker yellow border
                case 'untreated':  // Gerapporteerd nest (Black/Dark fill)
                    return { fillColor: '#212529', borderColor: '#000000', baseWeight: 1, fillOpacity: 0.8 }; // Black border
                default:
                    // console.warn(`Unknown status: ${status}, defaulting to untreated style.`);
                    return { fillColor: '#212529', borderColor: '#000000', baseWeight: 1, fillOpacity: 0.8 };
            }
        },
    },
});