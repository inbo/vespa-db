<template>
  <button class="btn btn-primary d-md-none" type="button" data-bs-toggle="collapse" data-bs-target="#filterCollapse" aria-expanded="false" aria-controls="filterCollapse">
    Filters
  </button>
  <div class="collapse d-md-block" id="filtersCollapse">
    <div class="container-fluid mt-1">
      <div class="row">
        <div class="col-12 col-md-2 mb-2" v-if="formattedMunicipalities.length > 0">
          <v-autocomplete v-model="selectedMunicipalities" :items="municipalities.length ? municipalities.map(municipality => ({
          title: municipality.name,
          value: municipality.id
        })) : []" item-text="title" item-value="value" label="Selecteer gemeente(s)" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
        <div class="col-12 col-md-2 mb-2">
          <v-autocomplete v-model="selectedYears" :items="jaartallen" label="Selecteer jaartal(len)" multiple chips dense
            solo @change="emitFilterUpdate"></v-autocomplete>
        </div>
        <div class="col-12 col-md-2 mb-2">
          <v-autocomplete v-model="selectedNestType" :items="nestType.length ? nestType.map(nesttype => ({
          title: nesttype.name,
          value: nesttype.value
        })) : []" item-text="title" item-value="value" label="Selecteer nesttype" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
        <div class="col-12 col-md-2 mb-2">
          <v-autocomplete v-model="selectedNestStatus" :items="nestStatus.length ? nestStatus.map(neststatus => ({
          title: neststatus.name,
          value: neststatus.value
        })) : []" item-text="title" item-value="value" label="Selecteer neststatus" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
        <div class="col-12 col-md-2 mb-2">
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
import ApiService from '@/services/apiService';
import { useVespaStore } from '@/stores/vespaStore';

export default {
  data() {
    return {
      selectedMunicipalities: [],
      municipalities: [],
      selectedYears: [],
      selectedNestType: [],
      selectedNestStatus: [],
      jaartallen: [2020, 2021, 2022, 2023, 2024],
      anbAreasActief: null,
      nestType: [
        { name: 'AH - actief embryonaal nest', value: 'AH_actief_embryonaal_nest' },
        { name: 'AH - actief primair nest', value: 'AH_actief_primair_nest' },
        { name: 'AH - actief secundair nest', value: 'AH_actief_secundair_nest' },
        { name: 'AH - inactief/leeg nest', value: 'AH_inactief_leeg_nest' },
        { name: 'AH - potentieel nest (meer info nodig)', value: 'AH_potentieel_nest' },
        { name: 'Nest andere soort', value: 'nest_andere_soort' },
        { name: 'Geen nest (object, insect)', value: 'geen_nest' }
      ],
      nestStatus: [
        { name: 'Uitgeroeid', value: 'eradicated' },
        { name: 'Gereserveerd', value: 'reserved' },
        { name: 'Open', value: 'open' }
      ],
      anbAreaOptions: [
        { name: 'Niet in ANB gebied', value: false },
        { name: 'Wel in ANB gebied', value: true },
      ],
    };
  },
  watch: {
    selectedMunicipalities: 'emitFilterUpdate',
    selectedYears: 'emitFilterUpdate',
    anbAreasActief: 'emitFilterUpdate',
    selectedNestType: 'emitFilterUpdate',
    selectedNestStatus: 'emitFilterUpdate',
  },
  computed: {
    formattedMunicipalities() {
      return this.municipalities.map(municipality => ({
        name: municipality.name,
        id: municipality.id
      }));
    },
  },
  methods: {
    async fetchMunicipalities() {
      try {
        const response = await ApiService.get('/municipalities/');
        if (response.status === 200) {
          this.municipalities = response.data;
        } else {
          console.error('Failed to fetch municipalities: Status Code', response.status);
        }
      } catch (error) {
        console.error('Error fetching municipalities:', error);
      }
    },
    emitFilterUpdate() {
      const vespaStore = useVespaStore();
      vespaStore.applyFilters({
        municipalities: this.selectedMunicipalities,
        years: this.selectedYears,
        anbAreasActief: this.anbAreasActief,
        nestType: this.selectedNestType,
        nestStatus: this.selectedNestStatus,
      });
    },
  },
  created() {
    this.fetchMunicipalities();
  },
}
</script>