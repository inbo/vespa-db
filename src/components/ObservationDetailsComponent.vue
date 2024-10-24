<template>
    <div v-if="selectedObservation">
        <div class="float-end">
            <button type="button" class="btn-close" aria-label="Close" @click="closeDetails"></button>
        </div>
        <div class="container mt-2">
            <text class="text-muted text-uppercase small">Melding <span id="identifier">{{ selectedObservation.id
                    }}</span></text>
            <h3 class="mt-3 mb-3">
                <span id="observation-datetime">{{ selectedObservation.observation_datetime ?
                    formatDate(selectedObservation.observation_datetime) : '' }}</span>,
                <span id="municipality-name">{{ selectedObservation.municipality_name || '' }}</span>
            </h3>

            <div class="d-flex justify-content-between mb-3" id="reservation">
                <button v-if="canReserve && !selectedObservation.reserved_by" class="btn btn-sm btn-outline-primary"
                    @click="reserveObservation">Reserveren</button>
                <span v-if="selectedObservation.reserved_by" class="badge bg-warning">Gereserveerd door {{
                    selectedObservation.reserved_by_first_name }} (nog {{ reservationStatus }})</span>
                <button v-if="(isUserReserver || canEditAdminFields) && selectedObservation.reserved_by"
                    class="btn btn-sm btn-outline-danger" @click="cancelReservation">Reservatie annuleren</button>
            </div>

            <div v-if="isLoggedIn && canEdit" class="mb-3" id="edit">
                <button class="btn btn-sm btn-outline-success" @click="confirmUpdate">Wijzigingen opslaan</button>
            </div>

            <div class="accordion accordion-flush mb-3" id="sections">
                <section class="accordion-item">
                    <h4 class="accordion-header" id="eradication-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#eradication" aria-expanded="false" aria-controls="eradication">
                            <strong>Bestrijding</strong>
                            <span class="badge bg-danger ms-2">{{ selectedObservation.eradication_date ? 'Bestreden'
                                : 'Niet bestreden' }}</span>
                        </button>
                    </h4>
                    <div id="eradication" class="accordion-collapse collapse" aria-labelledby="eradication-header"
                        data-bs-parent="#sections">
                        <div class="accordion-body">
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Datum</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.eradication_date !== undefined"
                                        v-model="editableObservation.eradication_date" type="date" class="form-control"
                                        :readonly="!canEdit" :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Uitvoerder</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.eradicator_name !== undefined"
                                        v-model="editableObservation.eradicator_name" type="text"
                                        placeholder="bv. Rato VZW" class="form-control" :readonly="!canEdit"
                                        :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Duur</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.eradication_duration !== undefined"
                                        v-model="editableObservation.eradication_duration" type="text"
                                        class="form-control" :readonly="!canEdit" placeholder="bv. 0.5 uur"
                                        :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Personeel</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.eradication_persons !== undefined"
                                        v-model="editableObservation.eradication_persons" type="number"
                                        class="form-control" :readonly="!canEdit" placeholder="bv. 2 (personen)"
                                        :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Resultaat</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_result !== undefined"
                                        v-model="editableObservation.eradication_result" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in eradicationResultEnum" :key="value"
                                            :value="value">{{ label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Methode</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_method !== undefined"
                                        v-model="editableObservation.eradication_method" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in eradicationMethodEnum" :key="value"
                                            :value="value">{{ label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Product</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_product !== undefined"
                                        v-model="editableObservation.eradication_product" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in eradicationProductEnum" :key="value"
                                            :value="value">{{ label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Nazorg</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_aftercare !== undefined"
                                        v-model="editableObservation.eradication_aftercare" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in eradicationAfterCareEnum" :key="value"
                                            :value="value">{{ label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Problemen</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_problems !== undefined"
                                        v-model="editableObservation.eradication_problems" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in eradicationProblemsEnum" :key="value"
                                            :value="value">{{ label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Opmerkingen</label>
                                <div class="col-8">
                                    <textarea v-if="selectedObservation.eradication_notes !== undefined"
                                        v-model="editableObservation.eradication_notes" rows="2" class="form-control"
                                        :readonly="!canEdit" :class="{ 'form-control-plaintext': !canEdit }"></textarea>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="accordion-item">
                    <h4 class="accordion-header" id="nest-header">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#nest"
                            aria-expanded="true" aria-controls="nest">
                            <strong>Nest info</strong>
                        </button>
                    </h4>
                    <div id="nest" class="accordion-collapse collapse show" aria-labelledby="nest-header"
                        data-bs-parent="#sections">
                        <div class="accordion-body">
                            <div v-if="selectedObservation.images && selectedObservation.images.length > 0"
                                id="carousel-12040" class="carousel carousel-dark slide carousel-fade mb-2"
                                data-bs-ride="carousel" data-bs-keyboard="false" data-bs-interval="500">
                                <div class="carousel-indicators">
                                    <button v-for="(image, index) in selectedObservation.images" :key="index"
                                        type="button" :data-bs-target="'#carousel-12040'" :data-bs-slide-to="index"
                                        :class="{ active: index === 0 }"
                                        :aria-current="index === 0 ? 'true' : undefined"
                                        :aria-label="'Foto ' + (index + 1)"></button>
                                </div>
                                <div class="carousel-inner">
                                    <div class="carousel-item d-flex w-100 justify-content-center bg-light"
                                        v-for="(image, index) in selectedObservation.images" :key="index"
                                        :class="{ active: index === 0 }">
                                        <img style="max-height: 200px;" :src="image">
                                    </div>
                                </div>
                                <button class="carousel-control-prev" type="button" data-bs-target="#carousel-12040"
                                    data-bs-slide="prev">
                                    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                                    <span class="visually-hidden">Vorige</span>
                                </button>
                                <button class="carousel-control-next" type="button" data-bs-target="#carousel-12040"
                                    data-bs-slide="next">
                                    <span class="carousel-control-next-icon" aria-hidden="true"></span>
                                    <span class="visually-hidden">Volgende</span>
                                </button>
                            </div>

                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Type</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.nest_type !== undefined"
                                        v-model="editableObservation.nest_type" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in nestTypeEnum" :key="value" :value="value">{{
                                            label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Locatie</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.nest_location !== undefined"
                                        v-model="editableObservation.nest_location" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in nestLocationEnum" :key="value" :value="value">
                                            {{ label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Grootte</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.nest_size !== undefined"
                                        v-model="editableObservation.nest_size" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in nestSizeEnum" :key="value" :value="value">{{
                                            label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Hoogte</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.nest_height !== undefined"
                                        v-model="editableObservation.nest_height" class="form-select"
                                        :disabled="!canEdit">
                                        <option v-for="(label, value) in nestHeightEnum" :key="value" :value="value">{{
                                            label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Opmerking</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">{{ selectedObservation.wn_admin_notes }}</p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Bron</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext"><a
                                            :href="'https://waarnemingen.be/observation/' + selectedObservation.wn_id"
                                            target="_blank">Waarnemingen.be</a></p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Validatiestatus</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">{{ selectedObservation.wn_validation_status }}</p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Opmerking validator</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">{{ selectedObservation.wn_notes }}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="accordion-item" v-if="canViewContactInfo">
                    <h4 class="accordion-header" id="contact-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#contact" aria-expanded="false" aria-controls="contact">
                            <strong>Contact info</strong>
                        </button>
                    </h4>
                    <div id="contact" class="accordion-collapse collapse" aria-labelledby="contact-header"
                        data-bs-parent="#sections">
                        <div class="accordion-body">
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Melder</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">{{ selectedObservation.observer_name }}</p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">E-mail</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">{{ selectedObservation.observer_email }}</p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Telefoon</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">{{ selectedObservation.observer_phone_number }}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="accordion-item" v-if="canEditAdminFields">
                    <h4 class="accordion-header" id="admin-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#admin" aria-expanded="false" aria-controls="admin">
                            <strong>Admin sectie</strong>
                        </button>
                    </h4>
                    <div id="admin" class="accordion-collapse collapse" aria-labelledby="admin-header"
                        data-bs-parent="#sections">
                        <div class="accordion-body">
                            <div class="row mb-2">
                                <div class="col-8 offset-4">
                                    <div class="form-check form-switch">
                                        <input v-if="selectedObservation.visible !== undefined"
                                            v-model="editableObservation.visible" class="form-check-input"
                                            type="checkbox" id="visible" :disabled="!canEdit" />
                                        <label class="form-check-label" for="visible">Nest tonen</label>
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Cluster ID</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.wn_cluster_id !== undefined"
                                        v-model="editableObservation.wn_cluster_id" type="text" class="form-control"
                                        :readonly="!canEdit" :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-8 offset-4">
                                    <div class="form-check form-switch">
                                        <input v-if="selectedObservation.observer_received_email !== undefined"
                                            v-model="editableObservation.observer_received_email"
                                            class="form-check-input" type="checkbox" id="observer-got-email"
                                            :disabled="!canEdit" />
                                        <label class="form-check-label" for="observer-got-email">Melder kreeg
                                            e-mail</label>
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-8 offset-4">
                                    <div class="form-check form-switch">
                                        <input v-if="selectedObservation.public_domain !== undefined"
                                            v-model="editableObservation.public_domain" class="form-check-input"
                                            type="checkbox" id="public-domain" :disabled="!canEdit" />
                                        <label class="form-check-label" for="public-domain">Nest op publiek
                                            terrein</label>
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Opmerkingen</label>
                                <div class="col-8">
                                    <textarea v-if="selectedObservation.admin_notes !== undefined"
                                        v-model="editableObservation.admin_notes" rows="2" class="form-control"
                                        :readonly="!canEdit" :class="{ 'form-control-plaintext': !canEdit }"></textarea>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>

            <p class="mb-3 text-muted small" id="metadata">
                Aangemaakt op <span class="created-datetime">{{ selectedObservation.created_datetime ?
                    formatDate(selectedObservation.created_datetime) : '' }}</span> door <span class="created-by">{{
                        selectedObservation.created_by_first_name || '' }}</span>, gewijzigd op <span
                    class="modified-datetime">{{ selectedObservation.modified_datetime ?
                        formatDate(selectedObservation.modified_datetime) : '' }}</span> door <span class="modified-by">{{
                        selectedObservation.modified_by_first_name || '' }}</span>.
            </p>
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
        const isEditing = ref(false);
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const canEdit = computed(() => isLoggedIn.value && vespaStore.canEditObservation(selectedObservation.value));
        const canEditAdminFields = computed(() => isLoggedIn.value && vespaStore.isAdmin);

        const editableObservation = ref({});

        const canReserve = computed(() => {
            return isLoggedIn.value && (!selectedObservation.value?.reserved_by || selectedObservation.value.reserved_by === vespaStore.user.username);
        });

        const isUserReserver = computed(() => {
            return selectedObservation.value?.reserved_by === vespaStore.user.id;
        });

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

        const eradicationResultEnum = {
            "successful": "Succesvol behandeld",
            "unsuccessful": "Niet succesvol behandeld",
            "untreated": "Niet behandeld",
            "unknown": "Onbekend"
        };

        const eradicationProductEnum = {
            "permas_d": "Permas-D",
            "vloeibare_stikstof": "vloeibare stikstof",
            "vespa_ficam_d": "Vespa Ficam D",
            "topscore_pal": "Topscore_PAL",
            "diatomeeenaarde": "diatomeeenaarde",
            "andere": "andere"
        };

        const eradicationMethodEnum = {
            "diepvries": "Diepvries",
            "telescoopsteel": "Telescoopsteel",
            "doos": "Doos",
            "vloeistofverstuiver": "Vloeistofverstuiver",
            "poederverstuiver": "Poederverstuiver"
        };

        const eradicationAfterCareEnum = {
            "nest_volledig_verwijderd": "Nest volledig verwijderd",
            "nest_gedeeltelijk_verwijderd": "Nest gedeeltelijk verwijderd",
            "nest_laten_hangen": "Nest laten hangen"
        };

        const eradicationProblemsEnum = {
            "steken": "Steken",
            "nest_gevallen": "Nest gevallen",
            "duizeligheid": "Duizeligheid",
            "gif_spuiten": "Gif spuiten",
        };

        const editableFields = [
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "observation_datetime",
            "eradication_date",
            "admin_notes",
            "observer_received_email",
            "eradicator_name",
            "eradication_duration",
            "eradication_persons",
            "eradication_result",
            "eradication_method",
            "eradication_product",
            "eradication_aftercare",
            "eradication_problems",
            "eradication_notes",
            "visible",
            "wn_cluster_id",
            "public_domain"
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
                month: 'long',
                day: 'numeric'
            }).format(date);
        };

        const formatDateTime = (isoString, defaultValue = "") => {
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
            const reservationDatetime = selectedObservation.value?.reserved_datetime;
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
                        return `${remainingDays} dagen ${remainingHours} uren`;
                    } else if (remainingDays > 0) {
                        return `${remainingDays} dagen`;
                    } else if (remainingHours > 0) {
                        return `${remainingHours} uren`;
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

        const closeDetails = () => {
            emit('closeDetails');
            vespaStore.isDetailsPaneOpen = false;
        };

        const startEdit = () => {
            isEditing.value = true;
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_date = formatToDatetimeLocal(selectedObservation.value.eradication_date);
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
                    isEditing.value = false;
                }
            } catch (error) {
                console.error('Fout bij het bijwerken van de observatie:', error);
            }
        };

        const cancelEdit = () => {
            isEditing.value = false;
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_date = formatToDatetimeLocal(selectedObservation.value.eradication_date);
            }
        };

        const canViewContactInfo = computed(() => {
            if (vespaStore.isAdmin) {
                return true;
            }
            if (!vespaStore.user.personal_data_access) {
                return false;
            }
            console.log('user municipalities:', vespaStore.user.municipalities);
            console.log('observation municipality:', selectedObservation.value?.municipality_name);
            const userMunicipalities = vespaStore.user.municipalities;
            const observationMunicipality = selectedObservation.value?.municipality_name;
            return userMunicipalities.includes(observationMunicipality);
        });

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
                editableObservation.value = { ...newVal };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_date = formatToDatetimeLocal(selectedObservation.value.eradication_date);
            }
        }, { immediate: true });

        return {
            selectedObservation,
            isEditing,
            isLoggedIn,
            canEdit,
            canEditAdminFields,
            canReserve,
            isUserReserver,
            editableObservation,
            nestHeightEnum,
            nestSizeEnum,
            nestLocationEnum,
            nestTypeEnum,
            eradicationResultEnum,
            eradicationMethodEnum,
            eradicationAfterCareEnum,
            eradicationProblemsEnum,
            reservationStatus,
            closeDetails,
            startEdit,
            confirmUpdate,
            cancelEdit,
            reserveObservation,
            cancelReservation,
            formatDate,
            getEnumLabel,
            eradicationProductEnum,
            canViewContactInfo
        };
    }
};
</script>
