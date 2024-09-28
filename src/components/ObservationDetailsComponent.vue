<template>
    <div v-if="selectedObservation">
        <div class="float-end">
            <button type="button" class="btn-close" aria-label="Close" @click="closeDetails"></button>
        </div>
        <div class="container mt-2">
            <text class="text-muted text-uppercase small">
                Melding <span id="identifier">{{ selectedObservation.id }}</span>
                <template v-if="selectedObservation.wn_id">
                    (WAARNEMING
                    <a :href="'https://waarnemingen.be/observation/' + selectedObservation.wn_id" target="_blank">{{
                        selectedObservation.wn_id }}</a>)
                </template>
            </text>
            <h3 class="mt-3 mb-3">
                <span id="observation-datetime">{{ selectedObservation.observation_datetime ?
                    formatDate(selectedObservation.observation_datetime) : '' }}</span>,
                <span id="municipality-name">{{ selectedObservation.municipality_name || '' }}</span>
            </h3>

            <div class="d-flex justify-content-between mb-3" id="reservation">
                <button v-if="canReserve && isAuthorizedToReserve && !selectedObservation.reserved_by"
                    class="btn btn-sm btn-outline-primary" @click="reserveObservation">
                    Reserveren
                </button>
                <span v-if="selectedObservation.reserved_by" class="badge bg-warning">Gereserveerd door {{
                    selectedObservation.reserved_by_first_name }} (nog {{ reservationStatus }})</span>
                <button v-if="(isUserReserver || canEditAdminFields) && selectedObservation.reserved_by"
                    class="btn btn-sm btn-outline-danger" @click="cancelReservation">Reservatie annuleren</button>
            </div>

            <div v-if="isLoggedIn && canEdit" class="mb-3" id="edit">
                <button class="btn btn-sm btn-outline-success" @click="confirmUpdate">Wijzigingen opslaan</button>
            </div>
            <div v-if="successMessage" class="alert alert-success alert-dismissible fade show" role="alert">
                {{ successMessage }}
            </div>
            <div v-if="errorMessage" class="alert alert-danger alert-dismissible fade show" role="alert">
                {{ errorMessage }}
            </div>

            <div class="accordion accordion-flush mb-3" id="sections">
                <section class="accordion-item">
                    <h4 class="accordion-header" id="eradication-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#eradication" aria-expanded="false" aria-controls="eradication">
                            <strong>Bestrijding</strong>
                            <span :class="['badge ms-2', eradicationStatusClass]">{{ eradicationStatusText }}</span>
                        </button>
                    </h4>
                    <div id="eradication" class="accordion-collapse collapse" aria-labelledby="eradication-header"
                        data-bs-parent="#sections">
                        <div class="accordion-body">
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Resultaat</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_result !== undefined"
                                        v-model="editableObservation.eradication_result" class="form-select"
                                        :class="{ 'is-invalid': eradicationResultError }" :disabled="!canEdit">
                                        <option :value="null">Geen</option>
                                        <option v-for="(label, value) in eradicationResultEnum" :key="value"
                                            :value="value">{{ label
                                            }}</option>
                                    </select>
                                    <div v-if="eradicationResultError" class="invalid-feedback">
                                        {{ eradicationResultError }}
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Datum</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.eradication_date !== undefined"
                                        v-model="editableObservation.eradication_date" type="date" class="form-control"
                                        :readonly="!canEdit" :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
                                <label class="col-4 col-form-label">Uitvoerder</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.eradicator_name !== undefined"
                                        v-model="editableObservation.eradicator_name" type="text"
                                        placeholder="bv. Rato VZW" class="form-control" :readonly="!canEdit"
                                        :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
                                <label class="col-4 col-form-label">Duur</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.eradication_duration !== undefined"
                                        v-model="editableObservation.eradication_duration" type="text"
                                        class="form-control" :readonly="!canEdit" placeholder="bv. 30 (min)"
                                        :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
                                <label class="col-4 col-form-label">Personeel</label>
                                <div class="col-8">
                                    <input v-if="selectedObservation.eradication_persons !== undefined"
                                        v-model="editableObservation.eradication_persons" type="number"
                                        class="form-control" :readonly="!canEdit" placeholder="bv. 2 (personen)"
                                        :class="{ 'form-control-plaintext': !canEdit }" />
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
                                <label class="col-4 col-form-label">Methode</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_method !== undefined"
                                        v-model="editableObservation.eradication_method" class="form-select"
                                        :disabled="!canEdit">
                                        <option :value="null">Geen</option>
                                        <option v-for="(label, value) in eradicationMethodEnum" :key="value"
                                            :value="value">{{ label
                                            }}</option>
                                    </select>
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
                                <label class="col-4 col-form-label">Product</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_product !== undefined"
                                        v-model="editableObservation.eradication_product" class="form-select"
                                        :disabled="!canEdit">
                                        <option :value="null">Geen</option>
                                        <option v-for="(label, value) in eradicationProductEnum" :key="value"
                                            :value="value">{{
                                                label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
                                <label class="col-4 col-form-label">Nazorg</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_aftercare !== undefined"
                                        v-model="editableObservation.eradication_aftercare" class="form-select"
                                        :disabled="!canEdit">
                                        <option :value="null">Geen</option>
                                        <option v-for="(label, value) in eradicationAfterCareEnum" :key="value"
                                            :value="value">{{
                                                label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
                                <label class="col-4 col-form-label">Problemen</label>
                                <div class="col-8">
                                    <select v-if="selectedObservation.eradication_problems !== undefined"
                                        v-model="editableObservation.eradication_problems" class="form-select"
                                        :disabled="!canEdit">
                                        <option :value="null">Geen</option>
                                        <option v-for="(label, value) in eradicationProblemsEnum" :key="value"
                                            :value="value">{{
                                                label }}</option>
                                    </select>
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
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
                                        <option :value="null">Geen</option>
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
                                        <option :value="null">Geen</option>
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
                                        <option :value="null">Geen</option>
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
                                        <option :value="null">Geen</option>
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
                                    <p class="form-control-plaintext">
                                        <a v-if="selectedObservation.wn_id"
                                            :href="'https://waarnemingen.be/observation/' + selectedObservation.wn_id"
                                            target="_blank">Waarnemingen.be</a>
                                        <span v-else>{{ selectedObservation.source }}</span>
                                    </p>
                                </div>
                            </div>
                            <div>
                                <div class="row mb-2">
                                    <label class="col-4 col-form-label">Validatiestatus</label>
                                    <div class="col-8">
                                        <p class="form-control-plaintext">{{ selectedObservation.wn_validation_status }}
                                        </p>
                                    </div>
                                </div>
                                <div v-if="isLoggedIn" class="row mb-2">
                                    <label class="col-4 col-form-label">Opmerking validator</label>
                                    <div class="col-8">
                                        <p class="form-control-plaintext">{{ selectedObservation.wn_notes }}</p>
                                    </div>
                                </div>
                            </div>
                            <div v-if="isLoggedIn" class="row mb-2">
                                <div class="col-8 offset-4">
                                    <div class="form-check form-switch">
                                        <input v-if="selectedObservation.public_domain !== undefined"
                                            v-model="editableObservation.public_domain" class="form-check-input"
                                            type="checkbox" id="public-domain" :disabled="!isLoggedIn" />
                                        <label class="form-check-label" for="public-domain">Nest op publiek
                                            terrein</label>
                                    </div>
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
                                    <input v-model="editableObservation.wn_cluster_id" type="text" class="form-control"
                                        readonly />
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
                    class="modified-datetime">{{
                        selectedObservation.modified_datetime ?
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
    emits: ['closeDetails', 'updateMarkerColor'],
    setup(props, { emit }) {
        const vespaStore = useVespaStore();
        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = ref(false);
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const canEdit = computed(() => isLoggedIn.value && vespaStore.canEditObservation(selectedObservation.value));
        const canEditAdminFields = computed(() => isLoggedIn.value && vespaStore.isAdmin);
        const successMessage = ref('');
        const errorMessage = ref('');
        const eradicationResultError = ref('');
        const editableObservation = ref({});

        const isAuthorizedToReserve = computed(() => {
            if (vespaStore.isAdmin) return true;
            const observationMunicipality = selectedObservation.value?.municipality_name;
            return vespaStore.userMunicipalities.includes(observationMunicipality);
        });

        const isObservationSuccessful = computed(() => {
            return selectedObservation.value?.eradication_result === 'successful';
        });

        const canReserve = computed(() => {
            return isLoggedIn.value &&
                (!selectedObservation.value?.reserved_by || selectedObservation.value.reserved_by === vespaStore.user.username) &&
                !isObservationSuccessful.value;
        });

        const resetEditableObservation = () => {
            editableObservation.value = JSON.parse(JSON.stringify(selectedObservation.value || {}));
        };

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
            "actief_embryonaal_nest": "Actief embryonaal nest",
            "actief_primair_nest": "Actief primair nest",
            "actief_secundair_nest": "Actief secundair nest",
            "inactief_leeg_nest": "Inactief/leeg nest",
        };

        const eradicationResultEnum = {
            "successful": "Succesvol behandeld",
            "unsuccessful": "Niet succesvol behandeld",
            "untreated": "Niet behandeld want andere soort",
            "untreatable": "Onbehandelbaar (bv. te hoog, inactief)",
            "unknown": "Onbekend"
        };

        const eradicationProductEnum = {
            "permas_d": "Permas-D",
            "vloeibare_stikstof": "Vloeibare stikstof",
            "ficam_d": "Ficam D",
            "topscore_pal": "Topscore PAL",
            "diatomeeenaarde": "Diatomeeënaarde",
            "ether_aceton_ethyl_acetaat": "Ether, aceton of ethylacetaat",
            "vespa": "Vespa",
            "andere": "Andere"
        };

        const eradicationMethodEnum = {
            "diepvries": "Diepvries",
            "telescoopsteel": "Telescoopsteel",
            "doos": "Doos",
            "vloeistofverstuiver": "Vloeistofverstuiver",
            "poederverstuiver": "Poederverstuiver",
            "stofzuiger": "Stofzuiger",
        };

        const eradicationAfterCareEnum = {
            "nest_volledig_verwijderd": "Nest volledig verwijderd",
            "nest_gedeeltelijk verwijderd": "Nest gedeeltelijk verwijderd",
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
            "public_domain",
            "eradication_aftercare",
        ];

        const eradicationStatusText = computed(() => {
            const result = selectedObservation.value?.eradication_result;
            if (result === 'successful') {
                return 'Bestreden';
            } else {
                return 'Niet bestreden';
            }
        });

        const eradicationStatusClass = computed(() => {
            const result = selectedObservation.value?.eradication_result;
            if (result === 'successful') {
                return 'bg-success';
            } else {
                return 'bg-danger';
            }
        });

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

        const formatToDatetimeLocal = (isoString) => {
            if (!isoString) return '';
            const date = new Date(isoString);
            return date.toISOString().slice(0, 16);
        };

        const formatToDate = (isoString) => {
            if (!isoString) return '';
            const date = new Date(isoString);
            const year = date.getFullYear();
            const month = ('0' + (date.getMonth() + 1)).slice(-2);
            const day = ('0' + date.getDate()).slice(-2);
            return `${year}-${month}-${day}`;
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
            resetEditableObservation();
            errorMessage.value = '';
            eradicationResultError.value = '';
        };

        const startEdit = () => {
            isEditing.value = true;
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_date = formatToDate(newVal.eradication_date);
            }
        };

        const confirmUpdate = async () => {
            try {
                // Check if any eradication fields are filled
                const eradicationFields = [
                    'eradication_date', 'eradicator_name', 'eradication_duration',
                    'eradication_persons', 'eradication_method', 'eradication_aftercare',
                    'eradication_problems', 'eradication_notes', 'eradication_product'
                ];
                const hasEradicationData = eradicationFields.some(field => editableObservation.value[field]);

                if (hasEradicationData && !editableObservation.value.eradication_result) {
                    eradicationResultError.value = 'Resultaat is verplicht wanneer andere bestrijdingsgegevens zijn ingevuld.';
                    throw new Error('Validation failed');
                }
                errorMessage.value = '';
                eradicationResultError.value = '';

                await vespaStore.updateObservation(editableObservation.value);
                resetEditableObservation();
            } catch (error) {
                if (error.message !== 'Validation failed') {
                    errorMessage.value = 'Er is een fout opgetreden bij het opslaan van de wijzigingen.';
                }
                console.error('Error updating observation:', error);
            }
        };
        const cancelEdit = () => {
            isEditing.value = false;
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_date = formatToDate(selectedObservation.value.eradication_date);
            }
        };

        const canViewContactInfo = computed(() => {
            if (vespaStore.isAdmin) {
                return true;
            }
            if (!vespaStore.user.personal_data_access) {
                return false;
            }
            const userMunicipalities = vespaStore.user.municipalities;
            const observationMunicipality = selectedObservation.value?.municipality_name;
            return userMunicipalities.includes(observationMunicipality);
        });

        const reserveObservation = async () => {
            if (vespaStore.user.reservation_count < 50) {
                await vespaStore.reserveObservation(selectedObservation.value);
            } else {
                errorMessage.value = 'U heeft het maximum aantal reserveringen bereikt.';
                setTimeout(() => {
                    errorMessage.value = '';
                }, 4000);
            }
        };

        const cancelReservation = async () => {
            await vespaStore.cancelReservation(selectedObservation.value);
        };

        const clearSuccessMessage = () => {
            successMessage.value = '';
        };

        watch(() => vespaStore.selectedObservation, (newVal) => {
            if (newVal) {
                editableObservation.value = { ...newVal };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_date = formatToDate(selectedObservation.value.eradication_date);
            }
        }, { immediate: true });
        watch(selectedObservation, resetEditableObservation, { immediate: true });

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
            canViewContactInfo,
            isAuthorizedToReserve,
            eradicationStatusText,
            eradicationStatusClass,
            successMessage,
            clearSuccessMessage,
            isObservationSuccessful,
            errorMessage,
            editableObservation,
            errorMessage,
            eradicationResultError,
        };
    }
};
</script>