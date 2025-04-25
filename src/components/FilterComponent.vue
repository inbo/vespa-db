<template>
  <div class="collapse d-block" id="filtersCollapse">
    <div class="container-fluid mt-1">
      <div class="row">
        <div class="col-12">
          <h3 class="filters-heading">Filters</h3>
        </div>
        <div class="col-12">
          <v-autocomplete
            v-model="selectedProvinces"
            :items="
              provinces.length
                ? provinces.map((province) => ({
                    title: province.name,
                    value: province.id,
                  }))
                : []
            "
            item-text="title"
            item-value="value"
            label="provincie(s)"
            multiple
            chips
            dense
            solo
            background-color="#f8f9fa"
            class="filter-autocomplete"
            @change="emitFilterUpdate"
          ></v-autocomplete>
        </div>
        <div class="col-12">
          <v-autocomplete
            v-model="selectedMunicipalities"
            :items="
              municipalities.length
                ? municipalities.map((municipality) => ({
                    title: municipality.name,
                    value: municipality.id,
                  }))
                : []
            "
            item-text="title"
            item-value="value"
            label="gemeente(s)"
            multiple
            chips
            dense
            solo
            background-color="#f8f9fa"
            class="filter-autocomplete"
            @change="emitFilterUpdate"
          ></v-autocomplete>
        </div>
        <div class="col-12">
          <DateFilter />
        </div>
        <div class="col-12">
          <v-autocomplete
            v-model="selectedNestType"
            :items="
              nestType.length
                ? nestType.map((nesttype) => ({
                    title: nesttype.name,
                    value: nesttype.value,
                  }))
                : []
            "
            item-text="title"
            item-value="value"
            label="nest type"
            multiple
            chips
            dense
            solo
            background-color="#f8f9fa"
            class="filter-autocomplete"
            @change="emitFilterUpdate"
          ></v-autocomplete>
        </div>
        <div class="col-12">
          <v-autocomplete
            v-model="selectedNestStatus"
            :items="
              nestStatus.length
                ? nestStatus.map((neststatus) => ({
                    title: neststatus.name,
                    value: neststatus.value,
                  }))
                : []
            "
            item-text="title"
            item-value="value"
            label="nest status"
            multiple
            chips
            dense
            solo
            background-color="#f8f9fa"
            class="filter-autocomplete"
            @change="emitFilterUpdate"
          ></v-autocomplete>
        </div>
        <div class="col-12">
          <v-autocomplete
            v-model="anbAreasActief"
            :items="
              anbAreaOptions.length
                ? anbAreaOptions.map((anb) => ({
                    title: anb.name,
                    value: anb.value,
                  }))
                : []
            "
            item-text="title"
            item-value="value"
            label="ANB"
            multiple
            chips
            dense
            solo
            background-color="#f8f9fa"
            class="filter-autocomplete"
            @change="emitFilterUpdate"
          ></v-autocomplete>
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

export default {
  components: {
    DateFilter,
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
    const nestType = ref([
      { name: 'Actief embryonaal nest', value: 'actief_embryonaal_nest' },
      { name: 'Actief primair nest', value: 'actief_primair_nest' },
      { name: 'Actief secundair nest', value: 'actief_secundair_nest' },
      { name: 'Inactief/leeg nest', value: 'inactief_leeg_nest' },
    ]);
    const nestStatus = ref([
      { name: 'Bestreden nest', value: 'eradicated' },
      { name: 'Gereserveerd nest', value: 'reserved' },
      { name: 'Gerapporteerd nest', value: 'open' },
    ]);
    const anbAreaOptions = ref([
      { name: 'Niet in ANB gebied', value: false },
      { name: 'Wel in ANB gebied', value: true },
    ]);

    const emitFilterUpdate = debounce(() => {
      vespaStore.applyFilters({
        municipalities:
          selectedMunicipalities.value.length > 0
            ? selectedMunicipalities.value
            : [],
        provinces:
          selectedProvinces.value.length > 0 ? selectedProvinces.value : [],
        anbAreasActief: anbAreasActief.value,
        nestType:
          selectedNestType.value.length > 0 ? selectedNestType.value : null,
        nestStatus:
          selectedNestStatus.value.length > 0 ? selectedNestStatus.value : null,
        // min_observation_date and max_observation_date are handled by DateFilter component
      });
    }, 300);

    const fetchMunicipalitiesByProvinces = async () => {
      if (selectedProvinces.value.length > 0) {
        await vespaStore.fetchMunicipalitiesByProvinces(selectedProvinces.value);
      } else {
        await vespaStore.fetchMunicipalities();
      }
    };

    watch(selectedProvinces, fetchMunicipalitiesByProvinces, { deep: true });

    watch(
      [selectedMunicipalities, selectedProvinces, selectedNestType, selectedNestStatus, anbAreasActief],
      () => {
        emitFilterUpdate();
      },
      { deep: true }
    );

    // Watch store filters for changes from other components
    watch(
      () => vespaStore.filters,
      (newFilters, oldFilters) => {
        const hasChanged = JSON.stringify(newFilters) !== JSON.stringify(oldFilters);

        if (hasChanged) {
          selectedMunicipalities.value = newFilters.municipalities || [];
          selectedProvinces.value = newFilters.provinces || [];
          anbAreasActief.value = newFilters.anbAreasActief || null;
          selectedNestType.value = newFilters.nestType || [];
          selectedNestStatus.value = newFilters.nestStatus || [];
          // min_observation_date and max_observation_date are handled by DateFilter component
        }
      },
      { immediate: true, deep: true }
    );

    onMounted(async () => {
      selectedMunicipalities.value = vespaStore.filters.municipalities || [];
      selectedProvinces.value = vespaStore.filters.provinces || [];
      anbAreasActief.value = vespaStore.filters.anbAreasActief;
      selectedNestType.value = vespaStore.filters.nestType || [];
      selectedNestStatus.value = vespaStore.filters.nestStatus || [];
      // min_observation_date and max_observation_date are handled by DateFilter component
    });

    return {
      municipalities,
      provinces,
      loading,
      nestType,
      nestStatus,
      anbAreaOptions,
      selectedMunicipalities,
      selectedProvinces,
      selectedNestType,
      selectedNestStatus,
      anbAreasActief,
      emitFilterUpdate,
    };
  },
};
</script>

<style scoped>
.filters-heading {
  font-size: 1.75rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e9ecef;
}

.filter-autocomplete {
  margin-bottom: 24px;
}

/* Override vuetify autocomplete styles to match with our DateFilter */
:deep(.v-text-field__slot) {
  font-size: 14px;
}

:deep(.v-select__selection) {
  font-size: 14px;
}

:deep(.v-chip) {
  font-size: 12px;
  background-color: #e9ecef !important;
  color: #495057 !important;
  border-radius: 4px !important;
}

:deep(.v-chip__close) {
  color: #6c757d !important;
}

:deep(.v-text-field.v-text-field--solo .v-input__control) {
  min-height: 44px;
}

:deep(.v-text-field.v-text-field--solo .v-input__slot) {
  border-radius: 4px;
  border: 1px solid #ced4da;
  transition: all 0.2s ease;
}

:deep(.v-text-field.v-text-field--solo .v-input__slot:hover) {
  border-color: #adb5bd;
  background-color: #fff !important;
}

:deep(.v-text-field.v-text-field--solo.v-input--is-focused .v-input__slot) {
  border-color: #007bff;
  background-color: #fff !important;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

:deep(.v-text-field__details) {
  display: none;
}

:deep(.v-label) {
  font-size: 14px;
  color: #495057;
}

:deep(.v-label--active) {
  color: #007bff;
}

:deep(.v-messages) {
  min-height: 0;
}

/* Add responsive styling to match the rest of the application */
@media (min-width: 768px) {
  .container-fluid {
    padding: 0 24px;
  }
  
  #filtersCollapse {
    background-color: transparent;
  }
}

/* Make this work with the filter-panel class from global CSS */
:deep(.filter-panel) {
  background-color: #fff;
  height: 100%;
  overflow-y: auto;
}
</style>
