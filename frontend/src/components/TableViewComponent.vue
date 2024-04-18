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
                        <td>{{ observation.nest_height }}</td>
                        <!-- Add other necessary fields as needed -->
                    </tr>
                </tbody>
            </table>
        </div>
        <div v-if="totalObservations > 0" class="d-flex justify-content-between mt-3">
            <button class="btn btn-outline-primary" @click="fetchPage('prev')" :disabled="!previousPage">
                <i class="fas fa-chevron-left"></i> Previous
            </button>
            <button class="btn btn-outline-primary" @click="fetchPage('next')" :disabled="!nextPage">
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
        const tableHeaders = ref(['ID', 'Location', 'Nest Height']); // Extend as needed

        const fetchPage = (direction) => {
            if (direction === 'next' && nextPage.value) {
                const pageParams = new URLSearchParams(nextPage.value.split('?')[1]);
                vespaStore.getObservations('', pageParams.get('page'), pageParams.get('page_size'));
            } else if (direction === 'prev' && previousPage.value) {
                const pageParams = new URLSearchParams(previousPage.value.split('?')[1]);
                vespaStore.getObservations('', pageParams.get('page'), pageParams.get('page_size'));
            }
        };

        onMounted(() => {
            vespaStore.getObservations();
        });

        return { observations, loading, fetchPage, nextPage, previousPage, totalObservations, tableHeaders };
    },
};
</script>
    