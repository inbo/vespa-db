
<template>
  <div class="d-flex flex-column vh-100">
    <NavbarComponent />
    <div class="flex-grow-1 position-relative">
      <div class="search-bar">
        <input v-model="searchQuery" @keyup.enter="searchAddress" placeholder="Zoek een adres..." />
        <button @click="searchAddress">
          <i class="fas fa-search"></i>
        </button>
      </div>
      <button class="btn-filter-toggle" @click="toggleFilterPanel">
        <i class="fas fa-sliders-h"></i> Filters
      </button>
      <div id="map" class="h-100"></div>
      <div class="loading-screen" v-if="isMapLoading">
        Observaties laden...
      </div>
      <div class="loading-screen" v-if="isExporting">
        Exporteren...
      </div>
      <div class="map-legend" v-if="map && !isMapLoading">
        <div>
          <span class="legend-icon bg-reported"></span> Gerapporteerd nest
        </div>
        <div>
          <span class="legend-icon bg-reserved"></span> Gereserveerd nest
        </div>
        <div>
          <span class="legend-icon bg-eradicated"></span> Bestreden nest
        </div>
        <div>
          <span class="legend-icon bg-visited"></span> Bezocht nest
        </div>
      </div>
      <div class="filter-panel"
        :class="{ 'd-none': !isFilterPaneOpen, 'd-block': isFilterPaneOpen, 'col-12': true, 'col-md-6': true, 'col-lg-4': true }">
        <div class="float-end mb-3">
          <button type="button" class="btn-close" aria-label="Close" @click="toggleFilterPanel"></button>
        </div>
        <div class="filter-content">
          <FilterComponent />
        </div>
      </div>
      <div class="details-panel"
        :class="{ 'd-none': !isDetailsPaneOpen, 'd-block': isDetailsPaneOpen, 'col-12': true, 'col-md-6': true, 'col-lg-4': true }">
        <ObservationDetailsComponent @updateMarkerColor="updateMarkerColor" />
      </div>
      <div v-if="formattedError" class="alert alert-danger position-absolute top-0 start-50 translate-middle-x mt-2">
        {{ formattedError }}
      </div>
    </div>
  </div>
</template>

<script>
import L from 'leaflet';
import { useVespaStore } from '@/stores/vespaStore';
import { nextTick } from 'vue';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
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
    const searchQuery = ref('');
    const isExporting = computed(() => vespaStore.isExporting);
    const router = useRouter();
    const selectedObservation = computed(() => vespaStore.selectedObservation);
    const isEditing = computed(() => vespaStore.isEditing);
    const map = ref(null);
    const isLoggedIn = computed(() => vespaStore.isLoggedIn);
    const isDetailsPaneOpen = computed(() => vespaStore.isDetailsPaneOpen);
    const isFilterPaneOpen = ref(false);
    const error = computed(() => vespaStore.error);
    const loadingObservations = computed(() => vespaStore.loadingObservations);
    const isMapLoading = ref(true);
    const filtersUpdated = ref(false);
    const isFetchingGeoJson = ref(false);
    const searchAddress = async () => {
      if (searchQuery.value) {
        try {
          const result = await vespaStore.searchAddress(searchQuery.value);
          if (result) {
            map.value.setView([result.lat, result.lon], 16);
          } else {
            // Handle case when address is not found

          }
        } catch (error) {
          console.error('Error searching address:', error);
        }
      }
    };
    const formattedError = computed(() => {
      if (!error.value) return null;
      if (error.value.includes("Failed to fetch observation details")) {
        return "Het ophalen van observatiedetails is mislukt.";
      }
      return error.value;
    });

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
        router.push({ path: '/' });
      }
    };

    const toggleFilterPanel = () => {
      isFilterPaneOpen.value = !isFilterPaneOpen.value;
    };

    const openObservationDetails = async (properties) => {
      try {
        await vespaStore.fetchObservationDetails(properties.id);
        if (vespaStore.selectedObservation && !vespaStore.selectedObservation.visible) {
          return;
        }
        vespaStore.isDetailsPaneOpen = true;
        router.push({ path: `/observation/${properties.id}` });
      } catch (error) {
        console.error("Failed to fetch observation details:", error);
      }
    };

    function debounce(func, wait) {
      let timeout;
      return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
      };
    }

    const updateMarkers = debounce(async () => {
        if (isFetchingGeoJson.value) return;
        isFetchingGeoJson.value = true;
        try {
            await vespaStore.updateObservations(); // This fetches and sets vespaStore.observations

            const observations = vespaStore.observations; // GeoJSON features
            const existingMarkerIds = new Set(Object.keys(vespaStore.markerCache));
            const newMarkerIds = new Set(observations.map(obs => obs.properties.id.toString()));

            existingMarkerIds.forEach((id) => {
                if (!newMarkerIds.has(id)) {
                    const marker = vespaStore.markerCache[id];
                    if (marker) {
                        vespaStore.markerClusterGroup.removeLayer(marker);
                        delete vespaStore.markerCache[id];
                    }
                }
            });

            const newMarkers = [];
            observations.forEach((feature) => {
                const id = feature.properties.id.toString();
                if (!vespaStore.markerCache[id]) { // Only create if not exists
                    const marker = vespaStore.createCircleMarker(
                        feature,
                        L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0])
                    );

                    marker.on('click', () => {
                        openObservationDetails(feature.properties);
                    });
                    
                    vespaStore.markerCache[id] = marker;
                    newMarkers.push(marker);
                } else {
                    const existingMarker = vespaStore.markerCache[id];
                    if (JSON.stringify(existingMarker.feature.properties) !== JSON.stringify(feature.properties)) {
                         existingMarker.feature = feature; // Update feature data
                         vespaStore.refreshMarkerStyle(id); // Refresh style
                    }
                }
            });

            if (newMarkers.length > 0) {
                vespaStore.markerClusterGroup.addLayers(newMarkers);
            }
            
            // If a specific observation was selected (e.g. direct navigation), ensure its style is correct
            if (selectedObservation.value) {
                vespaStore.refreshMarkerStyle(selectedObservation.value.id);
            }

        } catch (error) {
            console.error('Error updating markers:', error);
            vespaStore.error = "Fout bij het bijwerken van de kaartobservaties.";
        } finally {
            isFetchingGeoJson.value = false; // Ensure this is defined in setup: const isFetchingGeoJson = ref(false);
            isMapLoading.value = false;
        }
    }, 600);


    watch(selectedObservation, (newObs, oldObs) => {
        // Check if it's a genuinely different observation or just internal changes to the same one
        if (oldObs && (!newObs || newObs.id !== oldObs.id)) {
            vespaStore.refreshMarkerStyle(oldObs.id); // Deselect old
        }
        if (newObs && (!oldObs || newObs.id !== oldObs.id)) {
            nextTick(() => {
                vespaStore.refreshMarkerStyle(newObs.id); // Select new
            });
        }
        // If newObs and oldObs are the same id but content changed (e.g. status update from details panel)
        if (newObs && oldObs && newObs.id === oldObs.id) {
             nextTick(() => { // Ensure DOM/marker cache is updated if needed
                vespaStore.refreshMarkerStyle(newObs.id); // Refresh style of currently selected
            });
        }
    }, { deep: true });

  const updateMarkerColor = (observationId) => {
    if (observationId) {
      vespaStore.refreshMarkerStyle(observationId);
    } else {
      console.warn('MapComponent: updateMarkerColor was called without an observationId.');
    }
  };

    watch(
      () => vespaStore.filters,
      (newFilters) => {
        filtersUpdated.value = true;
        updateMarkers();
      },
      { deep: true }
    );

    watch(
      () => router.currentRoute.value,
      (newRoute, oldRoute) => {
        if (newRoute.path !== oldRoute.path && !newRoute.path.includes('/observation/')) {
          vespaStore.isDetailsPaneOpen = false;
        }
      }
    );

    onMounted(async () => {
      // Initialize marker cache if it doesn't exist
      if (!vespaStore.markerCache) {
        vespaStore.markerCache = {};
      }

      // Create the map immediately
      map.value = L.map('map', {
        center: [50.8503, 4.3517],
        zoom: 9,
        maxZoom: 19,
        renderer: L.svg(),
        layers: [
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data © OpenStreetMap contributors',
            maxZoom: 19,
          }),
        ],
      });
      vespaStore.map = map.value;

      // Set up clustering
      vespaStore.markerClusterGroup = L.markerClusterGroup({
        spiderfyOnMaxZoom: false,
        showCoverageOnHover: true,
        zoomToBoundsOnClick: true,
        disableClusteringAtZoom: 16,
        iconCreateFunction: (cluster) => {
          return L.divIcon({
            html: `<div style="background-color: rgba(var(--bs-dark-rgb)); color: white;"><span>${cluster.getChildCount()}</span></div>`,
            className: 'marker-cluster',
            iconSize: L.point(40, 40),
          });
        },
        polygonOptions: {
          color: '#ea792a',
          weight: 2,
          opacity: 0.5,
          fillOpacity: 0.2,
          fillColor: '#ea792a',
        },
        spiderLegPolylineOptions: {
          color: '#ea792a',
          weight: 1.5,
          opacity: 0.8,
        },
      });
      if (!map.value.hasLayer(vespaStore.markerClusterGroup)) {
        map.value.addLayer(vespaStore.markerClusterGroup);
      }

      // Fetch app data in background
      await vespaStore.initializeApp();

      if (!vespaStore.filters.min_observation_date) {
          vespaStore.applyFilters({
              min_observation_date: new Date('April 1, 2024').toISOString(),
          });
      }
      
      const observationIdParam = router.currentRoute.value.params.id;
      if (observationIdParam) {
        isMapLoading.value = true; // Show loading while we process direct navigation
        await updateMarkers(); // Load all markers first
        try {
            await vespaStore.fetchObservationDetails(observationIdParam); // This sets selectedObservation & calls refreshMarkerStyle
            if (vespaStore.selectedObservation) {
                vespaStore.isDetailsPaneOpen = true;
                const obsLocation = vespaStore.selectedObservation.location;
                if (obsLocation?.coordinates) { // Assuming GeoJSON point geometry
                    map.value.setView([obsLocation.coordinates[1], obsLocation.coordinates[0]], 16);
                }
                // refreshMarkerStyle is called within fetchObservationDetails now
            } else {
                 router.push({ path: '/' }); // Observation not found or error, redirect
            }
        } catch (error) {
            console.error("Failed to load observation for direct navigation:", error);
            vespaStore.error = "Kon de geselecteerde observatie niet laden.";
            router.push({ path: '/' });
        } finally {
             isMapLoading.value = false;
        }
      } else {
        updateMarkers(); // Initial load of markers
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
      formattedError,
      loadingObservations,
      isMapLoading,
      updateMarkerColor,
      searchQuery,
      searchAddress,
      isExporting,
      isEditing,
    };
  },
};
</script>