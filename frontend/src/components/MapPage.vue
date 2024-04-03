<template>
<div class="d-flex flex-column vh-100">
    <NavbarComponent />
    <div class="flex-grow-1 position-relative">
    <button class="btn-filter-toggle" @click="toggleFilterPane">
        <i class="fas fa-sliders-h"></i> Filters
    </button>

    <div id="mapid" class="h-100"></div>
    <div class="filter-panel" :class="{ 'panel-active': isFilterPaneOpen }">
        <FilterComponent/>
    </div>
    <div id="details" class="details-panel" :class="{ 'panel-active': isDetailsPaneOpen }">
        <h3>Observation Details</h3>
        <ObservationDetailsComponent/>
    </div>
    </div>
    <FooterComponent />
</div>
</template>
  
<script>
import { useVespaStore } from '@/stores/vespaStore';
import 'leaflet/dist/leaflet.css';
import { computed, onMounted, ref } from 'vue';
import FilterComponent from './FilterComponent.vue';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
import ObservationDetailsComponent from './ObservationDetailsComponent.vue';
export default {
    components: {
        NavbarComponent,
        FooterComponent,
        FilterComponent,
        ObservationDetailsComponent
    },
    setup() {
        const vespaStore = useVespaStore();

        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = computed(() => vespaStore.isEditing);
        const markers = computed(() => vespaStore.markers);
        const map = computed(() => vespaStore.map);
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const isDetailsPaneOpen = computed(() => vespaStore.isDetailsPaneOpen);
        const isFilterPaneOpen = ref(false);

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
        const toggleFilterPane = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };

        onMounted(async () => {
            await vespaStore.getObservations();
            vespaStore.initializeMapAndMarkers();
        });

        return {
            isFilterPaneOpen,
            toggleFilterPane,
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