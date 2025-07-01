<template>
  <div class="d-flex flex-column vh-100 app-container">
    <NavbarComponent />
    <div class="flex-grow-1 position-relative map-wrapper">
      <div id="map" class="h-100"></div>

      <div class="search-bar">
        <input v-model="searchQuery" @keyup.enter="searchAddress" placeholder="Zoek een adres..." />
        <button @click="searchAddress" aria-label="Search Address">
          <i class="fas fa-search"></i>
        </button>
      </div>

      <div class="loading-screen" v-if="isMapLoading">
        Observaties laden...
      </div>
      <div class="loading-screen" v-if="isExporting">
        Exporteren...
      </div>

      <div class="map-legend" v-if="map && !isMapLoading">
        <div><span class="legend-icon bg-reported"></span> Gerapporteerd nest</div>
        <div><span class="legend-icon bg-reserved"></span> Gereserveerd nest</div>
        <div><span class="legend-icon bg-eradicated"></span> Bestreden nest</div>
        <div><span class="legend-icon bg-visited"></span> Bezocht nest</div>
      </div>

      <button class="btn-fab btn-filter-toggle" @click="toggleFilterPanel" aria-label="Toggle Filters">
        <i class="fas fa-sliders-h"></i>
      </button>

      <div class="panel-overlay" 
           :class="{ 'is-active': isFilterPaneOpen || isDetailsPaneOpen }" 
           @click="closePanels">
      </div>

      <div class="side-panel filter-panel" :class="{ 'is-open': isFilterPaneOpen }">
        <div class="panel-header">
            <h3 class="panel-title">Filters</h3>
            <button type="button" class="btn-close" aria-label="Close" @click="toggleFilterPanel"></button>
        </div>
        <div class="panel-content">
          <FilterComponent />
        </div>
      </div>

      <div class="side-panel details-panel" :class="{ 'is-open': isDetailsPaneOpen }">
        <ObservationDetailsComponent @updateMarkerColor="updateMarkerColor" @close-panel="toggleDetailsPane" />
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
    const isDetailsPaneOpen = computed(() => vespaStore.isDetailsPaneOpen);
    const isFilterPaneOpen = ref(false);
    const error = computed(() => vespaStore.error);
    const isMapLoading = ref(true);
    const isFetchingGeoJson = ref(false);

    const searchAddress = async () => {
      if (searchQuery.value) {
        try {
          const result = await vespaStore.searchAddress(searchQuery.value);
          if (result) {
            map.value.setView([result.lat, result.lon], 16);
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

    const toggleDetailsPane = () => {
      vespaStore.isDetailsPaneOpen = !vespaStore.isDetailsPaneOpen;
      if (!vespaStore.isDetailsPaneOpen) {
        if(selectedObservation.value) {
           vespaStore.refreshMarkerStyle(selectedObservation.value.id);
        }
        vespaStore.selectedObservation = null;
        router.push({ path: '/' });
      }
    };

    const toggleFilterPanel = () => {
      isFilterPaneOpen.value = !isFilterPaneOpen.value;
    };
    
    const closePanels = () => {
        if (isFilterPaneOpen.value) {
            toggleFilterPanel();
        }
        if (isDetailsPaneOpen.value) {
            toggleDetailsPane();
        }
    };

    const openObservationDetails = async (properties) => {
      try {
        await vespaStore.fetchObservationDetails(properties.id);
        if (vespaStore.selectedObservation && !vespaStore.selectedObservation.visible) {
          return;
        }
        vespaStore.isDetailsPaneOpen = true;
        if (window.innerWidth < 768 && isFilterPaneOpen.value) {
            isFilterPaneOpen.value = false;
        }
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

            const observations = vespaStore.observations || [];
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
                if (!vespaStore.markerCache[id]) {
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
                         existingMarker.feature = feature;
                         vespaStore.refreshMarkerStyle(id);
                    }
                }
            });

            if (newMarkers.length > 0) {
                vespaStore.markerClusterGroup.addLayers(newMarkers);
            }
            
            if (selectedObservation.value) {
                vespaStore.refreshMarkerStyle(selectedObservation.value.id);
            }

        } catch (error) {
            console.error('Error updating markers:', error);
            vespaStore.error = "Fout bij het bijwerken van de kaartobservaties.";
        } finally {
            isFetchingGeoJson.value = false;
            isMapLoading.value = false;
        }
    }, 600);

    watch(selectedObservation, (newObs, oldObs) => {
        if (oldObs && (!newObs || newObs.id !== oldObs.id)) {
            vespaStore.refreshMarkerStyle(oldObs.id);
        }
        if (newObs) {
            nextTick(() => {
                vespaStore.refreshMarkerStyle(newObs.id);
            });
        }
    }, { deep: true });

    const updateMarkerColor = (observationId) => {
        if (observationId) {
          vespaStore.refreshMarkerStyle(observationId);
        }
    };

    watch(() => vespaStore.filters, () => {
        updateMarkers();
    }, { deep: true });

    watch(() => router.currentRoute.value, (newRoute, oldRoute) => {
        if (newRoute.path !== oldRoute.path && !newRoute.path.includes('/observation/')) {
          if(vespaStore.isDetailsPaneOpen) {
            vespaStore.isDetailsPaneOpen = false;
          }
        }
    });

    onMounted(async () => {
      if (!vespaStore.markerCache) {
        vespaStore.markerCache = {};
      }

      map.value = L.map('map', {
        center: [50.8503, 4.3517],
        zoom: 9,
        maxZoom: 19,
        zoomControl: false, 
        renderer: L.svg(),
      });
      
      L.control.zoom({ position: 'topleft' }).addTo(map.value);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map.value);

      vespaStore.map = map.value;

      vespaStore.markerClusterGroup = L.markerClusterGroup({
        spiderfyOnMaxZoom: false,
        showCoverageOnHover: true,
        zoomToBoundsOnClick: true,
        disableClusteringAtZoom: 16,
        iconCreateFunction: (cluster) => L.divIcon({
          html: `<div class="cluster-icon"><span>${cluster.getChildCount()}</span></div>`,
          className: 'marker-cluster',
          iconSize: L.point(40, 40),
        }),
      });

      map.value.addLayer(vespaStore.markerClusterGroup);

      await vespaStore.initializeApp();
      
      if (!vespaStore.filters.min_observation_date) {
          vespaStore.applyFilters({
              min_observation_date: new Date('2024-04-01T00:00:00.000Z').toISOString(),
          });
      }
      
      const observationIdParam = router.currentRoute.value.params.id;
      if (observationIdParam) {
        isMapLoading.value = true;
        await updateMarkers();
        try {
            await vespaStore.fetchObservationDetails(observationIdParam);
            if (vespaStore.selectedObservation) {
                vespaStore.isDetailsPaneOpen = true;
                const obsLocation = vespaStore.selectedObservation.location;
                if (obsLocation?.coordinates) {
                    map.value.setView([obsLocation.coordinates[1], obsLocation.coordinates[0]], 16);
                }
            } else {
                 router.push({ path: '/' });
            }
        } catch (error) {
            console.error("Failed to load observation for direct navigation:", error);
            vespaStore.error = "Kon de geselecteerde observatie niet laden.";
            router.push({ path: '/' });
        } finally {
             isMapLoading.value = false;
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
      closePanels,
      selectedObservation,
      isEditing,
      map,
      formattedError,
      isMapLoading,
      updateMarkerColor,
      searchQuery,
      searchAddress,
      isExporting,
    };
  },
};
</script>