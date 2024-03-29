<template>
    <div class="d-flex flex-column vh-100">
      <NavbarComponent />
  
      <!-- Toggle Button for Filters -->
      <button class="btn-filter-toggle" @click="toggleFilterPane">
        <i class="fas fa-sliders-h"></i> Filters
      </button>
  
      <!-- Filters Side Panel -->
      <div class="filter-panel" :class="{ 'panel-active': isFilterPaneOpen }">
        <FilterComponent @updateFilters="updateFilters" />
      </div>
  
      <div class="flex-grow-1 position-relative">
        <div id="mapid" class="h-100"></div>
        <div id="details" class="details-panel" v-if="selectedObservation">
          <h3>Observation Details</h3>
          <!-- Observation details content -->
        </div>
      </div>
  
      <FooterComponent></FooterComponent>
    </div>
  </template>
  
  <script>
  import { useVespaStore } from '@/stores/vespaStore';
import 'leaflet/dist/leaflet.css';
import { computed, onMounted, ref } from 'vue';
import FilterComponent from './FilterComponent.vue';
import FooterComponent from './FooterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';
  
  export default {
    components: {
      NavbarComponent,
      FooterComponent,
      FilterComponent
    },
    setup() {
      const vespaStore = useVespaStore();
      const isFilterPaneOpen = ref(false);
      
      const selectedObservation = computed(() => vespaStore.selectedObservation);
      const isLoggedIn = computed(() => vespaStore.isLoggedIn);
  
      const toggleFilterPane = () => {
        isFilterPaneOpen.value = !isFilterPaneOpen.value;
      };
  
      const updateFilters = (newFilters) => {
        // Handle the update filters event
      };
  
      onMounted(async () => {
        // Any additional logic to run on component mount
      });
  
      return {
        isFilterPaneOpen,
        toggleFilterPane,
        updateFilters,
        selectedObservation,
        isLoggedIn,
        // any other properties or methods
      };
    }
  };
  </script>
  
  <style>
  .btn-filter-toggle {
    position: absolute;
    top: 1rem;
    left: 1rem;
    z-index: 1050; /* above leaflet's z-index */
    background-color: #fff;
    color: #333;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.25rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    cursor: pointer;
  }
  
  .filter-panel {
    position: fixed;
    top: 0;
    right: -100%;
    width: 300px;
    height: 100%;
    background: #fff;
    transition: right 0.3s;
    z-index: 1050;
    overflow-y: auto;
    padding: 1rem;
    box-shadow: -2px 0 5px rgba(0, 0, 0, 0.3);
  }
  
  .filter-panel.panel-active {
    right: 0;
  }
  
  #mapid {
    width: 100%;
    /* Adjust height if necessary */
  }
  
  .details-panel {
    position: absolute;
    top: 0;
    right: 0;
    width: 300px;
    height: 100%;
    background: #fff;
    overflow-y: auto;
    border-left: 1px solid #ddd;
    padding: 1rem;
    box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
  }
  </style>
  