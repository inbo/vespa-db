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
        router.push({ path: '/map' });
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
        router.push({ path: `/map/observation/${properties.id}` });
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
      if (isFetchingGeoJson.value) return; // Prevent multiple calls

      isFetchingGeoJson.value = true;

      try {
        await vespaStore.getObservationsGeoJson();
        const geoJsonLayer = L.geoJSON(vespaStore.observations, {
          pointToLayer: (feature, latlng) => {
            const marker = vespaStore.createCircleMarker(feature, latlng);
            marker.on('click', () => {
              openObservationDetails(feature.properties);
              marker.setStyle({
                fillColor: marker.options.fillColor,
                color: '#ea792a',
                weight: 4
              });
            });
            return marker;
          },
        });
        vespaStore.markerClusterGroup.clearLayers();
        vespaStore.markerClusterGroup.addLayer(geoJsonLayer);
        map.value.addLayer(vespaStore.markerClusterGroup);
        filtersUpdated.value = false;

        // Update the selected marker style
        if (selectedObservation.value) {
          const selectedMarker = vespaStore.markerClusterGroup.getLayers().find(marker => marker.feature.properties.id === selectedObservation.value.id);
          if (selectedMarker) {
            selectedMarker.setStyle({
              fillColor: selectedMarker.options.fillColor,
              color: '#ea792a',
              weight: 4
            });
          }
        }
      } catch (error) {
        console.error('Error updating markers:', error);
      } finally {
        isFetchingGeoJson.value = false;
        isMapLoading.value = false;
        vespaStore.getObservations(1, 25).catch(error => console.error('Error fetching observations:', error));
      }
    }, 300);

    watch(selectedObservation, (newObservation, oldObservation) => {
      if (newObservation && !newObservation.visible) {
        vespaStore.isDetailsPaneOpen = false;
        router.push({ path: '/map' });
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

        clearAndUpdateMarkers();
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
      if (!vespaStore.municipalitiesFetched) await vespaStore.fetchMunicipalities();
      if (!vespaStore.provincesFetched) await vespaStore.fetchProvinces();
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
          fillColor: '#ea792a'
        },
        spiderLegPolylineOptions: {
          color: '#ea792a',
          weight: 1.5,
          opacity: 0.8,
        }
      });

      const tileLayerOptions = {
        attribution: 'Map data © OpenStreetMap contributors',
        maxZoom: 19,
      };

      const observationId = router.currentRoute.value.params.id;

      if (observationId) {
        await vespaStore.fetchObservationDetails(observationId);
        const location = selectedObservation.value.location;
        const loc = selectedObservation.value.location;
        let longitude, latitude;
        if (typeof loc === 'string') {
          // If location is in WKT format, e.g. "POINT(5.6899 50.8084)"
          const coords = loc.slice(loc.indexOf('(') + 1, loc.indexOf(')')).split(' ');
          [longitude, latitude] = coords.map(parseFloat);
        } else if (loc && loc.coordinates) {
          // If location is a GeoJSON object { type: "Point", coordinates: [lng, lat] }
          [longitude, latitude] = loc.coordinates;
        } else {
          // Fallback center
          longitude = 4.3517;
          latitude = 50.8503;
        }
        map.value = L.map('map', {
          center: [latitude, longitude],
          zoom: 16,
          maxZoom: 19,
          layers: [
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: 'Map data © OpenStreetMap contributors',
              maxZoom: 19,
            }),
          ],
        });
        vespaStore.isDetailsPaneOpen = true;
        updateMarkers();
      } else {
        map.value = L.map('map', {
          center: [50.8503, 4.3517],
          zoom: 9,
          maxZoom: 19,
          layers: [
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', tileLayerOptions),
          ],
        });
      }

      vespaStore.map = map.value;
      // if (vespaStore.lastAppliedFilters === null || vespaStore.lastAppliedFilters === 'null') {
      //   vespaStore.setLastAppliedFilters();
      // }
      updateMarkers();


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