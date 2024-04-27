<template>
    <div v-if="selectedObservation">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Observatie Detail</h5>
                <dl class="row">
                    <dt class="col-sm-3">ID</dt>
                    <dd class="col-sm-9">887</dd>

                    <dt class="col-sm-3">Aangemaakt op</dt>
                    <dd class="col-sm-9">2024-04-26 09:58</dd>

                    <dt class="col-sm-3">Laatst gewijzigd</dt>
                    <dd class="col-sm-9">2024-04-26 09:58</dd>

                    <dt class="col-sm-3">Bron</dt>
                    <dd class="col-sm-9">Unsupported Type</dd>

                    <dt class="col-sm-3">Soort</dt>
                    <dd class="col-sm-9">8807</dd>

                    <dt class="col-sm-3">Nest Hoogte</dt>
                    <dd class="col-sm-9">Unsupported Type</dd>

                    <dt class="col-sm-3">Nest Grootte</dt>
                    <dd class="col-sm-9">Unsupported Type</dd>

                    <dt class="col-sm-3">Nest Locatie</dt>
                    <dd class="col-sm-9">Unsupported Type</dd>

                    <dt class="col-sm-3">Nest Type</dt>
                    <dd class="col-sm-9">Type 1</dd>

                    <dt class="col-sm-3">Observatie Datum</dt>
                    <dd class="col-sm-9">2024-04-13 19:10</dd>

                    <dt class="col-sm-3">Cluster ID</dt>
                    <dd class="col-sm-9">3</dd>

                    <dt class="col-sm-3">Gewijzigd door</dt>
                    <dd class="col-sm-9">1</dd>

                    <dt class="col-sm-3">Aangemaakt door</dt>
                    <dd class="col-sm-9">1</dd>

                    <dt class="col-sm-3">Bestreden op</dt>
                    <dd class="col-sm-9">23 januari 2024 09:33</dd>

                    <dt class="col-sm-3">Gemeente</dt>
                    <dd class="col-sm-9">Tienen</dd>
                </dl>
            </div>
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
