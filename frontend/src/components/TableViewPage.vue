<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPane">
                <i class="fas fa-sliders-h"></i> Filters
            </button>
            <div class="filter-panel" :class="{ 'panel-active': isFilterPaneOpen }">
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
                                })) : []" item-text="title" item-value="value" label="gemeente(s)" multiple chips dense
                                    solo @change="emitFilterUpdate">
                                </v-autocomplete>
                            </div>
                            <div class="col-12">
                                <v-autocomplete v-model="selectedYears" :items="jaartallen" label="jaartal(len)" multiple
                                    chips dense solo @change="emitFilterUpdate"></v-autocomplete>
                            </div>
                            <div class="col-12">
                                <v-autocomplete v-model="selectedNestType" :items="nestType.length ? nestType.map(nesttype => ({
                                    title: nesttype.name,
                                    value: nesttype.value
                                })) : []" item-text="title" item-value="value" label="nest type" multiple chips dense
                                    solo @change="emitFilterUpdate">
                                </v-autocomplete>
                            </div>
                            <div class="col-12">
                                <v-autocomplete v-model="selectedNestStatus" :items="nestStatus.length ? nestStatus.map(neststatus => ({
                                    title: neststatus.name,
                                    value: neststatus.value
                                })) : []" item-text="title" item-value="value" label="nest status" multiple chips dense
                                    solo @change="emitFilterUpdate">
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
            </div>
            <div class="container mt-4">
                <div>
                    <div v-if="loading" class="text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                    <div v-else-if="table_observations.length > 0" class="table-responsive">
                        <table class="table table-hover table-sm">
                            <thead class="table-light">
                                <tr>
                                    <th scope="col" v-for="(header, index) in tableHeaders" :key="index">
                                        {{ header }}
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="observation in table_observations" :key="observation.id">
                                    <td>{{ observation.id }}</td>
                                    <td>{{ observation.location }}</td>
                                    <td>{{ observation.municipality }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div v-if="totalObservations > 0" class="d-flex justify-content-start mt-3">
                        <button class="btn btn-outline-success mr-2" @click="fetchPage('prev')" :disabled="!previousPage">
                            <i class="fas fa-chevron-left"></i> Previous
                        </button>
                        <button class="btn btn-outline-success" @click="fetchPage('next')" :disabled="!nextPage">
                            Next <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import ApiService from '@/services/apiService';
import { useVespaStore } from '@/stores/vespaStore';
import { computed, onMounted, ref, watch } from 'vue';
import NavbarComponent from './NavbarComponent.vue';

export default {
    components: {
        NavbarComponent,
    },
    setup() {
        const vespaStore = useVespaStore();
        const isFilterPaneOpen = ref(false);
        const loading = computed(() => vespaStore.loadingObservations);
        const table_observations = computed(() => vespaStore.table_observations);
        const totalObservations = computed(() => vespaStore.totalObservations);
        const nextPage = computed(() => vespaStore.nextPage);
        const previousPage = computed(() => vespaStore.previousPage);
        const tableHeaders = ref(['ID', 'Location', 'Municipality']);

        // States for filters
        const municipalities = ref([]);
        const selectedMunicipalities = ref([]);
        const jaartallen = ref([2020, 2021, 2022, 2023, 2024]);
        const selectedYears = ref([]);
        const selectedNestType = ref([]);
        const selectedNestStatus = ref([]);
        const anbAreasActief = ref(null);
        const nestType = ref([
            { name: 'AH - actief embryonaal nest', value: 'AH_actief_embryonaal_nest' },
            { name: 'AH - actief primair nest', value: 'AH_actief_primair_nest' },
            { name: 'AH - actief secundair nest', value: 'AH_actief_secundair_nest' },
            { name: 'AH - inactief/leeg nest', value: 'AH_inactief_leeg_nest' },
            { name: 'AH - potentieel nest (meer info nodig)', value: 'AH_potentieel_nest' },
            { name: 'Nest andere soort', value: 'nest_andere_soort' },
            { name: 'Geen nest (object, insect)', value: 'geen_nest' }
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

        const fetchMunicipalities = async () => {
            try {
                const response = await ApiService.get('/municipalities/');
                if (response.status === 200) {
                    municipalities.value = response.data;
                } else {
                    console.error('Failed to fetch municipalities: Status Code', response.status);
                }
            } catch (error) {
                console.error('Error fetching municipalities:', error);
            }
        };

        watch([selectedMunicipalities, selectedYears, selectedNestType, selectedNestStatus, anbAreasActief], () => {
            emitFilterUpdate();
        }, { deep: true });

        const emitFilterUpdate = () => {
            vespaStore.applyFilters({
                municipalities: selectedMunicipalities.value,
                years: selectedYears.value,
                anbAreasActief: anbAreasActief.value,
                nestType: selectedNestType.value.map(type => type.value),
                nestStatus: selectedNestStatus.value.map(status => status.value),
            });
            vespaStore.getObservations();
        };

        const toggleFilterPane = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };

        const fetchPage = (direction) => {
            let url;
            if (direction === 'next' && nextPage.value) {
                url = nextPage.value;
            } else if (direction === 'prev' && previousPage.value) {
                url = previousPage.value;
            }
            if (url) {
                const pageParams = new URLSearchParams(url.split('?')[1]);
                vespaStore.getObservations(pageParams.get('page'), pageParams.get('page_size'));
            }
        };

        onMounted(() => {
            fetchMunicipalities();
            if (vespaStore.filters) {
                vespaStore.applyFilters(vespaStore.filters);
            }
            vespaStore.getObservations();
        });
        return { municipalities, table_observations, loading, fetchPage, nextPage, previousPage, totalObservations, tableHeaders, toggleFilterPane, isFilterPaneOpen, formattedMunicipalities, nestType, nestStatus, anbAreaOptions, selectedMunicipalities, selectedYears, jaartallen, selectedNestType, selectedNestStatus, anbAreasActief, emitFilterUpdate };

    }
};
</script>
  