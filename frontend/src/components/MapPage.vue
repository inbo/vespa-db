<template>
    <NavbarComponent />
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
                <button v-if="isLoggedIn && isEditing" @click="deleteObservation">Verwijderen</button>
                <button v-if="isLoggedIn && isEditing" @click="cancelEdit">Annuleren</button>
            </div>
            <div v-if="!selectedObservation">
                <p>No observation selected</p>
            </div>
        </div>
    </div>
    <div id="filters">
        <div class="input-group">
            <label for="validated">Validated</label>
            <input type="checkbox" v-model="filters.validated" id="validated">
        </div>

        <div class="input-group">
            <span>Creation Date:</span>
            <label for="minCreationDatetime">From</label>
            <input type="datetime-local" v-model="filters.minCreationDatetime" id="minCreationDatetime">
            <label for="maxCreationDatetime">To</label>
            <input type="datetime-local" v-model="filters.maxCreationDatetime" id="maxCreationDatetime">
        </div>
        <div class="input-group">
            <button @click="applyFilters">Filter</button>
        </div>
    </div>
    <FooterComponent></FooterComponent>
</template>

<script>
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { mapActions, mapState } from 'vuex';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
export default {
    components: {
        NavbarComponent,
        FooterComponent,
    },
    data() {
        return {
            selectedObservation: null,
            isEditing: false,
            observations: [],
            map: null,
            markers: [],
            filters: {
                validated: false,
                minCreationDatetime: '',
                maxCreationDatetime: ''
            },
        };
    },
    computed: {
        ...mapState(['isLoggedIn', 'username', 'userId']),
    },
    methods: {
        ...mapActions(['fetchUserStatus']),
        selectObservation(observationData) {
            // Select a observation for viewing or editing
            this.selectedObservation = observationData;
        },
        async applyFilters() {
            let filterQuery = `${process.env.VUE_APP_API_URL}/observations/?`;
            if (this.filters.validated) {
                filterQuery += `validated=${this.filters.validated}&`;
            }
            if (this.filters.minCreationDatetime) {
                filterQuery += `min_creation_datetime=${this.filters.minCreationDatetime.toISOString()}&`;
            }
            if (this.filters.maxCreationDatetime) {
                filterQuery += `max_creation_datetime=${this.filters.maxCreationDatetime.toISOString()}&`;
            }
            await this.getObservations(filterQuery);
        },
        async getObservations(filterQuery = `${process.env.VUE_APP_API_URL}/observations/`) {
            try {
                const response = await fetch(filterQuery, { credentials: 'include' });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                this.observations = data;
                this.updateMarkers();
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error);
            }
        },
        initializeMapAndMarkers() {
            // Initialize map and place markers for each observation
            this.map = L.map('mapid').setView([51.0, 4.5], 9);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: 'Map data © OpenStreetMap contributors',
                maxZoom: 18,
            }).addTo(this.map);
            this.updateMarkers();
        },
        updateMarkers() {
            // Clear existing markers
            this.markers.forEach(marker => this.map.removeLayer(marker));
            this.markers = []; // Reset markers array

            // Add new markers based on observations data
            this.observations.forEach((observation) => {
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
                }
            });
        },
        deleteObservation() {
            if (!confirm("Are you sure you want to delete this observation?")) {
                return;
            }
            try {
                const response = fetch(`${process.env.VUE_APP_API_URL}/observations/${this.selectedObservation.id}/`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                console.log('Observation deleted successfully');
                this.selectedObservation = null; // Reset selected observation
                this.getObservations(); // Refresh observations list
            } catch (error) {
                console.error('Error when deleting the observation:', error);
            }
        },

        updateObservation() {
            try {
                const response = fetch(`${process.env.VUE_APP_API_URL}/observations/${this.selectedObservation.id}/`, {
                    method: 'PATCH',
                    credentials: 'include',
                    body: JSON.stringify(this.selectedObservation)
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = response.json();
                console.log('Success:', data);
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
            this.initializeMapAndMarkers();
            this.getObservations();
        });

        setInterval(() => {
            this.getObservations();
        }, 120000); // Poll every 120 seconds
    }
};
</script>