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
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ selectedObservation.species }}</span>
                        <input v-else v-model="editableObservation.species" class="form-control" />
                    </dd>

                    <dt class="col-sm-6">Nest Hoogte</dt>
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ getEnumLabel(nestHeightEnum, selectedObservation.nest_height) }}</span>
                        <select v-else v-model="editableObservation.nest_height" class="form-control">
                            <option v-for="(label, value) in nestHeightEnum" :key="value" :value="value">{{ label }}</option>
                        </select>
                    </dd>

                    <dt class="col-sm-6">Nest Grootte</dt>
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ getEnumLabel(nestSizeEnum, selectedObservation.nest_size) }}</span>
                        <select v-else v-model="editableObservation.nest_size" class="form-control">
                            <option v-for="(label, value) in nestSizeEnum" :key="value" :value="value">{{ label }}</option>
                        </select>
                    </dd>

                    <dt class="col-sm-6">Nest Locatie</dt>
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ getEnumLabel(nestLocationEnum, selectedObservation.nest_location) }}</span>
                        <select v-else v-model="editableObservation.nest_location" class="form-control">
                            <option v-for="(label, value) in nestLocationEnum" :key="value" :value="value">{{ label }}</option>
                        </select>
                    </dd>

                    <dt class="col-sm-6">Nest Type</dt>
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ getEnumLabel(nestTypeEnum, selectedObservation.nest_type) }}</span>
                        <select v-else v-model="editableObservation.nest_type" class="form-control">
                            <option v-for="(label, value) in nestTypeEnum" :key="value" :value="value">{{ label }}</option>
                        </select>
                    </dd>

                    <dt class="col-sm-6">Observatie Datum</dt>
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ formatDate(selectedObservation.observation_datetime) }}</span>
                        <input v-else v-model="editableObservation.observation_datetime" type="datetime-local" class="form-control" />
                    </dd>

                    <dt class="col-sm-6">Cluster ID</dt>
                    <dd class="col-sm-9">{{ selectedObservation.wn_cluster_id }}</dd>

                    <dt class="col-sm-6">Gewijzigd door</dt>
                    <dd class="col-sm-9">{{ selectedObservation.modified_by }}</dd>

                    <dt class="col-sm-6">Aangemaakt door</dt>
                    <dd class="col-sm-9">{{ selectedObservation.created_by }}</dd>

                    <dt class="col-sm-6">Bestreden op</dt>
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ formatDate(selectedObservation.eradication_datetime, 'Onbestreden') }}</span>
                        <input v-else v-model="editableObservation.eradication_datetime" type="datetime-local" class="form-control" />
                    </dd>

                    <dt class="col-sm-6">Gemeente</dt>
                    <dd class="col-sm-9">{{ selectedObservation.municipality_name }}</dd>
                </dl>

                <div>
                    <button v-if="isLoggedIn && canEdit && !isEditing" class="btn btn-success me-2" @click="startEdit">Wijzig</button>
                    <button v-if="isLoggedIn && canEdit && !isEditing && !selectedObservation.reserved_by && canReserve" class="btn btn-success me-2" @click="reserveObservation">Reserveren</button>
                    <button v-if="isUserReserver" class="btn btn-danger me-2" @click="cancelReservation">Reservatie annuleren</button>
                    <button v-if="isEditing && canEdit" class="btn btn-success me-2" @click="confirmUpdate">Bevestig</button>
                    <button v-if="isEditing && canEdit" class="btn btn-secondary" @click="cancelEdit">Annuleer</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { useVespaStore } from '@/stores/vespaStore';
import { computed, ref, watch } from 'vue';

export default {
    emits: ['closeDetails'],
    setup(props, { emit }) {
        const vespaStore = useVespaStore();
        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = computed(() => vespaStore.isEditing);
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const canEdit = computed(() => vespaStore.canEditObservation(selectedObservation.value));
        const isUserReserver = computed(() => vespaStore.isLoggedIn && vespaStore.selectedObservation.reserved_by === vespaStore.user.id);
        const canReserve = computed(() => vespaStore.user.reservation_count < 50);

        const editableObservation = ref({});

        const nestHeightEnum = {
            "lager_dan_4_meter": "Lager dan 4 meter",
            "hoger_dan_4_meter": "Hoger dan 4 meter"
        };

        const nestSizeEnum = {
            "kleiner_dan_25_cm": "Kleiner dan 25 cm",
            "groter_dan_25_cm": "Groter dan 25 cm"
        };

        const nestLocationEnum = {
            "buiten_onbedekt_op_gebouw": "Buiten, onbedekt op gebouw",
            "buiten_onbedekt_in_boom_of_struik": "Buiten, onbedekt in boom of struik",
            "buiten_maar_overdekt_door_constructie": "Buiten, maar overdekt door constructie",
            "buiten_natuurlijk_overdekt": "Buiten, natuurlijk overdekt",
            "binnen_in_gebouw_of_constructie": "Binnen, in gebouw of constructie"
        };

        const nestTypeEnum = {
            "actief_embryonaal_nest": "actief embryonaal nest",
            "actief_primair_nest": "actief primair nest",
            "actief_secundair_nest": "actief secundair nest",
            "inactief_leeg_nest": "inactief/leeg nest",
            "potentieel_nest": "potentieel nest"
        };

        const editableFields = [
            "species",
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "observation_datetime",
            "eradication_datetime",
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

        const formatToDatetimeLocal = (isoString) => {
            if (!isoString) return '';
            const date = new Date(isoString);
            return date.toISOString().slice(0, 16);
        };

        const getEnumLabel = (enumObject, value) => {
            return enumObject[value] || value;
        };

        const closeDetails = () => {
            emit('closeDetails');
            vespaStore.isDetailsPaneOpen = false;
        };

        const startEdit = () => {
            vespaStore.isEditing = true;
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_datetime = formatToDatetimeLocal(selectedObservation.value.eradication_datetime);
            }
        };

        const confirmUpdate = async () => {
            const updatedObservation = {};

            editableFields.forEach(field => {
                updatedObservation[field] = editableObservation.value[field];
            });

            await vespaStore.updateObservation({
                id: selectedObservation.value.id,
                ...updatedObservation
            });
            vespaStore.isEditing = false;
        };

        const cancelEdit = () => {
            vespaStore.isEditing = false;
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_datetime = formatToDatetimeLocal(selectedObservation.value.eradication_datetime);
            }
        };

        const reserveObservation = async () => {
            if (!selectedObservation.value.reserved_by) {
                await vespaStore.reserveObservation(selectedObservation.value);
            } else {
                alert('Deze observatie is al gereserveerd.');
            }
        };

        const cancelReservation = async () => {
            await vespaStore.cancelReservation(selectedObservation.value);
        };

        watch(selectedObservation, () => {
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_datetime = formatToDatetimeLocal(selectedObservation.value.eradication_datetime);
            }
        }, { immediate: true });

        return {
            selectedObservation,
            isEditing,
            isLoggedIn,
            startEdit,
            confirmUpdate,
            cancelEdit,
            closeDetails,
            reserveObservation,
            canEdit,
            cancelReservation,
            isUserReserver,
            formatDate,
            editableObservation,
            canReserve,
            nestHeightEnum,
            nestSizeEnum,
            nestLocationEnum,
            nestTypeEnum,
            getEnumLabel
        };
    },
};
</script>
