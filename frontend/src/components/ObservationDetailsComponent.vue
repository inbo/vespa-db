<template>
    <div v-if="selectedObservation">
        <div v-for="(value, key) in selectedObservation" :key="key" class="mb-3">
            <strong>{{ key }}:</strong>
            <template v-if="isEditing && editableFields.includes(key)">
                <input v-if="typeof value === 'number'" type="number" v-model="selectedObservation[key]"
                    class="form-control">
                <input v-else-if="typeof value === 'string'" type="text" v-model="selectedObservation[key]"
                    class="form-control">
            </template>
            <template v-else>
                <span v-if="typeof value === 'boolean'">{{ value ? 'Yes' : 'No' }}</span>
                <span v-else-if="typeof value === 'string' || typeof value === 'number'">{{ value }}</span>
                <span v-else>Unsupported Type</span>
            </template>
        </div>
        <div>
            <button v-if="isLoggedIn && canEdit && !isEditing" class="btn btn-success me-2"
                @click="startEdit">Edit</button>
            <button v-if="isEditing && canEdit" class="btn btn-success me-2" @click="confirmUpdate">Confirm</button>
            <button v-if="isEditing && canEdit" class="btn btn-secondary" @click="cancelEdit">Cancel</button>
        </div>
    </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed } from 'vue';

export default {
    emits: ['closeDetails'],
    setup(props, { emit }) {
        const vespaStore = useVespaStore();
        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = computed(() => vespaStore.isEditing);
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const canEdit = computed(() => {
            console.log(selectedObservation.value);
            return vespaStore.canEditObservation(selectedObservation.value);
        });

        const editableFields = [
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "notes",
            "modified_by",
            "created_by",
            "duplicate",
            "reserved_by",
            "reserved_datetime",
            "eradication_datetime",
            "eradicator_name",
            "eradication_result",
            "eradication_product",
            "eradication_notes",
        ];

        const closeDetails = () => {
            emit('closeDetails'); // Use emit from the context
            vespaStore.isDetailsPaneOpen = false;
        };

        const startEdit = () => {
            vespaStore.isEditing = true;
        };

        const confirmUpdate = async () => {
            await vespaStore.updateObservation(selectedObservation.value);
            vespaStore.isEditing = false;
        };

        const cancelEdit = () => {
            vespaStore.isEditing = false;
        };

        return {
            selectedObservation,
            isEditing,
            isLoggedIn,
            startEdit,
            confirmUpdate,
            cancelEdit,
            closeDetails,
            editableFields,
            canEdit
        };
    },
};
</script>
