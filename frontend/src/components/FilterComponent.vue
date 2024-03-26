<template>
  <v-row>
    <v-col v-if="formattedMunicipalities.length > 0" cols="5" sm="3" md="3" lg="3" class="d-flex align-start">
      <v-autocomplete v-model="selectedMunicipalities" :items="municipalities.length ? municipalities.map(municipality => ({
      title: municipality.name,
      value: municipality.id
    })) : []" item-text="title" item-value="value" label="Selecteer gemeente(s)" multiple chips dense solo
        @change="emitFilterUpdate">
      </v-autocomplete>
    </v-col>
    <v-col cols="5" sm="3" md="3" lg="3" class="d-flex align-start">
      <v-autocomplete v-model="selectedYears" :items="jaartallen" label="Selecteer jaartal(len)" multiple chips dense
        solo @change="emitFilterUpdate"></v-autocomplete>
    </v-col>
    <v-col cols="2" sm="3" md="3" lg="3" class="d-flex align-start">
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
      jaartallen: [2020, 2021, 2022, 2023],
      anbAreasActief: false,
    };
  },
  watch: {
    selectedMunicipalities: {
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
        anbAreasActief: this.anbAreasActief
      });
    },
  },
  created() {
    this.fetchMunicipalities();
  },
}
</script>
