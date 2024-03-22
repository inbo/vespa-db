<template>
    <NavbarComponent />
    <div id="filters">
        <FilterComponent :initialFilters="filtersConfig" @updateFilters="updateFilters" />
    </div>
    <div id="main-content">
        <div id="mapid"></div>
        <div id="details">
            <h3>Observation Details</h3>
            <div v-if="selectedObservation">
                <p><strong>ID:</strong> {{ selectedObservation.id }}</p>
                <p><strong>Source:</strong> <input v-if="isEditing" v-model="selectedObservation.source" type="text" />
                    <span v-else>{{ selectedObservation.source }}</span>
                </p>
                <p><strong>Validated:</strong> <input v-if="isEditing" v-model="selectedObservation.validated"
                        type="checkbox" /> <span v-else>{{ selectedObservation.validated }}</span></p>
                <p><strong>Notes:</strong> <textarea v-if="isEditing" v-model="selectedObservation.notes"></textarea>
                    <span v-else>{{ selectedObservation.notes
                        }}</span>
                </p>
                <p><strong>Admin Notes:</strong> <textarea v-if="isEditing"
                        v-model="selectedObservation.admin_notes"></textarea> <span v-else>{{
            selectedObservation.admin_notes }}</span></p>
                <p><strong>Species:</strong> <input v-if="isEditing" v-model="selectedObservation.species"
                        type="number" /> <span v-else>{{ selectedObservation.species }}</span></p>
                <p><strong>Activity:</strong> <input v-if="isEditing" v-model="selectedObservation.activity"
                        type="text" /> <span v-else>{{ selectedObservation.activity }}</span></p>
                <p><strong>Creation Datetime:</strong> <input v-if="isEditing"
                        v-model="selectedObservation.creation_datetime" type="datetime-local" /> <span v-else>{{
            selectedObservation.creation_datetime }}</span></p>
                <p><strong>Last Modification Datetime:</strong> <input v-if="isEditing"
                        v-model="selectedObservation.last_modification_datetime" type="datetime-local" /> <span
                        v-else>{{ selectedObservation.last_modification_datetime }}</span></p>


                <button v-if="isLoggedIn && !isEditing" @click="startEdit">Aanpassen</button>
                <button v-if="isLoggedIn && isEditing" @click="confirmUpdate">Bevestigen</button>
                <button v-if="isLoggedIn && isEditing" @click="cancelEdit">Annuleren</button>
            </div>
            <div v-if="!selectedObservation">
                <p>No observation selected</p>
            </div>
        </div>
    </div>
    <FooterComponent></FooterComponent>
</template>

<script>
import ApiService from '@/services/apiService';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { mapActions, mapState } from 'vuex';
import FilterComponent from './FilterComponent.vue';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
export default {
    components: {
        NavbarComponent,
        FooterComponent,
        FilterComponent
    },
    data() {
        return {
            selectedObservation: null,
            isEditing: false,
            map: null,
            markers: [],
            filters: {
                validated: false,
                minCreationDatetime: '',
                maxCreationDatetime: ''
            },
            filtersConfig: {
                minCreationDatetime: { label: 'Min Creation Datetime', type: 'date', value: '' },
                maxCreationDatetime: { label: 'Max Creation Datetime', type: 'date', value: '' },
            }
        };
    },
    computed: {
        ...mapState(['isLoggedIn', 'username', 'userId', 'observations']),
    },
    watch: {
        observations(newVal) {
            if (newVal && newVal.length > 0) {
                this.updateMarkers();
            }
        },
    },
    methods: {
        ...mapActions(['fetchUserStatus']),
        selectObservation(observationData) {
            // Select a observation for viewing or editing
            this.selectedObservation = observationData;
        },
        updateFilters(filters) {
            this.filters = {
                ...this.filters,
                ...filters
            };
            this.applyFilters();
        },
        async applyFilters() {
            let filterQuery = `?`;

            // If there are municipality filters
            if (this.filters.municipalities && this.filters.municipalities.length) {
                filterQuery += `municipality_id=${this.filters.municipalities.join(',')}&`;
            }

            // If there are year filters
            if (this.filters.years && this.filters.years.length) {
                filterQuery += `year_range=${this.filters.years.join(',')}&`;
            }

            if (!this.filters.municipalities.length && !this.filters.years.length) {
                filterQuery = '';
            }

            // Proceed to fetch observations with the constructed or default query
            this.$store.dispatch('getObservations', filterQuery);
        },
        initializeMapAndMarkers() {
            this.map = L.map('mapid').setView([51.0, 4.5], 9);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: 'Map data © OpenStreetMap contributors',
                maxZoom: 18,
            }).addTo(this.map);
            this.updateMarkers();
        },
        updateMarkers() {
            this.markers.forEach(marker => this.map.removeLayer(marker));
            this.markers = []; // Reset markers array

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
        startEdit() {
            this.isEditing = true;
        },
        confirmUpdate() {
            this.updateObservation();
        },
        cancelEdit() {
            this.isEditing = false;
        },
    },
    mounted() {
        this.fetchUserStatus().then(() => {
            this.$store.dispatch('getObservations');
            this.initializeMapAndMarkers();
        });

        setInterval(() => {
            this.$store.dispatch('getObservations');
        }, 120000); // Poll every 120 seconds
    },
};
</script>
