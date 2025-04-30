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
      </div>
      <div class="filter-panel"
        :class="{ 'd-none': !isFilterPaneOpen, 'd-block': isFilterPaneOpen, 'col-12': true, 'col-md-6': true, 'col-lg-4': true }">
        <FilterComponent />
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
import { useVespaStore } from '@/stores/vespaStore';
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
    const isFetchingGeoJson = ref(false); // Flag to prevent multiple calls
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
        await vespaStore.updateObservations();

        const observations = vespaStore.observations;
        const existingMarkerIds = new Set(Object.keys(vespaStore.markerCache));
        const newMarkerIds = new Set(observations.map(obs => obs.properties.id.toString()));

        // 1. Remove old markers
        existingMarkerIds.forEach((id) => {
          if (!newMarkerIds.has(id)) {
            const marker = vespaStore.markerCache[id];
            if (marker) {
              vespaStore.markerClusterGroup.removeLayer(marker);
              delete vespaStore.markerCache[id];
            }
          }
        });

        // 2. Create new markers
        const newMarkers = [];

        observations.forEach((feature) => {
          const id = feature.properties.id.toString();
          if (!vespaStore.markerCache[id]) {
            const marker = vespaStore.createCircleMarker(
              feature,
              L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0])
            );

            // your existing click handler
            marker.on('click', () => {
              openObservationDetails(feature.properties);
              marker.setStyle({
                fillColor: marker.options.fillColor,
                color: '#ea792a',
                weight: 4,
              });
            });

            vespaStore.markerCache[id] = marker;
            newMarkers.push(marker);
          }
        });

        // 3. Add ALL markers at once
        if (newMarkers.length > 0) {
          vespaStore.markerClusterGroup.addLayers(newMarkers);
        }

        filtersUpdated.value = false;

        // ighlight selected marker if needed
        if (selectedObservation.value) {
          const selectedMarker = vespaStore.markerCache[selectedObservation.value.id];
          if (selectedMarker) {
            selectedMarker.setStyle({
              fillColor: selectedMarker.options.fillColor,
              color: '#ea792a',
              weight: 4,
            });
          }
        }
      } catch (error) {
        console.error('Error updating markers:', error);
      } finally {
        isFetchingGeoJson.value = false;
        isMapLoading.value = false;
      }
    }, 600);


    watch(selectedObservation, (newObservation, oldObservation) => {
      if (newObservation && !newObservation.visible) {
        vespaStore.isDetailsPaneOpen = false;
        router.push({ path: '/' });
        return;
      }
      if (newObservation && oldObservation && newObservation.id !== oldObservation.id) {
        const oldMarker = vespaStore.markerClusterGroup.getLayers().find(marker => marker.feature.properties.id === oldObservation.id);
        if (oldMarker) {
          vespaStore.updateMarkerColor(oldObservation.id, oldMarker.options.fillColor, oldMarker.options.fillColor, 1, '');
        }

        const newMarker = vespaStore.markerClusterGroup.getLayers().find(marker => marker.feature.properties.id === newObservation.id);
        if (newMarker) {
          vespaStore.updateMarkerColor(newObservation.id, newMarker.options.fillColor, '#ea792a', 4, 'active-marker');
        }
      }
    });
    const clearAndUpdateMarkers = () => {
      if (vespaStore.markerClusterGroup) {
        vespaStore.markerClusterGroup.clearLayers();
      }
      vespaStore.observations = [];
      updateMarkers();
    };

    const updateMarkerColor = (observationId, fillColor, edgeColor, weight) => {
      vespaStore.updateMarkerColor(observationId, fillColor, edgeColor, weight);
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

      // Apply default date filter if not logged in
      if (!vespaStore.filters.min_observation_date && !vespaStore.isLoggedIn) {
        vespaStore.applyFilters({
          min_observation_date: new Date('April 1, 2024').toISOString(),
        });
      }

      // Check if we're navigating directly to an observation
      const observationId = router.currentRoute.value.params.id;
      if (observationId) {
        try {
          // First load the markers
          await updateMarkers();

          // Then fetch the selected observation details
          await vespaStore.fetchObservationDetails(observationId);

          // Open details panel and center map on the observation if it exists
          if (vespaStore.selectedObservation) {
            vespaStore.isDetailsPaneOpen = true;

            // Parse location
            let latitude = 50.8503;
            let longitude = 4.3517;
            const location = vespaStore.selectedObservation.location;
            if (location) {
              if (typeof location === 'string' && location.includes('POINT')) {
                const coords = location
                  .slice(location.indexOf('(') + 1, location.indexOf(')'))
                  .split(' ');
                [longitude, latitude] = coords.map(parseFloat);
              } else if (location.coordinates) {
                [longitude, latitude] = location.coordinates;
              }
            }

            // Center and zoom the map
            map.value.setView([latitude, longitude], 16);

            // Highlight the marker if it exists
            if (vespaStore.markerCache[observationId]) {
              vespaStore.updateMarkerColor(
                observationId,
                vespaStore.markerCache[observationId].options.fillColor,
                '#ea792a',
                4,
                'active-marker'
              );
            }
          }
        } catch (error) {
          console.error("Failed to load observation details:", error);
        }
      } else {
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
      formattedError,
      loadingObservations,
      isMapLoading,
      updateMarkerColor,
      searchQuery,
      searchAddress,
      isExporting,
    };
  },
};
</script>