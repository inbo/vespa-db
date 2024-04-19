<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPane">
                <i class="fas fa-sliders-h"></i> Filters
            </button>
            <div id="map" class="h-100"></div>
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
            <div class="details-panel" :class="{ 'panel-active': isDetailsPaneOpen }">
                <div class="d-flex justify-content-between align-items-center">
                    <h3>Observatie details</h3>
                    <button type="button" class="btn-close" aria-label="Close" @click="toggleDetailsPane"></button>
                </div>
                <ObservationDetailsComponent />
            </div>
        </div>
    </div>
</template>
  
<script>
import ApiService from '@/services/apiService';
import { useVespaStore } from '@/stores/vespaStore';
import 'leaflet/dist/leaflet.css';
import { computed, onMounted, ref, watch } from 'vue';
import NavbarComponent from './NavbarComponent.vue';
import ObservationDetailsComponent from './ObservationDetailsComponent.vue';

export default {
    components: {
        NavbarComponent,
        ObservationDetailsComponent,
    },
    setup() {
        const vespaStore = useVespaStore();
        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = computed(() => vespaStore.isEditing);
        const map = computed(() => vespaStore.map);
        const markerClusterGroup = L.markerClusterGroup({ spiderfyOnMaxZoom: false, showCoverageOnHover: false, zoomToBoundsOnClick: false });
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const isDetailsPaneOpen = computed(() => vespaStore.isDetailsPaneOpen);
        const isFilterPaneOpen = ref(false);
        const selectedMunicipalities = ref([]);
        const jaartallen = ref([2020, 2021, 2022, 2023, 2024]);
        const municipalities = ref([]);
        const selectedYears = ref([]);
        const selectedNestType = ref([]);
        const selectedNestStatus = ref([]);
        const anbAreasActief = ref(null);
        const nestType = [
            { name: 'AH - actief embryonaal nest', value: 'AH_actief_embryonaal_nest' },
            { name: 'AH - actief primair nest', value: 'AH_actief_primair_nest' },
            { name: 'AH - actief secundair nest', value: 'AH_actief_secundair_nest' },
            { name: 'AH - inactief/leeg nest', value: 'AH_inactief_leeg_nest' },
            { name: 'AH - potentieel nest (meer info nodig)', value: 'AH_potentieel_nest' },
            { name: 'Nest andere soort', value: 'nest_andere_soort' },
            { name: 'Geen nest (object, insect)', value: 'geen_nest' }
        ];
        const nestStatus = [
            { name: 'Uitgeroeid', value: 'eradicated' },
            { name: 'Gereserveerd', value: 'reserved' },
            { name: 'Open', value: 'open' }
        ];
        const anbAreaOptions = [
            { name: 'Niet in ANB gebied', value: false },
            { name: 'Wel in ANB gebied', value: true },
        ];

        const startEdit = () => {
            isEditing.value = true;
        };

        const confirmUpdate = () => {
            isEditing.value = false;
        };

        const cancelEdit = () => {
            isEditing.value = false;
        };
        const toggleFilterPane = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };
        const toggleDetailsPane = () => {
            vespaStore.isDetailsPaneOpen = !vespaStore.isDetailsPaneOpen;
        };
        const emitFilterUpdate = () => {
            console.log("emitting filter update")
            vespaStore.applyFilters({
                municipalities: selectedMunicipalities.value,
                years: selectedYears.value,
                anbAreasActief: anbAreasActief.value,
                nestType: selectedNestType.value,
                nestStatus: selectedNestStatus.value,
            });
            markerClusterGroup.clearLayers();
            vespaStore.observations = [];
            vespaStore.getObservationsGeoJson().then(geoJson => {
                const geoJsonLayer = L.geoJSON(vespaStore.observations, {
                    pointToLayer: (feature, latlng) => vespaStore.createCircleMarker(feature, latlng)
                });

                markerClusterGroup.addLayer(geoJsonLayer);
                vespaStore.map.addLayer(markerClusterGroup);
            });
        };

        const formattedMunicipalities = computed(() => {
            return municipalities.value.map(municipality => ({
                name: municipality.name,
                id: municipality.id
            }));
        });

        watch([selectedMunicipalities, selectedYears, selectedNestType, selectedNestStatus, anbAreasActief], () => {
            emitFilterUpdate();
        }, { deep: true });

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
        onMounted(() => {
            fetchMunicipalities();
            vespaStore.map = L.map('map', {
                center: [50.8503, 4.3517],
                zoom: 8,
                layers: [
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: 'Map data © OpenStreetMap contributors'
                    }),
                ]
            });
            if (vespaStore.observations.length === 0) {
                vespaStore.getObservationsGeoJson().then(geoJson => {
                    const geoJsonLayer = L.geoJSON(vespaStore.observations, {
                        pointToLayer: (feature, latlng) => vespaStore.createCircleMarker(feature, latlng)
                    });

                    markerClusterGroup.addLayer(geoJsonLayer);
                    vespaStore.map.addLayer(markerClusterGroup);
                });
            } else {
                console.log("using existing data")
                console.log("length obs:" + vespaStore.observations.length)
                const geoJsonLayer = L.geoJSON(vespaStore.observations, {
                    pointToLayer: (feature, latlng) => vespaStore.createCircleMarker(feature, latlng)
                });

                markerClusterGroup.addLayer(geoJsonLayer);
                vespaStore.map.addLayer(markerClusterGroup);
            }
        });

        return {
            isDetailsPaneOpen,
            isFilterPaneOpen,
            toggleFilterPane,
            toggleDetailsPane,
            selectedObservation,
            isEditing,
            map,
            isLoggedIn,
            startEdit,
            confirmUpdate,
            cancelEdit,
            selectedMunicipalities,
            municipalities,
            selectedYears,
            selectedNestType,
            selectedNestStatus,
            anbAreasActief,
            nestType,
            nestStatus,
            anbAreaOptions,
            formattedMunicipalities,
            jaartallen,
            emitFilterUpdate,
        };
    },
};
</script>
  