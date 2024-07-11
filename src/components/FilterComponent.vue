<template>
  <div class="collapse d-block" id="filtersCollapse">
    <div class="container-fluid mt-1">
      <div class="row">
        <div class="col-12">
          <h3>Filters</h3>
        </div>
        <div class="col-12">
          <v-autocomplete v-model="selectedProvinces" :items="provinces.length ? provinces.map(province => ({
            title: province.name,
            value: province.id
          })) : []" item-text="title" item-value="value" label="provincie(s)" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
        <div class="col-12">
          <v-autocomplete v-model="selectedMunicipalities" :items="municipalities.length ? municipalities.map(municipality => ({
            title: municipality.name,
            value: municipality.id
          })) : []" item-text="title" item-value="value" label="gemeente(s)" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
        <div class="col-12">
          <v-text-field v-model="minDate" label="Observaties vanaf" prepend-icon="mdi-calendar" readonly
            @click="toggleMenu1"></v-text-field>
          <v-date-picker v-model="minDate" v-show="menu1" @input="closeMenu1" @change="closeMenu1"></v-date-picker>
        </div>
        <div class="col-12">
          <v-text-field v-model="maxDate" label="Observaties tot" prepend-icon="mdi-calendar" readonly
            @click="toggleMenu2"></v-text-field>
          <v-date-picker v-model="maxDate" v-show="menu2" @input="closeMenu2" @change="closeMenu2"></v-date-picker>
        </div>
        <div class="col-12">
          <v-autocomplete v-model="selectedNestType" :items="nestType.length ? nestType.map(nesttype => ({
            title: nesttype.name,
            value: nesttype.value
          })) : []" item-text="title" item-value="value" label="nest type" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
        <div class="col-12">
          <v-autocomplete v-model="selectedNestStatus" :items="nestStatus.length ? nestStatus.map(neststatus => ({
            title: neststatus.name,
            value: neststatus.value
          })) : []" item-text="title" item-value="value" label="nest status" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
        <div class="col-12">
          <v-autocomplete v-model="anbAreasActief" :items="anbAreaOptions.length ? anbAreaOptions.map(anb => ({
            title: anb.name,
            value: anb.value
          })) : []" item-text="title" item-value="value" label="ANB" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { DateTime } from 'luxon';
import { computed, onMounted, ref, watch } from 'vue';
import debounce from 'lodash/debounce';

export default {
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
    const visibleActief = ref(true);
    const nestType = ref([
      { name: 'actief embryonaal nest', value: 'actief_embryonaal_nest' },
      { name: 'actief primair nest', value: 'actief_primair_nest' },
      { name: 'actief secundair nest', value: 'actief_secundair_nest' },
      { name: 'inactief/leeg nest', value: 'inactief_leeg_nest' },
      { name: 'potentieel nest (meer info nodig)', value: 'potentieel_nest' },
    ]);
    const nestStatus = ref([
      { name: 'Bestreden', value: 'eradicated' },
      { name: 'Gereserveerd', value: 'reserved' },
      { name: 'Niet bestreden', value: 'open' }
    ]);
    const anbAreaOptions = ref([
      { name: 'Niet in ANB gebied', value: false },
      { name: 'Wel in ANB gebied', value: true }
    ]);
    const VisibleOptions = ref([
      { name: 'Zichtbaar', value: true },
      { name: 'Niet zichtbaar', value: false }
    ]);
    const minDate = ref(new Date(new Date().getFullYear(), 3, 1));
    const maxDate = ref(null);
    const selectedObservationStart = ref(false);
    const selectedObservationEnd = ref(false);
    const menu1 = ref(false);
    const menu2 = ref(false);

    const emitFilterUpdate = debounce(() => {
      const minDateCET = minDate.value ? DateTime.fromJSDate(minDate.value).setZone('Europe/Paris').toFormat('yyyy-MM-dd\'T\'HH:mm:ss') : null;
      const maxDateCET = maxDate.value ? DateTime.fromJSDate(maxDate.value).setZone('Europe/Paris').toFormat('yyyy-MM-dd\'T\'HH:mm:ss') : null;

      vespaStore.applyFilters({
        municipalities: selectedMunicipalities.value.length > 0 ? selectedMunicipalities.value : [],
        provinces: selectedProvinces.value.length > 0 ? selectedProvinces.value : [],
        anbAreasActief: anbAreasActief.value,
        nestType: selectedNestType.value.length > 0 ? selectedNestType.value : null,
        nestStatus: selectedNestStatus.value.length > 0 ? selectedNestStatus.value : null,
        min_observation_date: minDateCET,
        max_observation_date: maxDateCET,
        visible: visibleActief.value
      });
    }, 300);

    const toggleMenu1 = () => {
      menu1.value = !menu1.value;
    };

    const closeMenu1 = () => {
      menu1.value = false;
      emitFilterUpdate();
    };

    const toggleMenu2 = () => {
      menu2.value = !menu2.value;
    };

    const closeMenu2 = () => {
      menu2.value = false;
      emitFilterUpdate();
    };

    const fetchMunicipalitiesByProvinces = async () => {
      if (selectedProvinces.value.length > 0) {
        await vespaStore.fetchMunicipalitiesByProvinces(selectedProvinces.value);
      } else {
        await vespaStore.fetchMunicipalities();
      }
    };

    watch(selectedProvinces, fetchMunicipalitiesByProvinces, { deep: true });

    watch([minDate, maxDate], emitFilterUpdate, { immediate: true });

    watch([selectedMunicipalities, selectedProvinces, selectedNestType, selectedNestStatus, anbAreasActief, selectedObservationStart, selectedObservationEnd, visibleActief], () => {
      emitFilterUpdate();
    }, { deep: true });

    onMounted(async () => {
      if (!vespaStore.municipalitiesFetched) await vespaStore.fetchMunicipalities();
      if (!vespaStore.provincesFetched) await vespaStore.fetchProvinces();
    });

    return {
      municipalities,
      provinces,
      loading,
      nestType,
      minDate,
      selectedObservationStart,
      selectedObservationEnd,
      nestStatus,
      anbAreaOptions,
      selectedMunicipalities,
      selectedProvinces,
      selectedNestType,
      selectedNestStatus,
      anbAreasActief,
      emitFilterUpdate,
      maxDate,
      menu1,
      menu2,
      toggleMenu1,
      closeMenu1,
      toggleMenu2,
      closeMenu2,
      VisibleOptions,
      visibleActief,
    };
  }
};
</script>
