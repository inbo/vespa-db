<template>
    <div>
        <div v-if="loading" class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
        <div v-else-if="observations.length > 0" class="table-responsive">
            <table class="table table-hover table-sm">
                <thead class="table-light">
                    <tr>
                        <th scope="col" v-for="(header, index) in tableHeaders" :key="index">
                            {{ header }}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="observation in observations" :key="observation.id">
                        <td>{{ observation.id }}</td>
                        <td>{{ observation.location }}</td>
                        <td>{{ observation.province }}</td>
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
</template>
    
<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed, onMounted, ref } from 'vue';

export default {
    setup() {
        const vespaStore = useVespaStore();
        const loading = computed(() => vespaStore.loadingObservations);
        const observations = computed(() => vespaStore.observations);
        const totalObservations = computed(() => vespaStore.totalObservations);
        const nextPage = computed(() => vespaStore.nextPage);
        const previousPage = computed(() => vespaStore.previousPage);
        const tableHeaders = ref(['ID', 'Location', 'Province']);
        const isFilterPaneOpen = ref(false);

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
        const toggleFilterPane = () => {
            isFilterPaneOpen.value = !isFilterPaneOpen.value;
        };

        onMounted(() => {
            if (vespaStore.filters) {
                vespaStore.applyFilters(vespaStore.filters);
            }
            vespaStore.getObservations();
        });

        return { observations, loading, fetchPage, nextPage, previousPage, totalObservations, tableHeaders, toggleFilterPane, isFilterPaneOpen };
    },
};
</script>
    