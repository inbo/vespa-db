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
                @click="startEdit">Wijzig</button>
            <button v-if="isLoggedIn && canEdit && !isEditing && !selectedObservation.reserved_by"
                class="btn btn-success me-2" @click="reserveObservation">Reserveren</button>
            <button v-if="isUserReserver" class="btn btn-danger me-2" @click="cancelReservation">Reservatie
                annuleren</button>
            <button v-if="isEditing && canEdit" class="btn btn-success me-2" @click="confirmUpdate">Bevestig</button>
            <button v-if="isEditing && canEdit" class="btn btn-secondary" @click="cancelEdit">Annuleer</button>
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
            return vespaStore.canEditObservation(selectedObservation.value);
        });
        const isUserReserver = computed(() => {
            return vespaStore.isLoggedIn && vespaStore.selectedObservation.reserved_by === vespaStore.user.id;
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

        const reserveObservation = async () => {
            if (!selectedObservation.value.reserved_by) {
                await vespaStore.reserveObservation(selectedObservation.value);
            } else {
                alert('This observation is already reserved.');
            }
        };

        const confirmUpdate = async () => {
            await vespaStore.updateObservation(selectedObservation.value);
            vespaStore.isEditing = false;
        };

        const cancelEdit = () => {
            vespaStore.isEditing = false;
        };

        const cancelReservation = async () => {
            await vespaStore.cancelReservation(selectedObservation.value);
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
            reserveObservation,
            canEdit,
            cancelReservation,
            isUserReserver
        };
    },
};
</script>
