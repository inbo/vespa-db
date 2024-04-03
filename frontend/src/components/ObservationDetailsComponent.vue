<template>
    <div v-if="selectedObservation" class="p-4">
        <button type="button" class="btn-close" aria-label="Close" @click="closeDetails"></button>
        <div class="mb-3" v-for="(value, key) in selectedObservation" :key="key">
            <strong>{{ key }}:</strong>
            <span v-if="typeof value === 'boolean'">{{ value ? 'Yes' : 'No' }}</span>
            <span v-else-if="typeof value === 'string' || typeof value === 'number'">{{ value }}</span>
            <span v-else>Unsupported Type</span>
        </div>
        <div>
            <button v-if="isLoggedIn" class="btn btn-success me-2" @click="startEdit">Edit</button>
            <button v-if="isEditing" class="btn btn-success me-2" @click="confirmUpdate">Confirm</button>
            <button v-if="isEditing" class="btn btn-secondary" @click="cancelEdit">Cancel</button>
        </div>
    </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed, defineEmits } from 'vue';

export default {
setup() {
    const emits = defineEmits(['closeDetails']);
    const vespaStore = useVespaStore();
    const selectedObservation = computed(() => vespaStore.selectedObservation);
    const isEditing = computed(() => vespaStore.isEditing);
    const isLoggedIn = computed(() => vespaStore.isLoggedIn);

    const closeDetails = () => {
        emits('closeDetails');
        vespaStore.isDetailsPaneOpen = false;
    };

    const startEdit = () => {
        // Logic to start editing
    };

    const confirmUpdate = () => {
        // Logic to confirm update
    };

    const cancelEdit = () => {
        // Logic to cancel editing
    };

    return {
        selectedObservation,
        isEditing,
        isLoggedIn,
        startEdit,
        confirmUpdate,
        cancelEdit,
        closeDetails,
    };
},
};
</script>

<style scoped>
.btn-close {
    position: absolute;
    top: 1rem;
    right: 1rem;
}
</style>
