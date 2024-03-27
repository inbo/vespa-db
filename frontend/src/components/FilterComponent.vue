<template>
  <v-row>
    <v-col v-if="formattedMunicipalities.length > 0" cols="2" class="d-flex align-start">
      <v-autocomplete v-model="selectedMunicipalities" :items="municipalities.length ? municipalities.map(municipality => ({
      title: municipality.name,
      value: municipality.id
    })) : []" item-text="title" item-value="value" label="Selecteer gemeente(s)" multiple chips dense solo
        @change="emitFilterUpdate">
      </v-autocomplete>
    </v-col>
    <v-col cols="2" class="d-flex align-start">
      <v-autocomplete v-model="selectedYears" :items="jaartallen" label="Selecteer jaartal(len)" multiple chips dense
        solo @change="emitFilterUpdate"></v-autocomplete>
    </v-col>
    <v-col cols="2"class="d-flex align-start">
      <v-autocomplete v-model="selectedNestType" :items="nestType.length ? nestType.map(nesttype => ({
      title: nesttype.name,
      value: nesttype.value
    })) : []" item-text="title" item-value="value" label="Selecteer nesttype" multiple chips dense solo
        @change="emitFilterUpdate">
      </v-autocomplete>
    </v-col>
    <v-col cols="2" class="d-flex align-start">
      <v-autocomplete v-model="selectedNestStatus" :items="nestStatus.length ? nestStatus.map(neststatus => ({
      title: neststatus.name,
      value: neststatus.value
    })) : []" item-text="title" item-value="value" label="Selecteer neststatus" multiple chips dense solo
        @change="emitFilterUpdate">
      </v-autocomplete>
    </v-col>
    <v-col cols="1" class="d-flex align-start">
      <v-switch v-model="anbAreasActief" :label="`ANB Areas ${anbAreasActief ? 'Aan' : 'Uit'}`"
        :color="anbAreasActief ? '#4C7742' : ''" @change="emitFilterUpdate"></v-switch>
    </v-col>
  </v-row>
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
      anbAreasActief: false,
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
    };
  },
  watch: {
    selectedMunicipalities: {
      handler() {
        this.emitFilterUpdate();
      },
      deep: true,
    },
    selectedYears: {
      handler() {
        this.emitFilterUpdate();
      },
      deep: true,
    },
    anbAreasActief: function() {
      this.emitFilterUpdate();
    },
    selectedNestType: {
      handler() {
        this.emitFilterUpdate();
      },
      deep: true,
    },
    selectedNestStatus: {
      handler() {
        this.emitFilterUpdate();
      },
      deep: true,
    },
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
