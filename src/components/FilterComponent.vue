<template>
  <div class="filters-container">
    <div class="container-fluid px-0">
      <div class="row g-3 mx-0">
        <!-- <div class="col-12">
          <h3 class="filters-heading">Filters</h3>
        </div> -->

        <!-- Provinces Filter -->
        <div class="col-12">
          <label class="form-label">Provincie(s)</label>
          <multiselect
            v-model="selectedProvinces"
            :options="provinceOptions"
            :multiple="true"
            track-by="value"
            label="title"
            placeholder="Selecteer provincie(s)"
            :close-on-select="false"
            :searchable="true"
            :disabled="!provinces.length"
            :select-label="''"
            :deselect-label="''"
            :selected-label="''"
            @input="emitFilterUpdate"
          >
            <template #option="{ option }">
              <div class="multiselect-option" :class="{ 'is-selected': selectedProvinces.some(p => p.value === option.value) }">
                <span class="option-label">{{ option.title }}</span>
              </div>
            </template>
            <template #tag="{ option, remove }">
              <span class="multiselect-tag">
                {{ option.title }}
                <button 
                  type="button" 
                  class="remove-tag" 
                  @click="remove(option)"
                  aria-label="Remove option"
                >×</button>
              </span>
            </template>
          </multiselect>
        </div>

        <!-- Municipalities Filter -->
        <div class="col-12">
          <label class="form-label">Gemeente(s)</label>
          <multiselect
            v-model="selectedMunicipalities"
            :options="municipalityOptions"
            :multiple="true"
            track-by="value"
            label="title"
            placeholder="Selecteer gemeente(s)"
            :close-on-select="false"
            :searchable="true"
            :disabled="!municipalities.length"
            :select-label="''"
            :deselect-label="''"
            :selected-label="''"
            @input="emitFilterUpdate"
          >
            <template #option="{ option }">
              <div class="multiselect-option" :class="{ 'is-selected': selectedMunicipalities.some(m => m.value === option.value) }">
                <span class="option-label">{{ option.title }}</span>
              </div>
            </template>
            <template #tag="{ option, remove }">
              <span class="multiselect-tag">
                {{ option.title }}
                <button 
                  type="button" 
                  class="remove-tag" 
                  @click="remove(option)"
                  aria-label="Remove option"
                >×</button>
              </span>
            </template>
          </multiselect>
        </div>

        <!-- Date Filter -->
        <div class="col-12">
          <DateFilter />
        </div>

        <!-- Nest Type Filter -->
        <div class="col-12">
          <label class="form-label">Nest type</label>
          <multiselect
            v-model="selectedNestType"
            :options="nestTypeOptions"
            :multiple="true"
            track-by="value"
            label="title"
            placeholder="Selecteer nest type(s)"
            :close-on-select="false"
            :searchable="false"
            :select-label="''"
            :deselect-label="''"
            :selected-label="''"
            @input="emitFilterUpdate"
          >
            <template #option="{ option }">
              <div class="multiselect-option" :class="{ 'is-selected': selectedNestType.some(n => n.value === option.value) }">
                <span class="option-label">{{ option.title }}</span>
              </div>
            </template>
            <template #tag="{ option, remove }">
              <span class="multiselect-tag">
                {{ option.title }}
                <button 
                  type="button" 
                  class="remove-tag" 
                  @click="remove(option)"
                  aria-label="Remove option"
                >×</button>
              </span>
            </template>
          </multiselect>
        </div>

        <!-- Nest Status Filter -->
        <div class="col-12">
          <label class="form-label">Nest status</label>
          <multiselect
            v-model="selectedNestStatus"
            :options="nestStatusOptions"
            :multiple="true"
            track-by="value"
            label="title"
            placeholder="Selecteer nest status(sen)"
            :close-on-select="false"
            :searchable="false"
            :select-label="''"
            :deselect-label="''"
            :selected-label="''"
            @input="emitFilterUpdate"
          >
            <template #option="{ option }">
              <div class="multiselect-option" :class="{ 'is-selected': selectedNestStatus.some(s => s.value === option.value) }">
                <span class="option-label">{{ option.title }}</span>
              </div>
            </template>
            <template #tag="{ option, remove }">
              <span class="multiselect-tag">
                {{ option.title }}
                <button 
                  type="button" 
                  class="remove-tag" 
                  @click="remove(option)"
                  aria-label="Remove option"
                >×</button>
              </span>
            </template>
          </multiselect>
        </div>

        <!-- ANB Areas Filter -->
        <div class="col-12">
          <label class="form-label">ANB</label>
          <select v-model="anbAreasActief" class="form-select" @change="emitFilterUpdate">
            <option :value="null">Alle gebieden</option>
            <option v-for="option in anbAreaOptions" :key="option.value" :value="option.value">
              {{ option.name }}
            </option>
          </select>
        </div>

        <!-- Reset Filters Button -->
        <div class="col-12 mt-4" v-if="hasActiveFilters">
          <button 
            type="button" 
            class="btn btn-outline-secondary w-100 reset-filters-btn"
            @click="resetAllFilters"
          >
            Verwijder alle filters
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import debounce from 'lodash/debounce';
import { computed, onMounted, ref, watch } from 'vue';
import DateFilter from '@/components/DateFilter.vue';
import Multiselect from 'vue-multiselect';
import 'vue-multiselect/dist/vue-multiselect.min.css';

export default {
  components: {
    DateFilter,
    Multiselect,
  },
  setup() {
    const vespaStore = useVespaStore();

    const loading = computed(() => vespaStore.loadingObservations);
    const municipalities = computed(() => vespaStore.municipalities);
    const provinces = computed(() => vespaStore.provinces);
    
    const selectedMunicipalities = ref([]);
    const selectedProvinces = ref([]);
    const selectedNestType = ref([]);
    const selectedNestStatus = ref([]);
    const anbAreasActief = ref(null);

    // Convert data to multiselect format
    const provinceOptions = computed(() => 
      provinces.value.length
        ? provinces.value.map((province) => ({
            title: province.name,
            value: province.id,
          }))
        : []
    );

    const municipalityOptions = computed(() => 
      municipalities.value.length
        ? municipalities.value.map((municipality) => ({
            title: municipality.name,
            value: municipality.id,
          }))
        : []
    );

    const nestTypeOptions = computed(() => [
      { title: 'Actief embryonaal nest', value: 'actief_embryonaal_nest' },
      { title: 'Actief primair nest', value: 'actief_primair_nest' },
      { title: 'Actief secundair nest', value: 'actief_secundair_nest' },
      { title: 'Inactief/leeg nest', value: 'inactief_leeg_nest' },
    ]);

    const nestStatusOptions = computed(() => [
      { title: "Bezocht nest", value: 'visited' },
      { title: 'Bestreden nest', value: 'eradicated' },
      { title: 'Gereserveerd nest', value: 'reserved' },
      { title: 'Gerapporteerd nest', value: 'open' },
    ]);

    const anbAreaOptions = ref([
      { name: 'Niet in ANB gebied', value: false },
      { name: 'Wel in ANB gebied', value: true },
    ]);

    // Check if any filters are active (excluding the default min_observation_date of 2024-04-01)
    const hasActiveFilters = computed(() => {
      const filters = vespaStore.filters;
      const defaultMinDate = '2024-04-01';
      return (
        (filters.provinces && filters.provinces.length > 0) ||
        (filters.municipalities && filters.municipalities.length > 0) ||
        (filters.nestType && filters.nestType.length > 0) ||
        (filters.nestStatus && filters.nestStatus.length > 0) ||
        (filters.anbAreasActief !== null && filters.anbAreasActief !== undefined) ||
        (filters.max_observation_date && filters.max_observation_date !== null) ||
        (filters.min_observation_date && filters.min_observation_date !== defaultMinDate)
        // Note: We include min_observation_date if it differs from the default 2024-04-01
      );
    });

    const emitFilterUpdate = debounce(() => {
      vespaStore.applyFilters({
        municipalities:
          selectedMunicipalities.value.length > 0
            ? selectedMunicipalities.value.map(m => m.value)
            : [],
        provinces:
          selectedProvinces.value.length > 0 
            ? selectedProvinces.value.map(p => p.value) 
            : [],
        anbAreasActief: anbAreasActief.value,
        nestType:
          selectedNestType.value.length > 0 
            ? selectedNestType.value.map(n => n.value) 
            : null,
        nestStatus:
          selectedNestStatus.value.length > 0 
            ? selectedNestStatus.value.map(s => s.value) 
            : null,
        // min_observation_date and max_observation_date are handled by DateFilter component
      });
    }, 300);

    const resetAllFilters = () => {
      // Reset local component state
      selectedMunicipalities.value = [];
      selectedProvinces.value = [];
      selectedNestType.value = [];
      selectedNestStatus.value = [];
      anbAreasActief.value = null;
      
      // Set the standard min_observation_date to 2024-04-01
      const standardMinDate = '2024-04-01';
      
      // Reset filters in store with the standard min_observation_date
      vespaStore.resetFilters({
        min_observation_date: standardMinDate
      });
      
      // Refresh municipalities list since provinces were cleared
      vespaStore.fetchMunicipalities();
    };

    const fetchMunicipalitiesByProvinces = async () => {
      if (selectedProvinces.value.length > 0) {
        await vespaStore.fetchMunicipalitiesByProvinces(selectedProvinces.value.map(p => p.value));
      } else {
        await vespaStore.fetchMunicipalities();
      }
    };

    watch(
      [selectedMunicipalities, selectedNestType, selectedNestStatus, anbAreasActief],
      () => {
        emitFilterUpdate();
      },
      { deep: true }
    );

    watch(selectedProvinces, (newProvinces, oldProvinces) => {
      if (JSON.stringify(newProvinces) === JSON.stringify(oldProvinces)) {
        return;
      }
      selectedMunicipalities.value = [];
      fetchMunicipalitiesByProvinces();
      emitFilterUpdate();
    }, { deep: true });


    // Watch store filters for changes from other components
    watch(
      () => vespaStore.filters,
      (newFilters, oldFilters) => {
        const hasChanged = JSON.stringify(newFilters) !== JSON.stringify(oldFilters);

        if (hasChanged) {
          // Convert array values back to multiselect format
          selectedMunicipalities.value = (newFilters.municipalities || []).map(id => 
            municipalityOptions.value.find(m => m.value === id)
          ).filter(Boolean);
          
          selectedProvinces.value = (newFilters.provinces || []).map(id => 
            provinceOptions.value.find(p => p.value === id)
          ).filter(Boolean);
          
          selectedNestType.value = (newFilters.nestType || []).map(value => 
            nestTypeOptions.value.find(n => n.value === value)
          ).filter(Boolean);
          
          selectedNestStatus.value = (newFilters.nestStatus || []).map(value => 
            nestStatusOptions.value.find(s => s.value === value)
          ).filter(Boolean);
          
          anbAreasActief.value = newFilters.anbAreasActief ?? null;
        }
      },
      { immediate: true, deep: true }
    );

    onMounted(async () => {
      // Initialize from store filters
      const filters = vespaStore.filters;
      
      selectedMunicipalities.value = (filters.municipalities || []).map(id => 
        municipalityOptions.value.find(m => m.value === id)
      ).filter(Boolean);
      
      selectedProvinces.value = (filters.provinces || []).map(id => 
        provinceOptions.value.find(p => p.value === id)
      ).filter(Boolean);
      
      selectedNestType.value = (filters.nestType || []).map(value => 
        nestTypeOptions.value.find(n => n.value === value)
      ).filter(Boolean);
      
      selectedNestStatus.value = (filters.nestStatus || []).map(value => 
        nestStatusOptions.value.find(s => s.value === value)
      ).filter(Boolean);
      
      anbAreasActief.value = filters.anbAreasActief;
    });

    return {
      municipalities,
      provinces,
      loading,
      provinceOptions,
      municipalityOptions,
      nestTypeOptions,
      nestStatusOptions,
      anbAreaOptions,
      selectedMunicipalities,
      selectedProvinces,
      selectedNestType,
      selectedNestStatus,
      anbAreasActief,
      hasActiveFilters,
      emitFilterUpdate,
      resetAllFilters,
    };
  },
};
</script>

<style scoped>
.filters-container {
  background-color: #fff;
  height: 100%;
  overflow-y: auto;
}

.filters-heading {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e9ecef;
}

/* Form styling */
.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #495057;
  margin-bottom: 0.25rem;
}

.form-select {
  font-size: 0.875rem;
  background-color: #f8f9fa;
  border: 1px solid #ced4da;
  border-radius: 4px;
  padding: 0.375rem 2.25rem 0.375rem 0.75rem;
  color: #495057;
  transition: all 0.2s ease;
}

.form-select:hover {
  background-color: #fff;
  border-color: #adb5bd;
}

.form-select:focus {
  background-color: #fff;
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* Reset filters button styling */
.reset-filters-btn {
  background-color: transparent;
  border: 1px solid #6c757d;
  color: #6c757d;
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.2s ease;
  text-decoration: none;
  cursor: pointer;
}

.reset-filters-btn:hover {
  background-color: #6c757d;
  color: #fff;
  border-color: #6c757d;
}

.reset-filters-btn:focus {
  outline: none;
  box-shadow: 0 0 0 0.2rem rgba(108, 117, 125, 0.25);
}

/* Multiselect styling */
.multiselect {
  font-size: 0.875rem;
  min-height: 40px;
  background-color: #f8f9fa;
  border: 1px solid #ced4da;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.multiselect:hover {
  background-color: #fff;
  border-color: #adb5bd;
}

.multiselect.multiselect--active {
  background-color: #fff;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

:deep(.multiselect__tags) {
  background-color: transparent;
  border: none;
  padding: 4px 8px;
  min-height: 38px;
}

:deep(.multiselect__placeholder) {
  color: #6c757d;
  padding-top: 4px;
  margin-bottom: 0;
  font-size: 0.875rem;
}

:deep(.multiselect__input) {
  background-color: transparent;
  border: none;
  font-size: 0.875rem;
  padding: 0;
  margin: 0;
}

:deep(.multiselect__select) {
  height: 38px;
  width: 30px;
}

:deep(.multiselect__select:before) {
  border-color: #6c757d transparent transparent;
  border-width: 5px 4px 0;
}

:deep(.multiselect__content-wrapper) {
  border: 1px solid #e9ecef;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  background-color: #fff;
  max-height: 200px;
}

:deep(.multiselect__content) {
  background-color: #fff;
}

:deep(.multiselect__element) {
  background-color: #fff;
}

:deep(.multiselect__option) {
  padding: 8px 12px;
  font-size: 0.875rem;
  color: #495057;
  background-color: #fff;
  transition: background-color 0.2s ease;
}

:deep(.multiselect__option:hover) {
  background-color: #f8f9fa;
  color: #495057;
}

:deep(.multiselect__option--highlight) {
  background-color: #007bff;
  color: #fff;
}

:deep(.multiselect__option--selected) {
  background-color: #e9ecef;
  color: #495057;
  font-weight: 500;
}

/* Custom tag styling */
.multiselect-tag {
  background-color: #e9ecef;
  color: #495057;
  border-radius: 4px;
  padding: 2px 8px;
  margin: 2px 4px 2px 0;
  font-size: 0.8rem;
  display: inline-flex;
  align-items: center;
  line-height: 1.2;
}

.remove-tag {
  background: none;
  border: none;
  color: #6c757d;
  font-size: 14px;
  margin-left: 4px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.remove-tag:hover {
  color: #343a40;
}

.multiselect-option {
  display: flex;
  align-items: center;
  width: 100%;
}

.option-label {
  flex: 1;
}

/* Responsive styling */
@media (min-width: 768px) {
  .container-fluid {
    padding: 0 1rem;
  }
}

/* Filter panel class compatibility */
.filter-panel {
  background-color: #fff;
  height: 100%;
  overflow-y: auto;
}
</style>