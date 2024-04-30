<template>
    <div v-if="selectedObservation">
        <div class="card">
            <div class="card-body">
                <dl class="row">
                    <dt class="col-sm-6">Aangemaakt op</dt>
                    <dd class="col-sm-9">{{ formatDate(selectedObservation.created_datetime) }}</dd>

                    <dt class="col-sm-6">Laatst gewijzigd</dt>
                    <dd class="col-sm-9">{{ formatDate(selectedObservation.modified_datetime) }}</dd>

                    <dt class="col-sm-6">Bron</dt>
                    <dd class="col-sm-9">{{ selectedObservation.source }}</dd>

                    <dt class="col-sm-6">Species</dt>
                    <dd class="col-sm-9">{{ selectedObservation.species }}</dd>

                    <dt class="col-sm-6">Nest Hoogte</dt>
                    <dd class="col-sm-9">{{ selectedObservation.nest_height }}</dd>

                    <dt class="col-sm-6">Nest Grootte</dt>
                    <dd class="col-sm-9">{{ selectedObservation.nest_size }}</dd>

                    <dt class="col-sm-6">Nest Locatie</dt>
                    <dd class="col-sm-9">{{ selectedObservation.nest_location }}</dd>

                    <dt class="col-sm-6">Nest Type</dt>
                    <dd class="col-sm-9">{{ selectedObservation.nest_type }}</dd>

                    <dt class="col-sm-6">Observatie Datum</dt>
                    <dd class="col-sm-9">{{ formatDate(selectedObservation.observation_datetime) }}</dd>

                    <dt class="col-sm-6">Cluster ID</dt>
                    <dd class="col-sm-9">{{ selectedObservation.wn_cluster_id }}</dd>

                    <dt class="col-sm-6">Gewijzigd door</dt>
                    <dd class="col-sm-9">{{ selectedObservation.modified_by }}</dd>

                    <dt class="col-sm-6">Aangemaakt door</dt>
                    <dd class="col-sm-9">{{ selectedObservation.created_by }}</dd>

                    <dt class="col-sm-6">Bestreden op</dt>
                    <dd class="col-sm-9">{{ formatDate(selectedObservation.eradication_datetime, 'Onbestreden') }}</dd>

                    <dt class="col-sm-6">Gemeente</dt>
                    <dd class="col-sm-9">{{ selectedObservation.municipality_name }}</dd>
                    <div>
                        <button v-if="isLoggedIn && canEdit && !isEditing" class="btn btn-success me-2"
                            @click="startEdit">Wijzig</button>
                        <button v-if="isLoggedIn && canEdit && !isEditing && !selectedObservation.reserved_by && canReserve"
                            class="btn btn-success me-2" @click="reserveObservation">Reserveren</button>
                        <button v-if="isUserReserver" class="btn btn-danger me-2" @click="cancelReservation">Reservatie
                            annuleren</button>
                        <button v-if="isEditing && canEdit" class="btn btn-success me-2" @click="confirmUpdate">Bevestig</button>
                        <button v-if="isEditing && canEdit" class="btn btn-secondary" @click="cancelEdit">Annuleer</button>
                    </div>
                </dl>
            </div>
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
        const canReserve = computed(() => vespaStore.user.reservation_count < 50);

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

        const formatDate = (isoString, defaultValue = "") => {
            if (!isoString) {
                return defaultValue;
            }
            const date = new Date(isoString);
            if (isNaN(date.getTime())) {
                return defaultValue;
            }
            return new Intl.DateTimeFormat('nl-NL', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        };
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
            isUserReserver,
            formatDate,
            canReserve
        };
    },
};
</script>
