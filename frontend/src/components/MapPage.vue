<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPane">
                <i class="fas fa-sliders-h"></i> Filters
            </button>
            <div ref="mapContainer" class="h-100"></div>
            <div class="filter-panel" :class="{ 'panel-active': isFilterPaneOpen }">
                <FilterComponent />
            </div>
            <div class="details-panel" :class="{ 'panel-active': isDetailsPaneOpen }">
                <div class="d-flex justify-content-between align-items-center">
                    <h3>Observatie details</h3>
                    <button type="button" class="btn-close" aria-label="Close" @click="toggleDetailsPane"></button>
                </div>
                <ObservationDetailsComponent />
            </div>
        </div>
        <FooterComponent />
    </div>
</template>
  
<script>
import { useVespaStore } from '@/stores/vespaStore';
import 'leaflet/dist/leaflet.css';
import { computed, nextTick, onActivated, onMounted, ref } from 'vue';
import FilterComponent from './FilterComponent.vue';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
import ObservationDetailsComponent from './ObservationDetailsComponent.vue';
export default {
    components: {
        NavbarComponent,
        FooterComponent,
        FilterComponent,
        ObservationDetailsComponent,
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
        const mapContainer = ref(null);
        const mapKey = ref(0);

        const startEdit = () => {
            isEditing.value = true;
        };

        const confirmUpdate = () => {
            isEditing.value = false;
        };

        const cancelEdit = () => {
            isEditing.value = false;
        };
        const toggleFilterPane = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };
        const toggleDetailsPane = () => {
            vespaStore.isDetailsPaneOpen = !vespaStore.isDetailsPaneOpen;
        };
        const initializeMap = () => {
            if (!vespaStore.map) {
                console.log('initializing map');
                vespaStore.initializeMapAndMarkers(mapContainer.value);
            } else {
                console.log('map already initialized');
                nextTick(() => {
                    vespaStore.map = null
                    vespaStore.initializeMapAndMarkers(mapContainer.value);
                });
            }
        };

        onMounted(initializeMap);
        onActivated(initializeMap);

        return {
            isDetailsPaneOpen,
            isFilterPaneOpen,
            toggleFilterPane,
            toggleDetailsPane,
            selectedObservation,
            isEditing,
            markers,
            map,
            isLoggedIn,
            startEdit,
            confirmUpdate,
            cancelEdit,
            mapContainer
        };
    },
};
</script>