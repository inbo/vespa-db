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
import { useVespaStore } from '@/stores/vespaStore';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { computed, onMounted, ref, watch } from 'vue';
import FilterComponent from './FilterComponent.vue';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
export default {
    components: {
        NavbarComponent,
        FooterComponent,
        FilterComponent
    },
    setup() {
        const vespaStore = useVespaStore();
        const map = ref(null);
        const markers = ref([]);
        const selectedObservation = ref(null);
        const isEditing = ref(false);

        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const parseLocation = (locationStr) => {
            // Check if the string includes 'POINT'
            if (locationStr.includes('POINT')) {
                // Extract the numbers after 'POINT (' and before the closing ')'
                const matches = locationStr.match(/POINT\s*\(([^)]+)\)/);
                if (matches) {
                    const points = matches[1].split(' ');
                    // Assuming the format is 'POINT (lng lat)'
                    const lat = parseFloat(points[1]);
                    const lng = parseFloat(points[0]);
                    return { lat, lng };
                }
            }
            console.error("Unable to parse location:", locationStr);
            return null;
        };
        const observations = computed(() => vespaStore.observations.map(obs => ({
            ...obs,
            location: parseLocation(obs.location)
        })));

        const filtersConfig = computed(() => ({
            minCreationDatetime: { label: 'Min Creation Date', type: 'date', value: '' },
            maxCreationDatetime: { label: 'Max Creation Date', type: 'date', value: '' },
            // Assuming these options are loaded from the store or another source
            municipalities: { label: 'Municipality', type: 'select', options: vespaStore.municipalities, value: [] },
            years: { label: 'Year', type: 'select', options: vespaStore.years, value: [] }
        }));

        const filters = ref({
            minCreationDatetime: '',
            maxCreationDatetime: '',
            municipalities: [],
            years: []
        });


        const updateSelectOptions = computed(() => {
            // Example logic to update options
            filtersConfig.value.municipalities.options = vespaStore.municipalities; // Assuming your store has this data
            filtersConfig.value.years.options = vespaStore.years; // Assuming your store has this data
        });

        // Function to update filters based on user input
        const updateFilters = (updatedFilters) => {
            // Loop through the updated filters and apply changes
            Object.keys(updatedFilters).forEach(key => {
                if (filters.value.hasOwnProperty(key)) {
                    filters.value[key] = updatedFilters[key];
                }
            });
            // Call a method to apply these filters
            applyFilters();
        };

        // Function to apply filters and fetch data based on the current filter state
        const applyFilters = async () => {
            // Construct the filter query based on the current state of `filters`
            // This query will depend on how your API expects to receive these filters
            let filterQuery = '?';
            // Append each filter to the query string if it's not empty
            Object.keys(filters.value).forEach(key => {
                const value = filters.value[key];
                if (value && Array.isArray(value) && value.length) {
                    filterQuery += `${key}=${value.join(',')}&`;
                } else if (value) {
                    filterQuery += `${key}=${value}&`;
                }
            });

            // Remove the last '&' for a clean query string
            filterQuery = filterQuery.slice(0, -1);

            // Assuming you have a method in your Pinia store to fetch observations with the constructed query
            await vespaStore.getObservations(filterQuery);
        };
        const fetchObservations = async () => {
            // Assuming you have a method to construct the filter query based on some criteria
            const filterQuery = ''; // Construct your filter query here
            await vespaStore.getObservations(filterQuery);
        };

        const initializeMapAndMarkers = () => {
            if (!map.value && document.getElementById('mapid')) { // Ensure the element is there
                map.value = L.map('mapid').setView([51.0, 4.5], 9);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: 'Map data © OpenStreetMap contributors',
                    maxZoom: 18,
                }).addTo(map.value);

                // Now that the map is guaranteed to be initialized, call updateMarkers
                updateMarkers();
            }
        };

        watch(observations, (newObservations) => {
            // Update markers based on new observations
            markers.value.forEach(marker => marker.remove());
            markers.value = [];
            newObservations.forEach(obs => {
                if (obs.location) {
                    const marker = L.marker([obs.location.lat, obs.location.lng])
                        .addTo(map.value)
                        .on('click', () => { selectedObservation.value = obs; });
                    markers.value.push(marker);
                }
            });
        }, { deep: true });

        const updateMarkers = () => {
            if (map.value && observations.value) {
                markers.value.forEach(marker => marker.remove()); // Remove existing markers
                markers.value = []; // Reset markers array

                observations.value.forEach(observation => {
                    if (observation.location) {
                        const customIcon = L.divIcon({
                            className: 'custom-div-icon',
                            html: "<i class='fa fa-bug' style='color: black; font-size: 24px;'></i>",
                            iconSize: [30, 42],
                            iconAnchor: [15, 42]
                        });
                        const marker = L.marker([observation.location.lat, observation.location.lng], { icon: customIcon })
                            .addTo(map.value)
                            .on('click', () => {
                                selectedObservation.value = observation;
                                // Additional logic for selecting an observation
                            });

                        markers.value.push(marker);
                    }
                });
            }
        };
        const startEdit = () => {
            isEditing.value = true;
        };

        const confirmUpdate = () => {
            isEditing.value = false;
            // Logic to confirm and save the updated observation
        };

        const cancelEdit = () => {
            isEditing.value = false;
        };

        onMounted(async () => {
            await fetchObservations();
            initializeMapAndMarkers();
        });


        return {
            selectedObservation,
            isEditing,
            markers,
            map,
            isLoggedIn,
            filtersConfig,
            updateFilters,
            startEdit,
            confirmUpdate,
            cancelEdit,
        };
    },
};
</script>