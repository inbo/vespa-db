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
                <p><strong>Attributes:</strong> <input v-if="isEditing" v-model="selectedObservation.attributes"
                        type="text" /> <span v-else>{{ selectedObservation.attributes | JSON }}</span></p>
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
            <span>Last Modification:</span>
            <label for="minLastModificationDatetime">From</label>
            <input type="datetime-local" v-model="filters.minLastModificationDatetime" id="minLastModificationDatetime">
            <label for="maxLastModificationDatetime">To</label>
            <input type="datetime-local" v-model="filters.maxLastModificationDatetime" id="maxLastModificationDatetime">
        </div>
        <div class="input-group">
            <button @click="applyFilters">Filter</button>
        </div>
    </div>
    <FooterComponent></FooterComponent>
</template>

<script>
import NavbarComponent from './NavbarComponent.vue';
import FooterComponent from './FooterComponent.vue';
export default {
    components: {
        NavbarComponent,
        FooterComponent,
    },
    data() {
        return {
            selectedObservation: null,
            isLoggedIn: false,
            isEditing: false,
            username: '',
            observations: [],
            map: null,
            markers: [],
            filters: {
                validated: false,
                minCreationDatetime: '',
                maxCreationDatetime: '',
                minLastModificationDatetime: '',
                maxLastModificationDatetime: ''
            },
        };
    },
    created() {
        this.initialize();
    },
    methods: {
        async initialize() {
            await this.checkLoginStatus();
        },
        selectObservation(observationData) {
            // Select a observation for viewing or editing
            this.selectedObservation = observationData;
        },
        async checkLoginStatus() {
            try {
                const response = await fetch('/check_login/', {
                    method: 'GET',
                    credentials: 'include'
                });
                if (response.ok) {
                    const data = await response.json();
                    this.isLoggedIn = data.isLoggedIn;
                    this.username = data.username;
                    this.user_id = data.user_id;
                } else {
                    this.isLoggedIn = false;
                }
            } catch (error) {
                this.isLoggedIn = false;
            }
        },
        async applyFilters() {
            let filterQuery = `/observations/?`;
            if (this.filters.validated) {
                filterQuery += `validated=${this.filters.validated}&`;
            }
            if (this.filters.minCreationDatetime) {
                filterQuery += `min_creation_datetime=${new Date(this.filters.minCreationDatetime).toISOString()}&`;
            }
            if (this.filters.maxCreationDatetime) {
                filterQuery += `max_creation_datetime=${new Date(this.filters.maxCreationDatetime).toISOString()}&`;
            }
            if (this.filters.minLastModificationDatetime) {
                filterQuery += `min_last_modification_datetime=${new Date(this.filters.minLastModificationDatetime).toISOString()}&`;
            }
            if (this.filters.maxLastModificationDatetime) {
                filterQuery += `max_last_modification_datetime=${new Date(this.filters.maxLastModificationDatetime).toISOString()}&`;
            }
            await this.getObservations(filterQuery);
        },
        async getObservations(filterQuery = '/observations/') {
            // Fetch observations data from the server
            try {
                const response = await fetch(filterQuery);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                this.observations = data;
                if (!this.map) {
                    this.initializeMapAndMarkers(); // Initialize map after fetching observations for the first time
                } else {
                    this.updateMarkers(); // Update markers based on new observations data
                }
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
                    const [_, longitude, latitude] = match; // Destructure to get longitude and latitude
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
                const response = await fetch(`/observations/${this.selectedObservation.id}/`, {
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
                const response = await fetch(`/observations/${this.selectedObservation.id}/`, {
                    method: 'PATCH',
                    credentials: 'include',
                    body: JSON.stringify(this.selectedObservation)
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                console.log('Success:', data);
                this.isEditing = false;
            } catch (error) {
                console.error('Error when updating the observation:', error);
            }
        },
        async checkLoginStatus() {
            try {
                const response = await fetch('/check_login/', {
                    method: 'GET',
                    credentials: 'include'
                });
                if (response.ok) {
                    const data = await response.json();
                    this.isLoggedIn = data.isLoggedIn;
                    this.username = data.username;
                    this.user_id = data.user_id;
                } else {
                    this.isLoggedIn = false;
                }
            } catch (error) {
                this.isLoggedIn = false;
            }
        },
        startEdit() {
            // Enable edit mode
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
        this.initializeMapAndMarkers();
        this.checkLoginStatus();
        this.getObservations();
        setInterval(this.getObservations, 20000); // Poll every 60 seconds
    }
};
</script>


<style scoped>
/* Voeg hier je CSS-stijlen toe */
</style>