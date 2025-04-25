<template>
    <div class="date-filter-wrapper">
      <div class="date-filter-container">
        <div class="date-input-group">
          <label class="filter-label">Observaties vanaf</label>
          <div class="date-picker-wrapper">
            <VueDatePicker
              v-model="minDate"
              :enable-time-picker="false"
              format="yyyy-MM-dd"
              placeholder="Selecteer startdatum"
              class="date-picker"
              :max-date="maxDate"
              @update:model-value="emitFilterUpdate"
              @clear="emitFilterUpdate"
            />
            <button v-if="minDate" class="clear-button" @click="clearMinDate" aria-label="Clear start date">
              <span class="clear-icon">×</span>
            </button>
          </div>
        </div>
        <div class="date-input-group">
          <label class="filter-label">Observaties tot</label>
          <div class="date-picker-wrapper">
            <VueDatePicker
              v-model="maxDate"
              :enable-time-picker="false"
              format="yyyy-MM-dd"
              placeholder="Selecteer einddatum"
              class="date-picker"
              :min-date="minDate"
              @update:model-value="emitFilterUpdate"
              @clear="emitFilterUpdate"
            />
            <button v-if="maxDate" class="clear-button" @click="clearMaxDate" aria-label="Clear end date">
              <span class="clear-icon">×</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { useVespaStore } from '@/stores/vespaStore';
  import debounce from 'lodash/debounce';
  import { onMounted, ref, watch } from 'vue';
  import VueDatePicker from '@vuepic/vue-datepicker';
  import '@vuepic/vue-datepicker/dist/main.css';
  
  export default {
    components: {
      VueDatePicker,
    },
    setup() {
      const vespaStore = useVespaStore();
  
      // Initialiseer startdatum op 1 april 2024 in plaats van vandaag
      const defaultDate = new Date(2024, 3, 1); // Merk op: maanden zijn 0-indexed, dus 3 = april
      const minDate = ref(defaultDate);
      const maxDate = ref(null); // Einddatum blijft initieel null
  
      // Emit filter updates with debouncing
      const emitFilterUpdate = debounce(() => {
        vespaStore.applyFilters({
          ...vespaStore.filters,
          min_observation_date: minDate.value ? minDate.value.toISOString() : null,
          max_observation_date: maxDate.value ? maxDate.value.toISOString() : null,
        });
      }, 300);
  
      // Clear functions for the date inputs
      const clearMinDate = () => {
        minDate.value = null;
        emitFilterUpdate();
      };
  
      const clearMaxDate = () => {
        maxDate.value = null;
        emitFilterUpdate();
      };
  
      // Watch for store filter changes to sync component state
      watch(
        () => vespaStore.filters,
        (newFilters) => {
          minDate.value = newFilters.min_observation_date
            ? new Date(newFilters.min_observation_date)
            : defaultDate; // Standaard naar 1 april 2024 als er geen waarde is
          maxDate.value = newFilters.max_observation_date
            ? new Date(newFilters.max_observation_date)
            : null;
        },
        { immediate: true, deep: true }
      );
  
      // Initialize filters on mount
      onMounted(() => {
        minDate.value = vespaStore.filters.min_observation_date
          ? new Date(vespaStore.filters.min_observation_date)
          : defaultDate; // Standaard naar 1 april 2024
        maxDate.value = vespaStore.filters.max_observation_date
          ? new Date(vespaStore.filters.max_observation_date)
          : null;
      });
  
      return {
        minDate,
        maxDate,
        emitFilterUpdate,
        clearMinDate,
        clearMaxDate,
      };
    },
  };
  </script>
  
  <style scoped>
  .date-filter-wrapper {
    margin-bottom: 20px;
    background-color: transparent;
    width: 100%;
  }
  
  .date-filter-header {
    font-size: 16px;
    font-weight: 600;
    color: #333;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding-bottom: 8px;
  }
  
  .date-filter-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .date-input-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .filter-label {
    font-size: 14px;
    font-weight: 400;
    color: #555;
    margin-bottom: 2px;
  }
  
  .date-picker-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }
  
  .date-picker {
    width: 100%;
  }
  
  /* Customize vue3-datepicker styles to match the screenshot */
  :deep(.dp__input) {
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 14px;
    color: #333;
    background-color: #f8f9fa;
    transition: all 0.2s ease;
    width: 100%;
    box-sizing: border-box;
  }
  
  /* Verberg het kalendericoontje */
  :deep(.dp__input_icon) {
    display: none !important;
  }
  
  :deep(.dp__input:hover) {
    background-color: #fff;
  }
  
  :deep(.dp__input:focus) {
    border-color: #007bff;
    background-color: #fff;
    outline: none;
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
  }
  
  :deep(.dp__input::placeholder) {
    color: #6c757d;
  }
  
  :deep(.dp__calendar) {
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    border: 1px solid #e9ecef;
  }
  
  :deep(.dp__calendar_header) {
    padding: 8px 0;
  }
  
  :deep(.dp__calendar_item) {
    font-size: 14px;
    border-radius: 4px;
    transition: background-color 0.2s ease;
  }
  
  :deep(.dp__calendar_item:hover) {
    background-color: #f3f4f6;
  }
  
  :deep(.dp__today) {
    border: 1px solid #007bff;
    font-weight: 600;
  }
  
  :deep(.dp__active_date) {
    background-color: #007bff;
    color: #fff;
    font-weight: 600;
  }
  
  :deep(.dp__calendar_header_item) {
    font-weight: 600;
    color: #4b5563;
    text-transform: uppercase;
    font-size: 12px;
  }
  
  :deep(.dp__month_year_select) {
    border-radius: 4px;
  }
  
  :deep(.dp__overlay_cell_active) {
    background-color: #007bff;
    color: white;
  }
  
  /* Clear button styles to match the screenshot */
  .clear-button {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background-color: transparent;
    border: none;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    padding: 0;
    z-index: 1;
  }
  
  .clear-icon {
    font-size: 18px;
    color: #6c757d;
    line-height: 1;
  }
  
  .clear-button:hover .clear-icon {
    color: #343a40;
  }
  
  /* Responsive adjustments */
  @media (min-width: 768px) {
    .date-filter-container {
      flex-direction: row;
      gap: 16px;
    }
    
    .date-input-group {
      flex: 1;
    }
  }
  </style>