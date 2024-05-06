<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPanel">
                <i class="fas fa-sliders-h"></i> Filters
            </button>
            <div id="map" class="h-100"></div>
            <div class="filter-panel"
                :class="{ 'd-none': !isFilterPaneOpen, 'd-block': isFilterPaneOpen, 'col-12': true, 'col-md-6': true, 'col-lg-4': true }">
                <FilterComponent />
            </div>
            <div class="details-panel"
                :class="{ 'd-none': !isDetailsPaneOpen, 'd-block': isDetailsPaneOpen, 'col-12': true, 'col-md-6': true, 'col-lg-4': true }">
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
import { useRouter } from 'vue-router';
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
        const router = useRouter();
        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = computed(() => vespaStore.isEditing);
        const map = computed(() => vespaStore.map);
        const markerClusterGroup = L.markerClusterGroup({ spiderfyOnMaxZoom: false, showCoverageOnHover: true, zoomToBoundsOnClick: true, disableClusteringAtZoom: 16 });
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
            if (!vespaStore.isDetailsPaneOpen) {
                router.push({ path: '/map' });
            }
        };

        const toggleFilterPanel = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };

        const openObservationDetails = async (properties) => {
            try {
                await vespaStore.fetchObservationDetails(properties.id);
                vespaStore.isDetailsPaneOpen = true;
                router.push({ path: `/map/observation/${properties.id}` });
            } catch (error) {
                console.error("Failed to fetch observation details:", error);
            }
        };

        const updateMarkers = () => {
            vespaStore.getObservationsGeoJson().then(geoJson => {
                const geoJsonLayer = L.geoJSON(vespaStore.observations, {
                    pointToLayer: (feature, latlng) => {
                        const marker = vespaStore.createCircleMarker(feature, latlng);
                        marker.on('click', () => openObservationDetails(feature.properties));
                        return marker;
                    }
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

        onMounted(async () => {
            vespaStore.fetchMunicipalities();
            // Check if there is an observation id in the URL
            const observationId = router.currentRoute.value.params.id;
            if (observationId) {
                await vespaStore.fetchObservationDetails(observationId);
                const location = selectedObservation.value.location;
                const [longitude, latitude] = location
                    .slice(location.indexOf("(") + 1, location.indexOf(")"))
                    .split(" ")
                    .map(parseFloat);

                vespaStore.map = L.map('map', {
                    center: [latitude, longitude],
                    zoom: 16,
                    maxZoom: 20,
                    layers: [
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: 'Map data © OpenStreetMap contributors'
                        }),
                    ]
                });
                updateMarkers();
            } else {
                vespaStore.map = L.map('map', {
                    center: [50.8503, 4.3517],
                    zoom: 9,
                    maxZoom: 20,
                    layers: [
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: 'Map data © OpenStreetMap contributors'
                        }),
                    ]
                });
                updateMarkers();
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
