<template>
  <div class="d-flex flex-column vh-100">
    <NavbarComponent />
    <div class="flex-grow-1 position-relative">
      <button class="btn-filter-toggle" @click="toggleFilterPanel">
        <i class="fas fa-sliders-h"></i> Filters
      </button>
      <div id="map" class="h-100"></div>
      <div class="map-legend" v-if="map">
        <div>
          <span class="legend-icon bg-green"></span> Bestreden
        </div>
        <div>
          <span class="legend-icon bg-grey"></span> Gereserveerd
        </div>
        <div>
          <span class="legend-icon bg-orange"></span> Standaard
        </div>
      </div>
      <div class="filter-panel"
        :class="{ 'd-none': !isFilterPaneOpen, 'd-block': isFilterPaneOpen, 'col-12': true, 'col-md-6': true, 'col-lg-4': true }">
        <FilterComponent />
      </div>
      <div class="details-panel"
        :class="{ 'd-none': !isDetailsPaneOpen, 'd-block': isDetailsPaneOpen, 'col-12': true, 'col-md-6': true, 'col-lg-4': true }">
        <ObservationDetailsComponent />
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
    const router = useRouter();
    const selectedObservation = computed(() => vespaStore.selectedObservation);
    const isEditing = computed(() => vespaStore.isEditing);
    const map = ref(null);
    const isLoggedIn = computed(() => vespaStore.isLoggedIn);
    const isDetailsPaneOpen = computed(() => vespaStore.isDetailsPaneOpen);
    const isFilterPaneOpen = ref(false);
    const error = computed(() => vespaStore.error);

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
        vespaStore.isDetailsPaneOpen = true;
        router.push({ path: `/map/observation/${properties.id}` });
      } catch (error) {
        console.error("Failed to fetch observation details:", error);
      }
    };

    const updateMarkers = () => {
      vespaStore.getObservationsGeoJson().then((geoJson) => {
        const geoJsonLayer = L.geoJSON(vespaStore.observations, {
          pointToLayer: (feature, latlng) => {
            const marker = vespaStore.createCircleMarker(feature, latlng);
            marker.on('click', () => openObservationDetails(feature.properties));
            return marker;
          },
        });
        vespaStore.markerClusterGroup.clearLayers();
        vespaStore.markerClusterGroup.addLayer(geoJsonLayer);
        map.value.addLayer(vespaStore.markerClusterGroup);
      });
    };

    const clearAndUpdateMarkers = () => {
      if (vespaStore.markerClusterGroup) {
        vespaStore.markerClusterGroup.clearLayers();
      }
      vespaStore.observations = [];
      updateMarkers();
    };

    watch(
      () => vespaStore.filters,
      (newFilters) => {
        clearAndUpdateMarkers();
      },
      { deep: true }
    );

    onMounted(async () => {
      vespaStore.markerClusterGroup = L.markerClusterGroup({
        spiderfyOnMaxZoom: false,
        showCoverageOnHover: true,
        zoomToBoundsOnClick: true,
        disableClusteringAtZoom: 16,
        iconCreateFunction: (cluster) => {
          return L.divIcon({
            html: `<div style="background-color: rgba(153,72,0,0.5);"><span>${cluster.getChildCount()}</span></div>`,
            className: 'marker-cluster',
            iconSize: L.point(40, 40),
          });
        },
      });
      const observationId = router.currentRoute.value.params.id;

      if (observationId) {
        await vespaStore.fetchObservationDetails(observationId);
        const location = selectedObservation.value.location;
        const [longitude, latitude] = location
          .slice(location.indexOf('(') + 1, location.indexOf(')'))
          .split(' ')
          .map(parseFloat);

        map.value = L.map('map', {
          center: [latitude, longitude],
          zoom: 16,
          maxZoom: 20,
          layers: [
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: 'Map data © OpenStreetMap contributors',
            }),
          ],
        });
      } else {
        map.value = L.map('map', {
          center: [50.8503, 4.3517],
          zoom: 9,
          maxZoom: 20,
          layers: [
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: 'Map data © OpenStreetMap contributors',
            }),
          ],
        });
      }

      vespaStore.map = map.value;
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
    };
  },
};
</script>

<style scoped>
.map-legend {
  font-family: Arial, sans-serif;
  font-size: 14px;
  background: white;
  padding: 10px;
  border-radius: 5px;
  position: absolute;
  bottom: 10px;
  left: 10px;
  z-index: 1000;
}

.legend-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-right: 8px;
  border-radius: 50%;
  vertical-align: middle;
}

.bg-green {
  background-color: green;
}

.bg-grey {
  background-color: grey;
}

.bg-orange {
  background-color: orange;
}
</style>
