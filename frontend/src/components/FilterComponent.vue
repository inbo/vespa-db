<template>
  <div class="collapse d-block" id="filtersCollapse">
    <div class="container-fluid mt-1">
      <div class="row">
        <div class="col-12">
          <h3>Filters</h3>
        </div>
        <div class="col-12" v-if="formattedMunicipalities.length > 0">
          <v-autocomplete v-model="selectedMunicipalities" :items="municipalities.length ? municipalities.map(municipality => ({
            title: municipality.name,
            value: municipality.id
          })) : []" item-text="title" item-value="value" label="gemeente(s)" multiple chips dense solo
            @change="emitFilterUpdate">
          </v-autocomplete>
        </div>
        <div class="col-12">
          <v-autocomplete v-model="selectedYears" :items="jaartallen" label="jaartal(len)" multiple chips dense solo
            @change="emitFilterUpdate"></v-autocomplete>
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
import { computed, onMounted, ref, watch } from 'vue';
import NavbarComponent from './NavbarComponent.vue';

export default {
  components: {
    NavbarComponent,
  },
  setup() {
    const vespaStore = useVespaStore();

    const loading = computed(() => vespaStore.loadingObservations);
    const municipalities = computed(() => vespaStore.municipalities);
    const selectedMunicipalities = ref([]);
    const jaartallen = ref([2020, 2021, 2022, 2023, 2024]);
    const selectedYears = ref([]);
    const selectedNestType = ref([]);
    const selectedNestStatus = ref([]);
    const anbAreasActief = ref(null);
    const nestType = ref([
      { name: 'actief embryonaal nest', value: 'actief_embryonaal_nest' },
      { name: 'actief primair nest', value: 'actief_primair_nest' },
      { name: 'actief secundair nest', value: 'actief_secundair_nest' },
      { name: 'inactief/leeg nest', value: 'inactief_leeg_nest' },
      { name: 'potentieel nest (meer info nodig)', value: 'potentieel_nest' },
    ]);
    const nestStatus = ref([
      { name: 'Uitgeroeid', value: 'eradicated' },
      { name: 'Gereserveerd', value: 'reserved' },
      { name: 'Open', value: 'open' }
    ]);
    const anbAreaOptions = ref([
      { name: 'Niet in ANB gebied', value: false },
      { name: 'Wel in ANB gebied', value: true }
    ]);
    const formattedMunicipalities = computed(() => municipalities.value.map(municipality => ({
      name: municipality.name,
      id: municipality.id
    })));
    const emitFilterUpdate = () => {
      vespaStore.applyFilters({
        municipalities: selectedMunicipalities.value,
        years: selectedYears.value,
        anbAreasActief: anbAreasActief.value,
        nestType: selectedNestType.value,
        nestStatus: selectedNestStatus.value,
      });
    };

    watch([selectedMunicipalities, selectedYears, selectedNestType, selectedNestStatus, anbAreasActief], () => {
      emitFilterUpdate();
    }, { deep: true });

    onMounted(() => {
      vespaStore.fetchMunicipalities();
    });
    return { municipalities, loading, formattedMunicipalities, nestType, nestStatus, anbAreaOptions, selectedMunicipalities, selectedYears, jaartallen, selectedNestType, selectedNestStatus, anbAreasActief, emitFilterUpdate };

  }
};
</script>
  