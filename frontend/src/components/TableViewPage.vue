<template>
    <div class="d-flex flex-column vh-100">
        <NavbarComponent />
        <div class="flex-grow-1 position-relative">
            <button class="btn-filter-toggle" @click="toggleFilterPane">
                <i class="fas fa-sliders-h"></i> Filters
            </button>
            <div class="filter-panel" 
     :class="{'d-none': !isFilterPaneOpen, 'd-block': isFilterPaneOpen, 'col-12': true, 'col-md-6': true, 'col-lg-4': true}">
                <FilterComponent />
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
                                    <th scope="col" v-for="header in tableHeaders" :key="header.value" @click="toggleSort(header.value)">
                                        {{ header.text }}
                                        <span v-if="sortBy === header.value">
                                            <i class="fas" :class="{'fa-sort-up': sortOrder === 'asc', 'fa-sort-down': sortOrder === 'desc'}"></i>
                                        </span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="observation in table_observations" :key="observation.id">
                                    <td>{{ observation.id }}</td>
                                    <td>{{ observation.municipality_name }}</td>
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
import { useVespaStore } from '@/stores/vespaStore';
import { computed, onMounted, ref, watch } from 'vue';
import FilterComponent from './FilterComponent.vue';
import NavbarComponent from './NavbarComponent.vue';

export default {
    components: {
        NavbarComponent,
        FilterComponent,
    },
    setup() {
        const vespaStore = useVespaStore();
        const isFilterPaneOpen = ref(false);
        const loading = computed(() => vespaStore.loadingObservations);
        const totalObservations = computed(() => vespaStore.totalObservations);
        const nextPage = computed(() => vespaStore.nextPage);
        const previousPage = computed(() => vespaStore.previousPage);
        const table_observations = computed(() => vespaStore.table_observations);
        const tableHeaders = ref([
            { text: 'ID', value: 'id' },
            { text: 'Gemeente', value: 'municipality_name' }
        ]);
        const sortBy = ref(null);
        const sortOrder = ref('asc');

        const toggleFilterPane = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };
        const toggleSort = (field) => {
            if (sortBy.value === field) {
                sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
            } else {
                sortBy.value = field;
                sortOrder.value = 'asc';
            }
            vespaStore.getObservations(1, 25, sortBy.value, sortOrder.value);
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

        watch(() => vespaStore.filters, (newFilters) => {
            vespaStore.getObservations();
        }, { deep: true });

        onMounted(() => {
            vespaStore.getObservations();
        });

        return { table_observations, loading, fetchPage, nextPage, previousPage, totalObservations, tableHeaders, toggleSort, toggleFilterPane, isFilterPaneOpen, sortBy, sortOrder };
    }
};
</script>