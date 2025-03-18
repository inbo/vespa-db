<template>
    <div v-if="selectedObservation">
        <div class="float-end">
            <button type="button" class="btn-close" aria-label="Close" @click="closeDetails"></button>
        </div>
        <div class="container mt-2">
            <text class="text-muted text-uppercase small">
                Melding <span id="identifier">{{ selectedObservation.id }}</span>
                <template v-if="sourceUrl">
                    (<a :href="sourceUrl" target="_blank">{{ selectedObservation.source }}</a>)
                </template>
                <template v-else>
                    {{ selectedObservation.source }}
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

            <div v-if="canViewRestrictedFields" class="mb-3" id="edit">
                <button class="btn btn-sm" :class="isEditing ? 'btn-outline-success' : 'btn-outline-primary'" @click="toggleEditMode">
                    {{ isEditing ? 'Wijzigingen opslaan' : 'Bewerken' }}
                </button>
                <button v-if="isEditing" class="btn btn-sm btn-outline-secondary ms-2" @click="cancelEdit">
                    Annuleren
                </button>
            </div>
            <div v-if="successMessage" class="alert alert-success alert-dismissible fade show" role="alert">
                {{ successMessage }}
                <button type="button" class="btn-close" @click="clearSuccessMessage" aria-label="Close"></button>
            </div>
            <div v-if="errorMessage" class="alert alert-danger alert-dismissible fade show" role="alert">
                {{ errorMessage }}
                <button type="button" class="btn-close" @click="errorMessage = ''" aria-label="Close"></button>
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
                                    <template v-if="isEditing && canEdit">
                                        <select v-model="editableObservation.eradication_result" class="form-select"
                                            :class="{ 'is-invalid': eradicationResultError }">
                                            <option :value="null">Geen</option>
                                            <option v-for="(label, value) in eradicationResultEnum" :key="value" :value="value">
                                                {{ label }}
                                            </option>
                                        </select>
                                        <div v-if="eradicationResultError" class="invalid-feedback">
                                            {{ eradicationResultError }}
                                        </div>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradication_result ? 
                                               eradicationResultEnum[selectedObservation.eradication_result] : 'Geen' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Datum</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <input v-model="editableObservation.eradication_date" type="date" class="form-control" />
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradication_date ? 
                                               formatDate(selectedObservation.eradication_date) : '-' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Uitvoerder</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <input v-model="editableObservation.eradicator_name" type="text"
                                            placeholder="bv. Rato VZW" class="form-control" />
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradicator_name || '-' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Duur</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <input v-model="editableObservation.eradication_duration" type="text"
                                            placeholder="bv. 30 (min)" class="form-control" />
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradication_duration || '-' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Personeel</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <input v-model="editableObservation.eradication_persons" type="number"
                                            placeholder="bv. 2 (personen)" class="form-control" />
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradication_persons || '-' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Methode</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <select v-model="editableObservation.eradication_method" class="form-select">
                                            <option :value="null">Geen</option>
                                            <option v-for="(label, value) in eradicationMethodEnum" :key="value" :value="value">
                                                {{ label }}
                                            </option>
                                        </select>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradication_method ? 
                                               eradicationMethodEnum[selectedObservation.eradication_method] : '-' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Product</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <select v-model="editableObservation.eradication_product" class="form-select">
                                            <option :value="null">Geen</option>
                                            <option v-for="(label, value) in eradicationProductEnum" :key="value" :value="value">
                                                {{ label }}
                                            </option>
                                        </select>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradication_product ? 
                                               eradicationProductEnum[selectedObservation.eradication_product] : '-' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Nazorg</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <select v-model="editableObservation.eradication_aftercare" class="form-select">
                                            <option :value="null">Geen</option>
                                            <option v-for="(label, value) in eradicationAfterCareEnum" :key="value" :value="value">
                                                {{ label }}
                                            </option>
                                        </select>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradication_aftercare ? 
                                               eradicationAfterCareEnum[selectedObservation.eradication_aftercare] : '-' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Problemen</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <select v-model="editableObservation.eradication_problems" class="form-select">
                                            <option :value="null">Geen</option>
                                            <option v-for="(label, value) in eradicationProblemsEnum" :key="value" :value="value">
                                                {{ label }}
                                            </option>
                                        </select>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.eradication_problems ? 
                                               eradicationProblemsEnum[selectedObservation.eradication_problems] : '-' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Opmerkingen</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <textarea v-model="editableObservation.eradication_notes" rows="2" class="form-control"></textarea>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">{{ selectedObservation.eradication_notes || '-' }}</p>
                                    </template>
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
                                    <p class="form-control-plaintext">
                                        {{ selectedObservation.nest_type ? nestTypeEnum[selectedObservation.nest_type] :
                                            'Geen' }}
                                    </p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Locatie</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">
                                        {{ selectedObservation.nest_location ?
                                            nestLocationEnum[selectedObservation.nest_location] :
                                            'Geen' }}
                                    </p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Grootte</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">
                                        {{ selectedObservation.nest_size ? nestSizeEnum[selectedObservation.nest_size] :
                                            'Geen' }}
                                    </p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Hoogte</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">
                                        {{ selectedObservation.nest_height ?
                                            nestHeightEnum[selectedObservation.nest_height] :
                                            'Geen' }}
                                    </p>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Bron</label>
                                <div class="col-8">
                                    <p class="form-control-plaintext">
                                    <template v-if="sourceUrl">
                                        <a :href="sourceUrl" target="_blank">{{ selectedObservation.source }}</a>
                                    </template>
                                    <template v-else>
                                        {{ selectedObservation.source }}
                                    </template>
                                    </p>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <label class="col-4 col-form-label">Extra info</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <multiselect
                                            v-model="selectedExtras"
                                            :options="extrasOptions"
                                            :multiple="true"
                                            track-by="value"
                                            label="label"
                                            placeholder="Selecteer opties"
                                            :close-on-select="false"
                                            :searchable="false"
                                            :select-label="''"
                                            :deselect-label="''"
                                            :selected-label="''">
                                            <template #option="{ option }">
                                                <div class="multiselect-option" :class="{ 'is-selected': selectedExtras.some(extra => extra.value === option.value) }">
                                                    <span class="option-label">{{ option.label }}</span>
                                                </div>
                                            </template>
                                            <template #tag="{ option, remove }">
                                                <span class="multiselect-tag">
                                                    {{ option.label }}
                                                    <button 
                                                        type="button" 
                                                        class="remove-tag" 
                                                        @click="remove(option)"
                                                        aria-label="Remove option">×</button>
                                                </span>
                                            </template>
                                        </multiselect>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            <span v-if="selectedObservation.queen_present">Koningin aanwezig</span>
                                            <span v-if="selectedObservation.queen_present && selectedObservation.moth_present">, </span>
                                            <span v-if="selectedObservation.moth_present">Mot aanwezig</span>
                                            <span v-if="!selectedObservation.queen_present && !selectedObservation.moth_present">-</span>
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div>
                                <div class="row mb-2">
                                    <label class="col-4 col-form-label">Validatie</label>
                                    <div class="col-8">
                                        <p class="form-control-plaintext">
                                            {{ validationStatusEnum[selectedObservation.wn_validation_status] || "Geen" }}
                                        </p>
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label class="col-4 col-form-label">Cluster ID</label>
                                    <div class="col-8">
                                        <p class="form-control-plaintext">{{ selectedObservation.wn_cluster_id }}</p>
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label class="col-4 col-form-label">Opmerking</label>
                                    <div class="col-8">
                                        <p class="form-control-plaintext">{{ selectedObservation.notes }}</p>
                                    </div>
                                </div>
                            </div>
                            <div v-if="canViewRestrictedFields" class="row mb-2">
                                <div class="col-8 offset-4">
                                    <div class="form-check form-switch">
                                        <template v-if="isEditing && canEdit">
                                            <input v-model="editableObservation.public_domain" class="form-check-input"
                                                type="checkbox" id="public-domain" />
                                            <label class="form-check-label" for="public-domain">Nest op publiek terrein</label>
                                        </template>
                                        <template v-else>
                                            <p class="form-control-plaintext">
                                                <span v-if="selectedObservation.public_domain">Nest op publiek terrein</span>
                                                <span v-else>Niet op publiek terrein</span>
                                            </p>
                                        </template>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="accordion-item" v-if="canViewRestrictedFields">
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
                                    <p class="form-control-plaintext">{{ selectedObservation.observer_phone_number }}</p>
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
                                        <template v-if="isEditing && canEdit">
                                            <input v-model="editableObservation.visible" class="form-check-input"
                                                type="checkbox" id="visible" />
                                            <label class="form-check-label" for="visible">Nest tonen</label>
                                        </template>
                                        <template v-else>
                                            <p class="form-control-plaintext">
                                                <span v-if="selectedObservation.visible">Nest wordt getoond</span>
                                                <span v-else>Nest wordt niet getoond</span>
                                            </p>
                                        </template>
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Cluster ID</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <input v-model="editableObservation.wn_cluster_id" type="text" class="form-control" />
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">{{ selectedObservation.wn_cluster_id || '-' }}</p>
                                    </template>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Melder kreeg e-mail</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <select v-model="editableObservation.observer_received_email" class="form-select">
                                            <option :value="true">Melder kreeg e-mail</option>
                                            <option :value="false">Melder kreeg geen e-mail</option>
                                        </select>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">
                                            {{ selectedObservation.observer_received_email ? 
                                              'Melder kreeg e-mail' : 'Melder kreeg geen e-mail' }}
                                        </p>
                                    </template>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <label class="col-4 col-form-label">Opmerkingen</label>
                                <div class="col-8">
                                    <template v-if="isEditing && canEdit">
                                        <textarea v-model="editableObservation.admin_notes" rows="2" class="form-control"></textarea>
                                    </template>
                                    <template v-else>
                                        <p class="form-control-plaintext">{{ selectedObservation.admin_notes || '-' }}</p>
                                    </template>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>

            <p v-if="canViewRestrictedFields" class="mb-3 text-muted small" id="metadata">
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
import Multiselect from 'vue-multiselect';
import 'vue-multiselect/dist/vue-multiselect.min.css';

export default {
    emits: ['closeDetails', 'updateMarkerColor'],
    components: {
        Multiselect
    },
    setup(props, { emit }) {
        const vespaStore = useVespaStore();
        const selectedObservation = computed(() => vespaStore.selectedObservation);
        const isEditing = ref(false);
        const isLoggedIn = computed(() => vespaStore.isLoggedIn);
        const canEdit = computed(() => {
            const result = isLoggedIn.value && vespaStore.canEditObservation(selectedObservation.value);
            console.log('canEdit computed:', {
                isLoggedIn: isLoggedIn.value,
                canEditObservation: vespaStore.canEditObservation(selectedObservation.value),
                userMunicipalities: vespaStore.userMunicipalities,
                isAdmin: vespaStore.isAdmin,
                observationMunicipality: selectedObservation.value?.municipality_name
            });
            return result;
        });
        const canEditAdminFields = computed(() => isLoggedIn.value && vespaStore.isAdmin);
        const successMessage = ref('');
        const errorMessage = ref('');
        const eradicationResultError = ref('');
        const editableObservation = ref({});
        const selectedExtras = ref([]);
        const sourceUrl = computed(() => {
            if (!selectedObservation.value) return '';
            const { source, source_id, wn_id } = selectedObservation.value;
            if (source && source.toLowerCase().includes('inaturalist') && source_id) {
                return `https://www.inaturalist.org/observations/${source_id}`;
            }
            if (source === 'Waarnemingen.be' && wn_id) {
                return `https://waarnemingen.be/observation/${wn_id}`;
            }
            return '';
        });
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
            if (result && result !== null) {
                return 'Bestreden';
            } else {
                return 'Niet bestreden';
            }
        });
        const canViewRestrictedFields = computed(() => {
            return vespaStore.isAdmin ||
                (isLoggedIn.value && vespaStore.userMunicipalities.includes(selectedObservation.value?.municipality_name));
        });

        const eradicationStatusClass = computed(() => {
            const result = selectedObservation.value?.eradication_result;
            if (result && result !== null) {
                return 'bg-success';
            } else {
                return 'bg-danger';
            }
        });
        const validationStatusEnum = {
            "goedgekeurd_met_bewijs": "Goedgekeurd met bewijs",
            "goedgekeurd_door_admin": "Goedgekeurd door admin"
        };
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

                if (daysDiff < 10) {
                    let remainingDays = 10 - daysDiff;
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
            errorMessage.value = '';
            eradicationResultError.value = '';
            emit('updateMarkerColor', null);
        };

        // Add toggle edit mode function to switch between edit mode and view mode
        const toggleEditMode = () => {
            console.log("Toggle edit mode, current state:", isEditing.value);
            if (!isEditing.value) {
                startEdit(); // Enter edit mode
            } else {
                confirmUpdate(); // Save changes
            }
        };

        const startEdit = () => {
            console.log("Starting edit mode");
            isEditing.value = true;
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_date = selectedObservation.value.eradication_date ? 
                    formatToDate(selectedObservation.value.eradication_date) : null;
            }
        };

        const isUpdating = ref(false);
        let isUpdatingObservation = false;

        const confirmUpdate = async () => {
            // If not in edit mode, enter edit mode and exit
            if (!isEditing.value) {
                startEdit();
                return;
            }
            console.log("Saving changes");
            
            if (isUpdating.value) return;
            try {
                isUpdating.value = true;
                isUpdatingObservation = true;

                const hasQueenPresent = selectedExtras.value.some(extra => extra.value === 'queen_present');
                const hasMothPresent = selectedExtras.value.some(extra => extra.value === 'moth_present');
                editableObservation.value.queen_present = hasQueenPresent;
                editableObservation.value.moth_present = hasMothPresent;

                if ('nest_extra' in editableObservation.value) {
                    delete editableObservation.value.nest_extra;
                }

                const eradicationFields = ['eradication_date', 'eradicator_name', 'eradication_duration', 'eradication_persons', 'eradication_method', 'eradication_aftercare', 'eradication_problems', 'eradication_notes', 'eradication_product'];
                const hasEradicationData = eradicationFields.some(field => editableObservation.value[field]);

                if (editableObservation.value.eradication_result && !editableObservation.value.eradication_date) {
                    const today = new Date();
                    editableObservation.value.eradication_date = today.toISOString().split('T')[0];
                }

                if (editableObservation.value.eradication_date) {
                    const date = new Date(editableObservation.value.eradication_date);
                    if (!isNaN(date.getTime())) {
                        editableObservation.value.eradication_date = date.toISOString().split('T')[0];
                    } else {
                        throw new Error("Invalid eradication date format");
                    }
                }

                if (hasEradicationData && !editableObservation.value.eradication_result) {
                    eradicationResultError.value = 'Resultaat is verplicht wanneer andere bestrijdingsgegevens zijn ingevuld.';
                    throw new Error('Validation failed');
                }

                errorMessage.value = '';
                eradicationResultError.value = '';

                const observationToSend = { ...editableObservation.value };
                observationToSend.queen_present = hasQueenPresent;
                observationToSend.moth_present = hasMothPresent;

                // Log the payload before sending
                console.log('confirmUpdate: Sending to backend:', observationToSend);

                // Log the update attempt
                console.log('confirmUpdate: Attempting to update observation with ID:', observationToSend.id);
                const updatedObservation = await vespaStore.updateObservation(observationToSend);
                
                // Log the response
                console.log('confirmUpdate: Update response:', updatedObservation);

                successMessage.value = 'Wijzigingen succesvol opgeslagen!';
                setTimeout(() => successMessage.value = '', 3000);
                
                // Exit edit mode after successful save
                isEditing.value = false;
            } catch (error) {
                console.error('confirmUpdate: Error during update:', error);
                if (error.message === "Invalid eradication date format") {
                    errorMessage.value = 'De ingevoerde datum is ongeldig.';
                } else if (error.message === 'Validation failed') {
                    // Error already set in eradicationResultError
                } else if (error.message && error.message.includes('Network response was not ok')) {
                    errorMessage.value = 'Serverfout bij het opslaan van wijzigingen.';
                } else {
                    errorMessage.value = error.message || 'Er is een fout opgetreden bij het opslaan van de wijzigingen.';
                }
            } finally {
                isUpdating.value = false;
                isUpdatingObservation = false;
            }
        };
        
        const cancelEdit = () => {
            console.log("Canceling edit mode");
            isEditing.value = false;
            if (selectedObservation.value) {
                editableObservation.value = { ...selectedObservation.value };
                editableObservation.value.observation_datetime = formatToDatetimeLocal(selectedObservation.value.observation_datetime);
                editableObservation.value.eradication_date = selectedObservation.value.eradication_date ? 
                    formatToDate(selectedObservation.value.eradication_date) : null;
            }
            errorMessage.value = '';
            eradicationResultError.value = '';
        };

        const canViewContactInfo = computed(() => {
            if (vespaStore.isAdmin) return true;
            const userMunicipalities = vespaStore.userMunicipalities;
            const observationMunicipality = selectedObservation.value?.municipality_name;
            return userMunicipalities.includes(observationMunicipality);
        });

        const extrasOptions = [
            { value: "queen_present", label: "Koningin aanwezig" },
            { value: "moth_present", label: "Mot aanwezig" }
        ];
        
        const availableExtrasOptions = computed(() => {
            return extrasOptions.filter(option => !selectedExtras.value.some(selected => selected.value === option.value));
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
        
        // Modified watch for selectedObservation that initializes the multi-select when loading data
        watch(() => vespaStore.selectedObservation, (newVal) => {
            console.log('watch: selectedObservation changed:', newVal);
            if (!newVal) return;
            
            editableObservation.value = { ...newVal };
            editableObservation.value.observation_datetime = formatToDatetimeLocal(newVal.observation_datetime);
            editableObservation.value.eradication_date = newVal.eradication_date ? formatToDate(newVal.eradication_date) : null;
            
            // Reset edit mode when a new observation is selected
            isEditing.value = false;
            
            selectedExtras.value = [];
            if (newVal.queen_present === true) {
                const queenOption = extrasOptions.find(option => option.value === 'queen_present');
                if (queenOption) selectedExtras.value.push(queenOption);
            }
            if (newVal.moth_present === true) {
                const mothOption = extrasOptions.find(option => option.value === 'moth_present');
                if (mothOption) selectedExtras.value.push(mothOption);
            }
            
            emit('updateMarkerColor', newVal.id);
        }, { immediate: true });

        
        watch(selectedExtras, (newVal) => {
            if (!editableObservation.value) return;
            editableObservation.value.queen_present = newVal.some(extra => extra.value === 'queen_present');
            editableObservation.value.moth_present = newVal.some(extra => extra.value === 'moth_present');
            emit('updateMarkerColor', selectedObservation.value?.id);
        }, { deep: true });

        watch(selectedObservation, { immediate: true });

        const removeExtra = (option) => {
            selectedExtras.value = selectedExtras.value.filter(extra => extra.value !== option.value);
        };

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
            toggleEditMode,
            confirmUpdate,
            cancelEdit,
            reserveObservation,
            cancelReservation,
            formatDate,
            selectedExtras,
            extrasOptions,
            availableExtrasOptions,
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
            canViewRestrictedFields,
            validationStatusEnum,
            sourceUrl,
            removeExtra,
        };
    }
};
</script>