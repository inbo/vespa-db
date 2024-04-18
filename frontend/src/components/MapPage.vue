<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPane">
                <i class="fas fa-sliders-h"></i> Filters
            </button>
            <div v-show="viewMode === 'map'" :key="mapKey" ref="mapContainer" class="h-100"></div>
            <TableViewComponent v-if="viewMode !== 'map'"></TableViewComponent>
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
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import FilterComponent from './FilterComponent.vue';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
import ObservationDetailsComponent from './ObservationDetailsComponent.vue';
import TableViewComponent from './TableViewComponent.vue';
export default {
    components: {
        NavbarComponent,
        FooterComponent,
        FilterComponent,
        ObservationDetailsComponent,
        TableViewComponent
    },
    setup() {
        const vespaStore = useVespaStore();
        const mapContainer = ref(null);
        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = computed(() => vespaStore.isEditing);
        const markers = computed(() => vespaStore.markers);
        const map = computed(() => vespaStore.map);
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const isDetailsPaneOpen = computed(() => vespaStore.isDetailsPaneOpen);
        const isFilterPaneOpen = ref(false);
        const viewMode = computed(() => vespaStore.viewMode);
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

        watch(() => vespaStore.viewMode, async (newVal) => {
            console.log(`View mode changing to ${newVal}`);
            if (newVal === 'map') {
                mapKey.value++;
                await nextTick();
                if (vespaStore.map) {
                    vespaStore.map.remove();
                    vespaStore.map = null;
                }
                vespaStore.initializeMapAndMarkers();
            }
        });
        onMounted(async () => {
            if (!vespaStore.map) {
                // Initializing map
                vespaStore.initializeMapAndMarkers(mapContainer.value);
            } else {
                // Wait until map bounds are ready or other necessary data is loaded.
                await nextTick();
                vespaStore.loadGeoJsonData();  // This should only be called when we are sure that bbox and filters are defined.
            }
        });

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
            viewMode,
            mapKey,
            mapContainer
        };
    },
};
</script>