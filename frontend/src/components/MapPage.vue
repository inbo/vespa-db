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
import 'leaflet/dist/leaflet.css';
import { computed, onMounted } from 'vue';
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

        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = computed(() => vespaStore.isEditing);
        const markers = computed(() => vespaStore.markers);
        const map = computed(() => vespaStore.map);
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);


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
            await vespaStore.getObservations();
            vespaStore.initializeMapAndMarkers();
        });

        return {
            selectedObservation,
            isEditing,
            markers,
            map,
            isLoggedIn,
            startEdit,
            confirmUpdate,
            cancelEdit,
        };
    },
};
</script>