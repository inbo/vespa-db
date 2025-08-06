<template>
  <div class="date-filter-container">
    <!-- Min Date Filter -->
    <div class="mb-2">
      <label class="form-label" for="min-date-picker">Observaties vanaf</label>
      <div class="date-input-wrapper">
        <input
          id="min-date-picker"
          type="date"
          class="form-control"
          v-model="minDateString"
          :min="absoluteMinDateString"
          :max="maxDateString"
          @change="handleMinDateChange"
        />
        <button 
          v-if="minDateString && minDateString !== defaultMinDateString" 
          class="clear-button" 
          @click="clearMinDate" 
          aria-label="Clear start date"
          type="button"
        >
          <span class="clear-icon">×</span>
        </button>
      </div>
    </div>

    <!-- Max Date Filter -->
    <div>
      <label class="form-label" for="max-date-picker">Observaties tot</label>
      <div class="date-input-wrapper">
        <input
          id="max-date-picker"
          type="date"
          class="form-control"
          v-model="maxDateString"
          :min="minDateForMaxPickerString"
          @change="handleMaxDateChange"
        />
        <button 
          v-if="maxDateString" 
          class="clear-button" 
          @click="clearMaxDate" 
          aria-label="Clear end date"
          type="button"
        >
          <span class="clear-icon">×</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import debounce from 'lodash/debounce';
import { computed, onMounted, ref, watch } from 'vue';

export default {
  setup() {
    const vespaStore = useVespaStore();

    // Initialize default date to April 1, 2025 (updated to match resetFilters)
    const defaultDate = new Date(2025, 3, 1); // Months are 0-indexed, so 3 = April
    const absoluteMinDate = new Date(2025, 3, 1); // Minimum allowed date for both pickers
    const minDate = ref(defaultDate);
    const maxDate = ref(null); // End date remains initially null

    // Helper function to convert Date object to YYYY-MM-DD string
    const dateToString = (date) => {
      if (!date) return '';
      try {
        return date.toISOString().split('T')[0];
      } catch (e) {
        return '';
      }
    };

    // Helper function to convert YYYY-MM-DD string to Date object
    const stringToDate = (dateString) => {
      if (!dateString) return null;
      try {
        return new Date(dateString + 'T00:00:00.000Z');
      } catch (e) {
        return null;
      }
    };

    // Helper function to convert ISO string (from store) to YYYY-MM-DD string
    const isoToDateString = (isoString) => {
      if (!isoString) return '';
      try {
        return new Date(isoString).toISOString().split('T')[0];
      } catch (e) {
        return '';
      }
    };

    // Computed properties for string representations (for input binding)
    const minDateString = ref(dateToString(defaultDate));
    const maxDateString = ref('');
    const absoluteMinDateString = computed(() => dateToString(absoluteMinDate));
    const defaultMinDateString = computed(() => dateToString(defaultDate));

    // Computed property for the minimum date of the maxDate picker
    const minDateForMaxPickerString = computed(() => {
      if (minDate.value && minDate.value > absoluteMinDate) {
        return dateToString(minDate.value);
      }
      return dateToString(absoluteMinDate);
    });

    // Emit filter updates with debouncing (same timing as original)
    const emitFilterUpdate = debounce(() => {
      vespaStore.applyFilters({
        ...vespaStore.filters,
        min_observation_date: minDate.value ? minDate.value.toISOString() : null,
        max_observation_date: maxDate.value ? maxDate.value.toISOString() : null,
      });
    }, 300);

    // Handle min date changes from input
    const handleMinDateChange = () => {
      const newDate = stringToDate(minDateString.value);
      minDate.value = newDate || defaultDate; // Fall back to default if invalid
      
      // If max date is now before min date, clear it
      if (maxDate.value && newDate && maxDate.value < newDate) {
        maxDate.value = null;
        maxDateString.value = '';
      }
      
      emitFilterUpdate();
    };

    // Handle max date changes from input
    const handleMaxDateChange = () => {
      maxDate.value = stringToDate(maxDateString.value);
      emitFilterUpdate();
    };

    // Clear functions with same logic as original
    const clearMinDate = () => {
      minDate.value = defaultDate; // Reset to default date (April 1, 2025)
      minDateString.value = dateToString(defaultDate);
      emitFilterUpdate();
    };

    const clearMaxDate = () => {
      maxDate.value = null;
      maxDateString.value = '';
      emitFilterUpdate();
    };

    // Watch for store filter changes to sync component state (same as original)
    watch(
      () => vespaStore.filters,
      (newFilters) => {
        const newMinDate = newFilters.min_observation_date
          ? new Date(newFilters.min_observation_date)
          : defaultDate; // Default to April 1, 2025 if no value
        const newMaxDate = newFilters.max_observation_date
          ? new Date(newFilters.max_observation_date)
          : null;

        minDate.value = newMinDate;
        maxDate.value = newMaxDate;
        minDateString.value = dateToString(newMinDate);
        maxDateString.value = dateToString(newMaxDate);
      },
      { immediate: true, deep: true }
    );

    // Initialize filters on mount (same as original)
    onMounted(() => {
      const initialMinDate = vespaStore.filters.min_observation_date
        ? new Date(vespaStore.filters.min_observation_date)
        : defaultDate; // Default to April 1, 2025
      const initialMaxDate = vespaStore.filters.max_observation_date
        ? new Date(vespaStore.filters.max_observation_date)
        : null;

      minDate.value = initialMinDate;
      maxDate.value = initialMaxDate;
      minDateString.value = dateToString(initialMinDate);
      maxDateString.value = dateToString(initialMaxDate);
    });

    return {
      minDateString,
      maxDateString,
      absoluteMinDateString,
      defaultMinDateString,
      minDateForMaxPickerString,
      handleMinDateChange,
      handleMaxDateChange,
      clearMinDate,
      clearMaxDate,
    };
  },
};
</script>

<style scoped>
.date-filter-container .form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #495057;
  margin-bottom: 0.25rem;
}

.date-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

/* Native date input styling to match other form controls */
.form-control[type="date"] {
  min-height: 38px;
  -webkit-appearance: none;
  appearance: none;
  background-color: #f8f9fa;
  border: 1px solid #ced4da;
  border-radius: 4px;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  color: #495057;
  line-height: 1.5;
  transition: all 0.2s ease;
  width: 100%;
  box-sizing: border-box;
}

.form-control[type="date"]:hover {
  background-color: #fff;
  border-color: #adb5bd;
}

.form-control[type="date"]:focus {
  background-color: #fff;
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* Clear button styles (same as original) */
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

/* Style the date picker calendar icon on webkit browsers */
.form-control[type="date"]::-webkit-calendar-picker-indicator {
  color: #6c757d;
  cursor: pointer;
  margin-right: 25px; /* Make room for clear button */
}

.form-control[type="date"]::-webkit-calendar-picker-indicator:hover {
  color: #495057;
}

/* Firefox date input styling */
.form-control[type="date"]::-moz-focus-inner {
  border: 0;
}
</style>