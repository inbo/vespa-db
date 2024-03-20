<template>
    <v-row>
      <v-col cols="5" sm="3" md="3" lg="3"class="d-flex align-start">
        <v-autocomplete
          v-model="selectedGemeentes"
          :menu-props="{ maxHeight: 500 }"
          :items="gemeentes"
          label="Selecteer gemeente(s)"
          multiple
          chips
          dense
          solo
        ></v-autocomplete>
      </v-col>

      <v-col cols="5" sm="3" md="3" lg="3"class="d-flex align-start">
        <v-autocomplete
          v-model="selectedJaartallen"
          :items="jaartallen"
          label="Selecteer jaartal(len)"
          multiple
          chips
          dense
          solo
        ></v-autocomplete>
      </v-col>

      <v-col cols="2" sm="3" md="3" lg="3" class="d-flex align-start">
        <v-switch
          v-model="anbAreasActief"
          :label="`ANB Areas ${anbAreasActief ? 'Aan' : 'Uit'}`"
          :color="anbAreasActief ? '#4C7742' : ''"
        ></v-switch>
      </v-col>
    </v-row>
</template>
<script>
import ApiService from '@/services/apiService';
export default {
  data: () => ({
    selectedGemeentes: [],
    gemeentes: [],
    selectedJaartallen: [],
    jaartallen: [2020, 2021, 2022, 2023],
    anbAreasActief: false,
    smallScreen: false,
  }),
  methods: {
    async fetchMunicipalities() {
      try {
        const response = await ApiService.get('/municipalities/');
        if (response.status === 200) {
          this.gemeentes = response.data.map(municipality => municipality.name);
        } else {
          console.error('Failed to fetch municipalities: Status Code', response.status);
        }
      } catch (error) {
        console.error('Error fetching municipalities:', error);
      }
    },
  },
  created() {
    this.fetchMunicipalities();
  },
}
</script>