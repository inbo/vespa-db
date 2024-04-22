<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPanel">
                <i class="fas fa-sliders-h"></i> Filters
            </button>
            <div id="map" class="h-100"></div>
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
    </div>
</template>
  
<script>
import { useVespaStore } from '@/stores/vespaStore';
import 'leaflet/dist/leaflet.css';
import { computed, onMounted, ref, watch } from 'vue';
import FilterComponent from './FilterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
import ObservationDetailsComponent from './ObservationDetailsComponent.vue';

export default {
    components: {
        NavbarComponent,
        FilterComponent,
        ObservationDetailsComponent,
    },
    setup() {
        const vespaStore = useVespaStore();
        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = computed(() => vespaStore.isEditing);
        const map = computed(() => vespaStore.map);
        const markerClusterGroup = L.markerClusterGroup({ spiderfyOnMaxZoom: false, showCoverageOnHover: true, zoomToBoundsOnClick: true });
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const isDetailsPaneOpen = computed(() => vespaStore.isDetailsPaneOpen);
        const isFilterPaneOpen = ref(false);

        const startEdit = () => {
            isEditing.value = true;
        };

        const confirmUpdate = () => {
            isEditing.value = false;
        };

        const cancelEdit = () => {
            isEditing.value = false;
        };
        const toggleDetailsPane = () => {
            vespaStore.isDetailsPaneOpen = !vespaStore.isDetailsPaneOpen;
        };
        const toggleFilterPanel = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };
        const updateMarkers = () => {
            vespaStore.getObservationsGeoJson().then(geoJson => {
                const geoJsonLayer = L.geoJSON(vespaStore.observations, {
                    pointToLayer: (feature, latlng) => vespaStore.createCircleMarker(feature, latlng)
                });

                markerClusterGroup.addLayer(geoJsonLayer);
                vespaStore.map.addLayer(markerClusterGroup);
            });
        };
        const clearAndupdateMarkers = () => {
            markerClusterGroup.clearLayers();
            vespaStore.observations = [];
            updateMarkers();
        };
        watch(() => vespaStore.filters, (newFilters) => {
            clearAndupdateMarkers();
        }, { deep: true });

        onMounted(() => {
            vespaStore.fetchMunicipalities();
            vespaStore.map = L.map('map', {
                center: [50.8503, 4.3517],
                zoom: 8,
                layers: [
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: 'Map data © OpenStreetMap contributors'
                    }),
                ]
            });
            if (vespaStore.observations.length === 0) {
                updateMarkers();
            } else {
                // In a happy flow, this would not apply  
                const geoJsonLayer = L.geoJSON(vespaStore.observations, {
                    pointToLayer: (feature, latlng) => vespaStore.createCircleMarker(feature, latlng)
                });

                markerClusterGroup.addLayer(geoJsonLayer);
                vespaStore.map.addLayer(markerClusterGroup);
            }
        });

        return {
            isDetailsPaneOpen,
            isFilterPaneOpen,
            toggleDetailsPane,
            toggleFilterPanel,
            selectedObservation,
            isEditing,
            map,
            isLoggedIn,
            startEdit,
            confirmUpdate,
            cancelEdit,
        };
    },
};
</script>
  