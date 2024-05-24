<template>
    <div v-if="selectedObservation">
        <h3>Observatie details</h3>
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
                    <div v-if="reservationStatus" class="mt-3">
                        <span class="text-danger">{{ reservationStatus }}</span>
                    </div>
                </dl>

                <div v-if="canEditAdminFields">
                    <dt class="col-sm-6">Admin Notes</dt>
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ selectedObservation.admin_notes }}</span>
                        <textarea v-else v-model="editableObservation.admin_notes" class="form-control"></textarea>
                    </dd>

                    <dt class="col-sm-6">Observer Sent Email</dt>
                    <dd class="col-sm-9">
                        <span v-if="!isEditing">{{ selectedObservation.observer_received_email ? 'Ja' : 'Nee' }}</span>
                        <input v-else type="checkbox" v-model="editableObservation.observer_received_email" class="form-check-input" />
                    </dd>
                </div>
                <div v-if="isLoggedIn && canEdit">
                    <button class="btn btn-success me-2" v-if="!isEditing" @click="startEdit">Wijzig</button>
                    <button class="btn btn-success me-2" v-if="isEditing" @click="confirmUpdate">Bevestig</button>
                    <button class="btn btn-secondary me-2" v-if="isEditing" @click="cancelEdit">Annuleer</button>
                </div>
                <div v-if="isLoggedIn && canEdit && !isEditing && !selectedObservation.eradication_datetime">
                    <button class="btn btn-success me-2" @click="markObservationAsEradicated">Nest markeren als bestreden</button>
                </div>
                <div v-if="isLoggedIn && canEdit && !isEditing && selectedObservation.eradication_datetime">
                    <button class="btn btn-danger me-2" @click="markObservationAsNotEradicated">Nest markeren als onbestreden</button>
                </div>
                <div v-if="isLoggedIn && canEdit && !isEditing && !selectedObservation.reserved_by">
                    <button class="btn btn-success me-2" @click="reserveObservation">Reserveren</button>
                </div>
                <div v-if="isLoggedIn && canEdit && !isEditing && isUserReserver">
                    <button class="btn btn-danger me-2" @click="cancelReservation">Reservatie annuleren</button>
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
        const canEditAdminFields = computed(() => {
            console.log('canEditAdminFields:', vespaStore.isAdmin);
            return vespaStore.isAdmin;
        });
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
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "observation_datetime",
            "eradication_datetime",
            "admin_notes",
            "observer_received_email"
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

        const reservationStatus = computed(() => {
            const reservationDatetime = selectedObservation.value.reserved_datetime;
            if (reservationDatetime) {
                const reservationTime = new Date(reservationDatetime).getTime();
                const currentTime = new Date().getTime();
                const timeDiff = currentTime - reservationTime;
                const daysDiff = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
                const hoursDiff = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

                if (daysDiff < 5) {
                    let remainingDays = 5 - daysDiff;
                    let remainingHours = 0;

                    if (hoursDiff > 0) {
                        remainingDays--;
                        remainingHours = 24 - hoursDiff;
                    }

                    if (remainingDays > 0 && remainingHours > 0) {
                        return `Nog ${remainingDays}d ${remainingHours}h gereserveerd`;
                    } else if (remainingDays > 0) {
                        return `Nog ${remainingDays}d gereserveerd`;
                    } else if (remainingHours > 0) {
                        return `Nog ${remainingHours}h gereserveerd`;
                    } else {
                        return 'Reservering verlopen';
                    }
                } else {
                    return 'Reservering verlopen';
                }
            } else {
                return null;
            }
        });

        const markObservationAsEradicated = () => {
            if (selectedObservation.value) {
                vespaStore.markObservationAsEradicated(selectedObservation.value.id);
            }
        };

        const markObservationAsNotEradicated = () => {
            if (selectedObservation.value) {
                vespaStore.markObservationAsNotEradicated(selectedObservation.value.id);
            }
        };

        const canMarkAsEradicated = computed(() => {
            return vespaStore.isLoggedIn && vespaStore.canEditObservation(selectedObservation.value);
        });

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

            let patch_response;
            try {
                patch_response = await vespaStore.updateObservation({
                    id: selectedObservation.value.id,
                    ...updatedObservation
                });

                if (patch_response && patch_response.data) {
                    vespaStore.selectedObservation = patch_response.data;
                    vespaStore.isEditing = false;
                }
            } catch (error) {
                console.error('Fout bij het bijwerken van de observatie:', error);
            }
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

        watch(() => vespaStore.selectedObservation, (newVal) => {
            if (newVal) {
                console.log('Selected Observation Changed:', newVal);
                editableObservation.value = { ...newVal };
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
            getEnumLabel,
            reservationStatus,
            canMarkAsEradicated,
            markObservationAsEradicated,
            markObservationAsNotEradicated,
            canEditAdminFields
        };
    },
};
</script>
