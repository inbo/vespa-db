<template>
  <v-container fluid>
    <v-row no-gutters>
      <v-col cols="12" md="2" class="py-1">
        <v-combobox
          v-model="filters.municipalities"
          :items="availableMunicipalities"
          label="Gemeente"
          multiple
          chips
          small-chips
          class="styled-combobox"
        ></v-combobox>
      </v-col>
      <v-col cols="12" md="2" class="py-1">
        <v-combobox
          v-model="filters.years"
          :items="availableYears"
          label="Year"
          multiple
          chips
          small-chips
          class="styled-combobox"
        ></v-combobox>
      </v-col>
      <v-col cols="12" md="1" class="py-1">
        <v-btn
          :color="filters.anb ? '#4C7742' : 'grey lighten-1'"
          @click="filters.anb = !filters.anb"
          class="styled-button"
        >
          ANB
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'FilterComponent',
  data: () => ({
    filters: {
      municipalities: [],
      anb: false,
      thisSeason: false,
      years: [],
    },
    availableMunicipalities: ['Leuven', 'Tienen', 'Brussel'],
    availableYears: Array.from({ length: 5 }, (v, k) => new Date().getFullYear() - k),
  }),
  methods: {
  },
  watch: {
    filters: {
      handler(newFilters) {
        this.$emit('update:filters', newFilters);
      },
      deep: true,
    },
  },
};
</script>
