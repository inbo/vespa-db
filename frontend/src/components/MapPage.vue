<template>
    <div class="d-flex flex-column vh-100">
    <NavbarComponent />
    <div class="container-fluid">
        <FilterComponent @updateFilters="updateFilters" />
    </div>
    <div class="flex-grow-1">
        <div class="row h-100">
            <div id="mapid" class="col-md-9 h-100"></div>
            <div id="details" class="col-md-3 bg-light border-start overflow-auto">
                <h3>Observation Details</h3>
                <div v-if="selectedObservation" class="mb-3">
                    <div class="mb-2">
                        <p><strong>ID:</strong> {{ selectedObservation.id }}</p>
                    </div>
                    <div class="mb-2">
                        <button v-if="isLoggedIn && !isEditing" @click="startEdit">Aanpassen</button>
                        <button v-if="isLoggedIn && isEditing" @click="confirmUpdate">Bevestigen</button>
                        <button v-if="isLoggedIn && isEditing" @click="cancelEdit">Annuleren</button>
                    </div>
                </div>
                <div v-if="!selectedObservation">
                    <p>No observation selected</p>
                </div>
            </div>
        </div>
    </div>
    <FooterComponent></FooterComponent>
    </div>
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