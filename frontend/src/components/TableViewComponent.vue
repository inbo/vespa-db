<template>
<div class="table-responsive">
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
        <td v-for="(value, key) in observation" :key="key">
            <span v-if="typeof value === 'object' && value !== null">{{ value.name || value.id || JSON.stringify(value) }}</span>
            <span v-else>{{ value }}</span>
        </td>
        </tr>
    </tbody>
    </table>
</div>
</template>
<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed, ref } from 'vue';

export default {
setup() {
    const vespaStore = useVespaStore();
    const observations = computed(() => vespaStore.observations);
    const tableHeaders = ref([]);

    if (observations.value.length > 0) {
    tableHeaders.value = Object.keys(observations.value[0]).map((key) => {
        return key.replace(/([A-Z])/g, ' $1').replace(/^./, (str) => str.toUpperCase());
    });
    }

    return { observations, tableHeaders };
},
};
</script>
