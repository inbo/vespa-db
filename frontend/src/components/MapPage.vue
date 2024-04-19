<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPane">
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
import { computed, onMounted, ref } from 'vue';
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
        const toggleFilterPane = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };
        const toggleDetailsPane = () => {
            vespaStore.isDetailsPaneOpen = !vespaStore.isDetailsPaneOpen;
        };
        onMounted(() => {
            vespaStore.map = L.map('map', {
                center: [50.8503, 4.3517],
                zoom: 8,
                layers: [
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: 'Map data © OpenStreetMap contributors'
                    }),
                ]
            });
            const markerClusterGroup = L.markerClusterGroup({ spiderfyOnMaxZoom: false, showCoverageOnHover: false, zoomToBoundsOnClick: false });
            if (vespaStore.observations.length === 0) {
                vespaStore.getObservationsGeoJson().then(geoJson => {
                    const geoJsonLayer = L.geoJSON(vespaStore.observations, {
                        pointToLayer: (feature, latlng) => vespaStore.createCircleMarker(feature, latlng)
                    });

                    markerClusterGroup.addLayer(geoJsonLayer);
                    vespaStore.map.addLayer(markerClusterGroup);
                });
            } else {
                console.log("using existing data")
                console.log("length obs:" + vespaStore.observations.length)
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
            toggleFilterPane,
            toggleDetailsPane,
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